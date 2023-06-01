import mlflow
from typing import Union
import logging
import numpy as np

from giskard.core.core import SupportedModelTypes
from giskard.core.model import MLFlowBasedModel

import transformers
from transformers import PreTrainedModel

logger = logging.getLogger(__name__)


class HuggingFaceModel(MLFlowBasedModel):
    #TODO: add this always should_save_model_class = True
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

    @classmethod
    def load_clf(cls, local_path):
        return PreTrainedModel.from_pretrained(local_path)

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        self.clf.save_pretrained(local_path)

    #TODO: abstract clf_predict (extreme plan B)
    def clf_predict(self, data):
        predictions = self.clf.predict(data)
        return predictions