#!/bin/sh
# Copyright 2022 EclecticIQ. All rights reserved.
# Platform: Linux x64
# Description: This script creates task for EclecticIQ agent uninstall via CPT after 2 minutes
# Pre-requisite: atd service should be running
# Usage: ./plgx_linux_agent_uninstall_3.0.sh -i <IP/FQDN>

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
    echo "Usage : ./plgx_linux_agent_uninstall_3.0.sh -i <IP/FQDN>"
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

  log "Triggering uninstall.."
  _uninstall
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
  else
    log "Unsupported system detected. Exiting !!"
    exit 1
  fi   
}

isAtdRunning() {
  SYSTYPE=$(ps -p 1 -o comm=)
  if [ "$SYSTYPE" = "systemd" ]; then
    log "Checking atd service state on systemd type system.."
	STATUS="$(systemctl is-active atd.service)"
	if [ "${STATUS}" = "active" ]; then
		log "atd service detected as Active"
	else
		log " atd service not running.... so exiting!!"
		exit 1
	fi
  else
    log "Checking atd service state on systemV type system.."
	service atd status | grep 'running' &> /dev/null
	if [ $? == 0 ]; then
		log "atd service detected as Running"
	else
		log " atd service not running.... so exiting!!"
		exit 1
	fi
  fi
}

downloadDependents() {
  _BASE_URL="https://$ip"
  _BASE_URL="$_BASE_URL"/downloads/
  log "$_BASE_URL"
  log "Downloading plgx_cpt for $OS os and setting exec perms for it.."
  if [ "$OS" = "linux" ]; then
    mkdir -p /tmp/plgx_osquery
    curl -f -o /tmp/plgx_osquery/plgx_cpt_maint  "$_BASE_URL"linux/plgx_cpt -k || wget -O /tmp/plgx_osquery/plgx_cpt_maint "$_BASE_URL"linux/plgx_cpt --no-check-certificate
    chmod +x /tmp/plgx_osquery/plgx_cpt_maint
  fi
}

scheduleUninstall() {
    echo "sudo /tmp/plgx_osquery/plgx_cpt_maint -u s" | at now + 2 minute
    log "Scheduled uninstall of agent."
}

log() {
  echo "[+] $1"
}

_uninstall() {
  downloadDependents
  scheduleUninstall
  log "Congratulations! $_PROJECT has been scheduled to be removed from node."
}

whatOS
isAtdRunning
set -e
parseCLArgs "$@"

# EOF
