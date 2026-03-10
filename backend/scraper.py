import os
import logging
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()
logger = logging.getLogger(__name__)

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()

_FIELD_MASK = (
    "places.id,"
    "places.displayName.text,"
    "places.formattedAddress,"
    "places.rating,"
    "places.userRatingCount,"
    "places.websiteUri,"
    "places.nationalPhoneNumber"
)
_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"


# ---------------------------------------------------------------------------
# Odpowiedzialność 1: Walidacja konfiguracji
# ---------------------------------------------------------------------------

def _validate_api_key() -> None:
    """Rzuca ValueError jeśli klucz API nie jest skonfigurowany."""
    if not GOOGLE_PLACES_API_KEY or GOOGLE_PLACES_API_KEY == "your_google_api_key_here":
        raise ValueError("Missing or invalid GOOGLE_PLACES_API_KEY in environment.")


# ---------------------------------------------------------------------------
# Odpowiedzialność 2: Komunikacja z Google Places API
# ---------------------------------------------------------------------------

async def _fetch_places(
    keyword: str, lat: float, lng: float, radius_km: float, limit: int
) -> list[dict]:
    """
    Wysyła zapytanie do Google Places API (New) Text Search.
    Rzuca ConnectionError przy problemach sieciowych,
    ValueError przy błędach API.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": _FIELD_MASK,
    }
    payload = {
        "textQuery": keyword,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_km * 1000.0,
            }
        },
        "maxResultCount": limit,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(_PLACES_URL, headers=headers, json=payload)
        except httpx.TimeoutException:
            raise ConnectionError(
                "Google Places API nie odpowiedział w czasie. Spróbuj ponownie."
            )
        except httpx.RequestError as exc:
            raise ConnectionError(
                f"Błąd połączenia z Google Places API: {exc}"
            )

        if response.status_code != 200:
            # Bezpieczne parsowanie — Google może zwrócić HTML przy błędach 5xx
            try:
                error_msg = (
                    response.json().get("error", {}).get("message", "Unknown error")
                )
            except Exception:
                error_msg = f"HTTP {response.status_code}: {response.text[:300]}"
            raise ValueError(f"Google Places API Error: {error_msg}")

        return response.json().get("places", [])


# ---------------------------------------------------------------------------
# Odpowiedzialność 3: Logika decyzji — czy miejsce jest dobrym leadem
# ---------------------------------------------------------------------------

def _is_good_lead(place: dict) -> bool:
    """
    Kwalifikuje każdą firmę jako leada — ocena jakości odbywa się w audycie AI.
    """
    return True


# ---------------------------------------------------------------------------
# Odpowiedzialność 4: Zapis do bazy danych (deduplication)
# ---------------------------------------------------------------------------

def _save_lead_if_new(place: dict, db: Session, user_id: int) -> bool:
    """
    Zapisuje lead do DB jeśli jeszcze nie istnieje.
    Zwraca True jeśli rekord został dodany, False jeśli pominięty (duplikat).
    """
    from app.models import Lead  # opóźniony import — Lead jest w osobnym pakiecie

    place_id: str = place.get("id", "")
    name: str = place.get("displayName", {}).get("text", "Unknown Name")

    # Deduplication — sprawdzamy po place_id, fallback po nazwie (dla danego użytkownika)
    if db.query(Lead).filter(Lead.place_id == place_id, Lead.user_id == user_id).first():
        logger.debug("Skipping duplicate (place_id): %s", place_id)
        return False
    if db.query(Lead).filter(Lead.company_name == name, Lead.user_id == user_id).first():
        logger.debug("Skipping duplicate (name): %s", name)
        return False

    db.add(
        Lead(
            place_id=place_id,
            company_name=name,
            phone=place.get("nationalPhoneNumber", ""),
            address=place.get("formattedAddress", ""),
            rating=place.get("rating", 0.0),
            reviews_count=place.get("userRatingCount", 0),
            website_uri=place.get("websiteUri", ""),
            user_id=user_id,
            status="new",
        )
    )
    return True


# ---------------------------------------------------------------------------
# Publiczne API modułu — fasada orkiestrująca pozostałe funkcje
# ---------------------------------------------------------------------------

async def scan_google_places(
    keyword: str,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int,
    db: Session,
    user_id: int,
) -> int:
    """
    Skanuje Google Places API, filtruje wyniki i zapisuje nowe leady do DB.

    Returns:
        Liczba nowo dodanych leadów.

    Raises:
        ValueError: Brak/nieprawidłowy klucz API lub błąd odpowiedzi Google.
        ConnectionError: Problem sieciowy (timeout, DNS, itp.).
    """
    _validate_api_key()

    logger.info(
        "Scanning Google Places: keyword='%s', lat=%.4f, lng=%.4f, radius=%.1fkm, limit=%d",
        keyword, lat, lng, radius_km, limit,
    )

    places = await _fetch_places(keyword, lat, lng, radius_km, limit)
    logger.info("Received %d places from Google API", len(places))

    qualified = [p for p in places if _is_good_lead(p)]
    logger.info("%d places qualified as leads after filtering", len(qualified))

    new_count = sum(_save_lead_if_new(p, db, user_id) for p in qualified)

    if new_count > 0:
        db.commit()
        logger.info("Committed %d new leads to DB", new_count)

    return new_count
