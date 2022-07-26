#!/usr/bin/env bash

set -ex

# Build the app with gradle
./gradlew build

# Boot the Java backend (which spins up a dev H2 database)
export JHIPSTER_CORS_ALLOWED_ORIGINS=https://$CODESPACE_NAME-8080.githubpreview.dev
./gradlew -Pprod bootJar
lsof -t -i:9000 | xargs -r kill
mv giskard-server/build/libs/giskard-server-*jar giskard-server/build/libs/giskard-server.jar || true && java -jar giskard-server/build/libs/giskard-server.jar &

# Start the Python backend
cd giskard-ml-worker && PYTHONPATH=generated .venv/bin/python main.py &

# Run the frontend in dev mode
lsof -t -i:8080 | xargs -r kill
cd giskard-frontend && npm install && npm run serve

