from typing import Iterable, Optional

import numpy as np
import pandas as pd

from ..core.core import ModelType
from ..datasets.base import Dataset
from .base import BaseModel, ModelPredictionResults


class PrecookedModel(BaseModel):
    """A dummy model for internal usage."""

    def __init__(
        self,
        data: Dataset,
        predictions: ModelPredictionResults,
        model_type: ModelType,
        feature_names: Optional[Iterable] = None,
        classification_labels: Optional[Iterable] = None,
        **kwargs,
    ):
        self._data = data
        self._predictions = predictions
        super().__init__(
            model_type=model_type, feature_names=feature_names, classification_labels=classification_labels, **kwargs
        )

    @classmethod
    def from_model(cls, model: BaseModel, dataset: Dataset):
        """Creates a PrecookedModel from an existing model and dataset.

        Parameters
        ----------
        model : BaseModel
            A instance of a Giskard model.
        dataset : Dataset
            Dataset for which predictions will be cached.

        Returns
        -------
        PrecookedModel

        """
        predictions = model.predict(dataset)

        return cls(
            dataset,
            predictions,
            model.meta.model_type,
            model.meta.feature_names,
            model.meta.classification_labels,
        )

    def predict(self, dataset: Dataset, *args, **kwargs) -> ModelPredictionResults:
        refs = pd.Series(np.arange(len(self._data)), index=self._data.df.index)
        idx = refs.loc[dataset.df.index]

        raw = np.asarray(self._predictions.raw)[idx]
        prediction = np.asarray(self._predictions.prediction)[idx]
        raw_prediction = np.asarray(self._predictions.raw_prediction)[idx]

        probabilities = getattr(self._predictions, "probabilities", None)
        if probabilities is not None:
            probabilities = np.asarray(probabilities)[idx]

        all_predictions = getattr(self._predictions, "all_predictions", None)
        if all_predictions is not None:
            all_predictions = np.asarray(all_predictions)[idx]

        return ModelPredictionResults(
            raw=raw,
            prediction=prediction,
            raw_prediction=raw_prediction,
            probabilities=probabilities,
            all_predictions=all_predictions,
        )

    def predict_df(self, df: pd.DataFrame, *args, **kwargs):
        raise NotImplementedError()
