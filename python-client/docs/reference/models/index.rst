Models
============

Currently we only support ML models from:

- sklearn
- catboost
- pytorch
- tensorflow
- huggingface

We provide a factory method :class:`~.giskard.wrap_model` that wraps your ML model with the correct wrapper among:

- :class:`~giskard.SKLearnModel`
- :class:`~giskard.CatboostModel`
- :class:`~giskard.PyTorchModel`
- :class:`~giskard.TensorFlowModel`
- :class:`~giskard.HuggingFaceModel`

These are our predefined model wrappers:

.. autofunction:: giskard.wrap_model

.. autoclass:: giskard.SKLearnModel

.. autoclass:: giskard.CatboostModel

.. autoclass:: giskard.PyTorchModel

.. autoclass:: giskard.TensorFlowModel

.. autoclass:: giskard.HuggingFaceModel

These classes are based on the following base classes:

.. autoclass:: giskard.BaseModel

.. autoclass:: giskard.WrapperModel

.. autoclass:: giskard.MLFlowBasedModel

In order to create your custom wrapper you could use:

.. autoclass:: giskard.CustomModel