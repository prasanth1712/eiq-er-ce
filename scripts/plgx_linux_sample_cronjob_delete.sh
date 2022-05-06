#!/bin/sh
# Copyright 2020 EclecticIQ. All rights reserved.
#
# Platform: Linux x64
#
# Description: This is a sample script that can be used to delete a cronjob on
# Linux agent(s) via Polylogyx Endpoint Platform Server Response Action UI.
# Update string on line 19 to uniquely identify cronjob on the agent, update
# corresponding username on line 20 for which cronjob is to be deleted and
# proceed to the steps described below.
#
# Details: Assuming admin is logged-in to the server, go to 'Response Action'
# tab and click 'Create New Response Action'. Select 'Custom Action' and provide
# 'Script Name', upload this file or paste contents in the 'Content' section and
# select 'Script Type' as 'Shell Script'. Finally, Select Hosts on which the
# script needs to run. Click 'Send' to push the script on the agent(s). The
# result of script execution can be viewed in Response Action View.

searchString='myString'
username='myUser'

crontab -l -u $username | grep -v $searchString | crontab -u $username -
