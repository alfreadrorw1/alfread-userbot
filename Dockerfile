# Dockerfile untuk Alfread UserBot - Railway Ready
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 userbot && chown -R userbot:userbot /app
USER userbot

# Expose port (Railway akan mengatur PORT environment variable)
ENV PORT=8080
EXPOSE $PORT

# Health check untuk Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Command untuk menjalankan UserBot
CMD ["python", "alfread.py"]