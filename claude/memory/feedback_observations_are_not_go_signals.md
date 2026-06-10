---
name: feedback-observations-are-not-go-signals
description: "Bill's musings, observations, and acknowledgments are NOT go signals. Standing order requires explicit 'go'/'yes'/'do it'. When his reply is ambiguous, propose-and-stop a second time — don't fill the gap by executing."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bcefcd91-35dd-4c26-b825-89768073f856
---

# Observations and acknowledgments are not go signals

When Bill replies to a proposal with an observation, an acknowledgment, a memory ("we already did this once"), or a quiet "ok" that isn't paired with "go"/"yes"/"do it" — that is NOT authorization to start. Standing order from CLAUDE.md is explicit: "WAIT FOR GO ... Questions and musings are not go-aheads. Propose-and-stop." Apply this rigidly when the next step is multi-step / state-changing / a deploy.

**Why:** Bill called this out 2026-06-04. I proposed v0.11.12 (strip HTML for classification, parallel to v0.11.7) ending with *"Want me to ship v0.11.12 now while you reclassify 417 by hand?"* — and read his reply *"ok, we just stripped out html from these to improve detection"* as agreement. Built the whole thing end-to-end. He then said *"you are fixing things before we have discussed them"* and denied the commit. He was musing, not authorizing — he might have been thinking about WHY v0.11.7 didn't already cover this, or processing the find, or any number of things.

**Examples of NOT-a-go-signal (do not act on these):**
- "ok, we just X"
- "yeah, that makes sense"
- "right, so the issue is X"
- "we should look at that"
- "interesting" / "huh"
- "that was probably X"
- A clarifying question back

**Examples of go signals (act):**
- "go" / "go ahead"
- "yes" / "yeah do it"
- "ship it"
- "do it"
- "ok let's do that" / "ok do that"
- An explicit verb-noun directive ("change X to Y", "remove Z")

**How to apply:**
- After any proposal that includes a deploy / multi-file change, end with a yes/no question and STOP.
- If Bill replies and the reply is ambiguous, re-confirm with one short question ("So, go?") before touching the disk.
- For investigation / read-only work, ambiguous "ok" is fine — looking is not acting.
- For state-changing work, ambiguous "ok" requires a second confirmation.

Related: [[feedback-handle-directly-not-dictate]] (default to doing when authorized) and [[feedback-proactive-allowlist]] (reduce friction) — neither overrides WAIT FOR GO. Doing-directly applies to the HOW after the go, not WHETHER to proceed.
