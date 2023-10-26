from typing import Optional

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.base.model import BaseModel
from .generators.base import BaseDataGenerator


@retry(stop=stop_after_attempt(3), wait=wait_exponential(3))
def llm(messages, model="gpt-4", temperature=0.5, n=1, **kwargs):
    completion = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature, n=n, **kwargs)
    if n == 1:
        return completion.choices[0].message.content
    return [c.message.content for c in completion.choices]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(3))
def llm_fn_call(messages, functions, model="gpt-4", temperature=0.5, n=1, **kwargs):
    completion = openai.ChatCompletion.create(
        model=model, messages=messages, functions=functions, temperature=temperature, n=n, **kwargs
    )
    if n == 1:
        return completion.choices[0].message
    return [c.message for c in completion.choices]


def generate_test_dataset(
    model: BaseModel, num_samples: int = 10, prompt: Optional[str] = None, temperature=0.5, column_types=None
):
    """Generates a synthetic test dataset using an LLM.

    Parameters
    ----------
    model : BaseModel
        The model to generate a test dataset for.
    num_samples : int, optional
        The number of samples to generate, by default 10.
    prompt : Optional[str], optional
        The prompt to use for the generation, if not specified a default will be used.
    temperature : float, optional
        The temperature to use for the generation, by default 0.5.

    Raises
    ------
    LLMGenerationError
        If the generation fails.

    Returns
    -------
    Dataset
        The generated dataset.

    See also
    --------
    :class:`giskard.llm.generators.BaseDataGenerator`
    """
    generator = BaseDataGenerator(prompt=prompt, llm_temperature=temperature)
    return generator.generate_dataset(model, num_samples, column_types)
