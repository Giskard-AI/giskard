from .base import LLMClient, LLMFunctionCall, LLMOutput
from .logger import LLMLogger
from .utils import autodetect_client, ApiType, get_scan_model

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

    api_type = autodetect_client()
    model = get_scan_model(api_type)

    try:
        # For openai>=1.0.0
        from openai import OpenAI, AzureOpenAI

        client = AzureOpenAI() if api_type is ApiType.azure else OpenAI()

        _default_client = OpenAIClient(client, model)
    except ImportError:
        # Fallback for openai<=0.28.1
        if api_type is not ApiType.openai:
            raise ValueError(f"LLM scan using {api_type.name} require openai>=1.0.0")
        _default_client = LegacyOpenAIClient()

    return _default_client


__all__ = ["LLMClient", "LLMFunctionCall", "LLMOutput", "LLMLogger", "get_default_client"]
