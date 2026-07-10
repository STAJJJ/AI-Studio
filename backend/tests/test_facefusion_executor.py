import os
from pathlib import Path

import pytest

from app.executors.facefusion_executor import FaceFusionExecutor


@pytest.mark.integration
def test_facefusion_executor_runs_headless_cli() -> None:
    if os.getenv("RUN_FACEFUSION_TEST") != "1":
        pytest.skip("Set RUN_FACEFUSION_TEST=1 to run FaceFusion CLI integration test")

    facefusion_root = Path("/3241903007/workstation/LYJ/FaceFusion/facefusion")
    if not (facefusion_root / "facefusion.py").exists():
        pytest.skip("FaceFusion CLI is not installed on this server yet")

    source_path = Path("tests/assets/source.png")
    target_path = Path("tests/assets/target.png")
    output_path = Path("tests/assets/output.png")
    output_path.unlink(missing_ok=True)

    executor = FaceFusionExecutor(
        facefusion_root=facefusion_root,
        python_executable="python",
        timeout_seconds=300,
        execution_provider="cpu",
        execution_device_ids=[0],
    )

    result = executor.execute(
        source_path=source_path,
        target_path=target_path,
        output_path=output_path,
    )

    assert result.command
    assert result.duration_seconds >= 0
    assert result.exit_code == 0, result.stderr
    assert output_path.exists()
    assert output_path.stat().st_size > 0
