# 📥 Install the Giskard Python Library

`giskard` works with Python `3.8`, `3.9`, `3.10` and `3.11`.

::::{tab-set}
:::{tab-item} Tabular and NLP Models

```sh
pip install "giskard>=2.0.0b" -U
```

:::

:::{tab-item} LLMs

```sh
pip install "giskard[llm]>=2.0.0b" -U
```

:::
::::

## What should I do if I have dependency issues?

While installing Giskard, if you have any conflicts with the Giskard dependencies, please uninstall the conflicting libraries and re-install Giskard.

For instance, if you have dependency conflicts with `pandas`, please do:

```sh
pip uninstall giskard
pip uninstall pandas
pip install "giskard>=2.0.0b" -U
```
