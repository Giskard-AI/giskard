import logging

import pandas as pd
from mlflow import MlflowClient
from mlflow.models.evaluation import EvaluationResult, ModelEvaluator
from mlflow.tracking.artifact_utils import get_artifact_uri

from ...scanner.report import ScanReport
from ...utils import fullname
from ...utils.analytics_collector import analytics
from .evaluation_artifacts import (
    GiskardDatasetEvaluationArtifact,
    GiskardScanResultEvaluationArtifact,
    GiskardScanSummaryEvaluationArtifact,
)
from .giskard_evaluator_utils import setup_dataset, setup_model, setup_scan

logger = logging.getLogger(__name__)


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
                local_path = giskard_dataset.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
                return giskard_dataset, local_path
            except Exception as e:
                analytics.track(
                    "mlflow_integration:wrapping_dataset:error",
                    {
                        "mlflow_run_id": self.run_id,
                        "error": str(e),
                    },
                )
                raise ValueError(
                    "An error occurred while wrapping the dataset. "
                    "Please submit the traceback as a GitHub issue in the following "
                    "repository for further assistance: https://github.com/Giskard-AI/giskard."
                ) from e

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
            raise ValueError(
                "An error occurred while wrapping the model. "
                "Please submit the traceback as a GitHub issue in the following "
                "repository for further assistance: https://github.com/Giskard-AI/giskard."
            ) from e

    def _perform_scan(self, giskard_model, giskard_dataset):
        try:
            scan_results = setup_scan(giskard_model, giskard_dataset, self.evaluator_config)

            # log html scan result
            scan_artifact_names = scan_results.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
            return scan_results, scan_artifact_names
        except Exception as e:
            analytics.track(
                "mlflow_integration:scan:error",
                {
                    "mlflow_run_id": self.run_id,
                    "error": str(e),
                },
            )
            raise ValueError(
                "An error occurred while scanning the model for vulnerabilities. "
                "Please submit the traceback as a GitHub issue in the following "
                "repository for further assistance: https://github.com/Giskard-AI/giskard."
            ) from e

    def _generate_test_suite(self, scan_results):
        try:
            test_suite = scan_results.generate_test_suite("scan test suite")
            test_suite_results = test_suite.run()

            # log metrics resulting from scan
            metrics = test_suite_results.to_mlflow(mlflow_client=self.client, mlflow_run_id=self.run_id)
            return test_suite_results, metrics
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
    ) -> EvaluationResult:
        self.client = MlflowClient()
        self.run_id = run_id
        self.evaluator_config = evaluator_config

        artifacts = dict()
        properties = dict()
        properties.update({"mlflow_run_id": str(self.run_id)} if self.run_id is not None else "none")

        # Wrapping dataset
        giskard_dataset, dataset_artifact_name = self._wrap_dataset(dataset)
        artifacts["giskard_dataset"] = GiskardDatasetEvaluationArtifact(
            uri=get_artifact_uri(self.run_id, dataset_artifact_name), content=giskard_dataset.df
        )
        properties.update({"dataset_id": str(giskard_dataset.id)} if giskard_dataset is not None else "none")

        # Wrapping model
        giskard_model = self._wrap_model(model, model_type=model_type, feature_names=dataset.feature_names)
        properties.update({"model_class": fullname(giskard_model), "model_inner_class": fullname(giskard_model.model)})
        analytics.track("mlflow_integration", properties)

        # Perform scan
        scan_results, scan_artifact_names = self._perform_scan(giskard_model, giskard_dataset)
        scan_results_artifact_name, scan_summary_artifact_name = scan_artifact_names[0], scan_artifact_names[1]
        scan_summary = ScanReport.get_scan_summary_for_mlflow(scan_results)
        artifacts["giskard_scan_results"] = GiskardScanResultEvaluationArtifact(
            uri=get_artifact_uri(self.run_id, scan_results_artifact_name), content=scan_results
        )
        if scan_summary_artifact_name:
            artifacts["giskard_scan_summary"] = GiskardScanSummaryEvaluationArtifact(
                uri=get_artifact_uri(self.run_id, scan_summary_artifact_name), content=scan_summary
            )

        # Generate test suite
        _, metrics = self._generate_test_suite(scan_results)

        print(
            "The evaluation with giskard ran successfully! You can now visualise the results by running 'mlflow ui' "
            "in the terminal."
        )

        return EvaluationResult(metrics=metrics, artifacts=artifacts)
