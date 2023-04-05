from importlib import import_module
import torch  # TODO: to be omitted in another PR
from typing import Union

from giskard.core.core import SupportedModelTypes


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
    _libraries = {
        ("giskard.models.huggingface", "HuggingFaceModel"): [("transformers", "PreTrainedModel")],
        ("giskard.models.sklearn", "SKLearnModel"): [("sklearn.base", "BaseEstimator")],
        ("giskard.models.catboost", "CatboostModel"): [("catboost", "CatBoost")],
        ("giskard.models.pytorch", "PyTorchModel"): [("torch.nn", "Module")],
        ("giskard.models.tensorflow", "TensorFlowModel"): [("tensorflow", "Module")]
    }

    for _giskard_class, _base_libs in _libraries.items():
        try:
            giskard_class = get_class(*_giskard_class)
            base_libs = [get_class(*_base_lib) for _base_lib in _base_libs]
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
    from giskard import SKLearnModel
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
    from giskard import CatboostModel
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
                       torch_dtype=None,
                       device="cpu",
                       name: str = None,
                       data_preprocessing_function=None,
                       model_postprocessing_function=None,
                       feature_names=None,
                       classification_threshold=0.5,
                       classification_labels=None,
                       iterate_dataset=True):
    from giskard import PyTorchModel
    import torch
    torch_dtype = torch.float32 if not torch_dtype else torch_dtype
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
    from giskard import TensorFlowModel
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
    from giskard import HuggingFaceModel
    return HuggingFaceModel(clf,
                            model_type,
                            name,
                            data_preprocessing_function,
                            model_postprocessing_function,
                            feature_names,
                            classification_threshold,
                            classification_labels)
