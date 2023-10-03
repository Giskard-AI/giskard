#!/usr/bin/env python3
"""Base Generator

All `garak` generators must inherit from this.
"""

import logging
from typing import List

import pandas as pd

from .....datasets import Dataset


class GiskardGenerator:
    """Base class for objects that wrap an LLM or other text-to-text service"""

    name = "GiskardGenerator"
    description = ""
    active = True

    def __init__(self, giskard_model, input_variable):
        if hasattr(giskard_model, "description"):
            self.description = giskard_model.description
        if hasattr(giskard_model, "name"):
            self.name = giskard_model.name
        logging.info(f"generator init: {self}")
        self.giskard_model = giskard_model
        self.input_variable = input_variable
        # TODO: Can we infer it from self.giskard_model.feature_names?
        #  (check if langchain and get it from input_variables, etc.)

    def generate(self, prompt) -> List[str]:
        giskard_dataset = Dataset(pd.DataFrame({self.input_variable: prompt}, index=[0]), validation=False)
        return [self.giskard_model.predict(giskard_dataset).prediction[0]]
