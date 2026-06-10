# Runbook — Cutover to a New Host

> Migrating the running intake system to a new physical or virtual machine. Estimated time: **2–4 hours** including stabilization window.

This runbook codifies the lessons from the home→office cutover (2026-06-01 → 2026-06-02). The system was migrated from "Dockhost" at 192.168.0.40 to "ipul-dockhost" at 192.168.2.15.

## Pre-cutover (day before)

### Inventory state

- Confirm latest backup is fresh: `journalctl --user -u ipul-intake-backup.service -n 10`.
- Confirm the offline secrets bundle is current: `.env`, SA JSON, SSH deploy keys.
- Note current container version (`docker logs ipul-intake | head -1`) and schema version.
- Snapshot the live DB explicitly via `systemctl --user start ipul-intake-backup.service` and confirm Drive upload.

### Prep the new box

- Run `fresh-box.md` runbook through Step 5 (bootstrap.sh creates the venv + systemd + Claude config + starts a container). **But pause before Step 6** (DB restore). The new container should be running with an *empty* DB at this point, ready to take the live restore.

### Notify stakeholders

- Slack message in `#intake-review`: "Maintenance window: cutting over to new host between X and Y. Brief outage expected."
- The system has a manual-fallback policy (Bill monitors inboxes directly) so even an extended outage is graceful.

## Cutover day

### Step 1 — Last live backup on the old host

```bash
# On old host:
systemctl --user start ipul-intake-backup.service
journalctl --user -u ipul-intake-backup.service -n 15 --no-pager
# Confirm upload — the cutover snapshot is the rollback floor.
```

### Step 2 — Stop the old container

```bash
# Old host:
docker compose -f ~/ipul-intake/docker-compose.yml down
# Slack bot disconnects. Gmail polling stops.
```

### Step 3 — Restore the cutover backup onto the new host

Follow `restore-from-backup.md` start to finish using the snapshot from Step 1.

### Step 4 — Start the new container

```bash
# New host:
cd ~/ipul-intake
docker compose up -d --build
sleep 10
docker logs ipul-intake 2>&1 | tail -20
```

### Step 5 — Verify end-to-end

- Container log shows correct version, `Bolt app is running`, polling.
- `/intake status` in Slack returns rotation board.
- Send a test email to `parents@` from a sender that should trigger AI classification — verify it lands in `#intake-review`.
- Verify `#intake-status` board updates if anyone changes availability.

### Step 6 — Decommission the old host

> Only after a 24–48 hour stabilization window. Don't rush this — keeping the old host quiescent lets you fail back if the new one misbehaves.

- Disable systemd timers on old host: `systemctl --user disable --now ipul-intake-backup.timer`.
- Mark the old host's DB clearly: `mv intake.db intake.db.stale-pre-cutover-YYYY-MM-DD`.
- Update `CLAUDE.md` (project + global) to point at the new IP.
- Update SSH known-hosts / Tailscale ACLs / firewall rules as needed.
- After 48 hours of clean operation on the new host: full shutdown of the old host.

## Lessons from the 2026-06-01 cutover (don't repeat these)

### 1. Tailscale stub-DNS got baked into the container

The new host had Tailscale running at boot. Docker captured `/etc/resolv.conf` → `127.0.0.53` (the Tailscale stub) into the container at create time. When Tailscale was disabled after cutover, the stub died, and the container went **DNS-blind for 23 hours** before anyone noticed.

**Prevention:** the current `docker-compose.yml` pins:
```yaml
dns:
  - 8.8.8.8
  - 1.1.1.1
```
Verify this is present in the repo before you cutover. If you're staging the container before disabling Tailscale, you can either pin DNS like this, or recreate the container **after** Tailscale is disabled. Restart-not-recreate won't re-read DNS config — must be a full container recreate.

### 2. Major-version SDK bump rode in on `docker compose up -d --build`

A `docker compose up -d --build` on the new host's first deploy pulled `google-genai 2.x` (latest at the time) — major-version bump from the 1.x the code had been tested against. Behavior shift caused intake 417 (a real voicemail) to silently auto-reject. **One day of operational chaos** before the fix shipped (v0.11.12 + the `<2.0.0` SDK pin).

**Prevention:** pin all major-version-sensitive dependencies in `pyproject.toml`. Current pins:
- `google-genai>=1.0.0,<2.0.0`
- Inspect `pyproject.toml` before cutover and tighten any other `>=X.0.0` that could ride a major bump.

### 3. Mid-cutover backups landed in the wrong Drive folder

Initial mistake (caught and fixed before going live): the backup script defaulted to a "test" folder ID. The DR backup wouldn't have been findable.

**Prevention:** the `host-scripts/backup.py` repo now hard-codes the production folder ID; verify `DRIVE_FOLDER_ID` matches the actual `intake_system_backups/actual-backups/` folder before re-deploying the script onto a new host.

### 4. Linger wasn't enabled — backup timer silently didn't fire

After cutover, the daily 17:15 backup didn't fire for the first three days because `loginctl enable-linger ipul-admin` hadn't been run.

**Prevention:** Step 4 of `fresh-box.md`. bootstrap.sh now warns when linger is not enabled — but doesn't auto-enable it because that needs sudo.

### 5. Claude config didn't follow the cutover

The new box was set up without copying memory entries, custom skills, or operational reference docs. Future-Claude inherited none of the operational context. Took several sessions of re-establishing preferences and learning the box state.

**Prevention:** the `claude/` directory in this repo holds settings, CLAUDE.md, skills, ipul-reference, and memory. `bootstrap.sh` syncs it all on first run. Don't skip Phase 4.
