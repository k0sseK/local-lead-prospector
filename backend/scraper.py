import os
import sys

# Append the current directory to sys.path to allow imports from "app"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Base, Lead

def seed_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(Lead).count() > 0:
            print("Database already contains leads, skipping mock generation.")
            return

        print("Generating mock leads...")
        mock_leads = [
            Lead(
                company_name="Tech Solutions Inc.",
                phone="+1-555-0100",
                address="123 Innovation Dr, Tech City",
                status="new"
            ),
            Lead(
                company_name="Local Bakery",
                phone="+1-555-0200",
                address="456 Main St, Downtown",
                status="new"
            ),
            Lead(
                company_name="Plumbing Pros",
                phone="+1-555-0300",
                address="789 Industrial Pkwy",
                status="new"
            )
        ]
        
        db.add_all(mock_leads)
        db.commit()
        print("Successfully added 3 mock leads to the database.")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
