---
name: save-session
description: Snapshot the current Claude Code conversation to a labeled file under ~/.claude/saved-sessions/ — copies the raw JSONL transcript and writes a human-readable markdown summary alongside it. Use when Bill says /save-session, /save session, or asks to save / snapshot / checkpoint the current conversation. Works from remote control surfaces where the terminal-local /save-session command isn't reachable.
tools: Bash, Read, Write, Glob
---

# Save Session

Snapshot the active Claude Code session to a labeled, durable record under `~/.claude/saved-sessions/`. Built because Claude Code's terminal-local `/save-session` command isn't reachable from the remote-control (claude.ai) surface.

## Args

`/save-session [optional-label]` — args is a free-text label (kebab-case preferred) describing what this session is about. If omitted, derive a short label from the most prominent thread in the conversation (e.g. `incident-response`, `v0.11.12-deploy`, `morning-standby`).

## Steps to perform on invocation

1. **Identify the current session's JSONL.**
   - Run `ls -t ~/.claude/projects/-home-ipul-admin/*.jsonl 2>/dev/null | head -1` to find the most-recently-modified jsonl. That's the active session being appended to as we talk.
   - Sanity check: the file's `mtime` should be within the last few minutes; if not, something's off — surface a warning rather than silently saving a stale file.

2. **Build the snapshot filename.**
   - Pattern: `<YYYY-MM-DD-HHMM>-<label>.jsonl` using Mountain time.
   - Get the current MDT time via `date "+%Y-%m-%d-%H%M"` (host is on America/Denver, so local clock = Mountain).
   - If no label was passed, choose one based on conversation context — keep it under 30 chars, kebab-case, descriptive.

3. **Copy the JSONL.**
   - `cp <source-jsonl> ~/.claude/saved-sessions/<filename>.jsonl`
   - Pure copy. The original keeps living and being appended to — don't move it.

4. **Write the markdown summary.**
   - Path: `~/.claude/saved-sessions/<filename>-summary.md`
   - Structure:
     - `# Session Summary — <label> (<date>)` header
     - **Overview**: 1-2 sentence framing of what this session covered.
     - **Major decisions / commits**: bullet list of code changes, version bumps, deploys, behaviour changes — pull from git log and from the conversation. Include commit SHAs and Change Log entry titles where relevant.
     - **Open threads / awaiting follow-up**: things that weren't fully closed.
     - **Standing rules captured to memory this session**: list any `feedback-*.md` files created in `~/.claude/projects/-home-ipul-admin/memory/`.
     - **Pointer**: filename of the raw JSONL alongside this summary.
   - Tone: factual, dense, skimmable. Bill prefers terse. Don't pad with adjectives.

5. **Report results in chat.**
   - One line per artifact saved (jsonl + summary).
   - Include the labels and full paths so Bill can grep / open from anywhere.
   - **Do not also fire /compact** — that's a Claude Code built-in command and can't be triggered from a skill. If Bill wants to compact afterward, he types it himself. Note this in the report if he asked for "save + compact" so he knows to follow up.

## Constraints

- This skill makes ONE state-changing action (the `cp`) and one Write (the summary). Both are local, low-risk, and reversible (just delete the saved files).
- Does not touch the active JSONL.
- Does not push to Drive (separate decision; can be a future enhancement).
- Does not auto-cleanup `~/.claude/saved-sessions/` — if the directory grows large, that's a future cleanup decision.

## Failure modes to handle gracefully

- No `.jsonl` files found at the projects path → report that and stop; nothing to save.
- Active JSONL's mtime is stale (>1 hour) → warn but still save (Bill may genuinely be checkpointing an idle session).
- `~/.claude/saved-sessions/` doesn't exist → create it (`mkdir -p`) before copying.
