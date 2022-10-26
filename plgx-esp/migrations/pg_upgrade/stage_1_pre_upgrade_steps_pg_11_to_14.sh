#!/bin/bash

echo "Pre upgrade steps for postgres from 11 to 14 started at" $(date)

echo "Updating base packages"
apt-get update
locale-gen en_US.UTF-8

echo "Installing postgres 11 on the host machine"
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
apt-get update
apt-get install postgresql-11

echo "Installing postgres 14 on the host machine"
apt-get install postgresql-14

echo "Changing ownership"
chown -R  postgres:postgres /usr/lib/postgresql/ 

echo "***********************************************"
echo "Follow the below steps before continuing to stage2"
echo "1. copy docker-compose-pg-upgrade.yml to the ER-3.5.1 project directory (To the same location where docker-compose file resides)"
echo "2. Run the command by going into the ER-3.5.1 project directory"
echo "docker-compose -f docker-compose-pg-upgrade.yml -p 'pg-upgrade' up --build -d"

echo "***********************************************"