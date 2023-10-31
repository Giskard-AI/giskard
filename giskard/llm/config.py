import os
from typing import Tuple

_openai_api_key = None
_openai_organization = None


def set_openai_key(key: str):
    global _openai_api_key
    _openai_api_key = key


def set_openai_organization(organization: str):
    global _openai_organization
    _openai_organization = organization


class LLMConfigurationError(ValueError):
    """Raised when the LLM client is not configured properly."""


def _get_openai():
    if "OPENAI_API_KEY" not in os.environ:
        raise EnvironmentError(
            """
            You're trying to use giskard LLM features without providing any LLM or OpenAI API key.
            To use the default OpenAI API please provide the OPENAI_API_KEY environment variable.
            To use a custom model, please setup your llm by calling `giskard.set_default_llm(my_llm)`
            """
        )

    from langchain.chat_models import ChatOpenAI

    return ChatOpenAI(temperature=0.1)


class _TalkConfig:
    reliability_thresholds: Tuple[int, int] = 4, 6


class _LlmConfig:
    _default_llm = None
    _scan_model: str = "gpt-4"
    talk: _TalkConfig = _TalkConfig()

    @property
    def default_llm(self):
        if self._default_llm is None:
            # Lazily call _get_openai as fallback to avoid getting missing key or dependency errors when not required
            self._default_llm = _get_openai()

        return self._default_llm

    def set_default_llm(self, default_llm=None):
        from langchain.base_language import BaseLanguageModel

        if default_llm is not None and not isinstance(default_llm, BaseLanguageModel):
            raise ValueError(
                "Please make sure that the default llm provided is instance of `langchain.base_language.BaseLanguageModel`"
            )

        self._default_llm = default_llm

    def build_scan_llm(self, gpt4_preferred: bool = False, **kwargs):
        from langchain.chat_models import ChatOpenAI

        if "OPENAI_API_KEY" not in os.environ:
            raise EnvironmentError(
                """
                You're trying to use giskard LLM scanning features without providing any LLM or OpenAI API key.
                To use the default OpenAI API please provide the OPENAI_API_KEY environment variable.
                """
            )

        model = (
            "gpt-3.5-turbo"
            if self._scan_model == "gpt-3.5" or (self._scan_model != "gpt-4" and not gpt4_preferred)
            else "gpt-4"
        )

        return ChatOpenAI(model_name=model, **kwargs)

    def set_scan_llm(self, scan_llm: str):
        if scan_llm not in ["gpt-3.5", "hybrid", "gpt-4"]:
            raise ValueError("Scan only support 'gpt-3.5', 'hybrid' or 'gpt-4' models")
        self._scan_model = scan_llm


llm_config = _LlmConfig()
