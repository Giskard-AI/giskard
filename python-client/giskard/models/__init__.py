from importlib import import_module
import torch  # TODO: to be omitted in another PR
from typing import Union
from giskard.core.core import SupportedModelTypes
from giskard.models.sklearn import SKLearnModel
from giskard.models.catboost import CatboostModel
from giskard.models.pytorch import PyTorchModel
from giskard.models.tensorflow import TensorFlowModel
from giskard.models.huggingface import HuggingFaceModel

# format: dict[GiskardModel: list(tuple(module, base_class))]
_libraries = {HuggingFaceModel: [("transformers", "PreTrainedModel")],
              SKLearnModel: [("sklearn.base", "BaseEstimator")],
              CatboostModel: [("catboost", "CatBoost"),
                              ("catboost", "CatBoostClassifier"),
                              ("catboost", "CatBoostRanker"),
                              ("catboost", "CatBoostRegressor")],
              PyTorchModel: [("torch.nn", "Module")],
              TensorFlowModel: [("tensorflow", "Module")]}


def get_class(_lib, _class):
    return getattr(import_module(_lib), _class)


def model(clf,
          model_type: Union[SupportedModelTypes, str],
          data_preprocessing_function=None,
          model_postprocessing_function=None,
          name: str = None,
          feature_names=None,
          classification_threshold=0.5,
          classification_labels=None,
          **kwargs):
    for giskard_class, _base_libs in _libraries.items():
        base_libs = [get_class(*_base_lib) for _base_lib in _base_libs]
        try:
            if isinstance(clf, tuple(base_libs)):
                return giskard_class(clf,
                                     model_type,
                                     data_preprocessing_function,
                                     model_postprocessing_function,
                                     name,
                                     feature_names,
                                     classification_threshold,
                                     classification_labels,
                                     **kwargs)
        except ImportError:
            pass

    raise ValueError(
        'We could not infer your model library. We currently only support models from:'
        '\n- sklearn'
        '\n- pytorch'
        '\n- tensorflow'
        '\n- huggingface'
    )


def model_from_sklearn(clf,
                       model_type: Union[SupportedModelTypes, str],
                       name: str = None,
                       data_preprocessing_function=None,
                       model_postprocessing_function=None,
                       feature_names=None,
                       classification_threshold=0.5,
                       classification_labels=None):
    return SKLearnModel(clf,
                        model_type,
                        name,
                        data_preprocessing_function,
                        model_postprocessing_function,
                        feature_names,
                        classification_threshold,
                        classification_labels)


def model_from_catboost(clf,
                        model_type: Union[SupportedModelTypes, str],
                        name: str = None,
                        data_preprocessing_function=None,
                        model_postprocessing_function=None,
                        feature_names=None,
                        classification_threshold=0.5,
                        classification_labels=None):
    return CatboostModel(clf,
                         model_type,
                         name,
                         data_preprocessing_function,
                         model_postprocessing_function,
                         feature_names,
                         classification_threshold,
                         classification_labels)


def model_from_pytorch(clf,
                       model_type: Union[SupportedModelTypes, str],
                       torch_dtype=torch.float32,
                       device="cpu",
                       name: str = None,
                       data_preprocessing_function=None,
                       model_postprocessing_function=None,
                       feature_names=None,
                       classification_threshold=0.5,
                       classification_labels=None,
                       iterate_dataset=True):
    return PyTorchModel(clf,
                        model_type,
                        torch_dtype,
                        device,
                        name,
                        data_preprocessing_function,
                        model_postprocessing_function,
                        feature_names,
                        classification_threshold,
                        classification_labels,
                        iterate_dataset)


def model_from_tensorflow(clf,
                          model_type: Union[SupportedModelTypes, str],
                          name: str = None,
                          data_preprocessing_function=None,
                          model_postprocessing_function=None,
                          feature_names=None,
                          classification_threshold=0.5,
                          classification_labels=None):
    return TensorFlowModel(clf,
                           model_type,
                           name,
                           data_preprocessing_function,
                           model_postprocessing_function,
                           feature_names,
                           classification_threshold,
                           classification_labels)


def model_from_huggingface(clf,
                           model_type: Union[SupportedModelTypes, str],
                           name: str = None,
                           data_preprocessing_function=None,
                           model_postprocessing_function=None,
                           feature_names=None,
                           classification_threshold=0.5,
                           classification_labels=None):
    return HuggingFaceModel(clf,
                            model_type,
                            name,
                            data_preprocessing_function,
                            model_postprocessing_function,
                            feature_names,
                            classification_threshold,
                            classification_labels)
