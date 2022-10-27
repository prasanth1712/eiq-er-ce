#!/bin/bash
echo "Starting docker entry point script..."


echo "Waiting for PostgreSQL to start..."

until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_ADDRESS -U $POSTGRES_USER -d $POSTGRES_DB_NAME -c "select 1" > /dev/null 2>&1 ; do
  sleep 5
done


file="/tmp/celerybeat.pid"

if [ -f $file ] ; then
    rm $file
fi

logdir="/var/log/er"

if [ ! -d $logdir ] ; then
    mkdir -p $logdir
fi

cd /src/plgx-esp

echo "Creating enroll file..."
exec `echo "$ENROLL_SECRET">resources/secret.txt`

echo "Creating celery tmux sessions..."
exec `tmux new-session -d -s plgx_gunicorn`
exec `tmux new-session -d -s plgx_celery_beat`
exec `tmux new-session -d -s flower`
exec `tmux new-session -d -s plgx_celery`


CORES="$(nproc --all)"
echo "CPU cores are $CORES"
WORKERS=$(( 2*CORES+1  ))
WORKERS_CELERY=$(( 2*CORES  ))

make run/db_upgrade
make run/db_create_partitions

make run/db_roles
exec `tmux send -t plgx_celery "make run/db_initial_data_load" ENTER`
exec `tmux send -t plgx_celery "make run/add_threat_intel_keys" ENTER`
exec `tmux send -t plgx_celery "make run/db_load_settings" ENTER`

echo "Starting EclecticIQ ER..."
exec `tmux send -t plgx_gunicorn "gunicorn -c gunicorn.py --capture-output manage:app --reload" ENTER`

echo "Starting celery beat..."
exec `tmux send -t plgx_celery_beat 'celery -A polylogyx.celery.worker:celery beat --schedule=/tmp/celerybeat-schedule --loglevel=INFO --logfile=/var/log/celery-beat.log --pidfile=/tmp/celerybeat.pid' ENTER`

echo "Sever is up and running.."
exec `tmux send -t flower "celery -A polylogyx.celery.worker:celery flower --address=0.0.0.0  --broker_api=http://guest:guest@$RABBITMQ_URL:5672/api --basic_auth=$POLYLOGYX_USER:$POLYLOGYX_PASSWORD" ENTER`

exec `tail -f /dev/null`
