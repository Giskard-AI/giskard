import openai

from ...core.errors import GiskardInstallationError


class LLMImportError(GiskardInstallationError):
    flavor = "llm"
    functionality = "LLM"


def llm(messages, model="gpt-4", temperature=0.5, **kwargs):
    completion = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature, **kwargs)
    return completion.choices[0].message.content
