### Multi-stage Dockerfile for act-dashboard (FastAPI)
### Optimized for build caching and smaller final image

FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Remove build dependencies to shrink image
RUN apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/* /root/.cache

# Create a non-root user
RUN useradd --create-home --uid 1000 appuser || true
RUN chown -R appuser:appuser /app

USER appuser
WORKDIR /app

EXPOSE 8000

# Production command: use uvicorn with multiple workers
# If you prefer to run with reload (dev), override the command in docker-compose
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
