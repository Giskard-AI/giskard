import pandas as pd

from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.core.model import GiskardModel
from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult, TestMessage, TestMessageType
from giskard.ml_worker.testing.abstract_test_collection import AbstractTestCollection
from giskard.ml_worker.testing.utils import apply_perturbation_inplace
from giskard.ml_worker.utils.logging import timer
from giskard.ml_worker.testing.stat_utils import equivalence_t_test, paired_t_test
from giskard.ml_worker.testing.stat_utils import equivalence_wilcoxon, paired_wilcoxon
from giskard.ml_worker.testing.utils import Direction


class MetamorphicTests(AbstractTestCollection):
    @staticmethod
    def _predict_numeric_result(
        ds: GiskardDataset, model: GiskardModel, output_proba=True, classification_label=None
    ):
        if model.model_type == "regression" or not output_proba:
            return model.run_predict(ds).raw_prediction
        elif model.model_type == "classification" and classification_label is not None:
            return model.run_predict(ds).all_predictions[classification_label].values
        elif model.model_type == "classification":
            return model.run_predict(ds).probabilities

    @staticmethod
    def _prediction_ratio(prediction, perturbed_prediction):
        return (
            abs(perturbed_prediction - prediction) / prediction
            if prediction != 0
            else abs(perturbed_prediction)
        )

    @staticmethod
    def _perturb_and_predict(
        ds: GiskardDataset,
        model: GiskardModel,
        perturbation_dict,
        output_proba=True,
        classification_label=None,
    ):
        results_df = pd.DataFrame()
        results_df["prediction"] = MetamorphicTests._predict_numeric_result(
            ds, model, output_proba, classification_label
        )
        modified_rows = apply_perturbation_inplace(ds.df, perturbation_dict)
        if len(modified_rows):
            ds.df = ds.df.iloc[modified_rows]
            results_df = results_df.iloc[modified_rows]
            results_df["perturbed_prediction"] = MetamorphicTests._predict_numeric_result(
                ds, model, output_proba, classification_label
            )
        else:
            results_df["perturbed_prediction"] = results_df["prediction"]
        return results_df, len(modified_rows)

    @timer("Compare and predict the data")
    def _compare_prediction(self, results_df, prediction_task, direction, output_sensitivity=None):
        if direction == Direction.Invariant:
            if prediction_task == "classification":
                passed_idx = results_df.loc[
                    results_df["prediction"] == results_df["perturbed_prediction"]
                ].index.values

            elif prediction_task == "regression":
                results_df["predict_difference_ratio"] = results_df.apply(
                    lambda x: self._prediction_ratio(x["prediction"], x["perturbed_prediction"]),
                    axis=1,
                )
                passed_idx = results_df.loc[
                    results_df["predict_difference_ratio"] < output_sensitivity
                ].index.values

        elif direction == Direction.Increasing:
            passed_idx = results_df.loc[
                results_df["prediction"] < results_df["perturbed_prediction"]
            ].index.values

        elif direction == Direction.Decreasing:
            passed_idx = results_df.loc[
                results_df["prediction"] > results_df["perturbed_prediction"]
            ].index.values

        failed_idx = results_df.loc[~results_df.index.isin(passed_idx)].index.values
        return passed_idx, failed_idx

    def _compare_probabilities_t_test(self, result_df, direction, window_size=0.1, critical_quantile=0.05):

          if direction == Direction.Invariant:
              p_value = equivalence_t_test(result_df['prediction'], result_df['perturbed_prediction'], window_size=window_size, critical_quantile=critical_quantile)[1]

          elif direction == Direction.Increasing:
              p_value = paired_t_test(result_df['prediction'], result_df['perturbed_prediction'], alternative='less', critical_quantile=critical_quantile)[1]

          elif direction == Direction.Decreasing:
              p_value = paired_t_test(result_df['prediction'], result_df['perturbed_prediction'], alternative='greater', critical_quantile=critical_quantile)[1]

          return p_value

    def _compare_probabilities_wilcoxon(self, result_df, direction, window_size=0.2, critical_quantile=0.05):

          if direction == Direction.Invariant:
              p_value = equivalence_wilcoxon(result_df['prediction'], result_df['perturbed_prediction'], window_size=window_size, critical_quantile=critical_quantile)[1]

          elif direction == Direction.Increasing:
              p_value = paired_wilcoxon(result_df['prediction'], result_df['perturbed_prediction'], alternative='less', critical_quantile=critical_quantile)[1]

          elif direction == Direction.Decreasing:
              p_value = paired_wilcoxon(result_df['prediction'], result_df['perturbed_prediction'], alternative='greater', critical_quantile=critical_quantile)[1]

          return p_value

    def _test_metamorphic(
        self,
        direction: Direction,
        actual_slice: GiskardDataset,
        model,
        perturbation_dict,
        threshold: float,
        classification_label=None,
        output_sensitivity=None,
        output_proba=True,
    ) -> SingleTestResult:
        actual_slice.df.reset_index(drop=True, inplace=True)

        results_df, modified_rows_count = self._perturb_and_predict(
            actual_slice,
            model,
            perturbation_dict,
            classification_label=classification_label,
            output_proba=output_proba,
        )

        passed_idx, failed_idx = self._compare_prediction(
            results_df, model.model_type, direction, output_sensitivity
        )
        passed_ratio = len(passed_idx) / modified_rows_count if modified_rows_count != 0 else 1

        messages = [
            TestMessage(
                type=TestMessageType.INFO, text=f"{modified_rows_count} rows were perturbed"
            )
        ]

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                metric=passed_ratio,
                passed=passed_ratio > threshold,
                messages=messages,
            )
        )

    def test_metamorphic_invariance(self,
                                    df: GiskardDataset,
                                    model,
                                    perturbation_dict,
                                    threshold=0.5,
                                    output_sensitivity=None
                                    ) -> SingleTestResult:
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
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            window_size(float):
              Threshold of the ratio of invariant rows
            output_sensitivity(float):
                Optional. The threshold for ratio between the difference between perturbed prediction and actual prediction over
                the actual prediction for a regression model. We consider there is a prediction difference for
                regression if the ratio is above the output_sensitivity of 0.1

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of unchanged rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """

        return self._test_metamorphic(
            direction=Direction.Invariant,
            actual_slice=df,
            model=model,
            perturbation_dict=perturbation_dict,
            threshold=threshold,
            output_sensitivity=output_sensitivity,
            output_proba=False,
        )

    def test_metamorphic_increasing(self,
                                    df: GiskardDataset,
                                    model,
                                    perturbation_dict,
                                    threshold=0.5,
                                    classification_label=None
    ):
        """
        Summary: Tests if the model probability increases when the feature values are perturbed

        Description: -
        - For classification: Test if the model probability of a given classification_label is
        increasing after feature values perturbation.

        - For regression: Test if the model prediction is increasing after feature values perturbation.

        The test is passed when the percentage of rows that are increasing is higher than the threshold

        Example : For a credit scoring model, the test is passed when a decrease of wage by 10%,
         default probability is increasing for more than 50% of people in the dataset

        Args:
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            window_size(float):
              Threshold of the ratio of increasing rows
            classification_label(str):
              Optional.One specific label value from the target column

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of increasing rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """
        assert (
            model.model_type != "classification"
            or str(classification_label) in model.classification_labels
        ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic(
            direction=Direction.Increasing,
            actual_slice=df,
            model=model,
            perturbation_dict=perturbation_dict,
            classification_label=classification_label,
            threshold=threshold,
        )

    def test_metamorphic_decreasing(
        self, df: GiskardDataset, model, perturbation_dict, threshold=0.5, classification_label=None
    ):
        """
        Summary: Tests if the model probability decreases when the feature values are perturbed

        Description: -
        - For classification: Test if the model probability of a given classification_label is
        decreasing after feature values perturbation.

        - For regression: Test if the model prediction is decreasing after feature values perturbation.

        The test is passed when the percentage of rows that are decreasing is higher than the threshold

        Example : For a credit scoring model, the test is passed when an increase of wage by 10%,
         default probability is decreasing for more than 50% of people in the dataset

        Args:
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            threshold(float):
              Threshold of the ratio of decreasing rows
            classification_label(str):
              Optional. One specific label value from the target column

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of decreasing rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """

        assert (
            model.model_type != "classification"
            or classification_label in model.classification_labels
        ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic(
            direction=Direction.Decreasing,
            actual_slice=df,
            model=model,
            perturbation_dict=perturbation_dict,
            classification_label=classification_label,
            threshold=threshold,
        )


    def _test_metamorphic_t_test(self,
                                direction: Direction,
                                actual_slice: GiskardDataset,
                                model,
                                perturbation_dict,
                                window_size: float,
                                critical_quantile: float,
                                classification_label=None,
                                output_proba=True
                                ) -> SingleTestResult:

         actual_slice.df.reset_index(drop=True, inplace=True)

         result_df, modified_rows_count = self._perturb_and_predict(actual_slice,
                                                                    model,
                                                                    perturbation_dict,
                                                                    output_proba=output_proba,
                                                                    classification_label=classification_label)

         p_value = self._compare_probabilities_t_test(result_df, direction, window_size, critical_quantile)

         messages = [TestMessage(
             type=TestMessageType.INFO,
             text=f"{modified_rows_count} rows were perturbed"
         )]

         return self.save_results(SingleTestResult(
             actual_slices_size=[len(actual_slice)],
             metric=p_value,
             passed=p_value < critical_quantile,
             messages=messages))

    def test_metamorphic_decreasing_t_test(self,
                                        df: GiskardDataset,
                                        model,
                                        perturbation_dict,
                                        critical_quantile=0.05,
                                        classification_label=None
                                        ):
        """
        Summary: Tests if the model probability decreases when the feature values are perturbed

        Description: Calculate the t-test on TWO RELATED samples. Sample (A) is the original probability predictions
        while sample (B) is the probabilities after perturbation of one or more of the features.
        This test computes the decreasing test to study if mean(B) < mean(A)
        The test is passed when the p-value of the t-test between (A) and (B) is below the critical quantile

        Example: For a credit scoring model, the test is passed when a decrease of wage by 10%,
                 causes a statistically significant probability decrease.

        Args:
            df(GiskardDataset):
                Dataset used to compute the test
            model(GiskardModel):
                Model used to compute the test
            perturbation_dict(dict):
                Dictionary of the perturbations. It provides the perturbed features as key
                and a perturbation lambda function as value
            critical_quantile(float):
                Critical quantile above which the null hypothesis cannot be rejected

        Returns:
            actual_slices_size:
                Length of actual_slice tested
            message:
                Test result message
            metric:
                The t-test in terms of p-value between unchanged rows over the perturbed rows
            passed:
                TRUE if the p-value of the t-test between (A) and (B) is below the critical value
        """

        assert (
            model.model_type != "classification"
            or str(classification_label) in model.classification_labels
        ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic_t_test(direction=Direction.Decreasing,
                                          actual_slice=df,
                                          model=model,
                                          perturbation_dict=perturbation_dict,
                                          classification_label=classification_label,
                                          window_size=float("nan"),
                                          critical_quantile=critical_quantile)

    def test_metamorphic_increasing_t_test(self,
                                        df: GiskardDataset,
                                        model,
                                        perturbation_dict,
                                        critical_quantile=0.05,
                                        classification_label=None
                                        ):
        """
        Summary: Tests if the model probability increases when the feature values are perturbed

        Description: Calculate the t-test on TWO RELATED samples. Sample (A) is the original probability predictions
        while sample (B) is the probabilities after perturbation of one or more of the features.
        This test computes the increasing test to study if mean(A) < mean(B)
        The test is passed when the p-value of the t-test between (A) and (B) is below the critical quantile

        Example: For a credit scoring model, the test is passed when a decrease of wage by 10%,
                 causes a statistically significant probability increase.

        Args:
            df(GiskardDataset):
                Dataset used to compute the test
            model(GiskardModel):
                Model used to compute the test
            perturbation_dict(dict):
                Dictionary of the perturbations. It provides the perturbed features as key
                and a perturbation lambda function as value
            critical_quantile(float):
                Critical quantile above which the null hypothesis cannot be rejected

        Returns:
            actual_slices_size:
                Length of actual_slice tested
            message:
                Test result message
            metric:
                The t-test in terms of p-value between unchanged rows over the perturbed rows
            passed:
                TRUE if the p-value of the t-test between (A) and (B) is below the critical value
        """

        assert (
            model.model_type != "classification"
            or str(classification_label) in model.classification_labels
        ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'


        return self._test_metamorphic_t_test(direction=Direction.Increasing,
                                          actual_slice=df,
                                          model=model,
                                          perturbation_dict=perturbation_dict,
                                          classification_label=classification_label,
                                          window_size=float("nan"),
                                          critical_quantile=critical_quantile)

    def test_metamorphic_invariance_t_test(self,
                                        df: GiskardDataset,
                                        model,
                                        perturbation_dict,
                                        window_size: float,
                                        critical_quantile: float,
                                        ) -> SingleTestResult:
        """
        Summary: Tests if the model predictions are statistically invariant when the feature values are perturbed.

        Description: Calculate the t-test on TWO RELATED samples. Sample (A) is the original probability predictions
        while sample (B) is the probabilities after perturbation of one or more of the features.
        This test computes the equivalence test to show that mean(B) - window_size/2 < mean(A) < mean(B) + window_size/2
        The test is passed when the following tests pass:
          - the p-value of the t-test between (A) and (B)+window_size/2 is below the critical quantile
          - the p-value of the t-test between (B)-window_size/2 and (A) is below the critical quantile

        Example: The test is passed when, after switching gender from male to female,
        the probability distributions remains statistically invariant. In other words, the test is passed if the mean of the
        perturbed sample is statistically within a window determined by the user.

        Args:
              df(GiskardDataset):
                  Dataset used to compute the test
              model(GiskardModel):
                  Model used to compute the test
              perturbation_dict(dict):
                  Dictionary of the perturbations. It provides the perturbed features as key
                  and a perturbation lambda function as value
              window_size(float):
                  Probability window in which the mean of the perturbed sample can be in
              critical_quantile(float):
                  Critical quantile above which the null hypothesis cannot be rejected

        Returns:
              actual_slices_size:
                  Length of actual_slice tested
              message:
                  Test result message
              metric:
                  The t-test in terms of p-value between unchanged rows over the perturbed rows
              passed:
                  TRUE if the p-value of the t-test between (A) and (B)+window_size/2 < critical_quantile && the p-value of the t-test between (B)-window_size/2 and (A) < critical_quantile
        """

        return self._test_metamorphic_t_test(direction=Direction.Invariant,
                                      actual_slice=df,
                                      model=model,
                                      perturbation_dict=perturbation_dict,
                                      window_size=window_size,
                                      critical_quantile=critical_quantile)


    def _test_metamorphic_wilcoxon(self,
                                direction: Direction,
                                actual_slice: GiskardDataset,
                                model,
                                perturbation_dict,
                                window_size: float,
                                critical_quantile: float,
                                classification_label=None,
                                output_proba=True
                                ) -> SingleTestResult:

         actual_slice.df.reset_index(drop=True, inplace=True)

         result_df, modified_rows_count = self._perturb_and_predict(actual_slice,
                                                                    model,
                                                                    perturbation_dict,
                                                                    output_proba=output_proba,
                                                                    classification_label=classification_label)

         p_value = self._compare_probabilities_wilcoxon(result_df, direction, window_size, critical_quantile)

         messages = [TestMessage(
             type=TestMessageType.INFO,
             text=f"{modified_rows_count} rows were perturbed"
         )]

         return self.save_results(SingleTestResult(
             actual_slices_size=[len(actual_slice)],
             metric=p_value,
             passed=p_value < critical_quantile,
             messages=messages))

    def test_metamorphic_decreasing_wilcoxon(self,
                                        df: GiskardDataset,
                                        model,
                                        perturbation_dict,
                                        critical_quantile=0.05,
                                        classification_label=None
                                        ):
        """
        Summary: Tests if the model probability decreases when the feature values are perturbed

        Description: Calculate the Wilcoxon signed-rank test on TWO RELATED samples. Sample (A) is the original probability predictions
        while sample (B) is the probabilities after perturbation of one or more of the features.
        This test computes the decreasing test to study if mean(B) < mean(A)
        The test is passed when the p-value of the Wilcoxon signed-rank test between (A) and (B) is below the critical quantile

        Example: For a credit scoring model, the test is passed when a decrease of wage by 10%,
                 causes a statistically significant probability decrease.

        Args:
            df(GiskardDataset):
                Dataset used to compute the test
            model(GiskardModel):
                Model used to compute the test
            perturbation_dict(dict):
                Dictionary of the perturbations. It provides the perturbed features as key
                and a perturbation lambda function as value
            critical_quantile(float):
                Critical quantile above which the null hypothesis cannot be rejected

        Returns:
            actual_slices_size:
                Length of actual_slice tested
            message:
                Test result message
            metric:
                The Wilcoxon signed-rank test in terms of p-value between unchanged rows over the perturbed rows
            passed:
                TRUE if the p-value of the Wilcoxon signed-rank test between (A) and (B) is below the critical value
        """

        assert (
            model.model_type != "classification"
            or str(classification_label) in model.classification_labels
        ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic_wilcoxon(direction=Direction.Decreasing,
                                          actual_slice=df,
                                          model=model,
                                          perturbation_dict=perturbation_dict,
                                          classification_label=classification_label,
                                          window_size=float("nan"),
                                          critical_quantile=critical_quantile)

    def test_metamorphic_increasing_wilcoxon(self,
                                        df: GiskardDataset,
                                        model,
                                        perturbation_dict,
                                        critical_quantile=0.05,
                                        classification_label=None
                                        ):
        """
        Summary: Tests if the model probability increases when the feature values are perturbed

        Description: Calculate the Wilcoxon signed-rank test on TWO RELATED samples. Sample (A) is the original probability predictions
        while sample (B) is the probabilities after perturbation of one or more of the features.
        This test computes the increasing test to study if mean(A) < mean(B)
        The test is passed when the p-value of the Wilcoxon signed-rank test between (A) and (B) is below the critical quantile

        Example: For a credit scoring model, the test is passed when a decrease of wage by 10%,
                 causes a statistically significant probability increase.

        Args:
            df(GiskardDataset):
                Dataset used to compute the test
            model(GiskardModel):
                Model used to compute the test
            perturbation_dict(dict):
                Dictionary of the perturbations. It provides the perturbed features as key
                and a perturbation lambda function as value
            critical_quantile(float):
                Critical quantile above which the null hypothesis cannot be rejected

        Returns:
            actual_slices_size:
                Length of actual_slice tested
            message:
                Test result message
            metric:
                The Wilcoxon signed-rank test in terms of p-value between unchanged rows over the perturbed rows
            passed:
                TRUE if the p-value of the Wilcoxon signed-rank test between (A) and (B) is below the critical value
        """

        assert (
            model.model_type != "classification"
            or str(classification_label) in model.classification_labels
        ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic_wilcoxon(direction=Direction.Increasing,
                                          actual_slice=df,
                                          model=model,
                                          perturbation_dict=perturbation_dict,
                                          classification_label=classification_label,
                                          window_size=float("nan"),
                                          critical_quantile=critical_quantile)

    def test_metamorphic_invariance_wilcoxon(self,
                                        df: GiskardDataset,
                                        model,
                                        perturbation_dict,
                                        window_size=0.2,
                                        critical_quantile=0.05
                                        ) -> SingleTestResult:
        """
        Summary: Tests if the model predictions are statistically invariant when the feature values are perturbed.

        Description: Calculate the Wilcoxon signed-rank test on TWO RELATED samples. Sample (A) is the original probability predictions
        while sample (B) is the probabilities after perturbation of one or more of the features.
        This test computes the equivalence test to show that mean(B) - window_size/2 < mean(A) < mean(B) + window_size/2
        The test is passed when the following tests pass:
        - the p-value of the t-test between (A) and (B)+window_size/2 is below the critical quantile
        - the p-value of the t-test between (B)-window_size/2 and (A) is below the critical quantile

        Example: The test is passed when, after switching gender from male to female,
        the probability distributions remains statistically invariant. In other words, the test is passed if the mean of the
        perturbed sample is statistically within a window determined by the user.

        Args:
            df(GiskardDataset):
                Dataset used to compute the test
            model(GiskardModel):
                Model used to compute the test
            perturbation_dict(dict):
                Dictionary of the perturbations. It provides the perturbed features as key
                and a perturbation lambda function as value
            window_size(float):
                Probability window in which the mean of the perturbed sample can be in
            critical_quantile(float):
                Critical quantile above which the null hypothesis cannot be rejected

        Returns:
            actual_slices_size:
                Length of actual_slice tested
            message:
                Test result message
            metric:
                The t-test in terms of p-value between unchanged rows over the perturbed rows
            passed:
                TRUE if the p-value of the Wilcoxon signed-rank test between (A) and (B)+window_size/2 < critical_quantile && the p-value of the t-test between (B)-window_size/2 and (A) < critical_quantile
        """

        return self._test_metamorphic_wilcoxon(direction=Direction.Invariant,
                                      actual_slice=df,
                                      model=model,
                                      perturbation_dict=perturbation_dict,
                                      window_size=window_size,
                                      critical_quantile=critical_quantile)
