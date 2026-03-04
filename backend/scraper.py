import os
import asyncio
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()

async def scan_google_places(keyword: str, location: str, radius_km: float, db: Session):
    """
    Scans Google Places API (New) via Text Search.
    Filters places based on criteria and adds them to DB without duplicates.
    """
    if not GOOGLE_PLACES_API_KEY or GOOGLE_PLACES_API_KEY == "your_google_api_key_here":
        raise ValueError("Missing GOOGLE_PLACES_API_KEY in environment.")

    query = f"{keyword} in {location}"

    # Places API (New) Text Search Endpoint
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName.text,places.formattedAddress,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber"
    }
    
    payload = {
        "textQuery": query
    }

    from app.models import Lead # Local import to avoid circular dependency
    new_leads_count = 0

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_data = response.json().get("error", {})
            error_msg = error_data.get("message", "Unknown error with Google API")
            raise ValueError(f"Google Places API (New) Error: {error_msg}")
            
        data = response.json()
        results = data.get("places", [])

        for place in results:
            place_id = place.get("id")
            
            # Navigate nested displayName
            display_name_dict = place.get("displayName", {})
            name = display_name_dict.get("text", "Unknown Name")
            
            address = place.get("formattedAddress", "")
            rating = place.get("rating", 0.0)
            user_ratings_total = place.get("userRatingCount", 0)
            website = place.get("websiteUri", "")
            phone = place.get("nationalPhoneNumber", "")
            
            # Filtering Strategy
            # Primary: No website. Secondary: Rating < 4.0 or Few ratings.
            is_good_lead = False
            
            if rating < 4.0 or user_ratings_total < 10:
                is_good_lead = True
                
            if not website:
                is_good_lead = True

            if is_good_lead:
                # Check for duplicates using place_id
                existing_lead = db.query(Lead).filter(Lead.place_id == place_id).first()
                if not existing_lead:
                    # Fallback check by name
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
