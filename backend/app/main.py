import csv
import io
import logging
import os
import resend
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, database
from .dependencies import get_current_user
from .routers import auth as auth_router

logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=database.engine)

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
    from scraper import scan_google_places

    try:
        new_leads_added = await scan_google_places(
            keyword=scan_request.keyword,
            lat=scan_request.lat,
            lng=scan_request.lng,
            radius_km=scan_request.radius_km,
            limit=scan_request.limit,
            db=db,
            user_id=current_user.id,
        )
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

    try:
        from .audit_service import run_full_audit
        return await run_full_audit(db_lead, db)
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
        raise HTTPException(status_code=400, detail="Lead has no email address")

    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY is not configured")

    from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    try:
        params = {
            "from": from_email,
            "to": [db_lead.email],
            "subject": request.subject,
            "html": request.body.replace('\n', '<br>')
        }
        resend.Emails.send(params)
    except Exception as e:
        logger.error(f"Failed to send email to {db_lead.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    db_lead.status = "contacted"
    db.commit()
    db.refresh(db_lead)
    return {"message": "Email sent successfully", "lead": db_lead}
