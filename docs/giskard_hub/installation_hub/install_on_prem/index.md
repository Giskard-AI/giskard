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

## 2. Start the ML worker

Giskard executes your model using an ML worker that runs the model. The worker is created along with your project, using the dependencies in your current environment. You can start the worker on Giskard Hub, if it is not started automatically.

For advanced and flexible usages, please check [our doc for ML worker](../mlworker/index.md).

You're all set to try Giskard in action. Upload your first model, dataset or test suite by following the [upload an object](../../../upload/index.md) page.
