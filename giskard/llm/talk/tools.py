from __future__ import annotations
from abc import ABC, abstractmethod

import numpy as np
from typing import TYPE_CHECKING

from shap import Explanation

if TYPE_CHECKING:
    from giskard.models.base import BaseModel

from giskard.datasets.base import Dataset


class BaseTool(ABC):
    @property
    @abstractmethod
    def specification(self) -> str:
        ...

    @abstractmethod
    def __call__(self, *args, **kwargs) -> str:
        ...


class PredictFromDatasetTool(BaseTool):
    default_name = "predict_from_dataset"
    default_description = ("You expect a dictionary with features and their values to filter rows from the dataset, "
                           "then you run the model prediction on that rows and finally return the prediction result.")

    def __init__(self, model: BaseModel, dataset: Dataset, name: str = None, description: str = None):
        self._model = model
        self._dataset = dataset

        self._name = name if name is not None else self.default_name
        self._description = description if description is not None else self.default_description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def _get_feature_json_type(self):
        number_columns = {column: "number" for column in self._dataset.df.select_dtypes(include=(int, float)).columns}
        string_columns = {column: "string" for column in self._dataset.df.select_dtypes(exclude=(int, float)).columns}
        return number_columns | string_columns

    @property
    def specification(self) -> str:
        feature_json_type = self._get_feature_json_type()

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "row_filter": {
                        "type": "object",
                        "properties": {feature: {"type": dtype} for feature, dtype in feature_json_type.items()}
                    }
                },
                "required": ["row_filter"]
            }
        }

    def _get_filtered_dataset(self, row_filter: dict) -> Dataset:
        filtered_df = self._dataset.df.copy()
        for col_name, col_value in row_filter.items():
            if filtered_df[col_name].dtype == "object":
                filtered_df = filtered_df[filtered_df[col_name].str.lower() == str(col_value).lower()]
            else:
                filtered_df = filtered_df[filtered_df[col_name] == col_value]

        return Dataset(filtered_df)

    def __call__(self, row_filter: dict) -> str:
        # 1) Filter dataset using predicted filter.
        filtered_dataset = self._get_filtered_dataset(row_filter)

        # 2) Get model prediction.
        prediction = self._model.predict(filtered_dataset).prediction

        # 3) Finalise the result.
        result = ", ".join(prediction)

        return result


class SHAPExplanationTool(PredictFromDatasetTool):
    default_name = "shap_prediction_explanation"
    default_description = ("You expect a dictionary with feature names as keys and their values as dict values, "
                           "which you use to filter rows in the dataset, "
                           "then you run the SHAP explanation on that filtered rows, "
                           "and finally you return the SHAP explanation result as well as the model prediction result."
                           "Please note, that the bigger SHAP value - the more important feature is for prediction.")

    _result_template = "'{feature_name}' | {attributions_values}"

    def _get_shap_explanations(self, filtered_dataset: Dataset) -> Explanation:
        from shap import KernelExplainer
        from giskard.models.model_explanation import _prepare_for_explanation, _get_background_example, _get_highest_proba_shap

        # Prepare background sample to be used in the KernelSHAP.
        background_df = self._model.prepare_dataframe(self._dataset.df, self._dataset.column_dtypes, self._dataset.target)
        background_sample = _get_background_example(background_df, self._dataset.column_types)

        # Prepare input data for an explanation.
        data_to_explain = _prepare_for_explanation(filtered_dataset.df, model=self._model, dataset=self._dataset)

        def prediction_function(_df):
            """Rolls-back SHAP casting of all columns to the 'object' type."""
            return self._model.predict_df(_df.astype(data_to_explain.dtypes))

        # Obtain SHAP explanations.
        explainer = KernelExplainer(prediction_function, background_sample, data_to_explain.columns, keep_index=True)
        shap_values = explainer.shap_values(data_to_explain, silent=True)

        if self._model.is_classification:
            shap_values = _get_highest_proba_shap(shap_values, self._model, filtered_dataset)

        # Put SHAP values to the Explanation object for a convenience.
        feature_names = self._model.meta.feature_names or list(self._dataset.df.columns.drop(self._dataset.target, errors="ignore"))
        shap_explanations = Explanation(shap_values, data=filtered_dataset.df[feature_names], feature_names=feature_names)
        return shap_explanations

    def __call__(self, row_filter: dict) -> str:
        # 0) Get prediction result from the parent tool.
        prediction_result = super().__call__(row_filter)

        # 1) Filter the dataset using the LLM-created filter expression.
        filtered_dataset = self._get_filtered_dataset(row_filter)

        # 2) Get a SHAP explanation.
        explanations = self._get_shap_explanations(filtered_dataset)

        # 3) Finalise the result.
        shap_result = [self._result_template.format(feature_name=f_name,
                                                    attributions_values=list(zip(np.abs(explanations[:, f_name].values),
                                                                                 explanations[:, f_name].data)))
                       for f_name in explanations.feature_names]
        shap_result = "\n".join(shap_result)

        result = (f"Prediction result:\n"
                  f"{prediction_result}\n\n"
                  f"SHAP result: \n"
                  f"'Feature name' | [('SHAP value', 'Feature value'), ...]\n"
                  f"--------------------------------------------------------\n"
                  f"{shap_result}\n\n")

        return result
