---
description: Create dataset slices to focus on a part of data
---

# Data filtering

Starting from Giskard v.1.4.0 it's possible to define a filtering function while inspecting a dataset. Applying this
filter can allow to focus on a specific part of a dataset based on a custom criteria.

In order to create a slice, open an inspection and click on "Slice to apply" selector:

![Filter creation](<../../assets/image_(1).png>)

In the modal that appears one can implement the filtering logic in python:

![](<../../assets/image_(2).png>)

The `filter_row` function will be applied to each row of the dataset and if it returns a `True` value the current row
will be part of a resulting slice, else it'll be filtered out.

For example, in case of a demo German credit scoring project, we can create a filter called "Older than 50" that would
look like this:

```python
def filter_row(row):
    return row.age > 50

```

