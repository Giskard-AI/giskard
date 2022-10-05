import pandas as pd
# import time
# import logging
import numpy as np
import math
from generated.ml_worker_pb2 import SingleTestResult, TestMessage, TestMessageType
import scipy.stats


from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.core.model import GiskardModel
from ml_worker.testing.abstract_test_collection import AbstractTestCollection
from ml_worker.testing.utils import apply_perturbation_inplace
from ml_worker.utils.logging import timer


class MetamorphicTests(AbstractTestCollection):
    @staticmethod
    def _predict_numeric_result(ds: GiskardDataset, model: GiskardModel, output_proba=True, classification_label=None):
        if model.model_type == 'regression' or not output_proba:
            return model.run_predict(ds).raw_prediction
        elif model.model_type == 'classification' and classification_label is not None:
            return model.run_predict(ds).all_predictions[classification_label].values
        elif model.model_type == 'classification':
            return model.run_predict(ds).probabilities

    @staticmethod
    def _prediction_ratio(prediction, perturbed_prediction):
        return abs(perturbed_prediction - prediction) / prediction if prediction != 0 else abs(perturbed_prediction)

    @staticmethod
    def _perturb_and_predict(ds: GiskardDataset, model: GiskardModel, perturbation_dict, output_proba=True,
                             classification_label=None):
        results_df = pd.DataFrame()
        results_df["prediction"] = MetamorphicTests._predict_numeric_result(ds, model, output_proba,
                                                                            classification_label)
        modified_rows = apply_perturbation_inplace(ds.df, perturbation_dict)
        if len(modified_rows):
            ds.df = ds.df.iloc[modified_rows]
            results_df = results_df.iloc[modified_rows]
            results_df["perturbed_prediction"] = MetamorphicTests._predict_numeric_result(ds,
                                                                                          model,
                                                                                          output_proba,
                                                                                          classification_label)
        else:
            results_df["perturbed_prediction"] = results_df["prediction"]
        return results_df, len(modified_rows)

    @staticmethod
    def paired_t_test_statistic(population_1, population_2):
        """
        Computes the test statistic of a paired t-test
        
        Inputs:
            - population_1, np.array 1D: an array of 1 dimension with the observations of 1st group
            - population_2, np.array 1D: an array of 1 dimension with the observations of 2nd group
        
        Output: the test statistic t
        """

        mean_diff = np.mean(population_1 - population_2)
        s_diff = np.std(population_1 - population_2)
        standard_errors = s_diff / math.sqrt(len(population_1))
      
        return mean_diff / standard_errors

    def paired_t_test(self, population_1, population_2, quantile=.05, type="TWO"):
        """
        Computes the result of the paired t-test given 2 groups of observations and a level of significance
        """
        
        statistic = self.paired_t_test_statistic(population_1, population_2)
        if type == "LEFT":
            "alternative shows pop_1<pop_2"
            p_value = scipy.stats.t.sf(-statistic, df=len(population_1) - 1)
        elif type == "RIGHT":
            "alternative shows pop_1>pop_2"
            p_value = scipy.stats.t.sf(statistic, df=len(population_1) - 1)
        elif type == "TWO":
            "alternative shows pop_1!=pop_2"
            p_value = scipy.stats.t.sf(abs(statistic), df=len(population_1) - 1) * 2
        else:
            raise Exception("Incorrect type! The type has to be one of the following: ['UPPER', 'LOWER', 'EQUAL']")
        # critical_value = paired_t_test_critical_value(threshold, len(population_1)-1, type)
        if p_value > quantile:
            return False, p_value
        else:
            return True, p_value

    def equivalence_t_test(self, population_1, population_2, threshold=0.1, quantile=0.05):
        """
        Computes the equivalence test to show that mean 2 - threshold < mean 1 < mean 2 + threshold

        Inputs:
            - population_1, np.array 1D: an array of 1 dimension with the observations of 1st group
            - population_2, np.array 1D: an array of 1 dimension with the observations of 2nd group
            - threshold, float: small value that determines the maximal difference that can be between means
            - quantile, float: the level of significance, is the 1-q quantile of the distribution
        
        Output, bool: True if the null is rejected and False if there is not enough evidence
        """
        population_2_up = population_2 + threshold
        population_2_low = population_2 - threshold
        if self.paired_t_test(population_1, population_2_low, quantile, type="RIGHT") and\
           self.paired_t_test(population_1, population_2_up, quantile, type="LEFT"):
            
            print("null hypothesis rejected at a level of significance", quantile)
            return True, max(self.paired_t_test(population_1, population_2_low, quantile, type="RIGHT")[1],
                             self.paired_t_test(population_1, population_2_up, quantile, type="LEFT")[1])
        else:
            print("not enough evidence to reject null hypothesis")
            return False, max(self.paired_t_test(population_1, population_2_low, quantile, type="RIGHT")[1],
                              self.paired_t_test(population_1, population_2_up, quantile, type="LEFT")[1])

    @timer("Compare and predict the data")
    def _compare_prediction(self, results_df, prediction_task, output_sensitivity=None, flag=None):
        if flag == 'Invariance':
            if prediction_task == 'classification':
                passed_idx = results_df.loc[
                    results_df['prediction'] == results_df['perturbed_prediction']].index.values

            elif prediction_task == 'regression':
                results_df['predict_difference_ratio'] = results_df.apply(
                    lambda x: self._prediction_ratio(x["prediction"], x["perturbed_prediction"]), axis=1)
                passed_idx = results_df.loc[results_df['predict_difference_ratio'] < output_sensitivity].index.values

        elif flag == 'Increasing':
            passed_idx = results_df.loc[
                results_df['prediction'] < results_df['perturbed_prediction']].index.values

        elif flag == 'Decreasing':
            passed_idx = results_df.loc[
                results_df['prediction'] > results_df['perturbed_prediction']].index.values

        failed_idx = results_df.loc[~results_df.index.isin(passed_idx)].index.values
        return passed_idx, failed_idx

    def _compare_probabilities(self, result_df, flag=None):

        if flag == 'Invariance':
            p_value = self.equivalence_t_test(result_df['prediction'], result_df['perturbed_prediction'])[1]
      
        elif flag == 'Increasing':
            p_value = self.paired_t_test(result_df['prediction'], result_df['perturbed_prediction'], type='LEFT')[1]
      
        elif flag == 'Decreasing':
            p_value = self.paired_t_test(result_df['prediction'], result_df['perturbed_prediction'], type='RIGHT')[1]
      
        return p_value

    def _test_metamorphic(self,
                          flag,
                          actual_slice: GiskardDataset,
                          model,
                          perturbation_dict,
                          threshold: float,
                          classification_label=None,
                          output_sensitivity=None,
                          output_proba=True
                          ) -> SingleTestResult:
        actual_slice.df.reset_index(drop=True, inplace=True)

        results_df, modified_rows_count = self._perturb_and_predict(actual_slice,
                                                                    model,
                                                                    perturbation_dict,
                                                                    classification_label=classification_label,
                                                                    output_proba=output_proba)

        passed_idx, failed_idx = self._compare_prediction(results_df,
                                                          model.model_type,
                                                          output_sensitivity,
                                                          flag)
        passed_ratio = len(passed_idx) / modified_rows_count if modified_rows_count != 0 else 1

        messages = [TestMessage(
            type=TestMessageType.INFO,
            text=f"{modified_rows_count} rows were perturbed"
        )]

        return self.save_results(SingleTestResult(
            actual_slices_size=[len(actual_slice)],
            metric=passed_ratio,
            passed=passed_ratio > threshold,
            messages=messages))

    def test_metamorphic_invariance(self,
                                    df: GiskardDataset,
                                    model,
                                    perturbation_dict,
                                    threshold=0.5,
                                    output_sensitivity=None) -> SingleTestResult:
        """
        Summary: Tests if the model prediction is invariant when the feature values are perturbed

        Description: -
        For classification: Test if the predicted classification label remains the same after
        feature values perturbation.
        For regression: Check whether the predicted output remains the same at the output_sensibility
        level after feature values perturbation.

        The test is passed when the ratio of invariant rows is higher than the threshold

        Example : The test is passed when, after switching gender from male to female,
        more than 50%(threshold 0.5) of males have unchanged outputs

        Args:
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            threshold(float):
              Threshold of the ratio of invariant rows
            output_sensitivity(float):
                Optional. The threshold for ratio between the difference between perturbed prediction and
                actual prediction over
                the actual prediction for a regression model. We consider there is a prediction difference for
                regression if the ratio is above the output_sensitivity of 0.1

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of unchanged rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """

        return self._test_metamorphic(flag='Invariance',
                                      actual_slice=df,
                                      model=model,
                                      perturbation_dict=perturbation_dict,
                                      threshold=threshold,
                                      output_sensitivity=output_sensitivity,
                                      output_proba=False
                                      )

    def test_metamorphic_increasing(self,
                                    df: GiskardDataset,
                                    model,
                                    perturbation_dict,
                                    threshold=0.5,
                                    classification_label=None):
        """
        Summary: Tests if the model probability increases when the feature values are perturbed

        Description: -
        - For classification: Test if the model probability of a given classification_label is
        increasing after feature values perturbation.

        - For regression: Test if the model prediction is increasing after feature values perturbation.

        The test is passed when the percentage of rows that are increasing is higher than the threshold

        Example : For a credit scoring model, the test is passed when a decrease of wage by 10%,
         default probability is increasing for more than 50% of people in the dataset

        Args:
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            threshold(float):
              Threshold of the ratio of increasing rows
            classification_label(str):
              Optional.One specific label value from the target column

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of increasing rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """
        assert model.model_type != "classification" or str(classification_label) in model.classification_labels, \
            f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic(flag='Increasing',
                                      actual_slice=df,
                                      model=model,
                                      perturbation_dict=perturbation_dict,
                                      classification_label=classification_label,
                                      threshold=threshold)

    def test_metamorphic_decreasing(self,
                                    df: GiskardDataset,
                                    model,
                                    perturbation_dict,
                                    threshold=0.5,
                                    classification_label=None
                                    ):
        """
        Summary: Tests if the model probability decreases when the feature values are perturbed

        Description: -
        - For classification: Test if the model probability of a given classification_label is
        decreasing after feature values perturbation.

        - For regression: Test if the model prediction is decreasing after feature values perturbation.

        The test is passed when the percentage of rows that are decreasing is higher than the threshold

        Example : For a credit scoring model, the test is passed when an increase of wage by 10%,
         default probability is decreasing for more than 50% of people in the dataset

        Args:
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            threshold(float):
              Threshold of the ratio of decreasing rows
            classification_label(str):
              Optional. One specific label value from the target column

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of decreasing rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """

        assert model.model_type != "classification" or classification_label in model.classification_labels, \
            f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic(flag='Decreasing',
                                      actual_slice=df,
                                      model=model,
                                      perturbation_dict=perturbation_dict,
                                      classification_label=classification_label,
                                      threshold=threshold)
    
    def _test_metamorphic_stat(self,
                               flag,
                               actual_slice: GiskardDataset,
                               model,
                               perturbation_dict,
                               threshold: float,
                               classification_label=None,
                               output_proba=True
                               ) -> SingleTestResult:
      
        actual_slice.df.reset_index(drop=True, inplace=True)
      
        result_df, modified_rows_count = self._perturb_and_predict(actual_slice,
                                                                   model,
                                                                   perturbation_dict,
                                                                   output_proba=output_proba,
                                                                   classification_label=classification_label)
        
        p_value = self._compare_probabilities(result_df, flag)

        messages = [TestMessage(
            type=TestMessageType.INFO,
            text=f"{modified_rows_count} rows were perturbed"
        )]

        return self.save_results(SingleTestResult(
            actual_slices_size=[len(actual_slice)],
            metric=p_value,
            passed=p_value < threshold,
            messages=messages))

    def test_metamorphic_decreasing_stat(self,
                                         df: GiskardDataset,
                                         model,
                                         perturbation_dict,
                                         threshold=0.05,
                                         classification_label=None
                                         ):
        """
        Summary: Tests if the model probability decreases when the feature values are perturbed

        Description: -
        - For classification: Test if the model probability of a given classification_label is
        decreasing after feature values perturbation.

        - For regression: Test if the model prediction is decreasing after feature values perturbation.

        The test is passed when the percentage of rows that are decreasing is higher than the threshold

        Example : For a credit scoring model, the test is passed when an increase of wage by 10%,
         default probability is decreasing for more than 50% of people in the dataset

        Args:
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            threshold(float):
              Threshold of the ratio of decreasing rows
            classification_label(str):
              Optional. One specific label value from the target column

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of decreasing rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """

        assert model.model_type != "classification" or classification_label in model.classification_labels, \
            f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic_stat(flag='Decreasing',
                                           actual_slice=df,
                                           model=model,
                                           perturbation_dict=perturbation_dict,
                                           classification_label=classification_label,
                                           threshold=threshold)
   
    def test_metamorphic_increasing_stat(self,
                                         df: GiskardDataset,
                                         model,
                                         perturbation_dict,
                                         threshold=0.05,
                                         classification_label=None
                                         ):
        """
        Summary: Tests if the model probability decreases when the feature values are perturbed

        Description: -
        - For classification: Test if the model probability of a given classification_label is
        decreasing after feature values perturbation.

        - For regression: Test if the model prediction is decreasing after feature values perturbation.

        The test is passed when the percentage of rows that are decreasing is higher than the threshold

        Example : For a credit scoring model, the test is passed when an increase of wage by 10%,
         default probability is decreasing for more than 50% of people in the dataset

        Args:
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            threshold(float):
              Threshold of the ratio of decreasing rows
            classification_label(str):
              Optional. One specific label value from the target column

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of decreasing rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """

        assert model.model_type != "classification" or classification_label in model.classification_labels, \
            f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic_stat(flag='Increasing',
                                           actual_slice=df,
                                           model=model,
                                           perturbation_dict=perturbation_dict,
                                           classification_label=classification_label,
                                           threshold=threshold)

    def test_metamorphic_invariance_stat(self,
                                         df: GiskardDataset,
                                         model,
                                         perturbation_dict,
                                         threshold=0.05,
                                         classification_label=None
                                         ):
        """
        Summary: Tests if the model probability decreases when the feature values are perturbed

        Description: -
        - For classification: Test if the model probability of a given classification_label is
        decreasing after feature values perturbation.

        - For regression: Test if the model prediction is decreasing after feature values perturbation.

        The test is passed when the percentage of rows that are decreasing is higher than the threshold

        Example : For a credit scoring model, the test is passed when an increase of wage by 10%,
         default probability is decreasing for more than 50% of people in the dataset

        Args:
            df(GiskardDataset):
              Dataset used to compute the test
            model(GiskardModel):
              Model used to compute the test
            perturbation_dict(dict):
              Dictionary of the perturbations. It provides the perturbed features as key
              and a perturbation lambda function as value
            threshold(float):
              Threshold of the ratio of decreasing rows
            classification_label(str):
              Optional. One specific label value from the target column

        Returns:
            actual_slices_size:
              Length of actual_slice tested
            message:
              Test result message
            metric:
              The ratio of decreasing rows over the perturbed rows
            passed:
              TRUE if metric > threshold
        """

        assert model.model_type != "classification" or classification_label in model.classification_labels, \
            f'"{classification_label}" is not part of model labels: {",".join(model.classification_labels)}'

        return self._test_metamorphic(flag='Invariance',
                                      actual_slice=df,
                                      model=model,
                                      perturbation_dict=perturbation_dict,
                                      classification_label=classification_label,
                                      threshold=threshold)









