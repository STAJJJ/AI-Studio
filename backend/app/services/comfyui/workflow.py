import copy
import json
from pathlib import Path
from typing import Any


class WorkflowTemplateError(RuntimeError):
    """Raised when a ComfyUI workflow template cannot be loaded or rendered."""


class ComfyUIWorkflowTemplate:
    def __init__(self, template_path: Path) -> None:
        self._template_path = template_path

    def render(self, prompt: str, width: int, height: int) -> dict[str, Any]:
        template = self._load_template()
        replacements = {
            "{{prompt}}": prompt,
            "{{width}}": width,
            "{{height}}": height,
        }
        rendered = self._replace_placeholders(template, replacements)
        if not isinstance(rendered, dict):
            raise WorkflowTemplateError("ComfyUI workflow template root must be an object")
        return rendered

    def _load_template(self) -> dict[str, Any]:
        try:
            with self._template_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as exc:
            raise WorkflowTemplateError(f"Workflow template not found: {self._template_path}") from exc
        except json.JSONDecodeError as exc:
            raise WorkflowTemplateError(f"Workflow template is invalid JSON: {self._template_path}") from exc
        if not isinstance(data, dict):
            raise WorkflowTemplateError("ComfyUI workflow template root must be an object")
        return data

    def _replace_placeholders(self, value: Any, replacements: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            return {key: self._replace_placeholders(item, replacements) for key, item in value.items()}
        if isinstance(value, list):
            return [self._replace_placeholders(item, replacements) for item in value]
        if isinstance(value, str) and value in replacements:
            return copy.deepcopy(replacements[value])
        return value
