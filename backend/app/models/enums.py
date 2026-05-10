from enum import Enum


class EscalationStage(str, Enum):
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"
    STAGE_4 = "STAGE_4"
    LEGAL_ESCALATION = "LEGAL_ESCALATION"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    ESCALATED = "ESCALATED"
