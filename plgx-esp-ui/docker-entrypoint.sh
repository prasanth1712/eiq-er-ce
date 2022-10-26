#!/bin/bash

echo "Starting docker entry point script..."
cd /src/plgx-esp-ui

echo "Creating enroll file..."
exec `echo "$ENROLL_SECRET">resources/secret.txt`

echo "Waiting for VASP to start..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_ADDRESS -U $POSTGRES_USER -d $POSTGRES_DB_NAME -c "select 1" > /dev/null 2>&1 ; do
  sleep 5
done

CORES="$(nproc --all)"
echo "CPU cores are $CORES"
WORKERS=$(( 2*CORES+1  ))

echo "Crating tmux sessions..."
exec `tmux new-session -d -s plgx`
exec `tmux new-session -d -s plgx_celery_beat`
exec `tmux new-session -d -s plgx_celery`

logdir="/var/log/er-ui"

if [ ! -d $logdir ] ; then
    mkdir -p $logdir
fi

TARGET=/usr/local/lib/python3.7/site-packages/celery/backends
cd $TARGET
if [ -e async.py ]
then
    mv async.py asynchronous.py
    sed -i 's/async/asynchronous/g' redis.py
    sed -i 's/async/asynchronous/g' rpc.py
fi

exec `tmux send -t plgx_celery 'flask set_log_level ' ENTER`
exec `tmux send -t plgx_celery 'flask add_existing_yara_filenames_to_json ' ENTER`

echo "Changing directory to plgx-esp-ui..."
cd /src/plgx-esp-ui

echo "Starting celery beat..."

exec `tmux send -t plgx_celery_beat 'celery -A polylogyx.worker:celery beat --schedule=/tmp/celerybeat-schedule --loglevel=INFO --logfile=/var/log/celery-beat.log --pidfile=/tmp/celerybeat.pid' ENTER`

echo "Starting EclecticIQ ER..."
exec `tmux send -t plgx "gunicorn -c gunicorn.py --capture-output manage:app --reload" ENTER`

echo "Starting celery workers..."
exec `tmux send -t plgx_celery "celery -A polylogyx.worker:celery worker --concurrency=8 --loglevel=INFO --logfile=/var/log/celery.log &" ENTER`

echo "UI Sever is up and running.."

exec `tail -f /dev/null`
