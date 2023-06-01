import typing
from typing import Union

import re
import uuid
from collections import Counter

import numpy as np
import pandas as pd
from scipy.stats import chi2, ks_2samp
from scipy.stats.stats import Ks_2sampResult, wasserstein_distance

from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.core.model import GiskardModel
from giskard.ml_worker.generated.ml_worker_pb2 import SingleTestResult, TestMessage, TestMessageType
from giskard.ml_worker.testing.abstract_test_collection import AbstractTestCollection


class DriftTests(AbstractTestCollection):
    # Class Variable
    other_modalities_pattern = "^other_modalities_[a-z0-9]{32}$"

    @staticmethod
    def _calculate_psi(category, actual_distribution, expected_distribution):
        # To use log and avoid zero distribution probability,
        # we bound distribution probability by min_distribution_probability
        min_distribution_probability = 0.0001

        expected_distribution_bounded = max(
            expected_distribution[category], min_distribution_probability
        )
        actual_distribution_bounded = max(
            actual_distribution[category], min_distribution_probability
        )
        modality_psi = (expected_distribution_bounded - actual_distribution_bounded) * np.log(
            expected_distribution_bounded / actual_distribution_bounded
        )
        return modality_psi

    @staticmethod
    def _calculate_frequencies(actual_series, reference_series, max_categories=None):
        all_modalities = list(set(reference_series).union(set(actual_series)))
        if max_categories is not None and len(all_modalities) > max_categories:
            var_count_expected = dict(Counter(reference_series).most_common(max_categories))
            other_modalities_key = "other_modalities_" + uuid.uuid1().hex
            var_count_expected[other_modalities_key] = len(reference_series) - sum(
                var_count_expected.values()
            )
            categories_list = list(var_count_expected.keys())

            var_count_actual = Counter(actual_series)
            # For test data, we take the same category names as expected_data
            var_count_actual = {i: var_count_actual[i] for i in categories_list}
            var_count_actual[other_modalities_key] = len(actual_series) - sum(
                var_count_actual.values()
            )

            all_modalities = categories_list
        else:
            var_count_expected = Counter(reference_series)
            var_count_actual = Counter(actual_series)
        expected_frequencies = np.array([var_count_expected[i] for i in all_modalities])
        actual_frequencies = np.array([var_count_actual[i] for i in all_modalities])
        return all_modalities, actual_frequencies, expected_frequencies

    @staticmethod
    def _calculate_drift_psi(actual_series, reference_series, max_categories):
        (
            all_modalities,
            actual_frequencies,
            expected_frequencies,
        ) = DriftTests._calculate_frequencies(actual_series, reference_series, max_categories)
        expected_distribution = expected_frequencies / len(reference_series)
        actual_distribution = actual_frequencies / len(actual_series)
        total_psi = 0
        output_data = pd.DataFrame(
            columns=["Modality", "Reference_distribution", "Actual_distribution", "Psi"]
        )
        for category in range(len(all_modalities)):
            modality_psi = DriftTests._calculate_psi(
                category, actual_distribution, expected_distribution
            )

            total_psi += modality_psi
            row = {
                "Modality": all_modalities[category],
                "Reference_distribution": expected_distribution[category],
                "Actual_distribution": expected_distribution[category],
                "Psi": modality_psi,
            }

            output_data = output_data.append(pd.Series(row), ignore_index=True)
        return total_psi, output_data

    @staticmethod
    def _calculate_ks(actual_series, reference_series) -> Ks_2sampResult:
        return ks_2samp(reference_series, actual_series)

    @staticmethod
    def _calculate_earth_movers_distance(actual_series, reference_series):
        unique_reference = np.unique(reference_series)
        unique_actual = np.unique(actual_series)
        sample_space = list(set(unique_reference).union(set(unique_actual)))
        val_max = max(sample_space)
        val_min = min(sample_space)
        if val_max == val_min:
            metric = 0
        else:
            # Normalizing reference_series and actual_series for comparison purposes
            reference_series = (reference_series - val_min) / (val_max - val_min)
            actual_series = (actual_series - val_min) / (val_max - val_min)

            metric = wasserstein_distance(reference_series, actual_series)
        return metric

    @staticmethod
    def _calculate_chi_square(actual_series, reference_series, max_categories):
        (
            all_modalities,
            actual_frequencies,
            expected_frequencies,
        ) = DriftTests._calculate_frequencies(actual_series, reference_series, max_categories)
        chi_square = 0
        # it's necessary for comparison purposes to normalize expected_frequencies
        # so that reference and actual has the same size
        # See https://github.com/scipy/scipy/blob/v1.8.0/scipy/stats/_stats_py.py#L6787
        k_norm = actual_series.shape[0] / reference_series.shape[0]
        output_data = pd.DataFrame(
            columns=["Modality", "Reference_frequencies", "Actual_frequencies", "Chi_square"]
        )
        for i in range(len(all_modalities)):
            chi_square_value = (actual_frequencies[i] - expected_frequencies[i] * k_norm) ** 2 / (
                expected_frequencies[i] * k_norm
            )
            chi_square += chi_square_value

            row = {
                "Modality": all_modalities[i],
                "Reference_frequencies": expected_frequencies[i],
                "Actual_frequencies": actual_frequencies[i],
                "Chi_square": chi_square_value,
            }

            output_data = output_data.append(pd.Series(row), ignore_index=True)
        # if reference_series and actual_series has only one modality it turns nan (len(all_modalities)=1)
        if len(all_modalities) > 1:
            chi_cdf = chi2.cdf(chi_square, len(all_modalities) - 1)
            p_value = 1 - chi_cdf if chi_cdf != 0 else 0
        else:
            p_value = 0
        return chi_square, p_value, output_data

    @staticmethod
    def _validate_column_type(gsk_dataset, column_name, column_type):
        assert gsk_dataset.feature_types[column_name] == column_type, (
            f'Column "{column_name}" is not of type "{column_type}"'
        )

    @staticmethod
    def _validate_column_name(actual_ds, reference_ds, column_name):
        assert (
            column_name in actual_ds.columns
        ), f'"{column_name}" is not a column of Actual Dataset Columns: {", ".join(actual_ds.columns)}'
        assert (
            column_name in reference_ds.columns
        ), f'"{column_name}" is not a column of Reference Dataset Columns: {", ".join(reference_ds.columns)}'

    @staticmethod
    def _validate_series_notempty(actual_series, reference_series):
        if actual_series.empty:
            raise ValueError("Actual Series computed from the column is empty")
        if reference_series.empty:
            raise ValueError("Reference Series computed from the column is empty")

    def _extract_series(self, actual_ds, reference_ds, column_name, column_type):
        actual_ds.df.reset_index(drop=True, inplace=True)
        reference_ds.df.reset_index(drop=True, inplace=True)
        self._validate_column_name(actual_ds, reference_ds, column_name)
        self._validate_column_type(actual_ds, column_name, column_type)
        self._validate_column_type(reference_ds, column_name, column_type)
        actual_series = actual_ds.df[column_name]
        reference_series = reference_ds.df[column_name]
        self._validate_series_notempty(actual_series, reference_series)
        return actual_series, reference_series

    def test_drift_psi(
        self,
        reference_ds: GiskardDataset,
        actual_ds: GiskardDataset,
        column_name: str,
        threshold=0.2,
        max_categories: int = 20,
        psi_contribution_percent: float = 0.2,
    ) -> SingleTestResult:
        """
        Test if the PSI score between the actual and reference datasets is below the threshold for
        a given categorical feature

        Example : The test is passed when the  PSI score of gender between reference and actual sets is below 0.2

        Args:
            actual_ds(GiskardDataset):
                Actual dataset to compute the test
            reference_ds(GiskardDataset):
                Reference dataset to compute the test
            column_name(str):
                Name of column with categorical feature
            threshold(float:
                Threshold value for PSI
            max_categories:
                the maximum categories to compute the PSI score
            psi_contribution_percent:
                the ratio between the PSI score of a given category over the total PSI score
                of the categorical variable. If there is a drift, the test provides all the
                categories that have a PSI contribution over than this ratio.

        Returns:
            actual_slices_size:
                Length of rows with given categorical feature in actual slice
            reference_slices_size:
                Length of rows with given categorical feature in reference slice
            metric:
                The total psi score between the actual and reference datasets
            passed:
                TRUE if total_psi <= threshold
        """
        actual_series, reference_series = self._extract_series(
            actual_ds, reference_ds, column_name, "category"
        )

        messages, passed, total_psi = self._test_series_drift_psi(
            actual_series,
            reference_series,
            "data",
            max_categories,
            psi_contribution_percent,
            threshold,
        )

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_series)],
                reference_slices_size=[len(reference_series)],
                passed=passed,
                metric=total_psi,
                messages=messages,
            )
        )

    def test_drift_chi_square(
        self,
        reference_ds: GiskardDataset,
        actual_ds: GiskardDataset,
        column_name: str,
        threshold=0.05,
        max_categories: int = 20,
        chi_square_contribution_percent: float = 0.2,
    ) -> SingleTestResult:
        """
        Test if the p-value of the chi square test between the actual and reference datasets is
        above the threshold for a given categorical feature

        Example : The test is passed when the pvalue of the chi square test of the categorical variable between
         reference and actual sets is higher than 0.05. It means that chi square test cannot be rejected at 5% level
         and that we cannot assume drift for this variable.

        Args:
            actual_ds(GiskardDataset):
                Actual dataset to compute the test
            reference_ds(GiskardDataset):
                Reference dataset to compute the test
            column_name(str):
                Name of column with categorical feature
            threshold(float):
                Threshold for p-value of chi-square
            max_categories:
                the maximum categories to compute the chi square
            chi_square_contribution_percent:
                the ratio between the Chi-Square value of a given category over the total Chi-Square
                value of the categorical variable. If there is a drift, the test provides all the
                categories that have a PSI contribution over than this ratio.

        Returns:
            actual_slices_size:
                Length of rows with given categorical feature in actual slice
            reference_slices_size:
                Length of rows with given categorical feature in reference slice
            metric:
                The pvalue of chi square test
            passed:
                TRUE if metric > threshold
        """
        actual_series, reference_series = self._extract_series(
            actual_ds, reference_ds, column_name, "category"
        )

        messages, p_value, passed = self._test_series_drift_chi(
            actual_series,
            reference_series,
            "data",
            chi_square_contribution_percent,
            max_categories,
            threshold,
        )

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_series)],
                reference_slices_size=[len(reference_series)],
                passed=passed,
                metric=p_value,
                messages=messages,
            )
        )

    def test_drift_ks(
        self,
        reference_ds: GiskardDataset,
        actual_ds: GiskardDataset,
        column_name: str,
        threshold=0.05,
    ) -> SingleTestResult:
        """
        Test if the pvalue of the KS test between the actual and reference datasets is above
        the threshold for a given numerical feature

        Example : The test is passed when the pvalue of the KS test of the numerical variable
        between the actual and reference datasets is higher than 0.05. It means that the KS test
        cannot be rejected at 5% level and that we cannot assume drift for this variable.

        Args:
            actual_ds(GiskardDataset):
               Actual dataset to compute the test
            reference_ds(GiskardDataset):
                Reference dataset to compute the test
            column_name(str):
                Name of column with numerical feature
            threshold:
                Threshold for p-value of KS test

        Returns:
            actual_slices_size:
                Length of rows with given numerical feature in actual slice
            reference_slices_size:
                Length of rows with given numerical feature in reference slice
            metric:
                The pvalue of KS test
            passed:
                TRUE if metric >= threshold
        """
        actual_series, reference_series = self._extract_series(
            actual_ds, reference_ds, column_name, "numeric"
        )

        result = self._calculate_ks(actual_series, reference_series)

        passed = result.pvalue >= threshold

        messages = self._generate_message_ks(passed, result, threshold, "data")

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_series)],
                reference_slices_size=[len(reference_series)],
                passed=passed,
                metric=result.pvalue,
                messages=messages,
            )
        )

    def test_drift_earth_movers_distance(
        self,
        reference_ds: GiskardDataset,
        actual_ds: GiskardDataset,
        column_name: str,
        threshold: float = 0.2,
    ) -> SingleTestResult:
        """
        Test if the earth movers distance between the actual and reference datasets is
        below the threshold for a given numerical feature

        Example : The test is passed when the earth movers distance of the numerical
         variable between the actual and reference datasets is lower than 0.1.
         It means that we cannot assume drift for this variable.

        Args:
            actual_ds(GiskardDataset):
                Actual dataset to compute the test
            reference_ds(GiskardDataset):
                Reference dataset to compute the test
            column_name(str):
                Name of column with numerical feature
            threshold:
                Threshold for earth movers distance

        Returns:
            actual_slices_size:
                Length of rows with given numerical feature in actual slice
            reference_slices_size:
                Length of rows with given numerical feature in reference slice
            metric:
                The earth movers distance
            passed:
                TRUE if metric <= threshold
        """
        actual_series, reference_series = self._extract_series(
            actual_ds, reference_ds, column_name, "numeric"
        )

        metric = self._calculate_earth_movers_distance(actual_series, reference_series)

        passed = metric <= threshold

        messages: Union[typing.List[TestMessage], None] = None

        if not passed:
            messages = [
                TestMessage(
                    type=TestMessageType.ERROR,
                    text=f"The data is drifting (metric is equal to {np.round(metric, 9)} and is below the test risk level {threshold}) ",
                )
            ]
        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_series)],
                reference_slices_size=[len(reference_series)],
                passed=True if threshold is None else passed,
                metric=metric,
                messages=messages,
            )
        )

    def test_drift_prediction_psi(
        self,
        reference_slice: GiskardDataset,
        actual_slice: GiskardDataset,
        model: GiskardModel,
        max_categories: int = 10,
        threshold: float = 0.2,
        psi_contribution_percent: float = 0.2,
    ):
        """
        Test if the PSI score between the reference and actual datasets is below the threshold
        for the classification labels predictions

        Example : The test is passed when the  PSI score of classification labels prediction
        for females between reference and actual sets is below 0.2

        Args:
            actual_slice(GiskardDataset):
                Slice of the actual dataset
            reference_slice(GiskardDataset):
                Slice of the reference dataset
            model(GiskardModel):
                Model used to compute the test
            threshold(float):
                Threshold value for PSI
            max_categories:
                The maximum categories to compute the PSI score
            psi_contribution_percent:
                The ratio between the PSI score of a given category over the total PSI score
                of the categorical variable. If there is a drift, the test provides all the
                categories that have a PSI contribution over than this ratio.

        Returns:
            actual_slices_size:
                Length of actual slice tested
            reference_slices_size:
                Length of reference slice tested
            passed:
                TRUE if metric <= threshold
            metric:
                Total PSI value
            messages:
                Psi result message
        """
        actual_slice.df.reset_index(drop=True, inplace=True)
        reference_slice.df.reset_index(drop=True, inplace=True)
        prediction_reference = pd.Series(model.run_predict(reference_slice).prediction)
        prediction_actual = pd.Series(model.run_predict(actual_slice).prediction)
        messages, passed, total_psi = self._test_series_drift_psi(
            prediction_actual,
            prediction_reference,
            "prediction",
            max_categories,
            psi_contribution_percent,
            threshold,
        )

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                reference_slices_size=[len(reference_slice)],
                passed=passed,
                metric=total_psi,
                messages=messages,
            )
        )

    def _test_series_drift_psi(
        self,
        actual_series,
        reference_series,
        test_data,
        max_categories,
        psi_contribution_percent,
        threshold,
    ):
        total_psi, output_data = self._calculate_drift_psi(
            actual_series, reference_series, max_categories
        )
        passed = True if threshold is None else total_psi <= threshold
        main_drifting_modalities_bool = output_data["Psi"] > psi_contribution_percent * total_psi
        messages = self._generate_message_modalities(
            main_drifting_modalities_bool, output_data, test_data
        )
        return messages, passed, total_psi

    @staticmethod
    def _generate_message_modalities(main_drifting_modalities_bool, output_data, test_data):
        modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()
        filtered_modalities = [
            w for w in modalities_list if not re.match(DriftTests.other_modalities_pattern, w)
        ]
        messages: Union[typing.List[TestMessage], None] = None
        if filtered_modalities:
            messages = [
                TestMessage(
                    type=TestMessageType.ERROR,
                    text=f"The {test_data} is drifting for the following modalities: {','.join(filtered_modalities)}",
                )
            ]
        return messages

    def test_drift_prediction_chi_square(
        self,
        reference_slice: GiskardDataset,
        actual_slice: GiskardDataset,
        model: GiskardModel,
        max_categories: int = 10,
        threshold: float = 0.05,
        chi_square_contribution_percent: float = 0.2,
    ):
        """
        Test if the Chi Square value between the reference and actual datasets is below the threshold
        for the classification labels predictions for a given slice

        Example : The test is passed when the  Chi Square value of classification labels prediction
        for females between reference and actual sets is below 0.05

        Args:
            actual_slice(GiskardDataset):
                Slice of the actual dataset
            reference_slice(GiskardDataset):
                Slice of the reference dataset
            model(GiskardModel):
                Model used to compute the test
            threshold(float):
                Threshold value of p-value of Chi-Square
            max_categories:
                the maximum categories to compute the PSI score
            chi_square_contribution_percent:
                the ratio between the Chi-Square value of a given category over the total Chi-Square
                value of the categorical variable. If there is a drift, the test provides all the
                categories that have a PSI contribution over than this ratio.

        Returns:
            actual_slices_size:
                Length of actual slice tested
            reference_slices_size:
                Length of reference slice tested
            passed:
                TRUE if metric > threshold
            metric:
                Calculated p-value of Chi_square
            messages:
                Message describing if prediction is drifting or not
        """
        actual_slice.df.reset_index(drop=True, inplace=True)
        reference_slice.df.reset_index(drop=True, inplace=True)
        prediction_reference = pd.Series(model.run_predict(reference_slice).prediction)
        prediction_actual = pd.Series(model.run_predict(actual_slice).prediction)

        messages, p_value, passed = self._test_series_drift_chi(
            prediction_actual,
            prediction_reference,
            "prediction",
            chi_square_contribution_percent,
            max_categories,
            threshold,
        )

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                reference_slices_size=[len(reference_slice)],
                passed=passed,
                metric=p_value,
                messages=messages,
            )
        )

    def _test_series_drift_chi(
        self,
        actual_series,
        reference_series,
        test_data,
        chi_square_contribution_percent,
        max_categories,
        threshold,
    ):
        chi_square, p_value, output_data = self._calculate_chi_square(
            actual_series, reference_series, max_categories
        )
        passed = p_value > threshold
        main_drifting_modalities_bool = (
            output_data["Chi_square"] > chi_square_contribution_percent * chi_square
        )
        messages = self._generate_message_modalities(
            main_drifting_modalities_bool, output_data, test_data
        )
        return messages, p_value, passed

    def test_drift_prediction_ks(
        self,
        reference_slice: GiskardDataset,
        actual_slice: GiskardDataset,
        model: GiskardModel,
        classification_label=None,
        threshold=None,
    ) -> SingleTestResult:
        """
        Test if the pvalue of the KS test for prediction between the reference and actual datasets for
         a given subpopulation is above the threshold

        Example : The test is passed when the pvalue of the KS test for the prediction for females
         between reference and actual dataset is higher than 0.05. It means that the KS test cannot be
         rejected at 5% level and that we cannot assume drift for this variable.

        Args:
            actual_slice(GiskardDataset):
                Slice of the actual dataset
            reference_slice(GiskardDataset):
                Slice of the reference dataset
            model(GiskardModel):
                Model used to compute the test
            threshold(float):
                Threshold for p-value of Kolmogorov-Smirnov test
            classification_label(str):
                One specific label value from the target column for classification model

        Returns:
            actual_slices_size:
                Length of actual slice tested
            reference_slices_size:
                Length of reference slice tested
            passed:
                TRUE if metric >= threshold
            metric:
                The calculated p-value Kolmogorov-Smirnov test
            messages:
                Kolmogorov-Smirnov result message
        """
        actual_slice.df.reset_index(drop=True, inplace=True)
        reference_slice.df.reset_index(drop=True, inplace=True)

        assert (
            model.model_type != "classification"
            or classification_label in model.classification_labels
        ), f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        prediction_reference = (
            pd.Series(
                model.run_predict(reference_slice).all_predictions[classification_label].values
            )
            if model.model_type == "classification"
            else pd.Series(model.run_predict(reference_slice).prediction)
        )
        prediction_actual = (
            pd.Series(model.run_predict(actual_slice).all_predictions[classification_label].values)
            if model.model_type == "classification"
            else pd.Series(model.run_predict(actual_slice).prediction)
        )

        result: Ks_2sampResult = self._calculate_ks(prediction_reference, prediction_actual)

        passed = True if threshold is None else result.pvalue >= threshold

        messages = self._generate_message_ks(passed, result, threshold, "prediction")

        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                reference_slices_size=[len(reference_slice)],
                passed=passed,
                metric=result.pvalue,
                messages=messages,
            )
        )

    @staticmethod
    def _generate_message_ks(passed, result, threshold, data_type):
        messages: Union[typing.List[TestMessage], None] = None
        if not passed:
            messages = [
                TestMessage(
                    type=TestMessageType.ERROR,
                    text=f"The {data_type} is drifting (p-value is equal to {np.round(result.pvalue, 9)} "
                    f"and is below the test risk level {threshold}) ",
                )
            ]
        return messages

    def test_drift_prediction_earth_movers_distance(
        self,
        reference_slice: GiskardDataset,
        actual_slice: GiskardDataset,
        model: GiskardModel,
        classification_label=None,
        threshold=0.2,
    ) -> SingleTestResult:
        """
        Test if the Earth Mover’s Distance value between the reference and actual datasets is
        below the threshold for the classification labels predictions for classification
        model and prediction for regression models

        Example :
        Classification : The test is passed when the  Earth Mover’s Distance value of classification
        labels probabilities for females between reference and actual sets is below 0.2

        Regression : The test is passed when the  Earth Mover’s Distance value of prediction
        for females between reference and actual sets is below 0.2

        Args:
            reference_slice(GiskardDataset):
                slice of the reference dataset
            actual_slice(GiskardDataset):
                slice of the actual dataset
            model(GiskardModel):
                uploaded model
            classification_label:
                one specific label value from the target column for classification model
            threshold:
                threshold for earth mover's distance

        Returns:
            passed:
                TRUE if metric <= threshold
            metric:
                Earth Mover's Distance value

        """
        actual_slice.df.reset_index(drop=True, inplace=True)
        reference_slice.df.reset_index(drop=True, inplace=True)

        prediction_reference = (
            model.run_predict(reference_slice).all_predictions[classification_label].values
            if model.model_type == "classification"
            else model.run_predict(reference_slice).prediction
        )
        prediction_actual = (
            model.run_predict(actual_slice).all_predictions[classification_label].values
            if model.model_type == "classification"
            else model.run_predict(actual_slice).prediction
        )

        metric = self._calculate_earth_movers_distance(prediction_reference, prediction_actual)

        passed = True if threshold is None else metric <= threshold
        messages: Union[typing.List[TestMessage], None] = None

        if not passed:
            messages = [
                TestMessage(
                    type=TestMessageType.ERROR,
                    text=f"The prediction is drifting (metric is equal to {np.round(metric, 9)} "
                    f"and is above the test risk level {threshold}) ",
                )
            ]
        return self.save_results(
            SingleTestResult(
                actual_slices_size=[len(actual_slice)],
                reference_slices_size=[len(reference_slice)],
                passed=True if threshold is None else metric <= threshold,
                metric=metric,
                messages=messages,
            )
        )
