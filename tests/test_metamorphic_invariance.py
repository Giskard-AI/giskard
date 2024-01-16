import numpy as np
import pandas as pd
import pytest

import giskard.testing.tests.metamorphic as metamorphic
from giskard import Dataset, Model
from giskard.registry.transformation_function import transformation_function
from giskard.testing.utils.stat_utils import (
    equivalence_t_test,
    equivalence_wilcoxon,
    paired_t_test,
    paired_wilcoxon,
)
from giskard.testing.utils.utils import Direction


def test_metamorphic_invariance_no_change(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        return x

    results = metamorphic.test_metamorphic_invariance(
        model=german_credit_model, dataset=german_credit_test_data, transformation_function=perturbation, threshold=0.1
    ).execute()

    assert results.actual_slices_size[0] == 1000
    assert results.passed


def test_metamorphic_invariance_with_non_linear_index(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    dataset = german_credit_test_data.slice(lambda df: df.sample(100), row_level=False)

    results = metamorphic.test_metamorphic_invariance(
        model=german_credit_model, dataset=dataset, transformation_function=perturbation, threshold=0.1
    ).execute()

    assert results.passed


def _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, threshold):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_invariance(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        threshold=threshold,
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert round(results.metric, 2) == 0.97
    return results.passed


def test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model):
    assert _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, 0.5)
    assert not _test_metamorphic_invariance_male_female(german_credit_test_data, german_credit_model, 1)


def test_metamorphic_invariance_2_perturbations(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.duration_in_month = x.duration_in_month * 2
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_invariance(
        model=german_credit_model, dataset=german_credit_test_data, transformation_function=perturbation, threshold=0.1
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert round(results.metric, 2) == 0.86


def test_metamorphic_invariance_some_rows(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_invariance(
        model=german_credit_model, dataset=german_credit_test_data, transformation_function=perturbation, threshold=0.1
    ).execute()

    assert round(results.metric, 2) == 0.97


def test_metamorphic_invariance_regression(diabetes_dataset_with_target, linear_regression_diabetes):
    sex_values = list(diabetes_dataset_with_target.df.sex.unique())
    assert len(sex_values) == 2

    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = sex_values[1] if x.sex == sex_values[0] else x.sex
        return x

    results = metamorphic.test_metamorphic_invariance(
        model=linear_regression_diabetes,
        dataset=diabetes_dataset_with_target,
        transformation_function=perturbation,
        threshold=0.1,
        output_sensitivity=0.1,
    ).execute()

    assert results.actual_slices_size[0] == len(diabetes_dataset_with_target)
    assert round(results.metric, 2) == 0.11


@pytest.mark.parametrize(
    "loc_pop, scale_pop, loc_perturb, scale_perturb, direction, window_size, critical_quantile",
    [
        (0.5, 0.5, 0, 1e-2, Direction.Invariant, 0.2, 0.05),
        (0.5, 0.5, 0.1, 0.1, Direction.Increasing, float("nan"), 0.05),
        (0.5, 0.5, -0.1, 0.1, Direction.Decreasing, float("nan"), 0.05),
    ],
)
def test_metamorphic_compare_t_test(
    loc_pop, scale_pop, loc_perturb, scale_perturb, direction, window_size, critical_quantile
):
    population = np.random.normal(loc_pop, scale_pop, size=100)
    perturbation = np.random.normal(loc_perturb, scale_perturb, size=100)
    print(perturbation)

    result_inc, p_value_inc = paired_t_test(
        population, population + perturbation, alternative="less", critical_quantile=critical_quantile
    )
    result_dec, p_value_dec = paired_t_test(
        population, population + perturbation, alternative="greater", critical_quantile=critical_quantile
    )
    result_inv, p_value_inv = equivalence_t_test(
        population, population + perturbation, window_size=window_size, critical_quantile=critical_quantile
    )

    dict_mapping = {
        Direction.Invariant: (result_inv, p_value_inv),
        Direction.Decreasing: (result_dec, p_value_dec),
        Direction.Increasing: (result_inc, p_value_inc),
    }

    print(f"Direction: {direction.name} and p_value; {dict_mapping[direction][1]}")
    assert dict_mapping[direction][1] < critical_quantile


@pytest.mark.parametrize(
    "loc_pop, scale_pop, loc_perturb, scale_perturb, direction, window_size, critical_quantile",
    [
        (0.5, 0.5, 0, 1e-2, Direction.Invariant, 0.2, 0.05),
        (0.5, 0.5, 0.1, 0.1, Direction.Increasing, float("nan"), 0.05),
        (0.5, 0.5, -0.1, 0.1, Direction.Decreasing, float("nan"), 0.05),
    ],
)
def test_metamorphic_compare_wilcoxon(
    loc_pop, scale_pop, loc_perturb, scale_perturb, direction, window_size, critical_quantile
):
    population = np.random.normal(loc_pop, scale_pop, size=100)
    perturbation = np.random.normal(loc_perturb, scale_perturb, size=100)

    result_inc, p_value_inc = paired_wilcoxon(
        population, population + perturbation, alternative="less", critical_quantile=critical_quantile
    )
    result_dec, p_value_dec = paired_wilcoxon(
        population, population + perturbation, alternative="greater", critical_quantile=critical_quantile
    )
    result_inv, p_value_inv = equivalence_wilcoxon(
        population, population + perturbation, window_size=window_size, critical_quantile=critical_quantile
    )

    dict_mapping = {
        Direction.Invariant: (result_inv, p_value_inv),
        Direction.Decreasing: (result_dec, p_value_dec),
        Direction.Increasing: (result_inc, p_value_inc),
    }

    print(f"Direction: {direction.name} and p_value; {dict_mapping[direction][1]}")
    assert dict_mapping[direction][1] < critical_quantile


def test_metamorphic_invariance_t_test(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_invariance_t_test(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        window_size=0.2,
        critical_quantile=0.05,
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"


def test_metamorphic_invariance_t_test_nopert(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        return x

    results = metamorphic.test_metamorphic_invariance_t_test(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        window_size=0.2,
        critical_quantile=0.05,
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"


def test_metamorphic_invariance_wilcoxon(german_credit_test_data, german_credit_model):
    @transformation_function
    def perturbation(x: pd.Series) -> pd.Series:
        x.sex = "female" if x.sex == "male" else "male"
        return x

    results = metamorphic.test_metamorphic_invariance_wilcoxon(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        window_size=0.2,
        critical_quantile=0.05,
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"


def test_metamorphic_invariance_wilcoxon_nopert(german_credit_test_data, german_credit_model):
    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        return x

    results = metamorphic.test_metamorphic_invariance_wilcoxon(
        model=german_credit_model,
        dataset=german_credit_test_data,
        transformation_function=perturbation,
        window_size=0.2,
        critical_quantile=0.05,
    ).execute()

    assert results.actual_slices_size[0] == len(german_credit_test_data)
    assert results.passed, f"metric = {results.metric}"


@pytest.mark.memory_expensive
def test_metamorphic_invariance_llm():
    from langchain.chains import LLMChain
    from langchain.llms.fake import FakeListLLM
    from langchain.prompts import PromptTemplate

    responses = [
        "\n\nHueFoots.",
        "\n\nEcoDrive Motors.",
        "\n\nRainbow Socks.",
        "\n\nNoOil Motors.",
    ]
    llm = FakeListLLM(responses=responses)
    prompt = PromptTemplate(
        input_variables=["product"],
        template="What is a good name for a company that makes {product}?",
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    wrapped_model = Model(
        chain, model_type="text_generation", name="demo", description="demo", feature_names=["product"]
    )
    df = pd.DataFrame(["colorful socks", "electric car"], columns=["product"])

    wrapped_dataset = Dataset(df, cat_columns=[])

    @transformation_function()
    def perturbation(x: pd.Series) -> pd.Series:
        x["product"] = f"some {x['product']}"
        return x

    results = metamorphic.test_metamorphic_invariance(
        model=wrapped_model,
        dataset=wrapped_dataset,
        transformation_function=perturbation,
        threshold=0.1,
        output_sensitivity=0.2,
    ).execute()

    assert results.actual_slices_size[0] == 2
    assert results.passed
