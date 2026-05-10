from app.models.enums import EscalationStage


def parse_stage(stage_value: str) -> EscalationStage | None:
    try:
        return EscalationStage(stage_value)
    except ValueError:
        return None
