🔍 Scan Tabular Models
====================

The Giskard python library provides an automatic scan functionality designed to automatically detect `potential vulnerabilities <../../getting-started/key_vulnerabilities/performance_bias/index.md>`_ affecting your ML model. It enables you to proactively identify and address key issues to ensure the reliability, fairness, and robustness of your Machine Learning models.

Step 1: Wrap your dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To scan your model, start by **wrapping your dataset**. This should be a validation or test set in Pandas format, as shown here:

.. code-block:: python

    # Wrap your Pandas DataFrame with Giskard.Dataset (validation or test set)
    giskard_dataset = giskard.Dataset(
        df=df,  # A pandas.DataFrame containing raw data (before pre-processing) and including ground truth variable.
        target="Survived",  # Ground truth variable
        name="Titanic dataset", # Optional: Give a name to your dataset
        cat_columns=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"]  # List of categorical columns. Optional, but improves quality of results if available.
    )


* **Mandatory parameters**
    * `df`: A `pandas.DataFrame` containing raw data (before pre-processing) and including ground truth variable. Extra columns not included as features of the model can remain in `df`.

* **Optional parameters**
    * `target`: The column name in `df` corresponding to the ground truth variable.
    * `name`: Give a name to your dataset.
    * `cat_columns`: List of strings representing names of categorical columns.Can be binary,
      numerical, or textual with a few unique values. If not provided, column types will be inferred automatically.
    * `column_types`: Dictionary of column names and their types (numeric, category or text) for all columns of `df`.
      If not provided, column types will be inferred automatically.

Wrap your model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Next, **wrap your model**. You can wrap either the prediction function or model object, as shown here:

.. code-block:: python

    import giskard

    # Wrap your model with Giskard.Model. Check the dedicated doc page: https://docs.giskard.ai/en/latest/guides/wrap_model/index.html
    # you can use any tabular, text or LLM models (PyTorch, HuggingFace, LangChain, etc.),
    # for classification, regression & text generation.
    def prediction_function(df):
        # The pre-processor can be a pipeline of one-hot encoding, imputer, scaler, etc.
        preprocessed_df = demo_data_processing_function(df)
        return demo_sklearn_model.predict_proba(preprocessed_df)

    giskard_model = giskard.Model(
        model=prediction_function,  # A prediction function that encapsulates all the data pre-processing steps and that could be executed with the dataset used by the scan.
        model_type="classification",  # Either regression, classification or text_generation.
        name="Titanic model",  # Optional
        classification_labels=demo_sklearn_model.classes_,  # Their order MUST be identical to the prediction_function's output order
        feature_names=['PassengerId', 'Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked'],  # Default: all columns of your dataset
        # classification_threshold=0.5,  # Default: 0.5
    )
Now you can scan your model and display your scan report:

.. code-block:: python

    scan_results = giskard.scan(giskard_model, giskard_dataset)
    display(scan_results)  # in your notebook

If you are not working in a notebook or want to keep the results for later, you can save them to an HTML file like this:

.. code-block:: python

    scan_results.to_html("model_scan_results.html")

In both cases, this will produce a dashboard that allows you to explore the detected issues, similar to this one:

.. raw:: html
    :file: ../../assets/scan_widget.html


Automatically generate a test suite based on the scan results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the scan found potential issues in your model, you can automatically generate a test suite.

Generating a test suite from your scan results will enable you to:

* Turn the issues you found into actionable tests that you can directly integrate in your CI/CD pipeline
* Diagnose your vulnerabilities and debug the issues you found in the scan

.. code-block:: python

    test_suite = scan_results.generate_test_suite("My first test suite")

    # You can run the test suite locally to verify that it reproduces the issues
    test_suite.run()


Upload your test suite to the Giskard server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can then upload the test suite to the local Giskard server. This will enable you to:

* Compare the quality of different models to decide which one to promote
* Debug your tests to diagnose the identified issues
* Create more domain-specific tests relevant to your use case
* Share results, and collaborate with your team to integrate business feedback

.. code-block:: python

    # Uploading the test suite will automatically save the model, dataset, tests, slicing & transformation functions inside the Giskard server that you previously installed locally, or on your internal servers. 
    # Create a Giskard client after having installed the Giskard server (see documentation)

    from giskard import GiskardClient

    key = "API_KEY"  # Find it in Settings in the Giskard server
    client = GiskardClient(
        url="http://localhost:19000",  # URL of your Giskard instance
        key=key
    )

    my_project = client.create_project("my_project", "PROJECT_NAME", "DESCRIPTION")

    # Upload to the current project ✉️
    test_suite.upload(client, "my_project")

.. warning:: You may need another token (SPACE_TOKEN) in order to upload your test suite to a private Space on Hugging Face Spaces. To create your Giskard Client, please use the following code instead:

    .. code-block:: python

        key = "API_KEY"  # Find it in Settings in your Giskard Hugging Face Space instance
        hf_token = "SPACE_TOKEN"  # Find it in Upload instructions in your Giskard Hugging Face Space instance
        client = GiskardClient(
            url="https://huggingface.co/spaces/<user-id>/<space-id>",  # URL of the Space
            key=key,
            hf_token=hf_token,
        )

For more information on uploading to your local Giskard server, go to the `Upload an object to the Giskard server <../../guides/upload/index.md>`_ page.

.. note::
   Uploading the test suite will automatically save the model, dataset, tests, slicing & transformation functions inside the Giskard server that you previously installed locally, or on your internal servers.


Troubleshooting
^^^^^^^^^^^^^^^

If you encounter any issues, join our `Discord <https://discord.gg/fkv7CAr3FE>`_ and ask questions in our #support channel. Our community
will gladly help!


