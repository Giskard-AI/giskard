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
import mlflow
import numpy
import pandas as pd
import yaml
from mlflow.pyfunc import PyFuncModel
from pydantic import BaseModel

from giskard.client.giskard_client import GiskardClient
from giskard.core.core import ModelMeta
from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.core.dataset import Dataset
from giskard.ml_worker.utils.logging import Timer
from giskard.path_utils import get_size
from giskard.settings import settings

MODEL_CLASS_PKL = "ModelClass.pkl"

logger = logging.getLogger(__name__)


class ModelPredictionResults(BaseModel):
    raw: Any
    prediction: Any
    raw_prediction: Any
    probabilities: Optional[Any]
    all_predictions: Optional[Any]


class Model(ABC):
    should_save_model_class = False
    id: uuid.UUID = None

    def __init__(self,
                 model_type: Union[SupportedModelTypes, str],
                 name: str = None,
                 feature_names=None,
                 classification_threshold=0.5,
                 classification_labels=None) -> None:

        if type(model_type) == str:
            try:
                model_type = SupportedModelTypes(model_type)
            except ValueError as e:
                available_values = {i.value for i in SupportedModelTypes}
                raise ValueError(
                    f'Invalid model type value "{model_type}". Available values are: {available_values}') from e

        self.meta = ModelMeta(
            name=name if name is not None else self.__class__.__name__,
            model_type=model_type,
            feature_names=list(feature_names) if feature_names else None,
            classification_labels=list(classification_labels) if classification_labels is not None else None,
            classification_threshold=classification_threshold,
            loader_class=self.__class__.__name__,
            loader_module=self.__module__
        )

    @property
    def is_classification(self):
        return self.meta.model_type == SupportedModelTypes.CLASSIFICATION

    @property
    def is_regression(self):
        return self.meta.model_type == SupportedModelTypes.REGRESSION

    @classmethod
    def determine_model_class(cls, meta, local_dir):
        class_file = Path(local_dir) / MODEL_CLASS_PKL
        if class_file.exists():
            with open(class_file, 'rb') as f:
                clazz = cloudpickle.load(f)
                if issubclass(clazz, Model):
                    raise ValueError(f"Unknown model class: {clazz}. Models should inherit from 'Model' class")
                return clazz
        else:
            return getattr(importlib.import_module(meta.loader_module), meta.loader_class)

    def save_meta(self, local_path):
        with open(Path(local_path) / 'giskard-model-meta.yaml', 'w') as f:
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
                    "id": self.id,
                    "name": self.meta.name,
                    "size": get_size(local_path),
                }, f, default_flow_style=False)

    def save(self, local_path: Union[str, Path]) -> None:
        if self.id is None:
            self.id = uuid.uuid4()
        if self.should_save_model_class:
            self.save_model_class(local_path)
        self.save_meta(local_path)

    def save_model_class(self, local_path):
        class_file = Path(local_path) / MODEL_CLASS_PKL
        with open(class_file, 'wb') as f:
            cloudpickle.dump(self.__class__, f, protocol=pickle.DEFAULT_PROTOCOL)

    def prepare_dataframe(self, dataset: Dataset):
        df = dataset.df.copy()
        column_types = dict(dataset.column_types) if dataset.column_types else None

        if column_types:
            for cname, ctype in column_types.items():
                if cname not in df:
                    df[cname] = None

        if dataset.target:
            if dataset.target in df.columns:
                df.drop(dataset.target, axis=1, inplace=True)
            if column_types and dataset.target in column_types:
                del column_types[dataset.target]

        if self.meta.feature_names:
            if set(self.meta.feature_names) > set(df.columns):
                column_names = set(self.meta.feature_names) - set(df.columns)
                raise ValueError(
                    f"The following columns are not found in the dataset: {', '.join(sorted(column_names))}"
                )
            df = df[self.meta.feature_names]
            if column_types:
                column_types = {k: v for k, v in column_types.items() if k in self.meta.feature_names}

        for cname, ctype in column_types.items():
            if cname not in df:
                df[cname] = None

        if column_types:
            df = Dataset.cast_column_to_types(df, column_types)
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
            labels = numpy.array(self.meta.classification_labels)
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

class WrapperModel(Model, ABC):
    """
    A subclass of a Model that wraps an existing model object (clf) and uses it to make inference
    This class introduces a `data_preprocessing_function` which can be used
    to preprocess incoming data before it's passed
    to the underlying model
    """
    clf: PyFuncModel
    data_preprocessing_function: any
    model_postprocessing_function: any

    def __init__(self,
                 clf,
                 model_type: Union[SupportedModelTypes, str],
                 data_preprocessing_function=None,
                 model_postprocessing_function=None,
                 name: str = None, feature_names=None,
                 classification_threshold=0.5, classification_labels=None) -> None:

        super().__init__(model_type=model_type, name=name, feature_names=feature_names,
                         classification_threshold=classification_threshold,
                         classification_labels=classification_labels)
        self.clf = clf
        self.data_preprocessing_function = data_preprocessing_function
        self.model_postprocessing_function = model_postprocessing_function

    def predict_df(self, df):
        if self.data_preprocessing_function:
            df = self.data_preprocessing_function(df)
        raw_prediction = self.clf_predict(df)

        if not self.model_postprocessing_function:
            return raw_prediction
        else:
            return self.model_postprocessing_function(raw_prediction)

    @abstractmethod
    def clf_predict(self, df):
        ...

    def upload(self, client: GiskardClient, project_key, validate_ds=None) -> None:
        from giskard.core.model_validation import validate_model

        validate_model(model=self, validate_ds=validate_ds)
        with tempfile.TemporaryDirectory(prefix="giskard-model-") as f:
            self.save(f)

            if client is not None:
                client.log_artifacts(f, posixpath.join(project_key, "models", str(self.id)))
                client.save_model_meta(project_key,
                                       self.id,
                                       self.meta,
                                       platform.python_version(),
                                       get_size(f))

    @classmethod
    def download(cls, client: GiskardClient, project_key, model_id):
        local_dir = settings.home_dir / settings.cache_dir / project_key / "models" / model_id
        if client is None:
            # internal worker case, no token based http client
            assert local_dir.exists(), f"Cannot find existing model {project_key}.{model_id} in {local_dir}"
            with open(Path(local_dir) / 'giskard-model-meta.yaml') as f:
                saved_meta = yaml.load(f, Loader=yaml.Loader)
                meta = ModelMeta(
                    name=saved_meta['name'],
                    model_type=SupportedModelTypes[saved_meta['model_type']],
                    feature_names=saved_meta['feature_names'],
                    classification_labels=saved_meta['classification_labels'],
                    classification_threshold=saved_meta['threshold'],
                    loader_module=saved_meta['loader_module'],
                    loader_class=saved_meta['loader_class']
                )
        else:
            client.load_artifact(local_dir, posixpath.join(project_key, "models", model_id))

            assert local_dir.exists(), f"Cannot find existing model {project_key}.{model_id}"
            with open(Path(local_dir) / 'giskard-model-meta.yaml') as f:
                saved_meta = yaml.load(f, Loader=yaml.Loader)
            res = client.load_model_meta(project_key, model_id)
            meta = ModelMeta(
                name=res['name'],
                feature_names=res['featureNames'],
                model_type=SupportedModelTypes[res['modelType']],
                classification_labels=res['classificationLabels'],
                classification_threshold=res['threshold'],
                loader_module=saved_meta['loader_module'],
                loader_class=saved_meta['loader_class']
            )
        clazz = cls.determine_model_class(meta, local_dir)
        return clazz(
            clf=clazz.read_model_from_local_dir(local_dir),
            data_preprocessing_function=clazz.load_data_preprocessing_function(local_dir),
            model_postprocessing_function=clazz.read_model_postprocessing_function_from_artifact(local_dir),
            **meta.__dict__
        )

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)

        if self.data_preprocessing_function:
            self.save_data_preprocessing_function(local_path)
        if self.model_postprocessing_function:
            self.save_model_postprocessing_function(local_path)

    def save_data_preprocessing_function(self, local_path: Union[str, Path]):
        with open(Path(local_path) / "giskard-data-preprocessing-function.pkl", 'wb') as f:
            cloudpickle.dump(self.data_preprocessing_function, f, protocol=pickle.DEFAULT_PROTOCOL)

    def save_model_postprocessing_function(self, local_path: Union[str, Path]):
        with open(Path(local_path) / "giskard-model-postprocessing-function.pkl", 'wb') as f:
            cloudpickle.dump(self.model_postprocessing_function, f, protocol=pickle.DEFAULT_PROTOCOL)

    @staticmethod
    def load_data_preprocessing_function(local_path: Union[str, Path]):
        local_path = Path(local_path)
        file_path = local_path / "giskard-data-preprocessing-function.pkl"
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return cloudpickle.load(f)

    @staticmethod
    def read_model_postprocessing_function_from_artifact(local_path: str):
        local_path = Path(local_path)
        file_path = local_path / "giskard-model-postprocessing-function.pkl"
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return cloudpickle.load(f)


class MLFlowBasedModel(WrapperModel, ABC):
    def save(self, local_path: Union[str, Path]) -> None:
        """
        MLFlow requires a target directory to be empty before the model is saved, thus we have to call
        save_with_mflow first and then save the rest of the metadata
        """
        if not self.id:
            self.id = uuid.uuid4()
        self.save_with_mflow(local_path, mlflow.models.Model(model_uuid=str(self.id)))
        super().save(local_path)

    @abstractmethod
    def save_with_mflow(self, local_path, mlflow_meta: mlflow.models.Model):
        ...


class CustomModel(Model, ABC):
    """
    Helper class to extend in case a user needs to extend a Model
    """
    should_save_model_class = True
