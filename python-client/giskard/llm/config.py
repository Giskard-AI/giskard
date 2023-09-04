import logging
import os
from typing import Tuple


def _get_openai():
    if "OPENAI_API_KEY" not in os.environ:
        raise EnvironmentError(
            """
            You're trying to use giskard LLM features without providing any LLM or OpenAI API key.
            To use the default OpenAI API please provide the OPENAI_API_KEY environment variable.
            To use a custom model, please setup your llm by calling `giskard.set_default_llm(my_llm)`
            """
        )

    from langchain.llms import OpenAI

    return OpenAI(temperature=0.1)


class _TalkConfig:
    reliability_thresholds: Tuple[int, int] = 4, 6


class _LlmConfig:
    _default_llm = None
    talk: _TalkConfig = _TalkConfig()

    @property
    def default_llm(self):
        if self._default_llm is None:
            # Lazily call _get_openai as fallback to avoid getting missing key or dependency errors when not required
            self._default_llm = _get_openai()

        return self._default_llm

    def build_llm(self, **kwargs):
        """
        Get the default llm with parameterized values
        If the parameter isn't supported for the llm, the parameter is ignored

        :param kwargs: list of parameters to set for the llm
        :return: default llm with parameterized values
        """
        default_llm = self.default_llm

        for key, arg in kwargs.items():
            if hasattr(default_llm, key):
                setattr(default_llm, key, arg)
            else:
                logging.debug(f"Skipping parameter {key} for LLM since {type(default_llm)} doesn't ' support it")

        return default_llm

    def set_default_llm(self, default_llm=None):
        from langchain.base_language import BaseLanguageModel

        if default_llm is not None and not isinstance(default_llm, BaseLanguageModel):
            raise ValueError(
                "Please make sure that the default llm provided is instance of `langchain.base_language.BaseLanguageModel`"
            )

        self._default_llm = default_llm


llm_config = _LlmConfig()
