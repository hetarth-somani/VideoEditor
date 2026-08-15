#!/bin/bash
# Start Celery Worker and Beat Scheduler

echo "Starting Redis server..."
# Start Redis (adjust path as needed)
redis-server --daemonize yes

echo "Starting Celery worker..."
celery -A celery_worker worker --loglevel=info --concurrency=1 --queues=video_processing,maintenance &

# Keep script running
wait