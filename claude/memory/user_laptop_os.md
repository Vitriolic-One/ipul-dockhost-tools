---
name: user-laptop-os
description: "Bill's laptop runs Windows 11 — use Windows Terminal/PowerShell, winget or installer, Windows conventions in cross-machine instructions"
metadata: 
  node_type: memory
  type: user
  originSessionId: 808c8eeb-51be-49ec-a2aa-6e01da1003dd
---

Bill's personal laptop runs **Windows 11**.

(Note: an earlier version of this file said macOS; that was wrong — Bill corrected. Recording the correction here so it doesn't recur.)

When instructions involve running something "on your laptop":

- Terminal: **Windows Terminal** (preinstalled on Win 11) or **PowerShell**. SSH client is built-in OpenSSH (`ssh user@host` works as-is).
- Package manager: **winget** (`winget install …`) for first-party CLI installs. Some tools may need vendor installers.
- Paths use backslashes; line endings are CRLF. If editing files for paste back into dockhost, watch for CRLF→LF conversion (notepad will add CRLF; Bill should use VS Code or paste through Windows Terminal which is generally fine).
- Browser: assume Edge by default; Chrome/Firefox if mentioned.

Related: [[feedback-specific-environment-instructions]] — the general "name the specific environment" rule.
