from dataclasses import dataclass

from giskard.llm.client import LLMOutput


@dataclass
class TalkResult:
    response: LLMOutput
    summary: LLMOutput

    def __str__(self):
        return (
            f"LLM Response:\n"
            f"-------------\n"
            f"{self.response.message}\n\n"
            f"Full Conversation Summary:\n"
            f"--------------------------\n"
            f"{self.summary.message}"
        )
