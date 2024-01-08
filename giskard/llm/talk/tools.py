from abc import ABC, abstractmethod

import numpy as np
from shap import Explanation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from giskard.models.base import BaseModel
    from giskard.scanner.report import ScanReport

from giskard.datasets.base import Dataset
from giskard.llm.talk.config import ToolDescription


class BaseTool(ABC):
    default_name: str = ...
    default_description: str = ...

    def __init__(self,
                 model: "BaseModel" = None,
                 dataset: Dataset = None,
                 scan_result: "ScanReport" = None,
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


class BasePredictTool(BaseTool, ABC):
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
                        "features_dict": {
                            "type": "object",
                            "properties": {feature: {"type": dtype} for feature, dtype in
                                           list(feature_json_type.items())}
                        }
                    },
                    "required": ["features_dict"]
                }
            }
        }

    @abstractmethod
    def _prepare_input(self, *args, **kwargs) -> Dataset:
        ...

    def __call__(self, features_dict: dict) -> str:
        model_input = self._prepare_input(features_dict)
        prediction = self._model.predict(model_input).prediction
        return ", ".join(prediction)


class PredictDatasetInputTool(BasePredictTool):
    default_name: str = "predict_dataset_input"
    default_description: str = ToolDescription.PREDICT_DATASET_INPUT.value

    def _prepare_input(self, row_filter: dict) -> Dataset:
        filtered_df = self._dataset.df.copy()
        for col_name, col_value in list(row_filter.items()):
            if filtered_df[col_name].dtype == "object":
                filtered_df = filtered_df[filtered_df[col_name].str.lower() == str(col_value).lower()]
            else:
                filtered_df = filtered_df[filtered_df[col_name] == col_value]

        return Dataset(filtered_df)


class PredictUserInputTool(BasePredictTool):
    default_name: str = "predict_user_input"
    default_description: str = ToolDescription.PREDICT_USER_INPUT.value

    def _prepare_input(self, feature_values: dict) -> Dataset:
        from giskard.models.model_explanation import _get_background_example

        # Prepare background sample.
        background_df = self._model.prepare_dataframe(self._dataset.df, self._dataset.column_dtypes,
                                                      self._dataset.target)
        background_sample = _get_background_example(background_df, self._dataset.column_types)

        # Fill background sample with known values.
        for col_name, col_value in list(feature_values.items()):
            background_sample.loc[0, col_name] = col_value

        return Dataset(background_sample)


class SHAPExplanationTool(PredictDatasetInputTool):
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

    @staticmethod
    def _finalise_output(prediction_result: str, shap_result: np.ndarray) -> str:
        shap_result = "\n".join(shap_result)
        return (f"Prediction result:\n"
                f"{prediction_result}\n\n"
                f"SHAP result: \n"
                f"'Feature name' | [('SHAP value', 'Feature value'), ...]\n"
                f"--------------------------------------------------------\n"
                f"{shap_result}\n\n")

    def __call__(self, features_dict: dict) -> str:
        # Get prediction result from the parent tool, to add more context to the result.
        prediction_result = super().__call__(features_dict)

        model_input = self._prepare_input(features_dict)
        explanations = self._get_shap_explanations(model_input)

        # Finalise the result.
        shap_result = [self._result_template.format(feature_name=f_name,
                                                    attributions_values=list(
                                                        zip(
                                                            np.abs(explanations[:, f_name].values),
                                                            explanations[:, f_name].data
                                                        )))
                       for f_name in explanations.feature_names]
        return self._finalise_output(prediction_result, shap_result)


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

    @staticmethod
    def _finalise_output(scan_result: str) -> str:
        return f"ML model performance issues scanner result:\n {scan_result}"

    def __call__(self) -> str:
        scan_result = self._scan_result.to_markdown()
        return self._finalise_output(scan_result)
