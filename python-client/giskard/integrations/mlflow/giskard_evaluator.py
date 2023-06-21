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
    "regressor": SupportedModelTypes.REGRESSION
}


class GiskardModel(Model):
    def model_predict(self, df):
        return self.model.predict(df)


class GiskardEvaluator(ModelEvaluator):
    def can_evaluate(self, model_type, **kwargs):
        return model_type in ["classifier", "regressor"]

    def evaluate(
            self, *, model, model_type, dataset, run_id, evaluator_config, baseline_model=None, **kwargs
    ):
        self.model_type = model_type
        self.client = MlflowClient()
        self.dataset = dataset
        self.run_id = run_id
        self.X = dataset.features_data
        self.y = dataset.labels_data

        if isinstance(dataset.features_data, pd.DataFrame):
            data = dataset.features_data.copy()
            data[dataset.targets_name] = dataset.labels_data
            giskard_dataset = Dataset(df=data,
                                      target=dataset.targets_name,
                                      name=dataset.name)
        else:
            raise ValueError("Only pd.DataFrame are currently supported in Giskard.")

        cl = evaluator_config["classification_labels"] if "classification_labels" in evaluator_config else None
        giskard_model = GiskardModel(model=model,
                                     model_type=gsk_model_types[model_type],
                                     feature_names=dataset.feature_names,
                                     classification_labels=cl)

        results = scan(giskard_model, giskard_dataset)

        # log html scan result
        with tempfile.NamedTemporaryFile(prefix="giskard-scan-results-", suffix=".html") as f:
            self.client.log_text(self.run_id, results.to_html(), f.name.split("/")[-1])

        # log metrics resulting from scan
        test_suite = results.generate_test_suite("scan test suite")
        test_suite_results = test_suite.run()
        for test_result in test_suite_results[1]:
            test_name = test_result[0]
            test_name = re.sub(r'\W+', '', test_name)
            self.client.log_metric(self.run_id, test_name, test_result[1].metric)
