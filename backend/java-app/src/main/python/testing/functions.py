import inspect
from typing import Dict

import great_expectations as ge
import pandas as pd
from pandas.core.frame import DataFrame

import ml_worker_pb2
from ml_worker_pb2 import SingleTestResult
from testing.utils import ge_result_to_test_result, apply_perturbation_inplace

EMPTY_SINGLE_TEST_RESULT = ml_worker_pb2.SingleTestResult()


class GiskardTestFunctions:

    def __init__(self) -> None:
        self.tests_results: Dict[str, SingleTestResult] = {}

    def save_results(self, result: ml_worker_pb2.SingleTestResult, test_name=None):
        if test_name is None:
            test_name = inspect.currentframe().f_back.f_code.co_name
        self.tests_results[test_name] = result
        return result

    def test_metamorphic_invariance(self, df: DataFrame, model, perturbation_dict) -> ml_worker_pb2.SingleTestResult:
        results_df = self._perturb_and_predict(df, model, perturbation_dict)

        ge_df = ge.from_pandas(results_df)
        result = ge_df.expect_column_pair_values_to_be_equal(
            "prediction",
            "perturbated_prediction",
            result_format="COMPLETE"
        )["result"]

        return self.save_results(ge_result_to_test_result(result))

    @staticmethod
    def _perturb_and_predict(df, model, perturbation_dict, classification_label_index=None):
        extract_prediction = lambda x: \
            x.argmax(1) if classification_label_index is None else x[:, classification_label_index]
        results_df = pd.DataFrame()
        results_df["prediction"] = extract_prediction(model(df))
        modified_rows = apply_perturbation_inplace(df, perturbation_dict)
        results_df = results_df.loc[modified_rows]
        if len(modified_rows):
            results_df["perturbated_prediction"] = extract_prediction(model(df.loc[modified_rows]))
        else:
            results_df["perturbated_prediction"] = results_df["prediction"]
        return results_df

    def test_metamorphic_increasing(self,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    classification_label_index: int):
        return self._test_metamorphic_direction(is_increasing=True,
                                                df=df,
                                                column_name=column_name,
                                                model=model,
                                                perturbation_percent=perturbation_percent,
                                                classification_label_index=classification_label_index)

    def test_metamorphic_decreasing(self,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    classification_label_index: int):
        return self._test_metamorphic_direction(is_increasing=False,
                                                df=df,
                                                column_name=column_name,
                                                model=model,
                                                perturbation_percent=perturbation_percent,
                                                classification_label_index=classification_label_index)

    def _test_metamorphic_direction(self,
                                    is_increasing,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    classification_label_index: int) -> ml_worker_pb2.SingleTestResult:
        perturbation_dict = {column_name: lambda x: x[column_name] * (1 + perturbation_percent)}
        results_df = self._perturb_and_predict(df, model, perturbation_dict, classification_label_index)

        ge_df = ge.from_pandas(results_df)
        result = ge_df.expect_column_pair_values_A_to_be_greater_than_B(
            "perturbated_prediction" if is_increasing else "prediction",
            "prediction" if is_increasing else "perturbated_prediction",
            result_format="COMPLETE"
        )["result"]

        return self.save_results(ge_result_to_test_result(result))

    def test_heuristic(self,
                       df: DataFrame,
                       model,
                       classification_label: int,
                       min_proba: float = 0,
                       max_proba: float = 1,
                       mask=None) -> ml_worker_pb2.SingleTestResult:
        results_df = pd.DataFrame()
        if mask is not None:
            df = df.loc[mask]

        results_df["prediction_proba"] = model(df).max(1)
        results_df["prediction"] = model(df).argmax(1)
        matching_prediction_mask = (results_df["prediction"] == classification_label) & \
                                (results_df["prediction_proba"] <= max_proba) & \
                                (results_df["prediction_proba"] >= min_proba)

        unexpected = df[~matching_prediction_mask]
        return SingleTestResult(
            element_count=len(df),
            unexpected_count=len(unexpected),
            unexpected_percent=len(unexpected) / len(df)
        )
