@echo off
REM Start Celery Worker and Beat Scheduler for Windows

echo Starting Redis server...
where redis-server >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start /B redis-server
    
    echo Starting Celery worker...
    start /B celery -A celery_worker worker --loglevel=info --concurrency=1 --queues=video_processing,maintenance
) else (
    echo WARNING: redis-server not found in PATH!
    echo Celery async background worker will NOT be started.
    echo The application will fall back to EAGER mode ^(synchronous video processing^).
    echo To enable fully async background tasks on Windows, please install Docker, WSL or Memurai ^(Redis for Windows^).
)

pause