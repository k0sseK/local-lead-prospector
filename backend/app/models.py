from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, JSON
from datetime import datetime, timezone
from .database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, unique=True, index=True, nullable=True) # Google Places ID
    company_name = Column(String, index=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=True)
    website_uri = Column(String, nullable=True)
    email = Column(String, nullable=True)
    has_ssl = Column(Boolean, nullable=True)
    audited = Column(Boolean, default=False)
    audit_report = Column(JSON, nullable=True)
    status = Column(String, default="new") # options: 'new', 'to_contact', 'contacted', 'rejected', 'closed'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
