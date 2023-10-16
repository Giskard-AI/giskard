import json
from typing import Optional

import pandas as pd

from giskard.scanner.llm import utils

from ...datasets import Dataset
from ...models.base.model import BaseModel
from ..logger import logger

GENERATE_INPUTS_PROMPT = """You are auditing an AI model. Your task is to generate typical but varied inputs for this model.

Your will generate inputs for the following model: {model_name} - {model_description}.
Model Features: {feature_names}

Each generated input must be an object with values for each of the model features, aimed at simulating typical usage of the model, or typical inputs that the model is supposed to handle.
Take the model description into account when generating the inputs. You should not generate repeated inputs or variations of the same input, instead try to generate inputs that varied for use cases of the model and cover all situations that could be encoutered during typical usage of the model.

Think step by step and then call the `generate_inputs` function with the generated inputs. You must generate {num_samples} inputs.
"""


def generate_test_dataset(model: BaseModel, num_samples: int = 10, prompt: Optional[str] = None, temperature=0.5):
    """Generates a test dataset for the model."""
    functions = [
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
    if prompt is None:
        prompt = GENERATE_INPUTS_PROMPT.format(
            model_name=model.meta.name,
            model_description=model.meta.description,
            feature_names=model.meta.feature_names,
            num_samples=num_samples,
        )

    out = utils.llm_fn_call(
        messages=[{"role": "system", "content": prompt}],
        functions=functions,
        function_call={"name": "generate_inputs"},
        temperature=temperature,
    )
    try:
        generated = json.loads(out.function_call.arguments)["inputs"]
    except (AttributeError, json.JSONDecodeError, KeyError):
        logger.warning("Could not generate validation dataset automatically.")
        return Dataset(pd.DataFrame(), validation=False)

    dataset = Dataset(df=pd.DataFrame(generated), name="Test Dataset (automatically generated)", validation=False)
    return dataset
