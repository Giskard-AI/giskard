# 🎯 RAGET Testset Generation 

> ⚠️ **The RAG Evaluation Toolkit (RAGET) is currently in early version and is subject to change**. Feel free to reach out on our [Discord server](https://discord.gg/fkv7CAr3FE) if you have any trouble or to provide feedback.


Waiting to collect data from production to evaluate your RAG applications extensively is a risky business. But building 
an in-house evaluation dataset is a painful task that requires manual curation and review. 

To help with this, the Giskard python library provides **RAGET: RAG Evaluation Toolkit**, a toolkit to evaluate RAG 
applications **automatically**.



(q_types)=
## What does RAGET do exactly?

RAGET automatically generates a list of `question`, `reference_answer` and `reference_context` from the knowledge 
base of the RAG. The **generated test set is then used to evaluate your RAG application**. 
All questions are asked to your application and its answers are compared against the reference answers to calculate a score.

RAGET is capable of targeting and evaluating the following components of a RAG application:
- **`Generator`**: the LLM used inside the RAG to generate the answers
- **`Retriever`**: fetch relevant documents from the knowledge base according to a user query
- **`Rewriter`** (optional): rewrite the user query to make it more relevant to the knowledge base or to account for chat history
- **`Router`** (optional): filter the query of the user based on his intentions (intentions detection)
- **`Knowledge Base`**: the set of documents given to the RAG to generate the answers

RAGET currently automatically generates 6 types of questions. Each of them are designed to target and evaluate specific 
components of the RAG system. 
```{list-table}
:header-rows: 1
:widths: 20, 50, 25
* - Question type
  - Description
  - Targeted RAG components
* - **Simple questions**
  - Simple questions generated from an excerpt of the knowledge base

    *Example: What is the capital of France?*
  - `Generator`, `Retriever`, `Router`
* - **Complex questions**
  - Questions made more complex by paraphrasing

    *Example: What is the capital of the country of Victor Hugo?*
  - `Generator` 
* - **Distracting questions**
  - Questions made to confuse the retrieval part of the RAG with a distracting element from the knowledge base but irrelevant to the question

    *Example: Italy is beautiful but what is the capital of France?*
  - `Generator`, `Retriever`, `Rewriter`
* - **Situational questions**
  - Questions including user context to evaluate the ability of the generation to produce relevant answer according to the context

    *Example: I am planning a trip to Europe, what is the capital of France?*
  - `Generator`
* - **Double questions**
  - Questions with two distinct parts to evaluate the capabilities of the query rewriter of the RAG 

    *Example: What is the capital and the population of France?*
  - `Generator`, `Rewriter`
* - **Conversational questions**
  - Questions made as part of a conversation, first message describe the context of the question that is ask in the last message, also tests the rewriter

    *Example: (two separate messages)* 
      - *I would like to know some information about France.* 
      - *What is its capital city?*
  - `Rewriter`
```



## Before starting

Before starting, make sure you have installed the LLM flavor of Giskard:

```bash
pip install "giskard[llm]"
```

To use the RAG test set generation and evaluation tools, you'll need an OpenAI API key. You can set it in your notebook
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
Make sure that both the LLM and Embeddings models are deployed on the Azure endpoint. The default embedding model used 
by the Giskard client is `text-embedding-ada-002`. 

```python
import os
from giskard.llm import set_llm_model, set_llm_api

os.environ['AZURE_OPENAI_API_KEY'] = '...'
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://xxx.openai.azure.com'
os.environ['OPENAI_API_VERSION'] = '2023-07-01-preview'


# You'll need to provide the name of the model that you've deployed
# Beware, the model provided must be capable of using function calls
set_llm_api('azure')
set_llm_model('my-gpt-4-model')
```

::::::
:::::::



## Prepare your Knowledge Base

Prepare your data or knowledge base in a pandas `DataFrame`. Then, initialize the 
{class}`~giskard.rag.knowledge_base.KnowledgeBase` by passing your dataframe. 

If certain columns in your dataframe are not relevant for the generation of questions (e.g. they contain metadata), 
make sure to specify their names in the `knowledge_base_columns` argument 
(see {class}`~giskard.rag.knowledge_base.KnowledgeBase`).

```python

from giskard.rag import generate_testset, KnowledgeBase

# Load your data and initialize the KnowledgeBase
knowledge_base_df = pd.read_csv("path/to/your/knowledge_base.csv")
knowledge_base = KnowledgeBase(knowledge_base_df, 
                               knowledge_base_columns=["column_1", "column_2"])
```


## Generate a test set
By default, **RAGET automatically generates 6 different [question types](q_types)**. The total number of questions is 
divided equally between each question type. To make the question generation more relevant and accurate, you can also 
provide a description of your application. 

```python
# Generate a testset with 10 questions & answers for each question types (this will take a while)
testset = generate_testset(
    knowledge_base, 
    num_questions=60,
    language='en', # Optional, if you want to  generate questions in a specific language
    # Optionally, you can provide a description of your RAG assistant to improve the questions quality.
    assistant_description="An assistant that answers common questions about our products",
)
```

You can save this generated test set and load it back for future use.

```python
# Save the generated testset
testset.save("my_testset.jsonl")

# Load it back
from giskard.rag import QATestset

loaded_testset = QATestset.load("my_testset.jsonl")
```

You can also convert it to a pandas DataFrame with `testset.to_pandas()`:

```py
# Convert it to a pandas dataframe
df = loaded_testset.to_pandas()
```

Here's an example of a generated question:

| question | reference_context | reference_answer |  metadata |
|----------|-------------------|------------------|-----------|
| For which countries can I track my shipping? | Document 1: We offer free shipping on all orders over \$50. For orders below \$50, we charge a flat rate of \$5.99. We offer shipping services to customers residing in all 50 states of the US, in addition to providing delivery options to Canada and Mexico. Document 2: Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. | We ship to all 50 states in the US, as well as to Canada and Mexico. We offer tracking for all our shippings. | {"question_type": "simple", "seed_document_id": 1, "topic": "Shipping policy"} |

Each row of the test set contains 5 columns:
- `question`: the generated question
- `reference_context`: the context that can be used to answer the question
- `reference_answer`: the answer to the question (generated with GPT-4)
- `conversation_history`: not shown in the table above, contain the history of the conversation with the assistant as a list, only relevant for conversational question, otherwise it contains an empty list.
- `metadata`: a dictionary with various metadata about the question, this includes the `question_type`, `seed_document_id` the id of the document used to generate the question and the `topic` of the question



### Select the question types in your test set

By default, the test set contains all question types. **You can change this by providing question generators** to the `giskard.rag.generate_testset` function. Generators are available inside the `question_generators` module. For instance to generate only complex and double questions use the following:

```python
from giskard.rag.question_generators import complex_questions, double_questions

testset = generate_testset(
    knowledge, 
    num_questions=60,
    language='en',
    assistant_description=assistant_description,
    question_modifiers=[complex_questions, double_questions],
    generate_simple_question=False,
)
```


## What data are being sent to OpenAI/Azure OpenAI

In order to perform the question generation, we will be sending the following information to OpenAI/Azure OpenAI:

- Data provided in your knowledge base
- Text generated by your model
- Model name and description

## Will the test set generation work in any language?
Yes, you can specify the language of the generated questions when calling the `generate_testset` function. Ultimately, the quality of the generated questions will depend on the LLM performance in the desired language.

## Troubleshooting
If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in our #support channel.
