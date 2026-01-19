FROM python:3.10-slim

# Install system dependencies
# ffmpeg is crucial for moviepy/video generation
# imagemagick might be needed for TextClip
# git for installing git dependencies if any
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    git \
    && rm -rf /var/lib/apt/lists/*

# Fix for ImageMagick policy (common issue with moviepy)
# Enable reading/writing of PDF/text if needed (though usually we just need text)
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml || true

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
# We assume the build context is the backend directory
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# Validation: Check if ffmpeg is installed
RUN ffmpeg -version

CMD ["python", "worker_main.py"]
