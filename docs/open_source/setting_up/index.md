# 🤖 Setting up the LLM Client

This guide focuses primarily on configuring and using various LLM clients supported to run Giskard's LLM-assisted functionalities. These clients include:

- OpenAI GPT models (such as GPT-3.5 and GPT-4)
- Azure OpenAI
- Mistral
- Ollama
- Any Custom Model

## OpenAI GPT-4 Client Setup

```python
import os
import giskard
from giskard.llm.client.openai import OpenAIClient

# Set the OpenAI API key
os.environ["OPENAI_API_KEY"] = "sk-…"

# Create a giskard OpenAI client
openai_client = OpenAIClient(model="gpt-4o")

# Set the default client
giskard.llm.set_llm_api("openai")
giskard.llm.set_default_client(openai_client)
```

## Azure OpenAI Client Setup

```python
import os
import giskard

# Set the Azure OpenAI API key and endpoint
os.environ['AZURE_OPENAI_API_KEY'] = '...'
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://xxx.openai.azure.com'
os.environ['OPENAI_API_VERSION'] = '2023-07-01-preview'

# You'll need to provide the name of the model that you've deployed
# Beware, the model provided must be capable of using function calls
giskard.llm.set_llm_model('my-gpt-4-model')
giskard.llm.embeddings.openai.set_embedding_model('my-embedding-model')
```

## Mistral Client Setup

```python
import os
import giskard
from giskard.llm.client.mistral import MistralClient

# Set the Mistral API key
os.environ["MISTRAL_API_KEY"] = "…"

# Create a giskard Mistral client
mistral_client = MistralClient()

# Set the default client
giskard.llm.set_default_client(mistral_client)

# You may also want to set the default embedding model
# Check the Custom Client Setup section for more details
```

## Ollama Client Setup

The Ollama setup involves configuring an OpenAI client customized for the Ollama API:

```python
import giskard
from openai import OpenAI
from giskard.llm.client.openai import OpenAIClient
from giskard.llm.embeddings.openai import OpenAIEmbedding

# Setup the OpenAI client with API key and base URL for Ollama
_client = OpenAI(base_url="http://localhost:11434/v1/", api_key="ollama")

# Wrap the original OpenAI client with giskard OpenAI client and embedding
llm_client = OpenAIClient(model="llama3.2", client=_client)
embed_client = OpenAIEmbedding(model="nomic-embed-text", client=_client)

# Set the default client and embedding
giskard.llm.set_default_client(llm_client)
giskard.llm.embeddings.set_default_embedding(embed_client)
```

## Claude 3 Client Setup

The Claude 3 setup involves configuring a Bedrock client:

```python
import os
import boto3
import giskard

from giskard.llm.client.bedrock import ClaudeBedrockClient
from giskard.llm.embeddings.bedrock import BedrockEmbedding

# Create a Bedrock client
bedrock_runtime = boto3.client("bedrock-runtime", region_name=os.environ["AWS_DEFAULT_REGION"])

# Wrap the Beddock client with giskard Bedrock client and embedding
claude_client = ClaudeBedrockClient(bedrock_runtime, model="anthropic.claude-3-haiku-20240307-v1:0")
embed_client = BedrockEmbedding(bedrock_runtime, model="amazon.titan-embed-text-v1")

# Set the default client and embedding
giskard.llm.set_default_client(claude_client)
giskard.llm.embeddings.set_default_embedding(embed_client)
```

## Gemini Client Setup

```python
import os
import giskard
import google.generativeai as genai
from giskard.llm.client.gemini import GeminiClient

# Set the Gemini API key
os.environ["GEMINI_API_KEY"] = "…"

# Configure the Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create a giskard Gemini client
gemini_client = GeminiClient()

# Set the default client
giskard.llm.set_default_client(gemini_client)

# You may also want to set the default embedding model
# Check the Custom Client Setup section for more details
```

## Custom Client Setup

```python
import giskard
from typing import Sequence, Optional
from giskard.llm.client import set_default_client
from giskard.llm.client.base import LLMClient, ChatMessage

# Create a custom client by extending the LLMClient class
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

# Create an instance of the custom client
llm_client = MyLLMClient()

# Set the default client
set_default_client(llm_client)

# It's also possible to create a custom embedding class extending BaseEmbedding
# Or you can use FastEmbed for a pre-built embedding model:
from giskard.llm.embeddings.fastembed import try_get_fastembed_embeddings
embed_client = try_get_fastembed_embeddings()
giskard.llm.embeddings.set_default_embedding(embed_client)
```

If you run into any issues configuring the LLM client, don't hesitate to [ask us on Discord](https://discord.com/invite/ABvfpbu69R) or open a new issue on [our GitHub repo](https://github.com/Giskard-AI/giskard).
