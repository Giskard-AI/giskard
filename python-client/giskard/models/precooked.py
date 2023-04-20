import pandas as pd
from typing import Optional, Iterable

from .base import BaseModel, ModelMeta, ModelType, ModelPredictionResults
from ..datasets.base import Dataset


class PrecookedModel(BaseModel):
    """A dummy model for internal usage."""

    def __init__(
        self,
        predictions: pd.DataFrame,
        model_type: ModelType,
        feature_names: Optional[Iterable] = None,
        classification_labels: Optional[Iterable] = None,
    ):
        self._predictions = predictions
        super().__init__(
            model_type=model_type, feature_names=feature_names, classification_labels=classification_labels
        )

    @classmethod
    def from_model(cls, model: BaseModel, dataset: Dataset):
        """Creates a PrecookedModel from an existing model and dataset."""
        predictions = pd.DataFrame(model.predict(dataset).raw, index=dataset.df.index)

        return cls(predictions, model.meta.model_type, model.meta.feature_names, model.meta.classification_labels)

    def predict_df(self, df: pd.DataFrame):
        raw = self._predictions.loc[df.index].values

        return raw
