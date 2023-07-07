import mlflow
import pytest

from giskard.core.core import SupportedModelTypes

mlflow_model_types = {
    SupportedModelTypes.CLASSIFICATION: "classifier",
    SupportedModelTypes.REGRESSION: "regressor",
    SupportedModelTypes.TEXT_GENERATION: "text"
}


def _evaluate(dataset_name, model_name, request):
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    mlflow.end_run()
    mlflow.start_run()
    model_info = model.to_mlflow()

    mlflow.evaluate(
        model=model_info.model_uri,
        model_type=mlflow_model_types[model.meta.model_type],
        data=dataset.df,
        targets=dataset.target,
        evaluators="giskard",
        evaluator_config={"classification_labels": model.meta.classification_labels}
    )
    mlflow.end_run()


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("german_credit_data", "german_credit_model"),
        ("breast_cancer_data", "breast_cancer_model"),
        ("drug_classification_data", "drug_classification_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes"),
        ("hotel_text_data", "hotel_text_model"),
    ],
)
def test_fast(dataset_name, model_name, request):
    _evaluate(dataset_name, model_name, request)


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("enron_data_full", "enron_model"),
        ("medical_transcript_data", "medical_transcript_model"),
        ("fraud_detection_data", "fraud_detection_model"),
        ("amazon_review_data", "amazon_review_model"),
    ],
)
@pytest.mark.slow
def test_slow(dataset_name, model_name, request):
    _evaluate(dataset_name, model_name, request)
