from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "start-mac-dev.sh"


def test_mac_start_script_manages_existing_local_comfyui_runtime() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'COMFYUI_HOME="${COMFYUI_HOME:-/Users/lyj/WorkStation/Project/ComfyUI}"' in script
    assert 'COMFYUI_PYTHON="${COMFYUI_PYTHON:-$(command -v python)}"' in script
    assert '"$COMFYUI_PYTHON" main.py --listen 127.0.0.1 --port 8188' in script
    assert 'comfyui_started=true' in script
    assert 'if [[ "$comfyui_started" == true ]]' in script


def test_mac_start_script_stops_the_process_trees_it_started() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "terminate_process_tree()" in script
    assert 'terminate_process_tree "$frontend_pid"' in script
    assert 'terminate_process_tree "$backend_pid"' in script
    assert 'terminate_process_tree "$comfyui_pid"' in script


def test_mac_start_script_has_no_remote_runtime_fallback() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "/Users/lyj/WorkStation/Services/ComfyUI" not in script
    assert "SSH" not in script
    assert "local-forward" not in script
