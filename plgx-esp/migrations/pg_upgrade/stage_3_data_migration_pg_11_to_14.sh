#!/bin/bash
echo "Stage 3"
echo "Data migration from PG 11 to PG 14 started at" $(date)
echo "======================================================"

echo "Migrating Data"
su -c "cd /usr/lib/postgresql/14/bin; ./pg_upgrade -b /usr/lib/postgresql/11/bin/ -d /var/lib/postgresql/11/_data/ -B /usr/lib/postgresql/14/bin/ -D /var/lib/postgresql/14/_data/ -U polylogyx" postgres


echo "changing the pg_hba.conf"
sed -i 's/scram-sha-256/md5/g' /var/lib/postgresql/14/_data/pg_hba.conf

echo "Starting the postgres 14"
su -c "cd /usr/lib/postgresql/14/bin; ./pg_ctl -D /var/lib/postgresql/14/_data start" postgres

echo "Vaccuming DB"
su -c "cd /usr/lib/postgresql/14/bin; /usr/lib/postgresql/14/bin/vacuumdb -U polylogyx --all --analyze-in-stages" postgres

echo "Stop the postgres 14"
su -c "cd /usr/lib/postgresql/14/bin; ./pg_ctl -D /var/lib/postgresql/14/_data stop" postgres