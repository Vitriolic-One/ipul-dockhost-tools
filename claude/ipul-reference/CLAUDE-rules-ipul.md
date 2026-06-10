<!-- CLAUDE-rules-ipul.md v1.0 — created 2026-05-07 (split from CLAUDE.md restructure) -->

# CLAUDE Rules — IPUL Intake System Domain

> Domain rules that apply when working on the **IPUL Intake System** (`~/Projects/ipul-intake/` + `~/Projects/IPUL-Intake-Docs/` vault). Loaded automatically by CRITICAL #2 (TOPIC SWITCH) when IPUL triggers fire. Always-apply CRITICAL rules in `CLAUDE.md` continue to apply on top of these.

**Project-local details (architecture, schema, deploy commands, credentials pointers, lessons learned):** see `~/Projects/ipul-intake/CLAUDE.md`.

**Documentation vault:** `~/Projects/IPUL-Intake-Docs/` — read on TOPIC SWITCH per `memory/feedback_review_vault_on_context_switch.md` IPUL section. Required reading on every spin-up: `README.md`, `Development/Change Log.md`, `Operations/Deployment.md`. Domain-specific reading per task.

---

## Domain Rules

### [CRITICAL] GIT PUSH REMINDER (with deploy-context exception)
**TRIGGER:** Any `git commit` in the `ipul-intake` repo.

**MUST:** Run `git status` after the commit. If the output shows `"Your branch is ahead of 'origin/<branch>' by N commit(s)"`, the commit is local-only.

**Default behavior** (commit OUTSIDE a deploy context — e.g., committing local doc edits with no shipping intent yet): surface to Bill before moving on:
> *"commit `<shortsha>` is local-only — push now, or hold?"*

**EXCEPTION — deploy context:** when the commit is part of a deploy flow (Bill said *"ship it"* / *"put in the fix"* / *"deploy this"* / similar, OR you're following `IPUL-Intake-Docs/Operations/Deployment.md`), the push is **automatic** — do NOT gate on Bill. Push immediately, then run the rest of the deploy (pull on host via `bash scripts/deploy.sh`, container rebuild auto-handled). Asking *"push or hold"* inside an active deploy adds friction Bill has already authorized away.

**MUST NOT:** Force-push to `main`. Skip hooks (`--no-verify`). Bypass signing.

**WHY:** A deliberate "hold" beats a forgotten commit. But repeatedly asking "push?" during an in-flight deploy that Bill explicitly authorized is the failure mode rule #4 (COMPLETE THE LOOP) addresses. Origin: 2026-05-07 — Bill caught me asking "push now or hold?" mid-deploy after he'd already said "put in the fix"; lesson is "always push when we deploy."

### [CRITICAL] PDF REGENERATION MANDATORY ON USER-FACING CHANGES
**TRIGGER:** IPUL Intake System update where the change touches user-facing docs (`User Guide/Staff Guide.md`, `User Guide/Admin Guide.md`, `User Guide/Troubleshooting.md`, `Development/Change Log.md`) OR changes a UX surface that staff reference operationally.

**MUST:** Regenerate the affected doc's PDF AND copy to Google Drive (`G:\Shared drives\Company\Process Documents\Intakes\Intakeorama\User Guide\`) as part of the **same deploy** — not as a separate follow-up step.

**MUST NOT:** Mark a deploy complete without the PDF refresh when user-facing docs changed. Stale PDFs in Google Drive mislead staff who read them, not the source markdown.

**WHY:** Staff reads PDFs from Google Drive, not source markdown. PDF lag = staff operating on outdated procedures. Per the project's "Always update documentation after user-facing changes" standing order in `~/Projects/ipul-intake/CLAUDE.md`.

### [CRITICAL] DOCS UPDATE ON USER-FACING CHANGES
**TRIGGER:** Shipping any change that affects: command syntax, button labels/order, automated post format (SOD/EOD/status), DM phrasing, dispatch logic visible to staff, or new admin commands.

**MUST:** Update — in the same deploy commit/sequence — the affected:
- `IPUL-Intake-Docs/User Guide/Staff Guide.md` (if staff-facing)
- `IPUL-Intake-Docs/User Guide/Admin Guide.md` (if admin-facing)
- `IPUL-Intake-Docs/Development/Change Log.md` (always, with version entry)
- Regenerate corresponding PDFs (per PDF rule above)
- Copy PDFs to Google Drive

**MUST NOT:** Defer doc updates to "next session" or "after live testing." Bill has caught me leaving doc gaps before — they don't get retroactively filled.

**WHY:** Staff sees the PDFs. Admins reference the Admin Guide. Change Log is the version history. All three need to advance lock-step with the code. Per project standing order.

### [IMPORTANT] STATUS-CHANGING COMMANDS ALLOWLIST
**TRIGGER:** Adding any new `/intake` subcommand or modifying an existing one's effect on staffing state.

**MUST:** Check `STATUS_CHANGING_COMMANDS` set in `src/slack_bot/app.py`. Any command that changes staffing state, availability, rotation, or system-pause must be in the allowlist so a `#intake-status` board refresh fires after the command runs.

**MUST NOT:** Ship a state-changing command and forget the allowlist — the symptom is "I ran `/intake X` but the status board didn't update" with no obvious error.

**WHY:** Status-board freshness is part of the contract. Silent staleness erodes trust in the board.

### [IMPORTANT] SLACK USER IDS USE `U` PREFIX
**TRIGGER:** Storing or comparing Slack user IDs in code, DB, config, tests.

**MUST:** Use `U`-prefixed real user IDs (`U01ABC...`). DM channel IDs (`D...`) are not user IDs.

**MUST NOT:** Mix `D` channel IDs into staff/user-id columns. Test fixtures using `U001` are fine; production DM-channel-as-user-id is not.

**WHY:** Slack treats them differently. Auth, mention rendering, DM lookup all break in subtle ways when conflated.

### [STYLE] PYTHON ENVIRONMENT
**TRIGGER:** Running tests, scripts, or installing packages locally.

**MUST:** Use `venv/Scripts/python.exe` (Windows path; venv is at `venv/`, not `.venv/`).

**MUST NOT:** Run `python` bare — Windows resolves it to the Microsoft Store stub when the venv isn't activated. Activate via `source venv/Scripts/activate` for shell sessions, or full path for Bash tool calls.

**WHY:** Bare `python` fails with "Python was not found" → wastes a turn diagnosing.

---

## Pointers (read on demand, not always)

- `~/Projects/ipul-intake/CLAUDE.md` — project-local standing orders, architecture, schema migrations, key files, deploy summary, credentials pointer, lessons learned (Gmail caching, SSH MCP 1000-char limit, HTML-only emails, Docker compose restart vs recreate, SQLite CREATE TABLE quirks).
- `~/Projects/IPUL-Intake-Docs/Operations/Deployment.md` — canonical deploy flow including `scripts/deploy.sh`. **Read before any deploy** to avoid asking "push? pull? rebuild?" — that's all documented.
- `~/Projects/IPUL-Intake-Docs/Technical/Database Schema.md` — column semantics (`created_at` vs `updated_at` vs `assigned_at`, status states, migration history). Required for any DB-query / migration / activity-window work.
- `~/Projects/IPUL-Intake-Docs/Technical/Architecture.md` — data flow, module boundaries.
- `memory/ipul-intake.md` — credentials pointer, staff roster, channel IDs, standing rules originating from past IPUL sessions.
- `memory/feedback_intake_channel_routing.md` — `#intake-review` vs `#intake-status` routing rule.
