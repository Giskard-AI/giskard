# 🤖 Setting up the LLM Client

This guide focuses primarily on configuring and using various language model (LLM) clients supported by Giskard, including but not limited to:
- OpenAI GPT models (such as GPT-3.5 and GPT-4)
- Azure OpenAI
- Mistral
- Ollama
- Any Custom Model

The core purpose of this page is to provide detailed instructions for **setting up different LLM clients**, a critical step that lays the groundwork for integrating these tools into your applications. This foundational setup is essential now, as understanding it will make the more detailed and practical applications discussed in subsequent sections more comprehensible. These future sections will explore specific use cases and demonstrate practical implementations of the LLM capabilities in varied scenarios, building on the initial setup detailed here.

Whether you are enhancing an existing application or building a new one from the ground up, the guidance provided here will ensure you have a robust setup ready to incorporate any of the supported language models efficiently and effectively.


## Setting Up Different LLM Clients and Running the Scans

### Setting Up Different LLM Clients

To ensure versatility and robustness in your applications, it's essential to integrate and configure multiple language model (LLM) clients. Below, we provide detailed instructions on how to set up clients for OpenAI GPT-4, Azure OpenAI, Ollama, Mistral and a general Custom Model.


1. **OpenAI GPT-4 Client Setup:**
    ```python
    import giskard
    import os
    from giskard.llm.client.openai import OpenAIClient

    os.environ["OPENAI_API_KEY"] = "sk-…"

    giskard.llm.set_llm_api("openai")
    oc = OpenAIClient(model="gpt-4-turbo-preview")
    giskard.llm.set_default_client(oc)
    ```

    This setup enables detailed logging and configures the Giskard system to use the GPT-4 model hosted on OpenAI's API, ideal for scenarios requiring cutting-edge language processing capabilities.

2. **Azure OpenAI Client Setup:**
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

3. **Mistral Client Setup:**
    ```python
    import os
    from giskard.llm.client.mistral import MistralClient

    os.environ["MISTRAL_API_KEY"] = "sk-…"

    mc = MistralClient()
    giskard.llm.set_default_client(mc)
    ```

4. **Ollama Client Setup:**
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

5. **Custom Client Setup:**
    Let's see how to create a Custom Client and how set it as the default client for the Giskard scan

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

### Running the Scans

Once the LLM client is configured, the next step is to run scans to evaluate your model’s performance across various metrics. These scans are pivotal in ensuring that your model adheres to expected standards and behaves as intended under different scenarios. Below, we provide an example of how to execute a scan using Giskard with specific evaluation parameters. For a comprehensive guide on preparing your model and dataset for scanning, please refer to the [🔍 Scan a model section](../scan/index.md), in particular to the [📚 LLM scan subsection](../scan/scan_llm/index.md).

```python
# Example: Running a scan with specific evaluation parameters
report = gsk.scan(
    model=<your-giskard-model>,  # Replace <your-giskard-model> with the model you have prepared
    dataset=<your-giskard-dataset>,  # Replace <your-giskard-dataset> with the dataset applicable to your model
    raise_exceptions=True,  # This option will force the scan to raise exceptions if issues are detected
    params={
        "llm_harmful_content": dict(num_requirements=3, num_samples=1),
        "llm_implausible_output": dict(num_samples=10),
        "llm_information_disclosure": dict(num_requirements=3, num_samples=1),
        "llm_stereotypes_detector": dict(num_requirements=3, num_samples=1),
    },
)
print(report)
```

This script initiates a scan on your model using the configured dataset. The `params` dictionary specifies various aspects to evaluate, including harmful content, implausibility of outputs, information disclosure risks, and potential stereotypes, ensuring a thorough review of the model's outputs. Each parameter is configurable to match the depth and breadth of analysis required for your specific use case.