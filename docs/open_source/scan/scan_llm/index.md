# 📚  LLM scan

The Giskard python library provides an automatic scan functionality designed to automatically detect [potential vulnerabilities](https://docs.giskard.ai/en/latest/knowledge/llm_vulnerabilities/index.html) affecting your LLMs. It enables you to proactively identify and address key issues to ensure the reliability, fairness, and robustness of your LLMs.

## Step 1: Wrap your model

Start by **wrapping your model**.

:::::::{tab-set}
::::::{tab-item} Wrap a stand-alone LLM

Wrap your LLM's API prediction function in Giskard's Model class.

```python
def model_predict(df):
    return df["query"].apply(lambda x: llm_api.run({"query": x}))

giskard_model = giskard.Model(
    model=model_predict,
    model_type="text_generation",
    name="Climate Change Question Answering",  # Optional.
    description="This model answers any question about climate change based on IPCC reports"  # Very important: used to generate prompts during the scan.
)
```
For further examples, check out the [tutorials section](https://docs.giskard.ai/en/latest/tutorials/tabular_tutorials/index.html).

<details>
<summary>Click to view parameter details</summary>

* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: A prediction function that takes a `pandas.DataFrame` as input and returns a string.
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.
    * `description`: A detailed description of what the model does, this is used to generate prompts to test during the scan.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Give a name to the wrapped model to identify it in metadata.
    * `feature_names`: An optional list of the column names of your feature. By default, `feature_names` are all the columns in your
      dataset. Make sure these features are all present and in the same order as they are in your training dataset.

</details>

::::::
::::::{tab-item} Wrap a RAG-based LLM

Wrap your RAG-based LLM app in an extension of Giskard's Model class. This example uses a FAISS vector store, a langchain chain and an OpenAI model.

```python
# Create the chain.
llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0)
prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["question", "context"])
climate_qa_chain = RetrievalQA.from_llm(llm=llm, retriever=get_context_storage().as_retriever(), prompt=prompt)

# Define a custom Giskard model wrapper for the serialization.
class FAISSRAGModel(giskard.Model):
    def model_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        return df["query"].apply(lambda x: self.model.run({"query": x}))

    def save_model(self, path: str):
        out_dest = Path(path)
        # Save the chain object
        self.model.save(out_dest.joinpath("model.json"))

        # Save the FAISS-based retriever
        db = self.model.retriever.vectorstore
        db.save_local(out_dest.joinpath("faiss"))

    @classmethod
    def load_model(cls, path: str) -> Chain:
        src = Path(path)

        # Load the FAISS-based retriever
        db = FAISS.load_local(src.joinpath("faiss"), OpenAIEmbeddings())

        # Load the chain, passing the retriever
        chain = load_chain(src.joinpath("model.json"), retriever=db.as_retriever())
        return chain


# Wrap the QA chain
giskard_model = FAISSRAGModel(
    model=climate_qa_chain,  # A prediction function that encapsulates all the data pre-processing steps and that could be executed with the dataset used by the scan.
    model_type="text_generation",  # Either regression, classification or text_generation.
    name="Climate Change Question Answering",  # Optional.
    description="This model answers any question about climate change based on IPCC reports",  # Is used to generate prompts during the scan.
)
```
For further examples, check out the [tutorials section](https://docs.giskard.ai/en/latest/tutorials/tabular_tutorials/index.html).

<details>
<summary>Click to view parameter details</summary>

* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `model`: A prediction function that takes a `pandas.DataFrame` as input and returns a string.
    * `model_type`: The type of model, either `regression`, `classification` or `text_generation`.
    * `description`: A detailed description of what the model does, this is used to generate prompts to test during the scan.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `name`: Give a name to the wrapped model to identify it in metadata.
    * `feature_names`: An optional list of the column names of your feature. By default, `feature_names` are all the columns in your
      dataset. Make sure these features are all present and in the same order as they are in your training dataset.

</details>

::::::
:::::::

## Step 2: Scan your model

Now you can scan your model and display your scan report:

```python
scan_results = giskard.scan(giskard_model)
display(scan_results)  # in your notebook
```

![Tabular scan results](../../../assets/scan_llm.png)

If you are not working in a notebook or want to save the results for later, you can save them to an HTML file like this:

```python
scan_results.to_html("model_scan_results.html")
```

## What's next? 

Your scan results may have highlighted important vulnerabilities. There are 2 important actions you can take next:

### 1. Generate a test suite from your scan results to:

* Turn the issues you found into actionable tests that you can save and reuse in further iterations

```python
test_suite = scan_results.generate_test_suite("My first test suite")

# You can run the test suite locally to verify that it reproduces the issues
test_suite.run()
```

Jump to the [test customization](https://docs.giskard.ai/en/latest/open_source/customize_tests/index.html) and [test integration](https://docs.giskard.ai/en/latest/open_source/integrate_tests/index.html) sections to find out everything you can do with test suites.

### 2. Upload your test suite to the Giskard Hub to:
* Compare the quality of different models and prompts to decide which one to promote
* Create more tests relevant to your use case, combining input prompts that make your model fail and custome evaluation criteria
* Share results, and collaborate with your team to integrate business feedback

[Here's a demo](https://huggingface.co/spaces/giskardai/giskard) of the Giskard Hub in action.

## Troubleshooting

If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in our #support channel.
