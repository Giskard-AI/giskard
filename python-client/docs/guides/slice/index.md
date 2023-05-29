# 🔪 Slicing your dataset

:::{warning}
First you'll need to create a dataset,
see [Wrap your dataset](../wrap_dataset/index.md)
:::

## Apply a slicing function to your dataset

:::{hint}
You can see all our slicing function in
the [🔪 Slicing Function Catalog](docs/catalogs/slicing-function-catalog/index.rst)
:::

:::::{tab-set}
::::{tab-item} Sentiment analysis

```python
from giskard import Dataset
from giskard.ml_worker.testing.functions.slicing import positive_sentiment_analysis

wrapped_dataset = Dataset(...)

positive_sentiment_slice = wrapped_dataset.slice(positive_sentiment_analysis(column_name='content'))

positive_sentiment_slice.df.head()

```

::::

::::{tab-item} Using a lambda

```python
from giskard import Dataset

wrapped_dataset = Dataset(...)

afternoon_slice = wrapped_dataset.slice(lambda row: row['Hour'] > 12)

afternoon_slice.df.head()

```

::::

::::{tab-item} Custom slicing function

```python
from giskard import Dataset, slicing_function
import pandas as pd

wrapped_dataset = Dataset(...)


# Define the slicing function
@slicing_function(row_level=False)
def n_firsts(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
  return df.head(n)


# Slice the dataset to get the first 5 rows
five_firsts_slice = wrapped_dataset.slice(n_firsts())

# Slice the dataset to get the first 10 rows
ten_firsts_slice = wrapped_dataset.slice(n_firsts(10))

ten_firsts_slice.df.head()

```

* <mark style="color:red;">**`slicing_function`**</mark> : decorator registers a slicing function in Giskard. Slicing
  functions can be executed at three different levels:
  * **DataFrame level**: The DataFrame level require `row_level` to be set to `False`
    * The slicing function must have its first argument and it's return type to
      be [`pandas.DataFrame`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html)
  * **Row level**: The row level is set by default
    * The slicing function must have its first argument to be
      a [pandas.Series](https://pandas.pydata.org/docs/reference/api/pandas.Series.html) and its return type to be
      a `bool`
  * **Cell level**: The Cell level require `cell_level` to be set to `True`
    * The slicing function must have its first input to be of type of the input data and its return type to be a `bool`

:::{hint}
You can specify any argument after the first one. Those argument will be provided when passing the slicing function in
the `slice` method
:::

For the DataFrame level, the slicing function will be called with the DataFrame to be filtered, and the result should be
the filtered DataFrame.

For row and cell level, the slicing function will be called for each row of the DataFrame, and the result will either be
True to keep the row or False to filter out the row.

::::
:::::
