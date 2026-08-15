#!/usr/bin/env python3
"""
Celery Integration Module
Provides Flask routes and utilities for background task processing
"""

from flask import jsonify, request
from celery_worker import celery, process_video_trim, process_video_resize, process_video_merge, process_video_effects, process_youtube_merge
import os
import time

def init_celery_routes(app):
    """Initialize Celery-related routes in Flask app"""
    
    @app.route('/api/process-video-async', methods=['POST'])
    def process_video_async():
        """Queue video processing task"""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file uploaded'})
            
            file = request.files['file']
            operation = request.form.get('operation', 'trim')
            
            if not file.filename:
                return jsonify({'success': False, 'error': 'No file selected'})
            
            # Save uploaded file
            timestamp = int(time.time())
            input_filename = f"{timestamp}_{file.filename}"
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
            file.save(input_path)
            
            # Generate output filename
            output_filename = f"{operation}_{timestamp}.mp4"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            # Queue appropriate task based on operation
            if operation == 'trim':
                start_time = request.form.get('start_time', '0')
                end_time = request.form.get('end_time', '10')
                task = process_video_trim.delay(input_path, output_path, start_time, end_time)
                
            elif operation == 'resize':
                width = request.form.get('width', '1280')
                height = request.form.get('height', '720')
                task = process_video_resize.delay(input_path, output_path, int(width), int(height))
                
            elif operation == 'effect':
                effect_type = request.form.get('effect_type', 'blur')
                intensity = float(request.form.get('intensity', '2.0'))
                task = process_video_effects.delay(input_path, output_path, effect_type, intensity=intensity)
                
            else:
                return jsonify({'success': False, 'error': f'Unknown operation: {operation}'})
            
            return jsonify({
                'success': True,
                'task_id': task.id,
                'message': f'{operation.title()} task queued successfully'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/merge-videos-async', methods=['POST'])
    def merge_videos_async():
        """Queue video merge task"""
        try:
            if 'files[]' not in request.files:
                return jsonify({'success': False, 'error': 'No files uploaded'})
            
            files = request.files.getlist('files[]')
            
            if len(files) < 2:
                return jsonify({'success': False, 'error': 'At least 2 videos required for merging'})
            
            # Save uploaded files
            timestamp = int(time.time())
            input_paths = []
            
            for i, file in enumerate(files):
                if file and file.filename:
                    input_filename = f"{timestamp}_{i}_{file.filename}"
                    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
                    file.save(input_path)
                    input_paths.append(input_path)
            
            # Generate output filename
            output_filename = f"merged_{timestamp}.mp4"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            # Queue merge task
            task = process_video_merge.delay(input_paths, output_path)
            
            return jsonify({
                'success': True,
                'task_id': task.id,
                'message': f'Merge task queued for {len(input_paths)} videos'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/youtube-merge-async', methods=['POST'])
    def youtube_merge_async():
        """Queue YouTube merge task"""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No video file provided'})
            
            video_file = request.files['file']
            video_id = request.form.get('video_id')
            
            if not video_id:
                return jsonify({'success': False, 'error': 'No YouTube video ID provided'})
            
            if not video_file.filename:
                return jsonify({'success': False, 'error': 'No file selected'})
            
            # Save uploaded file
            timestamp = int(time.time())
            user_video_filename = f"{timestamp}_{video_file.filename}"
            user_video_path = os.path.join(app.config['UPLOAD_FOLDER'], user_video_filename)
            video_file.save(user_video_path)
            
            # Generate output filename
            output_filename = f"youtube_merge_{timestamp}.mp4"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            # Queue YouTube merge task
            task = process_youtube_merge.delay(user_video_path, video_id, output_path)
            
            return jsonify({
                'success': True,
                'task_id': task.id,
                'message': 'YouTube merge task queued successfully'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/task-status/<task_id>')
    def task_status(task_id):
        """Get task status and progress"""
        try:
            task = celery.AsyncResult(task_id)
            
            if task.state == 'PENDING':
                response = {
                    'state': task.state,
                    'current': 0,
                    'total': 100,
                    'status': 'Task is waiting to be processed...'
                }
            elif task.state == 'PROGRESS':
                response = {
                    'state': task.state,
                    'current': task.info.get('current', 0),
                    'total': task.info.get('total', 100),
                    'status': task.info.get('status', 'Processing...')
                }
            elif task.state == 'SUCCESS':
                response = {
                    'state': task.state,
                    'current': 100,
                    'total': 100,
                    'status': 'Task completed successfully',
                    'result': task.info
                }
            else:  # FAILURE
                response = {
                    'state': task.state,
                    'current': 100,
                    'total': 100,
                    'status': 'Task failed',
                    'error': str(task.info)
                }
            
            return jsonify(response)
            
        except Exception as e:
            return jsonify({
                'state': 'FAILURE',
                'error': str(e)
            })
    
    @app.route('/api/cancel-task/<task_id>', methods=['POST'])
    def cancel_task(task_id):
        """Cancel a running task"""
        try:
            celery.control.revoke(task_id, terminate=True)
            return jsonify({
                'success': True,
                'message': f'Task {task_id} cancelled'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    
    @app.route('/api/queue-status')
    def queue_status():
        """Get queue status and active tasks"""
        try:
            # Get active tasks
            active_tasks = celery.control.inspect().active()
            
            # Get scheduled tasks
            scheduled_tasks = celery.control.inspect().scheduled()
            
            # Get reserved tasks
            reserved_tasks = celery.control.inspect().reserved()
            
            return jsonify({
                'active_tasks': active_tasks,
                'scheduled_tasks': scheduled_tasks,
                'reserved_tasks': reserved_tasks
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e)
            })

def get_task_progress(task_id):
    """Utility function to get task progress"""
    task = celery.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return {'state': 'PENDING', 'progress': 0, 'status': 'Waiting...'}
    elif task.state == 'PROGRESS':
        return {
            'state': 'PROGRESS',
            'progress': task.info.get('current', 0),
            'status': task.info.get('status', 'Processing...')
        }
    elif task.state == 'SUCCESS':
        return {
            'state': 'SUCCESS',
            'progress': 100,
            'status': 'Completed',
            'result': task.info
        }
    else:
        return {
            'state': 'FAILURE',
            'progress': 100,
            'status': 'Failed',
            'error': str(task.info)
        }

def is_task_ready(task_id):
    """Check if task is completed"""
    task = celery.AsyncResult(task_id)
    return task.ready()

def get_task_result(task_id):
    """Get task result if completed"""
    task = celery.AsyncResult(task_id)
    if task.ready():
        return task.result
    return None