Giskard Test Catalog
===================================

.. toctree::
    :maxdepth: 2
    :caption: Contents:
    :glob:
    :hidden:
    :numbered:
    :titlesonly:

Drift tests
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: giskard.test_drift_psi
.. autofunction:: giskard.test_drift_chi_square
.. autofunction:: giskard.test_drift_ks
.. autofunction:: giskard.test_drift_earth_movers_distance
.. autofunction:: giskard.test_drift_prediction_psi
.. autofunction:: giskard.test_drift_prediction_chi_square
.. autofunction:: giskard.test_drift_prediction_ks
.. autofunction:: giskard.test_drift_prediction_earth_movers_distance

Heuristic tests
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: giskard.test_right_label
.. autofunction:: giskard.test_output_in_range


Performance tests
^^^^^^^^^^^^^^^^^^^^^^^
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