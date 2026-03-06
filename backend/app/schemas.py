from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LeadBase(BaseModel):
    company_name: str
    place_id: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    website_uri: Optional[str] = None
    email: Optional[str] = None
    has_ssl: Optional[bool] = None
    audited: Optional[bool] = False
    audit_report: Optional[dict] = None
    status: Optional[str] = "new"

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    status: str

class Lead(LeadBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScanRequest(BaseModel):
    keyword: str
    lat: float
    lng: float
    radius_km: float = 5.0
    limit: int = 10

class EmailSendRequest(BaseModel):
    subject: str
    body: str
