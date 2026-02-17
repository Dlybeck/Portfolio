#!/usr/bin/env bash
set -euo pipefail

OPENCODE_PORT="${OPENCODE_PORT:-4096}"
OPENHANDS_PORT="${OPENHANDS_PORT:-3000}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

is_port_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltnp 2>/dev/null | grep -q ":${port} "
  elif command -v netstat >/dev/null 2>&1; then
    netstat -ltnp 2>/dev/null | grep -q ":${port} "
  else
    return 1
  fi
}

detect_pid_by_name() {
  local name="$1"
  pgrep -f "$name" | grep -v "manage-services.sh" | grep -v "$$" | head -n 1 || true
}

start_opencode() {
  local port="$OPENCODE_PORT"
  if is_port_listening "$port"; then
    log "OpenCode already listening on port $port"
    return 0
  fi
  local pid
  pid=$(detect_pid_by_name 'opencode')
  if [ -n "$pid" ]; then
    log "OpenCode process detected (pid $pid)."
    return 0
  fi
  if command -v opencode >/dev/null 2>&1; then
    opencode &
    pid=$!
    log "Starting OpenCode (opencode) with pid $pid"
  elif [ -x "./bin/opencode" ]; then
    "./bin/opencode" &
    pid=$!
    log "Starting OpenCode (bin/opencode) with pid $pid"
  elif [ -x "./open-code/start.sh" ]; then
    "./open-code/start.sh" &
    pid=$!
    log "Starting OpenCode via open-code/start.sh with pid $pid"
  else
    log "OpenCode start command not found. OpenCode may not be installed locally."
    return 1
  fi
  for i in {1..12}; do
    sleep 0.5
    if is_port_listening "$port"; then
      log "OpenCode started and listening on port $port (pid $pid)"
      return 0
    fi
  done
  log "OpenCode failed to listen on port $port after start attempt."
  return 1
}

start_openhands() {
  local port="$OPENHANDS_PORT"
  if is_port_listening "$port"; then
    log "OpenHands already listening on port $port"
    return 0
  fi
  local pid
  pid=$(detect_pid_by_name 'openhands|OpenHands')
  if [ -n "$pid" ]; then
    log "OpenHands process detected (pid $pid)."
    return 0
  fi
  if command -v openhands >/dev/null 2>&1; then
    openhands &
    pid=$!
    log "Starting OpenHands (openhands) with pid $pid"
  elif [ -x "./scripts/openhands_start.sh" ]; then
    "./scripts/openhands_start.sh" &
    pid=$!
    log "Starting OpenHands via scripts/openhands_start.sh with pid $pid"
  else
    log "OpenHands start command not found. OpenHands may not be installed locally."
    return 1
  fi
  for i in {1..12}; do
    sleep 0.5
    if is_port_listening "$port"; then
      log "OpenHands started and listening on port $port (pid $pid)"
      return 0
    fi
  done
  log "OpenHands failed to listen on port $port after start attempt."
  return 1
}

stop_opencode() {
  local pids
  pids=$(pgrep -f "opencode" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    log "Stopping OpenCode (pids: $pids)"
    kill -TERM $pids 2>/dev/null || true
    for i in {1..12}; do
      sleep 0.5
      if ! pgrep -f "opencode" >/dev/null; then
        log "OpenCode stopped gracefully"
        break
      fi
    done
  else
    log "OpenCode not running."
  fi
}

stop_openhands() {
  local pids
  pids=$(pgrep -f "openhands|OpenHands" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    log "Stopping OpenHands (pids: $pids)"
    kill -TERM $pids 2>/dev/null || true
    for i in {1..12}; do
      sleep 0.5
      if ! pgrep -f "openhands|OpenHands" >/dev/null; then
        log "OpenHands stopped gracefully"
        break
      fi
    done
  else
    log "OpenHands not running."
  fi
}

report_status() {
  local oc_pid oc_port
  oc_pid=$(pgrep -f "opencode" 2>/dev/null || true)
  oc_port="$OPENCODE_PORT"
  log "OpenCode: pid=${oc_pid:-none}, port=${oc_port}"
  if is_port_listening "$oc_port"; then
    log "OpenCode: port $oc_port listening"
  else
    log "OpenCode: port $oc_port not listening"
  fi

  local oh_pid oh_port
  oh_pid=$(pgrep -f "openhands|OpenHands" 2>/dev/null || true)
  oh_port="$OPENHANDS_PORT"
  log "OpenHands: pid=${oh_pid:-none}, port=${oh_port}"
  if is_port_listening "$oh_port"; then
    log "OpenHands: port $oh_port listening"
  else
    log "OpenHands: port $oh_port not listening"
  fi
}

usage() {
  cat <<'HELP'
Usage: scripts/manage-services.sh <command>

Commands:
- start-opencode   - Start OpenCode (port 4096)
- stop-opencode    - Stop OpenCode
- start-openhands  - Start OpenHands (port 3000)
- stop-openhands   - Stop OpenHands
- status           - Show status of both services
- restart          - Stop all then start both (best-effort)
- help             - Show this help
HELP
}

main() {
  if [ "$#" -lt 1 ]; then
    usage
    exit 0
  fi
  case "$1" in
    start-opencode) start_opencode ;;
    stop-opencode) stop_opencode ;;
    start-openhands) start_openhands ;;
    stop-openhands) stop_openhands ;;
    status) report_status ;;
    restart)
      stop_opencode
      stop_openhands
      sleep 0.5
      start_opencode
      start_openhands
      ;;
    help|*) usage ;;
  esac
}

main "$@"
