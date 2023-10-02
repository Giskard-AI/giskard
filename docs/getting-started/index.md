# Why Giskard?

Giskard is an **open-source testing framework** dedicated to ML models, covering any Python model, from tabular to LLMs.

Testing Machine Learning applications can be tedious. Since ML models depend on data, testing scenarios depend on the domain specificities and are often infinite. 

<p align="center">
<strong>Where to start testing? Which tests to implement? What issues to cover? How to implement the tests?</strong>
</p>

<p align="center">
  <img src="https://giskard.readthedocs.io/en/latest/_images/hey.png" alt="hey" width="20%">
</p>

At Giskard, we believe that Machine Learning needs its own testing framework. Created by ML engineers for ML engineers, Giskard enables you to:

- **Scan your model to find dozens of hidden vulnerabilities**: The Giskard scan automatically detects vulnerability issues such as performance bias, data leakage, unrobustness, spurious correlation, overconfidence, underconfidence, unethical issue, etc.

<br>

  ![](/_static/scan_example.png)
- **Instantaneously generate domain-specific tests**: Giskard automatically generates relevant tests based on the vulnerabilities detected by the scan. You can easily customize the tests depending on your use case by defining domain-specific data slicers and transformers as fixtures of your test suites.

<br>

  ![](/_static/test_suite_example.png)
- **Leverage the Quality Assurance best practices of the open-source community**: The Giskard catalog enables you to easily contribute and load data slicing & transformation functions such as AI-based detectors (toxicity, hate, etc.), generators (typos, paraphraser, etc.), or evaluators. Inspired by the Hugging Face philosophy, the aim of Giskard is to become the open-source hub of ML Quality Assurance.

<br>

  ![](/_static/catalog_example.png)
