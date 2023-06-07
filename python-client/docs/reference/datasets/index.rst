Dataset
============
Currently we only support **tabular** or **NLP** data types. Your data must be based on a :code:`pandas.DataFrame` and wrapped
with our own :class:`~.giskard.Dataset` class.

.. autoclass:: giskard.Dataset

   .. automethod:: __init__
   .. automethod:: _infer_column_types
   .. automethod:: add_slicing_function
   .. automethod:: add_transformation_function
   .. automethod:: slice
   .. automethod:: transform
   .. automethod:: process
   .. automethod:: upload
   .. automethod:: download