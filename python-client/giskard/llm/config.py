import os

DEFAULT_CONFIG = dict()


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


def set_default_llm(default_llm=None):
    if default_llm is None:
        DEFAULT_CONFIG.pop("llm")
        return

    from langchain.base_language import BaseLanguageModel

    if not isinstance(default_llm, BaseLanguageModel):
        raise ValueError(
            "Please make sure that the default llm provided is instance of `langchain.base_language.BaseLanguageModel`"
        )

    DEFAULT_CONFIG["llm"] = default_llm


def get_default_llm():
    # Lazily call _get_openai as fallback to avoid getting missing key or dependency errors when not required
    return DEFAULT_CONFIG["llm"] if "llm" in DEFAULT_CONFIG else _get_openai()
