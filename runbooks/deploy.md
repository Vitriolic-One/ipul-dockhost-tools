# Runbook — Standard Deploy

> The day-to-day "ship a code change" workflow. Estimated time: **5–15 minutes** depending on test-suite size + docker build time.

## Standing rules

These are non-negotiable. They live in the on-box CLAUDE.md too — written here for the runbook reader.

- **PRE-deploy backup is automatic.** Fire `systemctl --user start ipul-intake-backup.service` and wait for Drive upload confirmation before touching the container. Skip only for pure docs-only or tests-only changes that don't touch runtime behavior.
- **POST-deploy backup is offered, not auto-fired.** After the deploy looks healthy, *ask* the operator before firing a second "known-good" checkpoint.
- **Tests must pass before commit.** Full suite green is the minimum bar.
- **Change Log entry on every meaningful change.** Lives in `IPUL-Intake-Docs/Development/Change Log.md` (its own git repo). Bumps in the same commit (or the same push) as the code change.
- **Docs follow the code.** User-facing behavior change → Staff Guide / Admin Guide update + PDF regen + Drive push, in the same deploy (not later).

## Standard flow

### 1. Pre-flight backup (auto)

```bash
systemctl --user start ipul-intake-backup.service
sleep 10
journalctl --user -u ipul-intake-backup.service -n 10 --no-pager
# Confirm: "uploaded:" line. Exit code 0 not required (post-upload prune
# may fail on the trash step for a stuck file — uploads + new prune is
# what matters).
```

### 2. Make the code change

In `~/ipul-intake/`:
- Edit code.
- Bump `src/__init__.py` `__version__` if it's a meaningful release.
- Write tests for the change.
- Run the full suite: `venv/bin/pytest --tb=short`. Must be green.
- If schema changes: add migration to `src/db/models.py` (`_migrate_vN_to_vN+1`), bump `SCHEMA_VERSION`, and update `_run_migrations`.
- Update `IPUL-Intake-Docs/Development/Change Log.md` with the entry.
- Update user-facing docs (Staff Guide, Admin Guide, Troubleshooting) if behavior changed.

### 3. Commit + push

```bash
cd ~/ipul-intake
git add -A
git status --short    # confirm what's staging
git commit -m "vX.Y.Z — <summary>"
git push origin main
```

If you changed `IPUL-Intake-Docs/`:

```bash
cd ~/IPUL-Intake-Docs
git add -A
git commit -m "docs: <summary for the doc change>"
git push origin main
```

### 4. Regen + publish user-facing PDFs (if docs changed)

```bash
~/ipul-intake-backup/publish-docs.py --only "Staff Guide"
~/ipul-intake-backup/publish-docs.py --only "Admin Guide"
~/ipul-intake-backup/publish-docs.py --only "Change Log"
# (--only is per-doc; omit to push all four standard docs)
```

### 5. Deploy on the box

```bash
cd ~/ipul-intake
git pull
docker compose up -d --build
```

The `--build` rebuilds the image so dependency updates and code edits land in the running container.

### 6. Verify clean startup

```bash
sleep 8
docker logs ipul-intake 2>&1 | tail -20
```

Look for:
- `"version": "X.Y.Z"` matches the version you just pushed.
- `database_initialized` (and any expected migration log lines).
- `starting_gmail_poller` and `starting_slack_bot`.
- `Bolt app is running`.
- `gmail_messages_found` / `gmail_new_emails` on the first poll.
- No exception tracebacks.

### 7. Post-deploy backup offer (operator decision)

Ask the on-box maintainer: *"Want me to fire a manual post-deploy backup as the v0.X.Y known-good checkpoint?"*

If yes:

```bash
systemctl --user start ipul-intake-backup.service
```

## Rollback (if the deploy is bad)

1. Stop the container: `docker compose stop`
2. `git revert <commit>` or `git reset --hard <prior-commit>` (and force-push if needed — risky)
3. Restore the pre-deploy DB from `intake_system_backups/actual-backups/` per `restore-from-backup.md` (use the snapshot from step 1 of this runbook).
4. `docker compose up -d --build` to start the rolled-back code.
5. Verify per step 6.

If you can't roll back cleanly: the post-cutover state memory entry has on-box recovery tips, and `~/.claude/ipul-reference/CLAUDE-rules-ipul.md` has the full IPUL rules including "manual fallback always works" — Bill monitors the inboxes directly in the worst case.
