import pandas as pd
import re
import logging
import inspect
from mlflow import MlflowClient
from mlflow.models.evaluation import ModelEvaluator

from ...models.automodel import Model
from ...datasets.base import Dataset
from ...scanner import scan
from ...core.core import SupportedModelTypes
from ...core.model_validation import ValidationFlags
from ...utils.analytics_collector import analytics
from ...utils import fullname

logger = logging.getLogger(__name__)

gsk_model_types = {
    "classifier": SupportedModelTypes.CLASSIFICATION,
    "regressor": SupportedModelTypes.REGRESSION,
    "text": SupportedModelTypes.TEXT_GENERATION
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


class PyFuncModel(Model):
    def model_predict(self, df):
        return self.model.predict(df)


def process_text(some_string):
    for k, v in alphanumeric_map.items():
        some_string = some_string.replace(k, v)
    some_string = some_string.replace("data slice", "data slice -")
    some_string = re.sub(r'[^A-Za-z0-9_\-. /]+', '', some_string)

    return some_string


def setup_dataset(dataset, evaluator_config):
    data = dataset.features_data.copy()
    data[dataset.targets_name] = dataset.labels_data
    dataset_config = evaluator_config.get("dataset_config", None)
    if dataset_config is None:
        return Dataset(df=data, target=dataset.targets_name, name=dataset.name)
    else:
        config_set = set(dataset_config.keys())
        sign = inspect.signature(Dataset)
        sign_set = set(sign.parameters.keys())
        if config_set.issubset(sign_set):
            if "target" not in config_set:
                dataset_config["target"] = dataset.targets_name
            if "name" not in config_set:
                dataset_config["name"] = dataset.name

            return Dataset(df=data, **dataset_config)
        else:
            raise ValueError(f"The provided parameters {config_set - sign_set} in dataset_config are not valid. "
                             f"Make sure to pass only the attributes of giskard.Dataset "
                             f"(see https://docs.giskard.ai/en/latest/reference/datasets).")


def setup_model(model, model_type, feature_names, evaluator_config):
    model_config = evaluator_config.get("model_config", None)
    if model_config is None:
        return PyFuncModel(model=model,
                           model_type=gsk_model_types[model_type],
                           feature_names=feature_names)
    else:
        config_set = set(model_config.keys())
        sign = inspect.signature(Model)
        sign_set = set(sign.parameters.keys())
        if config_set.issubset(sign_set):
            if "model_type" not in config_set:
                model_config["model_type"] = gsk_model_types[model_type]
            if "feature_names" not in config_set:
                model_config["feature_names"] = feature_names

            return PyFuncModel(model=model,
                               **model_config)
        else:
            raise ValueError(f"The provided parameters {config_set - sign_set} in model_config are not valid. "
                             f"Make sure to pass only the attributes of giskard.Model "
                             f"(see https://docs.giskard.ai/en/latest/reference/models).")


def setup_scan(giskard_model, giskard_dataset, evaluator_config):
    validation_flags = ValidationFlags()
    validation_flags.model_loading_and_saving = False

    scan_config = evaluator_config.get("scan_config", None)
    if scan_config is None:
        return scan(model=giskard_model, dataset=giskard_dataset, validation_flags=validation_flags)
    else:
        config_set = set(scan_config.keys())
        sign = inspect.signature(scan)
        sign_set = set(sign.parameters.keys())
        if config_set.issubset(sign_set):
            return scan(model=giskard_model, dataset=giskard_dataset, validation_flags=validation_flags, **scan_config)
        else:
            raise ValueError(f"The provided parameters {config_set - sign_set} in scan_config are not valid. "
                             f"Make sure to pass only the attributes of giskard.scan.")


class GiskardEvaluator(ModelEvaluator):
    def can_evaluate(self, model_type, **kwargs):
        return model_type in ["classifier", "regressor", "text"]

    def _wrap_dataset(self, dataset):
        if not isinstance(dataset.features_data, pd.DataFrame):
            raise ValueError("Only pd.DataFrame are currently supported by the giskard evaluator.")
        else:
            try:
                giskard_dataset = setup_dataset(dataset, self.evaluator_config)

                # log dataset
                giskard_dataset.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
                return giskard_dataset
            except Exception as e:
                analytics.track(
                    "mlflow_integration:wrapping_dataset:error",
                    {
                        "mlflow_run_id": self.run_id,
                        "error": str(e),
                    },
                )
                raise ValueError("An error occurred while wrapping the dataset. "
                                 "Please submit the traceback as a GitHub issue in the following "
                                 "repository for further assistance: https://github.com/Giskard-AI/giskard.") from e

    def _wrap_model(self, model, model_type, feature_names):
        try:
            giskard_model = setup_model(model, model_type, feature_names, self.evaluator_config)
            return giskard_model
        except Exception as e:
            analytics.track(
                "mlflow_integration:wrapping_model:error",
                {
                    "mlflow_run_id": self.run_id,
                    "error": str(e),
                },
            )
            raise ValueError("An error occurred while wrapping the model. "
                             "Please submit the traceback as a GitHub issue in the following "
                             "repository for further assistance: https://github.com/Giskard-AI/giskard.") from e

    def _perform_scan(self, giskard_model, giskard_dataset):
        try:
            scan_results = setup_scan(giskard_model, giskard_dataset, self.evaluator_config)

            # log html scan result
            scan_results.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
            return scan_results
        except Exception as e:
            analytics.track(
                "mlflow_integration:scan:error",
                {
                    "mlflow_run_id": self.run_id,
                    "error": str(e),
                },
            )
            raise ValueError("An error occurred while scanning the model for vulnerabilities. "
                             "Please submit the traceback as a GitHub issue in the following "
                             "repository for further assistance: https://github.com/Giskard-AI/giskard.") from e

    def _generate_test_suite(self, scan_results):
        try:
            test_suite = scan_results.generate_test_suite("scan test suite")
            test_suite_results = test_suite.run()

            # log metrics resulting from scan
            test_suite_results.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
            return test_suite_results
        except Exception as e:
            analytics.track(
                "mlflow_integration:test_suite_generation:error",
                {
                    "mlflow_run_id": self.run_id,
                    "error": str(e),
                },
            )
            logger.warning(
                "An error occurred while generating the test suite. "
                "Visualising the results of the scan is still possible in the mlflow ui, but not as metrics."
                "Please submit the traceback as a GitHub issue in the following "
                "repository for further assistance: https://github.com/Giskard-AI/giskard."
            )

    def evaluate(
            self, *, model, model_type, dataset, run_id, evaluator_config, baseline_model=None, **kwargs
    ):
        self.client = MlflowClient()
        self.run_id = run_id
        self.evaluator_config = evaluator_config

        properties = dict()
        properties.update({"mlflow_run_id": str(self.run_id)} if self.run_id is not None else "none")

        # Wrapping dataset
        giskard_dataset = self._wrap_dataset(dataset)
        properties.update({"dataset_id": str(giskard_dataset.id)} if giskard_dataset is not None else "none")

        # Wrapping model
        giskard_model = self._wrap_model(model,
                                         model_type=model_type,
                                         feature_names=dataset.feature_names)
        properties.update(
            {"model_class": fullname(giskard_model),
             "model_inner_class": fullname(giskard_model.model)})
        analytics.track("mlflow_integration", properties)

        # Perform scan
        scan_results = self._perform_scan(giskard_model, giskard_dataset)

        # Generate test suite
        self._generate_test_suite(scan_results)
