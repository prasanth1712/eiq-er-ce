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
exec `tmux new-session -d -s plgx_celery`

CORES="$(nproc --all)"
echo "CPU cores are $CORES"
multiplier=1.5
if [[ $CORES -lt 4 ]]; then
    WORKERS_CELERY=1
    CONCURRENCY=$(echo $multiplier*$CORES | bc -l)
elif [[ $CORES -gt 32 ]]; then
    WORKERS_CELERY=$((CORES/4))
    CONCURRENCY=50
 else
     WORKERS_CELERY=$((CORES/4))
     CONCURRENCY=$(echo $multiplier*$CORES | bc -l)
fi
CONCURRENCY=${CONCURRENCY%.*}
echo "concurrency = $CONCURRENCY, workers = $WORKERS_CELERY"
cd /src/plgx-esp
i=1
while [ "$i" -le $((WORKERS_CELERY)) ]; do
     exec `tmux send -t plgx_celery "celery worker -A polylogyx.celery.worker:celery --concurrency=$CONCURRENCY -n er_celery$i@esp --loglevel=INFO --logfile=/var/log/celery$i.log &" ENTER`
     i=$(( i + 1 ))
done
exec `tail -f /dev/null`