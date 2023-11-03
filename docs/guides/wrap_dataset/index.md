# 📦 Wrap your dataset

To scan, test and debug your model, you need to provide a dataset that can be executed by your model. This dataset can be your training, testing, golden, or production dataset.

The `pandas.DataFrame` you provide should contain the **raw data before pre-processing** (categorical encoding, scaling,
etc.). The prediction function that you wrap with the [Giskard Model](../wrap_model/index.md) should be able to execute the pandas dataframe.

```python
from giskard import demo, Dataset

wrapped_dataset = Dataset(
    df=demo.titanic_df(),
    target="Survived",  # Ground truth variable
    cat_columns=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"]  # List of categorical columns. Optional, but is a MUST if available. Inferred automatically if not.
    # name="titanic_dataset", # Optional
    # column_types=None # # Optional: if not provided, it is inferred automatically
)
```


* <mark style="color:red;">**`Mandatory parameters`**</mark>
    * `df`: A `pandas.DataFrame` that contains the raw data (before all the pre-processing steps) and the actual
      ground truth variable (target). `df` can contain more columns than the features of the model, such as the sample_id,
      metadata, etc.

* <mark style="color:red;">**`Optional parameters`**</mark>
    * `target`: The column name in `dataset` corresponding to the actual target variable (ground truth).
    * `name`: Name of the wrapped dataset.
    * One of:
        * `cat_columns`: A list of strings representing the names of categorical columns. These are columns that are
          processed by the model with common categorical pre-processing, such as one-hot encoding. It can be binary,
          numerical, or textual with a few unique values.
          If not provided, the column types will automatically be inferred.
        * `column_types`: A dictionary of column names and their types (numeric, category or text) for all columns
          of `dataset`.
          If not provided, the column types will automatically be inferred.

:::{note}
You can easily revert your Giskard dataset back to a pandas DataFrame. To do so, use the `.df` method. For more information about Dataset methods, see the [API Reference](../../reference/datasets/index.rst).
:::

## Upload your Dataset to the Giskard hub

Uploading your dataset to the Giskard hub enables you to:

* Inspect and debug your dataset
* Use your dataset as the input for your tests (unit datasets)

To upload your dataset to the Giskard hub, go to the page [Upload an object to the Giskard hub](../upload/index.md).

