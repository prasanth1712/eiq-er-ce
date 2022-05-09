@echo off
REM Copyright 2022 EclecticIQ. All rights reserved.
REM Use this script to perform agent cert update on EclecticIQ Agent v3.5 onwards via 
REM Custom Script Execution on server. Update the server IP on line 12 below and new cert download url on line 14. 
REM A sample download url for new cert is already provided on line 16.
REM
REM Platform: Windows
REM Pre-requisite: Before running the script, make sure curl is installed on
REM the agent and its path set in environment variables.
REM Set local environment
setlocal
SET IP=<SET_SERVER_IP_ADDRESS_HERE_WITHOUT_ENCLOSING_IN_QUOTES>

SET DOWNLOADURL=https://%IP%/downloads/certificate.crt

SET TEMPDIR=c:\plgx-temp
SET TASKFILE=%TEMPDIR%\update_cert.bat
SET SRCPATH=%TEMPDIR%\updated_cert.crt
SET DESTPATH=%ProgramFiles%\plgx_osquery\certificate.crt
SET TASK="EclecticIQ Agent Cert Update"
SET TASKXML="%TEMPDIR%\plgx_agent_cert_update_3.5.0.xml"
SET XMLURL="https://%IP%/downloads/windows/plgx_agent_cert_update_3.5.0.xml"

REM Delete existing task first (in case it exists)
schtasks /DELETE /TN %TASK% /F

REM Create temporary directory for downloading CPT
IF EXIST %TEMPDIR% (
    echo Directory %TEMPDIR% already exists !!
) ELSE (
    echo Creating Directory %TEMPDIR%...
    mkdir %TEMPDIR%
)

echo "Downloading updated cert from server %DOWNLOADURL%"
curl --insecure -f -o "%SRCPATH%" %DOWNLOADURL%
IF %ERRORLEVEL% NEQ 0 (
	    ECHO ERROR: Download cert failed. Exiting!!
        goto :eof
)
echo "Cert download successful !!"

REM Download task xml from server in temporary directory
echo Download url set to: %XMLURL%
curl --insecure -f -o %TASKXML% %XMLURL%
IF %ERRORLEVEL% NEQ 0 (
        ECHO ERROR: Download task xml failed. Exiting!!
        goto :eof
)
echo "Task xml download successful !!"

REM Create another script to run from scheduled task
echo "Writing task steps in task file %TASKFILE%"
echo sc stop plgx_agent > "%TASKFILE%"
echo copy /Y "%SRCPATH%" "%DESTPATH%"  >> "%TASKFILE%"
echo sc start plgx_agent >> "%TASKFILE%"
echo del /F "%SRCPATH%"

:tryagain
REM Compute scheduled time for task (current time + 2 minutes)
SET CURRENTTIME=%TIME%
for /F "tokens=1 delims=:" %%h in ('echo %CURRENTTIME%') do (set /a HR=%%h)
for /F "tokens=2 delims=:" %%m in ('echo %CURRENTTIME%') do (set /a MIN=%%m + 2)

IF %ERRORLEVEL% NEQ 0 (
	    ECHO Probably Minute value is either 08 or 09 which is considered invalid **octal** number by DOS. !!
        ECHO Waiting a minute and trying again...
        ping localhost -n 60 >nul 2>&1
        goto :tryagain
)

IF %MIN% GEQ 60 (
    SET /a MIN=%MIN%-60 
    SET /a HR=%HR%+1
)

REM Date change
IF %HR% GEQ 24 (
	SET HR=0
	SET /a MIN=%MIN%+3
	REM allow date change
    ping localhost -n 60 >nul 2>&1
)

IF %MIN% LEQ 9 (
    SET MIN=0%MIN%
)

IF %HR% LEQ 9 (
    SET HR=0%HR%
)

SET NEWTIME=%HR%:%MIN%

for /f %%I in ('wmic os get localdatetime ^|find "20"') do set CURRENTDATE=%%I
set NEWDATE=%CURRENTDATE:~4,2%/%CURRENTDATE:~6,2%/%CURRENTDATE:~0,4%
echo scheduled date is %NEWDATE%
echo scheduled time is %NEWTIME%

schtasks /create /TN %TASK% /XML %TASKXML% /F
IF %ERRORLEVEL% NEQ 0 (
        ECHO ERROR: Failed to create scheduled task. Exiting!!
        goto :eof
)

schtasks /TN %TASK% /change /SD %NEWDATE% /ST %NEWTIME%
IF %ERRORLEVEL% NEQ 0 (
        ECHO ERROR: Failed to update scheduled task run time. Exiting!!
        goto :eof
)

:eof
endlocal
