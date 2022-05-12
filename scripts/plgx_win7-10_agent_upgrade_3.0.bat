@echo off
REM Copyright 2022 EclecticIQ. All rights reserved.
REM Use this script to perform upgrade on EclecticIQ Agent v3.0 via 
REM Custom Script Execution on server. Update the server IP on line 14 below
REM and push the script to the agent.
REM
REM Platform: Windows x64
REM Pre-requisite: Before running the script, make sure curl is installed on 
REM the agent and its path set in environment variables.
REM Set local environment
setlocal

REM Example: set IP=10.10.10.10
SET IP=<SET_SERVER_IP_ADDRESS_HERE_WITHOUT_ENCLOSING_IN_QUOTES>

SET TEMPDIR=c:\plgx-temp
SET OUTPUT="%TEMPDIR%\plgx_cpt_maint.exe"
SET TASKXML="%TEMPDIR%\plgx_agent_upgrade_3.0.xml"
SET TASK="EclecticIQ Agent Maintenance"
SET URL="https://%IP%/downloads/windows/plgx_cpt.exe"
SET XMLURL="https://%IP%/downloads/windows/plgx_agent_upgrade_3.0.xml"

REM Delete existing task first (in case it exists)
schtasks /DELETE /TN %TASK% /F

REM Create temporary directory for downloading CPT
IF EXIST %TEMPDIR% (
    echo Directory %TEMPDIR% already exists !!
) ELSE (
    echo Creating Directory %TEMPDIR%...
    mkdir %TEMPDIR%
)

REM Download CPT from server in temporary directory
echo Download url set to: %URL%
curl --insecure -f -o %OUTPUT% %URL%
IF %ERRORLEVEL% NEQ 0 (
        ECHO ERROR: Download failed. Exiting!!
        goto :eof
)
echo "CPT download successful !!"

REM Download task xml from server in temporary directory
echo Download url set to: %XMLURL%
curl --insecure -f -o %TASKXML% %XMLURL%
IF %ERRORLEVEL% NEQ 0 (
        ECHO ERROR: Download failed. Exiting!!
        goto :eof
)
echo "Task xml download successful !!"

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
