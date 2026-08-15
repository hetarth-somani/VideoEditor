#!/bin/bash
# Install FFmpeg on Render
set -e
apt-get update
apt-get install -y ffmpeg
echo "FFmpeg installation completed"