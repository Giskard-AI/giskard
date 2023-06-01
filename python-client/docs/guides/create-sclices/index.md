# Create slices

## Create your slicing function

```python
from giskard import slicing_function
import pandas as pd


@slicing_function
def afternoon_slicing_fn(row: pd.Series) -> bool:
    return row['Hour'] > 12

```

## Apply your slicing function to a dataset

```python
from giskard import dataset

my_dataset = dataset(...)

afternoon_slice = my_dataset.slice(afternoon_slicing_fn)

```

## Chain slices

```python
from giskard import dataset
from giskard import slicing_function
import pandas as pd


@slicing_function
def q1_slicing_fn(row: pd.Series) -> bool:
    return row['Month'] in ['Jan', 'Feb', 'Mar', 'Apr']


my_dataset = dataset(...)

afternoon_q1_slice = my_dataset.add_slicing_function(afternoon_slicing_fn)
    .add_slicing_function(q1_slicing_fn)
    .process()


```


