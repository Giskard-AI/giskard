from typing import Union
import logging
from scipy import special
from pathlib import Path
import yaml
from giskard.core.core import SupportedModelTypes
from giskard.models.base import WrapperModel

try:
    import torch
    from transformers import pipeline, pipelines
except ImportError:
    pass


logger = logging.getLogger(__name__)


class HuggingFaceModel(WrapperModel):
    def __init__(
        self,
        clf,
        model_type: Union[SupportedModelTypes, str],
        name: str = None,
        data_preprocessing_function=None,
        model_postprocessing_function=None,
        feature_names=None,
        classification_threshold=0.5,
        classification_labels=None,
    ) -> None:

        super().__init__(
            clf=clf,
            model_type=model_type,
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
        )

        self.huggingface_module = clf.__class__
        self.pipeline_task = clf.task if isinstance(clf, pipelines.Pipeline) else None

    @classmethod
    def load_clf(cls, local_path):
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
        self.save_with_huggingface(local_path)
        self.save_huggingface_meta(local_path)

    def save_with_huggingface(self, local_path):
        self.clf.save_pretrained(local_path)

    def clf_predict(self, data):
        predictions = self._get_predictions(data)

        if self.is_classification and hasattr(predictions, "logits"):
            if isinstance(self.clf, torch.nn.Module):
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
        if isinstance(self.clf, torch.nn.Module):
            with torch.no_grad():
                return self.clf(**data)

        if isinstance(self.clf, pipelines.Pipeline):
            _predictions = [{p["label"]: p["score"] for p in pl} for pl in self.clf(list(data), top_k=None)]
            return [[p[label] for label in self.meta.classification_labels] for p in _predictions]

        return self.clf(**data)
