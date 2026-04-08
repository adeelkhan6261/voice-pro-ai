# Use Python 3.12 as the base
FROM python:3.12-slim

# Install system dependencies (FFmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p outputs static/audio/temp && chmod 777 outputs static/audio/temp

# Set Hugging Face port (7860) as internal environment variable if needed
ENV PORT=7860

# Command to run the application using Gunicorn for production-ready serving
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--timeout", "600", "main:app"]
