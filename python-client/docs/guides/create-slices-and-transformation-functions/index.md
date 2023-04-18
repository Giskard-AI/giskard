# Create slices and transformations function

## Slices

### Create your slicing function

```python
from giskard import slicing_function
import pandas as pd


@slicing_function
def afternoon_slicing_fn(row: pd.Series) -> bool:
    return row['Hour'] > 12

```

### Apply your slicing function to a dataset

```python
from giskard import wrap_dataset

my_dataset = wrap_dataset(...)

afternoon_slice = my_dataset.slice(afternoon_slicing_fn)

```

## Transformation

### Create your transformation function

```python
from giskard import transformation_function
import pandas as pd


@transformation_function
def inverse_am_pm(row: pd.Series) -> pd.Series:
    row['Hour'] = (row['Hour'] + 12) % 24
    return row

```

### Apply your transformation function to a dataset

```python
from giskard import wrap_dataset

my_dataset = wrap_dataset(...)

afternoon_slice = my_dataset.transform(inverse_am_pm)

```

## Chain slices and transformation

```python
from giskard import wrap_dataset, slicing_function, transformation_function
import pandas as pd


@slicing_function
def afternoon_slicing_fn(row: pd.Series) -> bool:
    return row['Hour'] > 12


@slicing_function
def q1_slicing_fn(row: pd.Series) -> bool:
    return row['Month'] in ['Jan', 'Feb', 'Mar', 'Apr']


@transformation_function
def inverse_am_pm(row: pd.Series) -> pd.Series:
    row['Hour'] = (row['Hour'] + 12) % 24
    return row


my_dataset = wrap_dataset(...)

afternoon_q1_slice_inversed = my_dataset.add_slicing_function(afternoon_slicing_fn)
    .add_slicing_function(q1_slicing_fn)
    .add_transformation_function(inverse_am_pm)
    .process()


```
