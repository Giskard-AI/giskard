from re import match
import pandas as pd
from typing import Callable, Optional, Iterable, Any

from giskard.models import infer_giskard_cls
from giskard.models.base import WrapperModel
from giskard.core.core import ModelType


class Model:
    should_save_model_class = True

    def __new__(cls, model: Any,
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
                    classification_labels=classification_labels)
