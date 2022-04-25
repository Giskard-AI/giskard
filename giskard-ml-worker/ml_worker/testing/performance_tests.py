from ai_inspector import ModelInspector
from sklearn.metrics import accuracy_score, recall_score
from sklearn.metrics import roc_auc_score, f1_score, precision_score, mean_squared_error, \
    mean_absolute_error, r2_score

from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.core.ml import run_predict
from ml_worker.testing.abstract_test_collection import AbstractTestCollection


class PerformanceTests(AbstractTestCollection):
    def test_auc(self, df, model: ModelInspector, target, classification_labels, mask=None, failed_threshold=1):
        """
        Compute Area Under the Receiver Operating Characteristic Curve (ROC AUC)
        """

        def _calculate_auc(is_binary_classification, prediction, true_value):
            if is_binary_classification:
                return roc_auc_score(true_value, prediction)
            else:
                return roc_auc_score(true_value, prediction, average='macro', multi_class='ovr')

        if mask is not None:
            df = df.loc[mask]

        metric = _calculate_auc(
            len(classification_labels) == 2,
            run_predict(df, model).raw_prediction,
            df[target]
        )

        return self.save_results(
            SingleTestResult(
                element_count=len(df),
                props={"metric": str(metric)},
                passed=metric >= failed_threshold
            ))

    def _test_classification_score(self, score_fn, df, model: ModelInspector, target, classification_labels, mask=None,
                                   failed_threshold=1):
        if mask is not None:
            df = df.loc[mask]

        is_binary_classification = len(classification_labels) == 2
        prediction = run_predict(df, model).raw_prediction

        if is_binary_classification:
            metric = score_fn(df[target], prediction)
        else:
            metric = score_fn(df[target], prediction, average='macro', multi_class='ovr')

        return self.save_results(
            SingleTestResult(
                element_count=len(df),
                props={"metric": str(metric)},
                passed=metric >= failed_threshold
            ))

    def _test_regression_score(self, score_fn, df, model: ModelInspector, target, mask=None, failed_threshold=1,
                               negative=False):
        if mask is not None:
            df = df.loc[mask]

        metric = (-1 if negative else 1) * score_fn(
            run_predict(df, model).raw_prediction,
            df[target]
        )

        return self.save_results(
            SingleTestResult(
                element_count=len(df),
                props={"metric": str(metric)},
                passed=metric >= failed_threshold
            ))

    def test_f1(self, df, model: ModelInspector, target, classification_labels, mask=None, failed_threshold=1):
        """
        Compute the F1 score
        """

        return self._test_classification_score(f1_score,
                                               df, model, target, classification_labels, mask, failed_threshold)

    def test_accuracy(self, df, model: ModelInspector, target, classification_labels, mask=None, failed_threshold=1):
        """
        Compute Accuracy
        """

        return self._test_classification_score(accuracy_score,
                                               df, model, target, classification_labels, mask, failed_threshold)

    def test_precision(self, df, model: ModelInspector, target, classification_labels, mask=None, failed_threshold=1):
        """
        Compute Precision
        """

        return self._test_classification_score(precision_score,
                                               df, model, target, classification_labels, mask, failed_threshold)

    def test_recall(self, df, model: ModelInspector, target, classification_labels, mask=None, failed_threshold=1):
        """
        Compute Recall
        """

        return self._test_classification_score(recall_score,
                                               df, model, target, classification_labels, mask, failed_threshold)

    def test_neg_rmse(self, df, model: ModelInspector, target, mask=None, failed_threshold=1):
        return self._test_regression_score(mean_squared_error, df, model, target, mask, failed_threshold, negative=True)

    def test_neg_mae(self, df, model: ModelInspector, target, mask=None, failed_threshold=1):
        return self._test_regression_score(mean_absolute_error, df, model, target, mask, failed_threshold,
                                           negative=True)

    def test_r2(self, df, model: ModelInspector, target, mask=None, failed_threshold=1):
        return self._test_regression_score(r2_score, df, model, target, mask, failed_threshold)
