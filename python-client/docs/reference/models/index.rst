Model
============

We provide a :class:`~.giskard.Model` class that automatically wraps your ML model:

.. autoclass:: giskard.Model

   .. automethod:: __new__
   .. automethod:: is_classification
   .. automethod:: is_binary_classification
   .. automethod:: is_regression
   .. automethod:: is_generative
   .. automethod:: model_predict
   .. automethod:: predict
   .. automethod:: save_model
   .. automethod:: load_model
   .. automethod:: upload
   .. automethod:: download

.. autoclass:: giskard.models.base.ModelPredictionResults
