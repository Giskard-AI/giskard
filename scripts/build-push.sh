#! /usr/bin/env sh

# Exit in case of error
set -e

TAG=${TAG-latest} \
FRONTEND_ENV=${FRONTEND_ENV-production} \
  sh ./scripts/build.sh

docker-compose -f docker-compose.yml -f docker-compose.dev.yml push
