from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Add provider implementation.")
