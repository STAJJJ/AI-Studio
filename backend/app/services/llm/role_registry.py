from dataclasses import dataclass

from app.schemas.chat import ChatRoleInfo


class RoleNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class ChatRoleDefinition:
    id: str
    name: str
    description: str
    system_prompt: str

    def public_info(self) -> ChatRoleInfo:
        return ChatRoleInfo(id=self.id, name=self.name, description=self.description)


class RoleRegistry:
    def __init__(self, roles: list[ChatRoleDefinition]) -> None:
        self._roles = {role.id: role for role in roles}

    def get_role(self, role_id: str) -> ChatRoleDefinition:
        try:
            return self._roles[role_id]
        except KeyError as exc:
            raise RoleNotFoundError(f"Unsupported chat role: {role_id}") from exc

    def list_public_roles(self) -> list[ChatRoleInfo]:
        return [role.public_info() for role in self._roles.values()]


role_registry = RoleRegistry(
    roles=[
        ChatRoleDefinition(
            id="general_assistant",
            name="General Assistant",
            description="通用问答与任务协助",
            system_prompt=(
                "You are AI Studio's General Assistant. Be concise, reliable, and practical. "
                "Do not invent unknown facts; explain uncertainty clearly when needed."
            ),
        ),
        ChatRoleDefinition(
            id="aigc_engineer",
            name="AIGC Engineer",
            description=(
                "熟悉 ComfyUI、Stable Diffusion、FLUX、FaceFusion、InsightFace、LoRA、"
                "Prompt Engineering、模型部署与接口封装"
            ),
            system_prompt=(
                "You are AI Studio's senior AIGC engineer. Give practical engineering guidance for "
                "ComfyUI, Stable Diffusion, FLUX, FaceFusion, InsightFace, LoRA, prompt engineering, "
                "model deployment, inference optimization, and API integration. Prefer actionable plans "
                "over abstract explanations."
            ),
        ),
        ChatRoleDefinition(
            id="interview_coach",
            name="Interview Coach",
            description="针对 AI/AIGC 岗位进行面试提问、回答评价和答案优化",
            system_prompt=(
                "You are AI Studio's Interview Coach for AI and AIGC roles. Ask one interview question "
                "at a time, wait for the user's answer, then evaluate it and provide an improved sample answer. "
                "Do not dump many questions at once."
            ),
        ),
    ]
)
