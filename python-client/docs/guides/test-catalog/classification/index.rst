Classification tests
------------------------------

- **Metamorphic tests**

  - :func:`~.giskard.test_metamorphic_invariance`
  - :func:`~.giskard.test_metamorphic_increasing`
  - :func:`~.giskard.test_metamorphic_decreasing`
  - :func:`~.giskard.test_metamorphic_invariance_t_test`
  - :func:`~.giskard.test_metamorphic_increasing_t_test`
  - :func:`~.giskard.test_metamorphic_decreasing_t_test`
  - :func:`~.giskard.test_metamorphic_invariance_wilcoxon`
  - :func:`~.giskard.test_metamorphic_increasing_wilcoxon`
  - :func:`~.giskard.test_metamorphic_decreasing_wilcoxon`

- **Statistical tests**

  - :func:`~.giskard.test_right_label`
  - :func:`~.giskard.test_output_in_range`
  - :func:`~.giskard.test_disparate_impact`

- **Performance tests**

  - :func:`~.giskard.test_recall`
  - :func:`~.giskard.test_auc`
  - :func:`~.giskard.test_accuracy`
  - :func:`~.giskard.test_precision`
  - :func:`~.giskard.test_f1`
  - :func:`~.giskard.test_diff_recall`
  - :func:`~.giskard.test_diff_accuracy`
  - :func:`~.giskard.test_diff_precision`
  - :func:`~.giskard.test_diff_f1`
  - :func:`~.giskard.test_diff_reference_actual_accuracy`
  - :func:`~.giskard.test_diff_reference_actual_f1`

- **Drift tests**

  - :func:`~.giskard.test_drift_psi`
  - :func:`~.giskard.test_drift_chi_square`
  - :func:`~.giskard.test_drift_ks`
  - :func:`~.giskard.test_drift_earth_movers_distance`
  - :func:`~.giskard.test_drift_prediction_psi`
  - :func:`~.giskard.test_drift_prediction_chi_square`
  - :func:`~.giskard.test_drift_prediction_ks`
  - :func:`~.giskard.test_drift_prediction_earth_movers_distance`