FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create .env if not exists
RUN if [ ! -f .env ]; then \
    echo "Creating .env.example as .env" && \
    cp .env.example .env; \
    fi

# Run the bot
CMD ["python", "alfread.py"]