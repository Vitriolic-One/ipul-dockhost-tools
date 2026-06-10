# ipul-dockhost-tools

Host-side tooling for **ipul-dockhost** — the box that runs the IPUL Intake Dispatch System container.

This repo holds everything that exists *outside* the `ipul-intake` container itself: the daily-backup script, the docs-publish script, systemd units, the on-box Claude Code config, and the runbooks to bring a fresh Debian box from bare metal to running production.

## What this repo gives you

A fresh Debian box + 3 git clones (`ipul-intake`, `ipul-dockhost-tools`, `IPUL-Intake-Docs`) + secrets restored from your offline backup = the full production stack in **30–60 minutes**.

## Layout

```
host-scripts/        backup.py, publish-docs.py, requirements.txt
systemd/user/        backup .service + .timer, claude-remote-control .service
claude/              on-box Claude Code config — settings.json (allowlist),
                     CLAUDE.md (operational context), skills/, ipul-reference/
                     (Slack U-IDs / channel IDs / SF User IDs), memory/
                     (feedback + project memory entries that future-Claude
                      should inherit)
runbooks/            fresh-box.md, restore-from-backup.md, deploy.md, cutover.md
bootstrap.sh         idempotent host-setup script: pre-flight checks,
                     venv install, systemd wire-up, Claude config sync
```

## What's NOT here (and why)

- **Secrets** — `.env`, `secrets/gmail-service-account.json`, SSH deploy keys. These belong in an offline encrypted backup (1Password, encrypted Drive folder, hardware token). Never in git.
- **The Python venv itself** — `host-scripts/requirements.txt` lists pinned dependencies; `bootstrap.sh` creates the venv on the new box. Avoids 50 MB+ of binaries in git.
- **The docs vault** — `IPUL-Intake-Docs` lives as its own repo for clean separation. Cloned alongside.
- **The intake system source** — `ipul-intake` is its own repo (`Vitriolic-One/ipul-intake`). Cloned alongside.

## Quick start (on a fresh Debian box)

```bash
# 1. Install Docker + Claude Code (manual, ~10 min)
# 2. Clone the three repos:
git clone git@github.com:Vitriolic-One/ipul-intake.git
git clone git@github.com:Vitriolic-One/ipul-dockhost-tools.git
git clone git@github.com:Vitriolic-One/IPUL-Intake-Docs.git

# 3. Restore secrets from your offline backup into:
#    ~/ipul-intake/.env
#    ~/ipul-intake/secrets/gmail-service-account.json
#    ~/.ssh/github_ipul (with chmod 600)

# 4. Run the bootstrap:
cd ipul-dockhost-tools && ./bootstrap.sh

# 5. Verify:
docker logs ipul-intake          # should show 'intake_system_starting' v0.x.y
systemctl --user status ipul-intake-backup.timer   # should show 'Active: active'
```

For step-by-step detail, see `runbooks/fresh-box.md`.

## Other runbooks

- `runbooks/restore-from-backup.md` — pull the latest `.db.gz` from Drive and restore into the container volume.
- `runbooks/deploy.md` — standard `git pull` + `docker compose up -d --build` cycle (the daily deploy ritual).
- `runbooks/cutover.md` — migrate the running system to a new host (with the lessons from the 2026-06-01 home→office cutover, including the DNS-blind 23-hour incident and the v0.11.13 SDK pin).

## Versioning

Tools in `host-scripts/` carry their own `__version__` strings (currently `backup.py 1.0.1`, `publish-docs.py 1.0.0`). The intake system itself is versioned separately in the `ipul-intake` repo's `src/__init__.py`.

## Repo also holds Claude on-box context

`claude/` is a verbatim snapshot of what lives under `~/.claude/` on a working box. Including memory and reference docs makes future-Claude on a rebuilt box inherit operational context — preferences, lessons learned, staff roster, channel IDs. **Sensitive only to the IPUL operational scope** (no secrets, no parent PII per the contact-redaction policy).
