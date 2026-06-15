# Claude Code Permissions — Blueprint for Streamlining the "Click Yes" Train
<!-- v1.0 — 2026-06-15. Authored on Bill's Windows box (claude-opus-4-8) for the on-box IPUL maintainer ("the brother") running native on Linux. Framework + our concrete setup + a native-Linux starter config. -->

> **Purpose:** explain how Claude Code's permission system actually works, how we tamed the prompt train on Bill's machine, and how to adapt that to a native-Linux box. Hand this to the on-box maintainer. The *framework* is identical across platforms; only the paths and the specific allowed commands differ.
>
> Snapshotted into the org tools repo on 2026-06-15 from the document Bill pasted into the on-box Claude session. The on-box `~/.claude/settings.json` was tuned to match the framework that same day — see the version history of `claude/settings.json` in this repo for the concrete native-Linux config that landed.

---

## TL;DR — the three levers

1. **`defaultMode: "acceptEdits"`** — kills most edit prompts. Auto-accepts `Edit`/`Write` **and** the common filesystem Bash commands (`mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed`) for any path inside the working directory or `additionalDirectories`. Independent of the allow-list. **Read only at startup — a restart is required; `/compact` does NOT re-read it.**
2. **`permissions.allow`** — an allow-list that mops up the *other* prompts: arbitrary `Bash(...)` commands and MCP tools you run repeatedly (git, docker, pytest, the deploy script, etc.).
3. **`additionalDirectories`** — extends the no-prompt file scope to paths *outside* the project (the Docker volume, a backups dir, secrets), so acceptEdits and reads apply there too.

Set #1, populate #2 with your real commands, list out-of-project paths in #3, **restart**, done.

---

## The mental model: two independent gates

A tool call passes through **two separate checks**. This trips people up — clearing one does not clear the other.

- **Gate 1 — Permission rules + mode.** The `permissions.allow`/`deny`/`ask` lists plus the active permission `mode`. This is what `acceptEdits` and the allow-list control.
- **Gate 2 — Per-file "first touch" trust gate.** The *first* time an `Edit`/`Write` lands on a given file in a session, Claude Code asks for explicit approval — **this is NOT suppressible by allow rules or by `acceptEdits`.** Once you approve a file, subsequent edits to that same file in the same session don't re-prompt.

> **Platform note for the brother:** On Windows, Gate 2 misbehaves on UNC network paths (`\\host\share\...`) — parallel edits each look like "first touch" and re-prompt even with acceptEdits on. **On a native-Linux local repo this does not happen** — you'll see at most one trust prompt per file per session, then silence. This is one of the prompt sources you simply won't inherit.

---

## Settings files: locations & precedence

| Scope | Path | Notes |
|---|---|---|
| Managed | (org-deployed) | Cannot be overridden. Usually absent on a personal box. |
| **Local** | `<project>/.claude/settings.local.json` | Highest editable precedence. Gitignored by default — personal/secret-bearing. |
| **Project** | `<project>/.claude/settings.json` | Shared/committed project settings. |
| **User** | `~/.claude/settings.json` | Applies to all projects for this user. |

**How they combine for permissions:**
- Permission **rules MERGE (union)** across all scopes — they do **not** override each other. A command allowed in *any* file is allowed (unless denied — see next).
- **`deny` beats `allow` everywhere.** A deny at any scope blocks a matching allow at any other scope. Evaluation order on the merged set is: **deny → ask → allow.**
- Practical rule of thumb: it doesn't matter much *which* file you add an allow to — but put machine-specific / secret-bearing entries in **local** (gitignored), and shareable ones in **project** or **user**. When in doubt, local is safe.

> `defaultMode: "auto"` is special — it is ignored if set in project/local settings (only honored in `~/.claude/settings.json`), so a repo can't grant itself auto mode. `acceptEdits` has no such restriction.

---

## Permission modes (`defaultMode`)

| Mode | What it does |
|---|---|
| `default` | Prompts on first use of each tool; read-only commands run without asking. |
| **`acceptEdits`** | **Auto-accepts file edits + safe FS Bash commands (`mkdir`/`touch`/`rm`/`rmdir`/`mv`/`cp`/`sed`) within working dir + `additionalDirectories`.** The workhorse for reducing prompts. |
| `plan` | Read-only; proposes changes without executing. Good for "look before you touch." |
| `bypassPermissions` | Disables all prompts/safety checks. **Only for isolated containers/VMs.** Even then, explicit `ask` rules and root/home `rm -rf` still prompt as a circuit-breaker. |

**Switching:** `Shift+Tab` cycles `default → acceptEdits → plan` live (temporary, this session only). `defaultMode` in settings sets the *starting* mode and is read **only at process startup** — change it, then restart (`claude -c`) to apply. `/compact` does not count (same process).

**What acceptEdits will NOT auto-accept (always prompts):**
- Writes to **protected paths**: `.git/`, `.claude/`, `.vscode/`, `.idea/`, `.npmrc`, `.gitconfig`, `.bashrc`, etc.
- Arbitrary Bash beyond the named FS commands (that's the allow-list's job).
- MCP tools, network requests.
- Anything outside working dir + `additionalDirectories`.

---

## Rule syntax cheat-sheet

**Bash:**
- `Bash(git status*)` — prefix match.
- `Bash(ls *)` — the **space before `*` enforces a word boundary** (matches `ls -la`, not `lsof`).
- `Bash(ls*)` — no space, no boundary (matches `lsof` too).
- `Bash(pytest:*)` — the `:*` suffix is equivalent to `(pytest *)` (trailing wildcard).
- Compound commands (`a && b`, `a | b`) are evaluated **per-subcommand** — each needs to match.
- Wrappers `timeout`/`nice`/`nohup`/`time`/`stdbuf` are stripped before matching, so `Bash(npm test *)` also covers `timeout 30 npm test`.
- Read-only commands (`ls`, `cat`, `grep`, `find`, `head`, `tail`, `wc`, `pwd`, `which`, `diff`, `stat`, read-only `git`) are auto-approved without any rule.

**Paths (Read/Edit/Glob/Grep):** gitignore-style.
- `//abs/path/**` — absolute from filesystem root.
- `~/path/**` — from home.
- `/path/**` — relative to **project root**.
- `path` / `./path` — relative to current dir.
- `*` within a segment, `**` across directories.

**MCP tools:**
- `mcp__<server>__<tool>` — one specific tool.
- `mcp__<server>__*` — **all tools from that server** (allow-lists require the literal `mcp__server__` prefix before the `*`; a bare `*` or `mcp__*` is rejected in allow-lists, though `mcp__*` works for deny/ask).
- exec vs sudo-exec are just separate tool names — `mcp__ssh-host__exec` and `mcp__ssh-host__sudo-exec`; the `mcp__ssh-host__*` wildcard covers both.

---

## `additionalDirectories`

Grants no-prompt **file access** to paths outside the working directory. Reads become silent; edits there follow the current mode (auto in `acceptEdits`). Configure persistently:

```json
"permissions": {
  "additionalDirectories": ["/srv/ipul-data", "/home/ipul-admin/ipul-intake-backup"]
}
```

Or per-session with `/add-dir <path>`, or at launch with `--add-dir <path>`. Note: it grants *file access* only — it does **not** load `.claude/` config, skills, or CLAUDE.md from those dirs.

---

## How we set it up on Bill's home box (the working reference)

On Bill's box the prompt train was eliminated with this combination (Windows specifics elided):

1. **`"defaultMode": "acceptEdits"`** in **both** `~/.claude/settings.json` and the project `.claude/settings.local.json` (so whichever loads, the starting mode is right). **This was the single highest-impact change** — before it, every `Edit`/`Write` prompted.
2. A broad **`permissions.allow`** list of the Bash commands we actually run a lot — git (status/log/diff/add/commit/push/pull/checkout/reset), python/pytest, docker, plus the standard file utilities — written as prefix rules (`Bash(git commit *)`, `Bash(docker *)`, …).
3. **MCP servers allow-listed with wildcards** — e.g. `mcp__homeassistant__*`, `mcp__ssh-dockhost__*` (and the `exec` + `sudo-exec` pair each server exposes). Lesson learned: when you add a new MCP server, add its `mcp__server__*` wildcard proactively or every call prompts.
4. **`additionalDirectories`** listing every path outside the working dir we edit (on Windows: the mapped drives + network shares).
5. **Restart** after changing `defaultMode` — it's only read at startup.

The remaining unavoidable prompts on the home box are Gate-2 per-file trust prompts on **UNC network paths** — a Windows-network artifact the brother won't have on local Linux files.

---

## Translate for native Linux (the brother's starter)

Drop this into `<repo>/.claude/settings.local.json` (gitignored), adjust paths/commands to your box, then **restart Claude Code**. Everything here is the framework above, instantiated for the deploy loop (test → commit → push → docker rebuild).

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Read", "Glob", "Grep", "Edit", "Write",

      "Bash(git status*)", "Bash(git log*)", "Bash(git diff*)", "Bash(git show*)",
      "Bash(git add *)", "Bash(git commit *)", "Bash(git push *)", "Bash(git pull*)",
      "Bash(git fetch*)", "Bash(git checkout *)", "Bash(git reset *)", "Bash(git stash*)",

      "Bash(docker *)", "Bash(docker compose *)", "Bash(docker-compose *)",
      "Bash(bash scripts/deploy.sh*)", "Bash(./scripts/deploy.sh*)",

      "Bash(venv/bin/python *)", "Bash(venv/bin/pytest *)",
      "Bash(python *)", "Bash(python3 *)", "Bash(pip *)",

      "Bash(ls *)", "Bash(cat *)", "Bash(grep *)", "Bash(find *)", "Bash(tail *)",
      "Bash(head *)", "Bash(mkdir *)", "Bash(cp *)", "Bash(mv *)", "Bash(rm *)"
    ],
    "additionalDirectories": [
      "/home/ipul-admin/ipul-intake-backup"
    ]
  }
}
```

**Adjust before using:**
- **Repo path / venv path:** if your venv is `.venv/` or elsewhere, fix the `venv/bin/...` rules. If you invoke python by absolute path, allow that exact prefix.
- **Docker & sudo:** if your user is in the `docker` group, `Bash(docker *)` is enough. If you run `sudo docker`, add `Bash(sudo docker *)` and `Bash(sudo docker compose *)` — sudo changes the command string, so the non-sudo rule won't match it.
- **Deploy script:** match however you actually invoke it. Per-subcommand evaluation means a deploy script that *internally* runs docker/git is fine (the script is one allowed command); but commands you type *at the prompt* each need their own rule.
- **`additionalDirectories`:** add the Docker named-volume host path, the backups dir, and the `secrets/` dir if they live outside the repo — anything you read/write that isn't under the working directory.
- **MCP:** if the brother uses any MCP servers, add `mcp__<server>__*` per server (and remember `exec`/`sudo-exec` are covered by the wildcard).

**What you will NOT need (Windows-only here):** drive-letter rules (`Y:\*`), UNC rules (`\\host\*`), PowerShell rules. Skip all of it.

---

## Verification & gotchas

- **After editing `defaultMode`: restart.** Confirm by watching whether the first `Edit` of a session prompts. If it still prompts, the mode didn't load (you're in the same process, or the file has a syntax error).
- **First edit of each file still prompts once** (Gate 2) even in acceptEdits — that's expected and not fixable; it won't repeat for that file in-session.
- **Protected paths always prompt** (`.git/`, `.claude/`, dotfiles) — by design.
- **`deny` wins.** If something you allowed still gets blocked, search every settings file for a matching `deny`.
- **Validate JSON.** A trailing comma or bad escape silently drops the whole settings file — `python3 -m json.tool .claude/settings.local.json` to check.
- **Don't reach for `bypassPermissions`** on a production host. acceptEdits + a tuned allow-list gets you ~99% of the way with the safety rails intact.

---

## How this maps onto the on-box (ipul-dockhost) configuration

The native-Linux starter above was applied to `~/.claude/settings.json` on 2026-06-15 with these specific decisions:

- **`defaultMode: "acceptEdits"`** — landed. Single biggest reduction in prompts.
- **`additionalDirectories: ["/tmp"]`** — minimal. The working directory is `/home/ipul-admin/`, so `ipul-intake/`, `IPUL-Intake-Docs/`, `ipul-dockhost-tools/`, `ipul-intake-backup/`, `.config/systemd/user/` are all already in scope. `/tmp` is the only place probe scripts regularly land outside the home tree.
- **Allowlist additions on top of what was already there:** `git checkout *`, `git reset *`, `git stash*`, `python *`, `python3 *`, `pip *`, broader `docker *` / `docker compose *` catch-alls. The existing specific entries (`docker exec *`, `docker ps:*`, etc.) stay as redundant safety; not harmful.
- **`Bash(rm *)` deliberately NOT added to blanket allow.** Rationale: with `acceptEdits` mode on, `rm` is already auto-accepted WITHIN working dir + additionalDirectories. `rm` OUTSIDE those paths still prompts as a safety net. And the `feedback-autonomy-after-go` memory entry (also 2026-06-15) explicitly lists file/directory deletion as "truly destructive" — a behavioral guardrail above the permission gate.
- **MCP wildcards not added** — the on-box Claude rarely exercises MCP tools (the SA + venv path is used directly). If MCP usage picks up later, add `mcp__<server>__*` per server.
- **No `sudo docker *` entries** — `ipul-admin` is in the docker group; the bare `docker *` rule is sufficient.

Restart required for `defaultMode` to take effect. The new configuration sits in the live `~/.claude/settings.json`; the next time Claude Code restarts on this box (`systemctl --user restart claude-remote-control` or a fresh session), the prompt train should drop dramatically.
