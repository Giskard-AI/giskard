import builtins
import importlib
import logging
import pickle
import platform
import posixpath
import tempfile
import uuid
from abc import abstractmethod, ABC
from inspect import signature, isfunction
from pathlib import Path
from typing import Optional, Any, Union, Callable, Iterable

import cloudpickle
import mlflow
import numpy as np
import pandas as pd
import pydantic
import yaml

from giskard.client.giskard_client import GiskardClient
from giskard.core.core import ModelMeta, SupportedModelTypes, ModelType
from giskard.core.validation import configured_validate_arguments
from giskard.datasets.base import Dataset
from giskard.ml_worker.utils.logging import Timer
from giskard.models.cache import ModelCache
from giskard.path_utils import get_size
from giskard.settings import settings

from ..utils import np_types_to_native, warn_once
from ..cache import get_cache_enabled
from ..utils import np_types_to_native

META_FILENAME = "giskard-model-meta.yaml"

MODEL_CLASS_PKL = "ModelClass.pkl"

logger = logging.getLogger(__name__)


class ModelPredictionResults(pydantic.BaseModel):
    raw: Any
    prediction: Any
    raw_prediction: Any
    probabilities: Optional[Any]
    all_predictions: Optional[Any]


class BaseModel(ABC):
    """
    The BaseModel class is an abstract base class that defines the common interface for all the models used in this project.

    Attributes:
        model_type: ModelType
            Type of the model (ModelType.REGRESSION or ModelType.CLASSIFICATION).
        name: str, optional
            Name of the model.
        feature_names: iterable, optional
            List of names of the input features.
        classification_threshold: float, optional
            Threshold value used for classification models.
        classification_labels: iterable, optional
            List of labels for classification models.

    Raises:
        ValueError
            If an invalid model type is specified.

            If duplicate values are found in the classification_labels.
    """

    should_save_model_class = False
    id: uuid.UUID = None
    _cache: ModelCache

    @configured_validate_arguments
    def __init__(
        self,
        model_type: ModelType,
        name: Optional[str] = None,
        feature_names: Optional[Iterable] = None,
        classification_threshold: Optional[float] = 0.5,
        classification_labels: Optional[Iterable] = None,
    ) -> None:
        """
        Initialize a new instance of the BaseModel class.

        Parameters:
            model_type (ModelType): Type of the model, either ModelType.REGRESSION or ModelType.CLASSIFICATION.
            name (str, optional): Name of the model. If not provided, defaults to the class name.
            feature_names (Iterable, optional): A list of names of the input features.
            classification_threshold (float, optional): Threshold value used for classification models. Defaults to 0.5.
            classification_labels (Iterable, optional): A list of labels for classification models.

        Raises:
            ValueError: If an invalid model_type value is provided.
            ValueError: If duplicate values are found in the classification_labels list.

        Notes:
            This class uses the @configured_validate_arguments decorator to validate the input arguments.
            The initialized object contains the following attributes:
                - meta: a ModelMeta object containing metadata about the model.
        """
        if type(model_type) == str:
            try:
                model_type = SupportedModelTypes(model_type)
            except ValueError as e:
                available_values = {i.value for i in SupportedModelTypes}
                raise ValueError(
                    f'Invalid model type value "{model_type}". Available values are: {available_values}'
                ) from e

        if classification_labels is not None:
            classification_labels = list(classification_labels)
            if len(classification_labels) != len(set(classification_labels)):
                raise ValueError("Duplicates are found in 'classification_labels', please only provide unique values.")

        self._cache = ModelCache(model_type)

        self.meta = ModelMeta(
            name=name if name is not None else self.__class__.__name__,
            model_type=model_type,
            feature_names=list(feature_names) if feature_names else None,
            classification_labels=np_types_to_native(classification_labels),
            loader_class=self.__class__.__name__,
            loader_module=self.__module__,
            classification_threshold=classification_threshold,
        )

    @property
    def is_classification(self):
        return self.meta.model_type == SupportedModelTypes.CLASSIFICATION

    @property
    def is_binary_classification(self):
        return self.is_classification and len(self.meta.classification_labels) == 2

    @property
    def is_regression(self):
        return self.meta.model_type == SupportedModelTypes.REGRESSION

    @property
    def is_generative(self):
        return self.meta.model_type == SupportedModelTypes.GENERATIVE

    @classmethod
    def determine_model_class(cls, meta, local_dir):
        class_file = Path(local_dir) / MODEL_CLASS_PKL
        if class_file.exists():
            with open(class_file, "rb") as f:
                clazz = cloudpickle.load(f)
                if not issubclass(clazz, BaseModel):
                    raise ValueError(f"Unknown model class: {clazz}. Models should inherit from 'BaseModel' class")
                return clazz
        else:
            return getattr(importlib.import_module(meta.loader_module), meta.loader_class)

    def save_meta(self, local_path):
        with open(Path(local_path) / META_FILENAME, "w") as f:
            yaml.dump(
                {
                    "language_version": platform.python_version(),
                    "language": "PYTHON",
                    "model_type": self.meta.model_type.name.upper(),
                    "threshold": self.meta.classification_threshold,
                    "feature_names": self.meta.feature_names,
                    "classification_labels": self.meta.classification_labels,
                    "loader_module": self.meta.loader_module,
                    "loader_class": self.meta.loader_class,
                    "id": str(self.id),
                    "name": self.meta.name,
                    "size": get_size(local_path),
                },
                f,
                default_flow_style=False,
            )

    def save(self, local_path: Union[str, Path]) -> None:
        if self.id is None:
            self.id = uuid.uuid4()
            self._cache.set_id(str(self.id))
        if self.should_save_model_class:
            self.save_model_class(local_path)
        self.save_meta(local_path)

    def save_model_class(self, local_path):
        class_file = Path(local_path) / MODEL_CLASS_PKL
        with open(class_file, "wb") as f:
            cloudpickle.dump(self.__class__, f, protocol=pickle.DEFAULT_PROTOCOL)

    def prepare_dataframe(self, df, column_dtypes=None, target=None):
        """
        Prepares a Pandas DataFrame for inference by ensuring the correct columns are present and have the correct data types.

        Args:
            dataset (Dataset): The dataset to prepare.

        Returns:
            pd.DataFrame: The prepared Pandas DataFrame.

        Raises:
            ValueError: If the target column is found in the dataset.
            ValueError: If a specified feature name is not found in the dataset.
        """
        df = df.copy()
        column_dtypes = dict(column_dtypes) if column_dtypes else None

        if column_dtypes:
            for cname, ctype in column_dtypes.items():
                if cname not in df:
                    df[cname] = None

        if target:
            if target in df.columns:
                df.drop(target, axis=1, inplace=True)
            if column_dtypes and target in column_dtypes:
                del column_dtypes[target]

        if self.meta.feature_names:
            if set(self.meta.feature_names) > set(df.columns):
                column_names = set(self.meta.feature_names) - set(df.columns)
                raise ValueError(
                    f"The following columns are not found in the dataset: {', '.join(sorted(column_names))}"
                )
            df = df[self.meta.feature_names]
            if column_dtypes:
                column_dtypes = {k: v for k, v in column_dtypes.items() if k in self.meta.feature_names}

        for cname, ctype in column_dtypes.items():
            if cname not in df:
                df[cname] = None

        if column_dtypes:
            df = Dataset.cast_column_to_dtypes(df, column_dtypes)
        return df

    def predict(self, dataset: Dataset) -> ModelPredictionResults:
        """
        Generates predictions for the input dataset.

        Args:
            dataset (Dataset): The input dataset to make predictions on.

        Returns:
            ModelPredictionResults: The prediction results for the input dataset.

        Raises:
            ValueError: If the prediction task is not supported by the model.

        Notes:
            This method uses the `prepare_dataframe()` method to preprocess the input dataset before making predictions.
            The `predict_df()` method is used to generate raw predictions for the preprocessed data.
            The type of predictions generated by this method depends on the model type:
            * For regression models, the `prediction` field of the returned `ModelPredictionResults` object will contain the same
              values as the `raw_prediction` field.
            * For binary or multiclass classification models, the `prediction` field of the returned `ModelPredictionResults` object
              will contain the predicted class labels for each example in the input dataset.
              The `probabilities` field will contain the predicted probabilities for the predicted class label.
              The `all_predictions` field will contain the predicted probabilities for all class labels for each example in the input dataset.
        """
        timer = Timer()

        if get_cache_enabled():
            raw_prediction = self._predict_from_cache(dataset)
        else:
            raw_prediction = self.predict_df(
                self.prepare_dataframe(dataset.df, column_dtypes=dataset.column_dtypes, target=dataset.target)
            )

        if self.is_regression or self.is_generative:
            result = ModelPredictionResults(
                prediction=raw_prediction, raw_prediction=raw_prediction, raw=raw_prediction
            )
        elif self.is_classification:
            labels = np.array(self.meta.classification_labels)
            threshold = self.meta.classification_threshold

            if threshold is not None and len(labels) == 2:
                predicted_lbl_idx = (raw_prediction[:, 1] > threshold).astype(int)
            else:
                predicted_lbl_idx = raw_prediction.argmax(axis=1)

            all_predictions = pd.DataFrame(raw_prediction, columns=labels)

            predicted_labels = labels[predicted_lbl_idx]
            probability = raw_prediction[range(len(predicted_lbl_idx)), predicted_lbl_idx]

            result = ModelPredictionResults(
                raw=raw_prediction,
                prediction=predicted_labels,
                raw_prediction=predicted_lbl_idx,
                probabilities=probability,
                all_predictions=all_predictions,
            )
        else:
            raise ValueError(f"Prediction task is not supported: {self.meta.model_type}")
        timer.stop(f"Predicted dataset with shape {dataset.df.shape}")
        return result

    @abstractmethod
    def predict_df(self, df: pd.DataFrame):
        """
        Inner method that does the actual inference of a prepared dataframe
        :param df: dataframe to predict
        """
        ...

    def _predict_from_cache(self, dataset: Dataset):
        cached_predictions = self._cache.read_from_cache(dataset.row_hashes)
        missing = cached_predictions.isna()

        missing_slice = dataset.slice(lambda x: dataset.df[missing], row_level=False)
        df = self.prepare_dataframe(
            missing_slice.df, column_dtypes=missing_slice.column_dtypes, target=missing_slice.target
        )

        if len(df) > 0:
            raw_prediction = self.predict_df(df)
            self._cache.set_cache(dataset.row_hashes[missing], raw_prediction)
            cached_predictions.loc[missing] = raw_prediction.tolist()

        # TODO: check if there is a better solution
        return np.array(np.array(cached_predictions).tolist())

    def upload(self, client: GiskardClient, project_key, validate_ds=None) -> None:
        """
        Uploads the model to a Giskard project using the provided Giskard client. Also validates the model
        using the given validation dataset, if any.

        Args:
            client (GiskardClient): A Giskard client instance to use for uploading the model.
            project_key (str): The project key to use for the upload.
            validate_ds (Dataset, optional): A validation dataset to use for validating the model. Defaults to None.

        Notes:
            This method saves the model to a temporary directory before uploading it. The temporary directory
            is deleted after the upload is completed.
        """
        from giskard.core.model_validation import validate_model

        validate_model(model=self, validate_ds=validate_ds)
        with tempfile.TemporaryDirectory(prefix="giskard-model-") as f:
            self.save(f)

            if client is not None:
                client.log_artifacts(f, posixpath.join(project_key, "models", str(self.id)))
                client.save_model_meta(project_key, self.id, self.meta, platform.python_version(), get_size(f))

    @classmethod
    def download(cls, client: GiskardClient, project_key, model_id):
        """
        Downloads the specified model from the Giskard server and loads it into memory.

        Args:
            client (GiskardClient): The client instance that will connect to the Giskard server.
            project_key (str): The key for the project that the model belongs to.
            model_id (str): The ID of the model to download.

        Returns:
            An instance of the class calling the method, with the specified model loaded into memory.

        Raises:
            AssertionError: If the local directory where the model should be saved does not exist.
        """
        local_dir = settings.home_dir / settings.cache_dir / project_key / "models" / model_id
        if client is None:
            # internal worker case, no token based http client
            assert local_dir.exists(), f"Cannot find existing model {project_key}.{model_id} in {local_dir}"
            with open(Path(local_dir) / META_FILENAME) as f:
                file_meta = yaml.load(f, Loader=yaml.Loader)
                meta = ModelMeta(
                    name=file_meta["name"],
                    model_type=SupportedModelTypes[file_meta["model_type"]],
                    feature_names=file_meta["feature_names"],
                    classification_labels=file_meta["classification_labels"],
                    classification_threshold=file_meta["threshold"],
                    loader_module=file_meta["loader_module"],
                    loader_class=file_meta["loader_class"],
                )
        else:
            client.load_artifact(local_dir, posixpath.join(project_key, "models", model_id))
            meta_response = client.load_model_meta(project_key, model_id)
            # internal worker case, no token based http client
            assert local_dir.exists(), f"Cannot find existing model {project_key}.{model_id} in {local_dir}"
            with open(Path(local_dir) / META_FILENAME) as f:
                file_meta = yaml.load(f, Loader=yaml.Loader)
                classification_labels = cls.cast_labels(meta_response)
                meta = ModelMeta(
                    name=meta_response["name"],
                    model_type=SupportedModelTypes[meta_response["modelType"]],
                    feature_names=meta_response["featureNames"],
                    classification_labels=classification_labels,
                    classification_threshold=meta_response["threshold"],
                    loader_module=file_meta["loader_module"],
                    loader_class=file_meta["loader_class"],
                )

        clazz = cls.determine_model_class(meta, local_dir)

        constructor_params = meta.__dict__
        del constructor_params["loader_module"]
        del constructor_params["loader_class"]

        model = clazz.load(local_dir, **constructor_params)
        model.id = model_id
        model._cache = ModelCache(meta.model_type, model.id)
        return model

    @classmethod
    def cast_labels(cls, meta_response):
        labels_ = meta_response["classificationLabels"]
        labels_dtype = meta_response["classificationLabelsDtype"]
        if labels_ and labels_dtype and builtins.hasattr(builtins, labels_dtype):
            dtype = builtins.getattr(builtins, labels_dtype)
            labels_ = [dtype(i) for i in labels_]
        return labels_

    @classmethod
    def load(cls, local_dir, **kwargs):
        class_file = Path(local_dir) / MODEL_CLASS_PKL
        if class_file.exists():
            with open(class_file, "rb") as f:
                clazz = cloudpickle.load(f)
                return clazz(**kwargs)
        else:
            raise ValueError(
                f"Cannot load model ({cls.__module__}.{cls.__name__}), "
                f"{MODEL_CLASS_PKL} file not found and 'load' method isn't overriden"
            )


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
                    f"data_preprocessing_function only takes 1 argument (a pandas.DataFrame) but {sign_len} were provided."
                )
        if self.model_postprocessing_function:
            sign_len = len(signature(self.model_postprocessing_function).parameters)
            if sign_len != 1:
                raise ValueError(f"model_postprocessing_function only takes 1 argument but {sign_len} were provided.")

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
            warn_once(logger,
                      f"\nThe output of your model has shape {raw_predictions.shape}, but we expect a shape (n_entries, n_classes). \n"
                      "We will attempt to automatically reshape the output to match this format, please check that the results are consistent."
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
            warn_once(logger,
                      "Please make sure that your model's output corresponds "
                      "to the second label in classification_labels."
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
        Saving the model object.

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


class MLFlowBasedModel(WrapperModel, ABC):
    """
    An abstract base class for models that are serializable by the MLFlow library.

    This class provides functionality for saving the model with MLFlow in addition to saving other metadata with the
    `save` method. Subclasses should implement the `save_model` method to provide their own MLFlow-specific model
    saving functionality.
    """

    def save(self, local_path: Union[str, Path]) -> None:
        """
        MLFlow requires a target directory to be empty before the model is saved, thus we have to call
        save_with_mflow first and then save the rest of the metadata
        """
        if not self.id:
            self.id = uuid.uuid4()
            self._cache.set_id(str(self.id))
        self.save_model(local_path, mlflow.models.Model(model_uuid=str(self.id)))
        super().save(local_path)


class CloudpickleBasedModel(WrapperModel, ABC):
    """
    An abstract base class for models that are serializable by the cloudpickle library.
    """

    def save(self, local_path: Union[str, Path]) -> None:
        """
        TBF
        """
        super().save(local_path)
        self.save_model(local_path)

    def save_model(self, local_path: Union[str, Path]) -> None:
        try:
            model_file = Path(local_path) / "model.pkl"
            with open(model_file, "wb") as f:
                cloudpickle.dump(self.model, f, protocol=pickle.DEFAULT_PROTOCOL)
        except ValueError:
            raise ValueError(
                "We couldn't save your model with cloudpickle. Please provide us with your own "
                "serialisation method by overriding the save_model() and load_model() methods."
            )

    @classmethod
    def load_model(cls, local_dir):
        local_path = Path(local_dir)
        model_path = local_path / "model.pkl"
        if model_path.exists():
            with open(model_path, "rb") as f:
                model = cloudpickle.load(f)
                return model
        else:
            raise ValueError(
                "We couldn't load your model with cloudpickle. Please provide us with your own "
                "serialisation method by overriding the save_model() and load_model() methods."
            )


class CustomModel(BaseModel, ABC):
    """
    Helper class to extend in case a user needs to extend a BaseModel
    """

    should_save_model_class = True
