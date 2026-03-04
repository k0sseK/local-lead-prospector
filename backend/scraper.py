import os
import asyncio
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

async def scan_google_places(keyword: str, location: str, radius_km: float, db: Session):
    """
    Scans Google Places API via Text Search.
    Filters places based on criteria and adds them to DB without duplicates.
    """
    if not GOOGLE_PLACES_API_KEY or GOOGLE_PLACES_API_KEY == "your_google_api_key_here":
        raise ValueError("Missing GOOGLE_PLACES_API_KEY in environment.")

    # Convert radius km to meters (max 50000m for Places API Text Search)
    radius_meters = int(radius_km * 1000)
    query = f"{keyword} in {location}"

    # Prepare URL for Google Places API Text Search
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "radius": radius_meters,
        "key": GOOGLE_PLACES_API_KEY
    }

    from app.models import Lead # Local import to avoid circular dependency
    new_leads_count = 0

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching from Google API: {response.text}")
            return 0
            
        data = response.json()
        api_status = data.get("status")
        
        if api_status not in ("OK", "ZERO_RESULTS"):
            error_msg = data.get("error_message", f"Google API returned status: {api_status}")
            raise ValueError(f"Google API Error: {error_msg}")
            
        results = data.get("results", [])

        for place in results:
            place_id = place.get("place_id")
            name = place.get("name")
            address = place.get("formatted_address")
            rating = place.get("rating", 0.0)
            user_ratings_total = place.get("user_ratings_total", 0)
            
            # Since standard text search doesn't always return website/phone without place details,
            # we do a lightweight check. If we definitively need website info, we'd fire Place Details request.
            # However, for MVP, we rely on the rating and user rating counts as filtering metrics from the Text Search.
            # To check 'website', you ideally need Place Details API. Let's do a fast fetching of details if rules apply:
            
            # Strategy: First check primary conditions (ratings).
            # If rating < 4.0 OR user_ratings_total < 10, it's a lead!
            
            is_good_lead = False
            website = "" # Text search response generally doesn't include "website" property directly.
            
            if rating < 4.0 or user_ratings_total < 10:
                is_good_lead = True
            
            # Additional check: If we want to strictly check website, we have to make an extra API call per item.
            # Let's fetch details to get phone and website for better quality data and filtering.
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": place_id,
                "fields": "website,formatted_phone_number",
                "key": GOOGLE_PLACES_API_KEY
            }
            
            try:
                details_response = await client.get(details_url, params=details_params)
                if details_response.status_code == 200:
                    details_data = details_response.json().get("result", {})
                    website = details_data.get("website", "")
                    phone = details_data.get("formatted_phone_number", "")
            except Exception as e:
                print(f"Failed to fetch details for {name}: {e}")
                phone = ""

            if not website:
                is_good_lead = True

            if is_good_lead:
                # Check for duplicates using place_id
                existing_lead = db.query(Lead).filter(Lead.place_id == place_id).first()
                if not existing_lead:
                    # Also fallback check by name to be safe
                    existing_by_name = db.query(Lead).filter(Lead.company_name == name).first()
                    if not existing_by_name:
                        lead = Lead(
                            place_id=place_id,
                            company_name=name,
                            phone=phone,
                            address=address,
                            status="new"
                        )
                        db.add(lead)
                        new_leads_count += 1
        
        if new_leads_count > 0:
            db.commit()

    return new_leads_count
