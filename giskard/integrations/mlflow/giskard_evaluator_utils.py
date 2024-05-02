import inspect
import logging
import re
from inspect import isfunction

from giskard.core.core import SupportedModelTypes
from giskard.datasets import Dataset
from giskard.models import Model
from giskard.scanner import scan

logger = logging.getLogger(__name__)

gsk_model_types = {
    "classifier": SupportedModelTypes.CLASSIFICATION,
    "regressor": SupportedModelTypes.REGRESSION,
    "text": SupportedModelTypes.TEXT_GENERATION,
    "question-answering": SupportedModelTypes.TEXT_GENERATION,
}
alphanumeric_map = {
    ">=": "greater than or equal to",
    ">": "greater than",
    "<=": "less than or equal to",
    "<": "less than",
    "==": "equal to",
    "=": "equal to",
    "!=": "different of",
}
control_chars_map = {"\\r": "carriage return", "\\b": "backspace"}


def process_text(some_string):
    for k, v in alphanumeric_map.items():
        some_string = some_string.replace(k, v)
    for k, v in control_chars_map.items():
        some_string = some_string.replace(k, v)

    some_string = some_string.replace("data slice", "data slice -")
    some_string = re.sub(r"[^A-Za-z0-9_\-. /]+", "", some_string)

    return some_string


def setup_dataset(dataset, evaluator_config):
    data = dataset.features_data.copy()
    target = dataset.targets_name if hasattr(dataset, "targets_name") else None
    if target is not None:
        data[target] = dataset.labels_data
    dataset_config = evaluator_config.get("dataset_config", None)
    if dataset_config is None:
        return Dataset(df=data, target=target, name=dataset.name)

    config_set = set(dataset_config.keys())
    sign = inspect.signature(Dataset)
    sign_set = set(sign.parameters.keys())
    if config_set.issubset(sign_set):
        if "target" not in config_set:
            dataset_config["target"] = target
        if "name" not in config_set:
            dataset_config["name"] = dataset.name

        return Dataset(df=data, **dataset_config)

    raise ValueError(
        f"The provided parameters {config_set - sign_set} in dataset_config are not valid. "
        "Make sure to pass only the attributes of giskard.Dataset "
        "(see https://docs.giskard.ai/en/stable/reference/datasets)."
    )


def setup_model(model, model_type, feature_names, evaluator_config):
    model_config = evaluator_config.get("model_config", None)

    # by default wrap the "predict" bound method of the pyfunc model (or any other type that has predict)
    if hasattr(model, "predict"):
        model_to_be_wrapped = model.predict
    elif isfunction(model):
        model_to_be_wrapped = model
    else:
        raise ValueError(
            "The model types supported by the giskard evaluator are: "
            "(1) a model that has 'predict' bound method or (2) a callable function. "
            "In both cases, the model should have a pandas.DataFrame as input and a list as output."
        )

    if model_config is None:
        return Model(model=model_to_be_wrapped, model_type=gsk_model_types[model_type], feature_names=feature_names)

    config_set = set(model_config.keys())
    sign = inspect.signature(Model)
    sign_set = set(sign.parameters.keys())
    if config_set.issubset(sign_set):
        if "model_type" not in config_set:
            model_config["model_type"] = gsk_model_types[model_type]
        if "feature_names" not in config_set:
            model_config["feature_names"] = feature_names

        return Model(model=model_to_be_wrapped, **model_config)

    raise ValueError(
        f"The provided parameters {config_set - sign_set} in model_config are not valid. "
        "Make sure to pass only the attributes of giskard.Model "
        "(see https://docs.giskard.ai/en/stable/reference/models)."
    )


def setup_scan(giskard_model, giskard_dataset, evaluator_config):
    scan_config = evaluator_config.get("scan_config", None)
    if scan_config is None:
        return scan(model=giskard_model, dataset=giskard_dataset)

    config_set = set(scan_config.keys())
    sign = inspect.signature(scan)
    sign_set = set(sign.parameters.keys())
    if config_set.issubset(sign_set):
        return scan(model=giskard_model, dataset=giskard_dataset, **scan_config)

    raise ValueError(
        f"The provided parameters {config_set - sign_set} in scan_config are not valid. "
        "Make sure to pass only the attributes of giskard.scan."
    )
