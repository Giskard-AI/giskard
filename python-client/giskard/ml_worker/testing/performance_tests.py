import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.core.model import GiskardModel
from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult
from giskard.ml_worker.testing.abstract_test_collection import AbstractTestCollection


class PerformanceTests(AbstractTestCollection):
    @staticmethod
    def _verify_target_availability(dataset):
        if not dataset.target:
            raise ValueError("Target column is not available")

    def test_auc(self, actual_slice: GiskardDataset, model: GiskardModel, threshold=1.0):

        """
        Test if the model AUC performance is higher than a threshold for a given slice

        Example : The test is passed when the AUC for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value of AUC metrics

        Returns:
          actual_slices_size:
              Length of actual_slice tested
          metric:
              The AUC performance metric
          passed:
              TRUE if AUC metrics >= threshold
        """
        self._verify_target_availability(actual_slice)
        if len(model.classification_labels) == 2:
            metric = roc_auc_score(
                actual_slice.df[actual_slice.target], model.run_predict(actual_slice).raw_prediction
            )
        else:
            predictions = model.run_predict(actual_slice).all_predictions
            non_declared_categories = set(predictions.columns) - set(
                actual_slice.df[actual_slice.target].unique()
            )
            assert not len(
                non_declared_categories
            ), f'Predicted classes don\'t exist in the dataset "{actual_slice.target}" column: {non_declared_categories}'

            metric = roc_auc_score(
                actual_slice.df[actual_slice.target], predictions, multi_class="ovr"
            )

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)], metric=metric, passed=metric >= threshold
            )
        )

    def _test_classification_score(
        self, score_fn, gsk_dataset: GiskardDataset, model: GiskardModel, threshold=1.0
    ):
        self._verify_target_availability(gsk_dataset)
        is_binary_classification = len(model.classification_labels) == 2
        gsk_dataset.df.reset_index(drop=True, inplace=True)
        actual_target = gsk_dataset.df[gsk_dataset.target].astype(str)
        prediction = model.run_predict(gsk_dataset).prediction
        if is_binary_classification:
            metric = score_fn(actual_target, prediction, pos_label=model.classification_labels[1])
        else:
            metric = score_fn(actual_target, prediction, average="macro")

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(gsk_dataset)], metric=metric, passed=metric >= threshold
            )
        )

    def _test_accuracy_score(self, gsk_dataset: GiskardDataset, model: GiskardModel, threshold=1.0):
        self._verify_target_availability(gsk_dataset)
        gsk_dataset.df.reset_index(drop=True, inplace=True)
        prediction = model.run_predict(gsk_dataset).prediction
        actual_target = gsk_dataset.df[gsk_dataset.target].astype(str)

        metric = accuracy_score(actual_target, prediction)

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(gsk_dataset)], metric=metric, passed=metric >= threshold
            )
        )

    def _test_regression_score(
        self, score_fn, giskard_ds, model: GiskardModel, threshold=1.0, r2=False
    ):
        results_df = pd.DataFrame()
        giskard_ds.df.reset_index(drop=True, inplace=True)
        self._verify_target_availability(giskard_ds)

        results_df["actual_target"] = giskard_ds.df[giskard_ds.target]
        results_df["prediction"] = model.run_predict(giskard_ds).raw_prediction

        metric = score_fn(results_df["actual_target"], results_df["prediction"])

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(giskard_ds)],
                metric=metric,
                passed=metric >= threshold if r2 else metric <= threshold,
            )
        )

    def test_f1(self, actual_slice: GiskardDataset, model: GiskardModel, threshold=1.0):
        """
        Test if the model F1 score is higher than a defined threshold for a given slice

        Example: The test is passed when F1 score for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for F1 Score

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            metric:
              The F1 score metric
            passed:
              TRUE if F1 Score metrics >= threshold
        """
        return self._test_classification_score(f1_score, actual_slice, model, threshold)

    def test_accuracy(self, actual_slice: GiskardDataset, model: GiskardModel, threshold=1.0):
        """
        Test if the model Accuracy is higher than a threshold for a given slice

        Example: The test is passed when the Accuracy for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for Accuracy

        Returns:
          actual_slices_size:
              Length of actual_slice tested
          metric:
              The Accuracy metric
          passed:
              TRUE if Accuracy metrics >= threshold
        """
        return self._test_accuracy_score(actual_slice, model, threshold)

    def test_precision(self, actual_slice, model: GiskardModel, threshold=1.0):
        """
        Test if the model Precision is higher than a threshold for a given slice

        Example: The test is passed when the Precision for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for Precision
        Returns:
            actual_slices_size:
              Length of actual_slice tested
            metric:
              The Precision metric
            passed:
              TRUE if Precision metrics >= threshold
        """
        return self._test_classification_score(precision_score, actual_slice, model, threshold)

    def test_recall(self, actual_slice, model: GiskardModel, threshold=1.0):
        """
        Test if the model Recall is higher than a threshold for a given slice

        Example: The test is passed when the Recall for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for Recall
        Returns:
            actual_slices_size:
              Length of actual_slice tested
            metric:
              The Recall metric
            passed:
              TRUE if Recall metric >= threshold
        """
        return self._test_classification_score(recall_score, actual_slice, model, threshold)

    @staticmethod
    def _get_rmse(y_actual, y_predicted):
        return np.sqrt(mean_squared_error(y_actual, y_predicted))

    def test_rmse(self, actual_slice, model: GiskardModel, threshold=1.0):
        """
        Test if the model RMSE is lower than a threshold

        Example: The test is passed when the RMSE is lower than 10

        Args:
            actual_slice(GiskardDataset):
              Slice of actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for RMSE
        Returns:
            actual_slices_size:
              Length of actual_slice tested
            metric:
              The RMSE metric
            passed:
              TRUE if RMSE metric <= threshold
        """
        return self._test_regression_score(self._get_rmse, actual_slice, model, threshold)

    def test_mae(self, actual_slice, model: GiskardModel, threshold=1.0):
        """
        Test if the model Mean Absolute Error is lower than a threshold

        Example: The test is passed when the MAE is lower than 10

        Args:
            actual_slice(GiskardDataset):
              Slice of actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for MAE

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            reference_slices_size:
              Length of reference_slice tested
            metric:
              The MAE metric
            passed:
              TRUE if MAE metric <= threshold
        """
        return self._test_regression_score(mean_absolute_error, actual_slice, model, threshold)

    def test_r2(self, actual_slice, model: GiskardModel, threshold=1.0):
        """
        Test if the model R-Squared is higher than a threshold

        Example: The test is passed when the R-Squared is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
              Slice of actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for R-Squared

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            metric:
              The R-Squared metric
            passed:
              TRUE if R-Squared metric >= threshold
        """
        return self._test_regression_score(r2_score, actual_slice, model, threshold, r2=True)

    def _test_diff_prediction(
        self, test_fn, model, actual_slice, reference_slice, threshold=0.5, test_name=None
    ):
        self.do_save_results = False
        metric_1 = test_fn(reference_slice, model).metric
        metric_2 = test_fn(actual_slice, model).metric
        self.do_save_results = True
        try:
            change_pct = abs(metric_1 - metric_2) / metric_1
        except ZeroDivisionError:
            raise ZeroDivisionError(
                f"Unable to calculate performance difference: the {test_name} inside the"
                f" reference_slice is equal to zero"
            )

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                reference_slices_size=[len(reference_slice)],
                metric=change_pct,
                passed=change_pct < threshold,
            )
        )

    def test_diff_accuracy(self, actual_slice, reference_slice, model, threshold=0.1):
        """

        Test if the absolute percentage change of model Accuracy between two samples is lower than a threshold

        Example : The test is passed when the Accuracy for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Accuracy for males is 0.8 (actual_slice) and the Accuracy  for
        females is 0.6 (reference_slice) then the absolute percentage Accuracy change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            reference_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for Accuracy Score difference
        Returns:
            actual_slices_size:
              Length of actual_slice tested
            reference_slices_size:
              Length of reference_slice tested
            metric:
              The Accuracy difference  metric
            passed:
              TRUE if Accuracy difference < threshold
        """
        return self._test_diff_prediction(
            self.test_accuracy,
            model,
            actual_slice,
            reference_slice,
            threshold,
            test_name="Accuracy",
        )

    def test_diff_f1(self, actual_slice, reference_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change in model F1 Score between two samples is lower than a threshold

        Example : The test is passed when the F1 Score for females has a difference lower than 10% from the
        F1 Score for males. For example, if the F1 Score for males is 0.8 (actual_slice) and the F1 Score  for
        females is 0.6 (reference_slice) then the absolute percentage F1 Score  change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            reference_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for F1 Score difference

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            reference_slices_size:
              Length of reference_slice tested
            metric:
              The F1 Score difference  metric
            passed:
              TRUE if F1 Score difference < threshold
        """
        return self._test_diff_prediction(
            self.test_f1, model, actual_slice, reference_slice, threshold, test_name="F1 Score"
        )

    def test_diff_precision(self, actual_slice, reference_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change of model Precision between two samples is lower than a threshold

        Example : The test is passed when the Precision for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Precision for males is 0.8 (actual_slice) and the Precision  for
        females is 0.6 (reference_slice) then the absolute percentage Precision change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            reference_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for Precision difference
        Returns:
            actual_slices_size:
              Length of actual_slice tested
            reference_slices_size:
              Length of reference_slice tested
            metric:
              The Precision difference  metric
            passed:
              TRUE if Precision difference < threshold
        """
        return self._test_diff_prediction(
            self.test_precision,
            model,
            actual_slice,
            reference_slice,
            threshold,
            test_name="Precision",
        )

    def test_diff_recall(self, actual_slice, reference_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change of model Recall between two samples is lower than a threshold

        Example : The test is passed when the Recall for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Recall for males is 0.8 (actual_slice) and the Recall  for
        females is 0.6 (reference_slice) then the absolute percentage Recall change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            reference_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for Recall difference
        Returns:
            actual_slices_size:
              Length of actual_slice tested
            reference_slices_size:
              Length of reference_slice tested
            metric:
              The Recall difference  metric
            passed:
              TRUE if Recall difference < threshold
        """
        return self._test_diff_prediction(
            self.test_recall, model, actual_slice, reference_slice, threshold, test_name="Recall"
        )

    def test_diff_reference_actual_f1(self, reference_slice, actual_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change in model F1 Score between reference and actual data
        is lower than a threshold

        Example : The test is passed when the F1 Score for reference dataset has a difference lower than 10% from the
        F1 Score for actual dataset. For example, if the F1 Score for reference dataset is 0.8 (reference_slice) and the
         F1 Score  for actual dataset is 0.6 (actual_slice) then the absolute percentage F1 Score  change is
        0.2 / 0.8 = 0.25 and the test will fail.

        Args:
            actual_slice(GiskardDataset):
              Slice of actual dataset
            reference_slice(GiskardDataset):
              Slice of reference dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for F1 Score difference
        Returns:
          actual_slices_size:
              Length of actual_slice tested
          reference_slices_size:
              Length of reference_slice tested
          metric:
              The F1 Score difference  metric
          passed:
              TRUE if F1 Score difference < threshold
        """
        return self._test_diff_prediction(
            self.test_f1, model, reference_slice, actual_slice, threshold, test_name="F1 Score"
        )

    def test_diff_reference_actual_accuracy(
        self, reference_slice, actual_slice, model, threshold=0.1
    ):
        """
        Test if the absolute percentage change in model Accuracy between reference and actual data
        is lower than a threshold

        Example : The test is passed when the Accuracy for reference dataset has a difference lower than 10% from the
        Accuracy for actual dataset. For example, if the Accuracy for reference dataset is 0.8 (reference_slice) and the
         Accuracy  for actual dataset is 0.6 (actual_slice) then the absolute percentage Accuracy
        change is 0.2 / 0.8 = 0.25 and the test will fail.

        Args:
            actual_slice(GiskardDataset):
              Slice of actual dataset
            reference_slice(GiskardDataset):
              Slice of reference dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for Accuracy difference
        Returns:
            actual_slices_size:
              Length of actual_slice tested
            reference_slices_size:
              Length of reference_slice tested
            metric:
              The Accuracy difference  metric
            passed:
              TRUE if Accuracy difference < threshold
        """
        return self._test_diff_prediction(
            self.test_accuracy,
            model,
            reference_slice,
            actual_slice,
            threshold,
            test_name="Accuracy",
        )

    def test_diff_rmse(self, actual_slice, reference_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change of model RMSE between two samples is lower than a threshold

        Example : The test is passed when the RMSE for females has a difference lower than 10% from the
        RMSE for males. For example, if the RMSE for males is 0.8 (actual_slice) and the RMSE  for
        females is 0.6 (reference_slice) then the absolute percentage RMSE change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
              Slice of the actual dataset
            reference_slice(GiskardDataset):
              Slice of the actual dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for RMSE difference

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            reference_slices_size:
              Length of reference_slice tested
            metric:
              The RMSE difference  metric
            passed:
              TRUE if RMSE difference < threshold
        """
        return self._test_diff_prediction(
            self.test_rmse, model, actual_slice, reference_slice, threshold, test_name="RMSE"
        )

    def test_diff_reference_actual_rmse(self, reference_slice, actual_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change in model RMSE between reference and actual data
        is lower than a threshold

        Example : The test is passed when the RMSE for reference dataset has a difference lower than 10% from the
        RMSE for actual dataset. For example, if the RMSE for reference dataset is 0.8 (reference_slice) and the RMSE
        for actual dataset is 0.6 (actual_slice) then the absolute percentage RMSE  change is 0.2 / 0.8 = 0.25
        and the test will fail.

        Args:
            actual_slice(GiskardDataset):
              Slice of actual dataset
            reference_slice(GiskardDataset):
              Slice of reference dataset
            model(GiskardModel):
              Model used to compute the test
            threshold(float):
              Threshold value for RMSE difference
        Returns:
          actual_slices_size:
              Length of actual_slice tested
          reference_slices_size:
              Length of reference_slice tested
          metric:
              The RMSE difference  metric
          passed:
              TRUE if RMSE difference < threshold
        """
        return self._test_diff_prediction(
            self.test_rmse, model, reference_slice, actual_slice, threshold, test_name="RMSE"
        )
