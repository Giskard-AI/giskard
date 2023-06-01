from importlib import import_module


class AutoModel:
    def __new__(cls, *args, **kw):

        libraries = {"HuggingFaceModel": {"transformers": ["PreTrainedModel"]},
                     "SKLearnModel": {"sklearn.base": ["BaseEstimator"]},
                     "CatboostModel": {"catboost": ["CatBoost", "CatBoostClassifier", "CatBoostRanker", "CatBoostRegressor"]},
                     "PyTorchModel": {"torch.nn": ["Module"]},
                     "TensorFlowModel": {"tensorflow": ["Module"]}}

        for _giskard_class, _base_libs in libraries.items():
            giskard_cls = getattr(import_module('giskard'), _giskard_class)
            for _base_lib, _base_classes in _base_libs.items():
                for _base_class in _base_classes:
                    try:
                        base_cls = getattr(import_module(_base_lib), _base_class)
                        if isinstance(kw['clf'], base_cls):
                            return giskard_cls(**kw)
                    except ImportError:
                        pass

        raise ValueError(
            'We could not infer your model library. We currently only support models from:'
            '\n- sklearn'
            '\n- pytorch'
            '\n- tensorflow'
            '\n- huggingface'
        )
