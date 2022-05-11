from ai_inspector import ModelInspector
from sklearn.metrics import accuracy_score, recall_score
from sklearn.metrics import roc_auc_score, f1_score, precision_score, mean_squared_error, \
    mean_absolute_error, r2_score

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.ml import run_predict
from ml_worker.testing.abstract_test_collection import AbstractTestCollection


class PerformanceTests(AbstractTestCollection):
    def test_auc(self, df_slice, model: ModelInspector, target, threshold=1):
        """
        Compute Area Under the Receiver Operating Characteristic Curve (ROC AUC)

        """
        def _calculate_auc(is_binary_classification, prediction, true_value):
            if is_binary_classification:
                return roc_auc_score(true_value, prediction)
            else:
                return roc_auc_score(true_value, prediction, average='macro', multi_class='ovr')

        metric = _calculate_auc(
            len(model.classification_labels) == 2,
            run_predict(df_slice, model).raw_prediction,
            df_slice[target]
        )

        return self.save_results(
            SingleTestResult(
                element_count=len(df_slice),
                metric=metric,
                passed=metric >= threshold
            ))

    def _test_classification_score(self, score_fn, df, model: ModelInspector, target, threshold=1):
        is_binary_classification = len(model.classification_labels) == 2
        prediction = run_predict(df, model).raw_prediction
        labels_mapping = {model.classification_labels[i]: i for i in range(len(model.classification_labels))}
        if is_binary_classification:
            metric = score_fn(df[target].map(labels_mapping), prediction)
        else:
            metric = score_fn(df[target].map(labels_mapping), prediction, average='macro', multi_class='ovr')

        return self.save_results(
            SingleTestResult(
                element_count=len(df),
                metric=metric,
                passed=metric >= threshold
            ))

    def _test_regression_score(self, score_fn, df, model: ModelInspector, target, threshold=1, negative=False):
        metric = (-1 if negative else 1) * score_fn(
            run_predict(df, model).raw_prediction,
            df[target]
        )

        return self.save_results(
            SingleTestResult(
                element_count=len(df),
                metric=metric,
                passed=metric >= threshold
            ))

    def test_f1(self, df, model: ModelInspector, target, threshold=1):
        """
        Compute the F1 score
        """

        return self._test_classification_score(f1_score,
                                               df, model, target, threshold)

    def test_accuracy(self, df, model: ModelInspector, target, threshold=1):
        """
        Compute Accuracy
        """

        return self._test_classification_score(accuracy_score,
                                               df, model, target, threshold)

    def test_precision(self, df, model: ModelInspector, target, threshold=1):
        """
        Compute Precision
        """

        return self._test_classification_score(precision_score,
                                               df, model, target, threshold)

    def test_recall(self, df, model: ModelInspector, target, threshold=1):
        """
        Compute Recall
        """

        return self._test_classification_score(recall_score,
                                               df, model, target, threshold)

    def test_neg_rmse(self, df, model: ModelInspector, target, threshold=1):
        return self._test_regression_score(mean_squared_error, df, model, target, threshold, negative=True)

    def test_neg_mae(self, df, model: ModelInspector, target, threshold=1):
        return self._test_regression_score(mean_absolute_error, df, model, target, threshold,
                                           negative=True)

    def test_r2(self, df, model: ModelInspector, target, threshold=1):
        return self._test_regression_score(r2_score, df, model, target, threshold)

    def _test_diff_classification(self, test_fn, model, df, target, threshold=0.1, filter_1=None, filter_2=None):
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
        return self._test_diff_classification(self.test_accuracy, model, df, target, threshold, filter_1, filter_2)

    def test_diff_f1(self, df, model, target, threshold=0.1, filter_1=None, filter_2=None):
        return self._test_diff_classification(self.test_f1, model, df, target, threshold, filter_1, filter_2)

    def test_diff_precision(self, df, model, target, threshold=0.1, filter_1=None, filter_2=None):
        return self._test_diff_classification(self.test_precision, model, df, target, threshold, filter_1, filter_2)

    def test_diff_recall(self, df, model, target, threshold=0.1, filter_1=None, filter_2=None):
        return self._test_diff_classification(self.test_recall, model, df, target, threshold, filter_1, filter_2)
