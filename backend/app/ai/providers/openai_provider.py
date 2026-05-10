import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from openai import OpenAI

from app.ai.providers.base_provider import BaseAIProvider
from app.utils.config import settings
from app.utils.exceptions import AIProviderError

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise AIProviderError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        attempts = max(settings.openai_max_retries, 0) + 1

        for attempt in range(1, attempts + 1):
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        self.client.responses.create,
                        model=settings.openai_model_name,
                        input=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        text={
                            "format": {
                                "type": "json_schema",
                                "name": "followup_email",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "subject": {"type": "string"},
                                        "email_body": {"type": "string"},
                                        "tone_used": {"type": "string"},
                                        "escalation_stage": {"type": "string"},
                                    },
                                    "required": [
                                        "subject",
                                        "email_body",
                                        "tone_used",
                                        "escalation_stage",
                                    ],
                                    "additionalProperties": False,
                                },
                            }
                        },
                    )
                    result = future.result(timeout=settings.openai_timeout_seconds)

                payload = getattr(result, "output_text", "") or ""
                payload = payload.strip()
                if not payload:
                    raise AIProviderError("OpenAI returned an empty response")

                # Validate JSON shape string early for stable downstream behavior.
                json.loads(payload)
                return payload
            except TimeoutError as exc:
                logger.warning("OpenAI timeout on attempt %s", attempt)
                if attempt >= attempts:
                    raise AIProviderError("OpenAI request timed out") from exc
            except Exception as exc:  # noqa: BLE001
                logger.exception("OpenAI request failed on attempt %s", attempt)
                if attempt >= attempts:
                    raise AIProviderError("OpenAI request failed") from exc

        raise AIProviderError("OpenAI request failed")
