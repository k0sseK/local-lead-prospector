from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="B2B Lead Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, we allow all origins. In production, restrict this.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/leads", response_model=List[schemas.Lead])
def read_leads(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    leads = db.query(models.Lead).offset(skip).limit(limit).all()
    return leads

@app.patch("/api/leads/{lead_id}", response_model=schemas.Lead)
def update_lead_status(lead_id: int, lead_update: schemas.LeadUpdate, db: Session = Depends(database.get_db)):
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db_lead.status = lead_update.status
    db.commit()
    db.refresh(db_lead)
    return db_lead

@app.post("/api/scan")
async def scan_for_leads(scan_request: schemas.ScanRequest, db: Session = Depends(database.get_db)):
    from scraper import scan_google_places
    
    try:
        new_leads_added = await scan_google_places(
            keyword=scan_request.keyword,
            lat=scan_request.lat,
            lng=scan_request.lng,
            radius_km=scan_request.radius_km,
            limit=scan_request.limit,
            db=db
        )
        return {"message": f"Scan completed. Added {new_leads_added} new leads."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/leads/{lead_id}/audit", response_model=schemas.Lead)
async def audit_lead_endpoint(lead_id: int, db: Session = Depends(database.get_db)):
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    from .business_auditor import audit_lead
    from .ai_analyzer import generate_ai_analysis
    
    # 1. Collect raw data
    lead_data = {
        "rating": db_lead.rating,
        "reviews_count": db_lead.reviews_count,
        "website_uri": db_lead.website_uri,
    }
    
    raw_data = await audit_lead(lead_data)
    
    # 2. Generate AI analysis
    ai_result = await generate_ai_analysis(raw_data, db_lead.company_name)
    
    # 3. Build unified audit report
    audit_report = {
        "raw_data": raw_data,
        "selling_points": ai_result.get("selling_points", []),
        "email_draft": ai_result.get("email_draft", ""),
    }
    
    db_lead.audit_report = audit_report
    db_lead.has_ssl = raw_data.get("has_ssl", False)
    if raw_data.get("email"):
        db_lead.email = raw_data.get("email")
    db_lead.audited = True
    
    db.commit()
    db.refresh(db_lead)
    return db_lead

