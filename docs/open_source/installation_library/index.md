# 📥 Install the Giskard Python Library

Giskard supports Python `3.9`, `3.10` and `3.11`.

## Install

::::{tab-set}
:::{tab-item} LLMs

```sh
pip install giskard[llm] -U
```

:::

:::{tab-item} Tabular and NLP

```sh
pip install giskard -U
```

:::
::::

## Upgrade

```sh
pip uninstall giskard
pip install giskard -U
```

## Dependency issues

If you run into conflicts with Giskard dependencies, please uninstall the conflicting libraries and re-install Giskard.

For instance, if you have dependency conflicts with `pandas`, you can run:

```sh
pip uninstall giskard
pip uninstall pandas
pip install giskard -U
```
