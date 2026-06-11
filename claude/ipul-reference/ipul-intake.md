---
name: IPUL Intake Dispatch System — credentials, roster, integration state
description: Standing reference for the IPUL Intake dispatch system. Holds credentials pointers (GCP/Gmail service account, SF Connected App), staff roster with Slack U-IDs, channel IDs, integration architecture summary, lessons learned. Refreshed 2026-05-15 — Salesforce integration is LIVE via Client Credentials flow; FormAssembly is SUPERSEDED.
type: project
version: 2.0
last-verified: 2026-05-15
originSessionId: 3f5da6f9-cad2-463c-97a1-69b7479f04ee
---
# IPUL Intake Dispatch System

## Overview
Automated intake dispatch system for Idaho Parents Unlimited (IPUL), a nonprofit helping parents of children with disabilities. Polls Gmail inboxes, classifies emails, posts to Slack for approval, then dispatches: DM assigned staff + forward email + submit to Salesforce (Task + Intake_Log__c records).

**Pointer rule:** for canonical architecture, key files, pipeline detail, and deployment, read `~/Projects/ipul-intake/CLAUDE.md` (project-local). This memory holds the persistent identifiers (credentials, staff IDs, channel IDs) that don't belong in the project's CLAUDE.md.

## Knowledge Graph — query at context-switch
**Standing practice:** When switching into IPUL work, check `C:\Users\vitri\Projects\IPUL-Intake-Docs\graphify-out\graph.json` for cross-domain connections before making changes. Use `/graphify query "..."` to pull subgraphs for specific questions (e.g., "what calls dispatch_intake", "what concepts link to STATUS_CHANGING_COMMANDS"). After significant edits (code or docs), run `/graphify --update` (pointed at the same output dir) to keep it current. The graph combines code (`C:\Users\vitri\Projects\ipul-intake\src\`) and docs (`C:\Users\vitri\Projects\IPUL-Intake-Docs\`) — doc-drift becomes visible when `semantically_similar_to` edges break between docs and their code implementations. First built 2026-04-13: 623 nodes, 1,040 edges, 35 communities. Open `graph.html` for interactive browsing; read `GRAPH_REPORT.md` for god nodes, hyperedges, and knowledge gaps.

## Architecture
- **Runtime:** Python 3.11, Docker container on Dockhost (192.168.0.40)
- **Repo:** `github.com/IdahoParentsUnlimited/ipul-intake` (private), cloned to `/home/mcpuser/ipul-intake`
- **Local dev:** `C:\Users\vitri\Projects\ipul-intake`
- **Database:** SQLite (WAL mode), `/app/data/intake.db` (Docker named volume)
- **Slack:** Bolt SDK, Socket Mode (no public endpoint needed)
- **Container:** `ipul-intake`, restart: unless-stopped
- **Bot name:** `ipul_intake_bot`

## Pipeline (LIVE as of Mar 9)
1. **Gmail Poller** — polls `intakes@` and `parents@` every 2 min for unread emails
2. **Classification** — rule-based (all external → INTAKE) or AI when API key is set
3. **Extraction** — AI extracts structured data or fallback parser (voicemail transcript extraction, HTML-to-text stripping)
4. **Slack Review** — posts to `#intake-review` for Bill to approve/edit/reject
5. **Dispatch** — on approve: DM assigned staff + forward email (FA submission disabled)
6. **Mark as Read** — after processing, removes UNREAD label from Gmail

## Two-Path Classification
- **Rule-based:** When `LLM_API_KEY` is empty (or API fails), ALL inboxes use rules. Every external email → INTAKE for manual review. Internal `@ipulidaho.org` replies → NOT_INTAKE. Bounce/system senders (mailer-daemon, postmaster) → NOT_INTAKE.
- **AI mode:** When `LLM_API_KEY` is set, `parents@` gets AI classification. `intakes@` always uses rules. Graceful degradation: API failure → UNCERTAIN → manual review.

## LLM / AI Configuration
- **Production provider:** Google Gemini (`LLM_PROVIDER=google`, `LLM_MODEL=gemini-2.5-flash`)
- **GCP Project:** `ipul-intake-system` (IPUL Intake System) — Gmail + Gemini consolidated here
- **GCP Project (old):** `gen-lang-client-0304668277` (AI Studio auto-created, abandoned — AI Studio keys are permanently free tier)
- **API key:** `[REDACTED-GCP-API-KEY-rotated-2026-06-11]` (GCP Console key, paid tier, created Mar 11)
- **Model:** `gemini-2.5-flash` (upgraded from 2.0-flash which was retired for new projects)
- **Status (Mar 11):** WORKING. Paid tier, AI classification live on `parents@` inbox.
- **Supported providers in code:** OpenAI (`openai` pkg), Anthropic (`anthropic` pkg), Google (`google-genai>=1.0.0` pkg)
- **SDK:** Uses `google.genai.Client` (the newer `google-genai` SDK, NOT the old `google-generativeai`)
- **Two-stage pipeline:** classify (Stage 1) → extract (Stage 2). Prompts in `src/classifier/prompts.py`.
- **Fallback extraction:** Regex-based parser (`_fallback_extraction()`) handles voicemail and email without AI.
- **Confidence threshold:** 0.75 — below this, INTAKE becomes UNCERTAIN for manual review.
- **Workspace Gemini App vs API:** Workspace admin (Generative AI → Gemini) controls chatbot access, NOT the API. The `intake_processing` user group controls Gemini App access. API quota is separate, tied to the AI Studio API key.
- **Lesson learned:** AI Studio API keys are permanently free tier. GCP Console keys use paid tier. Always create keys in GCP Console for production.
- **Key restricted** to Generative Language API only (Mar 11).

## Voicemail Parsing
- Phone system: **Intermedia Cloud PBX**
- Voicemail emails are HTML-only (no text/plain body)
- `_strip_html()` converts HTML to text, then `_parse_voicemail_body()` extracts:
  - Caller name and phone from "message from" line
  - Date/time received, duration
  - Transcript between "Voicemail transcript:" and "The attached voicemail message"
- Transcript shown in Slack review card under ":telephone_receiver: Voicemail Transcript:" label

## Gmail Service Account
- **GCP Project:** ipul-intake-system
- **Service account:** `intake-email-reader@ipul-intake-system.iam.gserviceaccount.com`
- **Key ID:** [REDACTED-SA-KEY-ID]
- **Domain-wide delegation scopes:** `gmail.readonly`, `gmail.modify`, `gmail.send`
- **Credentials JSON:** deployed to `/home/mcpuser/ipul-intake/secrets/gmail-service-account.json`

## Staff Roster (last-verified 2026-05-15 via live DB SELECT * FROM staff)

| ID | Name | Email | Slack ID | SF User ID | Role | Status | Total Assigns | Hired |
|---|---|---|---|---|---|---|---|---|
| 1 | Bill Nuttycombe | bill@ipulidaho.org | UVB9L7WD6 | 005d00000066tycAAA | owner | active, logged-in, **lurker** | 3 | 2026-03-09 |
| 3 | Melissa Vian | melissa@ipulidaho.org | U01JDKET8FN | 0053o000007yOyd | **admin** | active, logged-in, overflow | 8 | 2026-03-09 |
| 2 | Kristy Colima | kristy@ipulidaho.org | U074GAPMZEE | 005VV000000p7AjYAI | staff | active, logged-in, **nobell** — **primary daily recipient** | **141** | 2026-03-09 |
| 4 | Allison Highley | allison@ipulidaho.org | U03KUKGCG91 | 0053o000009sM5D | staff | active, logged-in, overflow | 4 | 2026-03-09 |
| 5 | Sarah Gornik | sarah@ipulidaho.org | U0102QY4KA8 | 005d0000006FsfhAAC | staff | active, logged-in, overflow | 3 | 2026-03-09 |
| 6 | Jessy Lawson (SF: "Jessica Lawson") | jessical@ipulidaho.org | U0ANGRF006R | 005VV00000BYgBOYA1 | staff | active, logged-OUT, unavailable — **new hire, in training** | 0 | 2026-05-08 |
| 7 | Cara (SF: "Cara Bray") | cara@ipulidaho.org | U0AV2HK21NH | 005VV00000BpQmvYAF | staff | active, logged-OUT, unavailable — **new hire, in training** | 0 | 2026-05-08 |

**Onboarding plan (per Bill 2026-05-15):** Jessy Lawson and Cara will eventually do what Kristy is doing. Currently in training phase — logged out + unavailable until they're brought in via `/intake login` then `/intake in` (or `/intake overflow` for safe-default).

**Cross-system name mapping:** IPUL `display_name` stores the friendly/preferred names ("Jessy Lawson", "Cara"); Salesforce User records use formal/legal names ("Jessica Lawson", "Cara Bray"). Both surfaces stay in their native convention — the formal SF name appears in `Intake_Log__c.Assigned_To__c` only via the role-prefixed Bill-supplied `display_name`, so dispatched Tasks show "Jessy Lawson" / "Cara" not the formal names. Cosmetic asymmetry by design.

**SF User ID placeholder cleanup — RESOLVED 2026-05-15:** Both placeholder `005d00000066tyc` values (which were the 15-char form of Bill's `005d00000066tycAAA`) replaced with the real 18-char SF User IDs via direct `UPDATE staff` against the live DB. Verified via before/after SELECT — `updated_at` advanced from `2026-05-15 06:00:05` to `2026-05-15 14:07:22`. Field validation pending first real dispatch to either of them — Task ownership should land on their SF user, not Bill's.

**Sidekick relationships:** Currently NONE set (`sidekick_of` NULL for all staff). The May 12 multi-trainee sidekick validation has since been cleared. Overlay mechanism remains available for use during Jessy/Cara training.

**Dispatch eligibility (active recipients):** `is_active=1 AND is_logged_in=1 AND availability NOT IN ('unavailable', 'lurker')` → Kristy (nobell), Melissa (overflow), Allison (overflow), Sarah (overflow). In practice Kristy receives the dominant share — 141 cumulative vs single-digit counts for everyone else.

**ID prefix lesson:** Slack `U` = user ID (correct), `D` = DM channel ID (wrong). Always use `U` IDs for staff records. Salesforce ID lesson: 15-char and 18-char forms are equivalent (the 18-char adds a 3-char case-sensitivity check suffix); they refer to the same record.

**To re-verify this section in future sessions:** `mcp__ssh-dockhost__exec` →
```
docker exec ipul-intake python -c 'import sqlite3, json; c=sqlite3.connect("/app/data/intake.db"); c.row_factory=sqlite3.Row; [print(json.dumps(dict(row), default=str)) for row in c.execute("SELECT * FROM staff ORDER BY role DESC, display_name")]'
```

## Slack Workspace
- **Bot:** `ipul_intake_bot`
- **Channels:** `#intake-review` (C0AKCDS69N1), `#intake-status` (C0AKDR0KR5L). `#intake-log` (C0AKUQ546M7) retired in v0.8.0 — no longer receives posts.
- **Owner (Bill):** UVB9L7WD6

## FormAssembly (SUPERSEDED)
- **Status:** SUPERSEDED by direct Salesforce REST API integration. FA-form-as-trigger pattern is no longer used in production.
- **Premier plan limitation (historical context):** No API access on the grandfathered Premier plan — this was the original reason for prioritizing direct SF integration.
- **Form field IDs (historical, retained in case leftover FA forms are ever repurposed):** tfa_4 (Source), tfa_18 (Routed To), tfa_17 (Intake Reason), tfa_75 (Sent By), tfa_11 (Name), tfa_13 (Phone), tfa_50 (Email)

## Salesforce (NPSP) — LIVE as of 2026-05
- **Integration:** Direct SF REST API from dispatch engine. Source: `src/salesforce/submit.py`. Replaces the FA-form-as-trigger pattern entirely.
- **Auth pattern:** OAuth 2.0 **Client Credentials flow** — `POST https://ipul.my.salesforce.com/services/oauth2/token` with `grant_type=client_credentials` + `client_id` + `client_secret`. No user password. No client certificate / mTLS. Bearer token returned, used for all subsequent REST calls (`Authorization: Bearer <token>`).
- **Config:** `SalesforceConfig` dataclass in `src/config.py` (`instance_url`, `client_id`, `client_secret`). Env vars: `SF_INSTANCE_URL` (default `https://ipul.my.salesforce.com`), `SF_CLIENT_ID`, `SF_CLIENT_SECRET`. Connected App credentials in `secrets/admin-credentials.md` (gitignored).
- **Records created per approved intake:** Task (the work item, owned by assigned staff member) + Intake_Log__c (tracking/counting record).
- **Task fields:** Subject="Intake", ActivityDate=Boise-tomorrow, Source_of_Intake__c (mapped from source_type), Intake_Reason__c (validated against SF restricted picklist), Intake_Name__c, Intake_Phone__c, Intake_Email__c, OwnerId (from `staff.salesforce_user_id`).
- **Intake_Log__c fields:** Assigned_To__c (role-prefixed display like `"(FRS) Kristy Colima"` — prefixes: `(IT)` owner, `(DIR)` admin, `(FRS)` staff), Intake_Reason__c.
- **Staff SF User ID mapping:** Per-staff `salesforce_user_id` column in `staff` table. Set via `/intake sf-link @person <SF_ID>`. Display names + roles from `staff.display_name` / `staff.role`, not hardcoded.
- **Cert-related Salesforce platform notices (May 15 email triage):** None apply. IPUL is a vanilla REST API client over HTTPS; standard `certifi` trust store handles Salesforce's server certs. No client certs to rotate, no mTLS to audit. Chrome dual-use cert ban (Jun 15, 2026), reduced lifespans (Mar 15, 2026), and DigiCert G2 root transition (Feb 5, 2026) all bypass IPUL.

## Four-Layer Staffing Model (current as of v0.11.x)
Four independent dimensions control whether staff receive assignments. **For canonical command list + behavior, read `~/Projects/ipul-intake/CLAUDE.md` and `IPUL-Intake-Docs/User Guide/Admin Guide.md`.** Memory holds only the high-level model:

1. **Roster** (`is_active`) — Admin+: `/intake recruit @person` / `/intake sever @person`. Adds/removes staff.
2. **Shift** (`is_logged_in`) — Self or Admin+: `/intake login` / `/intake logout`. Active shift vs away/vacation.
3. **Availability** (tier) — Self or Admin+: `/intake in` / `/intake out` / `/intake overflow` / `/intake nobell` / `/intake lurk` (admin+ only, v0.7+). Daily granularity.
4. **Sidekick overlay** (`sidekick_of` column, v0.10.x) — Trainee shadows a mentor's dispatches. Independent of availability tier — overlay, not a tier. Multi-trainee verified May 12 (Jessy + Cara both sidekicking same mentor).

**Dispatch eligibility:** `is_active=1 AND is_logged_in=1 AND availability NOT IN ('unavailable', 'lurker')`. Sidekicks ALSO receive a training-copy DM of any dispatch their mentor receives.

## Capacity Management (v0.2.0, Mar 10)
- **4-tier availability:** Available, Overflow, No Bell, Unavailable
- **Daily caps:** Soft cap = 6 (skip, try next), Hard cap = 8 (done for the day). Reset at midnight Mountain.
- **5-phase rotation cascade:** Available < soft → No Bell (ignores caps) → Available < hard → Overflow < soft → Overflow < hard → none
- **Business hours:** M-F 9-5 Mountain. Review cards post 24/7, but assignment deferred outside hours.
- **Morning batch:** 9 AM M-F dispatches all approved-but-unassigned intakes from overnight.
- **Capacity DMs:** Staff get notified at soft cap hit, hard cap hit. Overflow activation logged.
- **Schema v12 (current, verified `src/db/models.py:19` 2026-05-15):** Migration chain v1→v12. Recent: v12 (latest), v11, v10 (`auto_rejected` status), v9 (blocked_senders), v8 (sidekick_of), v7 (admin_dm_refs), v6 (kept/test statuses), v5 (SF User IDs backfill), v4 (lurker tier), v3 (is_logged_in), v2 (availability). For exact per-migration semantics, read `src/db/models.py` `_migrate_vN_to_vN+1` functions.
- **Commands:** `/intake overflow`, `/intake nobell`, `/intake login`, `/intake logout`

## Key Design Decisions
- **Nothing happens without Bill's authorization** — standing order
- **Everything has tests** — current count is tracked in the latest version's Change Log entry (447+ passing as of v0.11.2; this number rots fast, defer to source rather than memory)
- **Manual fallback must always work** — system degrades gracefully
- **No AI required to run** — rule-based classification + fallback extraction works without API key
- **Google Gemini deployed** for AI (gemini-2.5-flash, paid tier, GCP Console key). Anthropic (`claude-sonnet-4-6`) is the backup alternative.
- **Always update documentation after every user-facing change** — standing order (canonicalized in `CLAUDE-rules-ipul.md` DOCS UPDATE + PDF REGENERATION rules)

## Docker Deployment
- **Dockerfile:** `useradd appuser` must come BEFORE `mkdir/chown` — order matters
- **Volume permissions:** Named volumes created as root; Dockerfile `chown`s to appuser (UID 1000). If volumes already exist, fix with: `docker run --rm -v ipul-intake_intake-data:/app/data busybox chown -R 1000:1000 /app/data`
- **Secrets:** Bind mount `./secrets:/app/secrets:ro`
- **No ports exposed** — outbound-only (Gmail, Slack, LLM APIs)
- **Local Dockerfile vs repo:** Local has `nobody` user + layer caching fix, repo has `appuser`. Needs sync.
- **Credentials reference:** `secrets/admin-credentials.md` (local, gitignored)

## Deployment Steps
1. `cd /home/mcpuser/ipul-intake && git pull`
2. `docker compose up -d --build`
3. Check logs: `docker logs ipul-intake`

## Lessons Learned
- **Gmail API caching:** Marking emails unread can take 1-2 minutes to reflect in API queries
- **SSH MCP command limit:** 1000 chars max — use python scripts for long content
- **HTML-only emails:** Intermedia voicemail emails have no text/plain part, only HTML. Must strip HTML to parse.
- **Docker log buffer:** Fast startup processing can scroll past before you check logs. Use `docker logs --since` with timestamps.
- **Slack bot channel access:** Bot must be explicitly invited to channels with `/invite @botname`

## Documentation
- **Docs vault:** `C:\Users\vitri\Projects\IPUL-Intake-Docs\`
- **Google Drive (shared):** `G:\Shared drives\Company\Process Documents\Intakes\Intakeorama\User Guide\`
- **Standing order:** When commands change, UX changes, or new features ship: update Staff Guide, Admin Guide, and Change Log in docs vault, copy to Google Drive, and regenerate PDFs (`Staff Guide.pdf`, `Admin Guide.pdf` in Drive root). Do this as part of each deploy, not as a separate step.

## Open Issues / TODO
- [x] **Fix Gemini API quota** — DONE (Mar 11). New GCP Console key on `ipul-intake-system`, model `gemini-2.5-flash`.
- [x] **Direct Salesforce integration** — DONE (2026-05). Client Credentials flow live in `src/salesforce/submit.py`. FA dependency eliminated.
- [x] **Admin "nobody logged in" notifications** — DONE (Mar 10).
- [x] **No Bell response GIF** — DONE (Mar 10). `assets/nobell.gif`.
- [ ] Sync local Dockerfile with repo (local uses `nobody`, repo uses `appuser`)
- [ ] Test Edit & Approve, Not Intake, and Reassign buttons on real `parents@` emails
- [ ] Test `/intake nobell` GIF delivery (needs `files:write` bot scope)
- [ ] Bot scope expansion (`pins:read`/`pins:write`) — flagged on multiple recent sessions
- [ ] Wipe-helper rate-limit hardening (v0.11.0 channel-wipe helper, may hit Slack rate limits on heavy-message channels)
- [ ] `today_rejected` / `today_auto_filtered` COALESCE consistency pass (stylistic follow-up from v0.11.2; not functional)
- [ ] Update IPUL-Intake-Docs vault (API Integrations, Secrets Inventory) to reflect Google Gemini + live Salesforce as deployed providers
