#!/home/ipul-admin/ipul-intake-backup/venv/bin/python
"""
IPUL intake DB backup -> Google Drive via service account.

Daily flow:
  1. Snapshot live intake.db via sqlite3 .backup inside the container (safe vs WAL).
  2. docker cp the snapshot out to the host, gzip it.
  3. Upload to Drive folder intake_system_backups/actual-backups/ using the
     intake-email-reader service account (Content manager on parent folder).
  4. Trash prior backups in that folder older than RETENTION_DAYS. Drive's
     30-day Trash auto-purge handles final removal — also gives a recovery
     window if the wrong file is ever pruned.
"""

__version__ = "1.0.1"  # 2026-06-10: trash route + per-file prune resilience

import datetime as dt
import gzip
import pathlib
import shutil
import subprocess
import sys
import tempfile

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SA_KEY_PATH = "/home/ipul-admin/ipul-intake/secrets/gmail-service-account.json"
DRIVE_FOLDER_ID = "1iXHNseTvfBZpGX0yoTgPT_edF2_4rZXi"  # intake_system_backups/actual-backups/
CONTAINER_NAME = "ipul-intake"
DB_PATH_IN_CONTAINER = "/app/data/intake.db"
RETENTION_DAYS = 7
SCOPES = ["https://www.googleapis.com/auth/drive"]


def log(msg: str) -> None:
    ts = dt.datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] {msg}", flush=True)


def snapshot_db(host_dest: pathlib.Path) -> None:
    """Snapshot the live DB from inside the container and copy it to the host."""
    container_tmp = "/tmp/intake-backup-snapshot.db"
    snapshot_py = (
        "import sqlite3; "
        f"src = sqlite3.connect({DB_PATH_IN_CONTAINER!r}); "
        f"dst = sqlite3.connect({container_tmp!r}); "
        "src.backup(dst); src.close(); dst.close()"
    )
    subprocess.run(
        ["docker", "exec", CONTAINER_NAME, "python", "-c", snapshot_py],
        check=True,
    )
    subprocess.run(
        ["docker", "cp", f"{CONTAINER_NAME}:{container_tmp}", str(host_dest)],
        check=True,
    )
    subprocess.run(
        ["docker", "exec", CONTAINER_NAME, "rm", "-f", container_tmp],
        check=True,
    )


def gzip_file(src: pathlib.Path, dest: pathlib.Path) -> None:
    with src.open("rb") as fi, gzip.open(dest, "wb", compresslevel=9) as fo:
        shutil.copyfileobj(fi, fo)


def drive_client():
    creds = service_account.Credentials.from_service_account_file(
        SA_KEY_PATH, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload(drive, path: pathlib.Path, name: str) -> dict:
    body = {"name": name, "parents": [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(str(path), mimetype="application/gzip", resumable=False)
    f = drive.files().create(
        body=body,
        media_body=media,
        fields="id,name,size,createdTime",
        supportsAllDrives=True,
    ).execute()
    log(f"uploaded: {f['name']} id={f['id']} size={f['size']}b")
    return f


def prune_old(drive, keep_id: str) -> None:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=RETENTION_DAYS)
    cutoff_rfc3339 = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    q = (
        f"'{DRIVE_FOLDER_ID}' in parents "
        "and name contains 'intake-' "
        f"and createdTime < '{cutoff_rfc3339}' "
        "and trashed = false"
    )
    resp = drive.files().list(
        q=q,
        fields="files(id,name,createdTime)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora="allDrives",
        pageSize=100,
    ).execute()
    files = resp.get("files", [])
    if not files:
        log("retention: nothing to prune")
        return
    for f in files:
        if f["id"] == keep_id:
            continue
        try:
            # v1.0.1: swapped files().delete() -> files().update(trashed=True)
            # because the SA's delete API returned 404 on files the list API
            # had just returned (a Drive list-vs-delete permission asymmetry
            # — same one hit on the v2 Staff Guide cleanup, 2026-06-05). The
            # trash route works at Content manager level; Drive's 30-day
            # Trash window also gives a recovery floor for any accidental
            # prune.
            drive.files().update(
                fileId=f["id"],
                body={"trashed": True},
                supportsAllDrives=True,
            ).execute()
            log(f"trashed: {f['name']} id={f['id']} createdTime={f['createdTime']}")
        except Exception as e:
            # Per-file resilience: one stubborn file shouldn't fail the whole
            # prune. Next run retries. Keeps the upload+prune pipeline
            # exit-0 healthy so systemd doesn't keep flagging the unit
            # as failed on a non-critical retention step.
            log(
                f"prune_skip: {f['name']} id={f['id']} "
                f"err={type(e).__name__}: {e}"
            )


def main() -> int:
    timestamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M")
    backup_name = f"intake-{timestamp}.db.gz"
    log(f"starting backup -> {backup_name}")

    with tempfile.TemporaryDirectory(prefix="ipul-backup-") as td:
        tdp = pathlib.Path(td)
        snapshot_path = tdp / "intake.db"
        gz_path = tdp / backup_name

        snapshot_db(snapshot_path)
        log(f"snapshot ok: {snapshot_path.stat().st_size}b")

        gzip_file(snapshot_path, gz_path)
        log(f"gzipped: {gz_path.stat().st_size}b")

        drive = drive_client()
        uploaded = upload(drive, gz_path, backup_name)
        prune_old(drive, keep_id=uploaded["id"])

    log("backup complete")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        log(f"FAILED: subprocess {e.cmd} exit={e.returncode}")
        sys.exit(1)
    except Exception as e:
        log(f"FAILED: {type(e).__name__}: {e}")
        sys.exit(1)
