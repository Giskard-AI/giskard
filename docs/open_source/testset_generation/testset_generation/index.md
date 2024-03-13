# 🎯 RAG Testset Generation

> ⚠️ **The RAG toolset is currently in early version and is subject to change**. Feel free to reach out on our [Discord server](https://discord.gg/fkv7CAr3FE) if you have any trouble with test set generation or to provide feedback.


The Giskard python library provides a toolset dedicated to Retrieval Augmented Generative models (RAGs) that generates a list of `question`, `reference_answer` and `reference_context` from the knowledge base of the model. The generated test set is then used to evaluate your RAG model. All questions are asked to your model and its answers are compared against the reference answers to create a score. 

## Before starting

Before starting, make sure you have installed the LLM flavor of Giskard:

```bash
pip install "giskard[llm]"
```

To use the RAG test set generation and evaluation tools, you need to have an OpenAI API key. You can set it in your notebook
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

We are now ready to start.


## Prepare your Knowledge Base

To start, you only need your data or knowledge base in a pandas `DataFrame`. Then, you can initialize the {class}`~giskard.rag.knowledge_base.KnowledgeBase` by passing your dataframe. 

If some columns in your dataframe are not relevant for the generation of questions (e.g. they contain metadata), make sure you specify
column names to the `knowledge_base_columns` argument (see {class}`~giskard.rag.knowledge_base.KnowledgeBase`).

```python

from giskard.rag import generate_testset, KnowledgeBase

# Load your data and initialize the KnowledgeBase
knowledge_base_df = pd.read_csv("path/to/your/knowledge_base.csv")
knowledge_base = KnowledgeBase(knowledge_base_df, 
                               knowledge_base_columns=["column_1", "column_2"])
```


## Generate a basic test set
We are ready to generate the test set. We can start with a small test set of 10 questions and answers for each question type.
To make the question generation more accurate, you can also provide a description of your assistant. This will help the generator to generate questions that are more relevant to your assistant's task. 

```python
# Generate a testset with 10 questions & answers for each question types (this will take a while)
testset = generate_testset(
    knowledge_base, 
    num_questions=10,
    language='en', # Optional, if you want to  generate questions in a specific language
    # Optionally, you can provide a description of your RAG assistant to improve the questions quality.
    assistant_description="An assistant that answers common questions about our products",
)
```

You can save the testset and load it back for future use.

```python
# Save the generated testset
testset.save("my_testset.jsonl")

# Load it back
from giskard.rag import QATestset

loaded_testset = QATestset.load("my_testset.jsonl")
```

The test set will be an instance of {class}`~giskard.rag.QATestset`. You can save it and load it later with `QATestset.load("path/to/testset.jsonl")`.

You can also convert it to a pandas DataFrame with `testset.to_pandas()`:

```py
# Convert it to a pandas dataframe
df = loaded_testset.to_pandas()
```

Let's have a look at the generated questions:

| question | reference_context | reference_answer |  metadata |
|----------|-------------------|------------------|-----------|
| For which countries can I track my shipping? | What is your shipping policy? We offer free shipping on all orders over \$50. For orders below \$50, we charge a flat rate of \$5.99. We offer shipping services to customers residing in all 50 states of the US, in addition to providing delivery options to Canada and Mexico. ------  How can I track my order? Once your purchase has been successfully confirmed and shipped, you will receive a confirmation email containing your tracking number. You can simply click on the link provided in the email or visit our website's order tracking page. | We ship to all 50 states in the US, as well as to Canada and Mexico. We offer tracking for all our shippings. | {"question_type": 1, "seed_document_id": 0, "topic": "Shipping policy"} |

As you can see, the data contains 4 columns:
- `question`: the generated question
- `reference_context`: the context that can be used to answer the question
- `reference_answer`: the answer to the question (generated with GPT-4)
- `conversation_history`: not shown in the table above, contain the history of the conversation with the assistant as a list, only relevant for conversational question, otherwise it contains an empty list.
- `metadata`: a dictionnary with various metadata about the question, this includes the `question_type` (an integer between 1 and 6), `seed_document_id` the id of the document used to generate the question and the `topic` of the question

(difficulty_levels)=
## Generate more elaborated questions

By default, the testset contains only simple questions. You can change this by providing question modifiers to the `generate_testset` function. 

```python
from giskard.rag.question_modifiers import complex_questions_modifier, double_questions_modifier

testset = generate_testset(
    knowledge, 
    num_questions=20,
    language='en',
    assistant_description=assistant_description,
    question_modifiers=[complex_questions_modifier, double_questions_modifier],
    generate_simple_question=False,
)
```

You can currently generate multiple questions type using the question modifiers available in `giskard.rag.question_modifiers`. Each type of question helps you to evaluate specific componenents of your RAG. More question types will be added in the future to provide thorough evaluation of RAG systems. 

```{list-table}
:header-rows: 1
:widths: 20, 50, 25
* - Question modifier
  - Description
  - Targeted RAG component
* - **`BaseQuestionGenerator` (no modifier)**
  - Simple questions generated from an excerpt of the knowledge base
  - Basic retrieval and LLM generation
* - **`complex_questions_modifier`**
  - Questions made more complex by paraphrasing
  - LLM understanding and generation 
* - **`distracting_questions_modifier`**
  - Questions made to confuse the retrieval part of the RAG with a distracting element from the knowledge base but irrelevant to the question
  - Robustness of retrieval
* - **`situational_questions_modifier`**
  - Questions including user context to evaluate the ability of the generation to produce relevant answer according to the context
  - LLM understanding and generation
* - **`double_questions_modifier`**
  - Questions with two distinct parts to evaluate the capabilities of the query rewriter of the RAG 
  - RAG rewriter
* - **`conversational_questions_modifier`**
  - Questions made as part of a conversation, first message describe the context of the question that is ask in the last message, also tests the rewriter
  - RAG rewriter
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
