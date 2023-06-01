from typing import Union
import logging

from scipy import special
import torch
from pathlib import Path
import yaml

from giskard.core.core import SupportedModelTypes
from giskard.core.model import WrapperModel

from transformers import pipeline, pipelines


logger = logging.getLogger(__name__)


class HuggingFaceModel(WrapperModel):

    def __init__(self,
                 clf,
                 model_type: Union[SupportedModelTypes, str],
                 name: str = None,
                 data_preprocessing_function=None,
                 model_postprocessing_function=None,
                 feature_names=None,
                 classification_threshold=0.5,
                 classification_labels=None) -> None:

        super().__init__(clf=clf,
                         model_type=model_type,
                         name=name,
                         data_preprocessing_function=data_preprocessing_function,
                         model_postprocessing_function=model_postprocessing_function,
                         feature_names=feature_names,
                         classification_threshold=classification_threshold,
                         classification_labels=classification_labels)

        self.huggingface_module = clf.__class__
        self.pipeline_task = clf.task if isinstance(clf, pipelines.Pipeline) else None

    # This works, but the problem with AutoModels (loaded model in that context) is that their
    # output are different from the original saved model output
    """@classmethod
    def load_clf(cls, local_path):
        huggingface_meta_file = Path(local_path) / 'giskard-model-huggingface-meta.yaml'
        if huggingface_meta_file.exists():
            with open(huggingface_meta_file) as f:
                huggingface_meta_file = yaml.load(f, Loader=yaml.Loader)

        return AutoModel.from_pretrained(local_path, from_tf=huggingface_meta_file["from_tf"])"""

    @classmethod
    def load_clf(cls, local_path):
        huggingface_meta_file = Path(local_path) / 'giskard-model-huggingface-meta.yaml'
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
                }, f, default_flow_style=False)

    def save(self, local_path: Union[str, Path]) -> None:
        super().save(local_path)
        self.save_with_huggingface(local_path)
        self.save_huggingface_meta(local_path)

    def save_with_huggingface(self, local_path):
        self.clf.save_pretrained(local_path)

    def clf_predict(self, data):
        if isinstance(self.clf, torch.nn.Module):
            with torch.no_grad():
                predictions = self.clf(**data)
        elif isinstance(self.clf, pipelines.Pipeline):
            _predictions = self.clf(data, top_k=None)
            predictions = []
            for label in self.meta.classification_labels:
                label_score = next(item for item in _predictions if item["label"] == label)
                predictions.append(label_score['score'])
        else:
            predictions = self.clf(**data) if isinstance(data, dict) else self.clf(data)

        if self.is_classification and hasattr(predictions, 'logits'):
            if isinstance(self.clf, torch.nn.Module):
                with torch.no_grad():
                    logits = predictions.logits.detach().numpy()
            else:
                logits = predictions.logits

            if self.model_postprocessing_function:
                logger.warning("Your model output is logits. In Giskard, we expect the output to be probabilities."
                               "Since you provided a model_postprocessing_function, we assume that you included softmax() yourself.", exc_info=True)
            else:
                predictions = special.softmax(logits, axis=1) if len(logits.shape) == 2 else special.softmax(logits)

        return predictions
