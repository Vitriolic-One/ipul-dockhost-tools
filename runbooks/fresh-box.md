# Runbook — Fresh-Box Setup

> Bring a brand-new Debian 13 box (or equivalent) from bare metal to running production. Estimated time: **30–60 minutes**.

## Prerequisites (gather BEFORE you start)

- Access to your offline secrets store (1Password / encrypted Drive folder / hardware token). You need:
  - `.env` for `ipul-intake` (Slack tokens, Gemini key, Salesforce creds, etc.)
  - `gmail-service-account.json` (the SA JSON for Gmail + Drive + Gemini auth)
  - `github_ipul` + `github_ipul.pub` (SSH deploy key for the three GitHub repos)
- A user account on the new box (this guide assumes `ipul-admin`) with sudo.

## Step 1 — Install Docker + Claude Code (10 min)

```bash
# Docker (Debian package, daemon enabled at boot)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ipul-admin
# Re-login or run `newgrp docker` so the group takes effect.

# Claude Code (current install method as of 2026-06)
# See: https://claude.com/code  — install + first-time auth
# After install: claude --version  should print 2.x
```

## Step 2 — Clone the three repos (1 min)

```bash
# Restore your SSH deploy key first:
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cp <offline-backup>/github_ipul* ~/.ssh/
chmod 600 ~/.ssh/github_ipul
chmod 644 ~/.ssh/github_ipul.pub

# Add to ssh-agent so git clone uses it:
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github_ipul

# Clone all three:
cd ~
git clone git@github.com:Vitriolic-One/ipul-intake.git
git clone git@github.com:IdahoParentsUnlimited/ipul-dockhost-tools.git
git clone git@github.com:IdahoParentsUnlimited/IPUL-Intake-Docs.git
```

## Step 3 — Restore secrets to their live locations (5 min)

```bash
# .env into ipul-intake repo
cp <offline-backup>/.env ~/ipul-intake/.env
chmod 600 ~/ipul-intake/.env

# Service Account JSON
mkdir -p ~/ipul-intake/secrets
chmod 711 ~/ipul-intake/secrets
cp <offline-backup>/gmail-service-account.json ~/ipul-intake/secrets/
chmod 600 ~/ipul-intake/secrets/gmail-service-account.json
```

## Step 4 — Enable systemd linger (one-time)

```bash
# So user timers fire when no shell is logged in:
sudo loginctl enable-linger ipul-admin
```

## Step 5 — Run the bootstrap script (5–10 min)

```bash
cd ~/ipul-dockhost-tools && ./bootstrap.sh
```

The script is idempotent — safe to re-run if any step needs retry. It will:

1. Verify prereqs.
2. Create the host-scripts venv at `~/ipul-intake-backup/venv/` and pip-install from requirements.txt.
3. Copy `backup.py` and `publish-docs.py` into `~/ipul-intake-backup/`.
4. Install the three systemd user units, daemon-reload, enable the backup timer.
5. Sync Claude config (`~/.claude/` settings, CLAUDE.md, skills, ipul-reference, memory).
6. Skip DB restore (see step 6 — do it explicitly).
7. Build + start the `ipul-intake` container.

## Step 6 — Restore the latest DB backup (5 min)

```bash
# See runbooks/restore-from-backup.md for the full recovery flow.
# In short: download the most recent intake-YYYY-MM-DD-HHMM.db.gz from
# intake_system_backups/actual-backups/ on Drive, gunzip, and copy into
# the container's named volume.
```

## Step 7 — Verify (5 min)

```bash
# Container running the expected version:
docker logs ipul-intake 2>&1 | head -20
# Look for "intake_system_starting" and the current version string.

# Slack bot connected:
docker logs ipul-intake 2>&1 | grep "Bolt app is running"

# Backup timer is enabled and shows next-run time:
systemctl --user list-timers ipul-intake-backup.timer

# Open Slack #intake-review:
# - Bot user should show as Online.
# - Send /intake status — should respond with the rotation board.

# Optional: fire a manual backup to confirm Drive write works:
systemctl --user start ipul-intake-backup.service
journalctl --user -u ipul-intake-backup.service -n 20 --no-pager
# Should see "uploaded:" line and exit 0.
```

## Step 8 — Update CLAUDE.md with the new IP / hostname (if applicable)

If the new box has a different IP than the old one, update:

- `~/.claude/CLAUDE.md` (global) — "Network: ..."
- `~/ipul-intake/CLAUDE.md` (project) — IP references if any

Commit + push from the new box back to GitHub.

## Done

You now have a running production intake system. Next scheduled backup at 17:15 Mountain, next deploy via the standard `runbooks/deploy.md` flow.

## Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `docker compose up` fails with "permission denied" on socket | Group change not in effect | `newgrp docker` then re-run |
| Container starts but Bolt doesn't connect | Bad Slack tokens in `.env` | Verify Slack app tokens, restart container |
| Backup timer doesn't fire | Linger not enabled | `sudo loginctl enable-linger ipul-admin` + `systemctl --user enable --now ipul-intake-backup.timer` |
| Gmail polling fails with "invalid_grant" | SA JSON not in place or wrong perms | `chmod 600` on the SA JSON; verify path in `.env` |
| Container reports DNS resolution errors | Tailscale stub-DNS leak (2026-06-03 lesson) | Confirm `docker-compose.yml` has `dns: [8.8.8.8, 1.1.1.1]`; recreate (not restart) the container |
