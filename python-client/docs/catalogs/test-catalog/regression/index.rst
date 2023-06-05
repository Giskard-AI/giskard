Regression tests
=================

- **Metamorphic tests**

  - :func:`~.giskard.testing.test_metamorphic_invariance`
  - :func:`~.giskard.testing.test_metamorphic_increasing`
  - :func:`~.giskard.testing.test_metamorphic_decreasing`

- **Statistical tests**

  - :func:`~.giskard.testing.test_output_in_range`

- **Performance tests**

  - :func:`~.giskard.testing.test_mae`
  - :func:`~.giskard.testing.test_rmse`
  - :func:`~.giskard.testing.test_diff_rmse`
  - :func:`~.giskard.testing.test_diff_reference_actual_rmse`
  - :func:`~.giskard.testing.test_r2`

- **Drift tests**

  - :func:`~.giskard.testing.test_drift_prediction_psi`
  - :func:`~.giskard.testing.test_drift_prediction_chi_square`
  - :func:`~.giskard.testing.test_drift_prediction_ks`
  - :func:`~.giskard.testing.test_drift_prediction_earth_movers_distance`
