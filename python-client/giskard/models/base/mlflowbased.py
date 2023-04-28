import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

import mlflow

from giskard import WrapperModel


class MLFlowBasedModel(WrapperModel, ABC):
    """
    An abstract base class for models that are serializable by the MLFlow library.

    This class provides functionality for saving the model with MLFlow in addition to saving other metadata with the
    `save` method. Subclasses should implement the `save_model` method to provide their own MLFlow-specific model
    saving functionality.
    """

    def save(self, local_path: Union[str, Path]) -> None:
        """
        MLFlow requires a target directory to be empty before the model is saved, thus we have to call
        save_with_mflow first and then save the rest of the metadata
        """
        if not self.id:
            self.id = uuid.uuid4()
        self.save_model(local_path, mlflow.models.Model(model_uuid=str(self.id)))
        super().save(local_path)

    @abstractmethod
    def save_model(self, local_path, mlflow_meta: mlflow.models.Model):
        ...
