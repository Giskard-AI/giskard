# Why Giskard?

Giskard is a **holistic Testing platform for AI models** to control all 3 types of AI risks: Quality, Security & Compliance.

It addresses the following challenges in AI testing:

- Edge cases in AI are **domain-specific** and often seemingly **infinite**.
- The AI development process is an experimental, **trial-and-error** process where quality KPIs are multi-dimensional.
- Generative AI introduces new **security vulnerabilities** which requires constant vigilance and continuous red-teaming.

Giskard provides a platform for testing all AI models, from tabular ML to LLMs. This enables AI teams to:

1. **Reduce AI risks** by enhancing the test coverage on quality & security dimensions.
2. **Save time** by automating testing, evaluation and debugging processes.

## Giskard Library (open-source)

An **open-source** library to detect hallucinations (RAGET) and security issues (scan) to turn them into test suites that you can automatically execute.

Testing Machine Learning applications can be tedious. Since AI models depend on data, quality testing scenarios depend on
**domain specificities** and are often **infinite**. Besides, detecting security vulnerabilities on LLM applications requires specialized knowledge that most AI teams don't possess.

To help you solve these challenges, Giskard library helps to:

- **Detect hallucinations and security issues automatically**: The `giskard` RAGET and SCAN automatically identify vulnerabilities
such as performance bias, hallucination, prompt injection, data leakage, spurious correlation, overconfidence, etc.
<br><br>
  <iframe src="https://htmlpreview.github.io/?https://gist.githubusercontent.com/AbSsEnT/a67354621807f3c3a332fca7d8b9a5c8/raw/588f027dc6b14c88c7393c50ff3086fe1122e2e9/LLM_QA_IPCC_scan_report.html" width="700" height="400"></iframe>

- **Instantaneously generate domain-specific tests**: `giskard` automatically generates relevant, customizable tests based on the
  vulnerabilities detected in the scan.
  <br><br>
  <img src="../assets/test_suite_scan_llm.png" width="500">

- **Integrate and automate** testing of AI models in **CI/CD** pipelines by leveraging native `giskard` integrations.
  <br><br>
  <img src="../assets/gh_discussion.png" width="650">

Get started **now** with our [quickstart notebooks](../getting_started/quickstart/index.md)! ⚡️

## The Giskard Enterprise LLM Hub

The LLM Hub is an enterprise solution offering a broader range of features such as a:
- **Continuous testing**: Detect new hallucinations and security issues during production
- **Annotation studio**: Easily write the right requirements for your LLM as a judge setup
- **Alerting**: Get alerted with regular vulnerability reports by emails during production
- **Red-teaming playground**: Collaboratively craft new test cases with high domain specificity

  
For a complete overview of LLM Hub’s features, check the documentation of the LLM Hub.
