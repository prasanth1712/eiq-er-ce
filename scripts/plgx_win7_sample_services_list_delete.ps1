# Copyright 2020 EclecticIQ. All rights reserved.
#
# Platform: Windows x64
#
# Description: This is a sample script that can be used to delete services
# on Windows agent(s) via Polylogyx Endpoint Platform Server Response Action UI
# Update your services list on line 16 and proceed to the steps described below.
#
# Details: Assuming admin is logged-in to the server, go to 'Response Action' 
# tab and click 'Create New Response Action'. Select 'Custom Action' and provide
# 'Script Name', upload this file or paste contents in the 'Content' section and
# select 'Script Type' as 'Powershell'. Finally, Select Hosts on which the 
# script needs to run. Click 'Send' to push the script on the agent(s). The 
# result of script execution can be viewed in Response Action View.

$array = @("service 1", "service_2", "service3")
foreach ($serviceName in $array) {
    sc stop $serviceName
    sc delete $serviceName
    Write-Host "$serviceName service deleted."
}
