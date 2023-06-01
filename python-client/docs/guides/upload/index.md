# Upload an object to the Giskard server

You can easily upload to the Giskard server objects, such as **model**, **dataset**, **slicing & transformation functions** and **test suite**.

Uploading objects to the Giskard server will help you:

* **Debug** your model by inspecting the rows that make your test fail
* **Compare** the results of your test suite for different models
* Help you create more **insightful tests** based on domain knowledge

## 1. Install the Giskard server

To install the Giskard server, please check [Install the Giskard server](docs/guide/install_app/index.md).

## 2. Create a Giskard client

To create a Giskard client please, execute the following Python code:

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
:::{tab-item} Test suite upload

```python
from giskard import test_f1, test_accuracy, Suite, GiskardClient

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload on a an external Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "enron"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)

# Create a project
client.create_project(project_name, "Project name", "Small description of the project")

suite = Suite()
.add_test(test_f1(dataset=wrapped_dataset))
.add_test(test_accuracy(dataset=wrapped_dataset))
.upload(client, project_name)
```

Then the suite that you uploaded will appear in the test tab of the Giskard server.
:::
:::{tab-item} Model upload

```python
from giskard import GiskardClient, Model

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload on a an external Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "enron"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)

# Create a project
client.create_project(project_name, "Project name", "Small description of the project")

wrapped_model = Model(model=prediction_function, ...)

wrapped_model.upload(client, project_name)
```

:::
:::{tab-item} Dataset upload

```python
from giskard import GiskardClient, Dataset

url = "http://localhost:19000"  # If Giskard is installed locally
# url = "http://app.giskard.ai" # If you want to upload on a an external Giskard server
token = "API_TOKEN"  # you can generate your API token in the Settings tab of the Giskard application
project_name = "enron"

# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token)

# Create a project
client.create_project(project_name, "Project name", "Small description of the project")

wrapped_dataset = Dataset(df=my_pandas_df, ...)

wrapped_dataset.upload(client, project_name)
```

:::
::::
