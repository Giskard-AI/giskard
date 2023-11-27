Automated model insights
========================

.. automodule:: giskard.push

.. autoclass:: giskard.push.Push

.. autoclass:: giskard.push.ExamplePush

.. autoclass:: giskard.push.FeaturePush

.. autoclass:: giskard.push.OverconfidencePush

.. autoclass:: giskard.push.BorderlinePush

.. autoclass:: giskard.push.ContributionPush

.. autoclass:: giskard.push.PerturbationPush


Automated model insights catalog
--------------------------------

.. autofunction:: giskard.push.push_test_catalog.catalog.test_diff_rmse_push
.. autofunction:: giskard.push.push_test_catalog.catalog.test_diff_f1_push
.. autofunction:: giskard.push.push_test_catalog.catalog.if_underconfidence_rate_decrease
.. autofunction:: giskard.push.push_test_catalog.catalog.if_overconfidence_rate_decrease
.. autofunction:: giskard.push.push_test_catalog.catalog.correct_example
.. autofunction:: giskard.push.push_test_catalog.catalog.increase_probability
.. autofunction:: giskard.push.push_test_catalog.catalog.one_sample_overconfidence_test
.. autofunction:: giskard.push.push_test_catalog.catalog.one_sample_underconfidence_test
.. autofunction:: giskard.push.push_test_catalog.catalog.test_metamorphic_invariance_with_mad