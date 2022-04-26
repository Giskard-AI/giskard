import pandas as pd
from ai_inspector import ModelInspector
from pandas import DataFrame

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.ml import run_predict
from ml_worker.testing.abstract_test_collection import AbstractTestCollection


class HeuristicTests(AbstractTestCollection):
    def test_heuristic(self,
                       df: DataFrame,
                       model: ModelInspector,
                       classification_label: int,
                       min_proba: float = 0,
                       max_proba: float = 1,
                       threshold=1) -> SingleTestResult:
        results_df = pd.DataFrame()

        prediction_results = run_predict(df, model)
        results_df["prediction_proba"] = prediction_results.probabilities
        results_df["prediction"] = prediction_results.raw_prediction
        matching_prediction_mask = (results_df["prediction"] == classification_label) & \
                                   (results_df["prediction_proba"] <= max_proba) & \
                                   (results_df["prediction_proba"] >= min_proba)

        unexpected = df[~matching_prediction_mask]
        failed_ratio = len(unexpected) / len(df)
        return self.save_results(SingleTestResult(
            element_count=len(df),
            unexpected_count=len(unexpected),
            unexpected_percent=failed_ratio * 100,
            passed=failed_ratio <= threshold
        ))
