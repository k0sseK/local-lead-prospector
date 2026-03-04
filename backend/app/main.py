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
    
    if not db_lead.website_uri:
        raise HTTPException(status_code=400, detail="Lead has no website to audit")

    from .website_auditor import audit_website
    
    audit_result = await audit_website(db_lead.website_uri)
    
    db_lead.has_ssl = audit_result.get("has_ssl", False)
    if audit_result.get("email"):
        db_lead.email = audit_result.get("email")
    db_lead.audited = True
    
    db.commit()
    db.refresh(db_lead)
    return db_lead

