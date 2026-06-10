#!/usr/bin/env bash
# bootstrap.sh — bring a fresh Debian box from "git clone" to running production.
#
# Idempotent: safe to re-run. Each step checks current state and only
# does the work that hasn't been done yet.
#
# Prerequisites BEFORE running this:
#   1. Docker + docker compose installed and ipul-admin in the docker group.
#   2. Claude Code installed (https://claude.com/code).
#   3. The three repos cloned to ~/:
#        - ipul-intake
#        - ipul-dockhost-tools (this one — pwd should be here)
#        - IPUL-Intake-Docs
#   4. Secrets restored from offline backup:
#        - ~/ipul-intake/.env
#        - ~/ipul-intake/secrets/gmail-service-account.json (chmod 600)
#        - ~/.ssh/github_ipul + github_ipul.pub (chmod 600 / 644)
#   5. systemd --user lingering enabled for ipul-admin so timers fire
#      when no session is open:
#        sudo loginctl enable-linger ipul-admin
#
# Run from this repo's root:
#   cd ~/ipul-dockhost-tools && ./bootstrap.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="$HOME"

log() { printf "\033[1;34m[bootstrap]\033[0m %s\n" "$*" >&2; }
err() { printf "\033[1;31m[FAIL]\033[0m %s\n" "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Phase 1 — sanity checks
# ---------------------------------------------------------------------------

check_prereqs() {
  log "Phase 1: sanity checks"

  command -v docker >/dev/null || err "docker not installed"
  command -v claude >/dev/null || log "  WARNING: claude CLI not in PATH — install before bootstrap completes"
  command -v python3 >/dev/null || err "python3 not installed"
  command -v systemctl >/dev/null || err "systemctl not installed (not a systemd system?)"

  [[ -d "$HOME_DIR/ipul-intake" ]] || err "~/ipul-intake not cloned"
  [[ -d "$HOME_DIR/IPUL-Intake-Docs" ]] || err "~/IPUL-Intake-Docs not cloned"

  [[ -f "$HOME_DIR/ipul-intake/.env" ]] || err ".env missing — restore from offline backup first"
  [[ -f "$HOME_DIR/ipul-intake/secrets/gmail-service-account.json" ]] || err "SA key missing — restore from offline backup first"

  loginctl show-user ipul-admin -p Linger 2>/dev/null | grep -q "Linger=yes" \
    || log "  WARNING: linger not enabled — run: sudo loginctl enable-linger ipul-admin"

  log "Prereqs OK"
}

# ---------------------------------------------------------------------------
# Phase 2 — host-scripts venv
# ---------------------------------------------------------------------------

setup_venv() {
  log "Phase 2: host-scripts venv"

  local venv_dir="$HOME_DIR/ipul-intake-backup/venv"
  mkdir -p "$HOME_DIR/ipul-intake-backup"

  if [[ ! -d "$venv_dir" ]]; then
    log "  creating venv at $venv_dir"
    python3 -m venv "$venv_dir"
  else
    log "  venv exists, reusing"
  fi

  log "  installing/upgrading dependencies from requirements.txt"
  "$venv_dir/bin/pip" install --quiet --upgrade pip
  "$venv_dir/bin/pip" install --quiet -r "$REPO_ROOT/host-scripts/requirements.txt"

  log "  copying scripts to ~/ipul-intake-backup/"
  cp "$REPO_ROOT/host-scripts/backup.py" "$HOME_DIR/ipul-intake-backup/backup.py"
  cp "$REPO_ROOT/host-scripts/publish-docs.py" "$HOME_DIR/ipul-intake-backup/publish-docs.py"
  chmod +x "$HOME_DIR/ipul-intake-backup/backup.py" "$HOME_DIR/ipul-intake-backup/publish-docs.py"

  log "Venv + scripts ready"
}

# ---------------------------------------------------------------------------
# Phase 3 — systemd user units
# ---------------------------------------------------------------------------

install_systemd_units() {
  log "Phase 3: systemd user units"

  local target_dir="$HOME_DIR/.config/systemd/user"
  mkdir -p "$target_dir"

  for unit in ipul-intake-backup.service ipul-intake-backup.timer claude-remote-control.service; do
    cp "$REPO_ROOT/systemd/user/$unit" "$target_dir/$unit"
    log "  installed $unit"
  done

  systemctl --user daemon-reload
  systemctl --user enable --now ipul-intake-backup.timer
  systemctl --user enable claude-remote-control.service \
    || log "  (claude-remote-control.service may need first-time auth — start manually after Claude login)"

  log "  timer status:"
  systemctl --user list-timers ipul-intake-backup.timer --no-pager 2>&1 | sed 's/^/    /'

  log "Systemd units installed and enabled"
}

# ---------------------------------------------------------------------------
# Phase 4 — Claude on-box config
# ---------------------------------------------------------------------------

sync_claude_config() {
  log "Phase 4: Claude on-box config"

  local claude_dir="$HOME_DIR/.claude"
  mkdir -p "$claude_dir/skills/save-session" "$claude_dir/ipul-reference" \
           "$claude_dir/projects/-home-ipul-admin/memory"

  # Top-level settings + CLAUDE.md
  cp "$REPO_ROOT/claude/settings.json" "$claude_dir/settings.json"
  cp "$REPO_ROOT/claude/CLAUDE.md"     "$claude_dir/CLAUDE.md"

  # Skill
  cp "$REPO_ROOT/claude/skills/save-session/SKILL.md" \
     "$claude_dir/skills/save-session/SKILL.md"

  # Operational reference (Slack U-IDs, channel IDs, SF User IDs, lessons)
  cp -r "$REPO_ROOT/claude/ipul-reference/." "$claude_dir/ipul-reference/"

  # Memory entries — restore so future-Claude inherits operational context
  cp -r "$REPO_ROOT/claude/memory/." \
        "$claude_dir/projects/-home-ipul-admin/memory/"

  log "Claude config synced"
}

# ---------------------------------------------------------------------------
# Phase 5 — restore latest DB backup (optional)
# ---------------------------------------------------------------------------

restore_latest_backup() {
  log "Phase 5: restore latest DB backup from Drive (optional)"
  log "  See runbooks/restore-from-backup.md for the recovery flow."
  log "  Skipping inline — explicit operator action required."
}

# ---------------------------------------------------------------------------
# Phase 6 — build + start the intake container
# ---------------------------------------------------------------------------

start_container() {
  log "Phase 6: build + start ipul-intake container"

  cd "$HOME_DIR/ipul-intake"
  docker compose up -d --build

  log "  waiting 8s for startup..."
  sleep 8

  log "  recent container logs:"
  docker logs ipul-intake 2>&1 | tail -10 | sed 's/^/    /'

  log "Container is up. Look for 'Bolt app is running' above to confirm Slack."
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

main() {
  log "======================================"
  log "ipul-dockhost-tools bootstrap starting"
  log "======================================"

  check_prereqs
  setup_venv
  install_systemd_units
  sync_claude_config
  restore_latest_backup
  start_container

  log "======================================"
  log "BOOTSTRAP COMPLETE"
  log "======================================"
  log "Next steps:"
  log "  1. systemctl --user list-timers   # confirm backup timer is active"
  log "  2. docker logs ipul-intake -f     # follow live container logs"
  log "  3. Open Slack #intake-review to confirm bot is connected"
  log ""
  log "If anything looks wrong: runbooks/fresh-box.md has the recovery playbook."
}

main "$@"
