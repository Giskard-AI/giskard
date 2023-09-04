import mlflow
import pytest

from giskard.core.core import SupportedModelTypes

mlflow_model_types = {
    SupportedModelTypes.CLASSIFICATION: "classifier",
    SupportedModelTypes.REGRESSION: "regressor",
    SupportedModelTypes.TEXT_GENERATION: "text"
}


def _evaluate(dataset, model, evaluator_config, request):
    mlflow.end_run()
    mlflow.start_run()
    model_info = model.to_mlflow()

    mlflow.evaluate(
        model=model_info.model_uri,
        model_type=mlflow_model_types[model.meta.model_type],
        data=dataset.df,
        targets=dataset.target,
        evaluators="giskard",
        evaluator_config=evaluator_config
    )
    mlflow.end_run()


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("breast_cancer_data", "breast_cancer_model"),
        ("drug_classification_data", "drug_classification_model"),
        ("diabetes_dataset_with_target", "linear_regression_diabetes"),
        ("hotel_text_data", "hotel_text_model"),
    ],
)
def test_fast(dataset_name, model_name, request):
    _run_test(dataset_name, model_name, request)


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("german_credit_data", "german_credit_model"),
        ("enron_data_full", "enron_model"),
        ("medical_transcript_data", "medical_transcript_model"),
        ("fraud_detection_data", "fraud_detection_model"),
        ("amazon_review_data", "amazon_review_model"),
    ],
)
@pytest.mark.slow
def test_slow(dataset_name, model_name, request):
    _run_test(dataset_name, model_name, request)


def _run_test(dataset_name, model_name, request):
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    evaluator_config = {"model_config": {"classification_labels": model.meta.classification_labels}}
    _evaluate(dataset, model, evaluator_config, request)


@pytest.mark.parametrize(
    "dataset_name,model_name", [("german_credit_data", "german_credit_model")])
def test_errors(dataset_name, model_name, request):
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    evaluator_config = {"model_config": {"classification_labels": model.meta.classification_labels}}

    # dataset type error
    dataset_copy = dataset.copy()
    dataset_copy.df = [[0.6, 0.4]]
    dataset_copy.target = [1]

    with pytest.raises(Exception) as e:
        _evaluate(dataset_copy, model, evaluator_config, request)
    assert e.match(r"Only pd.DataFrame are currently supported by the giskard evaluator.")

    # dataset wrapping error
    dataset_copy = dataset.copy()
    dataset_copy.df.savings[0] = ["wrong_entry"]

    with pytest.raises(Exception) as e:
        _evaluate(dataset_copy, model, evaluator_config, request)
    assert e.match(r"An error occurred while wrapping the dataset.*")

    # model wrapping error
    dataset_copy = dataset.copy()
    evaluator_config = {"model_config": {"classification_labels": None}}

    with pytest.raises(Exception) as e:
        _evaluate(dataset_copy, model, evaluator_config, request)
    assert e.match(r"An error occurred while wrapping the model.*")

    # scan error
    dataset_copy = dataset.copy()
    cl = model.meta.classification_labels
    cl.append("unknown_label")
    evaluator_config = {"model_config": {"classification_labels": cl}}

    with pytest.raises(Exception) as e:
        _evaluate(dataset_copy, model, evaluator_config, request)
    assert e.match(r"An error occurred while scanning the model for vulnerabilities.*")
