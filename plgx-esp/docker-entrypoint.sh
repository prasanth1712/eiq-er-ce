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

TARGET=/usr/local/lib/python3.7/site-packages/celery/backends
cd $TARGET
if [ -e async.py ]
then
    mv async.py asynchronous.py
    sed -i 's/async/asynchronous/g' redis.py
    sed -i 's/async/asynchronous/g' rpc.py
fi
CORES=1
if [[ "$OSTYPE" == "linux-gnu" ]]; then
        CORES="$(nproc --all)"
elif [[ "$OSTYPE" == "darwin"* ]]; then
        CORES="$(sysctl -n hw.ncpu)"
elif [[ "$OSTYPE" == "cygwin" ]]; then
		echo "Os is cygwin.."
        # POSIX compatibility layer and Linux environment emulation for Windows
elif [[ "$OSTYPE" == "msys" ]]; then
		echo "Os is msys.."
        # Lightweight shell and GNU utilities compiled for Windows (part of MinGW)
elif [[ "$OSTYPE" == "win32" ]]; then
		CORES=echo %NUMBER_OF_PROCESSORS%
        # I'm not sure this can happen.
elif [[ "$OSTYPE" == "freebsd"* ]]; then
        CORES="$(sysctl -n hw.ncpu)"
 else
		echo "Os is unknown.."
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


echo "Creating DB schema..."
python manage.py db upgrade

echo "Creating all basic roles..."
python manage.py create_all_roles

echo "Assigning admin role for all the existing users..."
python manage.py update_role_for_existing_users

echo "Creating default admin user..."
python manage.py add_admin_user

echo "Creating today's partition from backup"
python manage.py create_partition_from_old_data

echo "Creating buffer partitions "
python manage.py add_partition
exec `tmux send -t plgx_celery 'python manage.py delete_existing_unmapped_queries_filters' ENTER`

echo "Adding default filters..."
exec `tmux send -t plgx_celery 'python manage.py add_default_filters --filepath default_data/default_filters/default_filter_linux.conf --platform linux --name Default --is_default true' ENTER`
exec `tmux send -t plgx_celery 'python manage.py add_default_filters --filepath default_data/default_filters/default_filter_macos.conf --platform darwin --name Default --is_default true' ENTER`
exec `tmux send -t plgx_celery 'python manage.py add_default_filters --filepath default_data/default_filters/default_filter_windows.conf --platform windows --name Default --is_default true' ENTER`
exec `tmux send -t plgx_celery 'python manage.py add_default_filters --filepath default_data/default_filters/default_filter_windows_deep.conf --platform windows --name Deep' ENTER`

echo "Adding default queries..."
exec `tmux send -t plgx_celery 'python manage.py add_default_queries --filepath default_data/default_queries/default_queries_linux.conf --platform linux --name Default --is_default true' ENTER`
exec `tmux send -t plgx_celery 'python manage.py add_default_queries --filepath default_data/default_queries/default_queries_macos.conf --platform darwin --name Default --is_default true' ENTER`
exec `tmux send -t plgx_celery 'python manage.py add_default_queries --filepath default_data/default_queries/default_queries_windows.conf --platform windows --name Default --is_default true' ENTER`
exec `tmux send -t plgx_celery 'python manage.py add_default_queries --filepath default_data/default_queries/default_queries_windows_deep.conf --platform windows --name Deep' ENTER`

echo "Adding released version's agent information..."
exec `tmux send -t plgx_celery 'python manage.py add_release_versions --filepath default_data/platform_releases.conf' ENTER`

echo "updating query name from windows_events to windows_real_time_events for all the configs"
exec `tmux send -t plgx_celery 'python manage.py update_query_name_for_custom_config' ENTER`

echo "Adding default mitre rules..."
for entry in /src/plgx-esp/default_data/mitre-attack/*
do
  rulename=$(basename "$entry" .json)
  echo $rulename
  exec `tmux send -t plgx_celery 'python manage.py add_rules  --filepath '"$entry" ENTER`
done

for entry in /src/plgx-esp/default_data/default_rules/*
do
  rulename=$(basename "$entry" .json)
  echo $rulename
  exec `tmux send -t plgx_celery 'python manage.py add_rules  --filepath '"$entry" ENTER`
done

echo "Adding default query packs..."
for entry in /src/plgx-esp/default_data/packs/*
do
  packname=$(basename "$entry" .conf)
  echo $packname
  exec `tmux send -t plgx_celery 'python manage.py addpack ' $packname ' --filepath '"$entry" ENTER`
done

cd /src/plgx-esp
echo "Starting EclecticIQ ER..."
exec `tmux send -t plgx_gunicorn "gunicorn -c gunicorn.py --capture-output manage:app --reload" ENTER`

if [[ -z "$DATA_RETENTION_DAYS" ]]
then
  echo "DATA_RETENTION_DAYS value is not set, data will not be purged automatically!"
else
  echo "Creating platform settings..."
  exec `tmux send -t plgx_celery 'python manage.py update_settings --data_retention_days '"$DATA_RETENTION_DAYS" ENTER`
fi

exec `tmux send -t plgx_celery 'python manage.py set_log_level ' ENTER`


exec `tmux send -t plgx_celery 'python manage.py add_default_vt_av_engines --filepath default_data/Virustotal-avengines/default_VT_Av_engines.json' ENTER`

exec `tmux send -t plgx_celery 'python manage.py  update_vt_match_count --vt_min_match_count '"$VT_MIN_MATCH_COUNT" ENTER`

exec `tmux send -t plgx_celery 'python manage.py  update_vt_scan_retention_period --vt_scan_retention_period '"$VT_SCAN_RETENTION_PERIOD" ENTER`

echo "Updating OSQuery Schema from polylogyx/resources/osquery_schema.json ..."
exec `tmux send -t plgx_celery "python manage.py update_osquery_schema --file_path polylogyx/resources/osquery_schema.json " ENTER`

echo "Starting celery beat..."
exec `tmux send -t plgx_celery_beat 'celery beat -A polylogyx.celery.worker:celery --schedule=/tmp/celerybeat-schedule --loglevel=INFO --logfile=/var/log/celery-beat.log --pidfile=/tmp/celerybeat.pid' ENTER`

echo "Sever is up and running.."
exec `tmux send -t flower "flower -A polylogyx.celery.worker:celery --address=0.0.0.0  --broker_api=http://guest:guest@$RABBITMQ_URL:5672/api --basic_auth=$POLYLOGYX_USER:$POLYLOGYX_PASSWORD" ENTER`

exec `tail -f /dev/null`
