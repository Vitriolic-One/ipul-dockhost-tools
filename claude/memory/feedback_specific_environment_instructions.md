---
name: feedback-specific-environment-instructions
description: "When telling Bill to run a command \"on your laptop\" or \"in another terminal\", name the specific app/shell, not a generic hand-wave"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 808c8eeb-51be-49ec-a2aa-6e01da1003dd
---

When giving instructions that involve Bill running something somewhere other than the current shared dockhost session, **be specific about the target environment**. "Run this on your laptop" or "open another terminal" is not enough — he asked back with "do it where on my laptop?"

**Why:** He's running multiple environments (dockhost via shared Claude Code session, his laptop, possibly other boxes) and the instructions need to clearly identify which shell and which OS conventions apply. Generic instructions cost a round trip.

**How to apply:**
- Name the specific terminal app for the laptop (e.g., "Terminal.app on macOS", "PowerShell on Windows", "iTerm2 if you use it") — and if you don't know the OS, ask once.
- If a command differs by OS (e.g., `brew install` vs `apt install` vs `winget`), give the matching one for his OS, not a "or equivalent" wave.
- Memory does not currently record Bill's laptop OS. If it becomes load-bearing for a workflow, save it.
