from importlib import import_module
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


def make_model(clf, *args, **kwargs):
    for giskard_class, _base_libs in _libraries.items():
        base_libs = [get_class(*_base_lib) for _base_lib in _base_libs]
        try:
            if isinstance(clf, tuple(base_libs)):
                return giskard_class(clf, *args, **kwargs)
        except ImportError:
            pass

    raise ValueError(
        'We could not infer your model library. We currently only support models from:'
        '\n- sklearn'
        '\n- pytorch'
        '\n- tensorflow'
        '\n- huggingface'
    )
