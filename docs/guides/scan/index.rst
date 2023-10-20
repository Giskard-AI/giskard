🔍 Scan your ML model
====================

The Giskard python package provides an automatic scan functionality designed to automatically detect potential issues affecting your ML model. The Giskard scan is currently able to detect the following types of issues:


- `Performance bias <../../getting-started/key_vulnerabilities/performance_bias/index.md>`_
- `Unrobustness <../../getting-started/key_vulnerabilities/robustness/index.md>`_
- `Overconfidence <../../getting-started/key_vulnerabilities/overconfidence/index.md>`_
- `Underconfidence <../../getting-started/key_vulnerabilities/underconfidence/index.md>`_
- `Ethical bias <../../getting-started/key_vulnerabilities/ethics/index.md>`_
- `Data leakage <../../getting-started/key_vulnerabilities/data_leakage/index.md>`_
- `Stochasticity <../../getting-started/key_vulnerabilities/stochasticity/index.md>`_
- `Spurious correlation <../../getting-started/key_vulnerabilities/spurious/index.md>`_


With the automatic scan, you can proactively identify and address key vulnerabilities to ensure the reliability, fairness, and robustness of your Machine Learning models.


Prerequisites
^^^^^^^^^^^^^

To scan your ML model for vulnerabilities, you need:

- A **Giskard dataframe** composed of the examples you want to scan. To wrap your dataset, `check the instructions here <../wrap_dataset/index.md>`_.
- A **Model**. For example, a model from *scikit-learn*, *Tensorflow*, *HuggingFace*, *catboost*, *PyTorch*, ... or any set of *Python* functions. To wrap your model, see `the docs here <../wrap_model/index.md>`_.


Scan your model to detect vulnerabilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. hint::

    If you want to try this interactively, you can find a ready-to-use `notebook here <https://colab.research.google.com/github/giskard-ai/giskard/blob/main/docs/getting-started/quickstart.ipynb>`_.

To scan your model, wrap first your `model <../wrap_model/index.md>`_ & `dataset <../wrap_dataset/index.md>`_:

.. code-block:: python

    import giskard

    # Replace this with your own data & model creation.
    df = giskard.demo.titanic_df()
    demo_data_processing_function, demo_sklearn_model = giskard.demo.titanic_pipeline()

    # Wrap your Pandas DataFrame with Giskard.Dataset (test set, a golden dataset, etc.). Check the dedicated doc page: https://docs.giskard.ai/en/latest/guides/wrap_dataset/index.html
    giskard_dataset = giskard.Dataset(
        df=df,  # A pandas.DataFrame that contains the raw data (before all the pre-processing steps) and the actual ground truth variable (target).
        target="Survived",  # Ground truth variable
        name="Titanic dataset", # Optional
        cat_columns=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"]  # List of categorical columns. Optional, but is a MUST if available. Inferred automatically if not.
    )

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

    test_suite = scan_results.generate_test_suite("My first test suite", use_suite_input=False)

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


