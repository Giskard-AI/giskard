# 📥 Install the Giskard Python Library

## Install the Giskard Python Library for only Python use (no Giskard server) without LLM models

If you don't want to use the UI features and your model is not a text generation model, you need to install the `giskard` library with `pip`:

::::{tab-set}
:::{tab-item} Mac and Linux

```sh
pip install "giskard>=2.0.0b" -U
```

:::

:::{tab-item} Windows

```sh
pip install "giskard>=2.0.0b" -U --user
```

:::
::::

## Install the Giskard Python Library for Python + Giskard server (UI features) without LLM

If you want to use the Giskard server but your model is not a text generation model you need to install the `giskard` library with `pip`:

::::{tab-set}
:::{tab-item} Mac and Linux

```sh
pip install "giskard[server]>=2.0.0b" -U
```

:::

:::{tab-item} Windows

```sh
pip install "giskard[server]>=2.0.0b" -U --user
```

:::
::::

## Install the Giskard Python Library for only Python use (no Giskard server) and with LLM

If you don't want to use the UI features and your model is a text generation model, you need to install the `giskard` library with `pip`:

::::{tab-set}
:::{tab-item} Mac and Linux

```sh
pip install "giskard[llm]>=2.0.0b" -U
```

:::

:::{tab-item} Windows

```sh
pip install "giskard[llm]>=2.0.0b" -U
```

:::
::::

## Install the Giskard Python Library with full functionalities (server + LLM)

::::{tab-set}
:::{tab-item} Mac and Linux

```sh
pip install "giskard[server, llm]>=2.0.0b" -U
```

:::

:::{tab-item} Windows

```sh
pip install "giskard[server, llm]>=2.0.0b" -U
```

:::
::::

## Requirements

`giskard[server]` works with Python `3.8`, `3.9` and `3.10`.

Below is the list of dependencies needed to make `giskard[server]` work:

```sh
dependencies = [
    "cloudpickle>=1.1.1",
    "zstandard>=0.10.0 ",
    "mlflow-skinny>=2",
    "numpy>=1.22.0,<1.24.0", # shap doesn't work with numpy>1.24.0: module 'numpy' has no attribute 'int'
    "scikit-learn>=1.0",
    "scipy>=1.7.3,<1.9", # eli5 doesn't work with scipy>=1.9: cannot import name 'itemfreq' from 'scipy.stats'
    "shap>=0.41.0",
    "eli5>=0.12.0",
    "ipython", # eli5.show_prediction doesn't work without ipython
    "requests-toolbelt>=0.9.1",
    "mixpanel>=4.4.0",
    "grpcio>=1.39.0,<=1.51.1",
    "grpcio-status>=1.16.0,<=1.51.1",
    "requests>=2.19",
    "protobuf<=3.20.3",
    "pydantic>=1.7",
    "tenacity>=4.11.0",
    "python-daemon>=2.2.2,<3",
    "click>=7.0",
    "lockfile>=0.12.2",
    "psutil>=5.4.6",
    "tqdm>=4.42.0",
    "setuptools>=39.1.0,<68.0.0",
    "pycryptodome>=3.6.1",
    "pandas>=1.3.4,<2",
    "docker>=6.0.0",
    "xxhash>=2.0.0",
    "langdetect>=1.0.9",
    "chardet",  # text metadata
    "jinja2>=3",  # scan template (temporary)
]
```

## What should I do if I have dependency issues?

While installing Giskard, if you have any conflicts with the Giskard dependencies (see the list of dependencies above), please change the version of the conflicting libraries.

For instance, if you have dependency conflicts with `pandas`, please do:

```sh
pip uninstall giskard
pip uninstall pandas
pip install "giskard>=2.0.0b" -U
```
