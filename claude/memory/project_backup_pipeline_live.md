---
name: project-backup-pipeline-live
description: "Operating notes for the daily Drive backup pipeline (live since 2026-06-03). Where things live, how to verify, what to touch when secrets rotate."
metadata: 
  node_type: memory
  type: project
  originSessionId: bcefcd91-35dd-4c26-b825-89768073f856
---

# IPUL intake daily Drive backup pipeline — operating notes

Live since 2026-06-03. Replaces the prior "session handoff" memory (folded in once verified end-to-end). The pipeline is meant to be low-touch: see [[post-cutover-state-2026-06-02]] for context on why this workstream existed.

## Where things live

| Thing | Location |
|---|---|
| Backup script | `~/ipul-intake-backup/backup.py` (v1.0.0) |
| Python venv | `~/ipul-intake-backup/venv/` (google-api-python-client + google-auth) |
| systemd service | `~/.config/systemd/user/ipul-intake-backup.service` (oneshot) |
| systemd timer | `~/.config/systemd/user/ipul-intake-backup.timer` (`OnCalendar=*-*-* 17:15:00 America/Denver`, `Persistent=true`) |
| SA key (reused) | `/home/ipul-admin/ipul-intake/secrets/gmail-service-account.json` (also used for Gmail polling) |
| SA email | `intake-email-reader@ipul-intake-system.iam.gserviceaccount.com` |
| Drive parent folder | `intake_system_backups/` inside Shared Drive "IT stuff" (id `1JBbxZxrjQMz50rSmFsPYT_pbBvymm3Qy`) |
| Drive `/actual-backups/` | id `1iXHNseTvfBZpGX0yoTgPT_edF2_4rZXi` — rolling 7 days of `intake-*.db.gz` |
| Drive `/documentation/` | id `1Ldgdmm3FOOwJNY90GQzljtBw0yTnQgAe` — RESTORE.md, CLAUDE.md, MANIFEST.sha256, dot-env, gmail-service-account.json, github_ipul[.pub], claude-remote-control.service |
| Staging dir for doc bundle | `~/ipul-intake-backup/docs-staging/` |
| User linger | enabled on `ipul-admin` (so the timer fires without an interactive login) |

## How to verify it's running

```
systemctl --user list-timers ipul-intake-backup.timer
journalctl --user -u ipul-intake-backup.service --since "1 day ago"
```

Or eyeball: open the Drive `actual-backups/` folder, confirm a fresh `intake-*.db.gz` from the last day or two exists.

## When to refresh the `/documentation/` bundle

Re-upload to `intake_system_backups/documentation/` whenever any of these change:
- `RESTORE.md` or `CLAUDE.md` (the restore procedure)
- Any bundled secret (`.env` rotation, new Gmail SA key, new `github_ipul` deploy key)
- The `claude-remote-control.service` unit

Workflow: stage in `~/ipul-intake-backup/docs-staging/`, regenerate `MANIFEST.sha256`, upload via the SA (Content manager on the parent folder, so the SA can create + overwrite-by-replace there). The SA owns its own uploads, so it can delete the prior version it uploaded; older Bill-owned originals (e.g. the 2026-06-02 batch in the root) require Bill to trash via the Drive UI — same SA permission edge as the original `.part_*` cleanup.

## What's deliberately NOT wired

- **Failure notification** — backups failing will be silent. If you want email/Slack ping, add `OnFailure=` in the service unit pointing at a notifier unit. Bill's operating posture: monthly drive-by check of the folder.
- **Off-Drive replication** — single Drive folder is the only destination. Acceptable risk per Bill's "trusted admins" ACL boundary call.

## Pitfalls

- Don't add `*.iam.gserviceaccount.com` as a member of the Shared Drive itself unless really needed — folder-level grant has been sufficient and is narrower.
- The SA can't delete files owned by other principals in the folder. If you upload a doc with the SA and Bill replaces it via the UI, the SA can no longer delete the Bill-owned version — you'll need Bill to clean up.
- Backup script uses `docker exec` for the snapshot (avoids sudo on the Docker volume) — keep this approach if you refactor.

## Versioning

- `backup.py` carries `__version__`. Bump on any meaningful change.
- The `/documentation/` bundle's `RESTORE.md` + `CLAUDE.md` carry frontmatter `version:` — bump and re-upload with `MANIFEST.sha256` regenerated on any change.
- Operations/Deployment.md and Change Log in `~/IPUL-Intake-Docs/` get an entry on any pipeline-affecting change.

Related: [[post-cutover-state-2026-06-02]] for what's live on this host overall.
