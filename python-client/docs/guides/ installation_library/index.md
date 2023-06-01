# 🔬 Install the Giskard library

In order to scan your model for vulnerabilities, you'll need to install the `giskard` library with `pip`:

::::{tab-set}
:::{tab-item} Windows

```sh
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client" --user
```

:::

:::{tab-item} Mac and Linux

```sh
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client"
```

:::
::::

## Requirements

Giskard works with Python 3.8, 3.9 and 3.10.

Below is the list of dependencies to make Giskard work:
XXXX

## What should I do if I have dependency issues?

While installing Giskard, if you have any conflicts with the Giskard dependencies (see the list of dependencies for Giskard), please change the version of the conflicting library if possible. For instance, if you have dependency conflicts with pandas, please do
```sh
pip uninstall giskard
pip uninstall pandas
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client"
```
