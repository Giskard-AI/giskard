# ML worker

Giskard executes your model using an ML worker that runs the model:

1. in **a Python environment created by Giskard Hub** ([managed ML worker](#managed-ml-worker)),
2. or directly in **your Python environment** ([unmanaged ML worker](#unmanaged-ml-worker)),

with all the dependencies required by your model.

## Managed ML worker

<!-- TODO: Give the definition of managed ML worker -->

- Or let Giskard Hub create and manage an Python environment with all the dependencies of your model

<!-- TODO: Screenshots of management of managed ML worker -->

### Setup the environement variables

<!-- TODO: Allow to set env variables -->

## Unmanaged ML worker

<!-- TODO: Give the definition of unmanaged ML worker -->

You can either execute the ML worker:

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
!giskard worker start -d -k YOUR_KEY -u http://<your IP address>:19000/
```

::::::
::::::{tab-item} From Colab notebook

To start the ML worker from your Colab notebook, run in your Colab cell:

```
!giskard worker start -d -k YOUR_KEY -u http://<your IP address>:19000/
```

::::::
::::::{tab-item} From your terminal

Run the following command **within the Python environment that contains all the dependencies of your model**:

```
giskard worker start -k YOUR_KEY -u http://<your IP address>:19000/
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

