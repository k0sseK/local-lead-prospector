from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class UserCreate(BaseModel):
    email: str
    password: str
    cf_turnstile_response: str | None = None


class UserLogin(BaseModel):
    email: str
    password: str
    cf_turnstile_response: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResendVerificationRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


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
    industry: Optional[str] = None
    lead_score: Optional[int] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class BulkStatusUpdateRequest(BaseModel):
    ids: List[int]
    status: str


class BulkDeleteRequest(BaseModel):
    ids: List[int]


class BulkOperationResult(BaseModel):
    updated: int
    not_found: List[int] = []

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
    country_code: str = "pl"          # kod kraju ISO 3166-1 alpha-2, np. "pl", "es", "de"
    # Filtry kwalifikacji leadów
    website_filter: str = "all"       # "all" | "with" | "without"
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    min_reviews: Optional[int] = None
    max_reviews: Optional[int] = None
    auto_audit: bool = False          # automatyczny audyt AI dla nowych leadów po skanie

class EmailSendRequest(BaseModel):
    subject: str
    body: str


class SetPlanRequest(BaseModel):
    user_id: int
    plan: str  # 'free' | 'pro' | 'admin'


class UserSettingsBase(BaseModel):
    sender_name: Optional[str] = None
    company_name: Optional[str] = None
    offer_description: Optional[str] = None
    tone_of_voice: str = "formalny"
    
    email_provider: str = "resend"
    resend_api_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    default_email_language: str = "polskim"

class UserSettingsOut(UserSettingsBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class AuditTemplateCreate(BaseModel):
    name: str
    prompt: str
    is_default: bool = False


class AuditTemplateUpdate(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    is_default: Optional[bool] = None


class AuditTemplateOut(BaseModel):
    id: int
    user_id: int
    name: str
    prompt: str
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditRequest(BaseModel):
    template_id: Optional[int] = None
    target_language: Optional[str] = None  # np. "polskim", "angielskim", "hiszpańskim"


class GenerateAuditPromptRequest(BaseModel):
    description: str


class GenerateAuditPromptResponse(BaseModel):
    prompt: str


class KeywordSuggestionRequest(BaseModel):
    description: str


class KeywordSuggestionResponse(BaseModel):
    suggestions: List[str]
    detected_location: Optional[str] = None


# ─── Email Sequences ──────────────────────────────────────────────────────────

class SequenceStepDraft(BaseModel):
    subject: str
    body: str


class SequenceCreate(BaseModel):
    steps: List[SequenceStepDraft]  # exactly 3 steps


class EmailEventOut(BaseModel):
    id: str
    lead_id: int
    sequence_step_id: Optional[int] = None
    sent_at: datetime
    opened_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SequenceStepOut(BaseModel):
    id: int
    step_number: int
    day_offset: int
    subject: str
    body: str
    status: str
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None       # populated from EmailEvent
    email_event_id: Optional[str] = None       # UUID of the tracking pixel

    class Config:
        from_attributes = True


class SequenceOut(BaseModel):
    id: int
    lead_id: int
    user_id: int
    status: str
    created_at: datetime
    steps: List[SequenceStepOut] = []
    company_name: Optional[str] = None

    class Config:
        from_attributes = True


class SequencePatchRequest(BaseModel):
    status: str  # active | paused | cancelled


class SequenceStepUpdate(BaseModel):
    subject: str
    body: str


# ─── Saved Searches ────────────────────────────────────────────────────────────

class SavedSearchCreate(BaseModel):
    name: str
    keyword: str
    lat: float
    lng: float
    radius_km: float = 5.0
    limit: int = 10
    country_code: str = "pl"
    filters: Optional[dict] = None
    schedule: str = "manual"   # manual | daily | weekly | monthly
    auto_audit: bool = False


class SavedSearchPatch(BaseModel):
    name: Optional[str] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None
    auto_audit: Optional[bool] = None


class SavedSearchOut(BaseModel):
    id: int
    user_id: int
    name: str
    keyword: str
    lat: float
    lng: float
    radius_km: float
    limit: int
    country_code: str
    filters: Optional[dict] = None
    schedule: str
    auto_audit: bool
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_run_leads: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
