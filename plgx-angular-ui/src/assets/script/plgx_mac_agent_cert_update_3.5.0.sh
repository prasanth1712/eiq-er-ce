#!/bin/sh
# Copyright 2022 EclecticIQ. All rights reserved.
# Platform: MacOSX/Linux x64
# Description: This script creates task for cert update after 2 minutes
# Update _CERT_URL on line 63 as per the path of new cert on server for download. For simplicity, _BASE_URL is assumed to be _CERT_URL.
# Usage: ./plgx_mac_agent_cert_update_3.5.0.sh -i <IP/FQDN>
#
# NOTE: For MacOS, /usr/libexec/atrun needs to have Full Disk Access Permissions
# for this script to work. Please grant Full Disk Access to /usr/libexec/atrun

_PROJECT="EclecticIQ"
_LINUX_FLAVOUR=""
_BASE_URL=""
_CERT_URL=""

parseCLArgs(){
  while [ $# -gt 0 ]
  do
    key="${1}"
  case ${key} in
    -i)
    ip="${2}"
    log "IP: $ip"
    shift # past argument=value
    ;;
    
    -h|--help)
    echo "Usage : ./plgx_mac_agent_cert_update_3.5.0.sh -i <IP/FQDN>"
    shift # past argument
    ;;
    *)    
    shift # past argument=value
    ;;
    
    *)
          # unknown option
    ;;
  esac
  done

  log "Triggering cert update.."
  _restart
}

whatOS() {
  OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
  log "OS=$OS"
  if [ "$OS" = "linux" ]; then
    distro=$(/usr/bin/rpm -q -f /usr/bin/rpm >/dev/null 2>&1)
    if [ "$?" = "0" ]; then
      log "RPM based system detected"
      _LINUX_FLAVOUR="rpm"
	else
      _LINUX_FLAVOUR="debian"	
      log "Debian based system detected"
    fi
  elif [ "$OS" = "darwin" ]; then
    log "MacOSX detected"
    _LINUX_FLAVOUR="darwin"
  else
    log "Unsupported system detected. Exiting !!"
    exit 1
  fi   
}

darwinStartAtRun() {
  OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
  if [ "$OS" = "darwin" ]; then
    IS_ATRUN_INSTALLED=$(/bin/launchctl print-disabled system | /usr/bin/grep "com.apple.atrun" | /usr/bin/wc -l | /usr/bin/tr -d ' ')
    if [ "$IS_ATRUN_INSTALLED" = "0" ]; then
        log "atrun may not be installed, attempting to start it anyway"
        /usr/bin/sudo /bin/launchctl load -w /System/Library/LaunchDaemons/com.apple.atrun.plist
    else
        ATRUN_STATE=$(/bin/launchctl print-disabled system | /usr/bin/grep "com.apple.atrun" | /usr/bin/cut -f2 -d'>')
        if [ $ATRUN_STATE = "true" ]; then
            log "Starting atrun"
            /usr/bin/sudo /bin/launchctl load -w /System/Library/LaunchDaemons/com.apple.atrun.plist
        else
            log "atrun already started"
        fi
    fi
  fi
}

downloadDependentsLinux() {
  if [ "$OS" = "linux" ]; then
    _BASE_URL="https://$ip"
    _BASE_URL="$_BASE_URL"/downloads/
    _CERT_URL="$_BASE_URL"
    log "$_BASE_URL"
    log "Downloading cert file and plgx_cpt for $OS and setting exec perms for plgx_cpt.."
    log "Creating temp dir.."
    mkdir -p /tmp/plgx_osquery
    log "Downloading cpt.."
    curl -f -o /tmp/plgx_osquery/plgx_cpt_maint  "$_BASE_URL"linux/plgx_cpt -k || wget -O /tmp/plgx_osquery/plgx_cpt_maint "$_BASE_URL"linux/plgx_cpt --no-check-certificate
    log "Downloading cert.."
    curl -f -o /tmp/plgx_osquery/updated_cert.crt  "$_CERT_URL"certificate.crt -k || wget -O /tmp/plgx_osquery/updated_cert.crt "$_CERT_URL"certificate.crt --no-check-certificate
    log "Setting exec perms for cpt.."
    chmod +x /tmp/plgx_osquery/plgx_cpt_maint
    log "Removing existing task file, if any.."
    sudo rm -f /tmp/plgx_osquery/update_cert.sh
    log "Writing task steps in task file and adding exec perms to it.."
    sudo bash -c 'echo "yes | sudo cp -rf /tmp/plgx_osquery/updated_cert.crt /etc/plgx_osquery/certificate.crt" >> /tmp/plgx_osquery/update_cert.sh'
    sudo bash -c 'echo "sudo /tmp/plgx_osquery/plgx_cpt_maint -x" >> /tmp/plgx_osquery/update_cert.sh'
    log "Done writing task steps in task file"
    chmod +x /tmp/plgx_osquery/update_cert.sh
  fi
}

darwinDownloadDependents() {
  OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
  if [ "$OS" = "darwin" ]; then
    _BASE_URL="https://$ip"
    _BASE_URL="$_BASE_URL"/downloads/
    _CERT_URL="$_BASE_URL"
    log "$_BASE_URL"
    log "Downloading cert file and plgx_cpt for $OS and setting exec perms for plgx_cpt.."
    log "Creating temp dir.."
    mkdir -p /tmp/plgx_osquery
    log "Downloading cert.."
    curl -f -o /tmp/plgx_osquery/updated_cert.crt  "$_CERT_URL"certificate.crt -k || wget -O /tmp/plgx_osquery/updated_cert.crt "$_CERT_URL"certificate.crt --no-check-certificate
    log "Removing existing task file, if any.."
    sudo rm -f /tmp/plgx_osquery/update_cert.sh
    log "Writing task steps in task file and adding exec perms to it.."
    sudo bash -c 'echo "yes | sudo cp -rf /tmp/plgx_osquery/updated_cert.crt /usr/local/etc/plgx_osquery/certificate.crt" >> /tmp/plgx_osquery/update_cert.sh'
    sudo bash -c 'echo "sudo /usr/local/bin/plgx_cpt -x" >> /tmp/plgx_osquery/update_cert.sh'
    log "Done writing task steps in task file"
    chmod +x /tmp/plgx_osquery/update_cert.sh
  fi
}


scheduleCertUpdate() {
  OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
  if [ "$OS" = "darwin" ]; then
    echo "sudo /tmp/plgx_osquery/update_cert.sh" | at now + 2 minutes
  else
    echo "sudo /tmp/plgx_osquery/update_cert.sh" | at now + 2 minute
  fi
  log "Scheduled cert update."
}

log() {
  echo "[+] $1"
}

_restart() {
  OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
  if [ "$OS" = "darwin" ]; then
    darwinDownloadDependents
    darwinStartAtRun
  else
    downloadDependentsLinux
  fi
  scheduleCertUpdate
  log "Congratulations! The $_PROJECT agent certificate has been scheduled for update."
}

whatOS
set -e
parseCLArgs "$@"

# EOF
