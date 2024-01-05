from __future__ import annotations
from abc import ABC, abstractmethod

import numpy as np
from typing import TYPE_CHECKING

from shap import Explanation


if TYPE_CHECKING:
    from giskard.models.base import BaseModel
    from giskard.scanner.report import ScanReport

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import ToolDescription


class BaseTool(ABC):
    default_name: str = ...
    default_description: str = ...

    def __init__(self,
                 model: BaseModel,
                 dataset: Dataset,
                 scan_result: ScanReport,
                 name: str = None,
                 description: str = None):
        self._model = model
        self._dataset = dataset
        self._scan_result = scan_result

        self._name = name if name is not None else self.default_name
        self._description = description if description is not None else self.default_description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    @abstractmethod
    def specification(self) -> str:
        ...

    @abstractmethod
    def __call__(self, *args, **kwargs) -> str:
        ...


class PredictFromDatasetTool(BaseTool):
    default_name: str = "predict_from_dataset"
    default_description: str = ToolDescription.PREDICT_FROM_DATASET.value

    def _get_feature_json_type(self) -> dict[any, str]:
        number_columns = {column: "number" for column in self._dataset.df.select_dtypes(include=(int, float)).columns}
        string_columns = {column: "string" for column in self._dataset.df.select_dtypes(exclude=(int, float)).columns}
        return number_columns | string_columns

    @property
    def specification(self) -> str:
        feature_json_type = self._get_feature_json_type()

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "row_filter": {
                            "type": "object",
                            "properties": {feature: {"type": dtype} for feature, dtype in
                                           list(feature_json_type.items())}
                        }
                    },
                    "required": ["row_filter"]
                }
            }
        }

    def _filter_dataset(self, row_filter: dict) -> Dataset:
        filtered_df = self._dataset.df.copy()
        for col_name, col_value in list(row_filter.items()):
            if filtered_df[col_name].dtype == "object":
                filtered_df = filtered_df[filtered_df[col_name].str.lower() == str(col_value).lower()]
            else:
                filtered_df = filtered_df[filtered_df[col_name] == col_value]

        return Dataset(filtered_df)

    def __call__(self, row_filter: dict) -> str:
        filtered_dataset = self._filter_dataset(row_filter)
        prediction = self._model.predict(filtered_dataset).prediction

        # Finalise the result.
        return ", ".join(prediction)


class SHAPExplanationTool(PredictFromDatasetTool):
    default_name: str = "shap_prediction_explanation"
    default_description: str = ToolDescription.SHAP_EXPLANATION.value
    _result_template: str = "'{feature_name}' | {attributions_values}"

    def _get_shap_explanations(self, filtered_dataset: Dataset) -> Explanation:
        from shap import KernelExplainer
        from giskard.models.model_explanation import _prepare_for_explanation, _get_background_example, \
            _get_highest_proba_shap

        # Prepare background sample to be used in the KernelSHAP.
        background_df = self._model.prepare_dataframe(self._dataset.df, self._dataset.column_dtypes,
                                                      self._dataset.target)
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
        feature_names = self._model.meta.feature_names or list(
            self._dataset.df.columns.drop(self._dataset.target, errors="ignore"))
        shap_explanations = Explanation(shap_values, data=filtered_dataset.df[feature_names],
                                        feature_names=feature_names)
        return shap_explanations

    def __call__(self, row_filter: dict) -> str:
        filtered_dataset = self._filter_dataset(row_filter)
        explanations = self._get_shap_explanations(filtered_dataset)

        # Finalise the result.
        shap_result = [self._result_template.format(feature_name=f_name,
                                                    attributions_values=list(zip(np.abs(explanations[:, f_name].values),
                                                                                 explanations[:, f_name].data)))
                       for f_name in explanations.feature_names]
        shap_result = "\n".join(shap_result)

        # Get prediction result from the parent tool, to add more context to the result.
        prediction_result = super().__call__(row_filter)
        return (f"Prediction result:\n"
                f"{prediction_result}\n\n"
                f"SHAP result: \n"
                f"'Feature name' | [('SHAP value', 'Feature value'), ...]\n"
                f"--------------------------------------------------------\n"
                f"{shap_result}\n\n")


class IssuesScannerTool(BaseTool):
    default_name: str = "issues_scanner"
    default_description: str = ToolDescription.ISSUES_SCANNER.value

    @property
    def specification(self) -> str:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
            }
        }

    def __call__(self) -> str:
        return f"ML model performance issues scanner result:\n {self._scan_result.to_markdown()}"