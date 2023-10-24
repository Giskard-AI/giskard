import logging
import pickle
from abc import ABC, abstractmethod
from inspect import isfunction, signature
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union

import cloudpickle
import mlflow
import numpy as np
import pandas as pd
import yaml

from .model import BaseModel
from ..utils import warn_once
from ...core.core import ModelType
from ...core.validation import configured_validate_arguments

logger = logging.getLogger(__name__)


class WrapperModel(BaseModel, ABC):
    """Base class for model wrappers.

    This is subclass of a :class:`BaseModel` that wraps an existing model
    object and uses it to make inference.

    This class introduces a `data_preprocessing_function` which can be used
    to preprocess incoming data before it is passed to the underlying model.
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
        id: Optional[str] = None,
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Parameters
        ----------
        model : Any
            The model that will be wrapped.
        model_type : ModelType
            The type of the model. Must be a value from the :class:`ModelType`
            enumeration.
        data_preprocessing_function : Callable[[pd.DataFrame], Any], optional
            A function that will be applied to incoming data. Default is ``None``.
        model_postprocessing_function : Callable[[Any], Any], optional
            A function that will be applied to the model's predictions. Default
            is ``None``.
        name : str, optional
            A name for the wrapper. Default is ``None``.
        feature_names : Optional[Iterable], optional
            A list of feature names. Default is ``None``.
        classification_threshold : float, optional
            The probability threshold for classification. Default is 0.5.
        classification_labels : Optional[Iterable], optional
            A list of classification labels. Default is None.
        batch_size : Optional[int], optional
            The batch size to use for inference. Default is ``None``, which
            means inference will be done on the full dataframe.
        """
        super().__init__(
            model_type=model_type,
            name=name,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            id=id,
            batch_size=batch_size,
            **kwargs,
        )
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
        raw_predictions = self._convert_to_numpy(raw_predictions)

        # We try to automatically fix issues in the output shape
        raw_predictions = self._possibly_fix_predictions_shape(raw_predictions)

        return raw_predictions

    def _convert_to_numpy(self, raw_predictions):
        return np.asarray(raw_predictions)

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

        raw_prediction = np.concatenate(outputs)

        if self.is_regression:
            return raw_prediction.astype(float)

        return raw_prediction

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
    def model_predict(self, data):
        """Performs the model inference/forward pass.

        Parameters
        ----------
        data : Any
            The input data for making predictions. If you did not specify a
            `data_preprocessing_function`, this will be a :class:`pd.DataFrame`,
            otherwise it will be whatever the `data_preprocessing_function`
            returns.

        Returns
        -------
        numpy.ndarray
            If the model is ``classification``, it should return an array of
            probabilities of shape ``(num_entries, num_classes)``.
            If the model is ``regression`` or ``text_generation``, it should
            return an array of ``num_entries`` predictions.
        """
        ...

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)
        self.save_wrapper_meta(local_path)
        if self.data_preprocessing_function:
            self.save_data_preprocessing_function(local_path)
        if self.model_postprocessing_function:
            self.save_model_postprocessing_function(local_path)

    @abstractmethod
    def save_model(self, path: Union[str, Path]) -> None:
        """Saves the wrapped ``model`` object.

        Parameters
        ----------
        path : Union[str, Path]
            Path to which the model should be saved.
        """
        ...

    def save_data_preprocessing_function(self, local_path: Union[str, Path]):
        with open(Path(local_path) / "giskard-data-preprocessing-function.pkl", "wb") as f:
            cloudpickle.dump(self.data_preprocessing_function, f, protocol=pickle.DEFAULT_PROTOCOL)

    def save_model_postprocessing_function(self, local_path: Union[str, Path]):
        with open(Path(local_path) / "giskard-model-postprocessing-function.pkl", "wb") as f:
            cloudpickle.dump(self.model_postprocessing_function, f, protocol=pickle.DEFAULT_PROTOCOL)

    def save_wrapper_meta(self, local_path):
        with open(Path(local_path) / "giskard-model-wrapper-meta.yaml", "w") as f:
            yaml.dump(
                {
                    "batch_size": self.batch_size,
                },
                f,
                default_flow_style=False,
            )

    @classmethod
    def load(cls, local_dir, **kwargs):
        constructor_params = cls.load_constructor_params(local_dir, **kwargs)

        return cls(model=cls.load_model(local_dir), **constructor_params)

    @classmethod
    def load_constructor_params(cls, local_dir, **kwargs):
        params = cls.load_wrapper_meta(local_dir)
        params["data_preprocessing_function"] = cls.load_data_preprocessing_function(local_dir)
        params["model_postprocessing_function"] = cls.load_model_postprocessing_function(local_dir)
        params.update(kwargs)

        model_id, meta = cls.read_meta_from_local_dir(local_dir)
        constructor_params = meta.__dict__
        constructor_params["id"] = model_id
        constructor_params = constructor_params.copy()
        constructor_params.update(params)

        return constructor_params

    @classmethod
    @abstractmethod
    def load_model(cls, path: Union[str, Path]):
        """Loads the wrapped ``model`` object.

        Parameters
        ----------
        path : Union[str, Path]
            Path from which the model should be loaded.
        """
        ...

    @classmethod
    def load_data_preprocessing_function(cls, local_path: Union[str, Path]):
        local_path = Path(local_path)
        file_path = local_path / "giskard-data-preprocessing-function.pkl"
        if file_path.exists():
            with open(file_path, "rb") as f:
                return cloudpickle.load(f)
        return None

    @classmethod
    def load_model_postprocessing_function(cls, local_path: Union[str, Path]):
        local_path = Path(local_path)
        file_path = local_path / "giskard-model-postprocessing-function.pkl"
        if file_path.exists():
            with open(file_path, "rb") as f:
                return cloudpickle.load(f)
        return None

    @classmethod
    def load_wrapper_meta(cls, local_dir):
        wrapper_meta_file = Path(local_dir) / "giskard-model-wrapper-meta.yaml"
        if wrapper_meta_file.exists():
            with open(wrapper_meta_file) as f:
                wrapper_meta = yaml.load(f, Loader=yaml.Loader)
                wrapper_meta["batch_size"] = int(wrapper_meta["batch_size"]) if wrapper_meta["batch_size"] else None
                return wrapper_meta
        else:
            # ensuring backward compatibility
            return {"batch_size": None}

    def to_mlflow(self, artifact_path: str = "prediction-function-from-giskard", **kwargs):
        def _giskard_predict(df):
            return self.predict(df)

        class MLflowModel(mlflow.pyfunc.PythonModel):
            def predict(self, df):
                return _giskard_predict(df)

        mlflow_model = MLflowModel()
        return mlflow.pyfunc.log_model(artifact_path=artifact_path, python_model=mlflow_model)
