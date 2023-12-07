Advanced scan usage
===================

It is possible to customize the configuration of the scan by passing specific
configuration at runtime to the `scan` method.

The following examples show the different options available.


Limiting to a specific group of detectors
-----------------------------------------

If you want to run only a specific detector (or a group of detectors), you can
use the `only` argument. This argument accepts either a tag or a list of tags::

    import giksard as gsk

    report = gsk.scan(my_model, my_dataset, only="robustness")

or with multiple tags::

    report = gsk.scan(my_model, my_dataset, only=["robustness", "performance"])


Limiting to a selection of model features
-----------------------------------------

If your model has a great number of features and you want to limit the scan to
a specific subset, you can use the `features` argument::

    import giksard as gsk

    report = gsk.scan(my_model, my_dataset, features=["feature_1", "feature_2"])

This will produce scan results only for the features `feature_1` and `feature_2`.


Advanced detector configuration
-------------------------------

If you want to customize the configuration of a specific detector, you can use
the `params` argument, which accepts a dictionary where the key is the
identifier of the detector and the value is a dictionary of config options that
will be passed to the detector upon initialization::

    import giksard as gsk

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