from dataclasses import dataclass

from app.models.enums import EscalationStage


@dataclass(frozen=True)
class EscalationRule:
    min_days: int
    max_days: int | None
    stage: EscalationStage


ESCALATION_RULES: list[EscalationRule] = [
    EscalationRule(min_days=1, max_days=7, stage=EscalationStage.STAGE_1),
    EscalationRule(min_days=8, max_days=14, stage=EscalationStage.STAGE_2),
    EscalationRule(min_days=15, max_days=21, stage=EscalationStage.STAGE_3),
    EscalationRule(min_days=22, max_days=30, stage=EscalationStage.STAGE_4),
    EscalationRule(min_days=31, max_days=None, stage=EscalationStage.LEGAL_ESCALATION),
]


LEGAL_ESCALATION_MIN_DAYS = 31
