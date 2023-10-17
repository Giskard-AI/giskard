# Giskard developer readme

🚧  **WORK IN PROGRESS** 🚧
This readme is in process of creation, some information can be subject to change

## Requirements
- Java 17 ([Eclipse Temurin JDK](https://adoptium.net/installation/) for example)
- Python >= 3.7.13 with `pip`

## Quick start from sources on localhost
In order to run Giskard from sources you can run the following command:
```shell
./gradlew start --parallel
```
Giskard UI will be available at http://localhost:8080/

After running the command above there will be 3 modules running:
- frontend
- backend
- ml-worker

> When running Giskard in "dev mode" (as above) there's an H2 database that's used instead of a real one, the default location of this H2 database is `$HOME/giskard-home/database`

To build the project use
```shell
./gradlew build --parallel
```

This command will build all modules, including:
- creation of virtual environment inside ml-worker/.venv
- installing node inside .gradle


## Dockerized Giskard execution
By default Giskard is meant to be run inside Docker, by executing
```shell
docker-compose up
```

### Building Docker containers
Use the following command to build docker containers locally
```shell
docker-compose build --parallel
```
To check the logs, run:

```bash
docker-compose logs
```

To check the logs of a specific service, add the name of the service, e.g.:

```bash
docker-compose logs backend
```


## Python client
To install the latest version of python library `giskard` the following script can be used:
```shell
sh -c "$(curl -fsSL https://raw.githubusercontent.com/Giskard-AI/giskard/main/scripts/install-giskard-client-dev.sh)"
```
it will use the default `pip` available in the environment. To install `giskard` using a specific `pip` you can modify the command above, like
```shell
sh -c "$(curl -fsSL https://raw.githubusercontent.com/Giskard-AI/giskard-client/main/scripts/install-giskard-client-dev.sh)" - /path/to/pip
```


## Windows caveats

There are some extra steps required to use Giskard on Windows.

If you get this error: `'EntryPoints' object has no attribute 'get'`
Then please run:
> pip install importlib-metadata==4.1F3.0