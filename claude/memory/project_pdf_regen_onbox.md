---
name: project-pdf-regen-onbox
description: pandoc + texlive-xetex are installed on ipul-dockhost for regenerating IPUL docs vault PDFs. Drive push still needs SA permissions on the Intakeorama folder.
metadata: 
  node_type: memory
  type: project
  originSessionId: bcefcd91-35dd-4c26-b825-89768073f856
---

# On-box PDF regen for IPUL docs vault

Installed 2026-06-03: `pandoc` 3.1.11.1 + `texlive-xetex`. Confirmed working via a smoke render.

## What gets regenerated

The IPUL docs vault carries source markdown plus PDFs alongside:

| Source | PDF |
|---|---|
| `IPUL-Intake-Docs/User Guide/Staff Guide.md` | `Staff Guide.pdf` |
| `IPUL-Intake-Docs/User Guide/Admin Guide.md` | `Admin Guide.pdf` |
| `IPUL-Intake-Docs/User Guide/Troubleshooting.md` | `Troubleshooting.pdf` |
| `IPUL-Intake-Docs/Development/Change Log.md` | `Change Log.pdf` |

PDFs distribute to Google Drive at **`Process Documents > Intakeorama > User Guide`** (separate Drive folder from `intake_system_backups/`, different audience: staff/admins, not system-recovery).

## When to regen

Per IPUL standing rule "DOCS UPDATE + PDF REGEN on user-facing changes":
- Staff Guide / Admin Guide / Troubleshooting: regen when commands, UX, or staff-facing behavior change.
- Change Log: regen on every change-logged release/fix (it's the historical record).
- Purely operational/infra changes (e.g. container DNS pinning, host-side backup pipeline) update markdown only — staff-facing PDFs don't need refresh.

## How to regen + publish (single command)

```bash
# Full sweep (all 4 docs):
~/ipul-intake-backup/publish-docs.py

# Just one doc:
~/ipul-intake-backup/publish-docs.py --only "Change Log"
```

The script (`~/ipul-intake-backup/publish-docs.py` v1.0.0) renders the markdown via `pandoc --pdf-engine=xelatex -V geometry:margin=1in --toc`, then uploads .md + .pdf to Drive `User Guide/` using `files().update` against the existing file ids so URLs and share permissions stay stable. The script path is on the allowlist; the full chain runs without prompts.

If you need to render outside the script (e.g. preview an isolated change):
```bash
cd ~/IPUL-Intake-Docs
pandoc "Development/Change Log.md" -o "Development/Change Log.pdf" --pdf-engine=xelatex -V geometry:margin=1in --toc
```

## Drive push from on-box — SA access confirmed 2026-06-03

The SA has Content manager access on the Intakeorama tree (granted 2026-06-03). Folder IDs:

| Folder | ID |
|---|---|
| `Process Documents/Intakeorama` | `1_HP4jStl2V1USZT5Y5-ZTGaHuyoDuJQr` |
| `Process Documents/Intakeorama/User Guide` | `1D-bp7TYDvMJ6WaplHXagDqtie7J3mZij` |

Both live in IPUL Workspace Shared Drive `0AAiBPoB_3FcVUk9PVA`.

End-to-end push flow (when a real regen is needed):
1. Edit markdown in `~/IPUL-Intake-Docs/` on-box.
2. Regen relevant PDFs via `pandoc Source.md -o Source.pdf --pdf-engine=xelatex`.
3. Upload PDFs (and corresponding markdown if Drive is the canonical source for those) to `User Guide` folder id `1D-bp7TYDvMJ6WaplHXagDqtie7J3mZij` via the SA — same `googleapiclient` pattern as [[project-backup-pipeline-live]].
4. To replace an existing file rather than create a duplicate: query by name + parent, then `files().update(media_body=...)` against the existing file id.

## Divergence between Drive and local vault (as of 2026-06-03)

Worth knowing before any catch-up push:

- **Drive User Guide PDFs are dated 2026-04-09 to 2026-05-12.** Local vault PDFs are dated 2026-06-01. Local markdown has accumulated edits since then (today: backup pipeline + DNS incident entries). Catch-up means: regen all four PDFs locally, push to Drive replacing the older files.
- **Drive has two files NOT in local `User Guide/`:** `Architecture.md` (2026-03-12) and `Data Flow.md` (2026-03-12). Before pushing, check whether these were moved to a different vault subdirectory (e.g. `Technical/`) — if so, just push the User-Guide-targeted files and leave Architecture/Data Flow alone; if they only exist in Drive, decide whether to pull them into the vault or leave them as Drive-only.
- The Drive .md files were last edited 2026-04-09 to 2026-04-24. The local vault has been the authoritative source since cutover; future workflow should treat the vault as canonical and push to Drive as a publish step, not bidirectional sync.

## Gotchas

- Use `--pdf-engine=xelatex` explicitly. Pandoc's default `pdflatex` chokes on common UTF-8 punctuation (smart quotes, em-dashes) without extra package fiddling; xelatex handles them.
- Long tables in markdown may overflow margins under xelatex defaults. Add `-V geometry:margin=0.75in` if a regen looks crowded.
- **Emoji glyphs render as blanks — this is a CONTENT problem, not cosmetic.** Bill confirmed 2026-06-03 that the emojis in the docs are not decoration: they're the same identifiers the intake bot shows in Slack (status markers, action icons, etc.). When a staff member sees ℹ️ ✅ 🚫 🎯 in the Staff Guide, they're meant to recognize the symbol from the bot UI. Blank boxes break that recognition. "Acceptable for now" per Bill but should be fixed before any meaningful staff retraining or onboarding pass. Fix: install `fonts-noto-color-emoji`, render with `-V mainfont="DejaVu Sans" -V mainfontfallback="Noto Color Emoji"`; if xelatex still fights it, fall back to lualatex (handles fallback fonts better) or wkhtmltopdf (renders via HTML/Chrome stack with native emoji support).
- **xelatex render is leaner than the prior toolchain.** Comparing 2026-06-03 sweep against prior PDFs: Staff Guide 165KB→61KB, Admin Guide 203KB→99KB, Troubleshooting 97KB→28KB, Change Log 177KB→171KB. Content is intact; the originals likely had richer styling (Obsidian / Word? in the original toolchain). Acceptable for ongoing use; if Bill wants pixel-fidelity with the old look, that's a separate styling effort.
- The 2026-06-01 PDFs are no longer the visual baseline — the 2026-06-03 sweep replaced everything in Drive User Guide.

Related: [[project-backup-pipeline-live]] for the SA + Drive API pattern that would extend to PDF push.
