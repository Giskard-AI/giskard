🔍 Scan your ML model
===============

Before testing Machine Learning models, it's crucial to have a comprehensive understanding of the critical vulnerabilities that can impact your model. The Giskard scan is designed to automatically detect a variety of significant risks associated with your ML model. Learn more about different vulnerabilities here:

.. toctree::
   :maxdepth: 1

   performance_bias/index
   robustness/index
   overconfidence/index
   underconfidence/index
   ethics/index
   data_leakage/index
   stochasticity/index

By conducting a Giskard scan, you can proactively identify and address these vulnerabilities to ensure the reliability, fairness, and robustness of your Machine Learning models.


Prerequisites
^^^^^^^^^

To scan your ML model for vulnerabilities, you need:

- A **Giskard dataframe** composed of the examples you want to scan. To wrap your dataset, see `here <../wrap_dataset/index.md>`_.
- A **Model**. For example, a model from *scikit-learn*, *Tensorflow*, *HuggingFace*, *catboost*, *PyTorch*, ... or any set of *Python* functions. To wrap your model, see `here <../wrap_model/index.md>`_.


Scan your model to detect vulnerabilities
^^^^^^^^^

After having wrapped your `model <../wrap_model/index.md>`_ & `dataset <../wrap_dataset/index.md>`_, you can scan your model for vulnerabilities using:

.. code-block:: python

    from giskard import demo, Model, Dataset, scan

    model, df = demo.titanic()

    wrapped_model = Model(model=model, model_type="classification")
    wrapped_dataset = Dataset(df=df, target="Survived", cat_columns=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"])

    scan_results = scan(wrapped_model, wrapped_dataset)

    display(scan_results)  # in your notebook

This will produce a dashboard directly in your notebook that allows you to explore the detected issues:

.. image:: ../../assets/scan_results.png

You can also get a table of the scan results as a `pandas.DataFrame`. This is useful if you want to save the results of
the scan to a CSV or HTML file.

.. code-block:: python

    results_df = scan_results.to_dataframe()
    results_df.to_csv("scan_results_my_model.csv")


Automatically generate a test suite based on the scan results
^^^^^^^^^

Generating a test suite from your scan results will enable you to:

* Turn the issues you found into actionable tests that you can directly integrate in your CI/CD pipeline
* Diagnose your vulnerabilties and debug the issues you found in the scan

.. code-block:: python

    test_suite = scan_results.generate_test_suite("My first test suite")

    # You can run the test suite locally to verify that it reproduces the issues
    test_suite.run()

Upload your test suite to the Giskard server
^^^^^^^^^

You can then upload the test suite to the local Giskard server. This will enable you to:

* Compare the quality of different models to decide which one to promote
* Debug your tests to diagnose the identified issues
* Create more domain-specific tests relevant to your use case
* Share results, and collaborate with your team to integrate business feedback

.. code-block:: python

    # Uploading the test suite will automatically save the model, dataset, tests, slicing & transformation functions inside the Giskard server that you previously installed locally, or on your internal servers. 
    # Create a Giskard client after having installed the Giskard server (see documentation)
    token = "API_TOKEN"  # Find it in Settings in the Giskard server
    client = GiskardClient(
        url="http://localhost:19000",  # URL of your Giskard instance
        token=token
    )

    my_project = client.create_project("my_project", "PROJECT_NAME", "DESCRIPTION")

    # Upload to the current project ✉️
    test_suite.upload(client, "my_project")
    
For more information on uploading to your local Giskard server, go to the [Upload an object to the Giskard server](../upload/index.md) page.

.. note::
   Uploading the test suite will automatically save the model, dataset, tests, slicing & transformation functions inside the Giskard server that you previously installed locally, or on your internal servers.


Troubleshooting
^^^^^^^^^

If you encounter any issues, join our `Discord <https://discord.gg/fkv7CAr3FE>`_ and navigate to the #support channel. Our community
will gladly help!


