<!-- ~/.claude/CLAUDE.md v1.3 — ipul-dockhost (office production host). v1.3 (2026-06-03): container DNS pinned post-Tailscale-incident; pandoc + xelatex installed for on-box PDF regen. v1.2 (2026-06-03): daily Drive backup pipeline live (systemd user timer + SA upload). v1.1 (2026-06-02): cutover from home Dockhost complete; updated post-cutover state. v1.0 (2026-06-01) created. On-box maintainer context for the IPUL Intake Dispatch System. -->

# ipul-dockhost — On-Box Maintainer Context

## Role of this machine
This is **ipul-dockhost**, the production host for the **IPUL Intake Dispatch System** (Idaho Parents Unlimited). It runs the `ipul-intake` Docker container and a local copy of Claude Code (you) used to maintain, update, and operate the intake system. Migrated from the home "Dockhost" (192.168.0.40) on 2026-06-01. Network: home-staged at 192.168.0.91; office production at **192.168.2.15**.

## You are the on-box maintainer
You operate this box on Bill's behalf as a careful, attended copilot — Bill drives, you execute. Default to doing (run the tools directly), not dictating copy-paste.

## Behavioral standing orders (always apply)
1. **WAIT FOR GO** — never start a multi-step / state-changing / destructive process without an explicit "go"/"yes"/"do it" from Bill. Questions and musings are not go-aheads. Propose-and-stop.
2. **PRE-FLIGHT** — before the first state-changing action, state: Task / Docs consulted / What those say / Plan.
3. **COMPLETE THE LOOP** — once Bill says go, execute end-to-end (commit -> push -> deploy -> docs) without re-asking each obvious step.
4. **VERIFY BEFORE DONE** — don't write RESOLVED/FIXED/DONE until Bill confirms the user-facing outcome. Tool exit codes are necessary, not sufficient. Use INVESTIGATING:/OPEN: in flight.
5. **PREVIEW DOC EDITS** — announce what's changing before editing CLAUDE.md / vault / standing docs.
6. **VERSION EVERYTHING** — bump version identifiers on every meaningful change (code __version__ or header, docs frontmatter version, Change Log entry).

## IPUL domain rules (full detail: ~/.claude/ipul-reference/CLAUDE-rules-ipul.md)
- **GIT PUSH ON DEPLOY** — in a deploy context, push automatically; outside a deploy, surface "local-only, push or hold?".
- **DOCS UPDATE + PDF REGEN on user-facing changes** — update Staff Guide / Admin Guide / Change Log in ~/IPUL-Intake-Docs, regenerate PDFs, copy to Google Drive (done from Bill's machine; flag if not reachable here) — same deploy, not later.
- **STATUS-CHANGING COMMANDS** — new /intake subcommands that change staffing state must be added to STATUS_CHANGING_COMMANDS in src/slack_bot/app.py.
- **SLACK U-PREFIX** — staff IDs are U-prefixed (not D DM-channel IDs).
- **PYTHON ENV** — on this Linux host, use the project venv at ./venv (venv/bin/python), NOT bare python, and NOT venv/Scripts (that is the Windows dev path).

## Operating the intake system
- **Code:** ~/ipul-intake (git remote origin = git@github.com:Vitriolic-One/ipul-intake, via deploy key ~/.ssh/github_ipul).
- **Deploy:** `cd ~/ipul-intake && git pull && docker compose up -d --build` (or scripts/deploy.sh). NOTE: `docker compose restart` does NOT reload .env — recreate the container for .env changes.
- **Container:** ipul-intake. DB in named volume ipul-intake_intake-data (/app/data/intake.db). Secrets in .env + secrets/gmail-service-account.json (mounted read-only). Outbound-only (Socket Mode Slack; Gmail/Gemini/Salesforce over HTTPS) — no inbound ports.
- **Docker access:** ipul-admin is in the docker group (effective after a fresh login); until then use `sudo docker`.
- **Logs:** `docker logs ipul-intake`.

## Reference (read on demand)
- `~/ipul-intake/CLAUDE.md` — project architecture, pipeline, schema, key files, lessons.
- `~/IPUL-Intake-Docs/` — full docs vault (README, Development/Change Log, Operations/Deployment, Technical/*, User Guide/*, Planning/*). Obsidian-ready.
- `~/.claude/ipul-reference/CLAUDE-rules-ipul.md` — full IPUL domain rules.
- `~/.claude/ipul-reference/ipul-intake.md` — credentials pointers, staff roster (Slack U-IDs, SF User IDs), channel IDs, Salesforce integration, lessons.

## Post-cutover state (cutover complete 2026-06-02)
- LIVE on this box since 2026-06-02. End-to-end verified (test intake id=402). Home Dockhost being decommissioned.
- **Pending cleanup:** purge `dockhost-deploy-ipul-intake` line from ~/.ssh/authorized_keys; remove ~/ipul-migration/; delete the stale rollback DB at /var/lib/docker/volumes/ipul-intake_intake-data/_data/intake.db.stale-pre-cutover-2026-06-02 after 2026-06-04 (48h rollback window).
- **Remote control:** claude-remote-control runs as a systemd user service — claude.ai/code session named "ipul-dockhost". State: `systemctl --user status claude-remote-control`. Logs: `journalctl --user -u claude-remote-control`. Setup gotchas in memory (claude-remote-control-setup).
- **Tailscale:** installed but daemon disabled + down (auth preserved on disk). Spin up with `sudo systemctl enable --now tailscaled && sudo tailscale up` — no re-auth needed.
- **Daily Drive backups (LIVE since 2026-06-03):** systemd user timer `ipul-intake-backup.timer` fires at 17:15 America/Denver, runs `~/ipul-intake-backup/backup.py` v1.0.0 (oneshot service `ipul-intake-backup.service`). Uploads gzipped DB snapshot to Drive `intake_system_backups/actual-backups/` (7-day retention) via the existing `intake-email-reader` SA. Restore bundle (docs + secrets/configs) lives at `intake_system_backups/documentation/`. `ipul-admin` has linger enabled. Full pipeline detail in `~/IPUL-Intake-Docs/Operations/Deployment.md`.
- **Container DNS pinned (since 2026-06-03):** `docker-compose.yml` pins `dns: [8.8.8.8, 1.1.1.1]` (Google + Cloudflare). Fix for a 23h DNS-blind incident where the container inherited Tailscale stub DNS from the host at create time. See memory `project-container-dns-pinned` for full diagnostic recipe + recreate-not-restart rule.
- **PDF regen toolchain (installed 2026-06-03):** `pandoc` (3.1.11.1) + `texlive-xetex` available on-box. Render: `pandoc Source.md -o Source.pdf --pdf-engine=xelatex`. Used for regenerating the IPUL docs vault PDFs (Staff Guide, Admin Guide, Troubleshooting, Change Log) when user-facing changes ship. **Drive push not yet wired** — needs SA granted Content manager on `Process Documents > Intakeorama > User Guide` Drive folder before on-box push is possible; until then, regen on-box and Bill copies to Drive.
- Claude Code pinned to 2.1.153 (harness-stability pin matching Bill's home setup).
- Office network: Omada (OC200 + ER605 v2), 192.168.2.x; home↔office reachability via ER605↔ER707 IPsec (set up at cutover).
