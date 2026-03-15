from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://llp_user:llp_password@localhost:5432/llp_db")

_is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **({} if _is_sqlite else {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,    # testuje połączenie przed użyciem
        "pool_recycle": 1800,     # recykluje co 30 min (Railway ubija idle po ~60 min)
    })
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
