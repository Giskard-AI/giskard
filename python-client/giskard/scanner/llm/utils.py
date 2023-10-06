import openai

from ...core.errors import GiskardInstallationError


class LLMImportError(GiskardInstallationError):
    flavor = "llm"
    functionality = "LLM"


def llm(messages, model="gpt-4", temperature=0.5, n=1, **kwargs):
    completion = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature, n=n, **kwargs)
    if n == 1:
        return completion.choices[0].message.content
    return [c.message.content for c in completion.choices]


def llm_fn_call(messages, functions, model="gpt-4", temperature=0.5, n=1, **kwargs):
    completion = openai.ChatCompletion.create(
        model=model, messages=messages, functions=functions, temperature=temperature, n=n, **kwargs
    )
    if n == 1:
        return completion.choices[0].message
    return [c.message for c in completion.choices]
