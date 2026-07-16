from app.services.llm.role_registry import RoleNotFoundError, role_registry


def test_role_registry_returns_public_roles_without_system_prompt() -> None:
    roles = role_registry.list_public_roles()

    role_ids = {role.id for role in roles}
    assert {"general_assistant", "aigc_engineer", "interview_coach"}.issubset(role_ids)
    assert all(not hasattr(role, "system_prompt") for role in roles)


def test_role_registry_returns_internal_role_with_system_prompt() -> None:
    role = role_registry.get_role("aigc_engineer")

    assert role.id == "aigc_engineer"
    assert "ComfyUI" in role.system_prompt
    assert "FaceFusion" in role.system_prompt


def test_role_registry_rejects_unknown_role() -> None:
    try:
        role_registry.get_role("unknown")
    except RoleNotFoundError as exc:
        assert "Unsupported chat role" in str(exc)
    else:
        raise AssertionError("Expected RoleNotFoundError")
