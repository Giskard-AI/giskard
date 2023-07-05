import logging
import pickle
from abc import ABC, abstractmethod
from inspect import isfunction, signature
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union

import cloudpickle
import numpy as np
import pandas as pd

from ...core.core import ModelType
from ...core.validation import configured_validate_arguments
from ..utils import warn_once
from .model import BaseModel

logger = logging.getLogger(__name__)


class WrapperModel(BaseModel, ABC):
    """
    A subclass of a BaseModel that wraps an existing model object (model) and uses it to make inference
    This class introduces a `data_preprocessing_function` which can be used
    to preprocess incoming data before it's passed to the underlying model
    """

    @configured_validate_arguments
    def __init__(
        self,
        model: Any,
        model_type: ModelType,
        data_preprocessing_function: Optional[Callable[[pd.DataFrame], Any]] = None,
        model_postprocessing_function: Optional[Callable[[Any], Any]] = None,
        name: Optional[str] = None,
        feature_names: Optional[Iterable] = None,
        classification_threshold: Optional[float] = 0.5,
        classification_labels: Optional[Iterable] = None,
        batch_size: Optional[int] = None,
        **kwargs,
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
            batch_size (Optional[int], optional): The batch size to use for inference. Defaults to None, which means
              inference will be done on the full dataframe.

        Raises:
            ValueError: If `data_preprocessing_function` takes more than one argument.
            ValueError: If `model_postprocessing_function` takes more than one argument.
        """
        super().__init__(model_type, name, feature_names, classification_threshold, classification_labels, **kwargs)
        self.model = model
        self.data_preprocessing_function = data_preprocessing_function
        self.model_postprocessing_function = model_postprocessing_function
        self.batch_size = batch_size

        # TODO: refactor this into validate_args or another decorator @validate_sign
        if self.data_preprocessing_function and isfunction(self.data_preprocessing_function):
            sign_len = len(signature(self.data_preprocessing_function).parameters)
            if sign_len != 1:
                raise ValueError(
                    f"data_preprocessing_function only takes 1 argument (a pandas.DataFrame) but {sign_len} were provided."
                )
        if self.model_postprocessing_function:
            sign_len = len(signature(self.model_postprocessing_function).parameters)
            if sign_len != 1:
                raise ValueError(f"model_postprocessing_function only takes 1 argument but {sign_len} were provided.")

    def _preprocess(self, data):
        if self.data_preprocessing_function:
            return self.data_preprocessing_function(data)
        return data

    def _postprocess(self, raw_predictions):
        # User specified a custom postprocessing function
        if self.model_postprocessing_function:
            raw_predictions = self.model_postprocessing_function(raw_predictions)

        # Convert predictions to numpy array
        raw_predictions = np.asarray(raw_predictions)

        # We try to automatically fix issues in the output shape
        raw_predictions = self._possibly_fix_predictions_shape(raw_predictions)

        return raw_predictions

    @configured_validate_arguments
    def predict_df(self, df: pd.DataFrame):
        if self.batch_size and self.batch_size > 0:
            dfs = np.array_split(df, np.arange(self.batch_size, len(df), self.batch_size))
        else:
            dfs = [df]

        outputs = []
        for batch in map(self._preprocess, dfs):
            output = self.model_predict(batch)
            output = self._postprocess(output)
            outputs.append(output)

        return np.concatenate(outputs)

    def _possibly_fix_predictions_shape(self, raw_predictions: np.ndarray):
        if not self.is_classification:
            return raw_predictions

        # Ensure this is 2-dimensional
        if raw_predictions.ndim <= 1:
            raw_predictions = raw_predictions.reshape(-1, 1)

        # Fix possible extra dimensions (e.g. batch dimension which was not squeezed)
        if raw_predictions.ndim > 2:
            warn_once(
                logger,
                f"\nThe output of your model has shape {raw_predictions.shape}, but we expect a shape (n_entries, n_classes). \n"
                "We will attempt to automatically reshape the output to match this format, please check that the results are consistent.",
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
            warn_once(
                logger,
                "Please make sure that your model's output corresponds "
                "to the second label in classification_labels.",
            )

            raw_predictions = np.append(1 - raw_predictions, raw_predictions, axis=1)

        # For classification models, the last dimension must be equal to the number of classes
        if raw_predictions.shape[-1] != len(self.meta.classification_labels):
            raise ValueError(
                f"The output of your model has shape {raw_predictions.shape}, but we expect it to be (n_entries, n_classes), \n"
                f"where `n_classes` is the number of classes in your model output ({len(self.meta.classification_labels)} in this case)."
            )

        return raw_predictions

    @abstractmethod
    def model_predict(self, df):
        """
        Abstract method for making predictions using the model.
        The standard model output required for Giskard is:

        * if classification: an array (nxm) of probabilities corresponding to n data entries
          (rows of pandas.DataFrame)
          and m classification_labels. In the case of binary classification, an array of (nx1) probabilities is
          also accepted.
          Make sure that the probability provided is for the second label provided in classification_labels.
        * if regression or text_generation: an array of predictions corresponding to data entries
          (rows of pandas.DataFrame) and outputs.

        Args:
            df (pandas.DataFrame): The input data for making predictions.

        Returns:
            The predicted values based on the input data.
        """
        ...

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)

        if self.data_preprocessing_function:
            self.save_data_preprocessing_function(local_path)
        if self.model_postprocessing_function:
            self.save_model_postprocessing_function(local_path)

    @abstractmethod
    def save_model(self, local_path: Union[str, Path]) -> None:
        """
        Saving the ``model`` object. The serialization depends on the model type:

        - ``mlflow`` methods are used if the ``model`` is from either of ``sklearn``, ``catboost``, ``pytorch`` or ``tensorflow``.
        - ``transformers`` methods are used if the ``model`` is from ``huggingface``.
        - ``langchain`` methods are used if the ``model`` is from ``langchain``.

        :param local_path: path to the saved model
        """
        ...

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
        model_id, meta = cls.read_meta_from_local_dir(local_dir)
        constructor_params = meta.__dict__
        constructor_params["id"] = model_id
        constructor_params = constructor_params.copy()
        constructor_params.update(kwargs)

        return cls(model=cls.load_model(local_dir), **constructor_params)

    @classmethod
    @abstractmethod
    def load_model(cls, local_dir):
        """
        Loading the ``model`` object. The de-serialization depends on the model type:

        - ``mlflow`` methods are used if the ``model`` is from either of ``sklearn``, ``catboost``, ``pytorch`` or ``tensorflow``.
        - ``transformers`` methods are used if the ``model`` is from ``huggingface``.
        - ``langchain`` methods are used if the ``model`` is from ``langchain``.
        """
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
