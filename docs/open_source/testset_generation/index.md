# 🧰 RAG toolset
The Giskard python library provides a toolset dedicated to Retrieval Augmented Generative models (RAGs) that generates question & answer pairs from the knowledge base of the model. The generated testset is then used to evaluate your model. 

## Generate questions with difficulty levels
You can currently generate questions with three difficulty levels:
- **Easy questions (level 1):** simple questions generated from an excerpt of the knowledge base
- **Complex questions: (level 2)** questions made more complex by paraphrasing
- **Distracting questions (level 3):** questions made even more difficult by adding a distracting element which is related to the knowledge base but irrelevant to the question

These three difficulty levels allows to evaluate different components of your model. Easy questions are directly generated from your knowledge base. They assess the quality of the answer generation from the context, i.e. the quality of the LLM answer. Complex and distracting questions are more challenging as they can perturb the retrieval componenent of the RAG. These questions are more realistic of a user seeking precise information with your model.

## Before starting

Before starting, make sure you have installed the LLM flavor of Giskard:

```bash
pip install "giskard[llm]"
```

To use the RAG testset generation and evaluation tools, you need to have an OpenAI API key. You can set it in your notebook
like this:

:::::::{tab-set}
::::::{tab-item} OpenAI

```python
import os

os.environ["OPENAI_API_KEY"] = "sk-…"
```

::::::
::::::{tab-item} Azure OpenAI

Require `openai>=1.0.0`
Make sure that both the LLM and Embeddings models are both deployed on the Azure endpoint. The default embedding model used by the Giskard client is `text-embedding-ada-002`. 

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

::::::
:::::::

We are now ready to start.


## Step 1: Format and load your Knowledge Base
The RAG toolset currently only handles knowledge bases as pandas `DataFrame`. If the DataFrame has multiple columns,
they are concatenated automatically. If only some of the columns contains relevant information, you can specify it when building the generator by passing a list of column names to the `knowledge_base_features` argument (see [API Reference](https://docs.giskard.ai/en/latest/reference/rag-toolset/testset_generation.html#giskard.rag.KnowledgeBaseTestsetGenerator)).


```python
knowledge_base_df = pd.read_csv("path/to/your/knowledge_base.csv")
feature_names = ["col1", "col2"]
```

## Step 2: Generate the testset
Once the knowledge base is loaded as a pandas `DataFrame`, you can generate the testset with the 
`KnowledgeBaseTestsetGenerator`. 


```python
from giskard.rag import KnowledgeBaseTestsetGenerator

generator = KnowledgeBaseTestsetGenerator(
    knowledge_base_df, 
    model_name="Model name", # Optional, provide a name to your model to get better fitting questions
    model_description="Description of the model", # Optional, briefly describe the task done by your model
    knowledge_base_features=feature_names
)

# Generate a testset with 10 questions & answers for each difficulty level
testset = generator.generate_dataset(num_samples=10, difficulty=[1, 2])
```

The test set will be a subclass of {ref}`giskard.Dataset`. You can also get it as a pandas DataFrame by accessing `testset.df`.

Here's an example of the generated test set:

| question | reference_context | reference_answer | difficulty_level |
|----------|-------------------|------------------|------------------|
| For which countries can I track my shipping? | What is your shipping policy? We offer free shipping on all orders over \$50. For orders below \$50, we charge a flat rate of \$5.99. We offer shipping services to customers residing in all 50 states of the US, in addition to providing delivery options to Canada and Mexico. ------  How can I track my order? Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. | We ship to all 50 states in the US, as well as to Canada and Mexico. We offer tracking for all our shippings. | 1 |

## Step 3: Wrap your model
Before evaluating your model, you must wrap it as a `giskard.Model`. This step is necessary to ensure a common format for your model and its metadata. You can wrap anything as long as you can represent it in a Python function (for example an API call call to Azure or OpenAI). We also have pre-built wrappers for LangChain objects, or you can create your own wrapper by extending the `giskard.Model` class if you need to wrap a complex object such as a custom-made RAG communicating with a vectorstore.

To do so, you can follow the instructions from the [LLM Scan feature](../scan/scan_llm/index.md#step-1-wrap-your-model) or from the {doc}`Reference API </reference/models/index>`. Make sure that you pass `feature_names = "question"` when wrapping your model, so that it matches the question column of the testset. 

Detailed examples can also be found on our {doc}`LLM tutorials section </tutorials/llm_tutorials/index>`.


## Step 4: Generate a test suite to evaluate your model
Once your `testset` is ready, you can turn it into an actionable test suite that you can save and reuse in further iterations. Note that you need to pass your wrapped model when executing the suite, since the suite is generated only from the testset.

```python
test_suite = testset.to_test_suite("My first test suite")
test_suite.run(giskard_model)
```

Jump to the [test customization](https://docs.giskard.ai/en/latest/open_source/customize_tests/index.html) and [test integration](https://docs.giskard.ai/en/latest/open_source/integrate_tests/index.html) sections to find out everything you can do with test suites.


## Next: upload your test suite to the Giskard Hub
Uploading a test suite to the hub allows you to:
* Compare the quality of different models and prompts to decide which one to promote
* Create more tests relevant to your use case, combining input prompts that make your model fail and custome evaluation criteria
* Share results, and collaborate with your team to integrate business feedback

To upload your test suite, you must have created a project on Giskard Hub and instantiated a Giskard Python client. If you haven't done this yet, follow the first steps of [upload your object](https://docs.giskard.ai/en/latest/giskard_hub/upload/index.html#upload-your-object) guide.

Then, upload your test suite like this:
```python
test_suite.upload(giskard_client, project_id) #project_id should be the id of the Giskard project in which you want to upload the suite
```

[Here's a demo](https://huggingface.co/spaces/giskardai/giskard) of the Giskard Hub in action.

## What data are being sent to OpenAI/Azure OpenAI

In order to perform LLM-assisted detectors, we will be sending the following information to OpenAI/Azure OpenAI:

- Data provided in your knowledge base
- Text generated by your model
- Model name and description

## Will the testset generation work in any language?
The testset quality depends on GPT-4 capabilities regarding your model's language. 

## Troubleshooting
If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in our #support channel.