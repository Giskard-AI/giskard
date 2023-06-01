# What is Giskard?

Giskard is the **open-source testing framework** dedicated for ML models, from tabular to LLM.

Testing Machine Learning app can be fastiduous. Since ML model depends on data, testing scenarios depends on domain specificities and are often infinite. **Where to start testing? Which tests to implement? What are the issue to cover? How to implement the test?**

At Giskard, we think that Machine Learning needs its own testing framework. Practioners should easily create test suites that contains business-specific fixtures (data slicer & transformers, evaluators) that cover the various risks encounterd by AI. Created by ML engineers for ML engineers, Giskard enable you to:

* **Scan your model and find hundred of vulnerabilities**: The Giskard scan automatically detects vulnerability issues such as performance bias, data leakage, unrobustness, spurious correlation, overconfident or underconfident spots in your data
* **Instantaneously generate domain-specific tests**: Giskard automatically generates the right tests based on the vulnerabilites that were detected by the scan. You can easily customize the tests depending on your use case by defining domain-specific data slices and transformers as fixtures of your test suites.
* **Leverage the QA best practices of the open source community**: The Giskard catalog enables you to easily contribute and load QA objects, such as AI-based detectors (toxicity, hate, etc.), generators (typos, paraphraser, etc.) or evaluators. Inspired by the Hugging Face philosophy, the aim of Giskard is to become the open source hub of ML QA. 

