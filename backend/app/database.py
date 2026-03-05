from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import os

# In Docker, the DB lives in /app/data (mounted as a named volume).
# When running locally outside Docker, fall back to the repo root's leads.db.
_db_path = os.getenv("DATABASE_URL", "sqlite:////app/data/leads.db"
                     if os.path.isdir("/app/data") else "sqlite:///./leads.db")
SQLALCHEMY_DATABASE_URL = _db_path

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
