from typing import Optional
from typing_extensions import deprecated

import logging
import os

from .base import ChatMessage, LLMClient
from .logger import LLMLogger

logger = logging.getLogger(__name__)

_default_client = None

_default_llm_model = os.getenv("GSK_LLM_MODEL", "gpt-4o")
_disable_structured_output = False
_default_completion_params = dict()
_default_llm_api = None


if "GSK_LLM_BASE_URL" in os.environ is not None:
    _default_completion_params["api_base"] = os.getenv("GSK_LLM_BASE_URL")


@deprecated("set_default_client is deprecated: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html")
def set_default_client(client: LLMClient):
    global _default_client
    _default_client = client


def _unset_default_client():
    global _default_client
    _default_client = None


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


@deprecated("set_llm_api is deprecated: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html")
def set_llm_api(llm_api: str):
    if llm_api.lower() not in {"azure", "openai"}:
        raise ValueError("Giskard LLM-based evaluators is only working with `azure` and `openai`")

    global _default_llm_api
    _default_llm_api = llm_api.lower()
    # If the API is set, we unset the default client
    _unset_default_client()


@deprecated("set_default_client is deprecated: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html")
def set_llm_base_url(llm_base_url: Optional[str]):
    global _default_completion_params
    _default_completion_params["api_base"] = llm_base_url


def set_llm_model(llm_model: str, disable_structured_output=False, **kwargs):
    """

    :param llm_model: The model to be used
    :param disable_structured_output: Set this to True when the used model doesn't support structured output
    :param kwargs: Additional fixed params to be passed during completion
    """
    global _default_llm_model
    global _disable_structured_output
    global _default_completion_params

    _default_llm_model = llm_model
    _disable_structured_output = disable_structured_output
    _default_completion_params = kwargs

    # If the model is set, we unset the default client
    _unset_default_client()


def get_default_client() -> LLMClient:
    global _default_client
    global _default_llm_api
    global _default_llm_model
    global _disable_structured_output

    if _default_client is not None:
        return _default_client

    try:
        from .litellm import LiteLLMClient

        if (
            _default_llm_api is not None
            and "/" in _default_llm_model
            and not _default_llm_model.startswith(f"{_default_llm_api}/")
        ):
            raise ValueError(
                f"Model {_default_llm_model} is not compatible with {_default_llm_api}: https://docs.giskard.ai/en/latest/open_source/setting_up/index.html "
            )
        if _default_llm_api is not None and "/" not in _default_llm_model:
            _default_llm_model = f"{_default_llm_api}/{_default_llm_model}"

        _default_client = LiteLLMClient(_default_llm_model, _disable_structured_output, _default_completion_params)
    except ImportError:
        raise ValueError(f"LLM scan using {_default_llm_model} requires litellm")

    return _default_client


__all__ = [
    "LLMClient",
    "ChatMessage",
    "LLMLogger",
    "get_default_client",
    "set_llm_model",
    "get_default_llm_api",
    "set_llm_api",
]
