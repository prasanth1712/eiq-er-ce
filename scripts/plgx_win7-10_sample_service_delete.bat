@echo off
REM Copyright 2020 EclecticIQ. All rights reserved.
REM
REM Platform: Windows x64
REM
REM Description: This is a sample script that can be used to delete a service
REM on Windows agent(s) via Polylogyx Endpoint Platform Server Response Action 
REM UI. Update your service name on line 19 and proceed to the steps described 
REM below.
REM
REM Details: Assuming admin is logged-in to the server, go to 'Response Action' 
REM tab and click 'Create New Response Action'. Select 'Custom Action' and 
REM provide 'Script Name', upload this file or paste contents in the 'Content' 
REM section and select 'Script Type' as 'Batch'. Finally, Select Hosts on which
REM the script needs to run. Click 'Send' to push the script on the agent(s). 
REM The result of script execution can be viewed in Response Action View.

setlocal
set serviceName="MyService"

sc stop %serviceName%
sc delete %serviceName%
endlocal
