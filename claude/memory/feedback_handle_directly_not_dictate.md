---
name: feedback-handle-directly-not-dictate
description: "Bill prefers Claude executes commands directly rather than dictating them — he typically mistypes. Leave him as the fallback \"this is easier\" option only when truly necessary."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bcefcd91-35dd-4c26-b825-89768073f856
---

# Handle it directly — don't make Bill type things

When something can be done from this box's tools (Bash, Edit, Write, scripts, API calls), Claude should do it directly. Reserve "Bill, paste this into your browser / terminal" for steps that genuinely require it (e.g. acting on assets Claude can't touch — Bill-owned Drive files the SA can't delete, browser-only UI actions, decisions Claude shouldn't make unilaterally).

**Why:** Bill stated on 2026-06-03: "anything that you can do I prefer you handle — leave me as a 'dude, shut up, this is easier' option because I typically mistype stuff." Mistyped commands waste time and introduce subtle bugs (wrong path, missing flag, swapped chars in a Drive ID). This reinforces the existing CLAUDE.md standing order "default to doing, not dictating copy-paste" with a concrete reason.

**How to apply:**
- Default to executing the tool call yourself, not showing Bill the command to run.
- Use `Bash` / `Edit` / `Write` / API scripts rather than producing "now run `cmd`" prose blocks.
- If a step genuinely requires Bill (e.g. browser-only UI, owns-the-resource permission gap, irreversible decision), bundle it explicitly: "this one needs you because X — do Y."
- The standing rule "WAIT FOR GO before state-changing actions" still applies; this is about HOW once the go is given, not WHETHER to proceed.

Related: complements [[feedback-copyable-items-standalone]] (when Bill DOES need to copy something, make it cleanly copyable).
