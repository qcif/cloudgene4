#!/bin/bash

# Script to manage Celery workers for Cloudgene
cd "$(dirname "$0")"

case "$1" in
    start)
        echo "Starting Celery worker..."
        source venv/bin/activate && celery -A cloudgene_django worker --loglevel=info --detach
        echo "Celery worker started in background"
        ;;
    stop)
        echo "Stopping Celery workers..."
        pkill -f "celery.*cloudgene_django"
        echo "Celery workers stopped"
        ;;
    restart)
        echo "Restarting Celery workers..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        echo "Checking Celery worker status..."
        ps aux | grep -v grep | grep "celery.*cloudgene_django" || echo "No Celery workers running"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac