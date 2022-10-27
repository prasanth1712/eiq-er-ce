#!/bin/bash
echo "Starting docker entry point script..."

if [ "$RSYSLOG_FORWARDING" == "true" ] ; then
    echo "Starting rsyslog"
    exec `rsyslogd -n -f /etc/rsyslogd.conf`
else
    echo "Rsyslog forwarding is disabled"
    tail -f /dev/null
fi
