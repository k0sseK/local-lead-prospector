"""
audit_service.py

Warstwa serwisowa orkiestrująca pełny audyt leada.
Router (main.py) deleguje tutaj całą logikę biznesową —
sam odpowiada wyłącznie za HTTP: routing, 404, 500.
"""
import logging
from sqlalchemy.orm import Session

from . import models
from .business_auditor import audit_lead
from .ai_analyzer import generate_ai_analysis

logger = logging.getLogger(__name__)


async def run_full_audit(db_lead: models.Lead, db: Session) -> models.Lead:
    """
    Orkiestruje pełny audyt leada w dwóch krokach:
      1. Audyt techniczny strony (business_auditor)
      2. Analiza AI z Gemini (ai_analyzer)

    Partial failure jest obsługiwany gracefully:
    - Jeśli audyt strony zawiedzie → raw_data z flagą website_reachable=False
    - Jeśli AI zawiedzie → puste selling_points, pusty email_draft
    Rekord leada zostaje oznaczony jako `audited=True` w obu przypadkach.

    Returns:
        Odświeżony obiekt Lead z uzupełnionym audit_report.
    """
    lead_data = {
        "rating": db_lead.rating,
        "reviews_count": db_lead.reviews_count,
        "website_uri": db_lead.website_uri,
    }

    # --- Krok 1: Audyt techniczny strony www ---
    try:
        raw_data = await audit_lead(lead_data)
        logger.info("Website audit completed for lead %d", db_lead.id)
    except Exception as exc:
        logger.error(
            "Website audit failed for lead %d: %s", db_lead.id, exc, exc_info=True
        )
        raw_data = {
            "website_reachable": False,
            "has_ssl": False,
            "load_time": None,
            "has_viewport": None,
            "has_title": None,
            "has_h1": None,
            "missing_seo_tags": [],
            "email": None,
        }

    # --- Krok 2: Analiza AI (Gemini) ---
    try:
        ai_result = await generate_ai_analysis(raw_data, db_lead.company_name)
        logger.info("AI analysis completed for lead %d", db_lead.id)
    except Exception as exc:
        logger.error(
            "AI analysis failed for lead %d: %s", db_lead.id, exc, exc_info=True
        )
        ai_result = {"selling_points": [], "email_draft": ""}

    # --- Krok 3: Zapis wyników do modelu ---
    db_lead.audit_report = {
        "raw_data": raw_data,
        "selling_points": ai_result.get("selling_points", []),
        "email_draft": ai_result.get("email_draft", ""),
    }
    db_lead.has_ssl = raw_data.get("has_ssl", False)

    # Nadpisuj email tylko jeśli audyt znalazł nowy i lead go jeszcze nie ma
    discovered_email = raw_data.get("email")
    if discovered_email and not db_lead.email:
        db_lead.email = discovered_email

    db_lead.audited = True

    db.commit()
    db.refresh(db_lead)
    return db_lead
