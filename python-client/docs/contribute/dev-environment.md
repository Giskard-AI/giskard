# How to configure local development environment

After cloning the repository here are the useful commands to set up the local environment:

### Pre-commit hooks installation
Pre-commit hooks ensure that the basic code quality checks are performed before the code is committed

The current pre-commit hool configuration is defined in `.pre-commit-config.yaml`

To install it run:

```shell
brew install pre-commit
pre-commit install
```


## Troubleshooting

### `Fatal Python error: segmentation fault` when running `pytest` on MacOS

This is probably caused by a [known issue](https://github.com/microsoft/LightGBM/issues/4707) with `libomp>=12` and LightGBM on MacOS.
You can avoid this problem by downgrading `libomp` to version 11.1.0, which is compatible with LightGBM.

```sh
$ wget https://raw.githubusercontent.com/Homebrew/homebrew-core/fb8323f2b170bd4ae97e1bac9bf3e2983af3fdb0/Formula/libomp.rb
$ brew install ./libomp.rb
```
