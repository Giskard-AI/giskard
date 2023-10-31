from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd
from pydantic import BaseModel

from ...datasets.base import Dataset
from ..client import LLMClient, get_default_client
from ..errors import LLMGenerationError

DEFAULT_GENERATE_INPUTS_PROMPT = """You are auditing an AI model. Your task is to generate typical but varied inputs for this model.

Your will generate inputs for the following model: {model_name} - {model_description}.
Model Features: {feature_names}

Each generated input must be an object with values for each of the model features, aimed at simulating typical usage of the model, or typical inputs that the model is supposed to handle.
Take the model description into account when generating the inputs. You should not generate repeated inputs or variations of the same input, instead try to generate inputs that varied for use cases of the model and cover all situations that could be encoutered during typical usage of the model.

Think step by step and then call the `generate_inputs` function with the generated inputs. You must generate {num_samples} inputs.
"""


class LLMGenerator(ABC):
    _default_temperature = 0.5
    _default_model = "gpt-4"
    _default_prompt = DEFAULT_GENERATE_INPUTS_PROMPT

    def __init__(
        self,
        llm_model: Optional[str] = None,
        llm_temperature: Optional[float] = None,
        llm_client: LLMClient = None,
        prompt: Optional[str] = None,
    ):
        self.llm_model = llm_model if llm_model is not None else self._default_model
        self.llm_temperature = llm_temperature if llm_temperature is not None else self._default_temperature
        self.llm_client = llm_client or get_default_client()
        self.prompt = prompt if prompt is not None else self._default_prompt

    @abstractmethod
    def generate_dataset(self, model, num_samples=10, column_types=None) -> Dataset:
        ...


class BaseDataGenerator(LLMGenerator):
    def _make_generate_input_prompt(self, model: BaseModel, num_samples: int):
        return self.prompt.format(
            model_name=model.meta.name,
            model_description=model.meta.description,
            feature_names=", ".join(model.meta.feature_names),
            num_samples=num_samples,
        )

    def _make_generate_input_functions(self, model: BaseModel, num_samples: int):
        return [
            {
                "name": "generate_inputs",
                "description": "generates inputs for model audit",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "inputs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {name: {"type": "string"} for name in model.meta.feature_names},
                            },
                        }
                    },
                    "required": ["inputs"],
                },
            }
        ]

    def _make_dataset_name(self, model: BaseModel, num_samples):
        return f"Synthetic Test Dataset for {model.meta.name}"

    def generate_dataset(self, model: BaseModel, num_samples: int = 10, column_types=None) -> Dataset:
        """Generates a test dataset for the model.

        Parameters
        ----------
        model : BaseModel
            The model to generate a test dataset for.
        num_samples : int, optional
            The number of samples to generate, by default 10.
        column_types : float, optional
            The column types for the generated datasets.

        Raises
        ------
        LLMGenerationError
            If the generation fails.

        Returns
        -------
        Dataset
            The generated dataset.
        """
        prompt = self._make_generate_input_prompt(model, num_samples)
        functions = self._make_generate_input_functions(model, num_samples)

        out = self.llm_client.complete(
            messages=[{"role": "system", "content": prompt}],
            functions=functions,
            function_call={"name": "generate_inputs"},
            temperature=self.llm_temperature,
            model=self.llm_model,
            caller_id=self.__class__.__name__,
        )

        try:
            generated = out.function_call.args["inputs"]
        except (AttributeError, KeyError) as err:
            raise LLMGenerationError("Could not parse generated inputs") from err

        dataset = Dataset(
            df=pd.DataFrame(generated),
            name=self._make_dataset_name(model, num_samples),
            validation=False,
            column_types=column_types,
        )
        return dataset
