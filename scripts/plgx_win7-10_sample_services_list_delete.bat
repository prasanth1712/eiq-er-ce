@echo off
REM Copyright 2020 EclecticIQ. All rights reserved.
REM
REM Platform: Windows x64
REM
REM Description: This is a sample script that can be used to delete services
REM on Windows agent(s) via Polylogyx Endpoint Platform Server Response Action 
REM UI. Update your services list on line 20 and proceed to the steps described 
REM below.
REM
REM Details: Assuming admin is logged-in to the server, go to 'Response Action' 
REM tab and click 'Create New Response Action'. Select 'Custom Action' and 
REM provide 'Script Name', upload this file or paste contents in the 'Content' 
REM section and select 'Script Type' as 'Batch'. Finally, Select Hosts on which
REM the script needs to run. Click 'Send' to push the script on the agent(s). 
REM The result of script execution can be viewed in Response Action View.

setlocal
REM Example: set services=myservice1,my service2,myservice 3,my_service_4
set services=<UPDATE_COMMA_SEPARATED_SERVICE_NAMES_HERE> 

call :parse "%services%"
goto :eos
:parse

set list=%1
set list=%list:"=%

FOR /f "tokens=1* delims=," %%a IN ("%list%") DO (
  if not "%%a" == "" call :sub "%%a"
  if not "%%b" == "" call :parse "%%b"
)

goto :eos

:sub

echo Removing service %1
SC QUERY "%1" > NUL
IF %ERRORLEVEL% NEQ 1060 (
sc stop "%1"
sc delete "%1"
echo Removed service %1
) ELSE (
echo Service %1 could not be found!!
)

goto :eos

:eos
endlocal
