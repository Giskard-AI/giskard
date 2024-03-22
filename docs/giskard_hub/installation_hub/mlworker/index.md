# ML worker

Giskard executes your model using an ML worker that runs the model:

1. in **a Python environment created by Giskard Hub** ([managed ML worker](#managed-ml-worker)),
2. or directly in **your Python environment** ([unmanaged ML worker](#unmanaged-ml-worker)),

with all the dependencies required by your model.

When you create a project on Giskard hub using Giskard Python library, you need to associate a description of the environment where your model runs, which is called a Python **"Kernel"**.

## Managed ML worker

By default, during the creation of a project, a kernel describing your current environment will be automatically created and uploaded to Giskard hub.

Giskard hub is in charge of creating the environment from this kernel. An ML worker managed by the Giskard hub can be started using the environment, which is called "managed ML worker".

You can manage the kernels for managed ML worker in Giskard hub:

- Create a new kernel
- Update the kernel and the environment
- Start the ML worker in the environement described by one kernel
- Delete the kernel

etc.

<!-- TODO: Screenshots of management of managed ML worker -->

<!-- ### Setup the environement variables -->
<!-- TODO: Allow to set env variables -->

## Unmanaged ML worker

You can also directly start an ML worker from your own environment, which is not managed by Giskard hub.

To connect, you need to choose a name for your ML worker. There will be an automatically created kernel during the connection between the ML worker and Giskard hub.

You need to associate the kernel with your project in Giskard hub to use it for the models in your project.

We support to execute the ML worker:

- From your **local notebook** within the kernel that contains all the dependencies of your model
- From **Google Colab** within the kernel that contains all the dependencies of your model
- From **your terminal** within the Python environment that contains all the dependencies of your model

:::{note}
If you plan to use LLM-assisted tests or transformations, don’t forget to set the ``OPENAI_API_KEY`` environment
variable before starting the Giskard worker.
:::

:::::::{tab-set}
::::::{tab-item} From your local notebook

To start the ML worker from your notebook, run the following code in your notebook:

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

> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```
> in the local notebook or Colab notebook.
>
> Or exexute the following command in your terminal:
>```
>giskard worker --help
>```

For advanced usages of the worker cli, please check our API Reference.
