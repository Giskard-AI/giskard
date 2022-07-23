#!/usr/bin/env bash

set -ex

./gradlew build
docker compose -f docker-compose.dev.yml -f docker-compose.yml up -d db
cd giskard-frontend && npm install && npm run serve
