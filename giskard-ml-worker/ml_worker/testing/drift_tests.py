import typing
import uuid
from collections import Counter
from typing import Union
import re

import numpy as np
import pandas as pd
from scipy.stats import chi2, ks_2samp
from scipy.stats.stats import Ks_2sampResult, wasserstein_distance

from generated.ml_worker_pb2 import SingleTestResult, TestMessage, TestMessageType
from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.core.model import GiskardModel
from ml_worker.testing.abstract_test_collection import AbstractTestCollection
from ml_worker.testing.utils import save_df, compress, bin_numerical_values


class DriftTests(AbstractTestCollection):
    @staticmethod
    def _calculate_modality_drift(category, actual_distribution, expected_distribution):
        # To use log and avoid zero distribution probability,
        # we bound distribution probability by min_distribution_probability
        min_distribution_probability = 0.0001

        expected_distribution_bounded = max(expected_distribution[category], min_distribution_probability)
        actual_distribution_bounded = max(actual_distribution[category], min_distribution_probability)
        modality_drift = (expected_distribution_bounded - actual_distribution_bounded) * \
                        np.log(expected_distribution_bounded / actual_distribution_bounded)
        return modality_drift

    @staticmethod
    def _calculate_frequencies(actual_series, reference_series, max_categories=None):
        all_modalities = list(set(reference_series).union(set(actual_series)))
        if max_categories is not None and len(all_modalities) > max_categories:
            var_count_expected = dict(Counter(reference_series).most_common(max_categories))
            other_modalities_key = 'other_modalities_' + uuid.uuid1().hex
            var_count_expected[other_modalities_key] = len(reference_series) - sum(var_count_expected.values())
            categories_list = list(var_count_expected.keys())

            var_count_actual = Counter(actual_series)
            # For test data, we take the same category names as expected_data
            var_count_actual = {i: var_count_actual[i] for i in categories_list}
            var_count_actual[other_modalities_key] = len(actual_series) - sum(var_count_actual.values())

            all_modalities = categories_list
        else:
            var_count_expected = Counter(reference_series)
            var_count_actual = Counter(actual_series)
        expected_frequencies = np.array([var_count_expected[i] for i in all_modalities])
        actual_frequencies = np.array([var_count_actual[i] for i in all_modalities])
        return all_modalities, actual_frequencies, expected_frequencies

    @staticmethod
    def _calculate_drift_psi(actual_series, reference_series, max_categories):
        all_modalities, actual_frequencies, expected_frequencies = DriftTests._calculate_frequencies(
            actual_series, reference_series, max_categories)
        expected_distribution = expected_frequencies / len(reference_series)
        actual_distribution = actual_frequencies / len(actual_series)
        total_psi = 0
        output_data = pd.DataFrame(columns=["Modality", "Reference_distribution", "Actual_distribution", "Psi"])
        for category in range(len(all_modalities)):
            modality_psi = DriftTests._calculate_modality_drift(category, actual_distribution, expected_distribution)

            total_psi += modality_psi
            row = {
                "Modality": all_modalities[category],
                "Reference_distribution": expected_distribution[category],
                "Actual_distribution": expected_distribution[category],
                "Psi": modality_psi
            }

            output_data = output_data.append(pd.Series(row), ignore_index=True)
        return total_psi, output_data

    @staticmethod
    def _calculate_numerical_drift(actual_series, reference_series):
        all_modalities, actual_frequencies, expected_frequencies = DriftTests._calculate_frequencies(
            actual_series, reference_series)
        expected_distribution = expected_frequencies / len(reference_series)
        actual_distribution = actual_frequencies / len(actual_series)
        total_drift = 0
        output_data = pd.DataFrame(
            columns=["Modality", "Reference_distribution", "Actual_distribution", "Modality_drift"])
        for category in range(len(all_modalities)):
            modality_drift = DriftTests._calculate_modality_drift(category, actual_distribution, expected_distribution)

            total_drift += modality_drift
            row = {
                "Modality": all_modalities[category],
                "Reference_distribution": expected_distribution[category],
                "Actual_distribution": expected_distribution[category],
                "Modality_drift": modality_drift
            }

            output_data = output_data.append(pd.Series(row), ignore_index=True)
        return total_drift, output_data

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
        all_modalities, actual_frequencies, expected_frequencies = DriftTests._calculate_frequencies(
            actual_series, reference_series, max_categories)
        chi_square = 0
        # it's necessary for comparison purposes to normalize expected_frequencies
        # so that reference and actual has the same size
        # See https://github.com/scipy/scipy/blob/v1.8.0/scipy/stats/_stats_py.py#L6787
        k_norm = actual_series.shape[0] / reference_series.shape[0]
        output_data = pd.DataFrame(columns=["Modality", "Reference_frequencies", "Actual_frequencies", "Chi_square"])
        for i in range(len(all_modalities)):
            chi_square_value = (actual_frequencies[i] - expected_frequencies[i] * k_norm) ** 2 / (
                    expected_frequencies[i] * k_norm)
            chi_square += chi_square_value

            row = {"Modality": all_modalities[i],
                   "Reference_frequencies": expected_frequencies[i],
                   "Actual_frequencies": actual_frequencies[i],
                   "Chi_square": chi_square_value}

            output_data = output_data.append(pd.Series(row), ignore_index=True)
        # if reference_series and actual_series has only one modality it turns nan (len(all_modalities)=1)
        if len(all_modalities) > 1:
            chi_cdf = chi2.cdf(chi_square, len(all_modalities) - 1)
            p_value = 1 - chi_cdf if chi_cdf != 0 else 0
        else:
            p_value = 0
        return chi_square, p_value, output_data

    def test_drift_psi(self,
                       reference_ds: pd.DataFrame,
                       actual_ds: pd.DataFrame,
                       column_name: str,
                       threshold=0.2,
                       max_categories: int = 20,
                       psi_contribution_percent: float = 0.2) -> SingleTestResult:
        """
        Test if the PSI score between the actual and expected datasets is below the threshold for
        a given categorical feature

        Example : The test is passed when the  PSI score of gender between reference and actual sets is below 0.2


        Args:
            actual_ds(GiskardDataset):
                Actual dataset to compute the test
            reference_ds(GiskardDataset):
                Reference dataset to compute the test
            column_name(str):
                Name of column with numerical feature
            threshold:
                threshold value for PSI
            max_categories:
                the maximum categories to compute the PSI score
            psi_contribution_percent:
                the ratio between the PSI score of a given category over the total PSI score
                of the categorical variable. If there is a drift, the test provides all the
                categories that have a PSI contribution over than this ratio.

        Returns:
            metric:
                the total psi score between the actual and expected datasets
            passed:
                TRUE if total_psi <= threshold

        """
        assert column_name in actual_ds.columns, \
            f'"{column_name}" is not a column of Actual Dataset Columns: {", ".join(actual_ds.columns)}'
        actual_series = actual_ds[column_name]
        assert column_name in reference_ds.columns, \
            f'"{column_name}" is not a column of Reference Dataset Columns: {", ".join(reference_ds.columns)}'
        reference_series = reference_ds[column_name]
        total_psi, output_data = self._calculate_drift_psi(actual_series, reference_series, max_categories)

        passed = True if threshold is None else total_psi <= threshold
        messages: Union[typing.List[TestMessage], None] = None
        output_df_sample = None
        if not passed:
            main_drifting_modalities_bool = output_data["Psi"] > psi_contribution_percent * total_psi
            modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()
            filtered_modalities = [w for w in modalities_list if not re.match('^other_modalities_[a-z0-9]{32}$', w)]
            failed_df = actual_ds.loc[actual_series.isin(filtered_modalities)]
            output_df_sample = compress(save_df(failed_df))

            messages = [TestMessage(
                type=TestMessageType.ERROR,
                text=f"The data is drifting for the following modalities {*filtered_modalities,}"
            )]

        return self.save_results(SingleTestResult(
            passed=passed,
            metric=total_psi,
            messages=messages,
            output_df=output_df_sample
        ))

    def test_drift_chi_square(self,
                              reference_ds: pd.DataFrame,
                              actual_ds: pd.DataFrame,
                              column_name: str,
                              threshold=0.05,
                              max_categories: int = 20,
                              chi_square_contribution_percent: float = 0.2) -> SingleTestResult:
        """
        Test if the p-value of the chi square test between the actual and expected datasets is
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
                Name of column with numerical feature
            threshold:
                threshold for p-value of chi-square
            max_categories:
                the maximum categories to compute the chi square
            chi_square_contribution_percent:
                the ratio between the Chi-Square value of a given category over the total Chi-Square
                value of the categorical variable. If there is a drift, the test provides all the
                categories that have a PSI contribution over than this ratio.

        Returns:
            metric:
                the pvalue of chi square test
            passed:
                TRUE if metric > threshold

        """
        assert column_name in actual_ds.columns, \
            f'"{column_name}" is not a column of Actual Dataset Columns: {",".join(actual_ds.columns)}'
        actual_series = actual_ds[column_name]
        assert column_name in reference_ds.columns, \
            f'"{column_name}" is not a column of Reference Dataset Columns: {",".join(reference_ds.columns)}'
        reference_series = reference_ds[column_name]

        chi_square, p_value, output_data = self._calculate_chi_square(actual_series, reference_series, max_categories)
        passed = p_value > threshold
        messages: Union[typing.List[TestMessage], None] = None
        output_df_sample = None
        if not passed:
            main_drifting_modalities_bool = output_data["Chi_square"] > chi_square_contribution_percent * chi_square
            modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()
            filtered_modalities = [w for w in modalities_list if not re.match('^other_modalities_[a-z0-9]{32}$', w)]
            failed_df = actual_ds.loc[actual_series.isin(filtered_modalities)]

            output_df_sample = compress(save_df(failed_df))
            messages = [TestMessage(
                type=TestMessageType.ERROR,
                text=f"The prediction is drifting for the following modalities {*filtered_modalities,}"
            )]

        return self.save_results(SingleTestResult(
            passed=passed,
            metric=p_value,
            messages=messages,
            output_df=output_df_sample
        ))

    def test_drift_ks(self,
                      reference_ds: pd.DataFrame,
                      actual_ds: pd.DataFrame,
                      column_name: str,
                      threshold=0.05) -> SingleTestResult:
        """
         Test if the pvalue of the KS test between the actual and expected datasets is above
          the threshold for a given numerical feature

        Example : The test is passed when the pvalue of the KS test of the numerical variable
        between the actual and expected datasets is higher than 0.05. It means that the KS test
        cannot be rejected at 5% level and that we cannot assume drift for this variable.

        Args:
            actual_ds(GiskardDataset):
                Actual dataset to compute the test
            reference_ds(GiskardDataset):
                Reference dataset to compute the test
            column_name(str):
                Name of column with numerical feature
            threshold:
                threshold for p-value of KS test

        Returns:
            metric:
                the pvalue of KS test
            passed:
                TRUE if metric > threshold
        """
        assert column_name in actual_ds.columns, \
            f'"{column_name}" is not a column of Actual Dataset Columns: {",".join(actual_ds.columns)}'
        actual_series = actual_ds[column_name]
        assert column_name in reference_ds.columns, \
            f'"{column_name}" is not a column of Reference Dataset Columns: {",".join(reference_ds.columns)}'
        reference_series = reference_ds[column_name]

        reference_converted = bin_numerical_values(reference_series)
        actual_converted = bin_numerical_values(actual_series)
        total_ks, output_data = self._calculate_numerical_drift(actual_converted, reference_converted)
        result = self._calculate_ks(actual_series, reference_series)

        passed = result.pvalue >= threshold
        output_df_sample = None

        if not passed:
            main_drifting_modalities_bool = output_data["Modality_drift"] > 0.2 * threshold  # need to verify
            modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()
            failed_df = actual_ds.loc[actual_converted.isin(modalities_list)]
            output_df_sample = compress(save_df(failed_df))

        return self.save_results(SingleTestResult(
            passed=result.pvalue >= threshold,
            metric=result.pvalue,
            output_df=output_df_sample
        ))

    def test_drift_earth_movers_distance(self,
                                         reference_ds: pd.DataFrame,
                                         actual_ds: pd.DataFrame,
                                         column_name: str,
                                         threshold: float = None) -> SingleTestResult:
        """
        Test if the earth movers distance between the actual and expected datasets is
        below the threshold for a given numerical feature

        Example : The test is passed when the earth movers distance of the numerical
         variable between the actual and expected datasets is lower than 0.1.
         It means that we cannot assume drift for this variable.

        Args:
            actual_ds(GiskardDataset):
                Actual dataset to compute the test
            reference_ds(GiskardDataset):
                Reference dataset to compute the test
            column_name(str):
                Name of column with numerical feature
            threshold:
                threshold for p-value of earth movers distance

        Returns:
            metric:
                the earth movers distance
            passed:
                TRUE if metric < threshold
        """
        assert column_name in actual_ds.columns, \
            f'"{column_name}" is not a column of Actual Dataset Columns: {",".join(actual_ds.columns)}'
        actual_series = actual_ds[column_name]
        assert column_name in reference_ds.columns, \
            f'"{column_name}" is not a column of Reference Dataset Columns: {",".join(reference_ds.columns)}'
        reference_series = reference_ds[column_name]

        metric = self._calculate_earth_movers_distance(actual_series, reference_series)
        return self.save_results(SingleTestResult(
            passed=True if threshold is None else metric <= threshold,
            metric=metric
        ))

    def test_drift_prediction_psi(self, reference_slice: GiskardDataset, actual_slice: GiskardDataset,
                                  model: GiskardModel,
                                  max_categories: int = 10, threshold: float = 0.2,
                                  psi_contribution_percent: float = 0.2):
        """
        Test if the PSI score between the reference and actual datasets is below the threshold
        for the classification labels predictions

        Example : The test is passed when the  PSI score of classification labels prediction
        for females between reference and actual sets is below 0.2

        Args:
            reference_slice(GiskardDataset):
                slice of the reference dataset 
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(GiskardModel):
                uploaded model
            max_categories:
                the maximum categories to compute the PSI score
            threshold:
                threshold value for PSI
            psi_contribution_percent:
                the ratio between the PSI score of a given category over the total PSI score
                of the categorical variable. If there is a drift, the test provides all the
                categories that have a PSI contribution over than this ratio.

        Returns:
            passed:
                TRUE if total psi <= threshold
            metric:
                total PSI value
            messages:
                psi result message

        """
        reference_slice = reference_slice.df.reset_index(drop=True)
        actual_slice = actual_slice.df.reset_index(drop=True)
        prediction_reference = pd.Series(model.run_predict(reference_slice).prediction)
        prediction_actual = pd.Series(model.run_predict(actual_slice).prediction)
        total_psi, output_data = self._calculate_drift_psi(prediction_actual, prediction_reference, max_categories)

        passed = True if threshold is None else total_psi <= threshold
        messages: Union[typing.List[TestMessage], None] = None
        output_df_sample = None

        if not passed:
            main_drifting_modalities_bool = output_data["Psi"] > psi_contribution_percent * total_psi
            modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()
            filtered_modalities = [w for w in modalities_list if not re.match('^other_modalities_[a-z0-9]{32}$', w)]
            failed_df = actual_slice.loc[prediction_actual.isin(filtered_modalities)]
            output_df_sample = compress(save_df(failed_df))

            messages = [TestMessage(
                type=TestMessageType.ERROR,
                text=f"The prediction is drifting for the following modalities {*filtered_modalities,}"
            )]

        return self.save_results(SingleTestResult(
            passed=passed,
            metric=total_psi,
            messages=messages,
            output_df=output_df_sample
        ))

    def test_drift_prediction_chi_square(self, reference_slice, actual_slice, model,
                                         max_categories: int = 10,
                                         threshold: float = None,
                                         chi_square_contribution_percent: float = 0.2):
        """
        Test if the Chi Square value between the reference and actual datasets is below the threshold
        for the classification labels predictions for a given slice

        Example : The test is passed when the  Chi Square value of classification labels prediction
        for females between reference and actual sets is below 0.2

        Args:
            reference_slice(GiskardDataset):
                slice of the reference dataset 
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(GiskardModel):
                uploaded model
            max_categories:
                the maximum categories to compute the PSI score
            threshold:
                threshold value for p-value
            chi_square_contribution_percent:
                the ratio between the Chi-Square value of a given category over the total Chi-Square
                value of the categorical variable. If there is a drift, the test provides all the
                categories that have a PSI contribution over than this ratio.

        Returns:
            passed:
                TRUE if p_value > threshold
            metric:
                p-value of chi_square test
            messages:
                message describing if prediction is drifting or not

        """
        reference_slice = reference_slice.df.reset_index(drop=True)
        actual_slice = actual_slice.df.reset_index(drop=True)
        prediction_reference = pd.Series(model.run_predict(reference_slice).prediction)
        prediction_actual = pd.Series(model.run_predict(actual_slice).prediction)

        chi_square, p_value, output_data = self._calculate_chi_square(prediction_actual, prediction_reference,
                                                                      max_categories)

        passed = p_value > threshold
        messages: Union[typing.List[TestMessage], None] = None
        output_df_sample = None

        if not passed:
            main_drifting_modalities_bool = output_data["Chi_square"] > chi_square_contribution_percent * chi_square
            modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()

            filtered_modalities = [w for w in modalities_list if not re.match('^other_modalities_[a-z0-9]{32}$', w)]
            failed_df = actual_slice.loc[prediction_actual.isin(filtered_modalities)]

            output_df_sample = compress(save_df(failed_df))
            messages = [TestMessage(
                type=TestMessageType.ERROR,
                text=f"The prediction is drifting for the following modalities {*filtered_modalities,}"
            )]

        return self.save_results(SingleTestResult(
            passed=passed,
            metric=p_value,
            messages=messages,
            output_df=output_df_sample

        ))

    def test_drift_prediction_ks(self,
                                 reference_slice: GiskardDataset,
                                 actual_slice: GiskardDataset,
                                 model: GiskardModel,
                                 classification_label=None,
                                 threshold=None) -> SingleTestResult:
        """
        Test if the pvalue of the KS test for prediction between the reference and actual datasets for
         a given subpopulation is above the threshold

        Example : The test is passed when the pvalue of the KS test for the prediction for females
         between reference and actual dataset is higher than 0.05. It means that the KS test cannot be
         rejected at 5% level and that we cannot assume drift for this variable.

        Args:
            reference_slice(GiskardDataset):
                slice of the reference dataset 
            actual_slice(GiskardDataset):
                slice of the actual dataset 
            model(GiskardModel):
                uploaded model
            threshold:
                threshold for p-value Kolmogorov-Smirnov test
            classification_label:
                one specific label value from the target column for classification model

        Returns:
            passed:
                TRUE if p-value >= threshold
            metric:
                calculated p-value Kolmogorov-Smirnov test
            messages:
                Kolmogorov-Smirnov result message
        """
        assert model.model_type != "classification" or classification_label in model.classification_labels, \
            f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        prediction_reference = model.run_predict(reference_slice.df).all_predictions[classification_label].values if \
            model.model_type == "classification" else model.run_predict(reference_slice.df).prediction
        prediction_actual = model.run_predict(actual_slice.df).all_predictions[classification_label].values if \
            model.model_type == "classification" else model.run_predict(actual_slice.df).prediction

        result: Ks_2sampResult = self._calculate_ks(prediction_reference, prediction_actual)
        passed = True if threshold is None else result.pvalue >= threshold
        messages: Union[typing.List[TestMessage], None] = None
        if not passed:
            messages = [TestMessage(
                type=TestMessageType.ERROR,
                text=f"The prediction is drifting (pvalue is equal to {result.pvalue} and is below the test risk level {threshold}) "
            )]

        return self.save_results(SingleTestResult(
            passed=passed,
            metric=result.pvalue,
            messages=messages
        ))

    def test_drift_prediction_earth_movers_distance(self,
                                                    reference_slice: GiskardDataset,
                                                    actual_slice: GiskardDataset,
                                                    model: GiskardModel,
                                                    classification_label=None,
                                                    threshold=None) -> SingleTestResult:
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

        prediction_reference = model.run_predict(reference_slice.df).all_predictions[classification_label].values if \
            model.model_type == "classification" else model.run_predict(reference_slice.df).prediction
        prediction_actual = model.run_predict(actual_slice.df).all_predictions[classification_label].values if \
            model.model_type == "classification" else model.run_predict(actual_slice.df).prediction

        metric = self._calculate_earth_movers_distance(prediction_reference, prediction_actual)

        return self.save_results(SingleTestResult(
            passed=True if threshold is None else metric <= threshold,
            metric=metric,
        ))
