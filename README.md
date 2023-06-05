<p align="center">
  <img alt="giskardlogo" src="readme/correct_logo.png">
</p>
<h1 align="center" weight='300' >Quality Assurance for AI models</h1>
<h3 align="center" weight='300' >Eliminate AI bias in production. Deliver ML products, better & faster</h3>
<p align="center">
   <a href="https://github.com/Giskard-AI/giskard/releases">
      <img alt="GitHub release" src="https://img.shields.io/github/v/release/Giskard-AI/giskard">
  </a>
 <a href="https://github.com/Giskard-AI/giskard/blob/main/LICENSE">
     <img alt="GitHub" src="https://img.shields.io/badge/License-Apache_2.0-blue.svg">
 </a>
  <a href="https://github.com/Giskard-AI/giskard/actions/workflows/build.yml">
    <img alt="build" src="https://github.com/Giskard-AI/giskard/actions/workflows/build.yml/badge.svg?branch=main"/>
 </a>
   <a href="https://sonarcloud.io/summary/overall?id=giskard">
      <img alt="Reliability Rating" src="https://sonarcloud.io/api/project_badges/measure?project=giskard&metric=reliability_rating">
  </a>
  <a href="https://gisk.ar/discord">
    <img alt="Giskard on Discord" src="https://img.shields.io/discord/939190303397666868?label=Discord"/>
  </a>
  <a rel="me" href="https://fosstodon.org/@Giskard"></a>
</p>
<h3 align="center">
   <a href="https://docs.giskard.ai/"><b>Documentation</b></a> &bull;
   <a href="https://www.giskard.ai/knowledge-categories/blog/?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog"><b>Blog</b></a> &bull;  
  <a href="https://www.giskard.ai/?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog"><b>Website</b></a> &bull;
  <a href="https://gisk.ar/discord"><b>Discord Community</b></a> &bull;
  <a href="https://www.giskard.ai/about?utm_source=github&utm_medium=github&utm_campaign=github_readme&utm_id=readmeblog#advisors"><b>Advisors</b></a>
 </h3>
<br />

# About Giskard
**Giskard is an open-source testing framework dedicated to ML models, from tabular models to LLMs.**

Testing Machine Learning applications can be tedious. Since ML models depend on data, testing scenarios depend on the domain specificities and are often infinite. 

<p align="center">
<strong>Where to start testing? Which tests to implement? What issues to cover? How to implement the tests?</strong>
</p>

<p align="center">
  <img src="https://giskard.readthedocs.io/en/latest/_images/hey.png" alt="hey" width="20%">
</p>

At Giskard, we believe that Machine Learning needs its own testing framework. Created by ML engineers for ML engineers, Giskard enables you to:

- **Scan your model to find dozens of vulnerabilities**: The Giskard scan automatically detects vulnerability issues such as performance bias, data leakage, unrobustness, spurious correlation, overconfidence, underconfidence, unethical issue, etc.

<p align="center">
  <img src="/readme/scan_example.png" alt="Scan Example" width="700px">
</p>

- **Instantaneously generate domain-specific tests**: Giskard automatically generates relevant tests based on the vulnerabilities detected by the scan. You can easily customize the tests depending on your use case by defining domain-specific data slicers and transformers as fixtures of your test suites.

<p align="center">
  <img src="/readme/test_suite_example.png" alt="Scan Example" width="700px">
</p>

- **Leverage the Quality Assurance best practices of the open-source community**: The Giskard catalog enables you to easily contribute and load data slicing & transformation functions such as AI-based detectors (toxicity, hate, etc.), generators (typos, paraphraser, etc.), or evaluators. Inspired by the Hugging Face philosophy, the aim of Giskard is to become the open-source hub of ML Quality Assurance.

<p align="center">
  <img src="/readme/catalog_example.png" alt="Scan Example" width="700px">
</p>

And of course, Giskard works with any model, any environment and integrates seamlessly with your favorite tools ⤵️ <br/>
<p align="center">
  <img width='600' src="readme/tools.png">
</p>
<br/>



# Getting Started with Giskard
## Installation
```sh
pip install giskard

giskard server start
```

That's it. Access at http://localhost:19000

## Scan your model to detect vulnerabilities

After having wrapped your [model](../wrap_model/index.md) & [dataset](../wrap_dataset/index.md), you can scan your model for vulnerabilities using:

```python
from giskard import demo, Model, Dataset, scan

model, df = demo.titanic()

wrapped_model = Model(model=model, model_type="classification")
wrapped_dataset = Dataset(df=df, target="Survived", cat_columns=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"])

scan_results = scan(wrapped_model, wrapped_dataset)
```

Once the scan completes, you can display the results directly in your notebook:

```python
display(scan_results)  # in your notebook
```

## Automatically generate a test suite based on the scan results

If the scan found potential issues in your model, you can automatically generate a test suite.

Generating a test suite from your scan results will enable you to:
- Turn the issues you found into actionable tests that you can directly integrate in your CI/CD pipeline
- Diagnose your vulnerabilities and debug the issues you found in the scan

```python
test_suite = scan_results.generate_test_suite("My first test suite")

# You can run the test suite locally to verify that it reproduces the issues
test_suite.run()
```

## Upload your test suite to the Giskard server

You can then upload the test suite to the local Giskard server. This will enable you to:
- Compare the quality of different models to decide which one to promote
- Debug your tests to diagnose the identified issues
- Create more domain-specific tests relevant to your use case
- Share results, and collaborate with your team to integrate business feedback

```python

# Create a Giskard client after having installed the Giskard server (see documentation)
token = "API_TOKEN"  # Find it in Settings in the Giskard server
client = GiskardClient(
    url="http://localhost:19000",  # URL of your Giskard instance
    token=token
)

my_project = client.create_project("my_project", "PROJECT_NAME", "DESCRIPTION")

# Upload to the current project
test_suite.upload(client, "my_project")
```
    
For more information on uploading to your local Giskard server, go to the [Upload an object to the Giskard server](../upload/index.md) page.

# How to contribute
We welcome contributions from the Machine Learning community!

Read this [guide](CONTRIBUTING.md) to get started.

<br />

# Like what we're doing?
🌟 [Leave us a star](https://github.com/Giskard-AI/giskard), it helps the project to get discovered by others and keeps us motivated to build awesome open-source tools! 🌟
