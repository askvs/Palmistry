# Build from the repository root: docker build -f backend/Dockerfile .
# The app resolves its data/ and models/ directories relative to the
# repository root (parents[4] of the service modules), so both are copied
# to the matching absolute paths inside the image.
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /code
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libegl1 && rm -rf /var/lib/apt/lists/*COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY data /data
COPY models /models
RUN useradd -m appuser && mkdir -p /code/uploads && chown -R appuser:appuser /code
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').getcode()==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
