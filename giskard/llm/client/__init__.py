from typing import Optional

import logging
import os

from .base import ChatMessage, LLMClient
from .logger import LLMLogger

_default_client = None
_default_llm_api: Optional[str] = None
_default_llm_model = os.getenv("GSK_LLM_MODEL", "gpt-4")
_default_llm_base_url = os.getenv("GSK_LLM_BASE_URL", "")


def set_default_client(client: LLMClient):
    global _default_client
    _default_client = client


def set_llm_api(llm_api: str):
    if llm_api.lower() not in {"azure", "openai"}:
        raise ValueError("Giskard LLM-based evaluators is only working with `azure` and `openai`")

    global _default_llm_api
    _default_llm_api = llm_api.lower()
    # If the API is set, we unset the default client
    global _default_client
    _default_client = None


def srt_llm_base_url(llm_base_url: str):
    global _default_llm_base_url
    if _default_llm_base_url:
        # Additional logic to handle when the environment variable is set
        print(f"Using LLM base URL: {_default_llm_base_url}")
        # Here you can add any additional configuration or logic needed when the URL is set
    else:
        # Logic for when the environment variable is not set
        print("GSK_LLM_BASE_URL is not set. Using default configuration.")
        # Here you can add any additional configuration or logic needed for the default case


def set_llm_model(llm_model: str):
    global _default_llm_model
    _default_llm_model = llm_model
    # If the model is set, we unset the default client
    global _default_client
    _default_client = None


def get_openai_instance():
    # For openai>=1.0.0
    from openai import OpenAI
    """Return an OpenAI instance with or without a custom base URL."""
    if _default_llm_base_url:
        return OpenAI(base_url=_default_llm_base_url)
    else:
        return OpenAI()


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

    # Setup the default client
    from .openai import OpenAIClient

    default_llm_api = get_default_llm_api()

    try:
        # For openai>=1.0.0
        from openai import AzureOpenAI, OpenAI

        client = AzureOpenAI() if default_llm_api == "azure" else get_openai_instance()

        _default_client = OpenAIClient(model=_default_llm_model, client=client)
    except ImportError:
        raise ValueError(f"LLM scan using {default_llm_api.name} require openai>=1.0.0")

    return _default_client


__all__ = [
    "LLMClient",
    "ChatMessage",
    "LLMLogger",
    "get_default_client",
    "set_llm_model",
    "set_llm_api",
    "set_default_client",
]
