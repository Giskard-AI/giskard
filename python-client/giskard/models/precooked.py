import numpy as np
import pandas as pd
from typing import Optional, Iterable, Callable

from .base import BaseModel, ModelMeta, ModelType, ModelPredictionResults
from ..datasets.base import Dataset


class PrecookedModel(BaseModel):
    """A dummy model for internal usage."""

    def __init__(
        self,
        predictions: pd.DataFrame,
        original_data: pd.DataFrame,
        model_type: ModelType,
        data_preprocessing_fn: Optional[Callable] = None,
        feature_names: Optional[Iterable] = None,
        classification_labels: Optional[Iterable] = None,
    ):
        self._predictions = predictions
        self._data = original_data
        self._data_preprocessing_fn = data_preprocessing_fn
        super().__init__(
            model_type=model_type, feature_names=feature_names, classification_labels=classification_labels
        )

    @classmethod
    def from_model(cls, model: BaseModel, dataset: Dataset):
        """Creates a PrecookedModel from an existing model and dataset."""
        predictions = pd.DataFrame(model.predict(dataset).raw, index=dataset.df.index)
        data_preprocessing_fn = getattr(model, "data_preprocessing_function")

        return cls(
            predictions,
            dataset.df,
            model.meta.model_type,
            data_preprocessing_fn,
            model.meta.feature_names,
            model.meta.classification_labels,
        )

    def predict_df(self, df: pd.DataFrame):
        if self._data_preprocessing_fn is not None:
            df = self._data_preprocessing_fn(df)

        raw = self._predictions.loc[df.index].values

        assert np.all(df.values == self._data.loc[df.index].values)
        # Let’s actually check the row values
        assert np.all(df.values == self._data.loc[df.index].values)

        return raw
