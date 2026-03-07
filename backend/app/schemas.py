from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


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
    notes: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class Lead(LeadBase):
    id: int
    user_id: Optional[int] = None
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


class UserSettingsBase(BaseModel):
    sender_name: Optional[str] = None
    company_name: Optional[str] = None
    offer_description: Optional[str] = None
    tone_of_voice: str = "formalny"


class UserSettingsOut(UserSettingsBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
