---
name: feedback-backup-around-major-updates
description: "PRE-deploy: ALWAYS auto-fire a manual backup before deploying a major update — Bill's standing order from 2026-06-10. POST-deploy: ASK whether to fire a second 'known-good' checkpoint backup (existing rule from 2026-06-04). Both apply on the same release."
metadata:
  node_type: memory
  type: feedback
  originSessionId: bcefcd91-35dd-4c26-b825-89768073f856
---

# Backup around every major update — pre-deploy auto, post-deploy offer

## PRE-deploy: always pull a backup BEFORE updating

**Standing order, Bill 2026-06-10:** *"always pull a backup before updating things."* No offer — just do it. The pre-deploy backup is the rollback floor: if the deploy corrupts the DB or behavior turns out wrong, this is the snapshot to restore from. Skipping it because "the deploy looks safe" is exactly the moment it isn't.

**How to apply:**
- Before `git push` / `docker compose up -d --build` on a major release (anything with a Change Log entry above "trivial"), fire `systemctl --user start ipul-intake-backup.service` and **wait for it to land in Drive** before kicking off the deploy steps.
- Verify in the journal that the upload completed cleanly (`uploaded: ... size=...` line). NOTE: as of 2026-06-10 the service exits 1 on the retention-prune step due to a Drive delete-vs-list permission asymmetry — that's a separate bug. The upload itself succeeds first; check for the upload line, not the exit code.
- Mention it in the pre-flight summary so the operator knows the rollback floor is in place: *"Pulling pre-deploy backup — back in ~10s, then deploying."*

**Skip ONLY for:**
- Pure docs-only or tests-only changes that don't touch runtime behavior.
- Trivial config tweaks (allowlist updates, comment fixes) — anything where no DB-affecting code is shipping.

When in doubt, take the backup. They're cheap; corruption isn't.

## POST-deploy: OFFER a "known-good" checkpoint backup

After successfully shipping a major update and confirming the deploy is healthy on-box, **offer Bill a second manual backup**. The offer is one short sentence ("want me to fire a manual backup?") at the end of the deploy summary. **Don't auto-fire** this one — backups touch Drive, hit the SDK quota, and the post-deploy checkpoint is a record Bill wants to author intentionally.

**Why:** Bill called this out 2026-06-04 after the v0.11.12 voicemail / classifier fix shipped. *"going forward - ask to do a backup after a major update like this."* The point: every "known good post-fix" checkpoint is useful as a forensics reference if something else breaks later, and the daily 17:15 backup is often hours away.

**How to apply:**
- After version-bump deploys (v0.X.Y releases), include the offer.
- After incident hotfixes (anything responding to a Bill-flagged failure), include the offer.
- After significant behaviour changes (new feature ships, policy change in production), include the offer.
- Skip the offer for purely cosmetic / docs-only / test-only changes that don't touch runtime behaviour.
- Skip if a scheduled backup has fired in the last ~30 minutes (today's 17:15 is fresh).
- The trigger command is `systemctl --user start ipul-intake-backup.service` (uses the same path as the scheduled fires; logs through journalctl).

Related: [[project-backup-pipeline-live]] for the pipeline details, [[feedback-handle-directly-not-dictate]] for the broader pattern (act after authorization, but ASK when state changes).
