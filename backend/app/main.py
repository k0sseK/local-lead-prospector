import csv
import hashlib
import hmac
import io
import logging
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
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, database
from .dependencies import get_current_user
from .routers import auth as auth_router
from .routers import settings as settings_router
from .routers import ai as ai_router
from .quota_service import check_quota, increment_usage, get_quota_info

logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=database.engine)

def apply_migrations():
    from sqlalchemy import text
    user_settings_cols = [
        ("email_provider", "VARCHAR DEFAULT 'resend'"),
        ("resend_api_key", "VARCHAR"),
        ("smtp_host", "VARCHAR"),
        ("smtp_port", "INTEGER"),
        ("smtp_user", "VARCHAR"),
        ("smtp_password", "VARCHAR"),
        ("smtp_from_email", "VARCHAR"),
        ("default_email_language", "VARCHAR DEFAULT 'polskim'"),
    ]
    users_cols = [
        ("plan", "VARCHAR DEFAULT 'free'"),
        ("plan_expires_at", "TIMESTAMP"),
        ("lemon_subscription_id", "VARCHAR"),
    ]
    with database.engine.begin() as conn:
        for col_name, col_type in user_settings_cols:
            conn.execute(text(f"ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
            logger.info(f"Ensured column exists: user_settings.{col_name}")
        for col_name, col_type in users_cols:
            conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
            logger.info(f"Ensured column exists: users.{col_name}")
        # audit_templates — tworzone przez create_all, tu upewniamy się że tabela istnieje
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_templates (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                name VARCHAR NOT NULL,
                prompt TEXT NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        logger.info("Ensured table exists: audit_templates")

apply_migrations()

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


@app.get("/api/leads", response_model=List[schemas.Lead])
def read_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    leads = (
        db.query(models.Lead)
        .filter(models.Lead.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return leads


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

    from scraper import scan_google_places

    filters = {
        "website_filter": scan_request.website_filter,
        "min_rating": scan_request.min_rating,
        "max_rating": scan_request.max_rating,
        "min_reviews": scan_request.min_reviews,
        "max_reviews": scan_request.max_reviews,
    }

    try:
        new_leads_added = await scan_google_places(
            keyword=scan_request.keyword,
            lat=scan_request.lat,
            lng=scan_request.lng,
            radius_km=scan_request.radius_km,
            limit=scan_request.limit,
            db=db,
            user_id=current_user.id,
            filters=filters,
            country_code=scan_request.country_code,
        )
        increment_usage(db, current_user, "scans")
        return {"message": f"Scan completed. Added {new_leads_added} new leads."}
    except ValueError as e:
        # Nieprawidłowy klucz API lub błąd odpowiedzi Google
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        # Timeout, DNS failure — serwis Google niedostępny
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/leads/{lead_id}/audit", response_model=schemas.Lead)
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

    try:
        from .audit_service import run_full_audit
        result = await run_full_audit(db_lead, db, template_id=audit_request.template_id, target_language=audit_request.target_language)
        increment_usage(db, current_user, "ai_audits", tokens_in=900, tokens_out=500, lead_id=lead_id)
        return result
    except Exception as exc:
        logger.error("Audit endpoint failed for lead %d: %s", lead_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Audit failed. Sprawdź logi serwera.")


@app.post("/api/leads/{lead_id}/send-email")
async def send_email_endpoint(
    lead_id: int,
    request: schemas.EmailSendRequest,
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

    try:
        html_body = request.body.replace('\n', '<br>')
        
        if provider == "resend":
            import resend
            
            api_key = user_settings.resend_api_key if user_settings else None
            from_email = user_settings.smtp_from_email if user_settings else None
            
            # W ostateczności fallback na globalne pliki, ale priorytet to ustawienia użytkownika
            resend.api_key = api_key or os.getenv("RESEND_API_KEY")
            real_from = from_email or os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

            if not resend.api_key:
                raise ValueError("Brak klucza API dla Resend.")
            
            params = {
                "from": real_from,
                "to": [db_lead.email],
                "subject": request.subject,
                "html": html_body
            }
            resend.Emails.send(params)

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

    db_lead.status = "contacted"
    db.commit()
    db.refresh(db_lead)
    increment_usage(db, current_user, "emails_sent", lead_id=lead_id)
    return {"message": "Email wysłany pomyślnie!", "lead": db_lead}


@app.get("/api/usage")
def get_usage(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Zwraca bieżące zużycie i limity zalogowanego użytkownika."""
    return get_quota_info(db, current_user)


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
_LS_ACTIVE_STATUSES = {"active", "on_trial"}
_LS_INACTIVE_STATUSES = {"expired", "cancelled", "unpaid", "paused"}

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

    if event in ("subscription_created", "subscription_updated"):
        if status in _LS_ACTIVE_STATUSES:
            user.plan = "pro"
            user.lemon_subscription_id = subscription_id
            user.plan_expires_at = None
            logger.info("LS webhook: user %d upgraded to pro (sub %s)", user.id, subscription_id)
        elif status in _LS_INACTIVE_STATUSES:
            user.plan = "free"
            logger.info(
                "LS webhook: user %d downgraded to free (sub %s, status=%s)",
                user.id, subscription_id, status,
            )
    elif event == "subscription_expired":
        user.plan = "free"
        user.lemon_subscription_id = None
        logger.info("LS webhook: user %d subscription expired → free", user.id)

    db.commit()
    return {"received": True}


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
