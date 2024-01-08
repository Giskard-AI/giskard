import numpy as np

from giskard.llm.talk.config import ToolDescription
from giskard.llm.talk.utils.shap import explain_with_shap
from giskard.llm.talk.tools.predict import PredictDatasetInputTool


class SHAPExplanationTool(PredictDatasetInputTool):
    default_name: str = "shap_explanation"
    default_description: str = ToolDescription.SHAP_EXPLANATION.value
    _output_template: str = "'{feature_name}' | {attributions_values}"

    @staticmethod
    def _finalise_output(prediction_result: str, shap_result: np.ndarray) -> str:
        shap_result = "\n".join(shap_result)
        return (f"Prediction result:\n"
                f"{prediction_result}\n\n"
                f"SHAP result: \n"
                f"'Feature name' | [('SHAP value', 'Feature value'), ...]\n"
                f"-------------------------------------------------------\n"
                f"{shap_result}\n\n")

    def __call__(self, features_dict: dict) -> str:
        # Get prediction result from the parent tool, to add more context to the result.
        prediction_result = super().__call__(features_dict)

        model_input = self._prepare_input(features_dict)
        explanations = explain_with_shap(model_input, self._model, self._dataset)

        # Finalise the result.
        shap_result = [self._output_template.format(feature_name=f_name,
                                                    attributions_values=list(
                                                        zip(
                                                            np.abs(explanations[:, f_name].values),
                                                            explanations[:, f_name].data
                                                        )))
                       for f_name in explanations.feature_names]
        return self._finalise_output(prediction_result, shap_result)
