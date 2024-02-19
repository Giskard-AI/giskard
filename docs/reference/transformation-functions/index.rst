.. _transformation_functions:

Transformation functions
========================

.. autofunction:: giskard.transformation_function

.. autoclass:: giskard.registry.transformation_function.TransformationFunction

   .. automethod:: execute
   .. automethod:: upload
   .. automethod:: download

Textual transformation functions
--------------------------------

.. autofunction:: giskard.functions.transformation.keyboard_typo_transformation
.. autofunction:: giskard.functions.transformation.text_uppercase
.. autofunction:: giskard.functions.transformation.text_lowercase
.. autofunction:: giskard.functions.transformation.text_title_case
.. autofunction:: giskard.functions.transformation.text_typo
.. autofunction:: giskard.functions.transformation.text_typo_from_ocr
.. autofunction:: giskard.functions.transformation.text_punctuation_removal
.. autofunction:: giskard.functions.transformation.text_accent_removal
.. autofunction:: giskard.functions.transformation.text_gender_switch
.. autofunction:: giskard.functions.transformation.text_number_to_word
.. autofunction:: giskard.functions.transformation.text_religion_switch
.. autofunction:: giskard.functions.transformation.text_nationality_switch
.. autofunction:: giskard.functions.transformation.text_typo_from_speech


Special transformations used by the scan
----------------------------------------

.. automodule:: giskard.scanner.robustness.text_transformations
   :members:
   :show-inheritance:
