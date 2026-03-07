from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from datetime import datetime, timezone
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # 'user' | 'admin'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    sender_name = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    offer_description = Column(Text, nullable=True)
    tone_of_voice = Column(String, default="formalny")

    # Email provider settings
    email_provider = Column(String, default="resend") # "resend" | "smtp" | "none"
    resend_api_key = Column(String, nullable=True)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String, nullable=True)
    smtp_password = Column(String, nullable=True)
    smtp_from_email = Column(String, nullable=True)

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
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True, index=True)  # plain Integer, no FK object (SQLite-safe)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
