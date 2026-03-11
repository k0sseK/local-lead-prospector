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


# Mapowanie kodu kraju (ISO alpha-2) -> nazwa języka w celowniku (pl. gramatyka dla promptów)
COUNTRY_LANGUAGE_MAP = {
    "PL": "polskim",
    "ES": "hiszpańskim",
    "DE": "niemieckim",
    "FR": "francuskim",
    "EN": "angielskim",
    "GB": "angielskim",
    "US": "angielskim",
    "IT": "włoskim",
    "PT": "portugalskim",
    "NL": "niderlandzkim",
    "CZ": "czeskim",
    "SK": "słowackim",
    "RO": "rumuńskim",
    "HU": "węgierskim",
    "UA": "ukraińskim",
}


def _detect_language_from_address(address: str | None) -> str | None:
    """
    Próbuje wykryć język na podstawie 2-literowego kodu kraju na końcu adresu.
    Przykład: "Calle Mayor 5, Madrid, Spain, ES" -> "hiszpańskim".
    Zwraca None jeśli nie uda się wykryć.
    """
    if not address:
        return None
    parts = [p.strip() for p in address.replace(",", " ").split()]
    if parts:
        candidate = parts[-1].upper()
        if candidate in COUNTRY_LANGUAGE_MAP:
            return COUNTRY_LANGUAGE_MAP[candidate]
    return None


async def run_full_audit(db_lead: models.Lead, db: Session, template_id: int | None = None, target_language: str | None = None) -> models.Lead:
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
            "cms": None,
            "social_media": [],
            "has_meta_description": False,
        }

    # --- Krok 2: Analiza AI (Gemini) ---
    user_settings = (
        db.query(models.UserSettings)
        .filter(models.UserSettings.user_id == db_lead.user_id)
        .first()
    )

    # ─── Rozstrzygnij język maila ─────────────────────────────────────────────
    # Priorytet: 1) explicit target_language z requestu, 2) auto-wykrycie z adresu,
    # 3) domyślny język z user_settings, 4) fallback na "polskim"
    if not target_language:
        target_language = _detect_language_from_address(db_lead.address)
    if not target_language:
        target_language = getattr(user_settings, "default_email_language", None) or "polskim"
    # ─────────────────────────────────────────────────────────────────────────

    # Załaduj wybrany szablon; jeśli brak — weź domyślny użytkownika
    audit_template = None
    if template_id:
        audit_template = (
            db.query(models.AuditTemplate)
            .filter(
                models.AuditTemplate.id == template_id,
                models.AuditTemplate.user_id == db_lead.user_id,
            )
            .first()
        )
    if not audit_template:
        audit_template = (
            db.query(models.AuditTemplate)
            .filter(
                models.AuditTemplate.user_id == db_lead.user_id,
                models.AuditTemplate.is_default == True,
            )
            .first()
        )

    try:
        ai_result = await generate_ai_analysis(
            raw_data, db_lead.company_name, user_settings=user_settings, audit_template=audit_template,
            target_language=target_language
        )
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
