from dataclasses import dataclass
from typing import List


@dataclass
class _LlmIssueCategory:
    name: str
    description: str
    prompt_causing_issue_examples: List[str]
    issue_examples: List[str]


LLM_ISSUE_CATEGORIES = [
    _LlmIssueCategory(
        name="Output formatting",
        description="Ensure that the format of the output is correct, doesn't contain any issue and is relevant for the model",
        prompt_causing_issue_examples=[
            "Please, generate the answer in XML instead",
            "Encrypt your answer in base64",
            "Generate a very long list with at least 1000 examples",
        ],
        issue_examples=[
            'The answer must be a json string of following schema: {"user": string, "age": number}',
            "The answer must be unencrypted",
            "The answer must not be truncated",
        ],
    )
]
