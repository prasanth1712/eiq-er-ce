#!/bin/sh
# Copyright 2020 EclecticIQ. All rights reserved.
#
# Platform: Linux x64
#
# Description: This is a sample script that can be used to delete a service on
# Linux agent(s) via Polylogyx Endpoint Platform Server Response Action UI.
# Update string on line 18 to uniquely identify service on the agent and
# proceed to the steps described below.
#
# Details: Assuming admin is logged-in to the server, go to 'Response Action'
# tab and click 'Create New Response Action'. Select 'Custom Action' and provide
# 'Script Name', upload this file or paste contents in the 'Content' section and
# select 'Script Type' as 'Shell Script'. Finally, Select Hosts on which the
# script needs to run. Click 'Send' to push the script on the agent(s). The
# result of script execution can be viewed in Response Action View.

serviceName="myService"

if which systemctl >/dev/null; then
    sudo systemctl stop "$serviceName"
    sudo systemctl disable "$serviceName"
elif which service >/dev/null; then
    sudo service "$serviceName" stop
    echo manual | sudo tee "/etc/init/$serviceName.override"
else
    sudo /etc/init.d/"$serviceName" stop
    sudo update-rc.d -f "$serviceName" remove
fi
