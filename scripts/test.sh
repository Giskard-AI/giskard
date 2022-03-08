#! /usr/bin/env sh

# Exit in case of error
set -e

DOMAIN=backend \
SMTP_HOST="" \
TRAEFIK_PUBLIC_NETWORK_IS_EXTERNAL=false \
INSTALL_DEV=true \
GISKARD_PLAN=enterprise \
docker-compose -f docker-compose.yml -f docker-compose.dev.yml config \
| sed 's/app-db-data/app-db-test-data/g;s/pgadmin-data/pgadmin-test-data/g' > docker-stack.yml

docker-compose -f docker-stack.yml build
docker-compose -f docker-stack.yml down -v --remove-orphans # Remove possibly previous broken stacks left hanging after an error
docker-compose -f docker-stack.yml up -d
docker-compose -f docker-stack.yml exec -T backend bash /app/tests-start.sh "$@"
docker-compose -f docker-stack.yml down -v --remove-orphans
