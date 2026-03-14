"""
celery_app.py

Definicja instancji Celery.
Worker uruchamiany z katalogu backend/:
    celery -A app.celery_app worker --loglevel=info --concurrency=4
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

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
