from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        """Generate a JSON response string from the provider."""
