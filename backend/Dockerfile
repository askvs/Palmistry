
FROM python:3.11-slim

WORKDIR /app

# Install system libraries required by MediaPipe and OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application configuration and code
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app

# Copy project data and MediaPipe model
COPY data /data
COPY models /models

# Run the application as a non-root user
RUN useradd --create-home appuser && \
    chown -R appuser:appuser /app /data /models

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=5)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
