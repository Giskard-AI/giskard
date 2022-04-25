from typing import Any
import logging
import pandas as pd
from ai_inspector import ModelInspector
from alibi.explainers import KernelShap
from eli5.lime import TextExplainer

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import files, files_utils
from app.core.ml import run_predict, ModelPredictionResults, ModelPredictionResultsDTO
from app.core.model_explanation import (
    background_example,
    summary_shap_classification,
    summary_shap_regression,
    text_explanation_prediction_wrapper,
    parse_text_explainer_response
)

router = APIRouter()

logger = logging.getLogger("models-api")
logger.setLevel(logging.INFO)


@router.get("/{id}/metadata")
def get_model_metadata(
        id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    model_file = crud.project_model.get(db, id)

    project = crud.project.get(db, model_file.project_id)
    if files.has_read_access(current_user, project, model_file):
        try:
            model_inspector = files_utils.read_model_file(model_file.location)
            return schemas.ModelMetadata(
                prediction_task=model_inspector.prediction_task,
                input_types=model_inspector.input_types,
                classification_labels=model_inspector.classification_labels,
                classification_threshold=model_inspector.classification_threshold,
            )
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Model file cannot be read")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")


@router.get("/{modelId}/features/{datasetId}")
def get_model_features_metadata(
        modelId: int,
        datasetId: int,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    model_file = crud.project_model.get(db, modelId)
    data_file = crud.dataset.get(db, datasetId)

    project = crud.project.get(db, model_file.project_id)
    if files.has_read_access(current_user, project, model_file) and files.has_read_access(
            current_user, project, data_file
    ):
        try:
            model_inspector = files_utils.read_model_file(model_file.location)
            data_df = files_utils.read_dataset_file(data_file.location)
            feat_metadata = []
            for k, v in model_inspector.input_types.items():
                feat_desc = {"feat_name": k, "feat_type": v}
                if v == "category":  # read dataset file to extract unique feature values
                    categories = [str(c) for c in data_df[k].fillna("").unique() if str(c).strip()]
                    feat_desc["feat_cat_values"] = categories
                feat_metadata.append(feat_desc)
            return feat_metadata
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error processing files: {e}"
            )
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")


def select_single_prediction(model_inspector: ModelInspector, probabilities):
    labels = model_inspector.classification_labels
    if model_inspector.classification_threshold is not None and len(labels) == 2:
        return labels[1] if probabilities[labels[1]] >= model_inspector.classification_threshold else labels[0]
    else:
        return max(probabilities, key=lambda key: probabilities[key])


@router.post("/{modelId}/predict")
def predict(
        modelId: int,
        input_data: schemas.ModelPredictionInput,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
) -> ModelPredictionResults:
    model_file = crud.project_model.get(db, modelId)
    project = crud.project.get(db, model_file.project_id)
    if files.has_read_access(current_user, project, model_file):
        try:
            model_inspector = files_utils.read_model_file(model_file.location)
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Model file cannot be read")
        try:
            input_df = pd.DataFrame({k: [v] for k, v in input_data.features.items()})

            # raw_prediction = model_inspector.prediction_function(input_df)[0]
            prediction_results = run_predict(input_df, model_inspector)
            if model_inspector.prediction_task == "regression":
                result = ModelPredictionResultsDTO(prediction=prediction_results.raw_prediction[0])
            elif model_inspector.prediction_task == "classification":
                result = ModelPredictionResultsDTO(
                    prediction=prediction_results.prediction[0],
                    probabilities=prediction_results.all_predictions.iloc[0].to_dict(),
                )
            else:
                raise ValueError(
                    f"Prediction task is not supported: {model_inspector.prediction_task}"
                )
            return result
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid model prediction input: {e}")

    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")


@router.post("/{modelId}/{datasetId}/explain")
def get_model_explanation_on_dataset(
        modelId: int,
        datasetId: int,
        input_data: schemas.ModelPredictionInput,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.ModelExplanationResults:
    model_file = crud.project_model.get(db, modelId)
    data_file = crud.dataset.get(db, datasetId)
    project = crud.project.get(db, model_file.project_id)
    if files.has_read_access(current_user, project, model_file) and files.has_read_access(
            current_user, project, data_file
    ):
        try:
            model_inspector = files_utils.read_model_file(model_file.location)
            feature_columns = list(model_inspector.input_types.keys())
            df = files_utils.read_dataset_file(data_file.location)[feature_columns]
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error processing files: {e}"
            )
        try:
            feature_names = list(model_inspector.input_types.keys())
            kernel_shap = KernelShap(
                predictor=lambda array: model_inspector.prediction_function(
                    pd.DataFrame(array, columns=feature_columns)
                ),
                feature_names=feature_names,
                task=model_inspector.prediction_task,
            )
            kernel_shap.fit(background_example(df, model_inspector.input_types))
            input_df = pd.DataFrame({k: [v] for k, v in input_data.features.items()})[
                feature_columns
            ]
            explanations = kernel_shap.explain(input_df)
            if model_inspector.prediction_task == "regression":
                explanation_chart_data = summary_shap_regression(
                    shap_values=explanations.shap_values, feature_names=feature_names
                )
            elif model_inspector.prediction_task == "classification":
                explanation_chart_data = summary_shap_classification(
                    shap_values=explanations.shap_values,
                    feature_names=feature_names,
                    class_names=model_inspector.classification_labels,
                )
            else:
                raise ValueError(
                    f"Prediction task is not supported: {model_inspector.prediction_task}"
                )
            return schemas.ModelExplanationResults(
                explanations=explanation_chart_data["explanations"]
            )
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error computing explanations: {e}"
            )
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")


@router.post("/{modelId}/explain_text/{text_column}")
def get_model_explanation_on_text_column(
        modelId: int,
        input_data: schemas.ModelPredictionInput,
        text_column: str,
        n_samples: int = 500,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    model_file = crud.project_model.get(db, modelId)
    project = crud.project.get(db, model_file.project_id)
    if files.has_read_access(current_user, project, model_file):
        try:
            model_inspector = files_utils.read_model_file(model_file.location)
            feature_columns = list(model_inspector.input_types.keys())
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error processing files: {e}"
            )
        try:
            if model_inspector.input_types[text_column] != "text":
                raise ValueError(f"Column {text_column} is not of type text")
            text_document = input_data.features[text_column]
            input_df = pd.DataFrame({k: [v] for k, v in input_data.features.items()})[
                feature_columns
            ]
            text_explainer = TextExplainer(random_state=42, n_samples=n_samples)
            prediction_function = text_explanation_prediction_wrapper(
                model_inspector.prediction_function, input_df, text_column
            )
            text_explainer.fit(text_document, prediction_function)
            html_response = text_explainer.show_prediction(
                target_names=model_inspector.classification_labels)._repr_html_()
            return parse_text_explainer_response(html_response)
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error computing text explanations: {e}"
            )
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")
