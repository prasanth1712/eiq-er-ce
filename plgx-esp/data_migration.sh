#!/bin/bash
echo "Starting data migration script..."

echo "Waiting for PostgreSQL to start..."
export FLASK_APP=manage.py:app
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_ADDRESS -U $POSTGRES_USER -d $POSTGRES_DB_NAME -c "select 1" > /dev/null 2>&1 ; do
  sleep 5
done
exec `tmux new-session -d -s data_migration`

echo "Waiting untill vacuuming result_log_old"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_ADDRESS -U $POSTGRES_USER -d $POSTGRES_DB_NAME -c "VACUUM (VERBOSE, ANALYZE) result_log_old" ; do
  sleep 5
done
echo "Migrating data to Partitions and inserting ids int result_log_maps"
exec `tmux send -t data_migration 'flask add_partitions_existing_data' ENTER`



