import pandas as pd
import numpy as np
from typing import Callable

from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.core.model import GiskardModel
from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult, TestMessage, TestMessageType
from giskard.ml_worker.testing.abstract_test_collection import AbstractTestCollection

class StatisticalTests(AbstractTestCollection):
    def test_right_label(
            self,
            actual_slice: GiskardDataset,
            model: GiskardModel,
            classification_label: str,
            threshold=0.5,
    ) -> SingleTestResult:
        """
        Summary: Test if the model returns the right classification label for a slice

        Description: The test is passed when the percentage of rows returning the right
        classification label is higher than the threshold in a given slice

        Example: For a credit scoring model, the test is passed when more than 50%
        of people with high-salaries are classified as “non default”

        Args:
           actual_slice(GiskardDataset):
              Slice of the  actual dataset
          model(GiskardModel):
              Model used to compute the test
          classification_label(str):
              Classification label you want to test
          threshold(float):
              Threshold for the percentage of passed rows

        Returns:
          actual_slices_size:
              Length of actual_slice tested
          metrics:
              The ratio of rows with the right classification label over the total of rows in the slice
          passed:
              TRUE if passed_ratio > threshold
        """
        actual_slice.df.reset_index(drop=True, inplace=True)
        prediction_results = model.run_predict(actual_slice).prediction
        assert (
                classification_label in model.classification_labels
        ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        passed_idx = actual_slice.df.loc[prediction_results == classification_label].index.values

        passed_ratio = len(passed_idx) / len(actual_slice)
        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                metric=passed_ratio,
                passed=passed_ratio > threshold,
            )
        )

    def test_output_in_range(
            self,
            actual_slice: GiskardDataset,
            model: GiskardModel,
            classification_label=None,
            min_range: float = 0.3,
            max_range: float = 0.7,
            threshold=0.5,
    ) -> SingleTestResult:
        """
        Summary: Test if the model output belongs to the right range for a slice

        Description: - The test is passed when the ratio of rows in the right range inside the
        slice is higher than the threshold.

         For classification: Test if the predicted probability for a given classification label
         belongs to the right range for a dataset slice

        For regression : Test if the predicted output belongs to the right range for a dataset slice

        Example :
        For Classification: For a credit scoring model, the test is passed when more than 50% of
        people with high wage have a probability of defaulting between 0 and 0.1

        For Regression : The predicted Sale Price of a house in the city falls in a particular range
        Args:
            actual_slice(GiskardDataset):
                Slice of the actual dataset
            model(GiskardModel):
                Model used to compute the test
            classification_label(str):
                Optional. Classification label you want to test
            min_range(float):
                Minimum probability of occurrence of classification label
            max_range(float):
                Maximum probability of occurrence of classification label
            threshold(float):
                Threshold for the percentage of passed rows

        Returns:
            actual_slices_size:
                Length of actual_slice tested
            metrics:
                The proportion of rows in the right range inside the slice
            passed:
                TRUE if metric > threshold
        """
        results_df = pd.DataFrame()
        actual_slice.df.reset_index(drop=True, inplace=True)

        prediction_results = model.run_predict(actual_slice)

        if model.model_type == "regression":
            results_df["output"] = prediction_results.raw_prediction

        elif model.model_type == "classification":
            assert (
                    classification_label in model.classification_labels
            ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'
            results_df["output"] = prediction_results.all_predictions[classification_label]

        else:
            raise ValueError(f"Prediction task is not supported: {model.model_type}")

        passed_idx = actual_slice.df.loc[
            (results_df["output"] <= max_range) & (results_df["output"] >= min_range)
            ].index.values

        passed_ratio = len(passed_idx) / len(actual_slice)

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                metric=passed_ratio,
                passed=passed_ratio >= threshold,
            )
        )

    def test_disparate_impact(self,
                              gsk_dataset: GiskardDataset,
                              protected_slice: Callable[[pd.DataFrame], pd.DataFrame],
                              unprotected_slice: Callable[[pd.DataFrame], pd.DataFrame],
                              model: GiskardModel,
                              positive_outcome,
                              min_threshold=0.8,
                              max_threshold=1.25) -> SingleTestResult:

        """
        Summary: Tests if the model is biased more towards an unprotected slice of the dataset over a protected slice.
        Note that this test reflects only a possible bias in the model while being agnostic to any bias in the dataset
        it trained on. The Disparate Impact (DI) is only valid for classification models and is computed as the ratio
        between the average count of correct predictions for the protected_slice over the unprotected_slice given a
        certain positive_outcome.

        Description: Calculate the Disparate Impact between a protected and unprotected slice of a dataset. Otherwise
        known as the "80 percent" rule, the Disparate Impact determines if a model was having an "adverse impact" on a
        protected (or minority in some cases) group.

        Example: The rule was originally based on the rates at which job applicants were hired. For example, if XYZ
        Company hired 50 percent of the men applying for work in a predominantly male occupation while hiring only 20
        percent of the female applicants, one could look at the ratio of those two hiring rates to judge whether there
        might be a discrimination problem. The ratio of 20:50 means that the rate of hiring for female applicants is
        only 40 percent of the rate of hiring for male applicants. That is, 20 divided by 50 equals
        0.40, which is equivalent to 40 percent. Clearly, 40 percent is well below the 80 percent that was arbitrarily
        set as an acceptable difference in hiring rates. Therefore, in this example, XYZ Company could have been called
        upon to prove that there was a legitimate reason for hiring men at a rate so much higher than the rate of hiring
        women.

        Args:
              gsk_dataset(GiskardDataset):
                  Dataset used to compute the test
              protected_slice(Callable):
                  Slice that defines the protected group from the full dataset given
              unprotected_slice(Callable):
                  Slice that defines the unprotected group from the full dataset given
              model(GiskardModel):
                  Model used to compute the test
              positive_outcome(str or float):
                  The target value that is considered a positive outcome in the dataset
              min_threshold(float):
                  Threshold below which the DI test is considered to fail, by default 0.8
              max_threshold(float):
                  Threshold above which the DI test is considered to fail, by default 1.25

        Returns:
              metric:
                  The disparate impact ratio
              passed:
                  TRUE if the disparate impact ratio > min_threshold && disparate impact ratio < max_threshold
        """

        testing = gsk_dataset.df[gsk_dataset.target]

        if positive_outcome not in gsk_dataset.df[gsk_dataset.target].values:
            raise ValueError(
                f"The positive outcome chosen {positive_outcome} is not part of the dataset columns {gsk_dataset.columns}."
            )

        gsk_dataset.df.reset_index(drop=True, inplace=True)
        protected_ds=gsk_dataset.slice(protected_slice)
        unprotected_ds=gsk_dataset.slice(unprotected_slice)

        if protected_ds.df.equals(unprotected_ds.df):
            raise ValueError(
                f"The protected and unprotected datasets are equal. Please check that you chose different slices."
            )

        positive_idx = list(model.classification_labels).index(positive_outcome)

        protected_predictions = np.squeeze(model.run_predict(protected_ds).raw_prediction == positive_idx)
        unprotected_predictions = np.squeeze(model.run_predict(unprotected_ds).raw_prediction == positive_idx)

        protected_proba = np.count_nonzero(protected_predictions)/len(protected_ds.df)
        unprotected_proba = np.count_nonzero(unprotected_predictions)/len(unprotected_ds.df)
        disparate_impact_score = protected_proba/unprotected_proba

        messages = [TestMessage(
            type=TestMessageType.INFO,
            text=f"min_threshold = {min_threshold}, max_threshold = {max_threshold}"
        )]

        return self.save_results(
            SingleTestResult(
                metric=disparate_impact_score,
                passed=(disparate_impact_score > min_threshold)*(disparate_impact_score < max_threshold),
                messages = messages
            )
        )