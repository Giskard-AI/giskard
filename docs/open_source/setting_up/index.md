# 🤖 Setting up the LLM Client

This guide focuses primarily on configuring and using various LLM clients supported to run Giskard's LLM-assisted functionalities. These clients include:
- OpenAI GPT models (such as GPT-3.5 and GPT-4)
- Azure OpenAI
- Mistral
- Ollama
- Any Custom Model

## OpenAI GPT-4 Client Setup

```python
import giskard
import os
from giskard.llm.client.openai import OpenAIClient

os.environ["OPENAI_API_KEY"] = "sk-…"

giskard.llm.set_llm_api("openai")
oc = OpenAIClient(model="gpt-4-turbo-preview")
giskard.llm.set_default_client(oc)
```

## Azure OpenAI Client Setup

```python
import os
from giskard.llm import set_llm_model

os.environ['AZURE_OPENAI_API_KEY'] = '...'
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://xxx.openai.azure.com'
os.environ['OPENAI_API_VERSION'] = '2023-07-01-preview'


# You'll need to provide the name of the model that you've deployed
# Beware, the model provided must be capable of using function calls
set_llm_model('my-gpt-4-model')
```

## Mistral Client Setup

```python
import os
from giskard.llm.client.mistral import MistralClient

os.environ["MISTRAL_API_KEY"] = "sk-…"

mc = MistralClient()
giskard.llm.set_default_client(mc)
```

## Ollama Client Setup

The Ollama setup involves configuring an OpenAI client customized for the Ollama API:

```python
from openai import OpenAI
from giskard.llm.client.openai import OpenAIClient
from giskard.llm.client.mistral import MistralClient

# Setup the Ollama client with API key and base URL
_client = OpenAI(base_url="http://localhost:11434/v1/", api_key="ollama")
oc = OpenAIClient(model="gemma:2b", client=_client)
giskard.llm.set_default_client(oc)
```

## Claude 3 Client Setup

The Claude 3 setup involves configuring a Bedrock client:

```python
import os
import boto3
import giskard

from giskard.llm.client.bedrock import ClaudeBedrockClient

bedrock_runtime = boto3.client("bedrock-runtime", region_name=os.environ["AWS_DEFAULT_REGION"])
claude_client = ClaudeBedrockClient(bedrock_runtime, model="anthropic.claude-3-haiku-20240307-v1:0")
giskard.llm.set_default_client(claude_client)
```

## Custom Client Setup

```python
import giskard
from typing import Sequence, Optional
from giskard.llm.client import set_default_client
from giskard.llm.client.base import LLMClient, ChatMessage


class MyLLMClient(LLMClient):
    def __init__(self, my_client):
        self._client = my_client

    def complete(
            self,
            messages: Sequence[ChatMessage],
            temperature: float = 1,
            max_tokens: Optional[int] = None,
            caller_id: Optional[str] = None,
            seed: Optional[int] = None,
            format=None,
    ) -> ChatMessage:
        # Create the prompt
        prompt = ""
        for msg in messages:
            if msg.role.lower() == "assistant":
                prefix = "\n\nAssistant: "
            else:
                prefix = "\n\nHuman: "

            prompt += prefix + msg.content

        prompt += "\n\nAssistant: "

        # Create the body
        params = {
            "prompt": prompt,
            "max_tokens_to_sample": max_tokens or 1000,
            "temperature": temperature,
            "top_p": 0.9,
        }
        body = json.dumps(params)

        response = self._client.invoke_model(
            body=body,
            modelId=self._model_id,
            accept="application/json",
            contentType="application/json",
        )
        data = json.loads(response.get("body").read())

        return ChatMessage(role="assistant", message=data["completion"])

set_default_client(MyLLMClient())
```

If you run into any issues configuring the LLM client, don't hesitate to [ask us on Discord](https://discord.com/invite/ABvfpbu69R) or open a new issue on [our GitHub repo](https://github.com/Giskard-AI/giskard).
