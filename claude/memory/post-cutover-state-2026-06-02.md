---
name: post-cutover-state-2026-06-02
description: "State of ipul-dockhost after the 2026-06-02 cutover — what's live, what's dormant, what's queued"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9314e4cc-3cae-4a2e-9b75-56bd80347f2a
---

The IPUL Intake cutover from home Dockhost to ipul-dockhost completed 2026-06-02. End-to-end verified via test intake id=402 (Bill's email from vitriolic@gmail.com → parents@ipulidaho.org → polled → classified → review post in Slack channel C0AKCDS69N1 → admin DMs delivered). Total intakes 394 post-cutover. Stale pre-cutover DB preserved at `/var/lib/docker/volumes/ipul-intake_intake-data/_data/intake.db.stale-pre-cutover-2026-06-02`.

**State as of 2026-06-02 evening:**
- ipul-intake container: live, image v0.11.3, polling intakes@ + parents@ every 120s, Slack Socket Mode connected.
- claude-remote-control: live as systemd user service (see [[claude-remote-control-setup]]). Session "ipul-dockhost" reachable via claude.ai/code.
- Tailscale: installed but DAEMON DISABLED + DOWN. Auth state preserved on disk (tail7b3c6.ts.net, owner bill@ipulidaho.org, last assigned IP 100.120.97.13). Spin back up with `sudo systemctl enable --now tailscaled && sudo tailscale up` — no re-auth needed.

**Queued work (Bill's stated next priorities, in order):**
1. Google Drive access for this Claude — partly addressed via service-account direct upload (no MCP needed for the backup pipeline); broader Drive read/write for Claude not yet wired.
2. ~~Backup / portability system for the intake state~~ — **DONE 2026-06-03.** Daily Drive backup pipeline live; see [[project-backup-pipeline-live]] for operating notes.

**Open migration-cleanup TODOs (not blocking, but should close soon):**
- Purge `dockhost-deploy-ipul-intake` line from `~/.ssh/authorized_keys` (no longer needed).
- Remove `~/ipul-migration/`.
- Delete the stale pre-cutover DB snapshot after ~2026-06-04 (keep 48h rollback window).
- Confirm home Dockhost is fully decommissioned (poller stopped, container `docker compose down`, restart policy disabled). A drop-in prompt for the home Claude was drafted in the cutover conversation; ask Bill if he wants it again.

**Why:** ipul-dockhost is now the single point of failure for IPUL intake — backup design is the next critical workstream.

**How to apply:** treat this box as authoritative production. CLAUDE.md still references migration as "PENDING" in places — update that whenever Bill gives the go. Don't reuse the stale-pre-cutover DB; it's a rollback hatch only.
