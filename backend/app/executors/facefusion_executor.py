import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionResult:
    command: list[str]
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float
    output_path: Path


class FaceFusionExecutor:
    def __init__(
        self,
        facefusion_root: Path,
        python_executable: str = "python",
        timeout_seconds: int = 300,
        execution_provider: str = "cuda",
        execution_device_ids: list[int] | None = None,
    ) -> None:
        self._facefusion_root = facefusion_root
        self._python_executable = python_executable
        self._timeout_seconds = timeout_seconds
        self._execution_provider = execution_provider
        self._execution_device_ids = execution_device_ids or [0]

    def execute(self, source_path: Path, target_path: Path, output_path: Path) -> ExecutionResult:
        command = self._build_command(source_path, target_path, output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Executing FaceFusion CLI: source_path=%s target_path=%s output_path=%s "
            "target_suffix=%s output_suffix=%s argv=%s",
            source_path.resolve(),
            target_path.resolve(),
            output_path.resolve(),
            target_path.suffix.lower(),
            output_path.suffix.lower(),
            command,
        )

        started_at = monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=self._facefusion_root,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = self._decode_output(exc.output)
            stderr = self._decode_output(exc.stderr)
            exit_code = -1

        duration_seconds = monotonic() - started_at

        return ExecutionResult(
            command=command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_seconds=duration_seconds,
            output_path=output_path,
        )

    def _build_command(self, source_path: Path, target_path: Path, output_path: Path) -> list[str]:
        return [
            self._python_executable,
            "facefusion.py",
            "headless-run",
            "--source-paths",
            str(source_path.resolve()),
            "--target-path",
            str(target_path.resolve()),
            "--output-path",
            str(output_path.resolve()),
            "--processors",
            "face_swapper",
            "--execution-providers",
            self._execution_provider,
            "--execution-device-id",
            str(self._execution_device_ids[0]),
        ]

    def _decode_output(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        return value
