import os
from enum import Enum

from typing import Optional

from .base import LLMClient, LLMFunctionCall, LLMOutput
from .logger import LLMLogger


class LLMClientAPI(Enum):
    OPENAI = 1
    AZURE = 2


_default_client = None
_default_llm_api: Optional[LLMClientAPI] = None
_default_llm_model = os.getenv("GSK_LLM_MODEL", "gpt-4")


def set_default_client(client: LLMClient):
    global _default_client
    _default_client = client


def set_llm_api(llm__api: LLMClientAPI):
    global _default_llm_api
    _default_llm_api = llm__api


def set_llm_model(llm_model: str):
    global _default_llm_model
    _default_llm_model = llm_model


def get_default_llm_api() -> LLMClientAPI:
    global _default_llm_api
    if _default_llm_api is None:
        _default_llm_api = os.getenv(
            "GSK_LLM_API", LLMClientAPI.AZURE if "AZURE_OPENAI_API_KEY" in os.environ else LLMClientAPI.OPENAI
        )

    return _default_llm_api


def get_default_client() -> LLMClient:
    global _default_client

    if _default_client is not None:
        return _default_client

    # Setup the default client
    from .openai import LegacyOpenAIClient, OpenAIClient

    default_llm_api = get_default_llm_api()

    try:
        # For openai>=1.0.0
        from openai import OpenAI, AzureOpenAI

        client = AzureOpenAI() if default_llm_api is LLMClientAPI.AZURE else OpenAI()

        _default_client = OpenAIClient(_default_llm_model, client)
    except ImportError:
        # Fallback for openai<=0.28.1
        if default_llm_api is not LLMClientAPI.OPENAI:
            raise ValueError(f"LLM scan using {default_llm_api.name} require openai>=1.0.0")
        _default_client = LegacyOpenAIClient(_default_llm_model)

    return _default_client


__all__ = [
    "LLMClient",
    "LLMFunctionCall",
    "LLMOutput",
    "LLMLogger",
    "get_default_client",
    "set_llm_model",
    "set_llm_api",
    "set_default_client",
    "LLMClientAPI",
]
