# ☁️ Private Cloud


```{toctree}
:caption: Table of Contents
:maxdepth: 2
:hidden:

install_aws/index
install_azure/index
install_gcp/index
```

Private Cloud installation is adapted if you can easily run a **Cloud instance** by your favourite Cloud provider (AWS, GCP or Azure) and want to easily use Giskard collaborative features (collect feedback from business, share results, etc.). Make sure that you have the rights to **open ports** of your Cloud machine because Giskard needs to open a connection with an ML Worker running on your Python environment.

> For other ways to install the Giskard Hub, check the [Hugging Face Space](../install_hfs/index.md) setup
> (easy installation) or the [On-premise](../install_on_prem/index.md) installation.

The Giskard Hub is the app adapted for an enterprise use of Giskard. Extending the features of the open-source library, it enables you to:

* Debug tests to diagnose your issues
* Create domain-specific tests thanks to automatic model insights
* Compare models to decide which model to promote
* Collect business feedback of your model results
* Share your results with your colleagues for alignment
* Store all your QA objects (tests, data slices, evaluation criteria, etc.) in one place to work more efficiently

To know more about the 3 different licenses of the Hub (Trial, Startup and Enterprise) and its differences between the open-source library, have a look at this [page](https://www.giskard.ai/pricing).


::::::{grid} 1 1 2 2


::::{grid-item-card} <br/><h3>AWS</h3>
:text-align: center
:link: install_aws/index.html
::::

::::{grid-item-card} <br/><h3>Azure</h3>
:text-align: center
:link: install_azure/index.html
::::

::::{grid-item-card} <br/><h3>GCP</h3>
:text-align: center
:link: install_gcp/index.html
::::
