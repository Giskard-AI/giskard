Test Catalog
============

Regression tests
------------------------------
Metamorphic tests
^^^^^^^^^^^^^^^^^^^^^
:func:`giskard.test_metamorphic_invariance`
:func:`giskard.test_metamorphic_increasing`
:func:`giskard.test_metamorphic_decreasing`

Statistical tests
^^^^^^^^^^^^^^^^^^^^^
:func:`giskard.test_output_in_range`


Performance tests
^^^^^^^^^^^^^^^^^^^^^
:func:`giskard.test_mae`
:func:`giskard.test_rmse`
:func:`giskard.test_diff_rmse`
:func:`giskard.test_diff_reference_actual_rmse`
:func:`giskard.test_r2`

Drift tests
^^^^^^^^^^^^^^^^^^^^^
:func:`giskard.test_drift_prediction_psi`
:func:`giskard.test_drift_prediction_chi_square`
:func:`giskard.test_drift_prediction_ks`
:func:`giskard.test_drift_prediction_earth_movers_distance`

Classification tests
------------------------------

Metamorphic tests
^^^^^^^^^^^^^^^^^^^^^
:func:`giskard.test_metamorphic_invariance`
:func:`giskard.test_metamorphic_increasing`
:func:`giskard.test_metamorphic_decreasing`
:func:`giskard.test_metamorphic_invariance_t_test`
:func:`giskard.test_metamorphic_increasing_t_test`
:func:`giskard.test_metamorphic_decreasing_t_test`
:func:`giskard.test_metamorphic_invariance_wilcoxon`
:func:`giskard.test_metamorphic_increasing_wilcoxon`
:func:`giskard.test_metamorphic_decreasing_wilcoxon`

Statistical tests
^^^^^^^^^^^^^^^^^^^^^
:func:`giskard.test_right_label`
:func:`giskard.test_output_in_range`
:func:`giskard.test_disparate_impact`

Performance tests
^^^^^^^^^^^^^^^^^^^^^
:func:`giskard.test_recall`
:func:`giskard.test_auc`
:func:`giskard.test_accuracy`
:func:`giskard.test_precision`
:func:`giskard.test_f1`
:func:`giskard.test_diff_recall`
:func:`giskard.test_diff_accuracy`
:func:`giskard.test_diff_precision`
:func:`giskard.test_diff_f1`
:func:`giskard.test_diff_reference_actual_accuracy`
:func:`giskard.test_diff_reference_actual_f1`

Drift tests
^^^^^^^^^^^^^^^^^^^^^
:func:`giskard.test_drift_psi`
:func:`giskard.test_drift_chi_square`
:func:`giskard.test_drift_ks`
:func:`giskard.test_drift_earth_movers_distance`
:func:`giskard.test_drift_prediction_psi`
:func:`giskard.test_drift_prediction_chi_square`
:func:`giskard.test_drift_prediction_ks`
:func:`giskard.test_drift_prediction_earth_movers_distance`

All tests
------------------------------

Metamorphic tests
^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: giskard.test_metamorphic_invariance
.. autofunction:: giskard.test_metamorphic_increasing
.. autofunction:: giskard.test_metamorphic_decreasing
.. autofunction:: giskard.test_metamorphic_decreasing_t_test
.. autofunction:: giskard.test_metamorphic_increasing_t_test
.. autofunction:: giskard.test_metamorphic_invariance_t_test
.. autofunction:: giskard.test_metamorphic_decreasing_wilcoxon
.. autofunction:: giskard.test_metamorphic_increasing_wilcoxon
.. autofunction:: giskard.test_metamorphic_invariance_wilcoxon

Statistical tests
^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: giskard.test_right_label
.. autofunction:: giskard.test_output_in_range
.. autofunction:: giskard.test_disparate_impact

Performance tests
^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: giskard.test_mae
.. autofunction:: giskard.test_rmse
.. autofunction:: giskard.test_recall
.. autofunction:: giskard.test_auc
.. autofunction:: giskard.test_accuracy
.. autofunction:: giskard.test_precision
.. autofunction:: giskard.test_f1
.. autofunction:: giskard.test_r2
.. autofunction:: giskard.test_diff_recall
.. autofunction:: giskard.test_diff_accuracy
.. autofunction:: giskard.test_diff_precision
.. autofunction:: giskard.test_diff_rmse
.. autofunction:: giskard.test_diff_f1
.. autofunction:: giskard.test_diff_reference_actual_rmse
.. autofunction:: giskard.test_diff_reference_actual_accuracy
.. autofunction:: giskard.test_diff_reference_actual_f1

Drift tests
^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: giskard.test_drift_psi
.. autofunction:: giskard.test_drift_chi_square
.. autofunction:: giskard.test_drift_ks
.. autofunction:: giskard.test_drift_earth_movers_distance
.. autofunction:: giskard.test_drift_prediction_psi
.. autofunction:: giskard.test_drift_prediction_chi_square
.. autofunction:: giskard.test_drift_prediction_ks
.. autofunction:: giskard.test_drift_prediction_earth_movers_distance