LLM tests
^^^^^^^^^^^^^^^^^^^^^

Injections
----------
.. autofunction:: giskard.testing.tests.llm.test_llm_char_injection
.. autofunction:: giskard.testing.tests.llm.test_llm_single_output_against_strings
.. autofunction:: giskard.testing.tests.llm.test_llm_output_against_strings

LLM-as-a-judge
--------------
.. autofunction:: giskard.testing.tests.llm.test_llm_output_coherency
.. autofunction:: giskard.testing.tests.llm.test_llm_output_plausibility
.. autofunction:: giskard.testing.tests.llm.test_llm_output_against_requirement_per_row
.. autofunction:: giskard.testing.tests.llm.test_llm_single_output_against_requirement
.. autofunction:: giskard.testing.tests.llm.test_llm_output_against_requirement

Ground Truth
--------------
.. autofunction:: giskard.testing.tests.llm.test_llm_ground_truth
.. autofunction:: giskard.testing.tests.llm.test_llm_ground_truth_similarity
