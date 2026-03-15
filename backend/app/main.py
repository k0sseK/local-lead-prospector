import csv
import hashlib
import hmac
import io
import logging
import math
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
import resend
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import List

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from . import models, schemas, database
from .dependencies import get_current_user
from .routers import auth as auth_router
from .routers import settings as settings_router
from .routers import ai as ai_router
from .routers import contact as contact_router
from .quota_service import check_quota, increment_usage, get_quota_info

logger = logging.getLogger(__name__)

app = FastAPI(title="B2B Lead Generator API")

# Configure CORS
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost,http://localhost:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(settings_router.router)
app.include_router(ai_router.router)
app.include_router(contact_router.router)

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.get("/health", tags=["meta"])
def health_check():
    """Liveness probe used by CI and Railway health checks."""
    return {"status": "ok"}


# 1×1 transparent GIF (43 bytes)
_TRACKING_GIF = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
    b"\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00"
    b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
    b"\x44\x01\x00\x3b"
)


@app.get("/api/t/{event_id}.gif", include_in_schema=False)
def tracking_pixel(event_id: str, db: Session = Depends(database.get_db)):
    """Email open tracking pixel — no auth required (embedded in sent emails)."""
    event = db.query(models.EmailEvent).filter(models.EmailEvent.id == event_id).first()
    if event and event.opened_at is None:
        event.opened_at = datetime.now(timezone.utc)
        db.commit()
    from fastapi.responses import Response
    return Response(
        content=_TRACKING_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

# ─── Rate limiting (in-memory, per real client IP, 120 req/min) ──────────────
# NOTE: Railway (and most reverse-proxies) terminate TLS and forward the
# original client IP in the X-Forwarded-For header.  Using request.client.host
# alone would give the proxy's internal IP, effectively sharing one bucket
# across ALL users and causing false 429s for everyone simultaneously.
_ip_log: dict[str, list] = defaultdict(list)
_last_cleanup = time.time()
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))


def _get_client_ip(request: Request) -> str:
    """Return the real client IP, honouring X-Forwarded-For from Railway/Nginx."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # The header may contain a comma-separated list; the first entry is the
        # original client.  Strip whitespace to be safe.
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    global _last_cleanup
    ip = _get_client_ip(request)
    now = time.time()

    # Periodic cleanup every 5 minutes to avoid memory growth
    if now - _last_cleanup > 300:
        cutoff = now - 60
        for k in list(_ip_log.keys()):
            _ip_log[k] = [t for t in _ip_log[k] if t > cutoff]
            if not _ip_log[k]:
                del _ip_log[k]
        _last_cleanup = now

    _ip_log[ip] = [t for t in _ip_log[ip] if now - t < 60]
    if len(_ip_log[ip]) >= _RATE_LIMIT:
        logger.warning("Rate limit hit for IP %s (%d req/min)", ip, len(_ip_log[ip]))
        return JSONResponse(
            status_code=429,
            content={"detail": "Zbyt wiele żądań. Poczekaj chwilę i spróbuj ponownie."},
            headers={"Retry-After": "60"},
        )
    _ip_log[ip].append(now)
    return await call_next(request)
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/api/leads")
def read_leads(
    page: int = 1,
    page_size: int = 2000,
    search: str = "",
    sort_by: str = "newest",
    has_email: bool = False,
    has_phone: bool = False,
    has_website: bool = False,
    min_rating: float = 0,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Zwraca stronicę leadów z opcjonalnym filtrowaniem/sortowaniem.
    Domyślnie page_size=2000 (pobiera wszystko) dla wstecznej zgodności.
    """
    query = db.query(models.Lead).filter(models.Lead.user_id == current_user.id)

    if search:
        query = query.filter(
            or_(
                models.Lead.company_name.ilike(f"%{search}%"),
                models.Lead.address.ilike(f"%{search}%"),
            )
        )
    if has_email:
        query = query.filter(models.Lead.email.isnot(None), models.Lead.email != "")
    if has_phone:
        query = query.filter(models.Lead.phone.isnot(None), models.Lead.phone != "")
    if has_website:
        query = query.filter(models.Lead.website_uri.isnot(None), models.Lead.website_uri != "")
    if min_rating > 0:
        query = query.filter(models.Lead.rating >= min_rating)

    if sort_by == "rating":
        query = query.order_by(models.Lead.rating.desc())
    elif sort_by == "name":
        query = query.order_by(models.Lead.company_name.asc())
    elif sort_by == "score_asc":
        # Najgorsze strony najpierw (niski score = dużo problemów = najlepszy prospect)
        query = query.order_by(models.Lead.lead_score.asc().nullsfirst())
    elif sort_by == "score_desc":
        query = query.order_by(models.Lead.lead_score.desc().nullslast())
    else:
        query = query.order_by(models.Lead.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": max(1, math.ceil(total / page_size)),
    }


@app.patch("/api/leads/bulk-update-status", response_model=schemas.BulkOperationResult)
def bulk_update_lead_status(
    request: schemas.BulkStatusUpdateRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Masowa zmiana statusu leadów. Pojedyncza transakcja DB."""
    VALID_STATUSES = {"new", "to_contact", "contacted", "rejected", "closed"}
    if request.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Nieprawidłowy status. Dozwolone: {', '.join(VALID_STATUSES)}",
        )

    leads = (
        db.query(models.Lead)
        .filter(
            models.Lead.id.in_(request.ids),
            models.Lead.user_id == current_user.id,
        )
        .all()
    )

    found_ids = {lead.id for lead in leads}
    not_found = [i for i in request.ids if i not in found_ids]

    for lead in leads:
        lead.status = request.status

    db.commit()
    return {"updated": len(leads), "not_found": not_found}


@app.delete("/api/leads/bulk-delete", status_code=200)
def bulk_delete_leads(
    request: schemas.BulkDeleteRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Masowe usuwanie leadów. Pojedyncza transakcja DB."""
    deleted = (
        db.query(models.Lead)
        .filter(
            models.Lead.id.in_(request.ids),
            models.Lead.user_id == current_user.id,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted}


@app.get("/api/leads/{lead_id}", response_model=schemas.Lead)
def get_lead(
    lead_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id)
        .first()
    )
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db_lead


@app.patch("/api/leads/{lead_id}", response_model=schemas.Lead)
def update_lead_status(
    lead_id: int,
    lead_update: schemas.LeadUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id)
        .first()
    )
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead_update.status is not None:
        db_lead.status = lead_update.status
    if lead_update.notes is not None:
        db_lead.notes = lead_update.notes
    db.commit()
    db.refresh(db_lead)
    return db_lead


@app.delete("/api/leads/{lead_id}", status_code=204)
def delete_lead(
    lead_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id)
        .first()
    )
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(db_lead)
    db.commit()


@app.get("/api/leads/{lead_id}/email-events", response_model=list[schemas.EmailEventOut])
def get_lead_email_events(
    lead_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Returns all email events (sent + open tracking) for a lead."""
    db_lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id)
        .first()
    )
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    events = (
        db.query(models.EmailEvent)
        .filter(
            models.EmailEvent.lead_id == lead_id,
            models.EmailEvent.user_id == current_user.id,
        )
        .order_by(models.EmailEvent.sent_at.desc())
        .all()
    )
    return events


@app.get("/api/leads/export/csv")
def export_leads_csv(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    leads = (
        db.query(models.Lead)
        .filter(models.Lead.user_id == current_user.id)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Firma", "Adres", "Telefon", "Email", "Strona WWW",
        "Ocena Google", "Liczba opinii", "SSL", "CMS", "Status", "Notatki", "Data dodania"
    ])
    for lead in leads:
        cms = lead.audit_report.get("raw_data", {}).get("cms", "") if lead.audit_report else ""
        writer.writerow([
            lead.id,
            lead.company_name,
            lead.address or "",
            lead.phone or "",
            lead.email or "",
            lead.website_uri or "",
            lead.rating or "",
            lead.reviews_count or "",
            "Tak" if lead.has_ssl else ("Nie" if lead.has_ssl is False else ""),
            cms,
            lead.status,
            lead.notes or "",
            lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@app.post("/api/scan")
async def scan_for_leads(
    scan_request: schemas.ScanRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not check_quota(db, current_user, "scans"):
        raise HTTPException(
            status_code=429,
            detail="Wyczerpałeś miesięczny limit skanów. Przejdź na plan Pro, aby kontynuować.",
        )

    # Walidacja klucza API przed dispatch — szybki fail jeśli brakuje klucza
    google_api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not google_api_key or google_api_key == "your_google_api_key_here":
        raise HTTPException(status_code=400, detail="Brak klucza GOOGLE_PLACES_API_KEY w konfiguracji.")

    increment_usage(db, current_user, "scans")

    from .tasks import scan_places_task
    task = scan_places_task.delay(
        user_id=current_user.id,
        keyword=scan_request.keyword,
        lat=scan_request.lat,
        lng=scan_request.lng,
        radius_km=scan_request.radius_km,
        limit=scan_request.limit,
        country_code=scan_request.country_code,
        filters={
            "website_filter": scan_request.website_filter,
            "min_rating": scan_request.min_rating,
            "max_rating": scan_request.max_rating,
            "min_reviews": scan_request.min_reviews,
            "max_reviews": scan_request.max_reviews,
        },
        auto_audit=scan_request.auto_audit,
    )
    return {"task_id": task.id, "status": "queued", "auto_audit": scan_request.auto_audit}


@app.post("/api/leads/{lead_id}/audit")
async def audit_lead_endpoint(
    lead_id: int,
    audit_request: schemas.AuditRequest = schemas.AuditRequest(),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not check_quota(db, current_user, "ai_audits"):
        raise HTTPException(
            status_code=429,
            detail="Wyczerpałeś miesięczny limit audytów AI. Przejdź na plan Pro, aby kontynuować.",
        )

    db_lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id)
        .first()
    )
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    increment_usage(db, current_user, "ai_audits", tokens_in=900, tokens_out=500, lead_id=lead_id)

    from .tasks import audit_lead_task
    task = audit_lead_task.delay(
        lead_id=lead_id,
        user_id=current_user.id,
        template_id=audit_request.template_id,
        target_language=audit_request.target_language,
    )
    return {"task_id": task.id, "lead_id": lead_id, "status": "queued"}


@app.get("/api/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: models.User = Depends(get_current_user),
):
    """Polling endpoint — zwraca status taska Celery."""
    from celery.result import AsyncResult
    from .celery_app import celery_app as _celery

    result = AsyncResult(task_id, app=_celery)
    status = result.status  # PENDING | STARTED | SUCCESS | FAILURE | RETRY

    payload: dict = {"task_id": task_id, "status": status, "result": None}

    if result.ready():
        if result.successful():
            payload["result"] = result.result
        else:
            # result.result zawiera wyjątek — serializujemy do stringa
            payload["result"] = {"error": str(result.result)}

    return payload


@app.post("/api/leads/{lead_id}/send-email")
async def send_email_endpoint(
    lead_id: int,
    request: schemas.EmailSendRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    import uuid as _uuid

    db_lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id)
        .first()
    )
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not db_lead.email:
        raise HTTPException(status_code=400, detail="Lead ma zły/brak adresu e-mail")

    if not check_quota(db, current_user, "emails_sent"):
        raise HTTPException(
            status_code=429,
            detail="Wyczerpałeś miesięczny limit wysyłki e-mail. Przejdź na plan Pro, aby kontynuować.",
        )

    user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    provider = user_settings.email_provider if user_settings and user_settings.email_provider else "none"

    if provider == "none":
        raise HTTPException(status_code=400, detail="Najpierw skonfiguruj dostawcę e-mail w zakładce Ustawienia.")

    # Build tracking pixel
    event_id = str(_uuid.uuid4())
    app_url = os.getenv("APP_URL", "http://localhost:8000")
    tracking_pixel = (
        f'<img src="{app_url}/api/t/{event_id}.gif" '
        f'width="1" height="1" style="display:block;width:1px;height:1px;opacity:0;" alt="" />'
    )

    try:
        html_body = request.body.replace('\n', '<br>') + tracking_pixel

        if provider == "resend":
            import resend

            api_key = user_settings.resend_api_key if user_settings else None
            from_email = user_settings.smtp_from_email if user_settings else None

            # W ostateczności fallback na globalne pliki, ale priorytet to ustawienia użytkownika
            resend.api_key = api_key or os.getenv("RESEND_API_KEY")
            real_from = from_email or os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

            if not resend.api_key:
                raise ValueError("Brak klucza API dla Resend.")

            resend.Emails.send({
                "from": real_from,
                "to": [db_lead.email],
                "subject": request.subject,
                "html": html_body,
            })

        elif provider == "smtp":
            import smtplib
            from email.message import EmailMessage

            if not user_settings or not all([user_settings.smtp_host, user_settings.smtp_port, user_settings.smtp_user, user_settings.smtp_password, user_settings.smtp_from_email]):
                raise ValueError("Brak pełnych danych konfiguracji SMTP w Ustawieniach.")

            msg = EmailMessage()
            msg['Subject'] = request.subject
            msg['From'] = user_settings.smtp_from_email
            msg['To'] = db_lead.email
            msg.set_content("Masz wyłączone wsparcie HTML. Wiadomość była nadana z włączonymi znacznikami.")
            msg.add_alternative(html_body, subtype='html')

            with smtplib.SMTP_SSL(user_settings.smtp_host, user_settings.smtp_port) as server:
                server.login(user_settings.smtp_user, user_settings.smtp_password)
                server.send_message(msg)

        else:
            raise ValueError(f"Nieobsługiwany dostawca: {provider}")

    except Exception as e:
        logger.error(f"Porażka przy wysyłce email na {db_lead.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd wysyłki: {str(e)}")

    # Record the email event for open tracking
    db.add(models.EmailEvent(
        id=event_id,
        user_id=current_user.id,
        lead_id=lead_id,
        sequence_step_id=None,
        sent_at=datetime.now(timezone.utc),
    ))
    db_lead.status = "contacted"
    db.commit()
    db.refresh(db_lead)
    increment_usage(db, current_user, "emails_sent", lead_id=lead_id)
    return {"message": "Email wysłany pomyślnie!", "lead": db_lead}


# ─── Email Sequences ─────────────────────────────────────────────────────────

@app.post("/api/leads/{lead_id}/sequences/generate-drafts")
async def generate_sequence_drafts_endpoint(
    lead_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generates 3 AI email drafts for a sequence (no DB write)."""
    from .ai_analyzer import generate_sequence_drafts

    db_lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id)
        .first()
    )
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    audit_report = db_lead.audit_report or {}
    initial_draft = audit_report.get("email_draft", "")
    selling_points = audit_report.get("selling_points", [])

    user_settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    target_language = (user_settings.default_email_language if user_settings else None) or "polskim"

    drafts = await generate_sequence_drafts(
        company_name=db_lead.company_name,
        initial_email_draft=initial_draft,
        selling_points=selling_points,
        user_settings=user_settings,
        target_language=target_language,
    )
    return {"drafts": drafts}


@app.post("/api/leads/{lead_id}/sequences", response_model=schemas.SequenceOut)
def create_sequence(
    lead_id: int,
    request: schemas.SequenceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Creates and activates a 3-step email sequence for a lead."""
    from datetime import timedelta

    if len(request.steps) != 3:
        raise HTTPException(status_code=400, detail="Sekwencja musi mieć dokładnie 3 kroki.")

    db_lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id)
        .first()
    )
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not db_lead.email:
        raise HTTPException(status_code=400, detail="Lead nie ma adresu e-mail — nie można uruchomić sekwencji.")

    # Cancel any existing active/paused sequence for this lead
    existing = (
        db.query(models.EmailSequence)
        .filter(
            models.EmailSequence.lead_id == lead_id,
            models.EmailSequence.user_id == current_user.id,
            models.EmailSequence.status.in_(["active", "paused"]),
        )
        .all()
    )
    for seq in existing:
        seq.status = "cancelled"

    now = datetime.now(timezone.utc)
    day_offsets = [0, 2, 6]  # day 1, day 3, day 7

    sequence = models.EmailSequence(
        lead_id=lead_id,
        user_id=current_user.id,
        status="active",
    )
    db.add(sequence)
    db.flush()  # get sequence.id

    steps = []
    for i, (step_data, offset) in enumerate(zip(request.steps, day_offsets), start=1):
        step = models.EmailSequenceStep(
            sequence_id=sequence.id,
            step_number=i,
            day_offset=offset,
            subject=step_data.subject,
            body=step_data.body,
            status="pending",
            scheduled_at=now + timedelta(days=offset),
        )
        db.add(step)
        steps.append(step)

    db.commit()
    db.refresh(sequence)
    for s in steps:
        db.refresh(s)

    return schemas.SequenceOut(
        id=sequence.id,
        lead_id=sequence.lead_id,
        user_id=sequence.user_id,
        status=sequence.status,
        created_at=sequence.created_at,
        company_name=db_lead.company_name,
        steps=[schemas.SequenceStepOut.model_validate(s) for s in steps],
    )


@app.get("/api/sequences")
def list_sequences(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Returns all sequences for the current user, with step details."""
    sequences = (
        db.query(models.EmailSequence)
        .filter(models.EmailSequence.user_id == current_user.id)
        .order_by(models.EmailSequence.created_at.desc())
        .all()
    )

    result = []
    for seq in sequences:
        lead = db.query(models.Lead).filter(models.Lead.id == seq.lead_id).first()
        steps = (
            db.query(models.EmailSequenceStep)
            .filter(models.EmailSequenceStep.sequence_id == seq.id)
            .order_by(models.EmailSequenceStep.step_number)
            .all()
        )
        # Enrich each step with open tracking data from EmailEvent
        step_outs = []
        for s in steps:
            event = (
                db.query(models.EmailEvent)
                .filter(models.EmailEvent.sequence_step_id == s.id)
                .first()
            )
            step_out = schemas.SequenceStepOut(
                id=s.id,
                step_number=s.step_number,
                day_offset=s.day_offset,
                subject=s.subject,
                body=s.body,
                status=s.status,
                scheduled_at=s.scheduled_at,
                sent_at=s.sent_at,
                opened_at=event.opened_at if event else None,
                email_event_id=event.id if event else None,
            )
            step_outs.append(step_out)
        result.append(schemas.SequenceOut(
            id=seq.id,
            lead_id=seq.lead_id,
            user_id=seq.user_id,
            status=seq.status,
            created_at=seq.created_at,
            company_name=lead.company_name if lead else None,
            steps=step_outs,
        ))
    return result


@app.patch("/api/sequences/{seq_id}")
def patch_sequence(
    seq_id: int,
    request: schemas.SequencePatchRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Pause, resume or cancel a sequence."""
    allowed = {"active", "paused", "cancelled"}
    if request.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Nieprawidłowy status. Dozwolone: {allowed}")

    seq = (
        db.query(models.EmailSequence)
        .filter(models.EmailSequence.id == seq_id, models.EmailSequence.user_id == current_user.id)
        .first()
    )
    if seq is None:
        raise HTTPException(status_code=404, detail="Sequence not found")
    if seq.status in ("completed", "cancelled") and request.status != "cancelled":
        raise HTTPException(status_code=400, detail="Nie można zmienić statusu zakończonej/anulowanej sekwencji.")

    seq.status = request.status
    db.commit()
    return {"id": seq.id, "status": seq.status}


@app.put("/api/sequences/{seq_id}/steps/{step_id}")
def update_sequence_step(
    seq_id: int,
    step_id: int,
    request: schemas.SequenceStepUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Edit a pending step's subject and body."""
    seq = (
        db.query(models.EmailSequence)
        .filter(models.EmailSequence.id == seq_id, models.EmailSequence.user_id == current_user.id)
        .first()
    )
    if seq is None:
        raise HTTPException(status_code=404, detail="Sequence not found")

    step = (
        db.query(models.EmailSequenceStep)
        .filter(models.EmailSequenceStep.id == step_id, models.EmailSequenceStep.sequence_id == seq_id)
        .first()
    )
    if step is None:
        raise HTTPException(status_code=404, detail="Step not found")
    if step.status != "pending":
        raise HTTPException(status_code=400, detail="Można edytować tylko kroki ze statusem 'pending'.")

    step.subject = request.subject
    step.body = request.body
    db.commit()
    db.refresh(step)
    return schemas.SequenceStepOut.model_validate(step)


# ─────────────────────────────────────────────────────────────────────────────


@app.get("/api/usage")
def get_usage(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Zwraca bieżące zużycie i limity zalogowanego użytkownika."""
    data = get_quota_info(db, current_user)
    # Append subscription metadata for the Account tab
    plan_expires_at = current_user.plan_expires_at
    data["subscription"] = {
        "renews_at": plan_expires_at.isoformat() + "Z" if plan_expires_at else None,
        "status": current_user.lemon_subscription_status,
    }
    return data


@app.post("/api/admin/set-plan")
def admin_set_plan(
    request: schemas.SetPlanRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Zmienia plan użytkownika (tylko dla roli admin)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień.")

    target_user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony.")

    valid_plans = {"free", "pro", "admin"}
    if request.plan not in valid_plans:
        raise HTTPException(status_code=422, detail=f"Nieprawidłowy plan. Dozwolone: {', '.join(valid_plans)}")

    target_user.plan = request.plan
    db.commit()
    logger.info("Admin %d set plan='%s' for user %d", current_user.id, request.plan, request.user_id)
    return {"message": f"Plan użytkownika {target_user.email} zmieniony na '{request.plan}'."}


_LS_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")
_LS_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "")
_LS_ACTIVE_STATUSES = {"active", "on_trial"}
_LS_INACTIVE_STATUSES = {"expired", "unpaid", "paused"}

@app.post("/api/webhooks/lemonsqueezy", include_in_schema=False)
async def lemonsqueezy_webhook(request: Request, db: Session = Depends(database.get_db)):
    raw_body = await request.body()

    # Verify HMAC-SHA256 signature
    if _LS_WEBHOOK_SECRET:
        sig = request.headers.get("X-Signature", "")
        expected = hmac.new(
            _LS_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, sig):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    import json
    try:
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = payload.get("meta", {}).get("event_name", "")
    custom_data = payload.get("meta", {}).get("custom_data", {})
    attrs = payload.get("data", {}).get("attributes", {})
    subscription_id = str(payload.get("data", {}).get("id", ""))
    status = attrs.get("status", "")
    customer_email = attrs.get("user_email", "")

    # Find user — prefer custom user_id, fall back to email
    user = None
    raw_uid = custom_data.get("user_id")
    if raw_uid:
        try:
            user = db.query(models.User).filter(models.User.id == int(raw_uid)).first()
        except (ValueError, TypeError):
            pass
    if not user and customer_email:
        user = db.query(models.User).filter(models.User.email == customer_email).first()

    if not user:
        logger.warning(
            "LemonSqueezy webhook: no matching user for event=%s email=%s uid=%s",
            event, customer_email, raw_uid,
        )
        return {"received": True}

    def _parse_ls_date(date_str):
        """Parse ISO date string from Lemon Squeezy into a naive UTC datetime."""
        if not date_str:
            return None
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            return None

    if event in ("subscription_created", "subscription_updated"):
        if status in _LS_ACTIVE_STATUSES:
            user.plan = "pro"
            user.lemon_subscription_id = subscription_id
            user.lemon_subscription_status = status
            user.plan_expires_at = _parse_ls_date(attrs.get("renews_at"))
            logger.info("LS webhook: user %d upgraded to pro (sub %s, renews_at=%s)", user.id, subscription_id, attrs.get("renews_at"))
        elif status == "cancelled":
            # Cancelled but still active until period ends — keep pro access
            user.lemon_subscription_id = subscription_id
            user.lemon_subscription_status = "cancelled"
            user.plan_expires_at = _parse_ls_date(attrs.get("ends_at"))
            logger.info("LS webhook: user %d subscription cancelled (sub %s, ends_at=%s)", user.id, subscription_id, attrs.get("ends_at"))
        elif status in _LS_INACTIVE_STATUSES:
            user.plan = "free"
            user.lemon_subscription_status = status
            logger.info(
                "LS webhook: user %d downgraded to free (sub %s, status=%s)",
                user.id, subscription_id, status,
            )
    elif event == "subscription_expired":
        user.plan = "free"
        user.lemon_subscription_id = None
        user.lemon_subscription_status = "expired"
        user.plan_expires_at = None
        logger.info("LS webhook: user %d subscription expired → free", user.id)

    db.commit()
    return {"received": True}


@app.post("/api/subscription/cancel")
def cancel_subscription(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Anuluje subskrypcję Lemon Squeezy zalogowanego użytkownika."""
    if current_user.plan != "pro" or not current_user.lemon_subscription_id:
        raise HTTPException(status_code=400, detail="Brak aktywnej subskrypcji do anulowania.")
    if current_user.lemon_subscription_status == "cancelled":
        raise HTTPException(status_code=400, detail="Subskrypcja jest już anulowana.")
    if not _LS_API_KEY:
        raise HTTPException(status_code=500, detail="Brak konfiguracji Lemon Squeezy API.")

    import httpx
    sub_id = current_user.lemon_subscription_id
    try:
        resp = httpx.delete(
            f"https://api.lemonsqueezy.com/v1/subscriptions/{sub_id}",
            headers={
                "Accept": "application/vnd.api+json",
                "Authorization": f"Bearer {_LS_API_KEY}",
            },
            timeout=15.0,
        )
    except httpx.RequestError as exc:
        logger.error("LS cancel subscription request error: %s", exc)
        raise HTTPException(status_code=502, detail="Błąd połączenia z Lemon Squeezy.")

    if resp.status_code not in (200, 202, 204):
        logger.error("LS cancel subscription failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Nie udało się anulować subskrypcji w Lemon Squeezy.")

    # Update local state — webhook will eventually confirm, but update optimistically
    current_user.lemon_subscription_status = "cancelled"
    db.commit()
    logger.info("User %d cancelled subscription %s", current_user.id, sub_id)
    return {"message": "Subskrypcja została anulowana. Dostęp Pro pozostaje aktywny do końca okresu rozliczeniowego."}


@app.get("/api/admin/stats")
def admin_get_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Zwraca zagregowane statystyki systemu (tylko admin)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień.")

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_users = db.query(models.User).count()
    pro_users = db.query(models.User).filter(models.User.plan == "pro").count()
    new_users_this_month = db.query(models.User).filter(models.User.created_at >= month_start).count()
    total_leads = db.query(models.Lead).count()

    # Sumuj z monthly_usage wszystkich użytkowników za bieżący miesiąc
    monthly_agg = db.query(
        func.coalesce(func.sum(models.MonthlyUsage.ai_audits), 0).label("ai_audits"),
        func.coalesce(func.sum(models.MonthlyUsage.scans), 0).label("scans"),
        func.coalesce(func.sum(models.MonthlyUsage.emails_sent), 0).label("emails_sent"),
        func.coalesce(func.sum(models.MonthlyUsage.cost_usd), 0).label("cost_usd"),
    ).filter(models.MonthlyUsage.month == month).first()

    return {
        "total_users": total_users,
        "pro_users": pro_users,
        "new_users_this_month": new_users_this_month,
        "total_leads": total_leads,
        "month": month,
        "ai_audits_this_month": int(monthly_agg.ai_audits) if monthly_agg else 0,
        "scans_this_month": int(monthly_agg.scans) if monthly_agg else 0,
        "emails_sent_this_month": int(monthly_agg.emails_sent) if monthly_agg else 0,
        "cost_usd_this_month": round(float(monthly_agg.cost_usd or 0), 4) if monthly_agg else 0.0,
    }


@app.get("/api/admin/users")
def admin_get_users(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Lista wszystkich użytkowników z bieżącym zużyciem (tylko admin)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Brak uprawnień.")

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()

    result = []
    for u in users:
        usage = (
            db.query(models.MonthlyUsage)
            .filter_by(user_id=u.id, month=month)
            .first()
        )
        leads_count = db.query(models.Lead).filter_by(user_id=u.id).count()
        result.append({
            "id": u.id,
            "email": u.email,
            "plan": u.plan or "free",
            "role": u.role,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "leads_count": leads_count,
            "usage": {
                "ai_audits": getattr(usage, "ai_audits", 0) or 0,
                "scans": getattr(usage, "scans", 0) or 0,
                "emails_sent": getattr(usage, "emails_sent", 0) or 0,
                "cost_usd": round(float(usage.cost_usd or 0), 4) if usage else 0.0,
            },
        })
    return result
