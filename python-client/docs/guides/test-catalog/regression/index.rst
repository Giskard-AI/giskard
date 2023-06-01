Regression tests
=================

- **Metamorphic tests**

  - :func:`~.giskard.test_metamorphic_invariance`
  - :func:`~.giskard.test_metamorphic_increasing`
  - :func:`~.giskard.test_metamorphic_decreasing`

- **Statistical tests**

  - :func:`~.giskard.test_output_in_range`

- **Performance tests**

  - :func:`~.giskard.test_mae`
  - :func:`~.giskard.test_rmse`
  - :func:`~.giskard.test_diff_rmse`
  - :func:`~.giskard.test_diff_reference_actual_rmse`
  - :func:`~.giskard.test_r2`

- **Drift tests**

  - :func:`~.giskard.test_drift_prediction_psi`
  - :func:`~.giskard.test_drift_prediction_chi_square`
  - :func:`~.giskard.test_drift_prediction_ks`
  - :func:`~.giskard.test_drift_prediction_earth_movers_distance`
