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


With the automatic scan, you can proactively identify and address key vulnerabilities to ensure the reliability, fairness, and robustness of your Machine Learning models.


Prerequisites
^^^^^^^^^^^^^

To scan your ML model for vulnerabilities, you need:

- A **Giskard dataframe** composed of the examples you want to scan. To wrap your dataset, `check the instructions here <../wrap_dataset/index.md>`_.
- A **Model**. For example, a model from *scikit-learn*, *Tensorflow*, *HuggingFace*, *catboost*, *PyTorch*, ... or any set of *Python* functions. To wrap your model, see `the docs here <../wrap_model/index.md>`_.


Scan your model to detect vulnerabilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. hint::

    If you want to try this interactively, you can find a ready-to-use `notebook here <https://colab.research.google.com/github/giskard-ai/giskard/blob/main/python-client/docs/getting-started/quickstart.ipynb>`_.

After having wrapped your `model <../wrap_model/index.md>`_ & `dataset <../wrap_dataset/index.md>`_, you can scan your model for vulnerabilities using:

.. code-block:: python

    from giskard import demo, Model, Dataset, scan

    model, df = demo.titanic()

    wrapped_model = Model(model=model, model_type="classification")
    wrapped_dataset = Dataset(df=df, target="Survived", cat_columns=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"])

    scan_results = scan(wrapped_model, wrapped_dataset)

Once the scan completes, you can display the results directly in your notebook:

.. code-block:: python

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
^^^^^^^^^^^^^^^

If you encounter any issues, join our `Discord <https://discord.gg/fkv7CAr3FE>`_ and navigate to the #support channel. Our community
will gladly help!


