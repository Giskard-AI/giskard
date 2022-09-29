"""
Summary: Statistical tests to know if your perturbation follows your prior assumption

Description: You chose a type of perturbation: "Invariant", "Increasing" 
or "Decreasing". Then you apply the perturbation on your data and you run a test
to know if the results agree with the type of perturbation. 


Example : The test is passed when after replacing words by its synonyms, 
the equivalence test rejects the null hypothesis (the null hypothesis is that the mean
of the distributions is different).

Args:
    df(GiskardDataset):
        Dataset used to compute the test
    model(GiskardModel):
        Model used to compute the test

    type_perturbation(string): is the type of perturbation applied to the data "Increasing", "Decreasing" or "Invariant"

    perturbation_dict(dict):
        Dictionary of the perturbations. It provides the perturbed features as key
        and a perturbation lambda function as value

Returns:
 True if the assumption is satisfied
 False otherwise
"""

import scipy.stats
from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.testing.abstract_test_collection import AbstractTestCollection
from ml_worker.testing.utils import apply_perturbation_inplace
from ml_worker.core.giskard_dataset import GiskardDataset
from ml_worker.core.model import GiskardModel
import numpy as np
import pandas as pd 
import math


# Create your custom test
class CustomTest(AbstractTestCollection):

    def _perturb_and_predict(self,ds: GiskardDataset, model: GiskardModel, perturbation_dict, classification_label=0):
        """
        Returns the prediction of the perturbed dataframe
        """

        results_df = pd.DataFrame()
        results_df["prediction"] = model.run_predict(ds).all_predictions['0'].values
        modified_rows = apply_perturbation_inplace(ds.df, perturbation_dict)
        if len(modified_rows):
            ds.df = ds.df.iloc[modified_rows]
            results_df = results_df.iloc[modified_rows]

            results_df["perturbed_prediction"] = model.run_predict(ds).all_predictions[classification_label].values
        else:
            results_df["perturbed_prediction"] = results_df["prediction"]
        return results_df

    
    def paired_t_test_statistic(self, population_1:np.array, population_2:np.array):
        """
        Computes the test statistic of a paired t-test
    
        Inputs:
            - population_1, np.array 1D: an array of 1 dimension with the observations of 1st group
            - population_2, np.array 1D: an array of 1 dimension with the observations of 2nd group
    
        Output: the test statistic t
        """

        mean_diff = np.mean(population_1-population_2)
        s_diff = np.std(population_1-population_2)
        standard_errors = s_diff/math.sqrt(len(population_1))
   
        return mean_diff/standard_errors


    def paired_t_test(self, population_1, population_2, quantile=.05, type_="TWO"):
        """
        Computes the result of the paired t-test given 2 groups of observations and a level of significance
        """
    
        statistic = self.paired_t_test_statistic(population_1, population_2)
        if type_=="LEFT":
            "alternative shows pop_1<pop_2"
            p_value = scipy.stats.t.sf(-statistic, df=len(population_1)-1)
        elif type_=="RIGHT":
            "alternative shows pop_1>pop_2"
            p_value = scipy.stats.t.sf(statistic, df=len(population_1)-1)
        elif type_=="TWO":
            "alternative shows pop_1!=pop_2"
            p_value = scipy.stats.t.sf(abs(statistic), df=len(population_1)-1)*2
        else:
            raise Exception("Incorrect type! The type has to be one of the following: ['UPPER', 'LOWER', 'EQUAL']")
        print(p_value)
        #critical_value = paired_t_test_critical_value(threshold, len(population_1)-1, type)
        if p_value>quantile:
            return False, p_value
        else:
            return True, p_value

    def equivalence_t_test(self, population_1, population_2, threshold=0.05, quantile=0.05):
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
        if self.paired_t_test(population_1, population_2_low, quantile, type_="RIGHT") and self.paired_t_test(population_1, population_2_up, quantile, type_="LEFT"):
            print("null hypothesis rejected at a level of significance", quantile)
            return True, (self.paired_t_test(population_1, population_2_low, quantile, type_="RIGHT")[1] + self.paired_t_test(population_1, population_2_up, quantile, type_="LEFT")[1])/2
        else:
            print("not enough evidence to reject null hypothesis")
            return False, (self.paired_t_test(population_1, population_2_low, quantile, type_="RIGHT")[1] + self.paired_t_test(population_1, population_2_up, quantile, type_="LEFT")[1])/2


    def test_function(self,
                      df: GiskardDataset,
                      model, 
                      perturbation_dict, 
                      classification_label=0, 
                      perturbation_type="Invariant",
                      threshold=0.05) -> SingleTestResult:

        results_df = self._perturb_and_predict(df, model, perturbation_dict, classification_label)
        
        if perturbation_type=="Invariant":
            test = self.equivalence_t_test(results_df['prediction'].values, results_df['perturbed_prediction'])
            result = test[0]
            metric = test[1]
        elif perturbation_type == "Increasing":
            test = self.paired_t_test(results_df['prediction'].values, results_df['perturbed_prediction'], type_="LEFT")
            result = test[0]
            metric = test[1]
        elif perturbation_type == "Decreasing":
            test = self.paired_t_test(results_df['prediction'].values, results_df['perturbed_prediction'], type_="RIGHT")
            result = test[0]
            metric = test[1]
        else:
            raise Exception("Incorrect type! The type of perturbation has to be ['Invariant', 'Increasing', 'Decreasing']")

        if result:
                return self.save_results(
                SingleTestResult(
                passed=True,  # True if the test passed, False if the test failed
                metric=metric  # Metrics of your test
                )
                )
        else:
            return self.save_results(
            SingleTestResult(
            passed=False,  # True if the test passed, False if the test failed
            metric=0  # Metrics of your test
                )
                )


#################Helper Functions##########################################

def change_word(word, dict_):
  if word in dict_.keys():
    return dict_[word]
  else:
    return word

def transform_text(text, dict_):
  return " ".join(change_word(word, dict_) for word in text.split())
