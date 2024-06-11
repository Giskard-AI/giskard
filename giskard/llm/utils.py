from typing import Sequence

from ..models.base.model import BaseModel
from .generators.simple import SimpleDataGenerator


def generate_test_dataset(
    model: BaseModel,
    num_samples: int = 10,
    temperature=0.5,
    column_types=None,
    llm_seed: int = 1729,
):
    """Generates a synthetic test dataset using an LLM.

    Parameters
    ----------
    model : BaseModel
        The model to generate a test dataset for.
    num_samples : int
        The number of samples to generate, by default 10.
    temperature : Optional[float]
        The temperature to use for the generation, by default 0.5.
    column_types :
        (Default value = None)
    rng_seed :
        (Default value = 1729), seed used to generate completion

    Returns
    -------
    Dataset
        The generated dataset.

    Raises
    ------
    LLMGenerationError
        If the generation fails.

    See also
    --------
    :class:`giskard.llm.generators.BaseDataGenerator`
    """
    generator = SimpleDataGenerator(llm_temperature=temperature, llm_seed=llm_seed)

    return generator.generate_dataset(model, num_samples, column_types)


def format_chat_messages(messages: Sequence[dict]):
    """Formats a list of chat messages into a single string.

    Parameters
    ----------
    messages : List[ChatMessage]
        The list of messages to format.

    Returns
    -------
    str
        The formatted messages.
    """
    return "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
