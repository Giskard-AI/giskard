#!/bin/bash
# Script to guard lockfile with timeout

if [ -z "$1" ]
then
    echo "No lockfile to monitor"
    exit 0
fi

MAX_RETRY=${2:-100}
INTERNAL=${3:-0.2}
retry=0
LOCKFILE="$1"
while [ -f "$LOCKFILE" ] && [ $retry -lt $MAX_RETRY ]
do
    echo "Waiting for \"$LOCKFILE\" file to be removed"
    sleep $INTERNAL
    retry=$(( $retry + 1 ))
done

if [ -f "$LOCKFILE" ]
then
    echo "Warning: \"$LOCKFILE\" is still there after $MAX_RETRY retries"
    echo "         Force to remove $LOCKFILE"
    rm "$LOCKFILE"
fi