from app.models.enums import EscalationStage
from app.workflows.policy import ESCALATION_RULES


def determine_escalation_stage(overdue_days: int) -> EscalationStage:
    if overdue_days <= 0:
        return EscalationStage.STAGE_1

    for rule in ESCALATION_RULES:
        if overdue_days < rule.min_days:
            continue
        if rule.max_days is None or overdue_days <= rule.max_days:
            return rule.stage

    return EscalationStage.LEGAL_ESCALATION
