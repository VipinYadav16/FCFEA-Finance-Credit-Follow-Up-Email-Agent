import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError

import google.generativeai as genai

from app.ai.providers.base_provider import BaseAIProvider
from app.utils.config import settings
from app.utils.exceptions import AIProviderError

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise AIProviderError("GEMINI_API_KEY is not configured")
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model_name)

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        merged_prompt = f"{system_prompt}\n\n{user_prompt}"
        attempts = max(settings.gemini_max_retries, 0) + 1

        for attempt in range(1, attempts + 1):
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        self.model.generate_content,
                        merged_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.2,
                            response_mime_type="application/json",
                        ),
                    )
                    result = future.result(timeout=settings.gemini_timeout_seconds)
                text = (result.text or "").strip()
                if not text:
                    raise AIProviderError("Gemini returned an empty response")
                return text
            except TimeoutError as exc:
                logger.warning("Gemini timeout on attempt %s", attempt)
                if attempt >= attempts:
                    raise AIProviderError("Gemini request timed out") from exc
            except Exception as exc:  # noqa: BLE001
                logger.exception("Gemini request failed on attempt %s", attempt)
                if attempt >= attempts:
                    raise AIProviderError("Gemini request failed") from exc

        raise AIProviderError("Gemini request failed")
