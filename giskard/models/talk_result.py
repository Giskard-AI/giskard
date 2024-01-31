from dataclasses import dataclass

from giskard.llm.client import LLMMessage


@dataclass
class TalkResult:
    response: LLMMessage
    summary: LLMMessage

    def __str__(self):
        return (
            f"LLM Response:\n"
            f"-------------\n"
            f"{self.response.content}\n\n"
            f"Full Conversation Summary:\n"
            f"--------------------------\n"
            f"{self.summary.content}"
        )
