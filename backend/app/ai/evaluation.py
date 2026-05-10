from app.models.enums import EscalationStage
from app.models.schemas import AIEmailOutput

TONE_KEYWORDS = {
    EscalationStage.STAGE_1: ["friendly", "thank", "appreciate"],
    EscalationStage.STAGE_2: ["reminder", "update", "timeline"],
    EscalationStage.STAGE_3: ["attention", "required", "prompt"],
    EscalationStage.STAGE_4: ["urgent", "immediate", "escalation"],
    EscalationStage.LEGAL_ESCALATION: ["manual review", "internal review", "coordinate"],
}


def evaluate_tone_consistency(output: AIEmailOutput) -> bool:
    text = f"{output.tone_used} {output.email_body}".lower()
    expected = TONE_KEYWORDS.get(output.escalation_stage, [])
    return any(keyword in text for keyword in expected)


def evaluate_output_completeness(output: AIEmailOutput) -> bool:
    return all(
        [
            bool(output.subject.strip()),
            bool(output.email_body.strip()),
            bool(output.tone_used.strip()),
        ]
    )
