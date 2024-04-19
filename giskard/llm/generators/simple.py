from typing import Optional, Sequence

import json
from ast import Dict

from ...models.base import BaseModel
from ...utils.display import truncate
from ..client.base import ChatMessage
from .base import _BaseLLMGenerator

SYS_PROMPT = """You are auditing an AI agent. Your task is to generate syntetic inputs for this agent.

The user will provide a description of the agent, an example of its input format, languages to use, and the number of examples to generate. You must generate inputs specific to the agent and its input format. Carefully design each input to make it as varied and realistic as possible, given the agent description.

You must return a JSON object following this template:
{
    // Array of NUM EXAMPLES elements
    "inputs": [
        {
            // object with same form as INPUT FORMAT EXAMPLE
        },
        // ...
    ]
}
"""

PROMPT_TEMPLATE = """
### AGENT DESCRIPTION
{description}

### INPUT FORMAT EXAMPLE
{input_format}

### LANGUAGES
{languages}

### NUM EXAMPLES
{num_samples}
"""


USR_EXAMPLE_PROMPT = PROMPT_TEMPLATE.format(
    description="Question answering chatbot about climate change, based on IPCC reports",
    input_format='{"user_question": "...", "user_name": "Jeremy"}',
    languages="en, fr",
    num_samples=3,
)

AST_EXAMPLE_PROMPT = json.dumps(
    {
        "inputs": [
            {"user_question": "What is climate change and how will it affect the world?", "user_name": "Alice"},
            {
                "user_question": "Hi I'm Bob. I wanted to ask, what is the best thing I can do to reduce my carbon footprint?",
                "user_name": "Lea",
            },
            {
                "user_question": "Bonjour, je voulais savoir quelles sont les conséquences du changement climatique sur l'écosystème marin?",
                "user_name": "Mohammed",
            },
        ]
    }
)


class SimpleDataGenerator(_BaseLLMGenerator):
    def _make_dataset_name(self, model: BaseModel) -> str:
        return truncate(f"Synthetic dataset for {model.meta.name}")

    def _format_messages(
        self, model: BaseModel, num_samples: int, column_types: Optional[Dict] = None
    ) -> Sequence[ChatMessage]:
        prompt = PROMPT_TEMPLATE.format(
            description=model.description,
            input_format=json.dumps({f: "..." for f in model.feature_names}),
            languages=", ".join(self.languages),
            num_samples=num_samples,
        )
        return [
            ChatMessage(role="system", content=SYS_PROMPT),
            ChatMessage(role="user", content=USR_EXAMPLE_PROMPT),
            ChatMessage(role="assistant", content=AST_EXAMPLE_PROMPT),
            ChatMessage(role="user", content=prompt),
        ]
