import os
from unittest.mock import Mock, patch

import pytest

from giskard import scan
from tests.models.talk.talk_test_resources import (
    default_question,
    metric_tool_question,
    predict_tool_question,
    scan_tool_question,
    shap_tool_question,
    test_default_llm_responses,
    test_metric_tool_llm_responses,
    test_predict_tool_llm_responses,
    test_scan_tool_llm_responses_1,
    test_scan_tool_llm_responses_2,
    test_shap_tool_llm_responses,
    type_error_patterns,
)

os.environ["OPENAI_API_KEY"] = ""  # Mock openai token.


@pytest.mark.parametrize("dataset_name,model_name", [("titanic_dataset", "titanic_model")])
@patch(target="giskard.llm.client.copilot.GiskardCopilotClient", return_value=Mock())
def test_talk(mock_client, dataset_name, model_name, request):
    """Test the 'talk' feature.

    The responses from OpenAI LLM are mocked using unittest.mock.patch. Mocked LLM responses chains for different
    scenarios are located in the `talk_test_resources`.
    Specifically, sequential calls to the `GiskardCopilotClient.complete` were mocked with pre-calculated LLM responses.
    """
    dataset = request.getfixturevalue(dataset_name)
    model = request.getfixturevalue(model_name)
    scan_report = scan(model, dataset)

    # Test if an exception is raised when the necessary parameters are omitted.
    with pytest.raises(TypeError, match=type_error_patterns["question_dataset"]):
        model.talk()

    with pytest.raises(TypeError, match=type_error_patterns["dataset"]):
        model.talk(question=default_question)

    with pytest.raises(TypeError, match=type_error_patterns["question"]):
        model.talk(dataset=dataset)

    # Test if no exception is raised when the necessary parameters are passed.
    mock_client.return_value.complete.side_effect = lambda *args, **kwargs: next(test_default_llm_responses)
    model.talk(question=default_question, dataset=dataset, context="")
    model.talk(question=default_question, dataset=dataset, scan_report=scan_report)
    model.talk(question=default_question, dataset=dataset, context="", scan_report=scan_report)

    # Test tools calls.
    # Predict.
    mock_client.return_value.complete.side_effect = lambda *args, **kwargs: next(test_predict_tool_llm_responses)
    assert not model.talk(question=predict_tool_question, dataset=dataset).tool_errors

    # SHAP.
    mock_client.return_value.complete.side_effect = lambda *args, **kwargs: next(test_shap_tool_llm_responses)
    assert not model.talk(question=shap_tool_question, dataset=dataset).tool_errors

    # Metric.
    mock_client.return_value.complete.side_effect = lambda *args, **kwargs: next(test_metric_tool_llm_responses)
    assert not model.talk(question=metric_tool_question, dataset=dataset).tool_errors

    # Scan.
    mock_client.return_value.complete.side_effect = lambda *args, **kwargs: next(test_scan_tool_llm_responses_1)
    assert not model.talk(question=scan_tool_question, dataset=dataset, scan_report=scan_report).tool_errors
    # Test if the scan tool raises error when 'scan_report' is not provided.
    mock_client.return_value.complete.side_effect = lambda *args, **kwargs: next(test_scan_tool_llm_responses_2)
    assert model.talk(question=scan_tool_question, dataset=dataset).tool_errors
