import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Provide a clean `download_youtube`
new_download_youtube = """def download_youtube():
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        if request.is_json:
            data = request.get_json()
            url = data.get("url")
        else:
            url = request.form.get("url")

        if not url: return jsonify({'success': False, 'error': 'Missing YouTube URL'}), 400

        downloads_dir = os.path.join(app.config['OUTPUT_FOLDER'], 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        timestamp = int(import_time.time()) if 'import_time' not in globals() else int(time.time())
        output_filename = f'youtube_download_{timestamp}.%(ext)s'
        output_path = os.path.join(downloads_dir, output_filename)

        import sys, subprocess
        command = [sys.executable, '-m', 'yt_dlp', '-o', output_path, '--format', 'best[ext=mp4]/best', '--merge-output-format', 'mp4', '--no-warnings', '--no-playlist', '--no-check-certificate', url]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return jsonify({'success': False, 'error': f'yt-dlp failed: {result.stderr}'}), 500

        # Find the actual downloaded file since %(ext)s was used
        import os
        downloaded_files = [f for f in os.listdir(downloads_dir) if f.startswith(f'youtube_download_{timestamp}')]
        if not downloaded_files:
            return jsonify({'success': False, 'error': 'Video downloaded but file not found'}), 500
            
        actual_filename = downloaded_files[0]
        actual_path = os.path.join(downloads_dir, actual_filename)
        file_size = os.path.getsize(actual_path)
        
        return jsonify({
            'success': True,
            'message': 'Video downloaded successfully!',
            'filename': actual_filename,
            'file_size': file_size,
            'download_path': f'/downloads/{actual_filename}',
            'output': 'Success'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
"""
text = re.sub(r'def download_youtube\(\):.*?@app\.route\(\'/downloads/', new_download_youtube + '\n@app.route(\'/downloads/', text, flags=re.DOTALL)

# 2. Provide a clean `download_youtube_clip`
new_download_youtube_clip = """def download_youtube_clip():
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data or 'video_id' not in data:
            return jsonify({'success': False, 'error': 'No video ID provided'})

        video_id = data['video_id']
        output_filename = f'youtube_{video_id}_{int(time.time())}.mp4'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        url = f'https://www.youtube.com/watch?v={video_id}'

        import sys, subprocess
        command = [sys.executable, '-m', 'yt_dlp', '-o', output_path, '--format', 'best[ext=mp4]/best', '--merge-output-format', 'mp4', '--no-warnings', '--no-check-certificate', url]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode != 0 or not os.path.exists(output_path):
            return jsonify({'success': False, 'error': f'Failed to download video.'})

        try:
            browser_path = os.path.join(app.config['OUTPUT_FOLDER'], f'browser_{output_filename}')
            cmd = ['ffmpeg', '-y', '-i', output_path, '-c:v', 'libx264', '-preset', 'fast', '-crf', '26', '-c:a', 'aac', browser_path]
            succ, msg = run_ffmpeg_command(cmd)
            if succ and os.path.exists(browser_path):
                os.remove(output_path)
                os.rename(browser_path, output_path)
        except Exception:
            pass

        return jsonify({'success': True, 'filename': output_filename, 'url': f'/output/{output_filename}'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
"""
text = re.sub(r'def download_youtube_clip\(\):.*?@app\.route\(\'/add-youtube-to-video\'', new_download_youtube_clip + '\n@app.route(\'/add-youtube-to-video\'', text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f: f.write(text)
