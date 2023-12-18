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
.. autofunction:: giskard.functions.transformation.uppercase_transformation
.. autofunction:: giskard.functions.transformation.lowercase_transformation
.. autofunction:: giskard.functions.transformation.strip_punctuation
.. autofunction:: giskard.functions.transformation.change_writing_style


Special transformations used by the scan
----------------------------------------

.. automodule:: giskard.scanner.robustness.text_transformations
   :members:
   :show-inheritance:
