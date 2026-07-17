#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
DATA_DIR="$ROOT_DIR/data"

BACKEND_HOST="${AI_STUDIO_BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${AI_STUDIO_BACKEND_PORT:-8002}"
FRONTEND_HOST="${AI_STUDIO_FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${AI_STUDIO_FRONTEND_PORT:-3000}"
CONDA_ENV_NAME="${AI_STUDIO_CONDA_ENV:-studio}"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo
  echo "Stopping AI Studio development services..."
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

activate_conda_env() {
  if [[ -n "${CONDA_DEFAULT_ENV:-}" && "$CONDA_DEFAULT_ENV" == "$CONDA_ENV_NAME" ]]; then
    return
  fi
  if command -v conda >/dev/null 2>&1; then
    # shellcheck disable=SC1090
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_NAME"
  else
    echo "Conda was not found. Continuing with current Python: $(command -v python)" >&2
  fi
}

echo "Preparing AI Studio development environment..."
require_command python
require_command npm
activate_conda_env

mkdir -p "$DATA_DIR/uploads" "$DATA_DIR/outputs"
touch "$DATA_DIR/uploads/.gitkeep" "$DATA_DIR/outputs/.gitkeep"

if [[ ! -f "$ROOT_DIR/.env" && ! -f "$BACKEND_DIR/.env" ]]; then
  echo "No local .env found. Copy .env.example to .env and configure runtime values when using Chat, ComfyUI, or FaceFusion."
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run: cd frontend && npm install" >&2
  exit 1
fi

rm -rf "$FRONTEND_DIR/.next"

python - <<'PY'
try:
    import fastapi  # noqa: F401
    import sqlalchemy  # noqa: F401
except ModuleNotFoundError as exc:
    raise SystemExit(f"Backend dependency is missing: {exc.name}. Run: cd backend && pip install -r requirements-dev.txt")
PY

echo "Backend:  http://$BACKEND_HOST:$BACKEND_PORT/docs"
echo "Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "Python:   $(command -v python)"
echo "Press Ctrl+C to stop both services."

cd "$BACKEND_DIR"
python -m uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" &
BACKEND_PID="$!"

cd "$FRONTEND_DIR"
AI_STUDIO_API_BASE_URL="http://$BACKEND_HOST:$BACKEND_PORT" npm run dev -- --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT" &
FRONTEND_PID="$!"

wait "$BACKEND_PID" "$FRONTEND_PID"
