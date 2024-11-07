from typing import Optional
from typing_extensions import deprecated

import logging
import os

from .base import ChatMessage, LLMClient
from .logger import LLMLogger

_default_client = None
_default_llm_api: Optional[str] = None

_default_llm_model = os.getenv("GSK_LLM_MODEL", "gpt-4")
_default_completion_params = dict()

_default_llm_base_url = os.getenv("GSK_LLM_BASE_URL", None)


@deprecated(
    "set_default_client is deprecated, check documentation to setup llm: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html"
)
def set_default_client(client: LLMClient):
    global _default_client
    _default_client = client


def _unset_default_client():
    global _default_client
    _default_client = None


@deprecated(
    "set_llm_api is deprecated, check documentation to setup llm: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html"
)
def set_llm_api(llm_api: str):
    if llm_api.lower() not in {"azure", "openai"}:
        raise ValueError("Giskard LLM-based evaluators is only working with `azure` and `openai`")

    global _default_llm_api
    _default_llm_api = llm_api.lower()
    # If the API is set, we unset the default client
    _unset_default_client()


@deprecated(
    "set_llm_base_url is deprecated, check documentation to setup llm: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html"
)
def set_llm_base_url(llm_base_url: Optional[str]):
    global _default_llm_base_url
    _default_llm_base_url = llm_base_url
    # If the model is set, we unset the default client
    _unset_default_client()


def set_llm_model(llm_model: str, **kwargs):
    global _default_llm_model
    global _default_completion_params

    _default_llm_model = llm_model
    _default_completion_params = kwargs

    # If the model is set, we unset the default client
    _unset_default_client()


def get_default_llm_api() -> str:
    global _default_llm_api
    if _default_llm_api is None:
        _default_llm_api = os.getenv(
            "GSK_LLM_API", "azure" if "AZURE_OPENAI_API_KEY" in os.environ else "openai"
        ).lower()

        if _default_llm_api not in {"azure", "openai"}:
            logging.warning(
                f"LLM-based evaluation is only working with `azure` and `openai`. Found {_default_llm_api} in GSK_LLM_API, falling back to `openai`"
            )
            _default_llm_api = "openai"

    return _default_llm_api


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


__all__ = [
    "LLMClient",
    "ChatMessage",
    "LLMLogger",
    "get_default_client",
    "set_llm_model",
    "set_llm_api",
    "set_default_client",
    "set_llm_base_url",
]
