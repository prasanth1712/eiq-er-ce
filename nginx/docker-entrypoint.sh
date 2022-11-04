#!/bin/bash

logdir="/var/log/nginx"
if [ ! -d $logdir ]; then
    mkdir -p $logdir
fi
echo "Starting Nginx"
/usr/sbin/crond -b
nginx -g 'daemon off;'

