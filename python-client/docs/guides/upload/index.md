# ⬆️ Upload an object to the Giskard server

You can easily upload to the Giskard server objects, such as **model**, **dataset**, **slicing & transformation functions** and **test suite**.

Uploading objects to the Giskard server will help you:

* **Debug** your model by inspecting the rows that make your test fail
* **Compare** the results of your test suite for different models
* Help you create more **insightful tests** based on domain knowledge

## 1. Run the Giskard server

To install the Giskard server, please check the [run the Giskard server](../installation_app/index.rst) page.

## 2. Create a Giskard client

To create a Giskard client, please execute the following Python code:

```python
from giskard import GiskardClient

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload in a Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "enron"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)
```

## 3. Create a new project if needed

If you want to upload your object in a new project, you will need to create a new project. To do so, execute the following Python code:

```python
# Create a project
client.create_project(project_name, "Project name", "Small description of the project")
```

## 4. Upload your object

::::{tab-set}
:::{tab-item} Test suite
Upload your suite to the Giskard server to:
* Compare models to decide which model to promote
* Debug your tests to diagnose the issues
* Create more domain-specific tests that are integrating business feedback
* Share your results

```python
from giskard import demo, Model, testing, Suite, GiskardClient

model, _ = demo.titanic()

wrapped_model = Model(model=model, model_type="classification")

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload on a an external Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "my_project_id"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)

# Create a project
client.create_project(project_name, "Project name", "Small description of the project")

suite = Suite() \
    .add_test(testing.test_f1(model=wrapped_model)) \
    .add_test(testing.test_accuracy(model=wrapped_model)) \
    .upload(client, project_name)

```

Then the suite that you uploaded will appear in the test tab of the Giskard server.

<br>

  ![](/_static/test_suite_example.png)
:::
:::{tab-item} Model

Uploading the model to the Giskard server enables you to:
* Compare your model with others using a test suite.
* Gather feedback from your colleagues regarding your model.
* Debug your model effectively in case of test failures.
* Develop new tests that incorporate additional domain knowledge.

```python
from giskard import demo, Model, GiskardClient

model, _ = demo.titanic()

wrapped_model = Model(model=model, model_type="classification")

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload on a an external Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "my_project_id"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)

# Create a project
client.create_project(project_name, "Project name", "Small description of the project")

wrapped_model.upload(client, project_name)
```

:::
:::{tab-item} Dataset
Uploading your dataset to the Giskard server enables you to:
* Inspect and debug your dataset
* Use your dataset as the input for your tests (unit datasets)

```python
from giskard import demo, Dataset, GiskardClient

_ , df = demo.titanic()

wrapped_dataset = Dataset(
    df=df,
    target="Survived",
    cat_columns=["Pclass", "Sex", "SibSp", "Parch", "Embarked"],
)

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload on a an external Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "my_project_id"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)

# Create a project
client.create_project(project_name, "Project name", "Small description of the project")

wrapped_dataset.upload(client, project_name)
```

:::
:::{tab-item} Slicing function

Saving your slicing function to the Giskard server will enable you to:
* Use your slicing functions for testing purposes: your slices can be used as fixtures of your test suite
* Further debug the examples inside your data slice using explanation
* Apply the saved slicing functions to other datasets (new production data, etc.)
  
```python
from giskard import slicing_function, GiskardClient
import pandas as pd

@slicing_function(name="females")
def slice_sex(row: pd.Series):
    return row["Sex"] == "female"

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload on a an external Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "my_project_id"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)

# Create a project
client.create_project(project_name, "Project name", "Small description of the project")

slice_sex.upload(client, project_name)
```
<br>

  ![](/_static/catalog_slice.png)
:::

:::{tab-item} Transformation function

Saving your transformation function in the Giskard server will enable you to:
* Use your transformations for testing purposes: your transformations can be used as fixtures of your test suite
* Use the saved transformations to debug your dataset
* Use the saved transformations to augment your dataset
  
```python
from giskard import transformation_function, GiskardClient
import pandas as pd

@transformation_function(name="increase age")
def increase_age(row):
    row["Age"] = row["Age"] * 0.1
    return row

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload on a an external Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "my_project_id"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)

# Create a project
client.create_project(project_name, "Project name", "Small description of the project")

increase_age.upload(client, project_name)
```
<br>

  ![](/_static/catalog_transfo.png)
:::
::::
