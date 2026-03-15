"""
celery_app.py

Definicja instancji Celery.
Worker uruchamiany z katalogu backend/:
    celery -A app.celery_app worker --loglevel=info --concurrency=4
"""
import os
import sys
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Upewnij się że backend/ (katalog nad app/) jest w sys.path,
# żeby worker mógł zaimportować scraper.py (backend/scraper.py).
# Celery worker startuje jako: celery -A app.celery_app worker
# więc __file__ = /app/app/celery_app.py  →  parent parent = /app
_backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "llp",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,          # wyniki w Redis wygasają po 1h
    worker_prefetch_multiplier=1, # jeden task na raz per worker (długie operacje IO)
    task_acks_late=True,          # ACK po ukończeniu — bezpieczniejsze przy crashu workera
)
