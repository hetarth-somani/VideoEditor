#!/usr/bin/env python3
"""
Celery Worker for Video Processing Tasks
Handles background video processing to keep Flask responsive
"""

from celery import Celery
import os
import subprocess
import time
from datetime import datetime
import json

# Import your Flask app if needed
# from app import app

# Configure Celery (broker and backend settings are in celeryconfig.py)
celery = Celery('video_processor')
celery.config_from_object('celeryconfig')

# Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

@celery.task(bind=True)
def process_video_trim(self, input_path, output_path, start_time, end_time):
    """Background task for video trimming"""
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Starting video trim...'})
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c', 'copy',
            output_path
        ]
        
        self.update_state(state='PROGRESS', meta={'current': 25, 'total': 100, 'status': 'Processing video...'})
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': 'Finalizing...'})
        
        # Verify output file
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Output file not created or empty")
        
        file_size = os.path.getsize(output_path)
        
        return {
            'status': 'SUCCESS',
            'output_file': os.path.basename(output_path),
            'file_size': file_size,
            'message': 'Video trimmed successfully'
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("Video processing timeout")
    except Exception as e:
        raise Exception(f"Video processing failed: {str(e)}")

@celery.task(bind=True)
def process_video_resize(self, input_path, output_path, width, height):
    """Background task for video resizing"""
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Starting video resize...'})
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', f'scale={width}:{height}',
            '-c:a', 'copy',
            output_path
        ]
        
        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Resizing video...'})
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': 'Finalizing...'})
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Output file not created or empty")
        
        file_size = os.path.getsize(output_path)
        
        return {
            'status': 'SUCCESS',
            'output_file': os.path.basename(output_path),
            'file_size': file_size,
            'message': f'Video resized to {width}x{height} successfully'
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("Video processing timeout")
    except Exception as e:
        raise Exception(f"Video processing failed: {str(e)}")

@celery.task(bind=True)
def process_video_merge(self, input_paths, output_path):
    """Background task for video merging"""
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Starting video merge...'})
        
        # Create concat file
        concat_file = output_path.replace('.mp4', '_concat.txt')
        
        with open(concat_file, 'w', encoding='utf-8') as f:
            for path in input_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
        
        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': 'Normalizing videos...'})
        
        # Normalize videos first for better compatibility
        normalized_paths = []
        for i, input_path in enumerate(input_paths):
            norm_path = output_path.replace('.mp4', f'_norm_{i}.mp4')
            
            cmd_norm = [
                'ffmpeg', '-y',
                '-i', input_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-r', '30',
                '-s', '1280x720',
                '-pix_fmt', 'yuv420p',
                '-crf', '23',
                '-preset', 'fast',
                norm_path
            ]
            
            result = subprocess.run(cmd_norm, capture_output=True, text=True, timeout=1800)
            if result.returncode != 0:
                raise Exception(f"Video normalization failed: {result.stderr}")
            
            normalized_paths.append(norm_path)
            
            progress = 20 + (i + 1) * 30 // len(input_paths)
            self.update_state(state='PROGRESS', meta={'current': progress, 'total': 100, 'status': f'Normalized video {i+1}/{len(input_paths)}'})
        
        # Update concat file with normalized videos
        with open(concat_file, 'w', encoding='utf-8') as f:
            for path in normalized_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
        
        self.update_state(state='PROGRESS', meta={'current': 60, 'total': 100, 'status': 'Merging videos...'})
        
        # Merge normalized videos
        cmd_merge = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd_merge, capture_output=True, text=True, timeout=1800)
        
        if result.returncode != 0:
            raise Exception(f"Video merge failed: {result.stderr}")
        
        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': 'Cleaning up...'})
        
        # Clean up temporary files
        for path in normalized_paths:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(concat_file):
            os.remove(concat_file)
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Output file not created or empty")
        
        file_size = os.path.getsize(output_path)
        
        return {
            'status': 'SUCCESS',
            'output_file': os.path.basename(output_path),
            'file_size': file_size,
            'message': f'Successfully merged {len(input_paths)} videos'
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("Video processing timeout")
    except Exception as e:
        raise Exception(f"Video processing failed: {str(e)}")

@celery.task(bind=True)
def process_youtube_merge(self, user_video_path, youtube_video_id, output_path):
    """Background task for YouTube video merging"""
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Downloading YouTube video...'})
        
        # Download YouTube video (simplified - you'd use your existing yt-dlp logic)
        youtube_path = output_path.replace('.mp4', '_youtube.mp4')
        
        # Your existing YouTube download logic here
        # ... (use the yt-dlp code from your app.py)
        
        self.update_state(state='PROGRESS', meta={'current': 40, 'total': 100, 'status': 'Merging with user video...'})
        
        # Use the merge function
        result = process_video_merge.apply_async(args=[[user_video_path, youtube_path], output_path])
        
        return result.get()
        
    except Exception as e:
        raise Exception(f"YouTube merge failed: {str(e)}")

@celery.task(bind=True)
def process_video_effects(self, input_path, output_path, effect_type, **kwargs):
    """Background task for applying video effects"""
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': f'Applying {effect_type} effect...'})
        
        # Build FFmpeg command based on effect type
        if effect_type == 'blur':
            filter_str = f"gblur=sigma={kwargs.get('intensity', 2)}"
        elif effect_type == 'sharpen':
            filter_str = f"unsharp=5:5:{kwargs.get('intensity', 1.0)}:5:5:0.0"
        elif effect_type == 'brightness':
            filter_str = f"eq=brightness={kwargs.get('value', 0.1)}"
        elif effect_type == 'contrast':
            filter_str = f"eq=contrast={kwargs.get('value', 1.2)}"
        else:
            raise Exception(f"Unknown effect type: {effect_type}")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', filter_str,
            '-c:a', 'copy',
            output_path
        ]
        
        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Processing effect...'})
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': 'Finalizing...'})
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Output file not created or empty")
        
        file_size = os.path.getsize(output_path)
        
        return {
            'status': 'SUCCESS',
            'output_file': os.path.basename(output_path),
            'file_size': file_size,
            'message': f'{effect_type.title()} effect applied successfully'
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("Video processing timeout")
    except Exception as e:
        raise Exception(f"Effect processing failed: {str(e)}")

# Task to clean up old files
@celery.task
def cleanup_old_files():
    """Clean up files older than 24 hours"""
    import time
    current_time = time.time()
    
    folders = ['uploads', 'output']
    cleaned_count = 0
    
    for folder in folders:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    # Remove files older than 24 hours
                    if os.path.getctime(file_path) < current_time - 86400:  # 24 hours
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            print(f"Failed to remove {file_path}: {e}")
    
    return f"Cleaned up {cleaned_count} old files"

if __name__ == '__main__':
    celery.start()