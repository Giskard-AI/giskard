#!/usr/bin/env bash

[ ! -d $PGDATA ] && initdb -D "$PGDATA" -U giskard
bash $GSK_DIST_PATH/file-guard.sh "$PGDATA/postmaster.pid"
postgres -D "$PGDATA"
