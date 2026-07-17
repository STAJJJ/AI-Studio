#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV_NAME="${AI_STUDIO_CONDA_ENV:-studio}"

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

activate_conda_env
echo "Python: $(command -v python)"

echo "== Backend pytest =="
cd "$ROOT_DIR/backend"
python -m pytest -q

echo "== Frontend typecheck =="
cd "$ROOT_DIR/frontend"
npm run typecheck

echo "== Frontend lint =="
npm run lint

echo "== Frontend production build =="
npm run build

echo "All checks completed."
