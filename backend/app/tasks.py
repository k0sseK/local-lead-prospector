"""
tasks.py

Celery tasks dla długich operacji (audyt AI, skan Google Places, sekwencje email).
Taski są synchroniczne — async kod wywoływany przez asyncio.run().
Worker uruchamiany osobnym procesem (Railway service lub lokalnie).
"""
import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

from .celery_app import celery_app  # sys.path naprawiony tam

logger = logging.getLogger(__name__)


def _send_email_via_settings(
    user_settings,
    to_email: str,
    subject: str,
    body: str,
    tracking_pixel_html: str = "",
):
    """Sends an email using the user's configured provider (resend or smtp).

    tracking_pixel_html is appended to the HTML body when provided.
    """
    provider = user_settings.email_provider if user_settings else "none"
    html_body = body.replace('\n', '<br>') + tracking_pixel_html

    if provider == "resend":
        import resend as resend_lib
        api_key = user_settings.resend_api_key if user_settings else None
        from_email = user_settings.smtp_from_email if user_settings else None
        resend_lib.api_key = api_key or os.getenv("RESEND_API_KEY")
        real_from = from_email or os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        if not resend_lib.api_key:
            raise ValueError("Brak klucza API dla Resend.")
        resend_lib.Emails.send({"from": real_from, "to": [to_email], "subject": subject, "html": html_body})

    elif provider == "smtp":
        if not user_settings or not all([
            user_settings.smtp_host, user_settings.smtp_port,
            user_settings.smtp_user, user_settings.smtp_password,
            user_settings.smtp_from_email,
        ]):
            raise ValueError("Brak pełnych danych konfiguracji SMTP.")
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = user_settings.smtp_from_email
        msg['To'] = to_email
        msg.set_content("Masz wyłączone wsparcie HTML.")
        msg.add_alternative(html_body, subtype='html')
        with smtplib.SMTP_SSL(user_settings.smtp_host, user_settings.smtp_port) as server:
            server.login(user_settings.smtp_user, user_settings.smtp_password)
            server.send_message(msg)
    else:
        raise ValueError(f"Nie skonfigurowano dostawcy e-mail (provider='{provider}').")


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
    saved_search_id: int | None = None,
) -> dict:
    """
    Skanuje Google Places API i zapisuje nowe leady do bazy w tle.
    Jeśli auto_audit=True, uruchamia audyt AI dla każdego nowego leada.
    HTTP request wraca natychmiast z task_id.
    """
    from .database import SessionLocal
    from .scraper import scan_google_places

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

        # Update saved search stats if this task was triggered from one
        if saved_search_id is not None:
            from datetime import datetime, timezone
            from .database import SessionLocal as _SL
            from . import models as _m
            _db = _SL()
            try:
                saved = _db.query(_m.SavedSearch).filter(_m.SavedSearch.id == saved_search_id).first()
                if saved:
                    now = datetime.now(timezone.utc)
                    saved.last_run_at = now
                    saved.last_run_leads = new_count
                    # Compute next_run
                    if saved.schedule == "daily":
                        from datetime import timedelta
                        saved.next_run_at = now + timedelta(days=1)
                    elif saved.schedule == "weekly":
                        from datetime import timedelta
                        saved.next_run_at = now + timedelta(weeks=1)
                    elif saved.schedule == "monthly":
                        from datetime import timedelta
                        saved.next_run_at = now + timedelta(days=30)
                    else:
                        saved.next_run_at = None
                    _db.commit()
            finally:
                _db.close()

        return {"new_leads": new_count, "auto_audit": auto_audit, "audited_ids": new_lead_ids if auto_audit else []}

    except Exception as exc:
        logger.error("Scan task failed for user %d: %s", user_id, exc, exc_info=True)
        raise

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Periodic task: Send due email sequence steps
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.send_due_sequence_steps")
def send_due_sequence_steps() -> dict:
    """
    Periodic beat task (every 30 min): finds all pending sequence steps whose
    scheduled_at has passed and sends them using the user's email settings.
    Marks sequences as 'completed' when all steps are done.
    """
    import uuid as _uuid
    from datetime import datetime, timezone
    from .database import SessionLocal
    from . import models

    db = SessionLocal()
    sent_count = 0
    failed_count = 0
    app_url = os.getenv("APP_URL", "http://localhost:8000")

    try:
        now = datetime.now(timezone.utc)

        due_steps = (
            db.query(models.EmailSequenceStep)
            .join(models.EmailSequence, models.EmailSequenceStep.sequence_id == models.EmailSequence.id)
            .filter(
                models.EmailSequenceStep.status == "pending",
                models.EmailSequenceStep.scheduled_at <= now,
                models.EmailSequence.status == "active",
            )
            .order_by(models.EmailSequenceStep.sequence_id, models.EmailSequenceStep.step_number)
            .all()
        )

        logger.info("send_due_sequence_steps: found %d due steps", len(due_steps))

        for step in due_steps:
            seq = db.query(models.EmailSequence).filter(models.EmailSequence.id == step.sequence_id).first()
            if not seq or seq.status != "active":
                continue

            lead = db.query(models.Lead).filter(models.Lead.id == seq.lead_id).first()
            if not lead or not lead.email:
                step.status = "skipped"
                db.commit()
                continue

            user_settings = (
                db.query(models.UserSettings)
                .filter(models.UserSettings.user_id == seq.user_id)
                .first()
            )

            event_id = str(_uuid.uuid4())
            tracking_pixel = (
                f'<img src="{app_url}/api/t/{event_id}.gif" '
                f'width="1" height="1" style="display:block;width:1px;height:1px;opacity:0;" alt="" />'
            )

            try:
                _send_email_via_settings(
                    user_settings, lead.email, step.subject, step.body,
                    tracking_pixel_html=tracking_pixel,
                )
                step.status = "sent"
                step.sent_at = now
                lead.status = "contacted"
                db.add(models.EmailEvent(
                    id=event_id,
                    user_id=seq.user_id,
                    lead_id=seq.lead_id,
                    sequence_step_id=step.id,
                    sent_at=now,
                ))
                sent_count += 1
                logger.info(
                    "Sequence step sent: seq=%d step=%d lead=%d (%s)",
                    seq.id, step.step_number, lead.id, lead.email,
                )
            except Exception as e:
                step.status = "failed"
                failed_count += 1
                logger.error(
                    "Failed to send sequence step seq=%d step=%d: %s",
                    seq.id, step.step_number, e,
                )

            db.commit()

            # Check if the whole sequence is now finished
            all_steps = (
                db.query(models.EmailSequenceStep)
                .filter(models.EmailSequenceStep.sequence_id == seq.id)
                .all()
            )
            if all(s.status in ("sent", "failed", "skipped") for s in all_steps):
                seq.status = "completed"
                db.commit()
                logger.info("Sequence %d completed", seq.id)

        return {"sent": sent_count, "failed": failed_count}

    except Exception as exc:
        logger.error("send_due_sequence_steps crashed: %s", exc, exc_info=True)
        raise

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Periodic task: Run scheduled saved searches
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.run_scheduled_searches")
def run_scheduled_searches() -> dict:
    """
    Periodic beat task (every hour): finds all active saved searches whose
    next_run_at has passed and dispatches scan_places_task for each.
    """
    from datetime import datetime, timezone
    from .database import SessionLocal
    from . import models

    db = SessionLocal()
    dispatched = 0
    skipped = 0

    try:
        now = datetime.now(timezone.utc)

        due = (
            db.query(models.SavedSearch)
            .filter(
                models.SavedSearch.is_active == True,
                models.SavedSearch.next_run_at != None,
                models.SavedSearch.next_run_at <= now,
                models.SavedSearch.schedule != "manual",
            )
            .all()
        )

        logger.info("run_scheduled_searches: found %d due searches", len(due))

        for saved in due:
            filters = saved.filters or {}
            try:
                scan_places_task.delay(
                    user_id=saved.user_id,
                    keyword=saved.keyword,
                    lat=saved.lat,
                    lng=saved.lng,
                    radius_km=saved.radius_km,
                    limit=saved.limit,
                    country_code=saved.country_code,
                    filters=filters,
                    auto_audit=saved.auto_audit,
                    saved_search_id=saved.id,
                )
                dispatched += 1
                logger.info(
                    "Dispatched scheduled scan for saved_search=%d user=%d keyword='%s'",
                    saved.id, saved.user_id, saved.keyword,
                )
            except Exception as e:
                skipped += 1
                logger.error(
                    "Failed to dispatch scan for saved_search=%d: %s",
                    saved.id, e,
                )

        return {"dispatched": dispatched, "skipped": skipped}

    except Exception as exc:
        logger.error("run_scheduled_searches crashed: %s", exc, exc_info=True)
        raise

    finally:
        db.close()
