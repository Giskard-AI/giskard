import pandas as pd
from mlflow import MlflowClient
import re
import logging

from ...models.automodel import Model
from ...datasets.base import Dataset
from ...scanner import scan
from ...core.core import SupportedModelTypes
from ...core.model_validation import ValidationFlags
from ...utils.analytics_collector import analytics

from mlflow.models.evaluation import ModelEvaluator

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


class GiskardEvaluator(ModelEvaluator):
    def can_evaluate(self, model_type, **kwargs):
        return model_type in ["classifier", "regressor", "text"]

    def evaluate(
            self, *, model, model_type, dataset, run_id, evaluator_config, baseline_model=None, **kwargs
    ):
        self.client = MlflowClient()
        self.run_id = run_id
        self.evaluator_config = evaluator_config

        properties = dict()
        properties.update({"mlflow_run_id": str(self.run_id)} if self.run_id is not None else "none")

        if not isinstance(dataset.features_data, pd.DataFrame):
            raise ValueError("Only pd.DataFrame are currently supported by the giskard evaluator.")
        else:
            try:
                data = dataset.features_data.copy()
                data[dataset.targets_name] = dataset.labels_data
                giskard_dataset = Dataset(df=data,
                                          target=dataset.targets_name,
                                          name=dataset.name)
                properties.update({"dataset_id": str(giskard_dataset.id)} if giskard_dataset is not None else "none")

                # log dataset
                giskard_dataset.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
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

        try:
            giskard_model = PyFuncModel(model=model,
                                        model_type=gsk_model_types[model_type],
                                        feature_names=dataset.feature_names,
                                        **evaluator_config)
            properties.update({"model_id": str(model.id)})
            analytics.track("mlflow_integration", properties)
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

        try:
            validation_flags = ValidationFlags()
            validation_flags.model_loading_and_saving = False
            scan_results = scan(model=giskard_model, dataset=giskard_dataset, validation_flags=validation_flags)

            # log html scan result
            scan_results.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
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

        try:
            test_suite = scan_results.generate_test_suite("scan test suite")
            test_suite_results = test_suite.run()

            # log metrics resulting from scan
            test_suite_results.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
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
