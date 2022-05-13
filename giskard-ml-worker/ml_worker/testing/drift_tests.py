import typing
import uuid
from collections import Counter
from typing import Union

import numpy as np
import pandas as pd
from ai_inspector import ModelInspector
from scipy.stats import chi2, ks_2samp
from scipy.stats.stats import Ks_2sampResult, wasserstein_distance

from generated.ml_worker_pb2 import SingleTestResult, TestMessage, TestMessageType
from ml_worker.core.ml import run_predict
from ml_worker.testing.abstract_test_collection import AbstractTestCollection


class DriftTests(AbstractTestCollection):
    @staticmethod
    def _calculate_psi(category, actual_distribution, expected_distribution):
        # To use log and avoid zero distribution probability,
        # we bound distribution probability by min_distribution_probability
        min_distribution_probability = 0.0001

        expected_distribution_bounded = max(expected_distribution[category], min_distribution_probability)
        actual_distribution_bounded = max(actual_distribution[category], min_distribution_probability)
        modality_psi = (expected_distribution_bounded - actual_distribution_bounded) * \
                       np.log(expected_distribution_bounded / actual_distribution_bounded)
        return modality_psi

    @staticmethod
    def _calculate_frequencies(actual_series, expected_series, max_categories):
        all_modalities = list(set(expected_series).union(set(actual_series)))
        if max_categories is not None and len(all_modalities) > max_categories:
            var_count_expected = dict(Counter(expected_series).most_common(max_categories))
            other_modalities_key = 'other_modalities_' + uuid.uuid1().hex
            var_count_expected[other_modalities_key] = len(expected_series) - sum(var_count_expected.values())
            categories_list = list(var_count_expected.keys())

            var_count_actual = Counter(actual_series)
            # For test data, we take the same category names as expected_data
            var_count_actual = {i: var_count_actual[i] for i in categories_list}
            var_count_actual[other_modalities_key] = len(actual_series) - sum(var_count_actual.values())

            all_modalities = categories_list
        else:
            var_count_expected = Counter(expected_series)
            var_count_actual = Counter(actual_series)
        expected_frequencies = np.array([var_count_expected[i] for i in all_modalities])
        actual_frequencies = np.array([var_count_actual[i] for i in all_modalities])
        return all_modalities, actual_frequencies, expected_frequencies

    @staticmethod
    def _calculate_drift_psi(actual_series, expected_series, max_categories):
        all_modalities, actual_frequencies, expected_frequencies = DriftTests._calculate_frequencies(
            actual_series, expected_series, max_categories)
        expected_distribution = expected_frequencies / len(expected_series)
        actual_distribution = actual_frequencies / len(actual_series)
        total_psi = 0
        output_data = pd.DataFrame(columns=["Modality", "Train_distribution", "Test_distribution", "Psi"])
        for category in range(len(all_modalities)):
            modality_psi = DriftTests._calculate_psi(category, actual_distribution, expected_distribution)

            total_psi += modality_psi
            row = {
                "Modality": all_modalities[category],
                "Train_distribution": expected_distribution[category],
                "Test_distribution": expected_distribution[category],
                "Psi": modality_psi
            }

            output_data = output_data.append(pd.Series(row), ignore_index=True)
        return total_psi, output_data

    @staticmethod
    def _calculate_ks(actual_series, expected_series) -> Ks_2sampResult:
        return ks_2samp(expected_series, actual_series)

    @staticmethod
    def _calculate_earth_movers_distance(actual_series, expected_series):
        unique_train = np.unique(expected_series)
        unique_test = np.unique(actual_series)
        sample_space = list(set(unique_train).union(set(unique_test)))
        val_max = max(sample_space)
        val_min = min(sample_space)
        if val_max == val_min:
            metric = 0
        else:
            # Normalizing expected_series and actual_series for comparison purposes
            expected_series = (expected_series - val_min) / (val_max - val_min)
            actual_series = (actual_series - val_min) / (val_max - val_min)

            metric = wasserstein_distance(expected_series, actual_series)
        return metric

    @staticmethod
    def _calculate_chi_square(actual_series, expected_series, max_categories):
        all_modalities, actual_frequencies, expected_frequencies = DriftTests._calculate_frequencies(
            actual_series, expected_series, max_categories)
        chi_square = 0
        # it's necessary for comparison purposes to normalize expected_frequencies
        # so that train and test has the same size
        # See https://github.com/scipy/scipy/blob/v1.8.0/scipy/stats/_stats_py.py#L6787
        k_norm = actual_series.shape[0] / expected_series.shape[0]
        output_data = pd.DataFrame(columns=["Modality", "Train_frequencies", "Test_frequencies", "Chi_square"])
        for i in range(len(all_modalities)):
            chi_square_value = (actual_frequencies[i] - expected_frequencies[i] * k_norm) ** 2 / (
                    expected_frequencies[i] * k_norm)
            chi_square += chi_square_value

            row = {"Modality": all_modalities[i],
                   "Train_frequencies": expected_frequencies[i],
                   "Test_frequencies": actual_frequencies[i],
                   "Chi_square": chi_square_value}

            output_data = output_data.append(pd.Series(row), ignore_index=True)
        # if expected_series and actual_series has only one modality it turns nan (len(all_modalities)=1)
        p_value = 1 - chi2.cdf(chi_square, len(all_modalities) - 1)
        return chi_square, p_value, output_data

    def test_drift_psi(self,
                       expected_series: pd.Series,
                       actual_series: pd.Series,
                       threshold=None,
                       max_categories: int = 10) -> SingleTestResult:
        """
              Compute the Population Stability Index (PSI) for a categorical variable between a train and test datasets
              See https://www.mdpi.com/2227-9091/7/2/53/htm
              Parameters
              ----------
              expected_series: pd.Series
                  A categorical column in train dataset
              actual_series: pd.Series
                  A categorical column in test dataset that is compared to var_expected
              max_categories: int = 10
                  Maximum number of modalities
              Returns
              -------
              total_psi
                  The PSI score
              output_data
                  Pandas dataframe giving frequencies and total_psi for each category
             """
        total_psi, _ = self._calculate_drift_psi(actual_series, expected_series, max_categories)

        return self.save_results(SingleTestResult(
            passed=True if threshold is None else total_psi <= threshold,
            metric=total_psi
        ))

    def test_drift_chi_square(self,
                              expected_series: pd.Series,
                              actual_series: pd.Series,
                              threshold=None,
                              p_value_threshold=None,
                              max_categories: int = 10) -> SingleTestResult:
        """
        Compute one-way chi square test (Goodness of fit test) for a categorical variable
        between a train and test datasets.
        The Null hypothesis is that the categorical variable in
        the test dataset has the same distribution as in train dataset
        See https://www.statisticshowto.com/goodness-of-fit-test/

        :param expected_series: A categorical column in train dataset
        :param actual_series: A categorical column in test dataset that is compared to var_expected
        :param threshold: A value that will be compared with the calculated chi square score
        :param p_value_threshold: A value that will be compared with the calculated p-value
        :param max_categories: Maximum number of modalities
        :return:
        """

        chi_square, p_value, _ = self._calculate_chi_square(actual_series, expected_series, max_categories)

        return self.save_results(SingleTestResult(
            passed=(threshold is None or chi_square <= threshold) and
                   (p_value_threshold is None or p_value <= p_value_threshold),
            metric=chi_square,
            props={"p_value": str(p_value)}
        ))

    def test_drift_ks(self,
                      expected_series: pd.Series,
                      actual_series: pd.Series,
                      threshold=None,
                      p_value_threshold=None) -> SingleTestResult:
        """
         Compute the the two-sample Kolmogorov-Smirnov test (goodness of fit)
         for a numerical variable between a train and test datasets

         References
         ----------
         .. [1] Hodges, J.L. Jr., “The Significance Probability of the Smirnov Two-Sample Test,” Arkiv fiur Matematik, 3, No. 43 (1958), 469-86.

        :param expected_series: Union[np.ndarray, pd.Series] A numerical column in train dataset
        :param actual_series: Union[np.ndarray, pd.Series]   A numerical column in test dataset that is compared to expected_series
        :param threshold: A value that will be compared with the calculated ks score
        :param p_value_threshold: A value that will be compared with the calculated p-value
        :return:
        """

        result = self._calculate_ks(actual_series, expected_series)

        return self.save_results(SingleTestResult(
            passed=(threshold is None or result.statistic <= threshold) and
                   (p_value_threshold is None or result.pvalue <= p_value_threshold),
            metric=result.statistic,
            props={"p_value": str(result.pvalue)})
        )

    def test_drift_earth_movers_distance(self,
                                         expected_series: Union[np.ndarray, pd.Series],
                                         actual_series: Union[np.ndarray, pd.Series],
                                         threshold: float = None) -> SingleTestResult:
        """
        Compute the Earth Mover's Distance (Wasserstein distance with moment equals to 1)
        for a numerical variable between a train and test datasets

        References
        ----------
        .. [1] "Wasserstein metric", https://en.wikipedia.org/wiki/Wasserstein_metric
        .. [2] Ramdas, Garcia, Cuturi "On Wasserstein Two Sample Testing and Related
               Families of Nonparametric Tests" (2015). :arXiv:`1509.02237`

        Parameters
        ----------
        expected_series : Union[np.ndarray, pd.Series]
            A numerical column in train dataset
        actual_series : Union[np.ndarray, pd.Series]
            A numerical column in test dataset that is compared to var_train

        Returns
        -------
        Any
            The computed Wasserstein distance between the two distributions.
        """
        metric = self._calculate_earth_movers_distance(actual_series, expected_series)
        return self.save_results(SingleTestResult(
            passed=True if threshold is None else metric <= threshold,
            metric=metric
        ))

    def test_drift_prediction_psi(self, train_df_slice: pd.DataFrame, test_df_slice: pd.DataFrame, model: ModelInspector,
                                  max_categories: int = 10, threshold: float = 0.2,
                                  psi_contribution_percent: float = 0.2):
        prediction_train = run_predict(train_df_slice, model).prediction
        prediction_test = run_predict(test_df_slice, model).prediction
        total_psi, output_data = self._calculate_drift_psi(prediction_train, prediction_test, max_categories)

        passed = True if threshold is None else total_psi <= threshold
        messages: Union[typing.List[TestMessage], None] = None
        if not passed:
            main_drifting_modalities_bool = output_data["Psi"] > psi_contribution_percent * total_psi
            modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()
            messages = [TestMessage(
                type=TestMessageType.ERROR,
                text=f"The prediction is drifting for the following modalities {*modalities_list,}"
            )]

        return self.save_results(SingleTestResult(
            passed=passed,
            metric=total_psi,
            messages=messages
        ))

    def test_drift_prediction_chi_square(self, train_df, test_df, model,
                                         max_categories: int = 10,
                                         threshold: float = None,
                                         chi_square_contribution_percent: float = 0.2):
        prediction_train = run_predict(train_df, model).prediction
        prediction_test = run_predict(test_df, model).prediction
        chi_square, p_value, output_data = self._calculate_chi_square(prediction_train, prediction_test, max_categories)

        passed = True if threshold is None else chi_square <= threshold
        messages: Union[typing.List[TestMessage], None] = None
        if not passed:
            main_drifting_modalities_bool = output_data["Chi_square"] > chi_square_contribution_percent * chi_square
            modalities_list = output_data[main_drifting_modalities_bool]["Modality"].tolist()
            messages = [TestMessage(
                type=TestMessageType.ERROR,
                text=f"The prediction is drifting for the following modalities {*modalities_list,}"
            )]

        return self.save_results(SingleTestResult(
            passed=passed,
            metric=chi_square,
            messages=messages
        ))

    def test_drift_prediction_ks(self,
                                 train_df: pd.DataFrame,
                                 test_df: pd.DataFrame,
                                 model: ModelInspector,
                                 threshold=None) -> SingleTestResult:
        prediction_train = run_predict(train_df, model).prediction
        prediction_test = run_predict(test_df, model).prediction
        result: Ks_2sampResult = self._calculate_ks(prediction_train, prediction_test)
        passed = True if threshold is None else result.statistic <= threshold
        messages: Union[typing.List[TestMessage], None] = None
        if not passed:
            messages = [TestMessage(
                type=TestMessageType.ERROR,
                text=f"The prediction is drifting (pvalue is equal to {result.pvalue} and is below the test risk level {threshold})"
            )]

        return self.save_results(SingleTestResult(
            passed=passed,
            metric=result.statistic,
            props={"p_value": str(result.pvalue)},
            messages=messages
        ))

    def test_drift_prediction_earth_movers_distance(self,
                                                    train_df: pd.DataFrame,
                                                    test_df: pd.DataFrame,
                                                    model: ModelInspector,
                                                    threshold=None) -> SingleTestResult:
        prediction_train = run_predict(train_df, model).prediction
        prediction_test = run_predict(test_df, model).prediction
        metric = self._calculate_earth_movers_distance(prediction_train, prediction_test)

        return self.save_results(SingleTestResult(
            passed=True if threshold is None else metric <= threshold,
            metric=metric,
        ))
