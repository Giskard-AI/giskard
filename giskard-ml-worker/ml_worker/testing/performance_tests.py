from functools import partial
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, recall_score
from sklearn.metrics import roc_auc_score, f1_score, precision_score, mean_squared_error, \
    mean_absolute_error, r2_score

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.core.model import GiskardModel
from ml_worker.testing.abstract_test_collection import AbstractTestCollection
from ml_worker.testing.utils import save_df, compress


class RawSingleTestResult:
    def __init__(self, actual_slices_size=int, metric=float, passed=bool, output_df=pd.DataFrame):
        self.actual_slices_size = actual_slices_size
        self.metric = metric
        self.passed = passed
        self.output_df = output_df


class PerformanceTests(AbstractTestCollection):
    def transform_results(self, results):
        return self.save_results(
            SingleTestResult(
                actual_slices_size=results.actual_slices_size,
                metric=results.metric,
                passed=results.passed,
                output_df=compress(save_df(results.output_df))
            ))

    def test_auc(self, actual_slice: GiskardDataset, model: GiskardModel, threshold=1):

        """
        Test if the model AUC performance is higher than a threshold for a given slice

        Example : The test is passed when the AUC for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(GiskardModel):
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
        if len(model.classification_labels) == 2:
            metric = roc_auc_score(actual_slice.df[actual_slice.target],
                                   model.run_predict(actual_slice.df).raw_prediction)
        else:
            metric = roc_auc_score(actual_slice.df[actual_slice.target],
                                   model.run_predict(actual_slice.df).all_predictions, multi_class='ovr')

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                metric=metric,
                passed=metric >= threshold
            ))

    def _test_classification_score(self, score_fn, gsk_dataset: GiskardDataset, model: GiskardModel, threshold=1):
        is_binary_classification = len(model.classification_labels) == 2
        dataframe = gsk_dataset.df
        prediction = model.run_predict(dataframe).raw_prediction
        labels_mapping = {model.classification_labels[i]: i for i in range(len(model.classification_labels))}
        actual_target = dataframe[gsk_dataset.target].map(labels_mapping)
        if is_binary_classification:
            metric = score_fn(actual_target, prediction)
        else:
            metric = score_fn(actual_target, prediction, average='macro')
        output_df_sample = dataframe.loc[actual_target != prediction]

        return RawSingleTestResult(
            actual_slices_size=[len(gsk_dataset)],
            metric=metric,
            passed=metric >= threshold,
            output_df=output_df_sample
        )

    def _test_accuracy_score(self, score_fn, gsk_dataset: GiskardDataset, model: GiskardModel, threshold=1):
        dataframe = gsk_dataset.df
        prediction = model.run_predict(dataframe).raw_prediction
        labels_mapping = {model.classification_labels[i]: i for i in range(len(model.classification_labels))}
        actual_target = dataframe[gsk_dataset.target].map(labels_mapping)

        metric = score_fn(actual_target, prediction)

        output_df_sample = dataframe.loc[actual_target != prediction]

        return RawSingleTestResult(
                actual_slices_size=[len(gsk_dataset)],
                metric=metric,
                passed=metric >= threshold,
                output_df=output_df_sample
            )

    def _test_regression_score(self, score_fn, giskard_ds, model: GiskardModel, threshold=1, r2=False,
                               percent_rows=0.3):
        results_df = pd.DataFrame()
        results_df["actual_target"] = giskard_ds.df[giskard_ds.target]
        results_df["prediction"] = model.run_predict(giskard_ds.df).raw_prediction

        metric = score_fn(results_df["actual_target"], results_df["prediction"])
        output_df_sample = self._get_failed_df(results_df, percent_rows)

        return RawSingleTestResult(
                actual_slices_size=[len(giskard_ds)],
                metric=metric,
                passed=metric >= threshold if r2 else metric <= threshold,
                output_df=output_df_sample
            )

    def test_f1(self, actual_slice: GiskardDataset, model: GiskardModel, threshold=1):
        """
        Test if the model F1 score is higher than a defined threshold for a given slice

        Example: The test is passed when F1 score for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(GiskardModel):
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
        results = self._test_classification_score(f1_score, actual_slice, model, threshold)
        transformed_results = self.transform_results(results)
        return transformed_results

    def test_accuracy(self, actual_slice: GiskardDataset, model: GiskardModel, threshold=1):
        """
        Test if the model Accuracy is higher than a threshold for a given slice

        Example: The test is passed when the Accuracy for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(GiskardModel):
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
        results = self._test_accuracy_score(accuracy_score, actual_slice, model, threshold)
        transformed_results = self.transform_results(results)

        return transformed_results

    def test_precision(self, actual_slice, model: GiskardModel, threshold=1):
        """
        Test if the model Precision is higher than a threshold for a given slice

        Example: The test is passed when the Precision for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(GiskardModel):
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
        results = self._test_classification_score(precision_score, actual_slice, model, threshold)
        transformed_results = self.transform_results(results)

        return transformed_results

    def test_recall(self, actual_slice, model: GiskardModel, threshold=1):
        """
        Test if the model Recall is higher than a threshold for a given slice

        Example: The test is passed when the Recall for females is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(GiskardModel):
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
        results = self._test_classification_score(recall_score, actual_slice, model, threshold)
        transformed_results = self.transform_results(results)

        return transformed_results

    @staticmethod
    def _get_failed_df(results_df, percent_rows=0.3):
        results_df["metric"] = results_df.apply(lambda x: (abs(x["actual_target"] - x["prediction"])), axis=1)
        top_n = round(percent_rows * len(results_df))
        output_df = results_df.nlargest(top_n, 'metric')
        return output_df

    @staticmethod
    def _get_rmse(y_actual, y_predicted):
        return np.sqrt(mean_squared_error(y_actual, y_predicted))

    def test_rmse(self, actual_slice, model: GiskardModel, threshold=1, percent_rows=0.3):
        """
        Test if the model RMSE is lower than a threshold

        Example: The test is passed when the RMSE is lower than 0.7

        Args:
            actual_slice(GiskardDataset):
                actual dataset 
            model(GiskardModel):
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
        results = self._test_regression_score(self._get_rmse, actual_slice, model, threshold, percent_rows=percent_rows)
        transformed_results = self.transform_results(results)

        return transformed_results

    def test_mae(self, actual_slice, model: GiskardModel, threshold=1, percent_rows=0.3):
        """
        Test if the model Mean Absolute Error is lower than a threshold

        Example: The test is passed when the MAE is lower than 0.7

        Args:
            actual_slice(GiskardDataset):
                actual dataset 
            model(GiskardModel):
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
        results = self._test_regression_score(mean_absolute_error, actual_slice, model,
                                              threshold, percent_rows=percent_rows)
        transformed_results = self.transform_results(results)

        return transformed_results

    def test_r2(self, actual_slice, model: GiskardModel, threshold=1):
        """
        Test if the model R-Squared is higher than a threshold

        Example: The test is passed when the R-Squared is higher than 0.7

        Args:
            actual_slice(GiskardDataset):
                actual dataset 
            model(GiskardModel):
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
        results = self._test_regression_score(r2_score, actual_slice, model, threshold, r2=True)
        transformed_results = self.transform_results(results)

        return transformed_results

    def _test_diff_prediction(self, test_fn, model, actual_slice, reference_slice, threshold, percent_rows=None):
        self.do_save_results = False
        result_1 = test_fn(reference_slice, model, percent_rows=percent_rows) if percent_rows is not None \
            else test_fn(reference_slice, model)
        metric_1 = result_1.metric

        result_2 = test_fn(actual_slice, model, percent_rows=percent_rows) if percent_rows is not None \
            else test_fn(actual_slice, model)
        metric_2 = result_2.metric
        output_df_2 = result_2.output_df

        self.do_save_results = True
        change_pct = abs(metric_1 - metric_2) / metric_1
        output_df_sample = compress(save_df(output_df_2))

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                reference_slices_size=[len(reference_slice)],
                metric=change_pct,
                passed=change_pct < threshold,
                output_df=output_df_sample
            ))

    def test_diff_accuracy(self, actual_slice, reference_slice, model, threshold=0.1):
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
            model(GiskardModel):
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
        partial_accuracy = partial(self._test_classification_score, accuracy_score)
        return self._test_diff_prediction(partial_accuracy, model, actual_slice, reference_slice, threshold)

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
            model(GiskardModel):
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
        partial_f1 = partial(self._test_classification_score, f1_score)
        return self._test_diff_prediction(partial_f1, model, actual_slice, reference_slice, threshold)

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
            model(GiskardModel):
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
        partial_precision = partial(self._test_classification_score, precision_score)
        return self._test_diff_prediction(partial_precision, model, actual_slice, reference_slice, threshold)

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
            model(GiskardModel):
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
        partial_recall = partial(self._test_classification_score, recall_score)
        return self._test_diff_prediction(partial_recall, model, actual_slice, reference_slice, threshold)

    def _test_diff_reference_actual(self, test_fn, model, reference_slice, actual_slice, threshold=0.1):
        self.do_save_results = False
        result_1 = test_fn(reference_slice, model)
        metric_1 = result_1.metric

        result_2 = test_fn(actual_slice, model)
        metric_2 = result_2.metric
        output_df_2 = result_2.output_df

        self.do_save_results = True
        change_pct = abs(metric_1 - metric_2) / metric_1
        output_df_sample = compress(save_df(output_df_2))

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                reference_slices_size=[len(reference_slice)],
                metric=change_pct,
                passed=change_pct < threshold,
                output_df=output_df_sample

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
            model(GiskardModel):
                uploaded model
            threshold(int):
                threshold value for F1 Score difference


        Returns:
            metric:
                the F1 Score difference  metric
            passed:
                TRUE if F1 Score difference < threshold

        """
        partial_f1 = partial(self._test_classification_score, f1_score)
        return self._test_diff_reference_actual(partial_f1, model, reference_slice, actual_slice, threshold)

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
            model(GiskardModel):
                uploaded model
            threshold(int):
                threshold value for Accuracy difference


        Returns:
            metric:
                the Accuracy difference  metric
            passed:
                TRUE if Accuracy difference < threshold

        """
        partial_accuracy = partial(self._test_classification_score, accuracy_score)
        return self._test_diff_reference_actual(partial_accuracy, model, reference_slice, actual_slice, threshold)

    def test_diff_rmse(self, actual_slice, reference_slice, model, threshold=0.1, percent_rows=0.15):
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
            model(GiskardModel):
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
        partial_rmse = partial(self._test_regression_score, self._get_rmse)
        return self._test_diff_prediction(partial_rmse, model, actual_slice, reference_slice, threshold,
                                          percent_rows=percent_rows)

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
            model(GiskardModel):
                uploaded model
            threshold(int):
                threshold value for RMSE difference

        Returns:
            metric:
                the RMSE difference  metric
            passed:
                TRUE if RMSE difference < threshold

        """
        partial_rmse = partial(self._test_regression_score, self._get_rmse)
        return self._test_diff_reference_actual(partial_rmse, model, reference_slice, actual_slice, threshold)
