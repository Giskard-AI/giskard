import great_expectations as ge
import pandas as pd
from ai_inspector import ModelInspector
from pandas import DataFrame

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.ml import run_predict
from ml_worker.testing.abstract_test_collection import AbstractTestCollection
from ml_worker.testing.utils import apply_perturbation_inplace, ge_result_to_test_result


class MetamorphicTests(AbstractTestCollection):
    @staticmethod
    def _perturb_and_predict(df, model: ModelInspector, perturbation_dict):
        results_df = pd.DataFrame()
        results_df["prediction"] = run_predict(df, model).raw_prediction
        modified_rows = apply_perturbation_inplace(df, perturbation_dict)
        results_df = results_df.iloc[modified_rows]
        if len(modified_rows):
            results_df["perturbed_prediction"] = run_predict(df.iloc[modified_rows], model).raw_prediction
        else:
            results_df["perturbed_prediction"] = results_df["prediction"]
        return results_df

    def _test_metamorphic_direction(self,
                                    is_increasing,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    threshold: int) -> SingleTestResult:
        perturbation_dict = {column_name: lambda x: x[column_name] * (1 + perturbation_percent)}
        results_df = self._perturb_and_predict(df, model, perturbation_dict)

        ge_df = ge.from_pandas(results_df)
        result = ge_df.expect_column_pair_values_A_to_be_greater_than_B(
            "perturbed_prediction" if is_increasing else "prediction",
            "prediction" if is_increasing else "perturbed_prediction",
            result_format="COMPLETE"
        )["result"]

        return self.save_results(
            ge_result_to_test_result(result, result.get('unexpected_percent') / 100 <= threshold))

    def test_metamorphic_invariance(self,
                                    df: DataFrame,
                                    model,
                                    perturbation_dict,
                                    threshold=1) -> SingleTestResult:
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
                                     failed is not None and (failed / 100 <= threshold)
                                     )
        )

    def test_metamorphic_increasing(self,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    threshold=1):
        return self._test_metamorphic_direction(is_increasing=True,
                                                df=df,
                                                column_name=column_name,
                                                model=model,
                                                perturbation_percent=perturbation_percent,
                                                threshold=threshold)

    def test_metamorphic_decreasing(self,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_percent: float,
                                    threshold=1):
        return self._test_metamorphic_direction(is_increasing=False,
                                                df=df,
                                                column_name=column_name,
                                                model=model,
                                                perturbation_percent=perturbation_percent,
                                                threshold=threshold)
