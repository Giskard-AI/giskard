from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from giskard import Dataset
    from giskard.models.base import BaseModel

from giskard.core.errors import GiskardImportError


def _calculate_shap_values(data_to_explain: Dataset, model: BaseModel, dataset: Dataset) -> np.ndarray:
    """Perform Kernel SHAP explanation.

    Returns the feature importance in terms of SHAP values. Kernel SHAP is used
    to calculate feature contributions.

    Parameters
    ----------
    data_to_explain : Dataset
        The data for the prediction to explain.
    model : giskard.Model
        The model used for the SHAP explanation.
    dataset : giskard.Dataset
        The dataset used for the SHAP explanation.

    Returns
    -------
    shap_values : np.ndarray
        The model's SHAP values as a numpy array
    """
    # Import the private function from the 'model_explanation' module to avoid code duplication.
    # Also, if import from the top-level, we get the next error: "ImportError: cannot import name 'BaseModel'
    # from partially initialized module 'giskard.models.base' (most likely due to a circular import)"
    from giskard.models.model_explanation import _get_background_example, _prepare_for_explanation

    try:
        from shap import KernelExplainer
    except ImportError as e:
        raise GiskardImportError("shap") from e

    # Prepare background sample to be used in the KernelSHAP.
    background_df = model.prepare_dataframe(dataset.df, dataset.column_dtypes, dataset.target)
    background_sample = _get_background_example(background_df, dataset.column_types)

    # Prepare input data for an explanation.
    data_to_explain = _prepare_for_explanation(data_to_explain.df, model=model, dataset=dataset)

    def prediction_function(_df):
        """Rolls-back SHAP casting of all columns to the 'object' type."""
        return model.predict_df(_df.astype(data_to_explain.dtypes))

    # Obtain SHAP explanations.
    explainer = KernelExplainer(prediction_function, background_sample, data_to_explain.columns, keep_index=True)
    shap_values = explainer.shap_values(data_to_explain, silent=True)
    return shap_values


def explain_with_shap(data_to_explain: Dataset, model: BaseModel, dataset: Dataset, only_highest_proba: bool = True):
    """Explain prediction with SHAP.

    Parameters
    ----------
    data_to_explain : Dataset
        The data for the prediction to explain.
    model : giskard.Model
        The model used for the SHAP explanation
    dataset : giskard.Dataset
        The dataset used for the SHAP explanation.
    only_highest_proba : bool (optional, default=True)
        A flag indicating whether to provide SHAP explanations only for the
        predictions with the highest probability or not.

    Returns
    -------
    ShapResult
        The model's SHAP values.
    """
    # Import the private function from the 'model_explanation' module to avoid code duplication.
    # Also, if import from the top-level, we get the next error: "ImportError: cannot import name 'BaseModel'
    # from partially initialized module 'giskard.models.base' (most likely due to a circular import)"
    from giskard.models.model_explanation import _get_highest_proba_shap

    try:
        from shap import Explanation
    except ImportError as e:
        raise GiskardImportError("shap") from e
    shap_values = _calculate_shap_values(data_to_explain, model, dataset)
    if only_highest_proba and model.is_classification:
        shap_values = _get_highest_proba_shap(shap_values, model, data_to_explain)

    # Put SHAP values to the Explanation object for a convenience.
    feature_names = model.feature_names or list(dataset.df.columns.drop(dataset.target, errors="ignore"))
    shap_explanations = Explanation(shap_values, data=data_to_explain.df[feature_names], feature_names=feature_names)
    return shap_explanations
