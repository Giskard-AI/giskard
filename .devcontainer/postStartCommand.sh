#!/usr/bin/env bash

set -ex

# Build the app with gradle
nohup ./gradlew build --parallel -x test -x integrationTest > ~/build.log

# Boot the Java backend (which spins up a dev H2 database)
./gradlew -Pprod bootJar
lsof -t -i:9000 | xargs -r kill

nohup java -jar giskard-server/build/libs/giskard-server.jar > ~/backend.log &

# Start the Python backend
lsof -t -i:50051 | xargs -r kill
(cd giskard-ml-worker && PYTHONPATH=generated nohup .venv/bin/python main.py > ~/ml-worker.log &)

# Run the frontend in dev mode
lsof -t -i:8080 | xargs -r kill
(cd giskard-frontend && nohup npm run serve > ~/frontend.log &)

