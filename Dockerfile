# Dockerfile untuk Bot Telegram dengan kemampuan Voice Chat
# Gunakan image Python resmi versi 3.9 sebagai base
FROM python:3.9-slim

# Set working directory di dalam container
WORKDIR /app

# Install dependensi sistem yang diperlukan
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt terlebih dahulu (untuk caching layer Docker)
COPY requirements.txt .

# Install dependensi Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi ke dalam container
COPY . .

# Buat user non-root untuk keamanan
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Jalankan bot dengan file utama alfread.py
CMD ["python", "alfread.py"]