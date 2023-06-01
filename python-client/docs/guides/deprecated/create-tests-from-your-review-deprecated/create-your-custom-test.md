# Create your custom test

### Design your tests

#### 1. Import libraries

We will start with importing Giskard libraries, which enables you to  display the result of your tests on the Giskard application&#x20;

#### 2. Create your custom test&#x20;

Your test Class for example `CustomTest` has to inherit from Giskard's `AbstractTestCollection` which enables you to return the output metrics and passed to the frontend.

#### 3. Return the results using SingleTest Results

`SingleTestResult` enables you to return output to display on the Giskard frontend.&#x20;

We have two main output variables:&#x20;

* `passed`: boolean value of the results. Example: True if the test passed False if the test failed&#x20;
* `metrics`: metrics value of your test&#x20;

```python
# 1. Import libraries
from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.testing.abstract_test_collection import AbstractTestCollection

# 2. Create your custom test 
class CustomTest(AbstractTestCollection):
  def test_function(self, input_values)-> SingleTestResult:
      # write your code here 
      
      # 3. Return the results using SingleTest Results 
      return self.save_results(SingleTestResult(
          passed=True, 
          metric=1)
    )
```

### Test Execution

#### 4. Create Object

To run your custom class, we have to create an object of the class which inherits Giskard's "tests.test\_results"

#### 5. Execute the test&#x20;

```python
custom_test = CustomTest(tests.tests_results) # 4.Create Object

# 5. Execute the test 
custom_test.test_function(
  input_values = XXXX, #you can use the variables from your test suite
)
```

### Examples

#### 1. Custom test integrating with Great Expectations to validate column values are unique

```python
from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.testing.abstract_test_collection import AbstractTestCollection

class CustomTest(AbstractTestCollection):

  def test_function(self,  data, column_name, threshold)-> SingleTestResult:
      data = ge.from_pandas(data.df)
      uniqueness = data.expect_column_values_to_be_unique(column=column_name)
      passed = uniqueness["success"]
      metric = uniqueness["result"]["element_count"]
      return self.save_results(SingleTestResult(
          passed=passed, 
          metric = metric)
    )

custom_test = CustomTest(tests.tests_results)

custom_test.test_function(
  data=actual_ds,
  column_name='age',
  threshold=0.5
)
```

#### 2. Custom test for validating the frequency of a category is lower than the threshold

We have created a function "test\_category\_frequency" under the Class  `DataQuality` to check if the ratio of the Category in a column is less than a threshold

```python
from generated.ml_worker_pb2 import SingleTestResult
from ml_worker.testing.abstract_test_collection import AbstractTestCollection

class DataQuality(AbstractTestCollection):

  def test_category_frequency(self, data, threshold, column_name, category)-> SingleTestResult:
    freq_of_cat = data[column_name].value_counts()[category]/ (len(data))
    passed = freq_of_cat < threshold

    return self.save_results(SingleTestResult(
        passed=passed,
        metric=freq_of_cat,
    ))

data_quality_test = DataQuality(tests.tests_results)
data_quality_test.test_category_frequency(
  data=actual_ds.df,
  column_name='sex',
  category='male',
  threshold=0.5
)
```
