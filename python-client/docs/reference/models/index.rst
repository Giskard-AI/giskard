Models
============

We provide a :class:`~.giskard.Model` class that automatically wraps your ML model with the correct wrapper among:

- :class:`~giskard.SKLearnModel`
- :class:`~giskard.CatboostModel`
- :class:`~giskard.PyTorchModel`
- :class:`~giskard.TensorFlowModel`
- :class:`~giskard.HuggingFaceModel`
- :class:`~giskard.CloudpickleBasedModel` (abstract class in case of fall-back).

.. autoclass:: giskard.Model

   .. automethod:: __new__

These are our predefined model wrappers:

.. autoclass:: giskard.SKLearnModel

   .. automethod:: __init__
   .. automethod:: predict
   .. automethod:: download
   .. automethod:: upload

.. autoclass:: giskard.CatboostModel

   .. automethod:: __init__
   .. automethod:: predict
   .. automethod:: download
   .. automethod:: upload

.. autoclass:: giskard.PyTorchModel

   .. automethod:: __init__
   .. automethod:: predict
   .. automethod:: download
   .. automethod:: upload

.. autoclass:: giskard.TensorFlowModel

   .. automethod:: __init__
   .. automethod:: predict
   .. automethod:: download
   .. automethod:: upload

.. autoclass:: giskard.HuggingFaceModel

   .. automethod:: __init__
   .. automethod:: predict
   .. automethod:: download
   .. automethod:: upload

These classes are based on the following base classes:

.. autoclass:: giskard.BaseModel
   .. automethod:: prepare_dataframe
   .. automethod:: predict_df
   .. automethod:: predict
   .. automethod:: predict
   .. automethod:: download
   .. automethod:: upload


.. autoclass:: giskard.WrapperModel

   .. automethod:: __init__
   .. automethod:: predict
   .. automethod:: download
   .. automethod:: upload

.. autoclass:: giskard.MLFlowBasedModel

   .. automethod:: __init__
   .. automethod:: predict
   .. automethod:: download
   .. automethod:: upload

.. autoclass:: giskard.CloudpickleBasedModel

   .. automethod:: __init__
   .. automethod:: save_model
   .. automethod:: load_model

In order to create your custom wrapper you could use:

.. autoclass:: giskard.Model (if your prediction function involves a :code:`model` object)
.. autoclass:: giskard.CustomModel (if your prediction function does not involves a :code:`model` object)