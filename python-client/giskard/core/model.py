import logging
import pickle
import posixpath
import tempfile
from pathlib import Path
from typing import *

import cloudpickle
import mlflow.sklearn
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

logger = logging.getLogger(__name__)


class ModelPredictionResults(BaseModel):
    raw: Any
    prediction: Any
    raw_prediction: Any
    probabilities: Optional[Any]
    all_predictions: Optional[Any]


class Model:
    meta: ModelMeta
    model: PyFuncModel
    data_preparation_function: any

    def __init__(self,
                 model,
                 model_type: Union[SupportedModelTypes, str],
                 name: str = None,
                 data_preparation_function=None,
                 feature_names=None,
                 classification_threshold=0.5,
                 classification_labels=None) -> None:
        self.model = model
        self.data_preparation_function = data_preparation_function

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
            feature_names=feature_names,
            classification_labels=classification_labels,
            classification_threshold=classification_threshold
        )

    @property
    def is_classification(self):
        return self.meta.model_type == SupportedModelTypes.CLASSIFICATION

    @property
    def is_regression(self):
        return self.meta.model_type == SupportedModelTypes.REGRESSION

    def save(self, client: GiskardClient, project_key, validate_ds=None):
        from giskard.core.model_validation import validate_model

        validate_model(model=self, validate_ds=validate_ds)
        with tempfile.TemporaryDirectory(prefix="giskard-model-") as f:
            info = self.save_to_local_dir(f)
            self.save_data_preparation_funciton(f)
            if client is not None:
                client.log_artifacts(f, posixpath.join(project_key, "models", info.model_uuid))
                client.save_model_meta(project_key,
                                       info.model_uuid,
                                       self.meta,
                                       info.flavors['python_function']['python_version'],
                                       get_size(f))
        return info.model_uuid

    def save_data_preparation_funciton(self, path):
        if self.data_preparation_function:
            with open(Path(path) / "giskard-data-prep.pkl", 'wb') as f:
                cloudpickle.dump(self.data_preparation_function, f, protocol=pickle.DEFAULT_PROTOCOL)

    @classmethod
    def read_data_preparation_function_from_artifact(cls, local_path: str):
        local_path = Path(local_path)
        file_path = local_path / "giskard-data-prep.pkl"
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return cloudpickle.load(f)

    def save_to_local_dir(self, local_path):
        if self.is_classification:
            pyfunc_predict_fn = 'predict_proba'
        elif self.is_regression:
            pyfunc_predict_fn = 'predict'
        else:
            raise ValueError('Unsupported model type')

        mlflow.sklearn.save_model(self.model, path=local_path, pyfunc_predict_fn=pyfunc_predict_fn)
        info = mlflow.models.Model.load(local_path)

        with open(Path(local_path) / 'giskard-model-meta.yaml', 'w') as f:
            yaml.dump(
                {
                    "language_version": info.flavors['python_function']['python_version'],
                    "language": "PYTHON",
                    "model_type": self.meta.model_type.name.upper(),
                    "threshold": self.meta.classification_threshold,
                    "feature_names": self.meta.feature_names,
                    "classification_labels": self.meta.classification_labels,
                    "id": info.model_uuid,
                    "name": self.meta.name,
                    "size": get_size(local_path),
                }, f, default_flow_style=False)

        return info

    @classmethod
    def read_model_from_local_dir(cls, local_path: str):
        return mlflow.pyfunc.load_model(local_path)

    @classmethod
    def load(cls, client: GiskardClient, project_key, model_id):
        local_dir = settings.home_dir / settings.cache_dir / project_key / "models" / model_id
        if client is None:
            # internal worker case, no token based http client
            assert local_dir.exists(), f"Cannot find existing model {project_key}.{model_id}"
            with open(Path(local_dir) / 'giskard-model-meta.yaml') as f:
                saved_meta = yaml.load(f, Loader=yaml.Loader)
                meta = ModelMeta(
                    name=saved_meta['name'],
                    model_type=SupportedModelTypes[saved_meta['model_type']],
                    feature_names=saved_meta['feature_names'],
                    classification_labels=saved_meta['classification_labels'],
                    classification_threshold=saved_meta['threshold'],
                )
        else:
            client.load_artifact(local_dir, posixpath.join(project_key, "models", model_id))
            meta = client.load_model_meta(project_key, model_id)
        return cls(
            model=cls.read_model_from_local_dir(local_dir),
            data_preparation_function=cls.read_data_preparation_function_from_artifact(local_dir),
            **meta.__dict__
        )

    def prepare_data_and_predict(self, data):
        if self.data_preparation_function:
            data = self.data_preparation_function(data)
        return self._raw_predict(data)

    def _raw_predict(self, data):
        return self.model.predict(data)

    def predict(self, dataset: Dataset) -> ModelPredictionResults:
        timer = Timer()
        df = self.prepare_dataframe(dataset)
        raw_prediction = self.prepare_data_and_predict(df)
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

    def prepare_dataframe(self, dataset: Dataset):
        df = dataset.df.copy()
        column_types = dict(dataset.column_types) if dataset.column_types else None
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

        if column_types:
            df = Dataset.cast_column_to_types(df, column_types)
        return df
