#!/bin/sh
#
# IMPORTANT! If osquery is not installed, it will be installed.

_PROJECT="POLYLOGYX"

_SECRET_OSX=/private/var/osquery/secret.txt
_FLAGS_OSX=/private/var/osquery/osquery.flags
_CERT_OSX=/private/var/osquery/certificate.crt
_OSQUERY_PATH_OSX=/private/var/osquery

_PLIST_OSX=/Library/LaunchDaemons/io.osquery.agent.plist
_OSQUERY_PLIST=/private/var/osquery/io.osquery.agent.plist

_OSQUERY_PKG="darwin/osquery-5.2.2.pkg"
_OSQUERY_SERVICE_OSX="io.osquery.agent"

_SECRET_FILE=""
_FLAGS=""
_CERT=""
_SERVICE=""
_ACTION=""
_BASE_URL=""

CURL_CMD="curl -w httpcode=%{http_code}"
CURL_MAX_CONNECTION_TIMEOUT="-m 100"
CURL_RETURN_CODE=0

parseCLArgs() {
	port="443"
	while [ $# -gt 0 ]
	do
		key="${1}"
	case ${key} in
		-i)
		ip="${2}"
		shift
		;;
		-k)
		cert="${2}"
		shift
		;;
		-p)
		_ACTION="install"
		shift
		;;
		-u)
		if [ "${2}"  = 'd' ]
		then
		_ACTION='uninstall'
		fi
		shift
		;;

		-h|--help)
		echo "Usage : ./plgx_cpt.sh -p -i <IP/FQDN> -k <PATH_TO_CERTIFICATE>"
		shift
		;;
		*)
		shift
		;;
	esac
	done

	if [ "$_ACTION" = 'install' ]; then
		if  [ -z "$ip" ]; then
			echo "Please provide an ip"
			echo "Usage : ./plgx_cpt.sh -p -i <IP/FQDN> -k <PATH_TO_CERTIFICATE>"
			exit
		elif [ -z "$cert" ] ; then
			echo "Please provide the certificate"
			exit
		elif [ ! -f "$cert" ] ; then
			echo "Certificate path provided is not valid!"
			exit
		else
      HTTPS_URL="https://$ip:$port"
      CURL_OUTPUT=`${CURL_CMD} ${CURL_MAX_CONNECTION_TIMEOUT} ${HTTPS_URL} --cacert ${cert} 2> /dev/null` || CURL_RETURN_CODE=$?
      if [ ${CURL_RETURN_CODE} -ne 0 ]; then
        echo "Certificate provided is not valid to connect to the server, Please provide correct certificate."
        exit
      else
        _install
      fi
		fi
	elif [ "$_ACTION" = 'uninstall' ]; then
		_uninstall
	else
		echo "Usage : ./plgx_cpt.sh -p -i <IP/FQDN> -k <PATH_TO_CERTIFICATE>"
	fi
}

validateOS() {
	OS=$(echo `uname`|tr '[:upper:]' '[:lower:]')
	log "OS=$OS"
  if [ ! "$OS" = "darwin" ]; then
    echo "This CPT supports only Mac platform, Please use correct cpt for the proper installation!"
    exit
  fi
}


downloadDependents() {
	_BASE_URL="https://$ip:$port"
	_BASE_URL="$_BASE_URL"/downloads/
	echo "$_BASE_URL"
	echo "Downloading flags file, secret file, cert file"
  mkdir -p "$_OSQUERY_PATH_OSX"
  curl -o $_FLAGS_OSX  "$_BASE_URL"darwin/osquery.flags -k || wget -O $_FLAGS_OSX "$_BASE_URL"darwin/osquery.flags --no-check-certificate
  curl -o $_SECRET_OSX  "$_BASE_URL"secret.txt -k|| wget -O $_SECRET_OSX "$_BASE_URL"secret.txt --no-check-certificate
  cp -R "$cert" "$_OSQUERY_PATH_OSX"
}


fail() {
  echo "[!] $1"
  exit 1
}

log() {
  echo "[+] $1"
}

installOsquery() {
  _OSQUERY_PKG="$_BASE_URL$_OSQUERY_PKG"
  echo "$_OSQUERY_PKG"
  _PKG="$(echo "$_OSQUERY_PKG" | cut -d"/" -f6)"
  sudo curl -# "$_OSQUERY_PKG" -o "/tmp/$_PKG" -k
  sudo installer -pkg "/tmp/$_PKG" -target /
}

verifyOsquery() {
   installOsquery
}

prepareDependents() {
  _SECRET_FILE="$_SECRET_OSX"
  _FLAGS="$_FLAGS_OSX"
  _CERT="$_CERT_OSX"
  _SERVICE="$_OSQUERY_SERVICE_OSX"
	log "_SECRET_FILE=$_SECRET_FILE"
	log "_FLAGS=$_FLAGS"
	log "_CERT=$_CERT"
	log "IMPORTANT! If osquery is not installed, it will be installed."
}

stopOsquery() {
  log "Stopping $_OSQUERY_SERVICE_OSX"
  if launchctl list | grep -qcm1 "$_OSQUERY_SERVICE_OSX"; then
    sudo launchctl unload "$_PLIST_OSX"
  fi
}

startOsquery() {
  log "Starting $_OSQUERY_SERVICE_OSX"
  sudo cp "$_OSQUERY_PLIST" "$_PLIST_OSX"
  sudo launchctl load "$_PLIST_OSX"
}


stopOsqueryAndRemoveService() {
  log "Stopping $_OSQUERY_SERVICE_OSX"
  if launchctl list | grep -qcm1 "$_OSQUERY_SERVICE_OSX"; then
    sudo launchctl unload "$_PLIST_OSX"
    sudo rm -f "$_PLIST_OSX"
  fi
  cd /
  sudo rm -rf /private/var/log/osquery /private/var/osquery
  sudo rm /usr/local/bin/osquery*
  sudo pkgutil --forget io.osquery.agent
}

removeSecret() {
  log "Removing osquery secret: $_SECRET_FILE"
  sudo rm -f "$_SECRET_FILE"
}

removeFlags() {
  log "Removing osquery flags: $_FLAGS"
  sudo rm -f "$_FLAGS"
}

removeCert() {
  log "Removing osquery certificate"
  sudo rm -f "$_CERT"
}

removeDB() {
  log "Removing osquery db"
  sudo rm -f /tmp/osquery.pid
  sudo rm -f /tmp/osquery.db

}

bye() {
  result=$?
  if [ "$result" != "0" ]; then
    if [ "$_ACTION" = "install" ]; then
      echo "[!] Fail to enroll $_PROJECT node"
    else
      echo "[!] Fail to remove $_PROJECT node"
    fi
  fi
  exit $result
}

_install() {
  downloadDependents
  prepareDependents
  verifyOsquery
  stopOsquery
  startOsquery

  log "Congratulations! The node has been enrolled in $_PROJECT"
  log "REMINDER! $_SERVICE has been started and enabled."
}

_uninstall() {
  stopOsqueryAndRemoveService
  removeSecret
  removeFlags
  removeCert

  log "Congratulations! The node has been removed from $_PROJECT"
  log "WARNING! $_SERVICE has been stopped and disabled."
}

trap "bye" EXIT
validateOS
set -e
parseCLArgs "$@"
# EOF

