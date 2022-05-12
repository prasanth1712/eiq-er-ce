#!/bin/sh
# Copyright 2022 EclecticIQ. All rights reserved.
# Platform: MacOSX/Linux x64
# Description: This script creates task for service restart after 2 minutes
# Usage: ./plgx_mac_agent_restart_3.5.0.sh -i <IP/FQDN>
#
# NOTE: For MacOS, /usr/libexec/atrun needs to have Full Disk Access Permissions
# for this script to work. Please grant Full Disk Access to /usr/libexec/atrun

_PROJECT="EclecticIQ"
_LINUX_FLAVOUR=""
_BASE_URL=""

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
    echo "Usage : ./plgx_mac_agent_restart_3.5.0.sh -i <IP/FQDN>"
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

  log "Triggering restart.."
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
    _LINUX_FLAVOUR="darwin"
    log "MacOS detected"
  else
    log "Unsupported system detected. Exiting !!"
    exit 1
  fi   
}

downloadDependents() {
  OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
  if [ "$OS" = "linux" ]; then
    _BASE_URL="https://$ip"
    _BASE_URL="$_BASE_URL"/downloads/
    log "$_BASE_URL"
    log "Downloading plgx_cpt for $OS and setting exec perms for it.."
    if [ "$OS" = "linux" ]; then
      mkdir -p /tmp/plgx_osquery
      curl -f -o /tmp/plgx_osquery/plgx_cpt_maint  "$_BASE_URL"linux/plgx_cpt -k || wget -O /tmp/plgx_osquery/plgx_cpt_maint "$_BASE_URL"linux/plgx_cpt --no-check-certificate
      chmod +x /tmp/plgx_osquery/plgx_cpt_maint
    fi
  fi
}

darwinStartAtRun() {
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
}

scheduleRestart() {
  OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
  if [ "$OS" = "linux" ]; then
    echo "sudo /tmp/plgx_osquery/plgx_cpt_maint -x" | at now + 2 minute
  else
    darwinStartAtRun
    echo "sudo /usr/local/bin/plgx_cpt -x" | at now + 2 minutes
  fi
  log "Scheduled restart of agent."
}

log() {
  echo "[+] $1"
}

_restart() {
  downloadDependents
  scheduleRestart
  log "Congratulations! The $_PROJECT service has been scheduled for restart."
}

whatOS
set -e
parseCLArgs "$@"

# EOF
