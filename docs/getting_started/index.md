# Why Giskard?

Giskard is an **AI quality management system** dedicated to ML models.

Designed for comprehensive coverage of the AI model lifecycle, Giskard provides a suite of tools for scanning, testing, 
debugging, automation, collaboration, and monitoring of AI models, encompassing all models from tabular to LLMs.

Giskard currently offers 3 tools for AI quality management: the Giskard opens-source Python library, the Giskard Hub and LLMon.

## Giskard Python Library

An open-Source Library to Scan your models for vulnerabilities and generate test suites automatically


Testing Machine Learning applications can be tedious. Since ML models depend on data, testing scenarios depend on the 
domain specificities and are often infinite.

At Giskard, we believe that Machine Learning needs its own testing framework. Created by ML engineers for ML engineers, 
Giskard enables you to:

- **Scan your model to find dozens of hidden vulnerabilities**: The Giskard scan automatically detects vulnerability 
issues such as performance bias, data leakage, unrobustness, spurious correlation, overconfidence, underconfidence, unethical issue, etc.

<br>

  ![](/_static/scan_example.png)
- **Instantaneously generate domain-specific tests**: Giskard automatically generates relevant tests based on the 
vulnerabilities detected by the scan. You can easily customize the tests depending on your use case by defining 
domain-specific data slicers and transformers as fixtures of your test suites.

<br>

## Giskard Hub

An Enterprise AI Quality Management Platform

  ![](/_static/test_suite_example.png)
- **Leverage the Quality Assurance best practices of the open-source community**: The Giskard catalog enables you to 
easily contribute and load data slicing & transformation functions such as AI-based detectors (toxicity, hate, etc.), 
generators (typos, paraphraser, etc.), or evaluators. Inspired by the Hugging Face philosophy, the aim of Giskard is to 
become the open-source hub of ML Quality Assurance.

<br>

  ![](/_static/catalog_example.png)

<br>

:::{info}
**The Giskard hub is installed on your infrastructure.**

Giskard as a company does not have access to your datasets and models, so you can keep everything private.
:::

## LLMon

The monitoring platform for LLMs.

