from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np

from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.tools.predict import PredictTool
from giskard.llm.talk.utils.shap import explain_with_shap

if TYPE_CHECKING:
    from giskard.datasets.base import Dataset
    from giskard.models.base import BaseModel


class SHAPExplanationTool(PredictTool):
    """SHAP explanation Tool.

    Attributes
    ----------
    default_name : str
        The default name of the Tool. Can be re-defined with constructor.
    default_description: str
        The default description of the Tool's functioning. Can be re-defined with constructor.
    """

    default_name: str = "shap_explanation"
    default_description: str = ToolDescription.SHAP_EXPLANATION.value
    _output_template: str = "'{feature_name}' | {attributions_values}"

    def __init__(
        self, model: BaseModel, dataset: Dataset, name: Optional[str] = None, description: Optional[str] = None
    ):
        """Constructor of the class.

        Parameters
        ----------
        model : BaseModel
            The Giskard Model.
        dataset : Dataset
            The Giskard Dataset.
        name : str, optional
            The name of the Tool.
            If not set, the `default_name` is used.
        description : str, optional
            The description of the Tool.
            If not set, the `default_description` is used.
        """
        super().__init__(model, dataset, name, description)  # To reflect the docstring.

    @staticmethod
    def _finalise_output(prediction_result: str, shap_result: np.ndarray) -> str:
        """Define the output format.

        Create Tool's output string, using predictions and related SHAP explanations.

        Parameters
        ----------
        prediction_result : str
            The prediction result.
        shap_result : np.ndarray
            The SHAP explanations.

        Returns
        -------
        str
            The formatted Tool's output.
        """
        shap_result = "\n".join(shap_result)
        return (
            f"Prediction result:\n"
            f"{prediction_result}\n\n"
            f"SHAP result: \n"
            f"'Feature name' | [('SHAP value', 'Feature value'), ...]\n"
            f"-------------------------------------------------------\n"
            f"{shap_result}\n\n"
        )

    def __call__(self, features_dict: dict[str, any]) -> str:
        """Execute the Tool's functionality.

        Calculate the SHAP explanations.

        Parameters
        ----------
        features_dict : dict[str, any]
            The dictionary with features and related values extracted from the query.

        Returns
        -------
        str
            SHAP explanation of the predictions.
        """
        # Get a prediction result from the parent tool, to add more context to the result.
        prediction_result = super().__call__(features_dict)

        model_input = self._prepare_input(features_dict)
        explanations = explain_with_shap(model_input, self._model, self._dataset)

        # Finalise the result.
        shap_result = [
            self._output_template.format(
                feature_name=f_name,
                attributions_values=list(zip(np.abs(explanations[:, f_name].values), explanations[:, f_name].data)),
            )
            for f_name in explanations.feature_names
        ]
        return self._finalise_output(prediction_result, shap_result)
