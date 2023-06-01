# 🚀 Execute your test suite in your CI/CD pipeline

:::{warning}
First you'll need to know how to run Giskard's scan function
see [Scan your ML Model](../scan/index.md)
:::

Adding Giskard to your CI/CD pipeline will allow running its scan function on every commit to your repository, ensuring
new models are not introducing new vulnerabilities.

## Create a script to scan your model

By referring to the [Scan your ML Model](../scan/index.md) guide, you can create a script that will scan your model.

```python
import giskard

# Following the scan guide, you can create a wrapped model and dataset
scan_results = giskard.scan(wrapped_model, wrapped_dataset)
```

Using the results of the scan, you can then decide if your script should exit with an error code or not.

```python
if scan_results.has_vulnerabilities:
    print("Your model has vulnerabilities")
    exit(1)
else:
    print("Your model is safe")
    exit(0)
```