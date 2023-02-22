import mlflow
from typing import Union
import logging
import numpy as np

from giskard.core.core import SupportedModelTypes
from giskard.core.model import MLFlowBasedModel

logger = logging.getLogger(__name__)

class TensorFlowModel(MLFlowBasedModel):
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
        return mlflow.tensorflow.load_model(local_path)

    def save_with_mlflow(self, local_path, mlflow_meta: mlflow.models.Model):
        mlflow.tensorflow.save_model(self.clf,
                                     path=local_path,
                                     mlflow_model=mlflow_meta)

    def clf_predict(self, data):
        predictions = self.clf.predict(data)

        if self.is_classification and predictions.shape[1] == 1:
            logger.warning(f"\nYour binary classification model prediction is of the shape {predictions.shape}. \n"
                    f"In Giskard we expect for binary {(predictions.shape[0], 2)} for binary classification models. \n"
                    f"We automatically infered the second class prediction but please make sure that \n"
                    f"the probability output of your model corresponds to the first label of the \n"
                    f"classification_labels ({self.meta.classification_labels}) you provided us with.", exc_info=True)
            predictions = np.insert(predictions, 1, 1 - predictions[:, 0], axis=1)

        predictions = np.squeeze(np.array(predictions))

        if self.model_postprocessing_function:
            predictions = self.model_postprocessing_function(predictions)

        return predictions
