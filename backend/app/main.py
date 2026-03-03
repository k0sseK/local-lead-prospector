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
    from backend.scraper import scan_google_places
    
    try:
        new_leads_added = await scan_google_places(
            keyword=scan_request.keyword,
            location=scan_request.location,
            radius_km=scan_request.radius_km,
            db=db
        )
        return {"message": f"Scan completed. Added {new_leads_added} new leads."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

