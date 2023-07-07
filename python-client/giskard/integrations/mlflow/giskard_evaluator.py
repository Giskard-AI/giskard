import pandas as pd
from mlflow import MlflowClient
import re

from giskard.models.automodel import Model
from giskard.datasets.base import Dataset
from giskard.scanner import scan
from giskard.core.core import SupportedModelTypes
from giskard.core.model_validation import ValidationFlags, validate_model

from mlflow.models.evaluation import ModelEvaluator

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
        return model_type in ["classifier", "regressor"]

    def evaluate(
            self, *, model, model_type, dataset, run_id, evaluator_config, baseline_model=None, **kwargs
    ):
        self.client = MlflowClient()
        self.run_id = run_id
        self.evaluator_config = evaluator_config

        if not isinstance(dataset.features_data, pd.DataFrame):
            raise ValueError("Only pd.DataFrame are currently supported by the giskard evaluator.")
        else:
            try:
                data = dataset.features_data.copy()
                data[dataset.targets_name] = dataset.labels_data
                giskard_dataset = Dataset(df=data,
                                          target=dataset.targets_name,
                                          name=dataset.name)

                # log dataset
                giskard_dataset.to_mlflow(client=self.client, run_id=self.run_id)
            except Exception as e:
                raise ValueError("An error occurred while wrapping the dataset. "
                                 "Please submit the traceback as a GitHub issue in the following "
                                 "repository for further assistance: https://github.com/Giskard-AI/giskard.") from e

        try:
            giskard_model = PyFuncModel(model=model,
                                        model_type=gsk_model_types[model_type],
                                        feature_names=dataset.feature_names,
                                        **evaluator_config)
        except Exception as e:
            raise ValueError("An error occurred while wrapping the model. "
                             "Please submit the traceback as a GitHub issue in the following "
                             "repository for further assistance: https://github.com/Giskard-AI/giskard.") from e

        try:
            validation_flags = ValidationFlags()
            validation_flags.model_loading_and_saving = False
            scan_results = scan(model=giskard_model, dataset=giskard_dataset, validation_flags=validation_flags)

            # log html scan result
            scan_results.to_mlflow(client=self.client, run_id=self.run_id)
        except Exception as e:
            raise ValueError("An error occurred while scanning the model for vulnerabilities. "
                             "Please submit the traceback as a GitHub issue in the following "
                             "repository for further assistance: https://github.com/Giskard-AI/giskard.") from e

        try:
            test_suite = scan_results.generate_test_suite("scan test suite")
            test_suite_results = test_suite.run()

            # log metrics resulting from scan
            test_suite_results.to_mlflow(client=self.client, run_id=self.run_id)
        except Exception:  # noqa
            pass
