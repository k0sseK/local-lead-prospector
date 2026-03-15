"""
tasks.py

Celery tasks dla długich operacji (audyt AI, skan Google Places).
Taski są synchroniczne — async kod wywoływany przez asyncio.run().
Worker uruchamiany osobnym procesem (Railway service lub lokalnie).
"""
import asyncio
import logging

from .celery_app import celery_app  # sys.path naprawiony tam

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task: Audyt AI leada
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="tasks.audit_lead", max_retries=0)
def audit_lead_task(
    self,
    lead_id: int,
    user_id: int,
    template_id: int | None = None,
    target_language: str | None = None,
) -> dict:
    """
    Wykonuje pełny audyt leada (scrape strony + AI Gemini) w tle.
    Wywoływany asynchronicznie — HTTP request wraca natychmiast z task_id.
    """
    from .database import SessionLocal
    from . import models
    from .audit_service import run_full_audit

    db = SessionLocal()
    try:
        lead = (
            db.query(models.Lead)
            .filter(models.Lead.id == lead_id, models.Lead.user_id == user_id)
            .first()
        )
        if not lead:
            raise ValueError(f"Lead {lead_id} nie istnieje lub nie należy do usera {user_id}")

        logger.info("Starting audit task for lead %d (user %d)", lead_id, user_id)
        asyncio.run(run_full_audit(lead, db, template_id, target_language))
        logger.info("Audit task completed for lead %d", lead_id)

        return {"lead_id": lead_id}

    except Exception as exc:
        logger.error("Audit task failed for lead %d: %s", lead_id, exc, exc_info=True)
        raise  # Celery oznaczy task jako FAILURE

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task: Skan Google Places
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="tasks.scan_places", max_retries=0)
def scan_places_task(
    self,
    user_id: int,
    keyword: str,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int,
    country_code: str,
    filters: dict,
    auto_audit: bool = False,
) -> dict:
    """
    Skanuje Google Places API i zapisuje nowe leady do bazy w tle.
    Jeśli auto_audit=True, uruchamia audyt AI dla każdego nowego leada.
    HTTP request wraca natychmiast z task_id.
    """
    from .database import SessionLocal
    from scraper import scan_google_places

    db = SessionLocal()
    try:
        logger.info(
            "Starting scan task: user=%d keyword='%s' lat=%.4f lng=%.4f auto_audit=%s",
            user_id, keyword, lat, lng, auto_audit,
        )
        new_lead_ids = asyncio.run(
            scan_google_places(
                keyword=keyword,
                lat=lat,
                lng=lng,
                radius_km=radius_km,
                limit=limit,
                db=db,
                user_id=user_id,
                filters=filters,
                country_code=country_code,
            )
        )
        new_count = len(new_lead_ids)
        logger.info("Scan task completed: %d new leads for user %d", new_count, user_id)

        if auto_audit and new_lead_ids:
            logger.info(
                "Auto-audit enabled: queuing %d audit tasks for user %d",
                len(new_lead_ids), user_id,
            )
            for lead_id in new_lead_ids:
                audit_lead_task.delay(lead_id=lead_id, user_id=user_id)

        return {"new_leads": new_count, "auto_audit": auto_audit, "audited_ids": new_lead_ids if auto_audit else []}

    except Exception as exc:
        logger.error("Scan task failed for user %d: %s", user_id, exc, exc_info=True)
        raise

    finally:
        db.close()
