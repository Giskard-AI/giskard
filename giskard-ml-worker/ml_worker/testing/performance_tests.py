import numpy as np
from giskard_client import ModelInspector
from sklearn.metrics import accuracy_score, recall_score
from sklearn.metrics import roc_auc_score, f1_score, precision_score, mean_squared_error, \
    mean_absolute_error, r2_score

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.ml import run_predict
from ml_worker.server.ml_worker_service import GiskardDataset
from ml_worker.testing.abstract_test_collection import AbstractTestCollection


class PerformanceTests(AbstractTestCollection):
    def test_auc(self, actual_slice: GiskardDataset, model: ModelInspector, threshold=1):
        """
        Test if the model AUC performance is higher than a threshold for a given slice

        Example : The test is passed when the AUC for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value of AUC metrics

        Returns:
            total rows tested:
                length of actual_slice tested
            metric:
                the AUC performance metric
            passed:
                TRUE if AUC metrics > threshold

        """

        def _calculate_auc(is_binary_classification, prediction, true_value):
            if is_binary_classification:
                return roc_auc_score(true_value, prediction)
            else:
                return roc_auc_score(true_value, prediction, average='macro', multi_class='ovr')

        metric = _calculate_auc(
            len(model.classification_labels) == 2,
            run_predict(actual_slice.df, model).raw_prediction,
            actual_slice.df[actual_slice.target]
        )

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                metric=metric,
                passed=metric >= threshold
            ))

    def _test_classification_score(self, score_fn, gsk_dataset: GiskardDataset, model: ModelInspector, threshold=1):
        is_binary_classification = len(model.classification_labels) == 2
        dataframe = gsk_dataset.df
        prediction = run_predict(dataframe, model).raw_prediction
        labels_mapping = {model.classification_labels[i]: i for i in range(len(model.classification_labels))}
        if is_binary_classification:
            metric = score_fn(dataframe[gsk_dataset.target].map(labels_mapping), prediction)
        else:
            metric = score_fn(dataframe[gsk_dataset.target].map(labels_mapping), prediction, average='macro',
                              multi_class='ovr')

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(gsk_dataset)],
                metric=metric,
                passed=metric >= threshold
            ))

    def _test_regression_score(self, score_fn, giskard_ds, model: ModelInspector, threshold=1, negative=False,
                               r2=False):
        metric = (-1 if negative else 1) * score_fn(
            run_predict(giskard_ds.df, model).raw_prediction,
            giskard_ds.df[giskard_ds.target]
        )
        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(giskard_ds)],
                metric=metric,
                passed=metric >= threshold if r2 else metric <= threshold
            ))

    def test_f1(self, actual_slice: GiskardDataset, model: ModelInspector, threshold=1):
        """
        Test if the model F1 score is higher than a defined threshold for a given slice

        Example: The test is passed when F1 score for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for F1 Score

        Returns:
            total rows tested:
                length of actual_slice tested
            metric:
                the F1 score metric
            passed:
                TRUE if F1 Score metrics > threshold

        """
        return self._test_classification_score(f1_score, actual_slice, model, threshold)

    def test_accuracy(self, actual_slice: GiskardDataset, model: ModelInspector, threshold=1):
        """
        Test if the model Accuracy is higher than a threshold for a given slice

        Example: The test is passed when the Accuracy for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for Accuracy

        Returns:
            total rows tested:
                length of actual_slice tested
            metric:
                the Accuracy metric
            passed:
                TRUE if Accuracy metrics > threshold

        """
        return self._test_classification_score(accuracy_score, actual_slice, model, threshold)

    def test_precision(self, actual_slice, model: ModelInspector, threshold=1):
        """
        Test if the model Precision is higher than a threshold for a given slice

        Example: The test is passed when the Precision for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for Precision

        Returns:
            total rows tested:
                length of actual_slice tested
            metric:
                the Precision metric
            passed:
                TRUE if Precision metrics > threshold

        """
        return self._test_classification_score(precision_score,
                                               actual_slice, model, threshold)

    def test_recall(self, actual_slice, model: ModelInspector, threshold=1):
        """
        Test if the model Recall is higher than a threshold for a given slice

        Example: The test is passed when the Recall for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for Recall

        Returns:
            total rows tested:
                length of actual_slice tested
            metric:
                the Recall metric
            passed:
                TRUE if Recall metric > threshold

        """
        return self._test_classification_score(recall_score,
                                               actual_slice, model, threshold)

    @staticmethod
    def _get_rmse(y_actual, y_predicted):
        return np.sqrt(mean_squared_error(y_actual, y_predicted))

    def test_rmse(self, actual_slice, model: ModelInspector, threshold=1):
        """
        Test if the model RMSE is lower than a threshold

        Example: The test is passed when the RMSE is lower than 0.7

        Args:
            actual_slice(GiskardDataset):
                actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for RMSE

        Returns:
            total rows tested:
                length of actual_slice tested
            metric:
                the RMSE metric
            passed:
                TRUE if RMSE metric < threshold

        """
        return self._test_regression_score(self._get_rmse, actual_slice, model, threshold, negative=False)

    def test_mae(self, actual_slice, model: ModelInspector, threshold=1):
        """
        Test if the model Mean Absolute Error is lower than a threshold

        Example: The test is passed when the MAE is lower than 0.7

        Args:
            actual_slice(GiskardDataset):
                actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for MAE

        Returns:
            total rows tested:
                length of actual_slice tested
            metric:
                the MAE metric
            passed:
                TRUE if MAE metric < threshold

        """
        return self._test_regression_score(mean_absolute_error, actual_slice, model, threshold,
                                           negative=False)

    def test_r2(self, actual_slice, model: ModelInspector, threshold=1):
        """
        Test if the model R-Squared is higher than a threshold

        Example: The test is passed when the R-Squared is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for R-Squared

        Returns:
            total rows tested:
                length of actual_slice tested
            metric:
                the R-Squared metric
            passed:
                TRUE if R-Squared metric > threshold

        """
        return self._test_regression_score(r2_score, actual_slice, model, threshold, r2=True)

    def _test_diff_prediction(self, test_fn, model, actual_slice, reference_slice, threshold):
        self.do_save_results = False
        metric_1 = test_fn(actual_slice, model).metric
        metric_2 = test_fn(reference_slice, model).metric
        self.do_save_results = True
        change_pct = abs(metric_1 - metric_2) / metric_1

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                reference_slices_size=[len(reference_slice)],
                metric=change_pct,
                passed=change_pct < threshold
            ))

    def test_diff_accuracy(self,  actual_slice, reference_slice, model, threshold=0.1):
        """

        Test if the absolute percentage change of model Accuracy between two samples is lower than a threshold

        Example : The test is passed when the Accuracy for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Accuracy for males is 0.8 (actual_slice) and the Accuracy  for
        females is 0.6 (reference_slice) then the absolute percentage Accuracy change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
          actual_slice(GiskardDataset):
              slice of the actual dataset
          reference_slice(GiskardDataset):
              slice of the actual dataset
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for Accuracy Score difference

        Returns:
            total rows tested:
                length of actual dataset
            metric:
                the Accuracy difference  metric
            passed:
                TRUE if Accuracy difference < threshold

        """
        return self._test_diff_prediction(self.test_accuracy, model, actual_slice, reference_slice, threshold)

    def test_diff_f1(self, actual_slice, reference_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change in model F1 Score between two samples is lower than a threshold

        Example : The test is passed when the F1 Score for females has a difference lower than 10% from the
        F1 Score for males. For example, if the F1 Score for males is 0.8 (actual_slice) and the F1 Score  for
        females is 0.6 (reference_slice) then the absolute percentage F1 Score  change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset
            reference_slice(GiskardDataset):
                slice of the actual dataset
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for F1 Score difference

        Returns:
            total rows tested:
                length of actual dataset
            metric:
                the F1 Score difference  metric
            passed:
                TRUE if F1 Score difference < threshold

        """
        return self._test_diff_prediction(self.test_f1, model, actual_slice, reference_slice, threshold)

    def test_diff_precision(self, actual_slice, reference_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change of model Precision between two samples is lower than a threshold

        Example : The test is passed when the Precision for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Precision for males is 0.8 (actual_slice) and the Precision  for
        females is 0.6 (reference_slice) then the absolute percentage Precision change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset
            reference_slice(GiskardDataset):
                slice of the actual dataset
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for Precision difference

        Returns:
            total rows tested:
                length of actual dataset
            metric:
                the Precision difference  metric
            passed:
                TRUE if Precision difference < threshold
        """
        return self._test_diff_prediction(self.test_precision, model, actual_slice, reference_slice, threshold)

    def test_diff_recall(self, actual_slice, reference_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change of model Recall between two samples is lower than a threshold

        Example : The test is passed when the Recall for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Recall for males is 0.8 (actual_slice) and the Recall  for
        females is 0.6 (reference_slice) then the absolute percentage Recall change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset
            reference_slice(GiskardDataset):
                slice of the actual dataset
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for Recall difference

        Returns:
            total rows tested:
                length of actual dataset
            metric:
                the Recall difference  metric
            passed:
                TRUE if Recall difference < threshold
        """
        return self._test_diff_prediction(self.test_recall, model, actual_slice, reference_slice, threshold)

    def _test_diff_reference_actual(self, test_fn, model, reference_slice, actual_slice, threshold=0.1):
        self.do_save_results = False
        metric_1 = test_fn(reference_slice, model).metric
        metric_2 = test_fn(actual_slice, model).metric
        self.do_save_results = True
        change_pct = abs(metric_1 - metric_2) / metric_1

        return self.save_results(
            SingleTestResult(
                metric=change_pct,
                passed=change_pct < threshold
            ))

    def test_diff_reference_actual_f1(self, reference_slice, actual_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change in model F1 Score between reference and actual data
        is lower than a threshold

        Example : The test is passed when the F1 Score for reference dataset has a difference lower than 10% from the
        F1 Score for actual dataset. For example, if the F1 Score for reference dataset is 0.8 (reference_slice) and the F1 Score  for
        actual dataset is 0.6 (actual_slice) then the absolute percentage F1 Score  change is 0.2 / 0.8 = 0.25
        and the test will fail.

        Args:
            reference_slice(GiskardDataset):
                reference dataset 
            actual_slice(GiskardDataset):
                actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for F1 Score difference


        Returns:
            metric:
                the F1 Score difference  metric
            passed:
                TRUE if F1 Score difference < threshold

        """
        return self._test_diff_reference_actual(self.test_f1, model, reference_slice, actual_slice, threshold)

    def test_diff_reference_actual_accuracy(self, reference_slice, actual_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change in model Accuracy between reference and actual data
        is lower than a threshold

        Example : The test is passed when the Accuracy for reference dataset has a difference lower than 10% from the
        Accuracy for actual dataset. For example, if the Accuracy for reference dataset is 0.8 (reference_slice) and the Accuracy  for
        actual dataset is 0.6 (actual_slice) then the absolute percentage Accuracy  change is 0.2 / 0.8 = 0.25
        and the test will fail.

        Args:
            reference_slice(GiskardDataset):
                reference dataset 
            actual_slice(GiskardDataset):
                actual dataset 
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for Accuracy difference


        Returns:
            metric:
                the Accuracy difference  metric
            passed:
                TRUE if Accuracy difference < threshold

        """
        return self._test_diff_reference_actual(self.test_accuracy, model, reference_slice, actual_slice, threshold)

    def test_diff_rmse(self, actual_slice, reference_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change of model RMSE between two samples is lower than a threshold

        Example : The test is passed when the RMSE for females has a difference lower than 10% from the
        RMSE for males. For example, if the RMSE for males is 0.8 (actual_slice) and the RMSE  for
        females is 0.6 (reference_slice) then the absolute percentage RMSE change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset
            reference_slice(GiskardDataset):
                slice of the actual dataset
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for RMSE difference

        Returns:
            total rows tested:
                length of actual dataset
            metric:
                the RMSE difference  metric
            passed:
                TRUE if RMSE difference < threshold
        """
        return self._test_diff_prediction(self.test_rmse, model, actual_slice, reference_slice, threshold)

    def test_diff_reference_actual_rmse(self, reference_slice, actual_slice, model, threshold=0.1):
        """
        Test if the absolute percentage change in model RMSE between reference and actual data
        is lower than a threshold

        Example : The test is passed when the RMSE for reference dataset has a difference lower than 10% from the
        RMSE for actual dataset. For example, if the RMSE for reference dataset is 0.8 (reference_slice) and the RMSE  for
        actual dataset is 0.6 (actual_slice) then the absolute percentage RMSE  change is 0.2 / 0.8 = 0.25
        and the test will fail.

        Args:
            reference_slice(GiskardDataset):
                slice of reference dataset
            actual_slice(GiskardDataset):
                slice of actual dataset
            model(ModelInspector):
                uploaded model
            threshold(int):
                threshold value for RMSE difference

        Returns:
            metric:
                the RMSE difference  metric
            passed:
                TRUE if RMSE difference < threshold

        """
        return self._test_diff_reference_actual(self.test_rmse, model, reference_slice, actual_slice, threshold)
