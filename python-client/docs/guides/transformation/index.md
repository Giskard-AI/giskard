# 🔪 Transform your dataset

:::{warning}
First you'll need to create a dataset,
see [Wrap your dataset](../wrap_dataset/index.md)
:::

## Apply a transformation function to your dataset

:::{hint}
You can see all our slicing function in
the [🔪 Slicing Function Catalog](docs/catalogs/slicing-function-catalog/index.rst)
:::

::::{tab-set}
:::{tab-item} Text transformation

```python
from giskard import Dataset
from giskard.ml_worker.testing.functions.transformation import keyboard_typo_transformation

wrapped_dataset = Dataset(...)

keyboard_typo = wrapped_dataset.transform(keyboard_typo_transformation(column_name='content'))

keyboard_typo.df.head()

```

:::
:::{tab-item} Custom transformation function

```python
from giskard import Dataset, transformation_function
import pandas as pd

wrapped_dataset = Dataset(...)


# Define the transformation function
@transformation_function
def uppercase_transformation(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
  return df.head(column_name)


# Apply the uppercase transformation to the 'content' column at the DataFrame level
uppercase = wrapped_dataset.transform(uppercase_transformation('content'))

# Display the transformed dataset
uppercase.df.head()

```

`transformation_function`: The `transformation_function` decorator registers a transformation function in Giskard.
Transformation functions are used to modify the dataset based on specific operations.

The transformation function can be executed at three different levels:

* **DataFrame level**: The DataFrame level requires `row_level` to be set to `False`. This level operates on the entire
  DataFrame.
* **Row level**: The row level is set by default. This level operates on each row of the DataFrame.
* **Cell level**: The cell level requires `cell_level` to be set to `True`. This level operates on each cell of a
  specified column of the DataFrame.

:::
::::

## Chaining slicing and transformation functions

:::{hint}
You can chain as many slicing and transformation as you need
:::

```python
from giskard import Dataset
from giskard.ml_worker.testing.functions.slicing import positive_sentiment_analysis
from giskard.ml_worker.testing.functions.transformation import keyboard_typo_transformation

wrapped_dataset = Dataset(...)

positive_sentiment_with_typo = wrapped_dataset.slice(positive_sentiment_analysis(column_name='content')).transform(
    keyboard_typo_transformation(column_name='content'))

positive_sentiment_with_typo.df.head()
```
