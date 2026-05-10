from app.ai.evaluation import evaluate_output_completeness, evaluate_tone_consistency
from app.models.enums import EscalationStage
from app.models.schemas import AIEmailOutput


def test_evaluate_tone_consistency_for_stage_4() -> None:
    output = AIEmailOutput(
        subject="Urgent follow-up: Invoice INV-4",
        email_body="This is an urgent payment reminder. Immediate action is requested.",
        tone_used="urgent professional",
        escalation_stage=EscalationStage.STAGE_4,
    )
    assert evaluate_tone_consistency(output) is True


def test_evaluate_output_completeness() -> None:
    output = AIEmailOutput(
        subject="Reminder INV-1",
        email_body="Invoice INV-1 due 2026-05-01 amount 500.00 remains outstanding.",
        tone_used="professional reminder",
        escalation_stage=EscalationStage.STAGE_1,
    )
    assert evaluate_output_completeness(output) is True
