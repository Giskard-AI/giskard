# 🔪 Slicing and transformations function

:::{warning}
First you'll need to create a dataset,
see [🔬 Scan your ML model](../scan/index.md)
:::

## Apply a slicing function to your dataset

:::{hint}
You can see all our slicing function in the [🔪 Slicing Function Catalog](../slicing-function-catalog/index.rst)
:::

::::{tab-set}
:::{tab-item} Sentiment analysis

```python
from giskard import wrap_dataset
from giskard.ml_worker.testing.functions.slicing import positive_sentiment_analysis

wrapped_dataset = wrap_dataset(...)

positive_sentiment_slice = wrapped_dataset.slice(positive_sentiment_analysis(column_name='content'))

positive_sentiment_slice.df.head()

```

:::

:::{tab-item} Using a lambda

```python
from giskard import wrap_dataset

wrapped_dataset = wrap_dataset(...)

afternoon_slice = wrapped_dataset.slice(lambda row: row['Hour'] > 12)

afternoon_slice.df.head()

```

:::

:::{tab-item} Custom slicing function

```python
import pandas
from giskard import wrap_dataset, slicing_function
import pandas as pd

wrapped_dataset = wrap_dataset(...)


@slicing_function(row_level=False)
def n_firsts(df: pandas.DataFrame, n: int = 5) -> pd.DataFrame:
    return df.head(n)


five_firsts_slice = wrapped_dataset.slice(n_firsts())
ten_firsts_slice = wrapped_dataset.slice(n_firsts(10))

ten_firsts_slice.df.head()

```

:::
::::

## Apply a transformation function to your dataset

:::{hint}
You can see all our slicing function in the [🔪 Slicing Function Catalog](../slicing-function-catalog/index.rst)
:::

::::{tab-set}
:::{tab-item} Text transformation

```python
from giskard import wrap_dataset
from giskard.ml_worker.testing.functions.transformation import keyboard_typo_transformation

wrapped_dataset = wrap_dataset(...)

keyboard_typo = wrapped_dataset.slice(keyboard_typo_transformation(column_name='content'))

keyboard_typo.df.head()

```

:::
:::{tab-item} Custom transformation function

```python
import pandas
from giskard import wrap_dataset, transformation_function
import pandas as pd

wrapped_dataset = wrap_dataset(...)


@transformation_function
def uppercase_transformation(df: pandas.DataFrame, column_name: str) -> pd.DataFrame:
    return df.head(column_name)


uppercase = wrapped_dataset.slice(uppercase_transformation('content'))

uppercase.df.head()

```

:::
::::
