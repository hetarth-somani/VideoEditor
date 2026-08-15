# 🚀 Celery Integration for Video Editor Pro

## Overview

This integration adds **background task processing** to your video editing application using **Celery** with **Redis** as the message broker. This allows for:

- ⚡ **Non-blocking video processing** - Users can continue using the app while videos process
- 📊 **Real-time progress tracking** - Live updates on processing status
- 🔄 **Task queuing** - Handle multiple video processing requests efficiently
- 💪 **Scalability** - Add more workers to handle increased load
- 🛡️ **Reliability** - Failed tasks can be retried automatically

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Web     │    │   Redis Broker  │    │ Celery Workers  │
│   Application   │◄──►│   (Message      │◄──►│ (Video          │
│                 │    │    Queue)       │    │  Processing)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                                              │
         │                                              │
         ▼                                              ▼
┌─────────────────┐                          ┌─────────────────┐
│   Web Browser   │                          │   FFmpeg        │
│   (Progress     │                          │   Processing    │
│    Updates)     │                          │                 │
└─────────────────┘                          └─────────────────┘
```

## 📁 New Files Added

### Core Files
- `celery_worker.py` - Celery worker with video processing tasks
- `celery_integration.py` - Flask routes for async task management
- `celeryconfig.py` - Celery configuration
- `static/js/celery_tasks.js` - Frontend JavaScript for task management

### Deployment Files
- `docker-compose.yml` - Docker setup with Redis and Celery
- `Dockerfile` - Container configuration
- `start_celery.sh` - Linux/Mac startup script
- `start_celery.bat` - Windows startup script

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Manual Setup

1. **Install Redis:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   
   # Windows
   # Download from https://redis.io/download
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start services:**
   ```bash
   # Terminal 1: Start Redis
   redis-server
   
   # Terminal 2: Start Celery Worker
   celery -A celery_worker worker --loglevel=info
   
   # Terminal 3: Start Celery Beat (for scheduled tasks)
   celery -A celery_worker beat --loglevel=info
   
   # Terminal 4: Start Flask App
   python app.py
   ```

## 🎯 Available Background Tasks

### Video Processing Tasks
- `process_video_trim` - Trim videos asynchronously
- `process_video_resize` - Resize videos in background
- `process_video_merge` - Merge multiple videos
- `process_video_effects` - Apply effects (blur, sharpen, etc.)
- `process_youtube_merge` - Download and merge YouTube videos

### Maintenance Tasks
- `cleanup_old_files` - Automatically clean up old files (runs hourly)

## 🌐 API Endpoints

### Task Submission
- `POST /api/process-video-async` - Submit video processing task
- `POST /api/merge-videos-async` - Submit video merge task
- `POST /api/youtube-merge-async` - Submit YouTube merge task

### Task Management
- `GET /api/task-status/<task_id>` - Get task progress
- `POST /api/cancel-task/<task_id>` - Cancel running task
- `GET /api/queue-status` - Get queue information

## 💻 Frontend Integration

### JavaScript Usage

```javascript
// Submit a video processing task
const formData = new FormData();
formData.append('file', videoFile);
formData.append('operation', 'trim');
formData.append('start_time', '10');
formData.append('end_time', '30');

taskManager.submitVideoTask(formData, 'trim')
    .then(result => {
        console.log('Task submitted:', result.task_id);
    });

// Track progress automatically
// Progress updates appear in the UI automatically
```

### HTML Integration

```html
<!-- Add to your template -->
<div id="task-progress" class="task-progress-container"></div>
<div id="notifications" class="notifications-container"></div>

<!-- Include the JavaScript -->
<script src="/static/js/celery_tasks.js"></script>
```

## 📊 Monitoring

### Flower Web UI
Access Celery monitoring at: `http://localhost:5555`

- View active tasks
- Monitor worker status
- See task history
- Performance metrics

### Redis CLI
```bash
# Connect to Redis
redis-cli

# View queues
KEYS *

# Monitor commands
MONITOR
```

## ⚙️ Configuration

### Environment Variables
```bash
REDIS_URL=redis://localhost:6379/0  # Redis connection
FLASK_ENV=production                # Flask environment
```

### Celery Settings
Edit `celeryconfig.py` to customize:
- Task timeouts
- Queue routing
- Worker settings
- Beat schedule

## 🔧 Customization

### Adding New Tasks

1. **Add task to `celery_worker.py`:**
```python
@celery.task(bind=True)
def my_custom_task(self, input_data):
    self.update_state(state='PROGRESS', meta={'current': 50, 'total': 100})
    # Your processing logic here
    return {'status': 'SUCCESS', 'result': 'Done!'}
```

2. **Add route to `celery_integration.py`:**
```python
@app.route('/api/my-custom-task', methods=['POST'])
def submit_custom_task():
    task = my_custom_task.delay(request.json)
    return jsonify({'task_id': task.id})
```

3. **Add frontend function:**
```javascript
function submitCustomTask(data) {
    return taskManager.submitCustomTask(data);
}
```

## 🚀 Production Deployment

### Render.com with Redis Add-on
```yaml
# render.yaml
services:
  - type: web
    name: video-editor-web
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    
  - type: worker
    name: video-editor-worker
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A celery_worker worker
```

### Scaling Workers
```bash
# Add more workers for heavy load
celery -A celery_worker worker --concurrency=4 --queues=video_processing
```

## 🛠️ Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Check Redis is running
   redis-cli ping
   # Should return: PONG
   ```

2. **Tasks Stuck in PENDING**
   ```bash
   # Restart Celery worker
   celery -A celery_worker worker --loglevel=debug
   ```

3. **High Memory Usage**
   ```bash
   # Reduce worker concurrency
   celery -A celery_worker worker --concurrency=1
   ```

### Logs
```bash
# Celery worker logs
celery -A celery_worker worker --loglevel=debug

# Redis logs
redis-cli monitor

# Flask logs
python app.py
```

## 📈 Performance Tips

1. **Optimize FFmpeg commands** - Use hardware acceleration when available
2. **Adjust worker concurrency** - Match your CPU cores
3. **Use SSD storage** - Faster I/O for video files
4. **Monitor memory usage** - Video processing is memory-intensive
5. **Set appropriate timeouts** - Prevent stuck tasks

## 🔐 Security Considerations

1. **Redis Security** - Use password authentication in production
2. **Task Validation** - Validate all input parameters
3. **File Permissions** - Restrict access to upload/output directories
4. **Rate Limiting** - Prevent task queue flooding

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

🎉 **Your video editing application now supports background processing!** Users can submit tasks and continue using the app while videos process in the background with real-time progress updates.