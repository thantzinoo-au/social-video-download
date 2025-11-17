FROM python:3.11-slim

LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="yt-dlp REST API with Secret Key Authentication and User Directories"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    ffmpeg \
    curl \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install yt-dlp
RUN wget -O /usr/local/bin/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp && \
    yt-dlp --version

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create downloads directory and set permissions
RUN mkdir -p /downloads && \
    chown -R appuser:appuser /app /downloads

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Environment variables with secure defaults
ENV API_SECRET_KEY="" \
    DOWNLOAD_DIR="/downloads" \
    HOST="0.0.0.0" \
    PORT="5000" \
    DEBUG="False" \
    MAX_FILE_SIZE="314572800" \
    YTDLP_TIMEOUT="300"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "api.py"]
