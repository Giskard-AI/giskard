# 👨‍🔬 Add Domain-Specific Tests

Now that you have [scanned](../../open_source/scan/index.md) your model, you've got a first test suite covering the biggest [vulnerabilities](../../knowledge/llm_vulnerabilities/index.rst). However, real models usually need **hundreds of business-specific tests** to be ready for production. While the task of creating tests can be tedious, Giskard enables you to **semi-automate** this process.

In this section, we'll see how to enrich the tests you initially created from the [scan](../../open_source/scan/index.md) by:
* Adding tests from the automatic model insights.
* Adding tests from the Giskard catalog.

## Add Tests from the Automatic Model Insights

While you [debug](../inspect/index.md) your test suite, Giskard provides helpful notifications displaying a bulb 💡 at different places in your [debugging session](../inspect/index.md). These model insights cover various issues such as:
* Words or features that **contribute** to the incorrect prediction.
* **Unrobust** predictions against small variations.
* **Overconfident** predictions.
* **Underconfident** predictions.

By clicking on these small bulbs 💡, you have the option to:
* Add new **tests** to your test suite: this allows you to add new tests with just 1 click.
* **Save** the data slice: this enables you to add this slice as a parameter for your future tests.
* Directly **debug** the data slice: this allows you to analyze whether the model insight is general to the entire slice.

![Push](../../assets/push.png)

## Add Tests from the Giskard Catalog

The Giskard catalog is an **open-source** collection that is constantly updated by the community. It offers some **pre-made tests** that you can easily configure depending on your business case by inputting some domain-specific slices & transformations or evaluation criteria as **inputs** for your tests.

To add tests from the catalog, click on "add test" in your test suite tab. This will redirect you to the catalog displaying all Giskard tests. You then have the option to run your test before adding it to your suite.

> ⚠️ Warning
> * If you add a test **without** specifying the input for your test, you'll be asked to define the input at **suite execution time**. This input will become a *suite input*. For instance, models are great suite inputs if you want to [compare different models](../compare_models/index.md) with the same test suite.
> * If you add a test by **specifying the input** for your test, you won't need to define it at suite 
> execution time. This input becomes a *fixed value* in your suite. For instance, data slices or thresholds are 
> great fixed values because they are inherent to your suite.
>
> 💡 You can also define test inputs as *suite inputs* or *fixed values* by editing the parameters of your test 
> suite.

![Catalog](../../assets/catalog.png)

> 💡 Try it live with our Hugging Face space: [here](https://giskardai-giskard.hf.space/main/projects)