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
exec `tmux new-session -d -s plgx_celery`

CORES="$(nproc --all)"
echo "CPU cores are $CORES"
multiplier=1
if [[ $CORES -lt 4 ]]; then
    WORKERS_CELERY=1
    CONCURRENCY=$(echo $multiplier*$CORES | bc -l)
elif [[ $CORES -gt 32 ]]; then
    WORKERS_CELERY=$((CORES/4))
    CONCURRENCY=32
 else
     WORKERS_CELERY=$((CORES/4))
     CONCURRENCY=$(echo $multiplier*$CORES | bc -l)
fi
CONCURRENCY=${CONCURRENCY%.*}
echo "concurrency = $CONCURRENCY, workers = $WORKERS_CELERY"

SAVE_LOG_QUEUE=$(awk -F "=" '/save_log_queue/ {print $2}' common/config.ini)
MATCH_RULE_QUEUE=$(awk -F "=" '/match_rule_queue/ {print $2}' common/config.ini)
MATCH_IOC_QUEUE=$(awk -F "=" '/match_ioc_queue/ {print $2}' common/config.ini)
DISTRIBUTED_SETUP=$(awk -F "=" '/distributed_setup/ {print $2}' common/config.ini)

QUEUES=""
if [ "$RUN_TASKS" = true ]; then
    QUEUES="default_esp_queue"
fi
if [ "$SAVE_LOG" = true ] && [ -n "$SAVE_LOG_QUEUE" ]; then
    if [ "$QUEUES" = "" ]; then
        QUEUES="$SAVE_LOG_QUEUE"
    else
        QUEUES="$QUEUES"",""$SAVE_LOG_QUEUE"
    fi
fi
if [ "$MATCH_RULE" = true ] && [ -n "$MATCH_RULE_QUEUE" ]; then
    if [ "$QUEUES" = "" ]; then
        QUEUES="$MATCH_RULE_QUEUE"
    else
        QUEUES="$QUEUES"",""$MATCH_RULE_QUEUE"
    fi
fi
if [ "$MATCH_IOC" = true ] && [ -n "$MATCH_IOC_QUEUE" ]; then
    if [ "$QUEUES" = "" ]; then
        QUEUES="$MATCH_IOC_QUEUE"
    else
        QUEUES="$QUEUES"",""$MATCH_IOC_QUEUE"
    fi
fi

cd /src/plgx-esp
i=1
while [ "$i" -le $((WORKERS_CELERY)) ]; do
    if [ "$DISTRIBUTED_SETUP" = true ]; then
        exec `tmux send -t plgx_celery "celery -A polylogyx.celery.worker:celery worker --concurrency=$CONCURRENCY --prefetch-multiplier 1 -n er_$(hostname)_$i -Q $QUEUES --loglevel=INFO --logfile=/var/log/celery_$(hostname)_$i.log &" ENTER`
    else
        exec `tmux send -t plgx_celery "celery -A polylogyx.celery.worker:celery worker --concurrency=$CONCURRENCY --prefetch-multiplier 1 -n er_$(hostname)_$i --loglevel=INFO --logfile=/var/log/celery_$(hostname)_$i.log &" ENTER`
    fi
    i=$(( i + 1 ))
done
exec `tail -f /dev/null`
