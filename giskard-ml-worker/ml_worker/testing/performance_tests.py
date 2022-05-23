from ai_inspector import ModelInspector
from sklearn.metrics import accuracy_score, recall_score
from sklearn.metrics import roc_auc_score, f1_score, precision_score, mean_squared_error, \
    mean_absolute_error, r2_score
import numpy as np

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.ml import run_predict
from ml_worker.testing.abstract_test_collection import AbstractTestCollection


class PerformanceTests(AbstractTestCollection):
    def test_auc(self, slice_df, model: ModelInspector, target, threshold=1):
        """
        Test if the model AUC performance is higher than a threshold for a given slice

        Example : The test is passed when the AUC for females is higher than 0.7

        Args:
            slice_df(pandas.core.frame.DataFrame):
                slice of the test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value of AUC metrics

        Returns:
            total rows tested:
                length of slice_df tested
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
            run_predict(slice_df, model).raw_prediction,
            slice_df[target]
        )

        return self.save_results(
            SingleTestResult(
                element_count=len(slice_df),
                metric=metric,
                passed=metric >= threshold
            ))

    def _test_classification_score(self, score_fn, slice_df, model: ModelInspector, target, threshold=1):
        is_binary_classification = len(model.classification_labels) == 2
        prediction = run_predict(slice_df, model).raw_prediction
        labels_mapping = {model.classification_labels[i]: i for i in range(len(model.classification_labels))}
        if is_binary_classification:
            metric = score_fn(slice_df[target].map(labels_mapping), prediction)
        else:
            metric = score_fn(slice_df[target].map(labels_mapping), prediction, average='macro', multi_class='ovr')

        return self.save_results(
            SingleTestResult(
                element_count=len(slice_df),
                metric=metric,
                passed=metric >= threshold
            ))

    def _test_regression_score(self, score_fn, df, model: ModelInspector, target, threshold=1, negative=False,
                               r2=False):
        metric = (-1 if negative else 1) * score_fn(
            run_predict(df, model).raw_prediction,
            df[target]
        )
        return self.save_results(
            SingleTestResult(
                element_count=len(df),
                metric=metric,
                passed=metric >= threshold if r2 else metric <= threshold
            ))

    def test_f1(self, slice_df, model: ModelInspector, target, threshold=1):
        """
        Test if the model F1 score is higher than a defined threshold for a given slice

        Example: The test is passed when F1 score for females is higher than 0.7

        Args:
            slice_df(pandas.core.frame.DataFrame):
                slice of the test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for F1 Score

        Returns:
            total rows tested:
                length of slice_df tested
            metric:
                the F1 score metric
            passed:
                TRUE if F1 Score metrics > threshold

        """
        return self._test_classification_score(f1_score,
                                               slice_df, model, target, threshold)

    def test_accuracy(self, slice_df, model: ModelInspector, target, threshold=1):
        """
        Test if the model Accuracy is higher than a threshold for a given slice

        Example: The test is passed when the Accuracy for females is higher than 0.7

        Args:
            slice_df(pandas.core.frame.DataFrame):
                slice of the test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for Accuracy

        Returns:
            total rows tested:
                length of slice_df tested
            metric:
                the Accuracy metric
            passed:
                TRUE if Accuracy metrics > threshold

        """
        return self._test_classification_score(accuracy_score,
                                               slice_df, model, target, threshold)

    def test_precision(self, slice_df, model: ModelInspector, target, threshold=1):
        """
        Test if the model Precision is higher than a threshold for a given slice

        Example: The test is passed when the Precision for females is higher than 0.7

        Args:
            slice_df(pandas.core.frame.DataFrame):
                slice of the test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for Precision

        Returns:
            total rows tested:
                length of slice_df tested
            metric:
                the Precision metric
            passed:
                TRUE if Precision metrics > threshold

        """
        return self._test_classification_score(precision_score,
                                               slice_df, model, target, threshold)

    def test_recall(self, slice_df, model: ModelInspector, target, threshold=1):
        """
        Test if the model Recall is higher than a threshold for a given slice

        Example: The test is passed when the Recall for females is higher than 0.7

        Args:
            slice_df(pandas.core.frame.DataFrame):
                slice of the test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for Recall

        Returns:
            total rows tested:
                length of slice_df tested
            metric:
                the Recall metric
            passed:
                TRUE if Recall metric > threshold

        """
        return self._test_classification_score(recall_score,
                                               slice_df, model, target, threshold)

    def _get_rmse(self, y_actual, y_predicted):
        return np.sqrt(mean_squared_error(y_actual, y_predicted))

    def test_rmse(self, df, model: ModelInspector, target, threshold=1):
        """
        Test if the model RMSE is lower than a threshold

        Example: The test is passed when the RMSE is lower than 0.7

        Args:
            df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for RMSE

        Returns:
            total rows tested:
                length of slice_df tested
            metric:
                the RMSE metric
            passed:
                TRUE if RMSE metric < threshold

        """
        return self._test_regression_score(self._get_rmse, df, model, target, threshold, negative=False)

    def test_mae(self, df, model: ModelInspector, target, threshold=1):
        """
        Test if the model Mean Absolute Error is lower than a threshold

        Example: The test is passed when the MAE is lower than 0.7

        Args:
            df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for MAE

        Returns:
            total rows tested:
                length of slice_df tested
            metric:
                the MAE metric
            passed:
                TRUE if MAE metric < threshold

        """
        return self._test_regression_score(mean_absolute_error, df, model, target, threshold,
                                           negative=False)

    def test_r2(self, df, model: ModelInspector, target, threshold=1):
        """
        Test if the model R-Squared is higher than a threshold

        Example: The test is passed when the R-Squared is higher than 0.7

        Args:
            df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for R-Squared

        Returns:
            total rows tested:
                length of slice_df tested
            metric:
                the R-Squared metric
            passed:
                TRUE if R-Squared metric > threshold

        """
        return self._test_regression_score(r2_score, df, model, target, threshold, r2=True)

    def _test_diff_prediction(self, test_fn, model, df, target, threshold=0.1, filter_1=None, filter_2=None):
        self.do_save_results = False
        df_1 = df.loc[filter_1] if filter_1 is not None else df
        df_2 = df.loc[filter_2] if filter_2 is not None else df
        metric_1 = test_fn(df_1, model, target).metric
        metric_2 = test_fn(df_2, model, target).metric
        self.do_save_results = True
        change_pct = abs(metric_1 - metric_2) / metric_1

        return self.save_results(
            SingleTestResult(
                element_count=len(df),
                metric=change_pct,
                passed=change_pct < threshold
            ))

    def test_diff_accuracy(self, df, model, target, threshold=0.1, filter_1=None, filter_2=None):
        """

        Test if the absolute percentage change of model Accuracy between two samples is lower than a threshold

        Example : The test is passed when the Accuracy for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Accuracy for males is 0.8 (filter_1) and the Accuracy  for
        females is 0.6 (filter_2) then the absolute percentage Accuracy change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for Accuracy Score difference
            filter_1(int64Index):
                index of the slice of the dataset
            filter_2(int64Index):
                index of the slice of the dataset

        Returns:
            total rows tested:
                length of test dataset
            metric:
                the Accuracy difference  metric
            passed:
                TRUE if Accuracy difference < threshold

        """
        return self._test_diff_prediction(self.test_accuracy, model, df, target, threshold, filter_1, filter_2)

    def test_diff_f1(self, df, model, target, threshold=0.1, filter_1=None, filter_2=None):
        """
        Test if the absolute percentage change in model F1 Score between two samples is lower than a threshold

        Example : The test is passed when the F1 Score for females has a difference lower than 10% from the
        F1 Score for males. For example, if the F1 Score for males is 0.8 (filter_1) and the F1 Score  for
        females is 0.6 (filter_2) then the absolute percentage F1 Score  change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for F1 Score difference
            filter_1(int64Index):
                index of the slice of the dataset
            filter_2(int64Index):
                index of the slice of the dataset

        Returns:
            total rows tested:
                length of test dataset
            metric:
                the F1 Score difference  metric
            passed:
                TRUE if F1 Score difference < threshold

        """
        return self._test_diff_prediction(self.test_f1, model, df, target, threshold, filter_1, filter_2)

    def test_diff_precision(self, df, model, target, threshold=0.1, filter_1=None, filter_2=None):
        """
        Test if the absolute percentage change of model Precision between two samples is lower than a threshold

        Example : The test is passed when the Precision for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Precision for males is 0.8 (filter_1) and the Precision  for
        females is 0.6 (filter_2) then the absolute percentage Precision change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for Precision difference
            filter_1(int64Index):
                index of the slice of the dataset
            filter_2(int64Index):
                index of the slice of the dataset

        Returns:
            total rows tested:
                length of test dataset
            metric:
                the Precision difference  metric
            passed:
                TRUE if Precision difference < threshold
        """
        return self._test_diff_prediction(self.test_precision, model, df, target, threshold, filter_1, filter_2)

    def test_diff_recall(self, df, model, target, threshold=0.1, filter_1=None, filter_2=None):
        """
        Test if the absolute percentage change of model Recall between two samples is lower than a threshold

        Example : The test is passed when the Recall for females has a difference lower than 10% from the
        Accuracy for males. For example, if the Recall for males is 0.8 (df_filter_1) and the Recall  for
        females is 0.6 (filter_2) then the absolute percentage Recall change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for Recall difference
            filter_1(int64Index):
                index of the slice of the dataset
            filter_2(int64Index):
                index of the slice of the dataset

        Returns:
            total rows tested:
                length of test dataset
            metric:
                the Recall difference  metric
            passed:
                TRUE if Recall difference < threshold
        """
        return self._test_diff_prediction(self.test_recall, model, df, target, threshold, filter_1, filter_2)

    def _test_diff_traintest(self, test_fn, model, train_df, test_df, target, threshold=0.1):
        self.do_save_results = False
        metric_1 = test_fn(train_df, model, target).metric
        metric_2 = test_fn(test_df, model, target).metric
        self.do_save_results = True
        change_pct = abs(metric_1 - metric_2) / metric_1

        return self.save_results(
            SingleTestResult(
                metric=change_pct,
                passed=change_pct < threshold
            ))

    def test_diff_traintest_f1(self, train_df, test_df, model, target, threshold=0.1):
        """
        Test if the absolute percentage change in model F1 Score between train and test data
        is lower than a threshold

        Example : The test is passed when the F1 Score for train dataset has a difference lower than 10% from the
        F1 Score for test dataset. For example, if the F1 Score for train dataset is 0.8 (train_df) and the F1 Score  for
        test dataset is 0.6 (test_df) then the absolute percentage F1 Score  change is 0.2 / 0.8 = 0.25
        and the test will fail.

        Args:
            train_df(pandas.core.frame.DataFrame):
                train dataset 
            test_df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for F1 Score difference


        Returns:
            metric:
                the F1 Score difference  metric
            passed:
                TRUE if F1 Score difference < threshold

        """
        return self._test_diff_traintest(self.test_f1, model, train_df, test_df, target, threshold)

    def test_diff_traintest_accuracy(self, train_df, test_df, model, target, threshold=0.1):
        """
        Test if the absolute percentage change in model Accuracy between train and test data
        is lower than a threshold

        Example : The test is passed when the Accuracy for train dataset has a difference lower than 10% from the
        Accuracy for test dataset. For example, if the Accuracy for train dataset is 0.8 (train_df) and the Accuracy  for
        test dataset is 0.6 (test_df) then the absolute percentage Accuracy  change is 0.2 / 0.8 = 0.25
        and the test will fail.

        Args:
            train_df(pandas.core.frame.DataFrame):
                train dataset 
            test_df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for Accuracy difference


        Returns:
            metric:
                the Accuracy difference  metric
            passed:
                TRUE if Accuracy difference < threshold

        """
        return self._test_diff_traintest(self.test_accuracy, model, train_df, test_df, target, threshold)

    def test_diff_rmse(self, df, model, target, threshold=0.1, filter_1=None, filter_2=None):
        """
        Test if the absolute percentage change of model RMSE between two samples is lower than a threshold

        Example : The test is passed when the RMSE for females has a difference lower than 10% from the
        RMSE for males. For example, if the RMSE for males is 0.8 (filter_1) and the RMSE  for
        females is 0.6 (filter_2) then the absolute percentage RMSE change is 0.2 / 0.8 = 0.25
        and the test will fail

        Args:
            df(pandas.core.frame.DataFrame):
                test dataset 
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for RMSE difference
            filter_1(int64Index):
                index of the slice of the dataset
            filter_2(int64Index):
                index of the slice of the dataset

        Returns:
            total rows tested:
                length of test dataset
            metric:
                the RMSE difference  metric
            passed:
                TRUE if RMSE difference < threshold
        """
        return self._test_diff_prediction(self.test_rmse, model, df, target, threshold, filter_1, filter_2)

    def test_diff_traintest_rmse(self, train_slice, test_slice, model, target, threshold=0.1):
        """
        Test if the absolute percentage change in model RMSE between train and test data
        is lower than a threshold

        Example : The test is passed when the RMSE for train dataset has a difference lower than 10% from the
        RMSE for test dataset. For example, if the RMSE for train dataset is 0.8 (train_df) and the RMSE  for
        test dataset is 0.6 (test_df) then the absolute percentage RMSE  change is 0.2 / 0.8 = 0.25
        and the test will fail.

        Args:
            train_slice(pandas.core.frame.DataFrame):
                slice of train dataset
            test_slice(pandas.core.frame.DataFrame):
                slice of test dataset
            model(ModelInspector):
                uploaded model
            target(str):
                target column name
            threshold(int):
                threshold value for RMSE difference

        Returns:
            metric:
                the RMSE difference  metric
            passed:
                TRUE if RMSE difference < threshold

        """
        return self._test_diff_traintest(self.test_rmse, model, train_slice, test_slice, target, threshold)