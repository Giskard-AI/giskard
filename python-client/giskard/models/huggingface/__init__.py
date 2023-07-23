import logging
from pathlib import Path
from typing import Union, Optional, Iterable, Any, Callable

import pandas as pd
import yaml
from scipy import special

from giskard.core.core import ModelType
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import WrapperModel

try:
    import torch
except ImportError as e:
    raise ImportError("Please install it via 'pip install torch'") from e

try:
    from transformers import pipeline, pipelines
except ImportError as e:
    raise ImportError("Please install it via 'pip install transformers'") from e

logger = logging.getLogger(__name__)


class HuggingFaceModel(WrapperModel):
    """
    A subclass of the WrapperModel class for using HuggingFace transformers.

    The HuggingFaceModel class is a wrapper around the HuggingFace transformers library.

    Inherits all attributes and methods from the WrapperModel class.

    Attributes:
        huggingface_module (Type): The type of the HuggingFace module used by the model.
        pipeline_task (str, optional): The task performed by the HuggingFace pipeline, if applicable.
    """

    @configured_validate_arguments
    def __init__(
            self,
            model,
            model_type: ModelType,
            name: Optional[str] = None,
            data_preprocessing_function: Callable[[pd.DataFrame], Any] = None,
            model_postprocessing_function: Callable[[Any], Any] = None,
            feature_names: Optional[Iterable] = None,
            classification_threshold: Optional[float] = 0.5,
            classification_labels: Optional[Iterable] = None,
            id: Optional[str] = None,
            **kwargs,
    ) -> None:
        """
        Initializes an instance of a HuggingFaceModel with the provided arguments and sets necessary attributes.

        Arguments:
            model: The model to be wrapped.
            model_type (ModelType): The type of the model, either regression or classification.
            name (str, optional): The name of the model.
            data_preprocessing_function (Callable[[pd.DataFrame], Any], optional): A function to preprocess the input data.
            model_postprocessing_function (Callable[[Any], Any], optional): A function to postprocess the model output.
            feature_names (Iterable, optional): The names of the model features.
            classification_threshold (float, optional): The classification probability threshold for binary classification models.
            classification_labels (Iterable, optional): The labels for classification models.

        Notes:
            huggingface_module (Type): The type of the HuggingFace module used by the model.
            pipeline_task (str, optional): The task performed by the HuggingFace pipeline, if applicable.
        """

        super().__init__(
            model=model,
            model_type=model_type,
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            id=id,
            **kwargs,
        )

        self.huggingface_module = model.__class__
        self.pipeline_task = model.task if isinstance(model, pipelines.Pipeline) else None

    @classmethod
    def load_model(cls, local_path):
        huggingface_meta_file = Path(local_path) / "giskard-model-huggingface-meta.yaml"
        if huggingface_meta_file.exists():
            with open(huggingface_meta_file) as f:
                huggingface_meta = yaml.load(f, Loader=yaml.Loader)

        if huggingface_meta["pipeline_task"]:
            return pipeline(huggingface_meta["pipeline_task"], local_path)

        return huggingface_meta["huggingface_module"].from_pretrained(local_path)

    def save_huggingface_meta(self, local_path):
        with open(Path(local_path) / "giskard-model-huggingface-meta.yaml", "w") as f:
            yaml.dump(
                {
                    "huggingface_module": self.huggingface_module,
                    "pipeline_task": self.pipeline_task,
                },
                f,
                default_flow_style=False,
            )

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)
        self.save_model(local_path)
        self.save_huggingface_meta(local_path)

    def save_model(self, local_path):
        self.model.save_pretrained(local_path)

    def model_predict(self, data):
        predictions = self._get_predictions(data)

        if self.is_classification and hasattr(predictions, "logits"):
            if isinstance(self.model, torch.nn.Module):
                with torch.no_grad():
                    logits = predictions.logits.detach().numpy()
            else:
                logits = predictions.logits

            if self.model_postprocessing_function:
                logger.warning(
                    "Your model output is logits. In Giskard, we expect the output to be probabilities."
                    "Since you provided a model_postprocessing_function, we assume that you included softmax() yourself.",
                    exc_info=True,
                )
            else:
                predictions = special.softmax(logits, axis=1) if len(logits.shape) == 2 else special.softmax(logits)

        return predictions

    def _get_predictions(self, data):
        if isinstance(self.model, torch.nn.Module):
            with torch.no_grad():
                return self.model(**data)

        if isinstance(self.model, pipelines.Pipeline):
            _predictions = [{p["label"]: p["score"] for p in pl} for pl in self.model(list(data), top_k=None)]
            return [[p[label] for label in self.meta.classification_labels] for p in _predictions]

        return self.model(**data)

    def to_mlflow(self, artifact_path: str = "transformers-model-from-giskard", **kwargs):
        import mlflow
        return mlflow.transformers.log_model(self.model, artifact_path, **kwargs)
