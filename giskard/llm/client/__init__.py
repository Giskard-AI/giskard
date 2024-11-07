import os

from .base import ChatMessage, LLMClient
from .logger import LLMLogger

_default_client = None

_default_llm_model = os.getenv("GSK_LLM_MODEL", "gpt-4o")
_default_completion_params = dict()


def _unset_default_client():
    global _default_client
    _default_client = None


def set_llm_model(llm_model: str, **kwargs):
    global _default_llm_model
    global _default_completion_params

    _default_llm_model = llm_model
    _default_completion_params = kwargs

    # If the model is set, we unset the default client
    _unset_default_client()


def get_default_client() -> LLMClient:
    global _default_client

    if _default_client is not None:
        return _default_client

    try:
        from .litellm import LiteLLMClient

        _default_client = LiteLLMClient(_default_llm_model, _default_completion_params)
    except ImportError:
        raise ValueError(f"LLM scan using {_default_llm_model} requires litellm")

    return _default_client


__all__ = ["LLMClient", "ChatMessage", "LLMLogger", "get_default_client", "set_llm_model"]
