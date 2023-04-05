import importlib
import logging
import pickle
import platform
import posixpath
import tempfile
import uuid
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Optional, Any, Union
import cloudpickle
import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel
from inspect import signature
from giskard.client.giskard_client import GiskardClient
from giskard.core.core import ModelMeta
from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.ml_worker.utils.logging import Timer
from giskard.path_utils import get_size
from giskard.settings import settings

try:
    import mlflow
    from mlflow.pyfunc import PyFuncModel
except ImportError:
    pass

MODEL_CLASS_PKL = "ModelClass.pkl"

logger = logging.getLogger(__name__)


class ModelPredictionResults(BaseModel):
    raw: Any
    prediction: Any
    raw_prediction: Any
    probabilities: Optional[Any]
    all_predictions: Optional[Any]


class BaseModel(ABC):
    should_save_model_class = False
    id: uuid.UUID = None

    def __init__(
            self,
            model_type: Union[SupportedModelTypes, str],
            name: str = None,
            feature_names=None,
            classification_threshold=0.5,
            classification_labels=None,
    ) -> None:
        if type(model_type) == str:
            try:
                model_type = SupportedModelTypes(model_type)
            except ValueError as e:
                available_values = {i.value for i in SupportedModelTypes}
                raise ValueError(
                    f'Invalid model type value "{model_type}". Available values are: {available_values}'
                ) from e

        if classification_labels is not None:
            if len(classification_labels) != len(set(classification_labels)):
                raise ValueError(
                    "Duplicates are found in 'classification_labels', please only provide unique values."
                )

        self.meta = ModelMeta(
            name=name if name is not None else self.__class__.__name__,
            model_type=model_type,
            feature_names=list(feature_names) if feature_names else None,
            classification_labels=list(classification_labels) if classification_labels is not None else None,
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
        with open(Path(local_path) / "giskard-model-meta.yaml", "w") as f:
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
        if self.should_save_model_class:
            self.save_model_class(local_path)
        self.save_meta(local_path)

    def save_model_class(self, local_path):
        class_file = Path(local_path) / MODEL_CLASS_PKL
        with open(class_file, "wb") as f:
            cloudpickle.dump(self.__class__, f, protocol=pickle.DEFAULT_PROTOCOL)

    def prepare_dataframe(self, dataset: Dataset):
        df = dataset.df.copy()
        column_dtypes = dict(dataset.column_dtypes) if dataset.column_dtypes else None

        if column_dtypes:
            for cname, ctype in column_dtypes.items():
                if cname not in df:
                    df[cname] = None

        if dataset.target:
            if dataset.target in df.columns:
                df.drop(dataset.target, axis=1, inplace=True)
            if column_dtypes and dataset.target in column_dtypes:
                del column_dtypes[dataset.target]

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
        timer = Timer()
        df = self.prepare_dataframe(dataset)

        raw_prediction = self.predict_df(df)

        if self.is_regression:
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

    def upload(self, client: GiskardClient, project_key, validate_ds=None) -> None:
        from giskard.core.model_validation import validate_model

        validate_model(model=self, validate_ds=validate_ds)
        with tempfile.TemporaryDirectory(prefix="giskard-model-") as f:
            self.save(f)

            if client is not None:
                client.log_artifacts(f, posixpath.join(project_key, "models", str(self.id)))
                client.save_model_meta(project_key, self.id, self.meta, platform.python_version(), get_size(f))

    @classmethod
    def download(cls, client: GiskardClient, project_key, model_id):
        local_dir = settings.home_dir / settings.cache_dir / project_key / "models" / model_id
        if client is None:
            # internal worker case, no token based http client
            assert local_dir.exists(), f"Cannot find existing model {project_key}.{model_id} in {local_dir}"
            with open(Path(local_dir) / "giskard-model-meta.yaml") as f:
                saved_meta = yaml.load(f, Loader=yaml.Loader)
                meta = ModelMeta(
                    name=saved_meta["name"],
                    model_type=SupportedModelTypes[saved_meta["model_type"]],
                    feature_names=saved_meta["feature_names"],
                    classification_labels=saved_meta["classification_labels"],
                    classification_threshold=saved_meta["threshold"],
                    loader_module=saved_meta["loader_module"],
                    loader_class=saved_meta["loader_class"],
                )
        else:
            client.load_artifact(local_dir, posixpath.join(project_key, "models", model_id))
            meta_response = client.load_model_meta(project_key, model_id)
            # internal worker case, no token based http client
            assert local_dir.exists(), f"Cannot find existing model {project_key}.{model_id} in {local_dir}"
            with open(Path(local_dir) / "giskard-model-meta.yaml") as f:
                file_meta = yaml.load(f, Loader=yaml.Loader)
                meta = ModelMeta(
                    name=meta_response["name"],
                    model_type=SupportedModelTypes[meta_response["modelType"]],
                    feature_names=meta_response["featureNames"],
                    classification_labels=meta_response["classificationLabels"],
                    classification_threshold=meta_response["threshold"],
                    loader_module=file_meta["loader_module"],
                    loader_class=file_meta["loader_class"],
                )

        clazz = cls.determine_model_class(meta, local_dir)

        constructor_params = meta.__dict__
        del constructor_params["loader_module"]
        del constructor_params["loader_class"]
        return clazz.load(local_dir, **constructor_params)

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
    A subclass of a BaseModel that wraps an existing model object (clf) and uses it to make inference
    This class introduces a `data_preprocessing_function` which can be used
    to preprocess incoming data before it's passed
    to the underlying model
    """

    clf: PyFuncModel
    data_preprocessing_function: any
    model_postprocessing_function: any

    def __init__(
            self,
            clf,
            model_type: Union[SupportedModelTypes, str],
            data_preprocessing_function=None,
            model_postprocessing_function=None,
            name: str = None,
            feature_names=None,
            classification_threshold=0.5,
            classification_labels=None,
    ) -> None:
        super().__init__(model_type, name, feature_names, classification_threshold, classification_labels)
        self.clf = clf
        self.data_preprocessing_function = data_preprocessing_function
        self.model_postprocessing_function = model_postprocessing_function

        if self.data_preprocessing_function:
            sign_len = len(signature(self.data_preprocessing_function).parameters)
            print(sign_len)
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

    def predict_df(self, df):
        if self.data_preprocessing_function:
            df = self.data_preprocessing_function(df)

        raw_prediction = self.clf_predict(df)
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
                f"\nThe output of your clf has shape {raw_predictions.shape}, but we expect a shape (n_entries, n_classes). \n"
                "We will attempt to automatically reshape the output to match this format, please check that the results are consistent.",
                exc_info=True,
            )

            raw_predictions = raw_predictions.squeeze(tuple(range(1, raw_predictions.ndim - 1)))

            if raw_predictions.ndim > 2:
                raise ValueError(
                    f"The output of your clf has shape {raw_predictions.shape}, but we expect it to be (n_entries, n_classes)."
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
                f"The output of your clf has shape {raw_predictions.shape}, but we expect it to be (n_entries, n_classes), \n"
                f"where `n_classes` is the number of classes in your model output ({len(self.meta.classification_labels)} in this case)."
            )

        return raw_predictions

    @abstractmethod
    def clf_predict(self, df):
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
        return cls(clf=cls.load_clf(local_dir), **kwargs)

    @classmethod
    @abstractmethod
    def load_clf(cls, local_dir):
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
    def save(self, local_path: Union[str, Path]) -> None:
        """
        MLFlow requires a target directory to be empty before the model is saved, thus we have to call
        save_with_mflow first and then save the rest of the metadata
        """
        if not self.id:
            self.id = uuid.uuid4()
        self.save_with_mlflow(local_path, mlflow.models.Model(model_uuid=str(self.id)))
        super().save(local_path)

    @abstractmethod
    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        ...


class CustomModel(BaseModel, ABC):
    """
    Helper class to extend in case a user needs to extend a BaseModel
    """

    should_save_model_class = True
