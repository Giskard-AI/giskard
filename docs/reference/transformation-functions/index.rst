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

.. autofunction:: giskard.functions.text_transformations.TextUppercase
.. autofunction:: giskard.functions.text_transformations.TextLowercase
.. autofunction:: giskard.functions.text_transformations.TextTitleCase
.. autofunction:: giskard.functions.text_transformations.TextTypoTransformation
.. autofunction:: giskard.functions.text_transformations.TextFromOCRTypoTransformation
.. autofunction:: giskard.functions.text_transformations.TextPunctuationRemovalTransformation
.. autofunction:: giskard.functions.text_transformations.TextGenderTransformation
.. autofunction:: giskard.functions.text_transformations.TextReligionTransformation
.. autofunction:: giskard.functions.text_transformations.TextNationalityTransformation
.. autofunction:: giskard.functions.text_transformations.TextFromSpeechTypoTransformation
.. autofunction:: giskard.functions.transformation.change_writing_style


Special transformations used by the scan
----------------------------------------

.. automodule:: giskard.functions.text_transformations
   :members:
   :show-inheritance:
