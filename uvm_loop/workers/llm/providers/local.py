from .base import LLMProvider

class LocalProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Add local-model backend.")
