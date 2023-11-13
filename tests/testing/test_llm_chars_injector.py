from unittest.mock import Mock, patch, sentinel

import numpy as np
import pandas as pd
import pytest

from giskard.datasets import Dataset
from giskard.models.base import BaseModel
from giskard.models.base.model_prediction import ModelPredictionResults
from giskard.testing.tests.llm import LLMCharInjector
from giskard.testing.tests.llm.injections import CharInjectionResult, test_llm_char_injection


@pytest.mark.memory_expensive
def test_single_injection():
    dataset = Dataset(pd.DataFrame({"feature_1": ["one", "two", "three"], "feature_2": [1, 2, 3]}))
    reference_predictions = ["this is ok", "this is ok", "this is not ok"]

    model = Mock()
    model.meta.feature_names = ["feature_1", "feature_2"]
    model.predict.side_effect = [
        ModelPredictionResults(prediction=["This is ok!"]),
        ModelPredictionResults(prediction=["Yes, this is good."]),
        RuntimeError(),
        ModelPredictionResults(prediction=["And now for something completely different!!! The Larch!"]),
    ] * 3

    injector = LLMCharInjector(max_repetitions=23, threshold=0.1412, output_sensitivity=0.15)
    result = injector.run_single_injection(model, dataset, reference_predictions, char="\r", feature="feature_1")
    injector._cleanup()

    assert isinstance(result, CharInjectionResult)
    assert result.fail_rate == pytest.approx(1 / 3)
    assert result.vulnerable
    assert result.char == "\r"
    assert result.vulnerable_mask.tolist() == [False, False, True]

    # First sample has suffix of length 23
    assert result.perturbed_dataset.df.iloc[0]["feature_1"] == "one" + "\r" * 23

    # Third example got runtime error, and halved the number of repetitions to 11
    assert result.perturbed_dataset.df.iloc[2]["feature_1"] == "three" + "\r" * 11

    # Increase sensitivity
    injector = LLMCharInjector(max_repetitions=23, threshold=0.1412, output_sensitivity=0.2)
    result = injector.run_single_injection(model, dataset, reference_predictions, char="\r", feature="feature_1")
    injector._cleanup()
    assert not result.vulnerable
    assert result.fail_rate == pytest.approx(0.0)

    # Increase threshold
    injector = LLMCharInjector(max_repetitions=23, threshold=0.4, output_sensitivity=0.15)
    result = injector.run_single_injection(model, dataset, reference_predictions, char="\r", feature="feature_1")
    injector._cleanup()
    assert not result.vulnerable
    assert result.fail_rate == pytest.approx(1 / 3)


@pytest.mark.memory_expensive
def test_single_injection_with_nonstring_types():
    dataset = Dataset(pd.DataFrame({"feature_1": ["one", "two"], "feature_2": [1, 2]}))
    reference_predictions = ["this is ok", "this is ok!"]

    model = Mock()
    model.meta.feature_names = ["feature_1", "feature_2"]
    model.predict.side_effect = [
        ModelPredictionResults(prediction=[{"answer": "This is ok!"}]),
        RuntimeError(),
        ModelPredictionResults(prediction=[{"answer": "And now for something completely different!!! The Larch!"}]),
    ]

    injector = LLMCharInjector(max_repetitions=23, threshold=0.1412, output_sensitivity=0.15)
    result = injector.run_single_injection(model, dataset, reference_predictions, char="@", feature="feature_2")

    assert isinstance(result, CharInjectionResult)
    assert result.fail_rate == pytest.approx(1 / 2)
    assert result.vulnerable
    assert result.char == "@"
    assert result.vulnerable_mask.tolist() == [False, True]

    assert result.perturbed_dataset.df.iloc[0]["feature_2"] == "1" + "@" * 23


def test_runs_on_multiple_features_and_chars():
    dataset = Dataset(pd.DataFrame({"feature_1": ["one", "two"], "feature_2": [1, 2], "feature_3": [True, True]}))

    model = Mock()
    model.meta.feature_names = ["feature_1", "feature_2", "feature_3"]

    injector = LLMCharInjector(chars=["char1", "char2"])
    run_mock = Mock()
    run_mock.return_value = sentinel.injection_result
    injector.run_single_injection = run_mock

    results = list(injector.run(model, dataset))
    assert all(r is sentinel.injection_result for r in results)
    assert run_mock.call_count == 6

    assert run_mock.call_args_list[0].args[3] == "char1"
    assert run_mock.call_args_list[1].args[3] == "char2"

    assert run_mock.call_args_list[0].args[4] == "feature_1"
    assert run_mock.call_args_list[1].args[4] == "feature_1"
    assert run_mock.call_args_list[2].args[4] == "feature_2"

    # Check that features can be limited
    injector = LLMCharInjector(chars=["char1", "char2"])
    run_mock = Mock()
    run_mock.return_value = sentinel.injection_result
    injector.run_single_injection = run_mock

    results = list(injector.run(model, dataset, features=["feature_1"]))
    assert all(r is sentinel.injection_result for r in results)
    assert run_mock.call_count == 2

    assert run_mock.call_args_list[0].args[3] == "char1"
    assert run_mock.call_args_list[1].args[3] == "char2"


@patch("giskard.testing.tests.llm.injections.LLMCharInjector")
def test_char_injector_test_fails(Injector):
    original_dataset = Dataset(
        pd.DataFrame({"my_feature": ["original 1", "original 2"]}),
        validation=False,
    )
    perturbed_dataset = Dataset(
        pd.DataFrame({"my_feature": ["perturbed 1", "perturbed 2"]}),
        validation=False,
    )
    reference_predictions = ["Hello", "World"]
    predictions = ["Hello", "BOOM!"]

    results = [
        CharInjectionResult(
            char="a",
            feature="my_feature",
            fail_rate=0.81,
            vulnerable=True,
            vulnerable_mask=np.array([False, True]),
            original_dataset=original_dataset,
            perturbed_dataset=perturbed_dataset,
            predictions=predictions,
            original_predictions=reference_predictions,
        ),
        CharInjectionResult(
            char="a",
            feature="other_feature",
            fail_rate=0.01,
            vulnerable=False,
            vulnerable_mask=np.array([False, False]),
            original_dataset=original_dataset,
            perturbed_dataset=perturbed_dataset,
            predictions=predictions,
            original_predictions=reference_predictions,
        ),
        CharInjectionResult(
            char="b",
            feature="my_feature",
            fail_rate=0.89,
            vulnerable=True,
            vulnerable_mask=np.array([False, True]),
            original_dataset=original_dataset,
            perturbed_dataset=perturbed_dataset,
            predictions=predictions,
            original_predictions=reference_predictions,
        ),
        CharInjectionResult(
            char="b",
            feature="other_feature",
            fail_rate=None,
            vulnerable=None,
            vulnerable_mask=None,
            original_dataset=None,
            perturbed_dataset=None,
            predictions=None,
            original_predictions=None,
            errors=["Error 1", "Error 2"],
        ),
    ]

    Injector.return_value.run.return_value = results

    my_test = test_llm_char_injection()
    test_result = my_test(Mock(BaseModel), original_dataset).execute()

    assert test_result.passed is False
    assert test_result.is_error is False
    assert test_result.metric == pytest.approx(0.85)
    assert test_result.messages == ["Error 1", "Error 2"]


@patch("giskard.testing.tests.llm.injections.LLMCharInjector")
def test_char_injector_test_succeeds(Injector):
    original_dataset = Dataset(
        pd.DataFrame({"my_feature": ["original 1", "original 2"]}),
        validation=False,
    )
    perturbed_dataset = Dataset(
        pd.DataFrame({"my_feature": ["perturbed 1", "perturbed 2"]}),
        validation=False,
    )
    reference_predictions = ["Hello", "World"]
    predictions = ["Hello", "BOOM!"]

    results = [
        CharInjectionResult(
            char="a",
            feature="other_feature",
            fail_rate=0.01,
            vulnerable=False,
            vulnerable_mask=np.array([False, False]),
            original_dataset=original_dataset,
            perturbed_dataset=perturbed_dataset,
            predictions=predictions,
            original_predictions=reference_predictions,
        ),
        CharInjectionResult(
            char="b",
            feature="other_feature",
            fail_rate=None,
            vulnerable=None,
            vulnerable_mask=None,
            original_dataset=None,
            perturbed_dataset=None,
            predictions=None,
            original_predictions=None,
            errors=["Error 1", "Error 2"],
        ),
    ]

    Injector.return_value.run.return_value = results

    my_test = test_llm_char_injection()
    test_result = my_test(Mock(BaseModel), original_dataset).execute()

    assert test_result.passed
    assert test_result.is_error is False
    assert test_result.messages == ["Error 1", "Error 2"]


@patch("giskard.testing.tests.llm.injections.LLMCharInjector")
def test_char_injector_test_error(Injector):
    original_dataset = Dataset(
        pd.DataFrame({"my_feature": ["original 1", "original 2"]}),
        validation=False,
    )

    results = [
        CharInjectionResult(
            char="b",
            feature="other_feature",
            fail_rate=None,
            vulnerable=None,
            vulnerable_mask=None,
            original_dataset=None,
            perturbed_dataset=None,
            predictions=None,
            original_predictions=None,
            errors=["Error 1", "Error 2"],
        ),
        CharInjectionResult(
            char="b",
            feature="other_feature",
            fail_rate=None,
            vulnerable=None,
            vulnerable_mask=None,
            original_dataset=None,
            perturbed_dataset=None,
            predictions=None,
            original_predictions=None,
            errors=["Error 3"],
        ),
    ]

    Injector.return_value.run.return_value = results

    my_test = test_llm_char_injection()
    test_result = my_test(Mock(BaseModel), original_dataset).execute()

    assert test_result.is_error
    assert test_result.messages == ["Error 1", "Error 2", "Error 3"]
