FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
# Build context = backend/ (Railway uses service root as Docker build context)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE 8000

CMD sh -c "python migrate.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
