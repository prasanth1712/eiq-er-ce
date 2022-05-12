#!/bin/bash

logdir="/var/log/nginx"
if [ ! -d $logdir ]; then
    mkdir -p $logdir
fi
service cron start && nginx -g 'daemon off;'
