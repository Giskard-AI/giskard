from typing import Optional

from dataclasses import dataclass

from ...llm.client import ChatMessage


@dataclass
class QAGenerationPrompt:
    system_prompt: str
    user_input_template: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None

    def _format_example_prompt(self, examples):
        if examples is not None:
            return examples
        elif self.example_prompt is not None:
            examples = []
            if self.example_input is not None:
                examples.append(ChatMessage(role="user", content=self.example_input))
            if self.example_prompt is not None:
                examples.append(ChatMessage(role="assistant", content=self.example_answer))
            return examples
        return []

    def to_messages(
        self,
        system_prompt_input,
        user_input,
        add_examples=False,
        examples=None,
    ):
        messages = [
            ChatMessage(
                role="system",
                content=self.system_prompt.format(**system_prompt_input),
            )
        ]
        if add_examples:
            messages.extend(self._format_example_prompt(examples))

        if self.user_input_template is None:
            messages.append(ChatMessage(role="user", content=user_input))
        else:
            messages.append(ChatMessage(role="user", content=self.user_input_template.format(**user_input)))

        return messages
