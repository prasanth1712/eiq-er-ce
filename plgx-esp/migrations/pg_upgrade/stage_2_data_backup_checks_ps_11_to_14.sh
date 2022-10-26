#!/bin/bash
echo "Stage 2"
echo "Data migration from PG 11 to PG 14 started at" $(date)
echo "======================================================"

echo "Enter the old project dir"
read oldprojectDir
echo "Enter the old project name (by default kept as plgx-esp)"
read oldprojectName


echo "Project DIR: " $oldprojectDir
echo "Project Name: " $oldprojectName
newprojectName="pg-upgrade"

echo "Intializing"
pg11DataDir="/var/lib/postgresql/11/"
pg14DataDir="/var/lib/postgresql/14/"

echo "PG 11 data dir: " $pg11DataDir
echo "PG 14 data dir: " $pg14DataDir

echo "Checking for docker-compose file"
dockerComposeFile="docker-compose.yml"

dockerComposeFile="$oldprojectDir/$dockerComposeFile"
echo $dockerComposeFile
if [ ! -f $dockerComposeFile ] 
then
    echo "No docker compose file found"
    exit 0
fi

oldPostgreContainerId=$(docker ps -a --filter ancestor=postgres:11.14 --format {{.ID}})
oldVolume=$(docker inspect --format='{{(index .Mounts 0).Name}}' $oldPostgreContainerId)
echo "Old postgres container:" $oldPostgreContainerId " with volume: " $oldVolume
echo "Stopping the docker containers for the project " $oldprojectName


newPostgreContainerId=$(docker ps -a --filter ancestor=postgres:14.3-alpine3.16 --format {{.ID}})
newVolume=$(docker inspect --format='{{(index .Mounts 0).Name}}' $newPostgreContainerId)
echo "New postgres container:" $newPostgreContainerId " with volume: " $newVolume
echo "Stopping the docker containers for the project " $newprojectName

# 1. Stop all the containers
$(cd $oldprojectDir ; docker-compose -p $oldprojectName stop)
$(cd $oldprojectDir ; docker-compose -f docker-compose-pg-upgrade.yml -p $newprojectName stop)

# 2. Take backup / copy of current postgres volume
echo "Taking Backup of volume : " $oldVolume
mkdir -p $pg11DataDir
oldVolumedir=$(docker inspect --format="{{.Mountpoint}}" $oldVolume)
echo "Backing up from dir: "$oldVolumedir
cp -r  $oldVolumedir $pg11DataDir 

# 3. Take backup / copy of current postgres volume
echo "Taking Backup of volume : " $oldVolume
mkdir -p $pg14DataDir 
newVolumedir=$(docker inspect --format="{{.Mountpoint}}" $newVolume)
echo "Backing up from dir: "$newVolumedir
cp -r  $newVolumedir $pg14DataDir 



echo "Cluster compatibility check"
chown -R  postgres:postgres /usr/lib/postgresql/ 
chown -R  postgres:postgres /var/lib/postgresql/ 
chmod -R  750 /var/lib/postgresql/
chmod -R  750 /usr/lib/postgresql/

su -c "cd /usr/lib/postgresql/14/bin; ./pg_ctl -D /var/lib/postgresql/14/_data/ stop" postgres
su -c "cd /usr/lib/postgresql/11/bin; ./pg_ctl -D /var/lib/postgresql/11/_data/ stop" postgres
su -c "cd /usr/lib/postgresql/14/bin; ./pg_upgrade -b /usr/lib/postgresql/11/bin/ -d /var/lib/postgresql/11/_data/ -B /usr/lib/postgresql/14/bin/ -D /var/lib/postgresql/14/_data/ -U polylogyx -c" postgres
