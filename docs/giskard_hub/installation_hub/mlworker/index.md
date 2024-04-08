# ML worker

Giskard executes users' models using an ML worker. This process can run either:

1. in **a Python environment created by Giskard Hub** ([managed ML worker](#managed-ml-worker)),
2. or directly in **your Python environment** ([unmanaged ML worker](#unmanaged-ml-worker)),

Metadata of the python environment that includes the dependencies of your model is called a **kernel**. The kernel is used to create the environment for the ML worker.

## Managed ML worker
A managed kernel can be create in two ways:
- From the Giskard Hub interface
- From the Giskard Python library, when creating a new project (`giskard.create_project(...)`)

Based on a managed kernel Giskard Hub will create a virtual environment on the same host as the Hub.

## Unmanaged ML worker

It's also possible to run ML Worker externally from the Giskard Hub. The main benefits are:

- Reuse of an existing environment will all the necessary dependencies
- Offloading heavy computations to a different machine

Once the external ML worker is started, an unmanaged kernel will be automatically associated with it on the Hub side.

You need to associate the kernel with your project in Giskard Hub to use it for the models in your project.

We support to execute the ML worker:

- From your **local notebook** within the kernel that contains all the dependencies of your model
- From **Google Colab** within the kernel that contains all the dependencies of your model
- From a **terminal** within the Python environment that contains all the dependencies of your model

:::{note}
If you plan to use LLM-assisted tests or transformations, don’t forget to set the ``OPENAI_API_KEY`` environment
variable before starting the Giskard worker.
:::

:::::::{tab-set}
::::::{tab-item} From a local notebook

To start the ML worker from a notebook, run the following code in a notebook:

```
!giskard worker start -d -k YOUR_KEY -u http://<your IP address>:19000/ --name <your ML worker name>
```

::::::
::::::{tab-item} From Colab notebook

To start the ML worker from your Colab notebook, run in your Colab cell:

```
!giskard worker start -d -k YOUR_KEY -u http://<your IP address>:19000/ --name <your ML worker name>
```

::::::
::::::{tab-item} From your terminal

Run the following command **within the Python environment that contains all the dependencies of your model**:

```
giskard worker start -k YOUR_KEY -u http://<your IP address>:19000/ --name <your ML worker name>
```

::::::
:::::::

The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.

:::{note}
If your Giskard Hub is hosted in a private Hugging Face Space, you will need to append `--hf-token HF-TOKEN` to the command, in order to start and connect your worker.
:::

To find the **exact** command with the right API Access Key (`YOUR_KEY`), as well as HuggingFace token (`HF-TOKEN`), go to the "ML Worker" section in the Settings tab in the Giskard Hub.


:::{note}
To see the available commands of the worker, you can execute:

    !giskard worker --help

in the local notebook or Colab notebook.
Or exexute the following command in your terminal:

    giskard worker --help
:::

For advanced usages of the worker cli, please check our API Reference.
