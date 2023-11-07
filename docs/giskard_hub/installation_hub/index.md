# 🌐 Install the Giskard Hub

The Giskard Hub is the app adapted for an enterprise use of Giskard. Extending the features of the open-source library, it enables you to:
* Debug tests to diagnose your issues
* Create domain-specific tests thanks to automatic model insights
* Compare models to decide which model to promote
* Collect business feedback of your model results
* Share your results with your colleagues for alignment
* Store all your QA objects (tests, data slices, evaluation criteria, etc.) in one place to work more efficiently

> To know more about the 3 different licenses of the Hub (Trial, Startup and Enterprise) and its differences > between the open-source library, have a look at this [page](https://www.giskard.ai/pricing).

You have 3 ways to install the Hub:
* **Hugging Face Space installation**: This is adapted for an **easy installation** in the cloud for prototyping purposes. If you don't want to upload your own model and just want to check some Giskard demo projects, the HF public space is perfect for you.
* **On-premise installation**: This is adapted if your data and model are **private** and you don't have the possibility to use the cloud (for instance, because of privacy and connectivity issues).
* **Private cloud**: This is adapted if you can easily run a **Cloud instance** by your favourite Cloud provider (AWS, GCP or Azure) and want to easily use Giskard collaborative features (collect feedback from business, share results, etc.). Make sure that you have the rights to open ports of your Cloud machine because Giskard needs to open a connection with an ML Worker running on your Python environment.

```{toctree}
:caption: Table of Contents
:maxdepth: 2
:hidden:

install_hfs/index
install_on_prem/index
install_cloud/index
```

::::::{grid} 1 1 2 2
:gutter: 1

:::::{grid-item}
:::{card} <h3><center>🤗 HuggingFace Spaces</center></h3>
:link: install_hfs/index.html
:::
:::::

:::::{grid-item}
:::{card} <h3><center>🏠 On-Premise</center></h3>
:link: install_on_prem/index.html
:::
:::::

:::::{grid-item}
:::{card} <h3><center>☁️ Private Cloud</center></h3>
:link: install_cloud/index.html
:::
:::::
