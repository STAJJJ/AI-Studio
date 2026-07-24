#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
CONDA_ENV_NAME="${AI_STUDIO_CONDA_ENV:-studio}"
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8002"
FRONTEND_HOST="127.0.0.1"
FRONTEND_PORT="3000"
COMFYUI_BASE_URL="${COMFYUI_BASE_URL:-http://127.0.0.1:8188}"
COMFYUI_HOME="${COMFYUI_HOME:-/Users/lyj/WorkStation/Project/ComfyUI}"
RUNTIME_DIR="$PROJECT_ROOT/scripts/.runtime"
COMFYUI_LOG="$RUNTIME_DIR/comfyui.log"

backend_pid=""
frontend_pid=""
comfyui_pid=""
comfyui_started=false
cleaned_up=false

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

print_port_owner() {
  local port="$1"
  local pid
  pid="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [[ -n "$pid" ]]; then
    printf 'Port %s is already in use.\n' "$port" >&2
    printf 'PID: %s\n' "$pid" >&2
    printf 'Command: %s\n' "$(ps -p "$pid" -o command= 2>/dev/null || printf 'unknown')" >&2
    return 1
  fi
}

activate_conda() {
  if [[ "${CONDA_DEFAULT_ENV:-}" == "$CONDA_ENV_NAME" ]]; then
    return
  fi
  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate "$CONDA_ENV_NAME"
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local pid="$3"
  local attempts="$4"
  local attempt

  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if curl --silent --fail --max-time 2 "$url" >/dev/null; then
      return 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      printf '%s exited before becoming ready.\n' "$name" >&2
      return 1
    fi
    sleep 1
  done
  printf '%s did not become ready: %s\n' "$name" "$url" >&2
  return 1
}

terminate_process_tree() {
  local pid="$1"
  local child_pid

  if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
    return
  fi

  while IFS= read -r child_pid; do
    if [[ -n "$child_pid" ]]; then
      terminate_process_tree "$child_pid"
    fi
  done < <(pgrep -P "$pid" 2>/dev/null || true)

  kill "$pid" 2>/dev/null || true
}

cleanup() {
  if [[ "$cleaned_up" == true ]]; then
    return
  fi
  cleaned_up=true
  trap - INT TERM EXIT

  terminate_process_tree "$frontend_pid"
  terminate_process_tree "$backend_pid"
  for pid in "$frontend_pid" "$backend_pid"; do
    if [[ -n "$pid" ]]; then
      wait "$pid" 2>/dev/null || true
    fi
  done
  if [[ "$comfyui_started" == true ]] && [[ -n "$comfyui_pid" ]] && kill -0 "$comfyui_pid" 2>/dev/null; then
    terminate_process_tree "$comfyui_pid"
    wait "$comfyui_pid" 2>/dev/null || true
  fi
}

handle_signal() {
  printf '\nStopping AI Studio...\n'
  cleanup
  exit 130
}

trap handle_signal INT TERM
trap cleanup EXIT

require_command conda
require_command curl
require_command lsof
require_command npm
require_command pgrep
activate_conda
COMFYUI_PYTHON="${COMFYUI_PYTHON:-$(command -v python)}"

print_port_owner "$FRONTEND_PORT"
print_port_owner "$BACKEND_PORT"
mkdir -p "$RUNTIME_DIR"

if curl --silent --fail --max-time 3 "${COMFYUI_BASE_URL%/}/system_stats" >/dev/null; then
  comfyui_pid="$(lsof -nP -tiTCP:8188 -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  printf 'Reusing local ComfyUI at %s%s\n' "$COMFYUI_BASE_URL" "${comfyui_pid:+ (PID $comfyui_pid)}"
else
  occupied_pid="$(lsof -nP -tiTCP:8188 -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [[ -n "$occupied_pid" ]]; then
    printf 'Port 8188 is occupied but the ComfyUI health check failed.\n' >&2
    printf 'PID: %s\n' "$occupied_pid" >&2
    printf 'Command: %s\n' "$(ps -p "$occupied_pid" -o command= 2>/dev/null || printf 'unknown')" >&2
    exit 1
  fi

  if [[ ! -f "$COMFYUI_HOME/main.py" ]]; then
    printf 'ComfyUI is not installed at %s.\n' "$COMFYUI_HOME" >&2
    printf 'See: %s/docs/mac-local-image-generation.md\n' "$PROJECT_ROOT" >&2
    exit 1
  fi
  if ! "$COMFYUI_PYTHON" -c 'import aiohttp, torch' >/dev/null 2>&1; then
    printf 'ComfyUI dependencies are unavailable in Python: %s\n' "$COMFYUI_PYTHON" >&2
    printf 'Install %s/requirements.txt in the %s environment.\n' "$COMFYUI_HOME" "$CONDA_ENV_NAME" >&2
    exit 1
  fi

  printf 'Starting local ComfyUI from %s\n' "$COMFYUI_HOME"
  (
    cd "$COMFYUI_HOME"
    "$COMFYUI_PYTHON" main.py --listen 127.0.0.1 --port 8188
  ) >"$COMFYUI_LOG" 2>&1 &
  comfyui_pid="$!"
  comfyui_started=true

  if ! wait_for_url "ComfyUI" "${COMFYUI_BASE_URL%/}/system_stats" "$comfyui_pid" 120; then
    printf 'ComfyUI log: %s\n' "$COMFYUI_LOG" >&2
    tail -n 40 "$COMFYUI_LOG" >&2 || true
    exit 1
  fi
fi

mkdir -p "$PROJECT_ROOT/data/uploads" "$PROJECT_ROOT/data/outputs"

printf 'Starting AI Studio with Python: %s\n' "$(command -v python)"
printf 'ComfyUI: %s\n' "$COMFYUI_BASE_URL"

cd "$BACKEND_DIR"
COMFYUI_BASE_URL="$COMFYUI_BASE_URL" python -m uvicorn app.main:app \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT" &
backend_pid="$!"

cd "$FRONTEND_DIR"
AI_STUDIO_API_BASE_URL="http://$BACKEND_HOST:$BACKEND_PORT" npm run dev -- \
  --hostname "$FRONTEND_HOST" \
  --port "$FRONTEND_PORT" &
frontend_pid="$!"

if ! wait_for_url "FastAPI" "http://$BACKEND_HOST:$BACKEND_PORT/api/v1/health" "$backend_pid" 60; then
  exit 1
fi
if ! wait_for_url "Next.js" "http://$FRONTEND_HOST:$FRONTEND_PORT" "$frontend_pid" 120; then
  exit 1
fi

cat <<EOF

AI Studio started successfully.
Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT (PID $frontend_pid)
Backend:  http://$BACKEND_HOST:$BACKEND_PORT/docs (PID $backend_pid)
ComfyUI:  $COMFYUI_BASE_URL
ComfyUI log: $COMFYUI_LOG
Press Ctrl+C to stop services started by this script.
EOF

while true; do
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    printf 'FastAPI exited unexpectedly; stopping Next.js.\n' >&2
    exit 1
  fi
  if ! kill -0 "$frontend_pid" 2>/dev/null; then
    printf 'Next.js exited unexpectedly; stopping FastAPI.\n' >&2
    exit 1
  fi
  if [[ -n "$comfyui_pid" ]] && ! kill -0 "$comfyui_pid" 2>/dev/null; then
    printf 'ComfyUI exited unexpectedly; stopping AI Studio.\n' >&2
    exit 1
  fi
  sleep 1
done
