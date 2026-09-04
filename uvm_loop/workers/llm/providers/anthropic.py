from .base import LLMProvider

class AnthropicProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Add provider implementation.")
