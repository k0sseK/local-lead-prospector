from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Numeric, UniqueConstraint
from datetime import datetime, timezone
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # 'user' | 'admin'
    plan = Column(String, default="free")  # 'free' | 'pro'  (admin → rola, nie plan)
    plan_expires_at = Column(DateTime, nullable=True)
    lemon_subscription_id = Column(String, nullable=True, index=True)
    lemon_subscription_status = Column(String, nullable=True)  # 'active' | 'cancelled' | 'expired' etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True, index=True)


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
    default_email_language = Column(String, default="polskim")  # domyślny język maili

class MonthlyUsage(Base):
    __tablename__ = "monthly_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    month = Column(String(7), nullable=False)  # format: '2025-03'
    ai_audits = Column(Integer, default=0)
    scans = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 5), default=0)
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_monthly_usage_user_month"),)


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # 'ai_audit' | 'scan' | 'email_send'
    lead_id = Column(Integer, nullable=True)  # plain Integer, no FK (SQLite-safe)
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    cost_usd = Column(Numeric(10, 5), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditTemplate(Base):
    __tablename__ = "audit_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EmailSequence(Base):
    __tablename__ = "email_sequences"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    status = Column(String, default="active")  # active | paused | completed | cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EmailSequenceStep(Base):
    __tablename__ = "email_sequence_steps"

    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(Integer, ForeignKey("email_sequences.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)   # 1, 2, 3
    day_offset = Column(Integer, nullable=False)    # 0 = day 1, 2 = day 3, 6 = day 7
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String, default="pending")      # pending | sent | skipped | failed
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)


class EmailEvent(Base):
    """One record per sent email — stores tracking UUID + open timestamp."""
    __tablename__ = "email_events"

    id = Column(String(36), primary_key=True)          # UUID4 — tracking pixel key
    user_id = Column(Integer, nullable=False, index=True)
    lead_id = Column(Integer, nullable=False, index=True)
    sequence_step_id = Column(Integer, nullable=True, index=True)  # null = manual send
    sent_at = Column(DateTime, nullable=False)
    opened_at = Column(DateTime, nullable=True)


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    keyword = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    radius_km = Column(Float, default=5.0)
    limit = Column(Integer, default=10)
    country_code = Column(String(2), default="pl")
    filters = Column(JSON, default=dict)          # {website_filter, min_rating, max_rating, min_reviews, max_reviews}
    schedule = Column(String, default="manual")   # manual | daily | weekly | monthly
    auto_audit = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_leads = Column(Integer, nullable=True)  # how many new leads the last run produced
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, index=True, nullable=True)  # Google Places ID — unique per user, not globally
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
    industry = Column(String, nullable=True)  # Google Places primaryType (np. "restaurant", "plumber")
    lead_score = Column(Integer, nullable=True)  # 0-100: jakość strony, niższy = więcej problemów = lepszy prospect
    user_id = Column(Integer, nullable=True, index=True)  # plain Integer, no FK object (SQLite-safe)
    share_token = Column(String(36), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("user_id", "place_id", name="uq_leads_user_place"),)
