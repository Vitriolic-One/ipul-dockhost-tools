---
name: feedback-redact-contact-pii
description: "Redact contact PII (names, phone numbers, email addresses of people who contact IPUL for help) from ALL permanent artifacts — code, tests, comments, change log, vault docs, memory, session summaries. Use [redacted name], [redacted phone number], [redacted email] placeholders. Intake numbers OK as references."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bcefcd91-35dd-4c26-b825-89768073f856
---

# Redact contact PII from permanent code and notes

Anything that persists beyond the runtime database — source code, code comments, test data + docstrings, Change Log entries, IPUL-Intake-Docs vault, this memory directory, saved-session summaries — must redact PII of people who contact the system for assistance.

**The runtime processing pipeline is explicitly OUT of scope** (Bill confirmed 2026-06-05). Gmail message bodies, `intakes.extracted_data` JSON at runtime, Slack DMs to staff, Salesforce submissions, and the daily `.db.gz` Drive backups all touch real PII because the job requires it — but the system's own retention model already drops them: 30-day `purge_old_intake_pii` zeroes `extracted_data` to `{"purged": true}`; backups roll on 7-day retention; Gmail forwards are operational not archival. Do NOT scrub the runtime pipeline. The policy is about *frozen-archive* artifacts (git history, test fixtures, change-log entries, saved sessions, notes) where PII would otherwise persist indefinitely with no natural rolloff.

Use bracketed placeholders:

- `[redacted name]` — parent / caller / family member names
- `[redacted phone number]` — phone numbers
- `[redacted email]` — email addresses
- `[redacted address]` — street addresses, city + state combos when they identify a household

Refer to the intake by its intake number ("intake #417") — internal references are fine.

**Why:** Bill 2026-06-05, highest-priority directive: *"the people asking for our assistance — lets treat this as names, phone numbers, email addresses ... if they need to be saved [use redacted placeholders] ... it's ok to refer to the intake by the intake number but not to use their identifiers."*

The runtime DB has a 30-day PII purge but it does NOT reach into git history, test fixtures, change log entries, notes, memory files, or session snapshots — those persist indefinitely. A name embedded in a test docstring lives forever in `git log`.

**Scope — IMPORTANT, this is narrower than first read:**
- **In scope: VERIFIED INTAKES ONLY.** Per Bill 2026-06-05: *"this is for verified intakes — rejected are not this strictly covered."* If a row was a real person seeking IPUL's assistance (status `dispatched`, `approved`, `kept`, OR a reclassified-from-auto-reject like intake 417), strict redaction applies to their name, phone, email.
- **Not strictly covered:** auto-rejected / rejected intakes — spam, bulk mail, bounces, unsubscribe blasts, noreply@ senders. These typically aren't real people seeking help anyway (no human identity at stake), and the policy doesn't demand redaction there. Still: don't include rejected-sender names in artifacts for no reason; just no hard rule.
- **Out of scope entirely:** staff / operator names + emails (Bill, Kristy, Allison, Melissa, Sarah, etc — they ARE the system, not contacts). Platform domains (`@formassembly.com`, `@intermedia.com`). Intake row IDs.
- **Likely in scope but confirm if unsure:** child names, ages, school districts, addresses on a verified intake. Default to redacting unless Bill explicitly accepts.

**How to apply going forward:**
- BEFORE writing any new permanent artifact, mentally scrub for contact PII.
- For tests that exercise real-data shapes, fabricate PII that mirrors the SHAPE: same digit count for phones, same domain shape for emails, plausible-shaped names — so regex / parser logic is still exercised, but no real identifier survives.
- For Change Log / incident notes: lead with the intake number and the failure mode, not the parent's identity.
- For session summaries: redact in the markdown. Raw `.jsonl` transcripts are a separate decision (verbatim historical record — see [[post-cutover-state-2026-06-02]] if a deletion / quarantine policy gets defined).

**Historical sweep:** there is a backlog of pre-2026-06-05 PII to clean up (notable spots: `tests/test_v011_12.py`, Change Log v0.11.12 entry, recent saved-session summaries). That sweep is its own piece of work — scope with Bill before doing it.

Related: [[feedback-observations-are-not-go-signals]], [[project-backup-pipeline-live]].
