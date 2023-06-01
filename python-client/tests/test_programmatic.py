from giskard.ml_worker.testing.tests.performance import *

from giskard.ml_worker.core.dataset import Dataset
from giskard.ml_worker.core.suite import Suite
from test_performance import *


def test_dataset_size(ds: Dataset, threshold):
    print("Running test_dataset_size")
    return len(ds.df) > threshold


def test_a_greater_b(a: int, b: int):
    print("Running a_greater_b")
    return a > b


def test_one(german_credit_data, german_credit_model):
    ds = german_credit_data

    # # 2 tests with all inputs being "exposed" and shared
    # results = Suite() \
    #     .add_test(test_auc) \
    #     .add_test(test_f1) \
    #     .add_test(test_a_greater_b) \
    #     .run(actual_slice=german_credit_data,
    #          model=german_credit_model,
    #          threshold=0.8,
    #          a=1,
    #          b=2)
    #
    # # both tests have "fixed" thresholds, the rest of the inputs are exposed
    results = Suite() \
        .add_test(test_auc, threshold=0.9) \
        .add_test(test_f1, threshold=0.9) \
        .run(actual_slice=german_credit_data, model=german_credit_model)
    #
    # # both tests have "fixed" thresholds, the rest of the inputs are exposed
    first_half = german_credit_data.slice(lambda df: df.head(len(df) // 2))
    last_half = german_credit_data.slice(lambda df: df.tail(len(df) // 2))
    #
    # shared_input = SuiteInput("dataset", GiskardDataset)
    #
    # results = Suite() \
    #     .add_test(test_auc, actual_slice=shared_input, threshold=0.9) \
    #     .add_test(test_f1, actual_slice=shared_input, threshold=0.9) \
    #     .add_test(test_diff_f1, threshold=0.9) \
    #     .run(model=german_credit_model,
    #          dataset=german_credit_data,
    #          actual_slice=first_half,
    #          reference_slice=last_half
    #          )
    #
    # Suite(name="My perf tests") \
    #     .add_test(test_auc) \
    #     .add_test(test_f1) \
    #     .add_test(test_a_greater_b) \
    #     .save(client, project="project-key")

    # Suite() \
    #     .add_test(test_auc, actual_slice=ds, model=my_model) \
    #     .add_test(test_f1, actual_slice=ds, model=my_model) \
    #     .add_test(test_accuracy, actual_slice=ds, model=german_credit_model) \
    #     .run(my_model=german_credit_model)

    results = Suite() \
        .add_test(test_diff_f1, threshold=0.9, actual_slice=first_half) \
        .save(None, None) \
        .run(model=german_credit_model, reference_slice=last_half)
