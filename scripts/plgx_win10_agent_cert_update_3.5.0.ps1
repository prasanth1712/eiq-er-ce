# Copyright 2022 EclecticIQ. All rights reserved.
# Use this script to perform cert update on EclecticIQ Agent v3.5.0 via 
# Custom Script Execution on server. Update the server IP on line 12 below
# and new cert download url on line 14 and push the script to the agent.
# A sample download url for new cert is already provided on line 14 below.
#
# Platform: Windows x64

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::TLS12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ip="<PROVIDE_SERVER_IP_HERE>"

$certdownloadurl = -join("https://", $ip, "/downloads/certificate.crt")

$tempdir="c:\plgx-temp\"
$taskfile= -join($tempdir, "update_cert.bat")
$srcpath = -join($tempdir, "updated_cert.crt")
$destpath="c:\Program Files\plgx_osquery\certificate.crt"
$task = "EclecticIQ Agent Cert Update"
$xmlurl = -join("https://", $ip, "/downloads/windows/plgx_agent_cert_update_3.5.0.xml")
$taskxml = -join($tempdir, "plgx_agent_cert_update_3.5.0.xml")

if ($(Get-ScheduledTaskInfo -TaskName $task -ErrorAction SilentlyContinue).TaskName -eq $task)
{
    Unregister-ScheduledTask -TaskName $task -Confirm:$False
    write-output "Unregistered existing scheduled task '$task'"
}

if (-not (Test-Path -LiteralPath $tempdir)) 
{
    New-Item -Path $tempdir -ItemType Directory
    write-output "Created directory '$tempdir'"
}
else
{
    write-output "Directory '$tempdir' already exists !!"
}

try
{
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile($certdownloadurl, $srcpath)
    $wc.DownloadFile($xmlurl, $taskxml)
}
catch
{
    write-error "Error while downloading file from server"
    Exit 1 
}

Remove-Item -Force $taskfile
New-Item -Force $taskfile
Add-Content -Path $taskfile 'sc stop plgx_agent'
Add-Content -Path $taskfile "copy /Y `"$srcpath`" `"$destpath`""
Add-Content -Path $taskfile 'sc start plgx_agent'

try
{
    Register-ScheduledTask -TaskName $task -Xml (get-content $taskxml | out-string) -Force
}
catch
{
    write-error "Failed creating '$task' scheduled task"
    Exit 3 
}

if ($(Get-ScheduledTaskInfo -TaskName $task -ErrorAction SilentlyContinue).TaskName -eq $task)
{
	write-output "Successfully created '$task' scheduled task !!"
	
	$trigger =  New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(120) 
	Set-ScheduledTask -TaskName $task -Trigger $trigger
	write-output "Successfully updated '$task' run time!!"
}
