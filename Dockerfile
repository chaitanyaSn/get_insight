FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UVICORN_PORT=8000

WORKDIR /app

# System dependencies (git for GitLoader, build tools for scientific libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY app ./app

# Expose API port
EXPOSE 8000

# Default env placeholders (override in deployment)
ENV GOOGLE_API_KEY="" \
    CHROMA_API_KEY="" \
    CHROMA_TENANT="" \
    CHROMA_DATABASE=""

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

