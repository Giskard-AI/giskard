import pytest

from giskard import scan


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("titanic_dataset", "titanic_model"),
        ("hotel_text_data", "hotel_text_model"),
    ],
)
def test_talk(dataset_name, model_name, request):
    _default_question = "What can you do?"

    # Fetch dataset and model.
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)

    # Get the scan report.
    scan_report = scan(model, dataset)

    # [1] Check if an exception is raised when the necessary parameters are omitted.
    with pytest.raises(
        TypeError, match="BaseModel\.talk\(\) missing 2 required positional arguments: 'question' and 'dataset'"
    ):
        model.talk()

    with pytest.raises(TypeError, match="BaseModel\.talk\(\) missing 1 required positional argument: 'dataset'"):
        model.talk(question=_default_question)

    with pytest.raises(TypeError, match="BaseModel\.talk\(\) missing 1 required positional argument: 'question'"):
        model.talk(dataset=dataset)

    # [2] Check if no exception is raised when the necessary parameters are passed.
    model.talk(question=_default_question, dataset=dataset, context="")
    model.talk(question=_default_question, dataset=dataset, scan_report=scan_report)
    model.talk(question=_default_question, dataset=dataset, context="", scan_report=scan_report)

    # [3] Check if the context can be passed.
    talk_result = model.talk(question=_default_question, dataset=dataset, context="")
    model.talk(question=_default_question, dataset=dataset, context=talk_result.summary)

    # [4] Check if tools are called with no errors.
    # Predict tool.
    question = "Give me predictions of the model on a given dataset. Use 'predict' tool."
    assert not model.talk(question=question, dataset=dataset).tool_errors

    # SHAP tool.
    question = "Calculate SHAP values of each feature. Use 'shap_explanation' tool."
    assert not model.talk(question=question, dataset=dataset).tool_errors

    # Metric tool.
    question = (
        "If the model is classification, calculate accuracy. If regression, then calculate R2 score. Use "
        "'calculate_metric' tool."
    )
    assert not model.talk(question=question, dataset=dataset).tool_errors

    # Scan tool.
    question = "Tell me, which performance issues/vulnerabilities does the model have. Use 'issues_scanner' tool."
    assert not model.talk(question=question, dataset=dataset, scan_report=scan_report).tool_errors

    # [5] Check if scan tool raises error when 'scan_report' is not provided.
    question = "Tell me, which performance issues/vulnerabilities does the model have. Use 'issues_scanner' tool."
    assert model.talk(question=question, dataset=dataset).tool_errors
