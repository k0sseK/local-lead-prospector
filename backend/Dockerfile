FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
# Build context = repo root (Railway reads railway.toml from repo root)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY backend/ .

EXPOSE 8000

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
