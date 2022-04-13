import inspect
import logging
from typing import List

import great_expectations as ge
import pandas as pd
from pandas.core.frame import DataFrame

from generated.ml_worker_pb2 import SingleTestResult, NamedSingleTestResult
from ml_worker.testing.utils import ge_result_to_test_result, apply_perturbation_inplace

EMPTY_SINGLE_TEST_RESULT = SingleTestResult()


class GiskardTestFunctions:
    tests_results: List[NamedSingleTestResult]

    def __init__(self) -> None:
        self.tests_results = []

    def save_results(self, result: SingleTestResult, test_name=None):
        if test_name is None:
            test_name = self._find_caller_test_name()

        self.tests_results.append(NamedSingleTestResult(name=test_name, result=result))
        return result

    @staticmethod
    def _find_caller_test_name():
        curr_frame = inspect.currentframe()
        try:
            while curr_frame.f_back.f_code.co_name != '<module>':
                curr_frame = curr_frame.f_back
        except Exception as e:
            logging.error(f"Failed to extract test method name", e)
        return curr_frame.f_code.co_name

    @staticmethod
    def _perturb_and_predict(df, model, perturbation_dict, classification_label_index=None):
        def extract_prediction(x):
            return x.argmax(1) if classification_label_index is None else x[:, classification_label_index]

        results_df = pd.DataFrame()
        results_df["prediction"] = extract_prediction(model(df))
        modified_rows = apply_perturbation_inplace(df, perturbation_dict)
        results_df = results_df.loc[modified_rows]
        if len(modified_rows):
            results_df["perturbed_prediction"] = extract_prediction(model(df.loc[modified_rows]))
        else:
            results_df["perturbed_prediction"] = results_df["prediction"]
        return results_df

    def _test_metamorphic_direction(self,
                                    is_increasing,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    classification_label_index: int,
                                    failed_threshold: int) -> SingleTestResult:
        perturbation_dict = {column_name: lambda x: x[column_name] * (1 + perturbation_percent)}
        results_df = self._perturb_and_predict(df, model, perturbation_dict, classification_label_index)

        ge_df = ge.from_pandas(results_df)
        result = ge_df.expect_column_pair_values_A_to_be_greater_than_B(
            "perturbed_prediction" if is_increasing else "prediction",
            "prediction" if is_increasing else "perturbed_prediction",
            result_format="COMPLETE"
        )["result"]

        return self.save_results(
            ge_result_to_test_result(result, result.get('unexpected_percent') / 100 <= failed_threshold))

    def test_metamorphic_invariance(self,
                                    df: DataFrame,
                                    model,
                                    perturbation_dict,
                                    failed_threshold=1) -> SingleTestResult:
        results_df = self._perturb_and_predict(df, model, perturbation_dict)

        ge_df = ge.from_pandas(results_df)
        result = ge_df.expect_column_pair_values_to_be_equal(
            "prediction",
            "perturbed_prediction",
            result_format="COMPLETE"
        )["result"]

        failed = result.get('unexpected_percent')
        return self.save_results(
            ge_result_to_test_result(result,
                                     failed is not None and (failed / 100 <= failed_threshold)
                                     )
        )

    def test_metamorphic_increasing(self,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    classification_label_index: int,
                                    failed_threshold=1):
        return self._test_metamorphic_direction(is_increasing=True,
                                                df=df,
                                                column_name=column_name,
                                                model=model,
                                                perturbation_percent=perturbation_percent,
                                                classification_label_index=classification_label_index,
                                                failed_threshold=failed_threshold)

    def test_metamorphic_decreasing(self,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    classification_label_index: int,
                                    failed_threshold=1):
        return self._test_metamorphic_direction(is_increasing=False,
                                                df=df,
                                                column_name=column_name,
                                                model=model,
                                                perturbation_percent=perturbation_percent,
                                                classification_label_index=classification_label_index,
                                                failed_threshold=failed_threshold)

    def test_heuristic(self,
                       df: DataFrame,
                       model,
                       classification_label: int,
                       min_proba: float = 0,
                       max_proba: float = 1,
                       mask=None,
                       failed_threshold=1) -> SingleTestResult:
        results_df = pd.DataFrame()
        if mask is not None:
            df = df.loc[mask]

        results_df["prediction_proba"] = model(df).max(1)
        results_df["prediction"] = model(df).argmax(1)
        matching_prediction_mask = (results_df["prediction"] == classification_label) & \
                                   (results_df["prediction_proba"] <= max_proba) & \
                                   (results_df["prediction_proba"] >= min_proba)

        unexpected = df[~matching_prediction_mask]
        failed_ratio = len(unexpected) / len(df)
        return self.save_results(SingleTestResult(
            element_count=len(df),
            unexpected_count=len(unexpected),
            unexpected_percent=failed_ratio * 100,
            passed=failed_ratio <= failed_threshold
        ))
