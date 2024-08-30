from dataclasses import dataclass

from giskard.llm.client import ChatMessage


@dataclass
class TalkResult:
    """The dataclass containing the result of the 'talk' call.

    Attributes
    ----------
    response : ChatMessage
        The response to the user's query.
    summary : ChatMessage
        The summary of the conversation between the user and the LLM agent.
    tool_errors : list[Exception]
        The list of errors raised during tools execution.
    """

    response: ChatMessage
    summary: ChatMessage
    tool_errors: list[Exception]

    def __repr__(self) -> str:
        """Return the 'talk' result.

        Returns
        -------
        str
            The 'Talk' result, containing an answer and a conversation summary.
        """
        return (
            f"LLM Response:\n"
            f"-------------\n"
            f"{self.response.content}\n\n"
            f"Full Conversation Summary:\n"
            f"--------------------------\n"
            f"{self.summary.content}\n\n"
            f"Tool Errors Raised: {len(self.tool_errors)}"
        )
