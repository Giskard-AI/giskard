# 🧪 Pytest

It is possible to execute Giskard test via pytest with very minimal code. Using pytest to execute tests can facilitate the integration with CI/CD scripts and leverage builtin functionalities like test report or advanced markings (xfail, skip).

Once define in a script, the execution of the tests can be triggred using the pytest command:

```console
$ pytest test_ml_model.py

===================================== test session starts ======================================
platform darwin -- Python 3.11.5, pytest-7.4.3, pluggy-1.3.0
rootdir: [REDACTED]
configfile: pyproject.toml
plugins: reportlog-0.4.0, env-1.1.3, Faker-20.1.0, cov-4.1.0, asyncio-0.21.1, memray-1.5.0, anyio-3.7.1, requests-mock-1.11.0, xdist-3.5.0
asyncio: mode=Mode.STRICT
collected 5 items                                                                              

test_ml_model.py .FF                                                                   [100%]

=========================================== FAILURES ===========================================
_______ test_giskard[Accuracy(model=Classifier v1, dataset=Test Data Set, threshold=1)] ________
test_ml_model.py:31: in test_giskard
    test_partial.assert_()
giskard/registry/giskard_test.py:117: in assert_
    assert result.passed, message
E   AssertionError: Test failed Metric: 0.79
E   assert False
E    +  where False = \n               Test failed\n               Metric: 0.79\n               \n               .passed
------------------------------------- Captured stdout call -------------------------------------
2024-01-10 22:43:35,902 pid:33777 MainThread giskard.datasets.base INFO     Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.
2024-01-10 22:43:35,904 pid:33777 MainThread giskard.datasets.base INFO     Casting dataframe columns from {'PassengerId': 'int64', 'Pclass': 'int64', 'Name': 'object', 'Sex': 'object', 'Age': 'float64', 'SibSp': 'int64', 'Parch': 'int64', 'Fare': 'float64', 'Embarked': 'object'} to {'PassengerId': 'int64', 'Pclass': 'int64', 'Name': 'object', 'Sex': 'object', 'Age': 'float64', 'SibSp': 'int64', 'Parch': 'int64', 'Fare': 'float64', 'Embarked': 'object'}
2024-01-10 22:43:35,906 pid:33777 MainThread giskard.utils.logging INFO     Predicted dataset with shape (446, 10) executed in 0:00:00.025473
2024-01-10 22:43:35,916 pid:33777 MainThread giskard.datasets.base INFO     Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.
-------------------------------------- Captured log call ---------------------------------------
INFO     giskard.datasets.base:__init__.py:233 Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.
INFO     giskard.datasets.base:__init__.py:550 Casting dataframe columns from {'PassengerId': 'int64', 'Pclass': 'int64', 'Name': 'object', 'Sex': 'object', 'Age': 'float64', 'SibSp': 'int64', 'Parch': 'int64', 'Fare': 'float64', 'Embarked': 'object'} to {'PassengerId': 'int64', 'Pclass': 'int64', 'Name': 'object', 'Sex': 'object', 'Age': 'float64', 'SibSp': 'int64', 'Parch': 'int64', 'Fare': 'float64', 'Embarked': 'object'}
INFO     giskard.utils.logging:logging.py:50 Predicted dataset with shape (446, 10) executed in 0:00:00.025473
INFO     giskard.datasets.base:__init__.py:233 Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.
______________________________________ test_only_accuracy ______________________________________
test_ml_model.py:45: in test_only_accuracy
    test_accuracy(model=model, dataset=dataset, threshold=1).assert_()
giskard/registry/giskard_test.py:117: in assert_
    assert result.passed, message
E   AssertionError: Test failed Metric: 0.79
E   assert False
E    +  where False = \n               Test failed\n               Metric: 0.79\n               \n               .passed
------------------------------------- Captured stdout call -------------------------------------
2024-01-10 22:43:36,238 pid:33777 MainThread giskard.datasets.base INFO     Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.
2024-01-10 22:43:36,240 pid:33777 MainThread giskard.datasets.base INFO     Casting dataframe columns from {'PassengerId': 'int64', 'Pclass': 'int64', 'Name': 'object', 'Sex': 'object', 'Age': 'float64', 'SibSp': 'int64', 'Parch': 'int64', 'Fare': 'float64', 'Embarked': 'object'} to {'PassengerId': 'int64', 'Pclass': 'int64', 'Name': 'object', 'Sex': 'object', 'Age': 'float64', 'SibSp': 'int64', 'Parch': 'int64', 'Fare': 'float64', 'Embarked': 'object'}
2024-01-10 22:43:36,243 pid:33777 MainThread giskard.utils.logging INFO     Predicted dataset with shape (446, 10) executed in 0:00:00.017629
2024-01-10 22:43:36,250 pid:33777 MainThread giskard.datasets.base INFO     Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.
-------------------------------------- Captured log call ---------------------------------------
INFO     giskard.datasets.base:__init__.py:233 Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.
INFO     giskard.datasets.base:__init__.py:550 Casting dataframe columns from {'PassengerId': 'int64', 'Pclass': 'int64', 'Name': 'object', 'Sex': 'object', 'Age': 'float64', 'SibSp': 'int64', 'Parch': 'int64', 'Fare': 'float64', 'Embarked': 'object'} to {'PassengerId': 'int64', 'Pclass': 'int64', 'Name': 'object', 'Sex': 'object', 'Age': 'float64', 'SibSp': 'int64', 'Parch': 'int64', 'Fare': 'float64', 'Embarked': 'object'}
INFO     giskard.utils.logging:logging.py:50 Predicted dataset with shape (446, 10) executed in 0:00:00.017629
INFO     giskard.datasets.base:__init__.py:233 Your 'pandas.DataFrame' is successfully wrapped by Giskard's 'Dataset' wrapper class.
=================================== short test summary info ====================================
FAILED test_ml_model.py::test_giskard[Accuracy(model=Classifier v1, dataset=Test Data Set, threshold=1)] - AssertionError: Test failed Metric: 0.79
FAILED test_ml_model.py::test_only_accuracy - AssertionError: Test failed Metric: 0.79
================================= 2 failed, 1 passed in 11.50s =================================
```

## Wrapping Giskard test for pytest

Here is an example of definition of model and dataset that will be used in the following example:

```python
import pytest

from giskard import Dataset, Model, Suite, demo
from giskard.testing import test_accuracy, test_f1

model_raw, df = demo.titanic()

wrapped_dataset = Dataset(
    name="Test Data Set",
    df=df,
    target="Survived",
    cat_columns=["Pclass", "Sex", "SibSp", "Parch", "Embarked"],
)

wrapped_model = Model(model=model_raw, model_type="classification", name="Classifier v1")
```

### Running single test

It possible to simply wrap a Giskard test in a function that pytest can pick up. Reusing the defined `Dataset` and `Model`, we can define test as follow:

```python
@pytest.fixture
def dataset():
    return wrapped_dataset


@pytest.fixture
def model():
    return wrapped_model


def test_only_accuracy(dataset, model):
    test_accuracy(model=model, dataset=dataset, threshold=0.7).assert_()
```

### Running a full suite

You can run a full suite via pytest using `parametrize`. Further more using the `ids` argument of the decorator will generate a comprehensive name for the test base on the giskard test name and it parameters like `Accuracy(model=Classifier v1, dataset=Test Data Set, threshold=1)`

:::{hint}
Giving the wrapped model and dataset a `name` enriches the test name. Without a name the test name will look like:
`Accuracy(model=SKLearnModel, dataset=<giskard.datasets.base.Dataset object at 0x1485a4490>, threshold=1)`, refering object or class name.
:::

```python
suite = (
    Suite(
        default_params={
            "model": wrapped_model,
            "dataset": wrapped_dataset,
        }
    )
    .add_test(testing.test_f1(threshold=.6))
    .add_test(testing.test_accuracy(threshold=1)) # Certain to fail
)


@pytest.mark.parametrize("test_partial", suite.to_unittest(), ids=lambda t: t.fullname)
def test_giskard(test_partial):
    test_partial.assert_()
```

## Example

::::::{grid} 1 1 2 2

::::{grid-item-card} <br/><h3>📊 Tabular</h3>
:text-align: center
:link: full_example.ipynb
::::

::::::
