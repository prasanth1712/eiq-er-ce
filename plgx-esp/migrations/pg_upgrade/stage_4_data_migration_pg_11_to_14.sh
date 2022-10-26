#!/bin/bash
echo "Stage 4"
echo "Data migration from PG 11 to PG 14 started at" $(date)
echo "======================================================"
newprojectName='pg-upgrade'
echo "Enter the old project dir"
read oldprojectDir
echo "Deleting the data in the existing volume"
rm -rf /var/lib/docker/volumes/plgx-esp_postgres-data/*

echo "Copying the migrated data"
cp -r /var/lib/postgresql/14/_data /var/lib/docker/volumes/plgx-esp_postgres-data/

echo "Starting the postgres 14"
chown -R systemd-coredump:systemd-coredump /var/lib/docker/volumes/plgx-esp_postgres-data/*

echo "clean up"
newPostgreContainerId=$(docker ps -a --filter ancestor=postgres:14.3-alpine3.16 --format {{.ID}})
newVolume=$(docker inspect --format='{{(index .Mounts 0).Name}}' $newPostgreContainerId)
echo "New postgres container:" $newPostgreContainerId " with volume: " $newVolume
echo "Cleaning the docker containers for the project " $newprojectName
$(cd $oldprojectDir ; docker-compose -f docker-compose-pg-upgrade.yml -p $newprojectName down)


echo "***********************************************"
echo "If any auth issues - check the pg_hba.conf in the old volume it should be authenticated with md5 instead of scram-sha-256"
echo "Remove the docker volume pg-upgrade_postgres-data-upgrade once db upgrade is verified"
echo "***********************************************"