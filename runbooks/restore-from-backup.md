# Runbook — Restore DB from Drive Backup

> Recover the intake DB from a `.db.gz` snapshot in `intake_system_backups/actual-backups/`. Estimated time: **5 minutes**.

## When to use this

- **Fresh-box bootstrap.** Step 6 of `fresh-box.md`.
- **Bad deploy.** A code change corrupted DB state and you want to roll back.
- **DB corruption.** SQLite reports integrity check failure or container can't open the DB.
- **Audit.** You need to inspect what a prior day's state looked like — restore a snapshot into a *temporary* container or a sibling SQLite file, never overwriting prod.

## Where backups live

```
Drive: intake_system_backups/actual-backups/
File pattern: intake-YYYY-MM-DD-HHMM.db.gz
Retention: 7 days (older entries are trashed by the daily prune; Drive's
           30-day Trash auto-purge handles final removal).
```

Each gzipped backup is ~140 KB; the underlying DB ~1.2 MB uncompressed.

## Standard restore flow (overwriting prod DB)

> **⚠️ Destructive.** This overwrites the live intake DB. Pre-flight: confirm with a human owner before running on a healthy production container.

### 1. Stop the container

```bash
docker compose -f ~/ipul-intake/docker-compose.yml stop
```

### 2. Download the desired backup from Drive

Easiest path: open the Drive UI, navigate to `intake_system_backups/actual-backups/`, download the `.db.gz` you want, scp it to the box.

```bash
# On your laptop:
scp intake-2026-06-10-1715.db.gz ipul-admin@<dockhost-IP>:/tmp/
```

Alternative (on-box, via SA): write a one-off Python script using
`~/ipul-intake-backup/venv/bin/python` and the SA at
`~/ipul-intake/secrets/gmail-service-account.json` to download by file ID.

### 3. Gunzip and place into the volume

```bash
gunzip -k /tmp/intake-2026-06-10-1715.db.gz
# Produces /tmp/intake-2026-06-10-1715.db

# Sanity-check it's a valid SQLite file:
file /tmp/intake-2026-06-10-1715.db
# Should print: "SQLite 3.x database, ..."

# Copy into the Docker named volume (the volume is at
# /var/lib/docker/volumes/ipul-intake_intake-data/_data/intake.db).
# Easiest path: use `docker cp` into a temp container.

# First start a transient container that mounts the volume:
docker run --rm -v ipul-intake_intake-data:/data -v /tmp:/host alpine \
  sh -c "cp /host/intake-2026-06-10-1715.db /data/intake.db && \
         chown 1000:1000 /data/intake.db && \
         chmod 640 /data/intake.db"
```

### 4. Restart the container

```bash
docker compose -f ~/ipul-intake/docker-compose.yml up -d
sleep 8
docker logs ipul-intake 2>&1 | tail -15
```

### 5. Verify

- `database_initialized` log line appears.
- `gmail_messages_found` log lines appear (poller is back).
- `Bolt app is running` confirms Slack reconnected.
- Run `/intake status` in Slack — rotation board reflects the restored state.

## Safer alternative — read-only inspection

If you just need to *look* at a backup without overwriting prod:

```bash
gunzip -k /tmp/intake-2026-06-10-1715.db.gz
sqlite3 /tmp/intake-2026-06-10-1715.db
# inside the prompt:
.schema intakes
SELECT id, status, created_at FROM intakes ORDER BY id DESC LIMIT 10;
.quit
```

The container's live DB is unchanged.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `chown` fails inside the alpine container | UID/GID mismatch with the appuser inside ipul-intake | Use `docker exec ipul-intake chown appuser:appuser /app/data/intake.db` after the copy |
| Container starts but fails schema check | Restored DB was from a newer schema version than the current code | Either downgrade code or migrate the DB forward |
| Slack bot doesn't reconnect after restart | Token state cached in `processed_emails` confused | Usually self-heals; if not, container restart twice |
