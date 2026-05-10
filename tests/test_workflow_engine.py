from app.models.enums import EscalationStage
from app.workflows.engine import determine_escalation_stage


def test_determine_escalation_stage_boundaries() -> None:
    assert determine_escalation_stage(1) == EscalationStage.STAGE_1
    assert determine_escalation_stage(7) == EscalationStage.STAGE_1
    assert determine_escalation_stage(8) == EscalationStage.STAGE_2
    assert determine_escalation_stage(14) == EscalationStage.STAGE_2
    assert determine_escalation_stage(15) == EscalationStage.STAGE_3
    assert determine_escalation_stage(21) == EscalationStage.STAGE_3
    assert determine_escalation_stage(22) == EscalationStage.STAGE_4
    assert determine_escalation_stage(30) == EscalationStage.STAGE_4
    assert determine_escalation_stage(31) == EscalationStage.LEGAL_ESCALATION


def test_non_overdue_defaults_to_stage_1() -> None:
    assert determine_escalation_stage(0) == EscalationStage.STAGE_1
