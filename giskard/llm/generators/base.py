from typing import Dict, Optional, Sequence

import json
import logging
from abc import ABC, abstractmethod

import pandas as pd
from pydantic import BaseModel

from ...datasets.base import Dataset
from ..client import LLMClient, get_default_client
from ..client.base import ChatMessage
from ..errors import LLMGenerationError

logger = logging.getLogger("giskard.llm")


class BaseGenerator(ABC):
    @abstractmethod
    def generate_dataset(self, model, num_samples=10, column_types=None) -> Dataset:
        ...


class _BaseLLMGenerator(BaseGenerator, ABC):
    _default_temperature = 0.5
    _output_key = "inputs"

    def __init__(
        self,
        languages: Optional[Sequence[str]] = None,
        llm_temperature: Optional[float] = None,
        llm_client: LLMClient = None,
        llm_seed: int = 1729,
    ):
        self.languages = languages or ["en"]
        self.llm_temperature = llm_temperature if llm_temperature is not None else self._default_temperature
        self.llm_client = llm_client or get_default_client()
        self.llm_seed = llm_seed

    def generate_dataset(self, model: BaseModel, num_samples: int = 10, column_types: Dict = None) -> Dataset:
        """Generates a test dataset for the model.

        Parameters
        ----------
        model : BaseModel
            The model to generate a test dataset for.
        num_samples : int
            The number of samples to generate, by default 10.
        column_types : dict, optional
            The column types for the generated datasets. (Default value = None)

        Returns
        -------
        Dataset
            The generated dataset.

        Raises
        ------
        LLMGenerationError
            If the generation fails.
        """
        messages = self._format_messages(model, num_samples, column_types)

        out = self.llm_client.complete(
            messages=messages,
            temperature=self.llm_temperature,
            caller_id=self.__class__.__name__,
            seed=self.llm_seed,
            format="json",
        )

        generated = self._parse_output(out)

        dataset = Dataset(
            df=pd.DataFrame(generated),
            name=self._make_dataset_name(model),
            validation=False,
            column_types=column_types,
        )

        return dataset

    def _parse_output(self, raw_output: ChatMessage):
        try:
            data = json.loads(raw_output.content)
            if self._output_key:
                data = data[self._output_key]
        except (json.JSONDecodeError, KeyError) as err:
            logger.error("Generator output parse error, got raw output: %s", raw_output.content)
            raise LLMGenerationError("Could not parse generated data") from err
        return data

    def _make_dataset_name(self, model: BaseModel):
        return f"Synthetic Test Dataset for {model.name}"

    @abstractmethod
    def _format_messages(self, model: BaseModel, num_samples: int):
        ...


class LLMBasedDataGenerator(_BaseLLMGenerator):
    def __init__(
        self,
        prompt: str,
        prefix_messages: Optional[Sequence[ChatMessage]] = None,
        languages: Optional[Sequence[str]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.prompt = prompt
        self.prefix_messages = prefix_messages or []
        self.languages = languages or ["en"]

    def _format_messages(
        self, model: BaseModel, num_samples: int, column_types: Optional[Dict] = None
    ) -> Sequence[ChatMessage]:
        prompt = self.prompt.format(model=model, num_samples=num_samples, languages=", ".join(self.languages))
        return self.prefix_messages + [ChatMessage(role="user", content=prompt)]
