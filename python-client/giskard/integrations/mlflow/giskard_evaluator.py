import pandas as pd
from mlflow import MlflowClient
import tempfile
import re

from giskard.models.automodel import Model
from giskard.datasets.base import Dataset
from giskard.scanner import scan
from giskard.core.core import SupportedModelTypes

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

        if isinstance(dataset.features_data, pd.DataFrame):
            data = dataset.features_data.copy()
            data[dataset.targets_name] = dataset.labels_data
            giskard_dataset = Dataset(df=data,
                                      target=dataset.targets_name,
                                      name=dataset.name)
        else:
            raise ValueError("Only pd.DataFrame are currently supported in Giskard.")

        cl = evaluator_config["classification_labels"] if "classification_labels" in self.evaluator_config else None
        giskard_model = Model(model=model,
                              model_type=gsk_model_types[model_type],
                              feature_names=dataset.feature_names,
                              classification_labels=cl)

        scan_results = scan(giskard_model, giskard_dataset)
        test_suite = scan_results.generate_test_suite("scan test suite")
        test_suite_results = test_suite.run()

        # log html scan result
        scan_results.to_mlflow(client=self.client, run_id=self.run_id)

        # log metrics resulting from scan
        test_suite_results.to_mlflow(client=self.client, run_id=self.run_id)
