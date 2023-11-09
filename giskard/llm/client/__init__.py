from .base import LLMClient, LLMFunctionCall, LLMOutput
from .logger import LLMLogger

_default_client = None


def set_default_client(client: LLMClient):
    global _default_client
    _default_client = client


def get_default_client() -> LLMClient:
    global _default_client

    if _default_client is not None:
        return _default_client

    # Setup the default client
    from .openai import LegacyOpenAIClient, OpenAIClient

    try:
        # For openai>=1.0.0
        from openai import OpenAI

        client = OpenAI()
        _default_client = OpenAIClient(client)
    except ImportError:
        # Fallback for openai<=0.28.1
        _default_client = LegacyOpenAIClient()

    return _default_client


__all__ = ["LLMClient", "LLMFunctionCall", "LLMOutput", "LLMLogger", "get_default_client"]
