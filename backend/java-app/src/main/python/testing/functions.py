import inspect
from typing import Dict

import great_expectations as ge
import pandas as pd
from pandas.core.frame import DataFrame

import ml_worker_pb2
from ml_worker_pb2 import SingleTestResult
from testing.utils import ge_result_to_test_result, perturb_inplace


class TestFunctions:

    def __init__(self) -> None:
        self.tests_results: Dict[str, SingleTestResult] = {}

    def test_metamorphic_invariance(self, df: DataFrame, model, perturbation_dict):
        results_df = pd.DataFrame()
        results_df["prediction"] = model(df).argmax(1)

        modified_rows = perturb_inplace(df, perturbation_dict)

        results_df = results_df.loc[modified_rows]

        if len(modified_rows):
            results_df["perturbated_prediction"] = model(df.loc[modified_rows]).argmax(1)
        else:
            results_df["perturbated_prediction"] = results_df["prediction"]

        ge_df = ge.from_pandas(results_df)
        result = ge_df.expect_column_pair_values_to_be_equal(
            "prediction",
            "perturbated_prediction",
            result_format="COMPLETE"
        )["result"]
        self.save_results(ge_result_to_test_result(result))

    def save_results(self, result: ml_worker_pb2.SingleTestResult, test_name=None):
        if test_name is None:
            test_name = inspect.currentframe().f_back.f_code.co_name
        self.tests_results[test_name] = result
