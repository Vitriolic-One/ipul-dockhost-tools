---
name: feedback-task-list-screen-real-estate
description: Bill values terminal screen real estate; do not accumulate large task lists or leave them displayed
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 808c8eeb-51be-49ec-a2aa-6e01da1003dd
---

Bill is sensitive to screen space taken by the persistent task list at the bottom of the Claude Code TUI. He has said it "eats a fifth of the screen" when full.

**Why:** He is working in a single terminal session on dockhost and needs the working area for inspecting commands, logs, and tool output. The persistent task list compresses that area noticeably.

**How to apply:**
- Be sparing with `TaskCreate`. Use it only when a workflow genuinely benefits from tracking (≥4 steps, work across multiple turns, parallel work that risks getting lost). For 1–3 step linear work, just do the steps.
- Promptly delete (`status: deleted`) tasks that are no longer relevant — completed tasks accumulate visual clutter even when their status is "completed."
- When a task list grows past ~3–4 visible rows, ask before adding more. Consider sweeping completed/stale entries.
- If a session is wrapping up and tasks served their purpose, clear them.
