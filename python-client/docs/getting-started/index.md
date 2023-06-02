# What is Giskard?

Giskard is an **open-source testing framework** dedicated to ML models, ranging from tabular to LLM.

Testing Machine Learning applications can be tedious. Since ML models depend on data, testing scenarios depend on domain specificities and are often infinite. **Where to start testing? Which tests to implement? What issues to cover? How to implement the test?**

<p align="center">
  <img src="/_static/hey.png" alt="hey" width="20%">
</p>

At Giskard, we believe that Machine Learning needs its own testing framework. Created by ML engineers for ML engineers, Giskard enables you to:

- **Scan your model and find hundreds of vulnerabilities**: The Giskard scan automatically detects vulnerability issues such as performance bias, data leakage, unrobustness, spurious correlation, overconfident or underconfident spots in your data.
  ![](/_static/scan_example.png)
- **Instantaneously generate domain-specific tests**: Giskard automatically generates the right tests based on the vulnerabilities detected by the scan. You can easily customize the tests depending on your use case by defining domain-specific data slices and transformers as fixtures of your test suites.
  ![](/_static/test_suite_example.png)
- **Leverage the Quality Assurance best practices of the open-source community**: The Giskard catalog enables you to easily contribute and load Quality Assurance objects, such as AI-based detectors (toxicity, hate, etc.), generators (typos, paraphraser, etc.), or evaluators. Inspired by the Hugging Face philosophy, the aim of Giskard is to become the open source hub of ML Quality Assurance.
  ![](/_static/catalog_example.png)
