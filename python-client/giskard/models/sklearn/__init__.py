from typing import Callable, Iterable, Any, Optional

import mlflow
import pandas as pd

from giskard.core.core import ModelType, SupportedModelTypes
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import MLFlowBasedModel


class SKLearnModel(MLFlowBasedModel):
    """
    The SKLearnModel class is a subclass of MLFlowBasedModel that wraps a scikit-learn model.
    This class provides a way to standardize the API for scikit-learn models to make them compatible with
    the other model types in the giskard package.

    Attributes:
        _feature_names_attr (str):
            A private attribute that holds the name of the scikit-learn model's attribute that stores the feature names.
    """

    _feature_names_attr = "feature_names_in_"

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
            **kwargs,
    ) -> None:
        """
        Constructs an instance of the SKLearnModel class with the provided arguments.

        Args:
            model (Any): The machine learning model to be validated and used for inference.
            model_type (ModelType): The type of model being used. Must be a value from the SupportedModelTypes enum.
            name (str, optional): A string name for the model being used, used for identification purposes.
            data_preprocessing_function (Callable[[pd.DataFrame], Any], optional):
                A callable function that performs any necessary preprocessing on input data.
                Must take a pandas DataFrame as input and return a single object.
            model_postprocessing_function (Callable[[Any], Any], optional):
                A callable function that performs any necessary postprocessing on model output.
                Must take a single object as input and return a single object.
            feature_names (Iterable, optional): An iterable of string feature names.
            classification_threshold (float, optional):
                A float classification threshold value, if applicable to the model being used.
            classification_labels (Iterable, optional):
                An iterable of classification label names, if applicable to the model being used.
        """
        if model_type == SupportedModelTypes.CLASSIFICATION:
            if classification_labels is None and hasattr(model, "classes_"):
                classification_labels = list(getattr(model, "classes_"))
        if feature_names is None and hasattr(model, self._feature_names_attr):
            if data_preprocessing_function is None:
                feature_names = list(getattr(model, self._feature_names_attr))
            else:
                raise ValueError("feature_names must be provided if data_preprocessing_function is not None.")

        super().__init__(
            model=model,
            model_type=model_type,
            name=name,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            **kwargs,
        )

    def save_model(self, local_path, mlflow_meta):
        if self.is_classification:
            pyfunc_predict_fn = "predict_proba"
        elif self.is_regression:
            pyfunc_predict_fn = "predict"
        else:
            raise ValueError("Unsupported model type")

        mlflow.sklearn.save_model(
            self.model, path=local_path, pyfunc_predict_fn=pyfunc_predict_fn, mlflow_model=mlflow_meta
        )

    @classmethod
    def load_model(cls, local_dir):
        return mlflow.sklearn.load_model(local_dir)

    def model_predict(self, df):
        if self.is_regression:
            return self.model.predict(df)
        else:
            return self.model.predict_proba(df)

    def to_mlflow(self,
                  artifact_path="sklearn-model-from-giskard",
                  pyfunc_predict_fn="predict_proba",
                  **kwargs):
        return mlflow.sklearn.log_model(sk_model=self.model, artifact_path=artifact_path,
                                        pyfunc_predict_fn=pyfunc_predict_fn,
                                        **kwargs)
