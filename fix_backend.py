import re
import os

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix resize:
content = re.sub(
    r"'-vf', f'scale=\{width\}:\{height\}',\s*'-c:v'",
    r"'-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',\n            '-c:v'",
    content
)

# 2. Fix auto-cut backslashes:
content = re.sub(
    r"f\.write\(f\"file '\{chunk_path\}'\\n\"\)",
    r"f.write(f\"file '{chunk_path.replace('\\\\', '/')}'\\n\")",
    content
)

# 3. Fix motion blur:
content = re.sub(
    r"tblend=all_mode=average,framestep=1,setpts=N/FRAME_RATE/TB",
    r"tmix=frames=3:weights=\"1 1 1\"",
    content
)

# 4. Fix color grading (Boost cinematic and others):
content = content.replace(
    "'eq=contrast=1.2:saturation=1.1:brightness=0.05'",
    "'eq=contrast=1.5:saturation=1.5:brightness=0.05'"
)

# 5. Fix download_youtube_clip
ytclip_fixed = """
        print(f"Debug - Downloading YouTube video ID: {video_id} using yt-dlp via subprocess")

        # Generate output filename
        output_filename = f'youtube_{video_id}_{int(time.time())}.mp4'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        url = f'https://www.youtube.com/watch?v={video_id}'
        command = [
            sys.executable, "-m", "yt_dlp",
            "-o", output_path,
            "--format", "best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--no-warnings",
            "--no-check-certificate",
            url
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and os.path.exists(output_path):
                download_success = True
            else:
                download_success = False
                last_error = result.stderr
        except Exception as e:
            download_success = False
            last_error = str(e)
            
"""
content = re.sub(
    r"print\(f\"Debug - Downloading YouTube video ID: \{video_id\} using yt-dlp\"\).*?if not download_success:",
    ytclip_fixed.strip() + "\n\n        if not download_success:",
    content,
    flags=re.DOTALL
)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Fixes applied.")
