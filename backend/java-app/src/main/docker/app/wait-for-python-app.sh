#!/bin/sh
# wait-for-python-app.sh

set -e

appurl="$1"
shift

until curl "$appurl" --silent --output /dev/null; do
  >&2 echo "Python backend is not available, sleeping"
  sleep 1
done

>&2 echo "Python backend is up - executing command"
exec "$@"
