# 🏠 On-Premise

The On-Premise installation of Giskard is often adapted if your data and model are **private** and/or you don't have the possibility to use the cloud (for instance, because of connectivity issues). For other ways to install the Giskard Hub, check the [Hugging Face Space](../install_hfs/index.md) setup (easy installation) or the [Private Cloud](../install_on_prem/index.md) installation.

The Giskard Hub is the app adapted for an enterprise use of Giskard. Extending the features of the open-source library, it enables you to:

* Debug tests to diagnose your issues
* Create domain-specific tests thanks to automatic model insights
* Compare models to decide which model to promote
* Collect business feedback of your model results
* Share your results with your colleagues for alignment
* Store all your QA objects (tests, data slices, evaluation criteria, etc.) in one place to work more efficiently

To know more about the 3 different licenses of the Hub (Trial, Startup and Enterprise) and its differences between the open-source library, have a look at this [page](https://www.giskard.ai/pricing).

## 1. Start the Hub

To run the Giskard hub you need **3 requirements**:

1. A **Linux**, **macOS** machine, or **WSL2 in Windows**
2. To install the Giskard **Python library**, see [here](../../../open_source/installation_library/index.md).
3. A **running** ``docker``. After [installation](https://docs.docker.com/engine/install/debian/) of Docker, you can run it in the background by just opening the Docker app (Mac or Windows).

> For an easy **installation of Docker** you can execute:
> ```
> sudo curl -fsSL https://get.docker.com -o get-docker.sh
> sudo sh get-docker.sh
> ```
> If you don't have the `sudo` rights to run docker, please see the Docker setup [page](https://docs.docker.com/engine/install/linux-postinstall/).



To start the Giskard hub, **once the 3 above requirements are met**, execute the following command in your terminal:

```
giskard hub start
```

You'll then be able to open Giskard at `http://localhost:19000/`

> ### ⚠️ Warning
> - Make sure to **run Docker** before starting the Giskard hub
> - If the giskard command is not found then you need first to install the Giskard Python library (see the doc section [here](../../../open_source/installation_library/index.md)).
> - To see the available commands of the giskard hub, you can execute:
> ```
> giskard hub --help
> ```

<!-- TODO: Create an ML Worker on a hub -->

## 2. Start the ML worker

Giskard executes your model using a worker that runs the model directly in **your Python environment**, with all the dependencies required by your model. You can either execute the ML worker:

- From your **local notebook** within the kernel that contains all the dependencies of your model
- From **Google Colab** within the kernel that contains all the dependencies of your model
- Or from **your terminal** within the Python environment that contains all the dependencies of your model

:::{note}
If you plan to use LLM-assisted tests or transformations, don’t forget to set the ``OPENAI_API_KEY`` environment
variable before starting the Giskard worker.
:::

:::::::{tab-set}
::::::{tab-item} From your local notebook

To start the ML worker from your notebook, run in the cell of your notebook:

```
!giskard worker start -d -k YOUR_KEY
```

The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.


> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../../upload/index.md) page.

::::::
::::::{tab-item} From Colab notebook

To start the ML worker from your Colab notebook, read the following [instructions](../../../cli/ngrok/index.rst) in order to get the
`ngrok_API_token`. Once you got your token, run in your **local** terminal (**not the the terminal from Colab**):

```
giskard hub expose --ngrok-token <ngrok_API_token>
```

Then run in a **cell of your Colab notebook**:

```
!giskard worker start -d -k YOUR_KEY -u https://e840-93-23-184-184.ngrok-free.app
```

The API Access Key (`YOUR_KEY`) can be found in the Settings tab of the Giskard Hub.

> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../../upload/index.md) page.

::::::
::::::{tab-item} From your terminal

Run this command **within the Python environment that contains all the dependencies of your model**:

```
giskard worker start -k -u http://localhost:19000/
```

You then will be asked to provide your API Access Key. The API Access key can be found in the Settings tab of the Giskard hub (accessible via: http://localhost:19000/)

> ### ⚠️ Warning
> To see the available commands of the worker, you can execute:
>```
>!giskard worker --help
>```

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../../upload/index.md) page.

::::::
:::::::