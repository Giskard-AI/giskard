<p align="center">
  <img alt="giskardlogo" src="https://raw.githubusercontent.com/giskard-ai/giskard/main/readme/giskard_logo.png#gh-light-mode-only">
  <img alt="giskardlogo" src="https://raw.githubusercontent.com/giskard-ai/giskard/main/readme/giskard_logo_green.png#gh-dark-mode-only">
</p>
<h1 align="center" weight='300' >The testing framework dedicated to LLMs & other AI models</h1>
<h3 align="center" weight='300' >Scan AI models to detect risks of performance issues. In 4 lines of code. </h3>
<div align="center">

  [![GitHub release](https://img.shields.io/github/v/release/Giskard-AI/giskard)](https://github.com/Giskard-AI/giskard/releases)
  [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/Giskard-AI/giskard/blob/main/LICENSE)
  [![CI](https://github.com/Giskard-AI/giskard/actions/workflows/build-python.yml/badge.svg?branch=main)](https://github.com/Giskard-AI/giskard/actions/workflows/build-python.yml?query=branch%3Amain)
  [![Sonar](https://sonarcloud.io/api/project_badges/measure?project=giskard&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=giskard)
  [![Giskard on Discord](https://img.shields.io/discord/939190303397666868?label=Discord)](https://gisk.ar/discord)

  <a rel="me" href="https://fosstodon.org/@Giskard"></a>

</div>
<h3 align="center">
   <a href="https://docs.giskard.ai/en/latest/index.html"><b>Documentation</b></a> &bull;
   <a href="https://www.giskard.ai/knowledge-categories/blog/?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog"><b>Blog</b></a> &bull;
  <a href="https://www.giskard.ai/?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog"><b>Website</b></a> &bull;
  <a href="https://gisk.ar/discord"><b>Discord Community</b></a> &bull;
  <a href="https://www.giskard.ai/about?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog#advisors"><b>Advisors</b></a>
 </h3>
<br />

## Install Giskard 🐢
Install the latest version of Giskard from PyPi using pip:
```sh
pip install "giskard[llm]" -U
```
We officially support Python 3.9, 3.10 and 3.11.
## Try in Colab 📙
[Open Colab notebook](https://colab.research.google.com/github/giskard-ai/giskard/blob/main/docs/getting_started/quickstart/quickstart_llm.ipynb)

______________________________________________________________________

Giskard is a Python library that **automatically detects performance issues** in AI applications. The library covers LLM-based applications such as RAG agents, all the way to traditional ML models for tabular data. Issues detected include: 
- Hallucinations
- Harmful content generation
- Prompt injection
- Robustness issues
- Sensitive information disclosure
- Stereotypes & discrimination
- many more...

[//]: # (TODO: replace with GIF for IPCC scan)
<p align="center">
  <img src="https://raw.githubusercontent.com/giskard-ai/giskard/main/readme/scan_example.gif" alt="Scan Example" width="800">
</p>

Instantaneously generate evaluation datasets for your RAG applications ⤵️

[//]: # (TODO: replace with an example of dataset generated + GIF of RAGET)
<p align="center">
  <img src="https://raw.githubusercontent.com/giskard-ai/giskard/main/readme/suite_example.png" alt="Test Suite Example" width="800">
</p>


Giskard works with any model, in any environment and integrates seamlessly with your favorite tools ⤵️ <br/>

[//]: # (TODO: add logos of LLM providers, remove some logos like pandas, github, kaggle, xgboost, fastai, pytorch ignite)
<p align="center">
  <img width='600' src="https://raw.githubusercontent.com/giskard-ai/giskard/main/readme/tools.png">
</p>
<br/>


# Contents

1. 🤸‍♀️ **[Quickstart](#%EF%B8%8F-quickstart)**
2. 👋 **[Community](#-community)**


# 🤸‍♀️ Quickstart

## 1. 🏗️ Build a LLM agent

Let's build an agent that answers questions about climate change, based on the 2023 Climate Change Synthesis Report by the IPCC.

Before starting let's install the required libraries:
```sh
pip install langchain tiktoken "pypdf<=3.17.0"
```


```python
from langchain import OpenAI, FAISS, PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Prepare vector store (FAISS) with IPPC report
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100, add_start_index=True)
loader = PyPDFLoader("https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_LongerReport.pdf")
db = FAISS.from_documents(loader.load_and_split(text_splitter), OpenAIEmbeddings())

# Prepare QA chain
PROMPT_TEMPLATE = """You are the Climate Assistant, a helpful AI assistant made by Giskard.
Your task is to answer common questions on climate change.
You will be given a question and relevant excerpts from the IPCC Climate Change Synthesis Report (2023).
Please provide short and clear answers based on the provided context. Be polite and helpful.

Context:
{context}

Question:
{question}

Your answer:
"""

llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0)
prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["question", "context"])
climate_qa_chain = RetrievalQA.from_llm(llm=llm, retriever=db.as_retriever(), prompt=prompt)
```

## 2. 🔎 Scan your model for issues

Next, wrap your agent to prepare it for Giskard's scan:

```python
import giskard
import pandas as pd

def model_predict(df: pd.DataFrame):
    """Wraps the LLM call in a simple Python function.

    The function takes a pandas.DataFrame containing the input variables needed
    by your model, and must return a list of the outputs (one for each row).
    """
    return [climate_qa_chain.run({"query": question}) for question in df["question"]]

# Don’t forget to fill the `name` and `description`: they are used by Giskard
# to generate domain-specific tests.
giskard_model = giskard.Model(
    model=model_predict,
    model_type="text_generation",
    name="Climate Change Question Answering",
    description="This model answers any question about climate change based on IPCC reports",
    feature_names=["question"],
)
```

✨✨✨Then run Giskard's magical scan✨✨✨
```python
scan_results = giskard.scan(giskard_model)
```
Once the scan completes, you can display the results directly in your notebook:

```python
display(scan_results)

# Or save it to a file
scan_results.to_html("scan_results.html")
```

*If you're facing issues, check out our [docs](https://docs.giskard.ai/en/stable/open_source/scan/scan_llm/index.html) for more information.*

## 3. 🪄 Automatically generate an evaluation dataset

If the scan found issues in your model, you can automatically extract an evaluation dataset based on the vulnerabilities found:

```python
test_suite = scan_results.generate_test_suite("My first test suite")
```

If you're testing a RAG application, you can get an even more in-depth assessment using RAGET, Giskard's RAG Evaluation Toolkit.

RAGET can generate automatically a list of `question`, `reference_answer` and `reference_context` from the knowledge base of the RAG. It relies on a chain of LLM operations to generate realistic questions across different types. You can then use this generated test set to evaluate your RAG agent.

By default, RAGET automatically generates 6 different question types (these can be selected if needed, see advanced question generation). The total number of questions is divided equally between each question type. To make the question generation more relevant and accurate, you can also provide a description of your agent.

```python

from giskard.rag import generate_testset, KnowledgeBase

# Load your data and initialize the KnowledgeBase
df = pd.read_csv("path/to/your/knowledge_base.csv")

knowledge_base = KnowledgeBase.from_pandas(df, columns=["column_1", "column_2"])

# Generate a testset with 10 questions & answers for each question types (this will take a while)
testset = generate_testset(
    knowledge_base, 
    num_questions=60,
    language='en',  # optional, we'll auto detect if not provided
    agent_description="A customer support chatbot for company X", # helps generating better questions
)
```

Depending on how many questions you generate, this can take a while. Once you’re done, you can save this generated test set for future use:

```python
# Save the generated testset
testset.save("my_testset.jsonl")
```
You can easily load it back

```python
from giskard.rag import QATestset

loaded_testset = QATestset.load("my_testset.jsonl")

# Convert it to a pandas dataframe
df = loaded_testset.to_pandas()
```

# 👋 Community
We welcome contributions from the AI community! Read this [guide](CONTRIBUTING.md) to get started.

Join our thriving community on our Discord server: [join Discord server](https://gisk.ar/discord)

🌟 [Leave us a star](https://github.com/Giskard-AI/giskard), it helps the project to get discovered by others and keeps us motivated to build awesome open-source tools! 🌟

❤️ You can also [sponsor us](https://github.com/sponsors/Giskard-AI) on GitHub. With a monthly sponsor subscription, you can get a sponsor badge and get your bug reports prioritized. We also offer one-time sponsoring if you want us to get involved in a consulting project, run a workshop, or give a talk at your company.
