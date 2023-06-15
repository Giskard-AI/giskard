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