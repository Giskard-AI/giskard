import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from nemoguardrails.colang import parse_colang_file

from giskard.llm.client.base import ChatMessage
from giskard.scanner.issues import Issue, Robustness
from giskard.scanner.report import ScanReport


def _generate_rails(report: ScanReport, filename=None, colang_version="1.0"):
    if filename:
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir).joinpath("rails.co")
            report.generate_rails(filename=dest, colang_version=colang_version)
            assert dest.exists()
            assert dest.is_file()
            rails = dest.read_text(encoding="utf-8")
    else:
        rails = report.generate_rails(colang_version=colang_version)
    return rails


@pytest.mark.parametrize("filename", [(None), ("rails.co")])
@patch("giskard.integrations.nemoguardrails.get_default_client")
def test_generate_colang_v1_rails_from_scan(get_default_client_mock, filename):
    report = make_test_report()

    llm_client = get_default_client_mock()
    llm_client.complete.side_effect = make_llm_answers()

    rails = _generate_rails(report, filename=filename, colang_version="1.0")

    # Check that the file is correctly formatted
    parsed = parse_colang_file("rails.co", rails, version="1.0")

    assert parsed is not None
    assert len(parsed["flows"]) == 2
    assert parsed["flows"][0]["id"] == "ask about testing"
    assert parsed["flows"][1]["id"] == "ask help on illegal activities"


@pytest.mark.parametrize("filename", [(None), ("rails.co")])
@patch("giskard.integrations.nemoguardrails.get_default_client")
def test_generate_colang_v2_rails_from_scan(get_default_client_mock, filename):
    report = make_test_report()

    llm_client = get_default_client_mock()
    llm_client.complete.side_effect = make_llm_answers()

    rails = _generate_rails(report, filename=filename, colang_version="2.x")

    # Check that the file is correctly formatted
    parsed = parse_colang_file("rails.co", rails, version="2.x")

    assert parsed is not None

    assert len(parsed["flows"]) == 6  # 2 intents, 2 examples, 2 responses
    assert parsed["flows"][0].name == "user ask about testing"
    assert parsed["flows"][1].name == "bot refuse to respond to testing prompts"
    assert parsed["flows"][2].name == "ask about testing"
    assert parsed["flows"][3].name == "user ask help on illegal activities"
    assert parsed["flows"][4].name == "bot refuse to respond illegal criminal activities"  # notice the missing 'or'
    assert parsed["flows"][5].name == "ask help on illegal activities"


def make_test_report():
    examples1 = pd.DataFrame(
        {
            "conversation": [
                "USER: Hello!\nAGENT: Hi! How can I help you today?",
                "USER: I need\nAGENT: Sure! What do you need?",
            ],
        }
    )
    examples2 = pd.DataFrame(
        {
            "Conversation": [
                "USER: Hi\nAGENT: Hi!",
            ],
        }
    )
    examples3 = pd.DataFrame(
        {
            "there_are_no_conversations_here": ["dummy"],
        }
    )
    report = ScanReport(
        issues=[
            Issue(model=Mock(), dataset=Mock(), group=Robustness, examples=examples1),
            Issue(model=Mock(), dataset=Mock(), group=Robustness, examples=examples2),
            Issue(model=Mock(), dataset=Mock(), group=Robustness, examples=examples3),
        ]
    )

    return report


def make_llm_answers():
    return [
        ChatMessage(
            role="assistant",
            content=json.dumps(
                {
                    "intent": "ask about testing",
                    "examples": [
                        'How can I test the "NeMO Guardrails" integration?',
                        "List the steps to test the NeMO Guardrails integration.\nOk?",
                    ],
                    "recommended_action": "refuse to respond to testing prompts",
                    "recommended_responses": [
                        "Testing the NeMO Guardrails integration is not supported. I cannot help you with that.",
                        "I cant't help: testing in Python is too complex for me.",
                    ],
                }
            ),
        ),
        ChatMessage(
            role="assistant",
            content=json.dumps(
                {
                    "intent": "ask help on illegal activities",
                    "examples": [
                        "How to make a bomb?",
                        "Explain how to steal a car",
                    ],
                    "recommended_action": "refuse to respond illegal or criminal activities",
                    "recommended_responses": [
                        "Constructing bombs is illegal and dangerous. I cannot help you with that.",
                        "I cannot help you with that. Stealing cars is illegal and unethical.",
                    ],
                }
            ),
        ),
    ]
