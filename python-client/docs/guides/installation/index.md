# 🔧 Installation


### 1. Install the Giskard library

In order to scan your model for vulnerabilities, you'll need to install the `giskard` library with `pip`:

::::{tab-set} 
:::{tab-item} Windows

```sh
pip install "git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client" --user
```

:::

:::{tab-item} Mac and Linux

```sh
pip install "git+https://github.com/Giskard-AI/giskard.git@feature/ai-test-v2-merged#subdirectory=python-client"
```

:::
::::

:::{info}
Check our installation guide for more details on the installation procedures.
:::


### 2. Install Giskard's docker images

```sh
# Clone giskard
git clone https://github.com/Giskard-AI/giskard.git
# Go to giskard directory
cd giskard
# Pull the docker and start it
export TAG=feature-ai-test-v2-merged
docker compose pull
docker compose up -d --force-recreate --no-build

```

#### Install Giskard Python library

```sh
# Download preview wheel
pip install https://github.com/Giskard-AI/giskard-examples/blob/feature/new-upload-api/preview-dist/giskard-1.9.0-py3-none-any.whl?raw=true
```

#### Access the Jupyter notebook to get our examples

```sh
# Clone giskard-examples
git clone https://github.com/Giskard-AI/giskard-examples.git
# Go to giskard-examples directory
cd giskard-examples
# Checkout the preview branch
git checkout poc/function-storage
# Open the `AI test v2 preview` notebook project with your favorite tool
```
