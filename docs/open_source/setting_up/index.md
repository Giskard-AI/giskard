# 🤖 Setting up the LLM Client

This guide focuses primarily on configuring and using various LLM clients supported to run Giskard's LLM-assisted functionalities. These clients include:

- OpenAI GPT models (such as GPT-3.5 and GPT-4)
- Azure OpenAI
- Mistral
- Ollama
- Any Custom Model

## OpenAI GPT-4 Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/openai)

```python
import os
import giskard

os.environ["OPENAI_API_KEY"] = "your-api-key"

# Optional, setup a model (default model is gpt-4)
giskard.llm.set_llm_model("gpt-4")
giskard.llm.embeddings.set_embedding_model("text-embedding-ada-002")
```

## Azure OpenAI Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/azure)


```python
import os
import giskard

os.environ["AZURE_API_KEY"] = "" # "my-azure-api-key"
os.environ["AZURE_API_BASE"] = "" # "https://example-endpoint.openai.azure.com"
os.environ["AZURE_API_VERSION"] = "" # "2023-05-15"
giskard.llm.set_llm_model("azure/<your_deployment_name>")
giskard.llm.embeddings.set_embedding_model("azure/<your_deployment_name>")

# optional
os.environ["AZURE_AD_TOKEN"] = ""
os.environ["AZURE_API_TYPE"] = ""
```

## Mistral Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/mistral)

```python
import os
import giskard

os.environ['MISTRAL_API_KEY'] = ""
giskard.llm.set_llm_model("mistral/mistral-tiny")
giskard.llm.embeddings.set_embedding_model("mistral/mistral-embed")

```

## Ollama Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/ollama)

```python
import litellm
import giskard

giskard.llm.set_llm_model("ollama/llama2") # See supported models here: https://docs.litellm.ai/docs/providers/ollama#ollama-models
litellm.api_base = "http://localhost:11434"

# TODO: embedding
```

## AWS Bedrock Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/bedrock)

```python
import os
import giskard

os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""
os.environ["AWS_REGION_NAME"] = ""
giskard.llm.set_llm_model("bedrock/anthropic.claude-3-sonnet-20240229-v1:0")
giskard.llm.embeddings.set_embedding_model("bedrock/amazon.titan-embed-text-v1")
```

## Gemini Client Setup

More information on [litellm documentation](https://docs.litellm.ai/docs/providers/gemini)

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
import giskard
import litellm
from litellm import CustomLLM, completion, get_llm_provider


class MyCustomLLM(CustomLLM):
    def completion(self, *args, **kwargs) -> litellm.ModelResponse:
        return litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello world"}],
            mock_response="Hi!",
        )

    def embedding(self, *args, **kwargs) -> litellm.EmbeddingResponse:
        return litellm.embedding(
            model="openai/text-embedding-ada-002",
            input=["Hello world"]
            
        )

my_custom_llm = MyCustomLLM()

litellm.custom_provider_map = [ # 👈 KEY STEP - REGISTER HANDLER
    {"provider": "my-custom-llm", "custom_handler": my_custom_llm}
]

giskard.llm.set_llm_model("my-custom-llm/my-fake-llm-model")
giskard.llm.embeddings.set_embedding_model("my-custom-llm/my-fake-embedding-model")


```

If you run into any issues configuring the LLM client, don't hesitate to [ask us on Discord](https://discord.com/invite/ABvfpbu69R) or open a new issue on [our GitHub repo](https://github.com/Giskard-AI/giskard).
