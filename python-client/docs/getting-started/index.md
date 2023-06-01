# Getting Started

Load the titanic demo models and dataset 👇
```python
from giskard.demo import titanic  # for demo purposes only 🛳️
original_model, df = titanic()  # Replace with your dataframe creation
```

Follow the code snippet below to wrap a dataset 👇
```python
from giskard import Dataset

# Wrap your Pandas Dataframe with Giskard dataset 🎁
giskard_dataset = Dataset(df,
                          target="Survived",
                          name="Titanic dataset")

```

Follow the code snippet below to wrap a model 👇
```python
from giskard import Model

# Wrap your model with Giskard model 🎁
giskard_model = Model(original_model, model_type="classification", name="Titanic model")
```

Follow the code snippet below to scan your model 👇
```python
import giskard

results = giskard.scan(wrapped_model, wrapped_dataset)

display(results)  # in your notebook

```

Generate a test suite from the scan 👇
```python
test_suite = results.generate_test_suite("My first test suite")

# You can run the test suite locally to verify that it reproduces the issues
test_suite.run()
```

Upload artefacts 👇
```python
from giskard import GiskardClient

# Create a Giskard client
token = "API_TOKEN" # Find it in Settings
client = GiskardClient(
    url="http://localhost:19000",  # URL of your Giskard instance
    token=token
)

my_project = client.create_project("my_project", "PROJECT_NAME", "DESCRIPTION")

# Upload to the current project ✉️
test_suite.upload(client, "my_project")
```