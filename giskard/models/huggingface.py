"""
This module provides a wrapper for HuggingFace models that allows them to be
used with Giskard. It supports both standard models from the ``transfomers``
library (for example pretrained models like ``AutoModel.from_pretrained(...)``),
as well as pipelines (e.g. ``pipeline("sentiment-analysis")``).


Quickstart
----------

Let’s load a pretrained model from HuggingFace ``transformers``:

>>> from transformers import AutoModelForSequenceClassification, AutoTokenizer
>>> model = AutoModelForSequenceClassification.from_pretrained(
...     "distilbert-base-uncased-finetuned-sst-2-english"
... )
>>> tokenizer = AutoTokenizer.from_pretrained(
...     "distilbert-base-uncased-finetuned-sst-2-english"
... )

Now we can wrap the model with Giskard:

>>> import giskard as gsk
>>> gsk_model = gsk.Model(
...     model=model,
...     model_type="classification",
...     name="DistilBERT SST-2",
...     data_preprocessing_function=lambda df: tokenizer(
...         df["text"].tolist(),
...         padding=True,
...         truncation=True,
...         max_length=512,
...         return_tensors="pt",
...     ),
...     feature_names=["text"],
...     classification_labels=["negative", "positive"],
...     batch_size=32,  # set the batch size here to speed up inference on GPU
... )

>>> type(gsk_model)
<class 'giskard.models.huggingface.HuggingFaceModel'>

Notice how using :class:`giskard.Model` automatically detected that we are using
a HuggingFace model and returned the correct subclass. You can also provide the
class explicitly using :class:`giskard.models.huggingface.HuggingFaceModel`.

Let’s create a simple dataset to test the model execution:

>>> import pandas as pd
>>> gsk_dataset = gsk.Dataset(
...     pd.DataFrame({"text": ["I hate this movie", "I love this movie"]})
... )
>>> gsk_model.predict(gsk_dataset)
ModelPredictionResults(...)

Optimizing performance
----------------------

Setting an appropriate batch size can significantly improve the model
performance on inference through ``gsk_model.predict(...)``. There is no general
way to optimize the batch size, as it depends on the model, the data, and the
hardware used. However, we recommend to start with a small batch size and
increase it as long as you can measure a speed up or you encounter not
out-of-memory errors::

    import time
    import giskard
    from giskard.models.huggingface import HuggingFaceModel

    wrapped_model = HuggingFaceModel(...)
    wrapped_dataset = giskard.Dataset(...)

    with giskard.models.cache.no_cache():
        for batch_size in [1, 2, 4, 8, 16, 32, 64, 128]:
            wrapped_model.batch_size = batch_size

            start = time.perf_counter()
            wrapped_model.predict(wrapped_dataset)
            elapsed = time.perf_counter() - start

            print(f"Batch size: {batch_size}, Inference time: {elapsed} seconds")


Expected model output
---------------------

An important thing to notice is that Giskard expects classification models to
return probabilities for each class. HuggingFace models usually return logits
instead of probabilities. In general, we will handle this for you by applying a
softmax function to the logits. However, if you are using a model that deviates
from this behavior, you can provide a custom postprocessing function using
the `model_postprocessing_function` argument. This function should take the
raw output of your model and return a numpy array of probabilities.
"""
from typing import Any, Callable, Iterable, Optional, Tuple, Union

import logging
from pathlib import Path

import pandas as pd
import yaml
from scipy import special

from giskard.core.core import ModelType
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import WrapperModel

from ..client.python_utils import warning

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
    @configured_validate_arguments
    def __init__(
        self,
        model,
        model_type: ModelType,
        name: Optional[str] = None,
        data_preprocessing_function: Optional[Callable[[pd.DataFrame], Any]] = None,
        model_postprocessing_function: Optional[Callable[[Any], Any]] = None,
        feature_names: Optional[Iterable] = None,
        classification_threshold: Optional[float] = 0.5,
        classification_labels: Optional[Iterable] = None,
        id: Optional[str] = None,
        batch_size: Optional[int] = 1,
        **kwargs,
    ) -> None:
        """Automatically wraps a HuggingFace model or pipeline.

        This class provides a default wrapper around the HuggingFace
        ``transformers`` library for usage with Giskard.

        Parameters
        ----------
        model : object
            The model instance to be wrapped. Should be an instance of a HuggingFace model or pipeline
            (e.g. from the ``transformers`` library).
        model_type : ModelType
            The type of the model, either ``regression`` or ``classification``.
        name : Optional[str]
            The name of the model, used in the Giskard UI.
        data_preprocessing_function : Optional[callable]
            A function to preprocess the input data.
        model_postprocessing_function : Optional[callable]
            A function to postprocess the model output.
        feature_names : Optional[iterable]
            The names of the model features.
        classification_threshold : Optional[float]
            The classification probability threshold for binary classification models.
        classification_labels : Optional[iterable]
            The labels for classification models.
        batch_size : Optional[int]
            The batch size used for inference. Default to 1. We recommend to increase the batch size to improve
            performance, but your mileage may vary. See *Notes* for more information.

        Attributes
        ----------
        batch_size : Optional[int]
            The batch size used for inference.
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
            batch_size=batch_size,
            **kwargs,
        )

        self.huggingface_module = model.__class__
        self.pipeline_task = model.task if isinstance(model, pipelines.Pipeline) else None

        try:
            if batch_size == 1 and model.device.type == "cuda":
                warning(
                    "Your model is running on GPU. We recommend to set a batch "
                    "size greater than 1 to improve performance."
                )
        except AttributeError:
            pass

    @classmethod
    def load_model(cls, local_path, model_py_ver: Optional[Tuple[str, str, str]] = None, *args, **kwargs):
        huggingface_meta_file = Path(local_path) / "giskard-model-huggingface-meta.yaml"
        if huggingface_meta_file.exists():
            with open(huggingface_meta_file) as f:
                huggingface_meta = yaml.load(f, Loader=yaml.Loader)

        if huggingface_meta["pipeline_task"]:
            return pipeline(huggingface_meta["pipeline_task"], local_path)

        return huggingface_meta["huggingface_module"].from_pretrained(local_path)

    def save_huggingface_meta(self, local_path, *args, **kwargs):
        with open(Path(local_path) / "giskard-model-huggingface-meta.yaml", "w") as f:
            yaml.dump(
                {
                    "huggingface_module": self.huggingface_module,
                    "pipeline_task": self.pipeline_task,
                },
                f,
                default_flow_style=False,
            )

    def save(self, local_path: Union[str, Path], *args, **kwargs) -> None:
        super().save(local_path, *args, **kwargs)
        self.save_model(local_path)
        self.save_huggingface_meta(local_path)

    def save_model(self, local_path, *args, **kwargs):
        self.model.save_pretrained(local_path)

    def model_predict(self, data):
        predictions = self._get_predictions(data)

        if self.is_classification and hasattr(predictions, "logits"):
            if isinstance(self.model, torch.nn.Module):
                with torch.no_grad():
                    logits = predictions.logits.detach().cpu().numpy()
            else:
                logits = predictions.logits

            if self.model_postprocessing_function:
                # @TODO: Are we sure we want to log a warning here?
                logger.warning(
                    "Your model output is logits. In Giskard, we expect the output to be probabilities."
                    "Since you provided a model_postprocessing_function, we assume that you included softmax() yourself.",
                    exc_info=True,
                )
            else:
                predictions = special.softmax(logits, axis=1) if len(logits.shape) == 2 else special.softmax(logits)

        return predictions

    def _get_predictions(self, data):
        if isinstance(self.model, pipelines.Pipeline):
            if isinstance(data, pd.DataFrame):
                data = data.to_dict(orient="records")
            _predictions = [{p["label"]: p["score"] for p in pl} for pl in self.model(data, top_k=None)]
            return [[p[label] for label in self.classification_labels] for p in _predictions]

        if isinstance(self.model, torch.nn.Module):
            with torch.no_grad():
                return self.model(**data)

        return self.model(**data)

    def to_mlflow(self, artifact_path: str = "transformers-model-from-giskard", **kwargs):
        import mlflow

        return mlflow.transformers.log_model(self.model, artifact_path, **kwargs)
