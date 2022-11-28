import numpy as np
import scipy.stats as stats

def paired_t_test(population_1, population_2, alternative, critical_quantile):
    """
    Computes the result of the paired t-test given 2 groups of observations and a level of significance

    p_value > quantile ==> we support the null hypothesis
    p_value < quantile ==> we support the alternative hypothesis

    less ==> alternative: mean(pop1) < mean(pop2)
    greater ==> alternative: mean(pop1) > mean(pop2)
    """

    if alternative not in ["less", "greater"]:
        raise ValueError("Incorrect alternative hypothesis! It has to be one of the following: ['less', 'greater']")

    if np.array_equal(population_1, population_2):
        p_value = 1.
    else:
        _, p_value = stats.ttest_rel(population_1, population_2, alternative=alternative)

    return p_value <= critical_quantile, p_value

def equivalence_t_test(population_1, population_2, window_size, critical_quantile):
    """
    Computes the equivalence test to show that mean 2 - window_size/2 < mean 1 < mean 2 + window_size/2

    Inputs:
        - population_1, np.array 1D: an array of 1 dimension with the observations of 1st group
        - population_2, np.array 1D: an array of 1 dimension with the observations of 2nd group
        - window_size, float: small value that determines the maximal difference that can be between means
        - critical_quantile, float: the level of significance, is the 1-q quantile of the distribution
    
    Output, bool: True if the null is rejected and False if there is not enough evidence
    """
    population_2_up = population_2 + window_size/2.
    population_2_low = population_2 - window_size/2.

    if np.array_equal(population_1, population_2):
        p_value_low, p_value_up = 0., 0.
    else:
        p_value_up = stats.ttest_rel(population_1, population_2_up, alternative="less")[1]
        p_value_low = stats.ttest_rel(population_1, population_2_low, alternative="greater")[1]

    test_up = p_value_up < critical_quantile
    test_low = p_value_low < critical_quantile

    if test_low and test_up:
        print("null hypothesis rejected at a level of significance", critical_quantile)
        return True, max(p_value_low, p_value_up)
    else:
        print("not enough evidence to reject null hypothesis")
        return False, max(p_value_low, p_value_up)


def paired_wilcoxon(population_1, population_2, alternative, critical_quantile):
    """
    Computes the result of the Wilcoxon rank-sum given 2 groups of observations and a level of significance

    p_value > quantile ==> we support the null hypothesis
    p_value < quantile ==> we support the alternative hypothesis

    less ==> alternative: mean(pop1) < mean(pop2)
    greater ==> alternative: mean(pop1) > mean(pop2)
    """

    if alternative not in ["less", "greater"]:
        raise ValueError(
            "Incorrect alternative hypothesis! It has to be one of the following: ['less', 'greater']")

    if np.array_equal(population_1, population_2):
        p_value = 1.
    else:
        _, p_value = stats.wilcoxon(population_1, population_2, alternative=alternative)

    return p_value <= critical_quantile, p_value


def equivalence_wilcoxon(population_1, population_2, window_size, critical_quantile):
    """
    Computes the equivalence test to show that mean 2 - window_size/2 < mean 1 < mean 2 + window_size/2

    Inputs:
        - population_1, np.array 1D: an array of 1 dimension with the observations of 1st group
        - population_2, np.array 1D: an array of 1 dimension with the observations of 2nd group
        - threshold, float: small value that determines the maximal difference that can be between means
        - quantile, float: the level of significance, is the 1-q quantile of the distribution

    Output, bool: True if the null is rejected and False if there is not enough evidence
    """
    population_2_up = population_2 + window_size/2.
    population_2_low = population_2 - window_size/2.

    if np.array_equal(population_1, population_2):
        p_value_low, p_value_up = 0., 0.
    else:
        p_value_up = stats.wilcoxon(population_1, population_2_up, alternative="less")[1]
        p_value_low = stats.wilcoxon(population_1, population_2_low, alternative="greater")[1]

    test_up = p_value_up < critical_quantile
    test_low = p_value_low < critical_quantile

    if test_low and test_up:
        print("null hypothesis rejected at a level of significance", critical_quantile)
        return True, max(p_value_low, p_value_up)
    else:
        print("not enough evidence to reject null hypothesis")
        return False, max(p_value_low, p_value_up)