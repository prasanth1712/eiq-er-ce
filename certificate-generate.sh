#!/bin/bash
if [ "$(whoami &2>/dev/null)" != "root" ] && [ "$(id -un &2>/dev/null)" != "root" ]
    then
    path="$(dirname "$(pwd)")"/.rnd
else
    root_path="/root/.rnd"
    path="$(dirname "$(pwd)")"/.rnd
fi

touch $path $root_path
a=$1
echo $a
if [ -e nginx/private.key ]
then
    echo "Certificate already exists. Please remove the existing certificates and then try again"
else
    openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -keyout nginx/private.key -out nginx/certificate.crt -subj '/CN='$a'/O=EclecticIQ B.V./C=NL'
fi
# Setting tls_hostname as the provided ip address while generating certs

for i in $(find $PWD -type  f -name \*.flags); do # Not recommended, will break on whitespace
    sed  's/tls_hostname=.*/tls_hostname='"$a"'/g' $i > "${1}_copy"
    rm -rf $i
    mv "${1}_copy" $i
done
rm -rf $path $root_path
sh ./resources-add.sh
