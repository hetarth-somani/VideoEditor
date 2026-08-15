FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flower for monitoring
RUN pip install flower

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads output

# Set environment variables
ENV PYTHONPATH=/app
ENV REDIS_URL=redis://redis:6379/0

# Expose port
EXPOSE 5000

# Default command
CMD ["python", "app.py"]