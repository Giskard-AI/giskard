import pickle
from abc import ABC, abstractmethod
from inspect import isfunction, signature
from pathlib import Path
from typing import Any, Callable, Optional, Iterable, Union

import cloudpickle
import numpy as np
import pandas as pd

from giskard.core.core import ModelType
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import BaseModel
import logging

logger = logging.getLogger(__name__)


class WrapperModel(BaseModel, ABC):
    """
    A subclass of a BaseModel that wraps an existing model object (model) and uses it to make inference
    This class introduces a `data_preprocessing_function` which can be used
    to preprocess incoming data before it's passed to the underlying model
    """

    model: Any
    data_preprocessing_function: Callable[[pd.DataFrame], Any]
    model_postprocessing_function: Callable[[Any], Any]

    @configured_validate_arguments
    def __init__(
            self,
            model: Any,
            model_type: ModelType,
            data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
            model_postprocessing_function: Callable[[Any], Any] = None,
            name: Optional[str] = None,
            feature_names: Optional[Iterable] = None,
            classification_threshold: Optional[float] = 0.5,
            classification_labels: Optional[Iterable] = None,
    ) -> None:
        """
        Initialize a new instance of the WrapperModel class.

        Args:
            model (Any): The model that will be wrapped.
            model_type (ModelType): The type of the model. Must be a value from the `ModelType` enumeration.
            data_preprocessing_function (Callable[[pd.DataFrame], Any], optional): A function that will be applied to incoming data. Defaults to None.
            model_postprocessing_function (Callable[[Any], Any], optional): A function that will be applied to the model's predictions. Defaults to None.
            name (str, optional): A name for the wrapper. Defaults to None.
            feature_names (Optional[Iterable], optional): A list of feature names. Defaults to None.
            classification_threshold (float, optional): The probability threshold for classification. Defaults to 0.5.
            classification_labels (Optional[Iterable], optional): A list of classification labels. Defaults to None.

        Raises:
            ValueError: If `data_preprocessing_function` takes more than one argument.
            ValueError: If `model_postprocessing_function` takes more than one argument.
        """
        super().__init__(model_type, name, feature_names, classification_threshold, classification_labels)
        self.model = model
        self.data_preprocessing_function = data_preprocessing_function
        self.model_postprocessing_function = model_postprocessing_function

        # TODO: refactor this into validate_args or another decorator @validate_sign
        if self.data_preprocessing_function and isfunction(self.data_preprocessing_function):
            sign_len = len(signature(self.data_preprocessing_function).parameters)
            if sign_len != 1:
                raise ValueError(
                    f"data_preprocessing_function only takes 1 argument (a pandas.DataFrame) but {sign_len} were provided.")
        if self.model_postprocessing_function:
            sign_len = len(signature(self.model_postprocessing_function).parameters)
            if sign_len != 1:
                raise ValueError(
                    f"model_postprocessing_function only takes 1 argument but {sign_len} were provided.")

    def _postprocess(self, raw_predictions):
        # User specified a custom postprocessing function
        if self.model_postprocessing_function:
            raw_predictions = self.model_postprocessing_function(raw_predictions)

        # Convert predictions to numpy array
        raw_predictions = self._convert_to_numpy(raw_predictions)

        # We try to automatically fix issues in the output shape
        raw_predictions = self._possibly_fix_predictions_shape(raw_predictions)

        return raw_predictions

    @configured_validate_arguments
    def predict_df(self, df: pd.DataFrame):
        if self.data_preprocessing_function:
            df = self.data_preprocessing_function(df)

        raw_prediction = self.model_predict(df)
        raw_prediction = self._postprocess(raw_prediction)

        return raw_prediction

    def _convert_to_numpy(self, raw_predictions):
        return np.asarray(raw_predictions)

    def _possibly_fix_predictions_shape(self, raw_predictions):
        if not self.is_classification:
            return raw_predictions

        # Ensure this is 2-dimensional
        if raw_predictions.ndim <= 1:
            raw_predictions = raw_predictions.reshape(-1, 1)

        # Fix possible extra dimensions (e.g. batch dimension which was not squeezed)
        if raw_predictions.ndim > 2:
            logger.warning(
                f"\nThe output of your model has shape {raw_predictions.shape}, but we expect a shape (n_entries, n_classes). \n"
                "We will attempt to automatically reshape the output to match this format, please check that the results are consistent.",
                exc_info=True,
            )

            raw_predictions = raw_predictions.squeeze(tuple(range(1, raw_predictions.ndim - 1)))

            if raw_predictions.ndim > 2:
                raise ValueError(
                    f"The output of your model has shape {raw_predictions.shape}, but we expect it to be (n_entries, n_classes)."
                )

        # E.g. for binary classification, prediction should be of the form `(p, 1 - p)`.
        # If a binary classifier returns a single prediction `p`, we try to infer the second class
        # prediction as `1 - p`.
        if self.is_binary_classification and raw_predictions.shape[-1] == 1:
            logger.warning(
                f"\nYour binary classification model prediction is of the shape {raw_predictions.shape}. \n"
                f"In Giskard we expect the shape {(raw_predictions.shape[0], 2)} for binary classification models. \n"
                "We automatically inferred the second class prediction but please make sure that \n"
                "the probability output of your model corresponds to the first label of the \n"
                f"classification_labels ({self.meta.classification_labels}) you provided us with.",
                exc_info=True,
            )

            raw_predictions = np.append(raw_predictions, 1 - raw_predictions, axis=1)

        # For classification models, the last dimension must be equal to the number of classes
        if raw_predictions.shape[-1] != len(self.meta.classification_labels):
            raise ValueError(
                f"The output of your model has shape {raw_predictions.shape}, but we expect it to be (n_entries, n_classes), \n"
                f"where `n_classes` is the number of classes in your model output ({len(self.meta.classification_labels)} in this case)."
            )

        return raw_predictions

    @abstractmethod
    def model_predict(self, df):
        ...

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)

        if self.data_preprocessing_function:
            self.save_data_preprocessing_function(local_path)
        if self.model_postprocessing_function:
            self.save_model_postprocessing_function(local_path)

    def save_data_preprocessing_function(self, local_path: Union[str, Path]):
        with open(Path(local_path) / "giskard-data-preprocessing-function.pkl", "wb") as f:
            cloudpickle.dump(self.data_preprocessing_function, f, protocol=pickle.DEFAULT_PROTOCOL)

    def save_model_postprocessing_function(self, local_path: Union[str, Path]):
        with open(Path(local_path) / "giskard-model-postprocessing-function.pkl", "wb") as f:
            cloudpickle.dump(self.model_postprocessing_function, f, protocol=pickle.DEFAULT_PROTOCOL)

    @classmethod
    def load(cls, local_dir, **kwargs):
        kwargs["data_preprocessing_function"] = cls.load_data_preprocessing_function(local_dir)
        kwargs["model_postprocessing_function"] = cls.load_model_postprocessing_function(local_dir)
        return cls(model=cls.load_model(local_dir), **kwargs)

    @classmethod
    @abstractmethod
    def load_model(cls, local_dir):
        ...

    @classmethod
    def load_data_preprocessing_function(cls, local_path: Union[str, Path]):
        local_path = Path(local_path)
        file_path = local_path / "giskard-data-preprocessing-function.pkl"
        if file_path.exists():
            with open(file_path, "rb") as f:
                return cloudpickle.load(f)
        else:
            return None

    @classmethod
    def load_model_postprocessing_function(cls, local_path: Union[str, Path]):
        local_path = Path(local_path)
        file_path = local_path / "giskard-model-postprocessing-function.pkl"
        if file_path.exists():
            with open(file_path, "rb") as f:
                return cloudpickle.load(f)
        else:
            return None
