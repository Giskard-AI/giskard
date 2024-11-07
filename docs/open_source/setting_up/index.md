# 🤖 Setting up the LLM Client

This guide focuses primarily on configuring and using various LLM clients supported to run Giskard's LLM-assisted functionalities. We are using [LiteLLM](https://github.com/BerriAI/litellm) to handle the model calls, you can see the list of supported models in the [LiteLLM documentation](https://docs.litellm.ai/docs/providers).

## OpenAI Client Setup

More information on [LiteLLM documentation](https://docs.litellm.ai/docs/providers/openai)

### Setup using .env variables

```python
import os
import giskard

os.environ["OPENAI_API_KEY"] = "your-api-key"

# Optional, setup a model (default model is gpt-4)
giskard.llm.set_llm_model("gpt-4")
giskard.llm.set_embedding_model("text-embedding-ada-002")

# Optional Keys - OpenAI Organization, OpenAI API Base
os.environ["OPENAI_ORGANIZATION"] = "your-org-id"
os.environ["OPENAI_API_BASE"] = "openaiai-api-base"
```

### Setup using completion params

```python
import giskard

giskard.llm.set_llm_model("gpt-4", api_key="your-api-key")
giskard.llm.set_embedding_model("text-embedding-ada-002", api_key="your-api-key")
```

## Azure OpenAI Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/azure)

### Setup using .env variables

```python
import os
import giskard

os.environ["AZURE_API_KEY"] = "" # "my-azure-api-key"
os.environ["AZURE_API_BASE"] = "" # "https://example-endpoint.openai.azure.com"
os.environ["AZURE_API_VERSION"] = "" # "2023-05-15"

giskard.llm.set_llm_model("azure/<your_deployment_name>")
giskard.llm.set_embedding_model("azure/<your_deployment_name>")

# optional
os.environ["AZURE_AD_TOKEN"] = ""
os.environ["AZURE_API_TYPE"] = ""
```

### Setup using completion params

```python
import giskard

# Using api_key, api_base, api_version
giskard.llm.set_llm_model("azure/<your_deployment_name>", api_base="", api_version="", api_key="")
giskard.llm.set_embedding_model("azure/<your_deployment_name>", api_base="", api_version="", api_key="")

# Using azure_ad_token, api_base, api_version
giskard.llm.set_llm_model("azure/<your_deployment_name>", api_base="", api_version="", azure_ad_token="")
giskard.llm.set_embedding_model("azure/<your_deployment_name>", api_base="", api_version="", azure_ad_token="")
```


## Mistral Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/mistral)

### Setup using .env variables

```python
import os
import giskard

os.environ['MISTRAL_API_KEY'] = ""

giskard.llm.set_llm_model("mistral/mistral-tiny")
giskard.llm.set_embedding_model("mistral/mistral-embed")

```

## Ollama Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/ollama)

### Setup using completion params

```python
import giskard

giskard.llm.set_llm_model("ollama/llama2", api_base="http://localhost:11434") # See supported models here: https://docs.litellm.ai/docs/providers/ollama#ollama-models
# TODO: embedding
```

## AWS Bedrock Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/bedrock)

### Setup using .env variables

```python
import os
import giskard

os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""
os.environ["AWS_REGION_NAME"] = ""

giskard.llm.set_llm_model("bedrock/anthropic.claude-3-sonnet-20240229-v1:0")
giskard.llm.set_embedding_model("bedrock/amazon.titan-embed-text-v1")
```

## Gemini Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/gemini)

### Setup using .env variables

```python
import os
import giskard

os.environ["GEMINI_API_KEY"] = "your-api-key"

giskard.llm.set_llm_model("gemini/gemini-pro")
# TODO: embedding
```

## Custom Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/custom_llm_server    )

```python
import requests
import giskard
import litellm
import os
from typing import Optional


class MyCustomLLM(litellm.CustomLLM):
    def completion(self, messages: str, api_key: Optional[str] = None, **kwargs) -> litellm.ModelResponse:
        api_key = api_key or os.environ.get('MY_SECRET_KEY')
        if api_key is None:
            raise litellm.AuthenticationError("Api key is not provided")
        
        response = requests.post('https://www.my-fake-llm.ai/chat/completion', json={
            'messages': messages
        }, headers={'Authorization': api_key})
        
        return litellm.ModelResponse(**response.json())

    def embedding(self, inputs, api_key: Optional[str] = None, **kwargs) -> litellm.EmbeddingResponse:
        api_key = api_key or os.environ.get('MY_SECRET_KEY')
        if api_key is None:
            raise litellm.AuthenticationError("Api key is not provided")
        
        response = requests.post('https://www.my-fake-llm.ai/embeddings', json={
            'inputs': inputs
        }, headers={'Authorization': api_key})

        return litellm.EmbeddingResponse(**response.json())


my_custom_llm = MyCustomLLM()

litellm.custom_provider_map = [  # 👈 KEY STEP - REGISTER HANDLER
    {"provider": "my-custom-llm", "custom_handler": my_custom_llm}
]

api_key = os.environ['MY_SECRET_KEY']

giskard.llm.set_llm_model("my-custom-llm/my-fake-llm-model", api_key=api_key)
giskard.llm.set_embedding_model("my-custom-llm/my-fake-embedding-model", api_key=api_key)


```

If you run into any issues configuring the LLM client, don't hesitate to [ask us on Discord](https://discord.com/invite/ABvfpbu69R) or open a new issue on [our GitHub repo](https://github.com/Giskard-AI/giskard).
