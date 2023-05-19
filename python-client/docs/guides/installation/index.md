# 🔧 Installation


## 1. Install the Giskard library

In order to scan your model for vulnerabilities, you'll need to install the `giskard` library with `pip`:

::::{tab-set} 
:::{tab-item} Windows

```sh
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@user-test/19-05-2023#subdirectory=python-client" --user
```

:::

:::{tab-item} Mac and Linux

```sh
pip install "giskard[scan] @ git+https://github.com/Giskard-AI/giskard.git@user-test/19-05-2023#subdirectory=python-client"
```

:::
::::

:::{info}
Check our installation guide for more details on the installation procedures.
:::


## 2. Install Giskard's docker images
In order to install the Giskard server, Execute the following command in your terminal:
```sh
giskard server start --version 2.0.0-user-test
```
To see the available commands, you can execute:
```sh
giskard server --help  
```
For the full documentation, go to <project:/cli/index.rst>.

## 3. Connect the Giskard ML worker
In order to connect the ML worker, Execute the following command in your terminal:
```sh
giskard worker start -u http://localhost:19000/
```