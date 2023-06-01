#!/bin/sh

spawn-fcgi -M 666 -s /var/run/fcgiwrap.socket /usr/bin/fcgiwrap
