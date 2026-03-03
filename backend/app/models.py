from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from .database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    status = Column(String, default="new") # options: 'new', 'contacted', 'rejected'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
