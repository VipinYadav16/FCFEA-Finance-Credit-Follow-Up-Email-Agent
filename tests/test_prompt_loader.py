from app.ai.prompt_loader import load_stage_prompt, load_system_prompt
from app.models.enums import EscalationStage


def test_system_prompt_loads() -> None:
    content = load_system_prompt()
    assert "enterprise finance credit follow-up communication assistant" in content.lower()


def test_stage_prompt_loads_for_legal_escalation() -> None:
    content = load_stage_prompt(EscalationStage.LEGAL_ESCALATION)
    assert "manual internal review" in content.lower()
