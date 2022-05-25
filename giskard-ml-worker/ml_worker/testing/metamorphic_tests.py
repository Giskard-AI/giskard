import pandas as pd
from ai_inspector import ModelInspector
from pandas import DataFrame
from ml_worker.testing.utils import save_df, compress

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.ml import run_predict
from ml_worker.testing.abstract_test_collection import AbstractTestCollection
from ml_worker.testing.utils import apply_perturbation_inplace, ge_result_to_test_result


class MetamorphicTests(AbstractTestCollection):
    @staticmethod
    def _predict_numeric_result(df, model: ModelInspector, output_proba=True):
        if model.prediction_task == 'regression' or not output_proba:
            return run_predict(df, model).raw_prediction
        elif model.prediction_task == 'classification':
            return run_predict(df, model).probabilities

    @staticmethod
    def _prediction_ratio(prediction, perturbed_prediction):
        return abs(perturbed_prediction - prediction) / prediction

    @staticmethod
    def _perturb_and_predict(df, model: ModelInspector, perturbation_dict, output_proba=True):
        results_df = pd.DataFrame()
        results_df["prediction"] = MetamorphicTests._predict_numeric_result(df, model, output_proba)
        modified_rows = apply_perturbation_inplace(df, perturbation_dict)
        results_df = results_df.iloc[modified_rows]
        if len(modified_rows):
            results_df["perturbed_prediction"] = MetamorphicTests._predict_numeric_result(df.iloc[modified_rows], model,
                                                                                          output_proba)
        else:
            results_df["perturbed_prediction"] = results_df["prediction"]
        return results_df, len(modified_rows)

    def _compare_predict(self, results_df, prediction_task, output_sensitivity):
        if prediction_task == 'classification':
            passed_idx = results_df.loc[
                results_df['prediction'] == results_df['perturbed_prediction']].index.values

        if prediction_task == 'regression':
            results_df['predict_difference_ratio'] = results_df.apply(
                lambda x: self._prediction_ratio(x["prediction"], x["perturbed_prediction"]), axis=1)

            passed_idx = results_df.loc[results_df['predict_difference_ratio'] < output_sensitivity].index.values

        failed_idx = results_df.loc[~results_df.index.isin(passed_idx)].index.values
        return passed_idx, failed_idx

    def _test_metamorphic_direction(self,
                                    is_increasing,
                                    df: DataFrame,
                                    column_name: str,
                                    model,
                                    perturbation_dict,
                                    threshold: float) -> SingleTestResult:
        import great_expectations as ge

        # perturbation_dict = {column_name: lambda x: x[column_name] * (1 + perturbation_percent)}
        results_df = self._perturb_and_predict(df, model, perturbation_dict)
        ge_df = ge.from_pandas(results_df)
        result = ge_df.expect_column_pair_values_A_to_be_greater_than_B(
            "perturbed_prediction" if is_increasing else "prediction",
            "prediction" if is_increasing else "perturbed_prediction",
            result_format="COMPLETE"
        )["result"]

        return self.save_results(
            ge_result_to_test_result(result, (result.get('unexpected_percent') or 0) / 100 <= threshold))

    def test_metamorphic_invariance(self,
                                    df: DataFrame,
                                    model,
                                    perturbation_dict,
                                    threshold=1,
                                    output_sensitivity: int = 0.1) -> SingleTestResult:
        """
        Summary: Tests if the model prediction is invariant when the feature values are perturbed

        Description: -
        For classification: Test if the predicted classification label remains the same after
        feature values perturbation.
        For regression: Check whether the predicted output remains the same at the output_sensibility
        level after feature values perturbation.
        
        The test is passed when the ratio of invariant rows is higher than the threshold

        Example : The test is passed when, after switching gender from male to female,
        more than 50%(threshold 0.5) of males have unchanged outputs

        Args:
            df(pandas.core.frame.DataFrame):
                Dataset used to compute the test
            model(ModelInspector):
                Model used to compute the test
            perturbation_dict(dict):
                dictionary of the perturbations. It provides the perturbed features as key and a perturbation lambda function as value
            threshold(float):
                threshold of the ratio of invariant rows
            output_sensitivity(float):
                the threshold for ratio between the difference between perturbed prediction and actual prediction over
                the actual prediction for a regression model. We consider there is a prediction difference for
                regression if the ratio is above the output_sensitivity of 0.1

        Returns:
            total_nb_rows:
                total number of rows of dataframe
            number_of_perturbed_rows:
                number of perturbed rows
            metric:
                the ratio of invariant rows over the perturbed rows
            passed:
                TRUE if passed_ratio > threshold
            output_df:
                dataframe containing the non invariant raws

        """
        results_df, modified_rows_count = self._perturb_and_predict(df, model, perturbation_dict, output_proba=False)
        passed_idx, failed_idx = self._compare_predict(results_df, model.prediction_task, output_sensitivity)
        failed_df = df.loc[failed_idx]
        passed_ratio = len(passed_idx) / len(df)

        output_df_sample = compress(save_df(failed_df))

        return self.save_results(SingleTestResult(
            total_nb_rows=len(df),
            number_of_perturbed_rows=modified_rows_count,
            metric=passed_ratio,
            passed=passed_ratio > threshold,
            output_df=output_df_sample
        ))

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
