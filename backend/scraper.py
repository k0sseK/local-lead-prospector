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
    keyword: str,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int,
    country_code: str = "pl",
) -> list[dict]:
    """
    Wysyła zapytanie do Google Places API (New) Text Search.
    Używa locationRestriction (twarde ograniczenie) zamiast locationBias (hint),
    co eliminuje wyniki spoza wybranego obszaru.
    Rzuca ConnectionError przy problemach sieciowych,
    ValueError przy błędach API.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": _FIELD_MASK,
    }
    # locationRestriction — twarde ograniczenie obszaru (nie hint jak locationBias)
    payload = {
        "textQuery": keyword,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_km * 1000.0,
            }
        },
        "languageCode": country_code,          # język wyników (np. "pl", "es")
        "regionCode": country_code.upper(),    # region/kraj wyników (np. "PL", "ES")
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

def _matches_filters(place: dict, filters: dict) -> bool:
    """
    Kwalifikuje firmę jako leada na podstawie filtrów wybranych przez użytkownika.
    Domyślnie (filtry puste) akceptuje wszystkich.
    """
    rating: float = place.get("rating") or 0.0
    reviews: int = place.get("userRatingCount") or 0
    website: str = place.get("websiteUri", "") or ""

    website_filter = filters.get("website_filter", "all")
    if website_filter == "with" and not website:
        return False
    if website_filter == "without" and website:
        return False

    min_rating = filters.get("min_rating")
    if min_rating is not None and rating < min_rating:
        return False

    max_rating = filters.get("max_rating")
    if max_rating is not None and rating > max_rating:
        return False

    min_reviews = filters.get("min_reviews")
    if min_reviews is not None and reviews < min_reviews:
        return False

    max_reviews = filters.get("max_reviews")
    if max_reviews is not None and reviews > max_reviews:
        return False

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
    filters: dict | None = None,
    country_code: str = "pl",
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
        "Scanning Google Places: keyword='%s', lat=%.4f, lng=%.4f, radius=%.1fkm, limit=%d, country='%s'",
        keyword, lat, lng, radius_km, limit, country_code,
    )

    places = await _fetch_places(keyword, lat, lng, radius_km, limit, country_code)
    logger.info("Received %d places from Google API", len(places))

    _filters = filters or {}
    qualified = [p for p in places if _matches_filters(p, _filters)]
    logger.info("%d places qualified as leads after filtering", len(qualified))

    new_count = sum(_save_lead_if_new(p, db, user_id) for p in qualified)

    if new_count > 0:
        db.commit()
        logger.info("Committed %d new leads to DB", new_count)

    return new_count
