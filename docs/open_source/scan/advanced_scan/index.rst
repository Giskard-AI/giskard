Advanced scan usage
===================

It is possible to customize the configuration of the scan by passing specific
configuration at runtime to the `scan` method.

The following examples show the different options available.


Limiting to a specific group of detectors
-----------------------------------------

If you want to run only a specific detector (or a group of detectors), you can
use the `only` argument. This argument accepts either a tag or a list of tags::

    import giskard as gsk

    report = gsk.scan(my_model, my_dataset, only="robustness")

or with multiple tags::

    report = gsk.scan(my_model, my_dataset, only=["robustness", "performance"])


Limiting to a selection of model features
-----------------------------------------

If your model has a great number of features and you want to limit the scan to
a specific subset, you can use the `features` argument::

    import giskard as gsk

    report = gsk.scan(my_model, my_dataset, features=["feature_1", "feature_2"])

This will produce scan results only for the features `feature_1` and `feature_2`.


Advanced detector configuration
-------------------------------

If you want to customize the configuration of a specific detector, you can use
the `params` argument, which accepts a dictionary where the key is the
identifier of the detector and the value is a dictionary of config options that
will be passed to the detector upon initialization::

    import giskard as gsk

    params = {
        "performance_bias": dict(threshold=0.04, metrics=["accuracy", "f1"]),
        "ethical_bias": dict(output_sensitivity=0.5),
    }

    report = gsk.scan(my_model, my_dataset, params=params)

You can check in the reference documentation of each detector which options are
available for customization.


How to make the scan faster
---------------------------

If you are dealing with a big dataset, the scan may take a long time to
analyze all the vulnerabilities. If this is the case, you may choose to limit
the scan to a subset of the features and detectors that are the most relevant
to your use case (see above for detailed instructions)::

    report = gsk.scan(my_model,
        my_dataset,
        only=["robustness", "performance"],
        features=["feature_1", "feature_2"],
    )

Moreover, certain detectors do a full scan of the dataset, which can be very
slow. If this is the case, we recommend use the following configuration which
so that these detectors will only scan a random sample of your dataset::

    params = {
        "performance_bias": dict(max_dataset_size=100_000),
        "overconfidence": dict(max_dataset_size=100_000),
        "underconfidence": dict(max_dataset_size=100_000),
    }

    report = gsk.scan(my_model, my_dataset, params=params)

This will limit the scan to 100,000 samples of your dataset. You can adjust this
number to your needs.

Note: for classification models, we will make sure that the sample is balanced
between the different classes via stratified sampling.


How to specify the minimum slice size
-------------------------------------

By default, the minimum slice size is set to the maximum between 1% of the
dataset size and 30 samples. You may want to customize this value, for example,
when you expect to have a low number of problematic samples in your dataset.
In that case, simply pass the `min_slice_size` parameter to the metrics you are
interested in, either as an integer to set the minimum slice size to a fixed
value or as a float to set it as a percentage of the dataset size::

    import giskard as gsk

    params = {
        "performance_bias": dict(min_slice_size=50),
        "spurious_correlation": dict(min_slice_size=0.01),
    }

    report = gsk.scan(my_model, my_dataset, params=params)


How to add a custom metric
---------------------------

If you want to add a custom metric to the scan, you can do so by creating a
class that extends the `giskard.scanner.performance.metrics.PerformanceMetric`
class and implementing the `__call__` method. This method should return an
instance of `giskard.scanner.performance.metrics.MetricResult`::

    from giskard.scanner.performance.metrics import PerformanceMetric, MetricResult

    class MyCustomMetric(PerformanceMetric):
        def __call__(self, model, dataset):
            # your custom logic here
            return MetricResult(
                name="my_custom_metric",
                value=0.42,
                affected_counts=100,
                binary_counts=[25, 75],
            )

You can also directly extend `giskard.scanner.performance.metrics.ClassificationPerformanceMetric`
for classification models or `giskard.scanner.performance.metrics.RegressionPerformanceMetric`
for regression models, implementing the method `_calculate_metric`.
The following is an example of a custom classification metric that calculates the
frequency-weighted accuracy::

    from giskard.scanner.performance.metrics import (
        ClassificationPerformanceMetric,
        MetricResult
    )
    import numpy as np
    import sklearn.metrics

    class FrequencyWeightedAccuracy(ClassificationPerformanceMetric):
        name = "Frequency-Weighted Accuracy"
        greater_is_better = True
        has_binary_counts = False

        def _calculate_metric(
            self,
            y_true: np.ndarray,
            y_pred: np.ndarray,
            model: BaseModel
        ):
            labels = model.meta.classification_labels
            label_to_id = {label: i for i, label in enumerate(labels)}
            y_true_ids = np.array([label_to_id[label] for label in y_true])
            class_counts = np.bincount(y_true_ids, minlength=len(labels))
            total_count = np.sum(class_counts)

            weighted_sum = 0

            for i in range(len(labels)):
                class_mask = y_true_ids == i
                if not np.any(class_mask):
                    continue
                label_acc = sklearn.metrics.accuracy_score(y_true[class_mask], y_pred[class_mask])
                weighted_sum += (class_counts[i] / total_count) * label_acc
            return weighted_sum

Then, you can instantiate the metric and pass it to the `scan` method::

    import giskard as gsk

    frequency_weighted_accuracy = FrequencyWeightedAccuracy()

    params = {
        "performance_bias": {"metrics": ["accuracy", frequency_weighted_accuracy]}
    }
    report = gsk.scan(my_model, my_dataset, params=params)