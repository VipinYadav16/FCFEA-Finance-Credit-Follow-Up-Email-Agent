from pathlib import Path

from app.models.enums import EscalationStage
from app.utils.exceptions import PromptLoadError

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

STAGE_PROMPT_FILES = {
    EscalationStage.STAGE_1: "stage_1.txt",
    EscalationStage.STAGE_2: "stage_2.txt",
    EscalationStage.STAGE_3: "stage_3.txt",
    EscalationStage.STAGE_4: "stage_4.txt",
    EscalationStage.LEGAL_ESCALATION: "legal_escalation.txt",
}


def _read_prompt(file_name: str) -> str:
    prompt_path = PROMPTS_DIR / file_name
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise PromptLoadError(f"Failed to load prompt file: {prompt_path}") from exc


def load_system_prompt() -> str:
    return _read_prompt("system_prompt.txt")


def load_stage_prompt(stage: EscalationStage) -> str:
    prompt_file = STAGE_PROMPT_FILES.get(stage)
    if not prompt_file:
        raise PromptLoadError(f"No stage prompt configured for: {stage.value}")
    return _read_prompt(prompt_file)
