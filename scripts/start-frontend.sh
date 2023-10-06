#!/usr/bin/env bash

envsubst '\$GSK_HOME \$GSK_DIST_PATH' < $GSK_DIST_PATH/frontend/nginx.conf.template > $GSK_DIST_PATH/frontend/nginx.conf
nginx -c $GSK_DIST_PATH/frontend/nginx.conf
