Models
============

Currently we only support ML models from: :code:`sklearn`, :code:`catboost`, :code:`pytorch`, :code:`tensorflow` and :code:`huggingface`.
We provide a factory method :class:`~.giskard.wrap_model` that automatically wraps your ML model with the correct wrapper among:

- :class:`~giskard.SKLearnModel`
- :class:`~giskard.CatboostModel`
- :class:`~giskard.PyTorchModel`
- :class:`~giskard.TensorFlowModel`
- :class:`~giskard.HuggingFaceModel`

.. autofunction:: giskard.wrap_model

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

In order to create your custom wrapper you could use:

.. autoclass:: giskard.CustomModel

Here are some additional factory methods:

.. autofunction:: giskard.model_from_sklearn

.. autofunction:: giskard.model_from_catboost

.. autofunction:: giskard.model_from_pytorch

.. autofunction:: giskard.model_from_tensorflow

.. autofunction:: giskard.model_from_huggingface