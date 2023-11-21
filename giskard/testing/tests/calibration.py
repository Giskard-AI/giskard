from typing import Optional

import numpy as np
import pandas as pd

from . import debug_description_prefix
from ...datasets.base import Dataset
from ...ml_worker.testing.registry.decorators import test
from ...ml_worker.testing.registry.slicing_function import SlicingFunction
from ...ml_worker.testing.test_result import TestResult
from ...models.base import BaseModel


def _calculate_overconfidence_score(model: BaseModel, dataset: Dataset) -> pd.Series:
    true_target = dataset.df.loc[:, dataset.target].values
    pred = model.predict(dataset)
    label2id = {label: n for n, label in enumerate(model.meta.classification_labels)}

    # Empirical cost associated to overconfidence, i.e. the difference between
    # the probability assigned to the predicted label and the correct label.
    p_max = pred.probabilities
    p_true_label = np.array([pred.raw[n, label2id[label]] for n, label in enumerate(true_target)])

    overconfidence_score = p_max - p_true_label
    return pd.Series(overconfidence_score, index=dataset.df.index)


def _default_overconfidence_threshold(model: BaseModel) -> float:
    n = len(model.meta.classification_labels)
    return 1 / (3e-1 * (n - 2) + 2 - 1e-3 * (n - 2) ** 2)


@test(
    name="Overconfidence Rate",
    tags=["classification"],
    debug_description=debug_description_prefix + "that are <b>predicted with overconfidence</b>.",
)
def test_overconfidence_rate(
    model: BaseModel,
    dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: Optional[float] = 0.10,
    p_threshold: Optional[float] = None,
):
    """Tests that the rate of overconfident predictions is below a threshold.

    Overconfident predictions are defined as predictions where the model
    assigned a large probability to the wrong label. We quantify this as the
    difference between the largest probability assigned to a label and the
    probability assigned to the correct label (this will be 0 if the model
    made the correct prediction). If this is larger than a threshold
    (`p_threshold`, typically determined automatically depending on the number
    of classes), then the prediction is considered overconfident.
    We then calculate the rate of overconfident predictions as the number of
    overconfident samples divided by the total number of wrongly predicted
    samples, and check that it is below a user-specified threshold.

    Arguments:
        model(BaseModel): The model to test.
        dataset(Dataset): The dataset to test the model on.
        slicing_function(SlicingFunction, optional): An optional slicing
            function used to slice the dataset before testing. If not provided,
            the whole dataset will be considered in calculating the
            overconfidence rate.
        threshold(float, optional): The threshold for overconfident prediction
            rate, i.e. the max ratio of overconfident samples over number of
            wrongly predicted samples. Default is 0.10 (10%).
        p_threshold(float, optional): The threshold for the difference between
            the probability assigned to the wrong label and the correct label
            over which a prediction is considered overconfident. If not
            provided, it will be determined automatically depending on the
            number of classes.
    """
    if not model.is_classification:
        raise ValueError("This test is only applicable to classification models.")

    if slicing_function is not None:
        dataset = dataset.slice(slicing_function)

    overconfidence_score = _calculate_overconfidence_score(model, dataset)

    if p_threshold is None:
        p_threshold = _default_overconfidence_threshold(model)

    overconfidence_mask = overconfidence_score[overconfidence_score > 0].dropna() > p_threshold
    rate = (overconfidence_mask).mean()
    passed = rate < threshold

    # --- debug ---
    output_ds = list()
    if not passed:
        output_ds.append(
            dataset.slice(lambda df: df.loc[overconfidence_mask[overconfidence_mask].index], row_level=False)
        )
    # ---

    return TestResult(passed=bool(passed), metric=rate, output_ds=output_ds)


def _calculate_underconfidence_score(model: BaseModel, dataset: Dataset) -> pd.Series:
    # Empirical cost associated to underconfidence: difference between the two
    # most probable classes.
    ps = model.predict(dataset).raw

    # Relative difference
    ps_2 = -np.partition(-ps, 1, axis=-1)[:, :2]
    score_values = ps_2.min(axis=-1) / ps_2.max(axis=-1)

    return pd.Series(score_values, index=dataset.df.index)


@test(
    name="Underconfidence Rate",
    tags=["classification"],
    debug_description=debug_description_prefix + "that are <b>predicted with underconfidence</b>.",
)
def test_underconfidence_rate(
    model: BaseModel,
    dataset: Dataset,
    slicing_function: Optional[SlicingFunction] = None,
    threshold: Optional[float] = 0.10,
    p_threshold: float = 0.90,
):
    """Tests that the rate of underconfident predictions is below a threshold.

    Underconfident predictions are defined as predictions where the two most
    probable labels have very similar probabilities. In this case, slight
    changes can make the model flip its predicted label. By default, we mark a
    prediction as underconfident when the second most probable prediction has a
    probability which is only less than 10% smaller than the predicted label
    (`p_threshold=0.90`).
    We then calculate the rate of underconfident predictions as the number of
    underconfident samples divided by the total number of samples, and check
    that it is below the user-specified threshold.


    Arguments:
        model(BaseModel): The model to test.
        dataset(Dataset): The dataset to test the model on.
        slicing_function(SlicingFunction, optional): An optional slicing
            function used to slice the dataset before testing. If not provided,
            the whole dataset will be considered in calculating the
            underconfidence rate.
        threshold(float, optional): The threshold for underconfident prediction
            rate. Default is 0.10 (10%).
        p_threshold(float, optional): The threshold for the relative value of
            the second most-probable prediction and the max probability. If
            greater that this value, the prediction is considered
            underconfident. Default is 0.90, i.e. when the second most probable
            prediction is 90% or more with respect to the highest probability,
            the sample prediction is considered underconfident.
    """
    if not model.is_classification:
        raise ValueError("This test is only applicable to classification models.")

    if slicing_function is not None:
        dataset = dataset.slice(slicing_function)

    underconfidence_score = _calculate_underconfidence_score(model, dataset)

    underconfidence_mask = underconfidence_score.dropna() > p_threshold
    rate = (underconfidence_mask).mean()
    passed = rate < threshold

    # --- debug ---
    output_ds = list()
    if not passed:
        output_ds.append(
            dataset.slice(lambda df: df.loc[underconfidence_mask[underconfidence_mask].index], row_level=False)
        )

    # ---

    return TestResult(passed=bool(passed), metric=rate, output_ds=output_ds)
