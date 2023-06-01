# Getting Started

<p align="center">
  <img alt="giskardlogo" src="../assets/Logo_full_black@4x.jpg" style="width: 50%;">
</p>
<h1 align="center" weight='300' >Quality Assurance for AI models</h1>
<h3 align="center" weight='300' >The testing framework dedicated for  ML models, from tabular to LLM</h3>
<h3 align="center">
   <a href="https://docs.giskard.ai/"><b>Documentation</b></a> &bull;
   <a href="https://www.giskard.ai/knowledge-categories/blog/?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog"><b>Blog</b></a> &bull;  
  <a href="https://www.giskard.ai/?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog"><b>Website</b></a> &bull;
  <a href="https://gisk.ar/discord"><b>Discord Community</b></a> &bull;
  <a href="https://www.giskard.ai/about?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog#advisors"><b>Advisors</b></a>
 </h3>
<br />

## What is Giskard?

Giskard is the **open-source testing framework** dedicated for  ML models, from tabular to LLM.

Testing Machine Learning app can be fastiduous. Since ML model depends on data,  testing scenarios depends on domain specificities and are often infinite. **Where to start testing? Which tests to implement? What are the issue to cover? How to implement the test?**

At Giskard, we think that Machine Learning needs its own testing framework. Practioners should easily create test suites that contains business-specific fixtures (data slicer & transformers, evaluators) that cover the various risks encounterd by AI. Created by ML engineers for ML engineers, Giskard enable you to:

* **Scan your model and find hundred of vulnerabilities**: The Giskard scan automatically detects vulnerability issues such as performance bias, data leakage, unrobustness, spurious correlation, overconfident or underconfident spots in your data
* **Instantaneously generate  tests  with domain insights**: Giskard automatically generates the right tests based on the vulnerabilites that were detected by the scan. You can easily customize the tests depending on your use case by defining domain-specific data slices and transformers as fixtures of your test suites.
* **Leverage the QA best practices of the open source community**: The Giskard catalog enables you to easily contribute and load QA objects, such as AI-based detectors (toxicity, hate, etc.), generators (typos, paraphraser, etc.) or evaluators. Inspired by the Hugging Face philosophy, the aim of Giskard is to become the open source hub of ML QA. 

## Quickstart?
Load the titanic demo models and dataset 👇
```python
from giskard.demo import titanic  # for demo purposes only 🛳️
original_model, df = titanic()  # Replace with your dataframe creation
```

Follow the code snippet below to wrap a dataset 👇
```python
from giskard import Dataset

# Wrap your Pandas Dataframe with Giskard dataset 🎁
giskard_dataset = Dataset(df,
                          target="Survived",
                          name="Titanic dataset")

```

Follow the code snippet below to wrap a model 👇
```python
from giskard import Model

# Wrap your model with Giskard model 🎁
giskard_model = Model(original_model, model_type="classification", name="Titanic model")
```

Follow the code snippet below to scan your model 👇
```python
import giskard

results = giskard.scan(wrapped_model, wrapped_dataset)

display(results)  # in your notebook

```

Generate a test suite from the scan 👇
```python
test_suite = results.generate_test_suite("My first test suite")

# You can run the test suite locally to verify that it reproduces the issues
test_suite.run()
```

Upload artefacts 👇
```python
from giskard import GiskardClient

# Create a Giskard client
token = "API_TOKEN" # Find it in Settings
client = GiskardClient(
    url="http://localhost:19000",  # URL of your Giskard instance
    token=token
)

my_project = client.create_project("my_project", "PROJECT_NAME", "DESCRIPTION")

# Upload to the current project ✉️
test_suite.upload(client, "my_project")
```
