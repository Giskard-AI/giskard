from ml_worker.testing.functions import GiskardTestFunctions
# flake8:noqa
import numpy as np
import pytest



@pytest.mark.parametrize('loc_pop, scale_pop, loc_perturb, scale_perturb, direction',
                         [(0.5, 0.5, 0, 1e-2, 'Invariant'),
                         (0.5, 0.5, 0.1, 0.1, 'Increasing'),
                         (0.5, 0.5, -0.1, 0.1, 'Decreasing')])
 
def test_metamorphic_compare_statistic_tests(loc_pop, scale_pop, loc_perturb, scale_perturb, direction):
      population = np.random.normal(loc_pop, scale_pop, size=100)
      perturbation = np.random.normal(loc_perturb, scale_perturb, size=100)
      print(perturbation)

      tests = GiskardTestFunctions()

      result_inc, p_value_inc = tests.metamorphic.paired_t_test(population, population+perturbation, type="LEFT")
      result_dec, p_value_dec = tests.metamorphic.paired_t_test(population, population+perturbation, type="RIGHT")
      result_inv, p_value_inv = tests.metamorphic.equivalence_t_test(population, population+perturbation)

      dict_mapping = {'Invariant': (result_inv, p_value_inv), 
                      'Decreasing':(result_dec, p_value_dec),
                      'Increasing':(result_inc, p_value_inc)}
      
      for key in dict_mapping.keys():
            print(f'key: {key} and p_value; {dict_mapping[key][1]}')
            if key == direction:
                  assert dict_mapping[key][1]<0.05
            else:
                  assert dict_mapping[key][1]>0.05
      return None








 









#def test_metamorphic_compare_probabilities(german_credit_test_data, german_credit_model):
#    assert _test_metamorphic_compare_probabilities(german_credit_test_data, german_credit_model)
    #assert _test_metamorphic_invariance_male_female_stat(german_credit_test_data, german_credit_model, 0.5)
