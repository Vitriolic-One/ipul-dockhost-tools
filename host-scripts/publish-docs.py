#!/home/ipul-admin/ipul-intake-backup/venv/bin/python
"""
IPUL docs vault -> Google Drive publish.

Regenerates the 4 user-facing PDFs (Staff Guide, Admin Guide,
Troubleshooting, Change Log) from their markdown sources via pandoc
+ xelatex, then pushes both .md + .pdf into the Intakeorama / User
Guide Drive folder using the intake-email-reader service account.

Existing files in Drive are REPLACED (files().update with the same
file id) so URLs and share permissions stay stable.

Single-shot: run with no arguments to do the full sweep.

Pass --only NAME (e.g. `--only "Change Log"`) to regen + push just
one of the 4. NAME is matched against the base filename without
extension and is case-sensitive.
"""

__version__ = "1.0.0"

import argparse
import datetime as dt
import os
import subprocess
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SA_KEY_PATH    = "/home/ipul-admin/ipul-intake/secrets/gmail-service-account.json"
VAULT_ROOT     = "/home/ipul-admin/IPUL-Intake-Docs"
USER_GUIDE_ID  = "1D-bp7TYDvMJ6WaplHXagDqtie7J3mZij"
SCOPES         = ["https://www.googleapis.com/auth/drive"]

# (local relative path of .md, base name for Drive)
DOCS = [
    ("User Guide/Staff Guide.md",     "Staff Guide"),
    ("User Guide/Admin Guide.md",     "Admin Guide"),
    ("User Guide/Troubleshooting.md", "Troubleshooting"),
    ("Development/Change Log.md",     "Change Log"),
]


def log(msg: str) -> None:
    ts = dt.datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] {msg}", flush=True)


def render(md_rel: str) -> str:
    """Render markdown -> PDF alongside the source. Returns the PDF path."""
    md_abs  = os.path.join(VAULT_ROOT, md_rel)
    pdf_abs = md_abs[:-3] + ".pdf"
    subprocess.run(
        [
            "pandoc", md_abs, "-o", pdf_abs,
            "--pdf-engine=xelatex",
            "-V", "geometry:margin=1in",
            "--toc",
        ],
        check=True,
    )
    return pdf_abs


def drive_client():
    creds = service_account.Credentials.from_service_account_file(SA_KEY_PATH, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def existing_by_name(drive) -> dict:
    resp = drive.files().list(
        q=f"'{USER_GUIDE_ID}' in parents and trashed=false",
        fields="files(id,name,size)",
        supportsAllDrives=True, includeItemsFromAllDrives=True, pageSize=200,
    ).execute()
    return {f["name"]: f for f in resp["files"]}


def mime(name: str) -> str:
    if name.endswith(".pdf"): return "application/pdf"
    if name.endswith(".md"):  return "text/markdown"
    return "application/octet-stream"


def push(drive, existing: dict, local_path: str, drive_name: str) -> None:
    media = MediaFileUpload(local_path, mimetype=mime(drive_name), resumable=False)
    if drive_name in existing:
        fid    = existing[drive_name]["id"]
        old_sz = existing[drive_name].get("size", "?")
        f = drive.files().update(
            fileId=fid, media_body=media, fields="id,name,size",
            supportsAllDrives=True,
        ).execute()
        log(f"UPDATE {f['name']:35s}  id={f['id']}  {old_sz}b -> {f['size']}b")
    else:
        body = {"name": drive_name, "parents": [USER_GUIDE_ID]}
        f = drive.files().create(
            body=body, media_body=media, fields="id,name,size",
            supportsAllDrives=True,
        ).execute()
        log(f"CREATE {f['name']:35s}  id={f['id']}  size={f['size']}b")


def main() -> int:
    p = argparse.ArgumentParser(description="Regen IPUL docs PDFs and push to Drive User Guide.")
    p.add_argument("--only", help="Base name to publish (e.g. 'Change Log'). Default: all four.")
    args = p.parse_args()

    targets = DOCS
    if args.only:
        targets = [(rel, name) for rel, name in DOCS if name == args.only]
        if not targets:
            log(f"FAILED: --only '{args.only}' didn't match any of {[n for _,n in DOCS]}")
            return 2

    drive = drive_client()
    existing = existing_by_name(drive)

    for md_rel, name in targets:
        md_abs = os.path.join(VAULT_ROOT, md_rel)
        if not os.path.exists(md_abs):
            log(f"FAILED: source missing: {md_abs}")
            return 1
        log(f"rendering: {md_rel}")
        pdf_abs = render(md_rel)
        push(drive, existing, md_abs,  f"{name}.md")
        push(drive, existing, pdf_abs, f"{name}.pdf")

    log("publish complete")
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
