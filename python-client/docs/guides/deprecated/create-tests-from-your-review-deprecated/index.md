---
description: How to get started with Automated Machine Learning testing
---

# Test your ML model

Giskard enables you to create test suites on AI models. It provides **presets** of tests so that you design and execute your tests in no time.&#x20;

Here are the 3 steps to create and execute tests: \


:::{hint}
If you have **custom tests**, go to the [Create your custom test](create-your-custom-test.md) section
:::

## 1. Create an automatic test suite

To create tests, you need first to create a test suite, here are the 3 steps:

&#x20;1\. Go to the test suite tab in Giskard and click on the button "create test suite"

![](<../../.gitbook/assets/Screenshot 2022-07-18 at 09.21.16.png>)

2\. Choose the inputs parameters of your test suite:

* **Test suite name**: A test suite name
* **Model**: The model that the test suite will test
* **Actual dataset**: A test dataset used to execute the tests inside the test suite. It could be any datasets that you've uploaded with [#3.-upload-a-model-and-a-dataset](../upload-your-model-deprecated/#3.-upload-a-model-and-a-dataset "mention")
* **Reference dataset (optional)**: An optional reference dataset used for the drift testing to assess the changes with the Actual dataset. It could be any datasets that you've uploaded with [#3.-upload-a-model-and-a-dataset](../upload-your-model-deprecated/#3.-upload-a-model-and-a-dataset "mention")\


3\. Toggle on "the automatic test" to automatically pre-compute a batch of tests that is preloaded by Giskard according to your case.

## 2. Customize your tests inside your test suite

Giskard proposes 5 families of tests that you can customize (see [documentation](https://github.com/Giskard-AI/giskard/tree/main/python-client/giskard/ml\_worker/testing)):

* **Metamorphic testing:** Test if your model outputs behave as expected before and after input perturbation
* **Heuristics testing**: Test if your model output respect some business rules
* **Performance testing**: Test if your model performance is sufficiently high within some particular data slices
* **Data drift testing**: Test if your features don't drift between the reference and actual dataset
* **Prediction drift testing**: Test the absence of concept drift inside your model

![](<../../.gitbook/assets/Screenshot 2022-07-18 at 10.29.32.png>)

:::{hint}
To have detailed **documentation** on these tests, go to [https://github.com/Giskard-AI/giskard/tree/main/python-client/giskard/ml\_worker/testing](https://github.com/Giskard-AI/giskard/tree/main/python-client/giskard/ml\_worker/testing)
:::

:::{hint}
If you have **custom tests**, go to the [Create your custom test](create-your-custom-test.md) section
:::

## 3. Read the test results

Once you have run the test you designed, Giskard provides the results (PASS or FAIL) of all your tests. You can then click on the test and further investigate the outputs of the tests to understand the issue.

![](<../../.gitbook/assets/Screenshot 2022-07-18 at 10.23.02.png>)

## 4. Open a test API to execute your tests externally

**1. Find the ids of the objects you created in Giskard**

To find the ids of the **tests and test suites** you created in Giskard, use:

```clike
project.list_tests_in_suite(suite_id)
project.list_test_suites()
```

To find the ids of the model and datasets you uploaded in Giskard, use the \*upload\_\* methods:

```clike
ds_id = upload_df(...)
model_id = upload_model(...)
model_id, ds_id = upload_model_and_df(...)
```

:::{hint}
You can also find all your ids in the Giskard UI
:::

**2. Execute your tests & test suites externally**

To execute your model externally and have your test results as a JSON file, use the following APIs:

```clike
project.execute_test(
    test_id,
    actual_ds_id=None,
    reference_ds_id=None,
    model_id=None)

project.execute_test_suite(
    test_suite_id,
    actual_ds_id=None,
    reference_ds_id=None,
    model_id=None)
```

:::{hint}
When the optional arguments (**model / actual\_ds / reference\_ds**) are provided, they replace the existing ones in the test suites. If they're not provided, the old values (model / actual\_ds / reference\_ds) remain unchanged in the test suite settings.
:::

**Example:**

A typical workflow can be:

```clike
new_model_id = upload_model(...)

test_result = project.execute_test_suite(
    test_suite_id=123,
    model_id=new_model_id)
```

## Troubleshooting

If you encounter any issues, join our [**Discord**](https://discord.gg/fkv7CAr3FE) on our #support channel. Our community will help!&#x20;
