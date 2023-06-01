from pathlib import Path
from re import match
import abc
import cloudpickle, pickle
from importlib import import_module

import pandas as pd
import uuid
import numpy as np
from typing import Callable, Optional, Iterable, Any, Union
import mlflow

from giskard.models import infer_giskard_cls
from giskard.models.base import WrapperModel, MLFlowBasedModel
from giskard.core.core import ModelType


class FormalParserInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'model_predict') and
                callable(subclass.model_predict) and
                hasattr(subclass, 'save_model') and
                callable(subclass.model_predict) and
                hasattr(subclass, 'load_model') and
                callable(subclass.model_predict) or
                NotImplemented)

    def model_predict(self, df: pd.DataFrame):
        raise NotImplementedError

    def save_model(self, local_path, mlflow_meta: mlflow.models.Model):
        raise NotImplementedError

    @classmethod
    def load_model(cls, local_dir):
        raise NotImplementedError


class Model(WrapperModel):
    should_save_model_class = True

    """def __new__(cls, model: Any,
                model_type: ModelType,
                data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
                model_postprocessing_function: Callable[[Any], Any] = None,
                name: Optional[str] = None,
                feature_names: Optional[Iterable] = None,
                classification_threshold: Optional[float] = 0.5,
                classification_labels: Optional[Iterable] = None,
                **kwargs
                ):

        if not model:
            raise ValueError("The 'Model' class requires a 'model' object. In case you want to create a custom "
                             "class without a 'model' object, please use 'CustomModel' instead.")
        else:
            cls_properties = {
                name: getattr(cls, name) for name in dir(cls) if not match("__.*__", name)
            }
            giskard_cls = infer_giskard_cls(model)
            if giskard_cls:
                return type(giskard_cls.__name__, (giskard_cls,), cls_properties)(
                    model=model,
                    model_type=model_type,
                    data_preprocessing_function=data_preprocessing_function,
                    model_postprocessing_function=model_postprocessing_function,
                    name=name,
                    feature_names=feature_names,
                    classification_threshold=classification_threshold,
                    classification_labels=classification_labels,
                    **kwargs)
            else:
                return type(cls.__name__, (WrapperModel,), cls_properties)(
                    model=model,
                    model_type=model_type,
                    data_preprocessing_function=data_preprocessing_function,
                    model_postprocessing_function=model_postprocessing_function,
                    name=name,
                    feature_names=feature_names,
                    classification_threshold=classification_threshold,
                    classification_labels=classification_labels,
                    **kwargs)"""

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
            **kwargs
    ) -> None:
        super().__init__(model,
                         model_type,
                         data_preprocessing_function,
                         model_postprocessing_function,
                         name,
                         feature_names,
                         classification_threshold,
                         classification_labels)

        giskard_cls = infer_giskard_cls(model)
        if not giskard_cls:
            giskard_cls = WrapperModel

        self.inferred_model = giskard_cls(
            model=model,
            model_type=model_type,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            name=name,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            **kwargs)

    def model_predict(self, df):
        self.inferred_model.model_predict(df)

    def save(self, local_path: Union[str, Path]) -> None:

        if isinstance(self.inferred_model, MLFlowBasedModel):
            if not self.id:
                self.id = uuid.uuid4()
            self.inferred_model.save_model(local_path, mlflow.models.Model(model_uuid=str(self.id)))
            super().save(local_path)
        else:
            super().save(local_path)
            self.save_model(local_path)
