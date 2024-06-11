from typing import Optional, Tuple, Union

from pathlib import Path

import cloudpickle

from giskard.exceptions.giskard_exception import python_env_exception_helper

from ...registry.utils import dump_by_value
from .wrapper import WrapperModel

# @TODO: decouple the serialization logic from models. These abstract classes
# could be implemented as mixins and then used in the models that need them.
# The logic of saving the model should be moved to the serialization classes.


class MLFlowSerializableModel(WrapperModel):
    """A base class to serialize models with MLFlow.

    This class provides functionality for saving the model with MLFlow in
    addition to saving other metadata with the `save` method. Subclasses should
    implement the `save_model` method to provide their own MLFlow-specific model
    saving functionality.
    """

    def save(self, local_path: Union[str, Path], *args, **kwargs) -> None:
        import mlflow

        # MLFlow requires the target directory to be empty before the model is
        # saved, thus we have to call ``save_model`` first and then save the
        # rest of the metadata.
        self.save_model(local_path, mlflow.models.Model(model_uuid=str(self.id)), *args, **kwargs)
        super().save(local_path, *args, **kwargs)


class CloudpickleSerializableModel(WrapperModel):
    """A base class for models that are serializable by cloudpickle."""

    def save(self, local_path: Union[str, Path], *args, **kwargs) -> None:
        super().save(local_path, *args, **kwargs)
        self.save_model(local_path, *args, **kwargs)

    def save_model(self, local_path: Union[str, Path], *args, **kwargs) -> None:
        try:
            model_file = Path(local_path) / "model.pkl"
            with open(model_file, "wb") as f:
                dump_by_value(self.model, f, kwargs.get("should_register_by_reference", False))
        except ValueError:
            raise ValueError(
                "We couldn't save your model with cloudpickle. Please provide us with your own "
                "serialisation method by overriding the save_model() and load_model() methods."
            )

    @classmethod
    def load_model(cls, local_dir, model_py_ver: Optional[Tuple[str, str, str]] = None, *args, **kwargs):
        local_path = Path(local_dir)
        model_path = local_path / "model.pkl"
        if model_path.exists():
            with open(model_path, "rb") as f:
                try:
                    # According to https://github.com/cloudpipe/cloudpickle#cloudpickle:
                    # Cloudpickle can only be used to send objects between the exact same version of Python.
                    model = cloudpickle.load(f)
                except Exception as e:
                    raise python_env_exception_helper(cls.__name__, e, required_py_ver=model_py_ver)
                return model
        else:
            raise ValueError(
                "We couldn't load your model with cloudpickle. Please provide us with your own "
                "serialisation method by overriding the save_model() and load_model() methods."
            )
