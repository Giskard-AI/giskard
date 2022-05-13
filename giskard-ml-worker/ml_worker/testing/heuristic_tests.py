import pandas as pd
from ai_inspector import ModelInspector
from pandas import DataFrame

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.ml import run_predict
from ml_worker.testing.abstract_test_collection import AbstractTestCollection


class HeuristicTests(AbstractTestCollection):
    def test_heuristic(self,
                       df: DataFrame, #changer en slice
                       model: ModelInspector,
                       classification_label: str,
                       min_proba: float = 0,
                       max_proba: float = 1,
                       threshold=1) -> SingleTestResult:
        results_df = pd.DataFrame()

        prediction_results = run_predict(df, model)
        results_df["prediction_proba"] = prediction_results.probabilities
        results_df["prediction"] = prediction_results.raw_prediction

        assert classification_label in model.classification_labels, \
            f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        matching_prediction_mask = \
            (results_df["prediction"] == model.classification_labels.index(classification_label)) & \
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

    def test_output_in_range(self,
                             df_slice: DataFrame,
                             model: ModelInspector,
                             classification_label=None,
                             min_proba: float = 0.3,
                             max_proba: float = 0.7,
                             threshold=0.5) -> SingleTestResult:
        results_df = pd.DataFrame()

        prediction_results = run_predict(df_slice, model)

        if model.prediction_task == "regression":
            results_df["output"] = prediction_results.raw_prediction

        elif model.prediction_task == "classification":
            results_df["output"] == prediction_results.all_predictions[classification_label]
            assert classification_label in model.classification_labels, \
                f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        else:
            raise ValueError(
                f"Prediction task is not supported: {model.prediction_task}"
            )

        matching_prediction_mask = \
            (results_df["output"] <= max_proba) & \
            (results_df["output"] >= min_proba)

        expected = df_slice[matching_prediction_mask]
        passed_ratio = len(expected) / len(df_slice)
        return self.save_results(SingleTestResult(
            slice_nb_rows=len(df_slice),
            metric=passed_ratio,
            passed=passed_ratio >= threshold
        ))



