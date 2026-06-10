---
name: claude-remote-control-setup
description: "Two non-obvious gates when running `claude remote-control` headlessly as a systemd service on ipul-dockhost — and how the service is wired"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9314e4cc-3cae-4a2e-9b75-56bd80347f2a
---

When running `claude remote-control` as a non-interactive daemon (e.g. systemd user service), expect TWO gates that interactive sessions don't hit:

1. **Workspace trust flag** — `claude` reads `~/.claude.json` and checks `projects["<cwd>"].hasTrustDialogAccepted`. Interactive runs auto-bypass this via TTY heuristic without flipping the flag, so a headless run still fails with `Error: Workspace not trusted` even after the user has "accepted" interactively. Fix: directly set that key to `true` in `~/.claude.json` for the launch dir (atomic write).
2. **`Enable Remote Control? (y/n)` prompt** — fires on every launch (not persisted). Headless stdin is `/dev/null`, the prompt sees EOF and the process exits cleanly (status 0). Fix: pipe `y` in via the unit file: `ExecStart=/bin/bash -c "printf 'y\n' | /usr/bin/claude remote-control --name ipul-dockhost"`.

The live service is `~/.config/systemd/user/claude-remote-control.service` (user-mode, lingered via `sudo loginctl enable-linger ipul-admin`). `journalctl --user -u claude-remote-control` for logs. Network is outbound-only to Anthropic; no inbound ports.

**Why:** today (2026-06-02) we set this up for browser access via claude.ai/code; debugging the two gates took ~20 minutes because the error messages point at user intervention that doesn't actually fix it.

**How to apply:** if `claude remote-control` ever fails to start on this box (or on a sibling box being newly set up), check the trust flag and the y-pipe before re-installing or running `claude /login`. If the service is restart-looping with status=1, it's the trust flag; if status=0 (clean exit) it's the stdin prompt.

Related: [[post-cutover-state-2026-06-02]]
