# TorrentJanitor Docker Image
FROM python:3.11-alpine

# Metadata
LABEL maintainer="Giovanni Guarino"
LABEL description="TorrentJanitor - Automated qBittorrent Cleanup"
LABEL version="1.0.0"

# Install system dependencies
RUN apk add --no-cache \
    tzdata \
    curl \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1000 janitor && \
    adduser -D -u 1000 -G janitor janitor

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY torrentjanitor.py .
COPY config.example.json .

# Create directories for configs and data
RUN mkdir -p /config /data && \
    chown -R janitor:janitor /app /config /data

# Switch to non-root user
USER janitor

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    WORK_DIR=/data \
    CONFIG_FILE=/config/config.json

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD python torrentjanitor.py --once --dry-run || exit 1

# Volume for persistent data
VOLUME ["/config", "/data"]

# Default command
ENTRYPOINT ["python", "torrentjanitor.py"]
CMD ["--config", "/config/config.json"]