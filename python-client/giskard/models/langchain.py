from typing import Any, Callable, Iterable, Optional

import mlflow
import pandas as pd

from giskard.core.core import ModelType, SupportedModelTypes
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import MLFlowSerializableModel


class LangchainModel(MLFlowSerializableModel):
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
            **kwargs,
    ) -> None:
        assert (
                model_type == SupportedModelTypes.TEXT_GENERATION
        ), "LangchainModel only support text_generation ModelType"

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
        mlflow.langchain.save_model(self.model, path=local_path, mlflow_model=mlflow_meta)

    @classmethod
    def load_model(cls, local_dir):
        return mlflow.langchain.load_model(local_dir)

    def model_predict(self, df):
        return [self.model.predict(**data) for data in df.to_dict("records")]

    def rewrite_prompt(self, template, input_variables=None, **kwargs):
        from langchain import LLMChain

        update = dict(template=template)
        if input_variables is not None:
            update["input_variables"] = input_variables

        new_prompt = self.model.prompt.copy(update=update)
        chain = LLMChain(llm=self.model.llm, prompt=new_prompt)

        model_kwargs = dict(
            model_type=self.meta.model_type,
            data_preprocessing_function=self.data_preprocessing_function,
            model_postprocessing_function=self.model_postprocessing_function,
            feature_names=None,
            # The dataset passed with the new prompts could have different column name in the scan detectors
            classification_threshold=self.meta.classification_threshold,
            classification_labels=self.meta.classification_labels,
        )
        model_kwargs.update(kwargs)

        return self.__class__(chain, **model_kwargs)

    def to_mlflow(self, artifact_path: str = "langchain-model-from-giskard", **kwargs):
        return mlflow.langchain.log_model(self.model, artifact_path, **kwargs)
