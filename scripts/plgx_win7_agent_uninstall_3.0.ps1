# Copyright 2022 EclecticIQ. All rights reserved.
# Use this script to perform EclecticIQ Agent v3.0 uninstall via 
# Custom Script Execution on server. Update the server IP on line 11 below
# and push the script to the agent.
#
# Platform: Windows x64

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ip="<PROVIDE_SERVER_IP_HERE>"

$tempdir="c:\plgx-temp\"
$url = -join("https://", $ip, "/downloads/windows/plgx_cpt.exe")
$xmlurl = -join("https://", $ip, "/downloads/windows/plgx_agent_uninstall_3.0.xml")
$output = -join($tempdir, "plgx_cpt_maint.exe")
$taskxml = -join($tempdir, "plgx_agent_uninstall_3.0.xml")
$task = "EclecticIQ Agent Maintenance"

schtasks /DELETE /TN $task /F
write-output "Unregistered existing scheduled task '$task'"

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
    $wc.DownloadFile($url, $output)
    $wc.DownloadFile($xmlurl, $taskxml)
}
catch
{
    write-error "Error while downloading file from server"
    Exit 1 
}

$time = [DateTime]::Now.AddMinutes(2)
$hourMinute=$time.ToString("HH:mm")
$day=$time.ToString("MM/dd/yyyy")

schtasks /create /TN $task /XML $taskxml /F
write-output "Successfully created '$task' scheduled task !!"

schtasks /TN $task /change /SD $day /ST $hourMinute
write-output "Successfully updated '$task' run time to '$day $hourMinute'!!"
