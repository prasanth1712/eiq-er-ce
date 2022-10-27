#!/bin/sh
# Copyright 2022 EclecticIQ. All rights reserved.
# Platform: Darwin x64
# Description: This script creates task for EclecticIQ agent upgrade via CPT after
# 2 minutes
# Usage: ./plgx_mac_agent_upgrade_4.0.0.sh -i <IP/FQDN>


# IMPORTANT:
# Please ensure that /usr/libexec/atrun has "full disk access" permisssions
# in the end-point before running this script on MacOSX.


# IMPORTANT:
# Please ensure that /usr/libexec/atrun has "full disk access" permisssions
# in the end-point before running this script on MacOSX.

_PROJECT="EclecticIQ ER"
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
                echo "Usage : ./plgx_mac_agent_upgrade_4.0.0.sh -i <IP/FQDN>"
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

    log "Triggering upgrade.."
    upgrade
}

whatOS() {
    OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
    log "OS=$OS"
    if [ "$OS" != "darwin" ]; then
        log "Unsupported system detected. Exiting !!"
        exit 1
    fi     
}

PLATFORM="darwin"
downloadDependents() {
    _BASE_URL="https://${ip}"
    _BASE_URL="${_BASE_URL}"/downloads/
    log "$_BASE_URL"
    log "Downloading plgx_cpt for $OS os and setting exec perms for it.."
    if [[ "$OS" == "${PLATFORM}" ]]; then
        mkdir -p /tmp/plgx_osquery
        if [[ -f /tmp/plgx_osquery/plgx_cpt_maint.sh ]]; then
            rm -f /tmp/plgx_osquery/plgx_cpt_maint.sh
        fi
        curl -f -o /tmp/plgx_osquery/plgx_cpt_maint.sh "${_BASE_URL}${PLATFORM}"/plgx_cpt.sh -k || wget -O /tmp/plgx_osquery/plgx_cpt_maint.sh "${_BASE_URL}${PLATFORM}"/plgx_cpt.sh --no-check-certificate
        chmod +x /tmp/plgx_osquery/plgx_cpt_maint.sh
    fi
}

scheduleUpgrade() {
    launchctl load -w /System/Library/LaunchDaemons/com.apple.atrun.plist
    if [[ $? -ne 0 ]]; then
        log "launchctl load -w /System/Library/LaunchDaemons/com.apple.atrun.plist failed with error ${?}"
    fi
    echo "sudo bash /tmp/plgx_osquery/plgx_cpt_maint.sh -g s" | at now + 2 minutes
    log "Scheduled upgrade of agent."
}

log() {
    echo "[+] $1"
}

upgrade() {
    downloadDependents
    scheduleUpgrade
    log "Congratulations! $_PROJECT has been scheduled for upgrade on the node."
}

whatOS
set -e
parseCLArgs "$@"

# EOF
