from giskard.testing.tests.drift import test_drift_psi, test_drift_chi_square, \
    test_drift_prediction_chi_square, test_drift_prediction_psi
from giskard.datasets.base import Dataset
from collections import Counter
import pytest
import numpy as np
import pandas as pd


@pytest.mark.parametrize("dataset, male_drift_samples", [("german_credit_data", 2), ("german_credit_data", 0)])
def test_data_drift_psi_detailed(dataset, male_drift_samples, request):
    dataset = request.getfixturevalue(dataset)
    actual_dataset = Dataset(
        df=pd.concat(
            [dataset.df[dataset.df.sex == 'female'], dataset.df[dataset.df.sex == 'male'].sample(male_drift_samples)],
            axis=0),
        target=dataset.target,
        column_types=dataset.column_types)
    reference_dataset = Dataset(df=dataset.df,
                                target=dataset.target,
                                column_types=dataset.column_types)

    column_name = 'sex'
    reference_series = reference_dataset.df[column_name]
    actual_series = actual_dataset.df[column_name]

    # deciphering _calculate_frequencies
    all_modalities = list(set(reference_series).union(set(actual_series)))
    var_count_expected = Counter(reference_series)  # Counter({'male': 342, 'female': 158})
    var_count_actual = Counter(actual_series)  # Counter({'male': 348, 'female': 152})
    expected_frequencies = np.array([var_count_expected[i] for i in all_modalities])  # [342 158]
    actual_frequencies = np.array([var_count_actual[i] for i in all_modalities])  # [348 152]

    # deciphering _calculate_drift_psi
    expected_distribution = expected_frequencies / len(reference_series)  # [0.684 0.316]
    actual_distribution = actual_frequencies / len(actual_series)  # [0.696 0.304]
    total_psi = 0
    output_data = pd.DataFrame(columns=["Modality", "Reference_distribution", "Actual_distribution", "Psi"])
    for category in range(len(all_modalities)):
        # --- deciphering _calculate_psi
        min_distribution_probability = 0.0001

        expected_distribution_bounded = max(expected_distribution[category], min_distribution_probability)
        actual_distribution_bounded = max(actual_distribution[category], min_distribution_probability)
        modality_psi = (expected_distribution_bounded - actual_distribution_bounded) * np.log(
            expected_distribution_bounded / actual_distribution_bounded
        )
        # ---

        total_psi += modality_psi
        row = {
            "Modality": all_modalities[category],
            "Reference_distribution": expected_distribution[category],
            "Actual_distribution": expected_distribution[category],
            "Psi": modality_psi,
        }
        output_data = output_data.append(pd.Series(row), ignore_index=True)

    psi_contribution_percent = 0.2
    main_drifting_modalities_bool = output_data["Psi"] > psi_contribution_percent * total_psi
    modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()
    benchmark_failed_df = actual_dataset.df.loc[actual_series.isin(modalities_list)]

    if male_drift_samples == 0:
        with pytest.raises(ValueError, match="test_drift_psi: the categories .* completely drifted as they.*"):
            test_drift_psi(actual_dataset=actual_dataset,
                           reference_dataset=reference_dataset,
                           column_name=column_name,
                           debug=True).execute()

    else:
        results = test_drift_psi(actual_dataset=actual_dataset,
                                 reference_dataset=reference_dataset,
                                 column_name=column_name,
                                 debug=True).execute()
        assert list(results.output_df.df.index.values) == list(benchmark_failed_df.index.values)
        assert len(results.output_df.df) == male_drift_samples


@pytest.mark.parametrize("dataset, male_drift_samples", [("german_credit_data", 2), ("german_credit_data", 0)])
def test_data_drift_globally(dataset, male_drift_samples, request):
    dataset = request.getfixturevalue(dataset)
    actual_df = pd.concat(
        [dataset.df[dataset.df.sex == 'female'], dataset.df[dataset.df.sex == 'male'].sample(male_drift_samples)],
        axis=0)
    actual_dataset = Dataset(
        df=actual_df,
        target=dataset.target,
        column_types=dataset.column_types)
    reference_dataset = Dataset(df=dataset.df,
                                target=dataset.target,
                                column_types=dataset.column_types)

    column_name = 'sex'
    results = test_drift_chi_square(actual_dataset=actual_dataset,
                                    reference_dataset=reference_dataset,
                                    column_name=column_name,
                                    debug=True).execute()

    assert len(results.output_df.df) == len(actual_df)


@pytest.mark.parametrize("model, dataset", [("german_credit_model", "german_credit_data")])
def test_prediction_drift_globally(model, dataset, request):
    model = request.getfixturevalue(model)
    dataset = request.getfixturevalue(dataset)

    actual_df = dataset.df[dataset.df.default == 'Default']
    reference_df = dataset.df[dataset.df.default == 'Not default']
    actual_dataset = Dataset(
        df=actual_df,
        target=dataset.target,
        column_types=dataset.column_types)
    reference_dataset = Dataset(
        df=reference_df,
        target=dataset.target,
        column_types=dataset.column_types)

    results = test_drift_prediction_psi(model=model,
                                        actual_dataset=actual_dataset,
                                        reference_dataset=reference_dataset,
                                        debug=True).execute()
    assert len(results.output_df.df) == len(actual_df)

    actual_prediction = pd.Series(model.predict(actual_dataset).prediction)
    benchmark_len = len(actual_dataset.df.loc[actual_prediction.isin(["Default"]).values])
    results = test_drift_prediction_chi_square(model=model,
                                               actual_dataset=actual_dataset,
                                               reference_dataset=reference_dataset,
                                               debug=True).execute()
    assert len(results.output_df.df) == benchmark_len
