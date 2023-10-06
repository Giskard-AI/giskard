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

    def __init__(self, giskard_model, feature_names):
        if hasattr(giskard_model, "description"):
            self.description = giskard_model.description
        if hasattr(giskard_model, "name"):
            self.name = giskard_model.name
        logging.info(f"generator init: {self}")
        self.giskard_model = giskard_model
        if len(feature_names) > 1:
            raise ValueError("Giskard Generator accepts only 1 text feature at the moment.")
        self.input_variable = feature_names[0]

    def generate(self, prompt) -> List[str]:
        giskard_dataset = Dataset(pd.DataFrame({self.input_variable: prompt}, index=[0]), validation=False)
        return [self.giskard_model.predict(giskard_dataset).prediction[0]]
