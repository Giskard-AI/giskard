# ML worker

Giskard executes your model using an ML worker that runs the model:

1. in **a Python environment created by Giskard Hub** (managed),
2. or directly in **your Python environment** (unmanaged),

with all the dependencies required by your model.

## Managed ML worker

- Or let Giskard Hub create and manage an Python environment with all the dependencies of your model


### Setup the environement variables

<!-- TODO: Allow to set env variables -->

## Unmanaged ML worker

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
!giskard worker start -d -k YOUR_KEY -u http://<your IP address>:19000/ --name <ml-work-id>
```

The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.


> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../../../upload/index.md) page.

::::::
::::::{tab-item} From Colab notebook

To start the ML worker from your Colab notebook, run in your Colab cell:

```
!giskard worker start -d -k YOUR_KEY -u http://<your IP address>:19000/ --name <ml-work-id>
```
The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.

> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../../../upload/index.md) page.

::::::
::::::{tab-item} From your terminal

* Run the following command **within the Python environment that contains all the dependencies of your model**:

```
giskard worker start -k YOUR_KEY -u http://<your IP address>:19000/ --name <mlwork-id>
```
The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.

> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../../../upload/index.md) page.

::::::
::::::{tab-item} On Giskard Hub

* Run the following command **within the Python environment that contains all the dependencies of your model** to create a managed Python environment on your Giskard Hub:


You need to indicate a name for the worker

```
giskard worker start -k YOUR_KEY -u http://<your IP address>:19000/
```

* Then, run the following command to

```
giskard worker start -k YOUR_KEY -u http://<your IP address>:19000/
```

The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.

> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../../../upload/index.md) page.

::::::
:::::::
