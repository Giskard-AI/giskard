#!/bin/sh

if [[! -e /git/HEAD ]]
then
    cd /git && \
    git --bare init && \
    git update-server-info

    cd /udf-template && \
    git init --initial-branch=main && \
    git add . && \
    git config --global user.email "noreply@giskard.ai" && \
    git config --global user.name "Giskard" && \
    git commit -m 'Added README.md' && \
    git remote add origin /git && \
    git push origin main
fi


spawn-fcgi -M 666 -s /var/run/fcgiwrap.socket /usr/bin/fcgiwrap
