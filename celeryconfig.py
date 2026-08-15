#!/usr/bin/env python3
"""
Celery Configuration
"""

import os

# Broker settings
broker_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Check if Redis is available, otherwise use eager mode (synchronous)
try:
    import redis
    r = redis.from_url(broker_url)
    r.ping()
    task_always_eager = False
except Exception:
    import logging as _logger
    _logger.getLogger(__name__).warning("Redis not found or unreachable. Falling back to EAGER mode (synchronous tasks).")
    print("WARNING: Redis not found or unreachable. Falling back to EAGER mode (synchronous tasks).")
    task_always_eager = True

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task execution settings
task_track_started = True
task_time_limit = 30 * 60  # 30 minutes
task_soft_time_limit = 25 * 60  # 25 minutes
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 50

# Task routing
task_routes = {
    'celery_worker.process_video_trim': {'queue': 'video_processing'},
    'celery_worker.process_video_resize': {'queue': 'video_processing'},
    'celery_worker.process_video_merge': {'queue': 'video_processing'},
    'celery_worker.process_video_effects': {'queue': 'video_processing'},
    'celery_worker.process_youtube_merge': {'queue': 'video_processing'},
    'celery_worker.cleanup_old_files': {'queue': 'maintenance'},
}

# Beat schedule for periodic tasks
beat_schedule = {
    'cleanup-old-files': {
        'task': 'celery_worker.cleanup_old_files',
        'schedule': 3600.0,  # Run every hour
    },
}

# Result backend settings
result_expires = 3600  # Results expire after 1 hour

# Worker settings
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Security settings
worker_hijack_root_logger = False
worker_log_color = False