# 🥇 RAG Evaluation

> ⚠️ **The RAG toolset is currently in early version and is subject to change**. Feel free to reach out on our [Discord server](https://discord.gg/fkv7CAr3FE) if you have any trouble with test set generation or to provide feedback.


## Evaluate your RAG system on your test set

To evaluate your RAG on the generated test set you can use the `giskard.rag.evaluate` function:

```python
def answer_fn(question):
    # a function that wraps your model predictions function

    return your_assistant.predict(question)

evaluate(answers_fn, testset=testset)
```

The evaluate function generates a `giskard.rag.RAGReport` object. The report takes the form an HTML widget presenting all the results of the evaluation. It displays automatically in a notebook, but you can save it and view it in any browser: `report.save_html("report.html")`.

You can access the correctness of the assistant aggregated in various ways: 

```python
# Correctness on each topic of the Knowledge Base
report.correctness_by_topic()

# Correctness on each type of question
report.correctness_by_question_type()
```

The failures examples can be accessed easily as:
```python
# get all the failed questions
report.failures

# get the failed questions filtered by topic and question type
report.get_failures(topic="Topic from your knowledge base", question_type=1)
```

You can also access the score the components of the RAG with `report.component_scores()`. More detail about the computation of these scores is available [here]().


## Evaluate your RAG with custom metrics

You can pass evaluation metrics to the `evaluate` function so they will be computed during the evaluation. 
Your metrics should inherit from the `giskard.rag.metric.Metric` class and implement a `__call__` function. 
Then you can pass it to the `evaluate` function as follows: 

```python
report = evaluate(answers_fn, testset=testset, metrics=[your_custom_metric])
```

The results of your metrics will be displayed in the report object. 

## Giskard Hub Evaluation 
### Step 1: Convert the test set into a test suite
Let's convert our test set into an actionable test suite ({class}`giskard.Suite`) that we can save and reuse in further iterations.

```python
test_suite = testset.to_test_suite("My first test suite")

test_suite.run(model=giskard_model)
```

![](./test_suite_widget.png)


Note that you can split the test suite on the question metadata values, for instance on each question type. 

```python
test_suite_by_question_types = testset.to_test_suite("Split test suite", slicing_metadata=["question_type"])
```

Jump to the [test customization](https://docs.giskard.ai/en/latest/open_source/customize_tests/index.html) and [test integration](https://docs.giskard.ai/en/latest/open_source/integrate_tests/index.html) sections to find out everything you can do with test suites.

### Step 2: Wrap your model
Before evaluating your model with a test suite, you must wrap it as a `giskard.Model`. This step is necessary to ensure a common format for your model and its metadata. You can wrap anything as long as you can represent it in a Python function (for example an API call to Azure or OpenAI). We also have pre-built wrappers for LangChain objects, or you can create your own wrapper by extending the `giskard.Model` class if you need to wrap a complex object such as a custom-made RAG communicating with a vectorstore.

To do so, you can follow the instructions from the [LLM Scan feature](../scan/scan_llm/index.md#step-1-wrap-your-model). Make sure that you pass `feature_names = "question"` when wrapping your model, so that it matches the question column of the test set.

Detailed examples can also be found on our {doc}`LLM tutorials section </tutorials/llm_tutorials/index>`.

Once you have wrapped your model, we can proceed with evaluation.

```python
test_suite.run(model=giskard_model)
```

## Step 3: upload your test suite to the Giskard Hub

Uploading a test suite to the hub allows you to:
* Compare the quality of different models and prompts to decide which one to promote
* Create more tests relevant to your use case, combining input prompts that make your model fail and custome evaluation criteria
* Share results, and collaborate with your team to integrate business feedback

To upload your test suite, you must have created a project on Giskard Hub and instantiated a Giskard Python client. If you haven't done this yet, follow the first steps of [upload your object](https://docs.giskard.ai/en/latest/giskard_hub/upload/index.html#upload-your-object) guide. 

Then, upload your test suite and model like this:
```python
test_suite.upload(giskard_client, project_id)  # project_id should be the id of the Giskard project in which you want to upload your suite
giskard_model.upload(giskard_client, project_id)
```

> ⚠️ To upload your model to the hub, it must be pickleable. If your model is not, you must extend the `giskard.Model` class and override the `save_model` and `load_model` methods to properly save and load the non-pickleable parts of your model (e.g. the vector store). You can find an [example here](../scan/scan_llm/index.md#step-1-wrap-your-model) inside the "Wrap a custom RAG" tab.

[Here's a demo](https://huggingface.co/spaces/giskardai/giskard) of the Giskard Hub in action.



## Troubleshooting
If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in our #support channel.