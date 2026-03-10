import asyncio
import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/keyword-suggestions", response_model=schemas.KeywordSuggestionResponse)
async def get_keyword_suggestions(
    request: schemas.KeywordSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(
            status_code=503, detail="Klucz GEMINI_API_KEY nie jest skonfigurowany."
        )

    description = request.description.strip()
    if not description:
        raise HTTPException(status_code=422, detail="Opis nie może być pusty.")

    prompt = f"""Jesteś ekspertem od marketingu i SEO lokalnego.

Użytkownik szuka firm, które chce pozyskać jako klientów. Opisuje swój cel w ten sposób:
"{description}"

Wykonaj dwa zadania:

1. Wygeneruj dokładnie 5 profesjonalnych, konkretnych słów kluczowych branżowych w języku polskim (BEZ nazw miast/lokalizacji), które najlepiej sprawdzą się jako zapytania do Google Maps / Google Places.
   Zasady dla słów kluczowych:
   - Wyłącznie frazy branżowe, bez nazw miejscowości
   - Zwięzłe (1-3 słowa)
   - Frazy, które ktoś faktycznie wpisuje szukając danej branży

2. Jeśli w opisie pojawia się konkretna miejscowość lub region (np. "Warszawa", "Kraków", "Trójmiasto", "Śląsk"), wyodrębnij ją jako lokalizację. Jeśli brak — zwróć null.

Odpowiedz WYŁĄCZNIE w formacie JSON:
{{"suggestions": ["słowo 1", "słowo 2", "słowo 3", "słowo 4", "słowo 5"], "detected_location": "Warszawa"}}

Jeśli brak lokalizacji:
{{"suggestions": ["słowo 1", "słowo 2", "słowo 3", "słowo 4", "słowo 5"], "detected_location": null}}"""

    try:
        import google.generativeai as genai

        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.8,
            ),
        )

        result = json.loads(response.text)

        if "suggestions" not in result or not isinstance(result["suggestions"], list):
            raise ValueError("Nieprawidłowa struktura odpowiedzi Gemini")

        detected_location = result.get("detected_location")
        if detected_location and not isinstance(detected_location, str):
            detected_location = None

        return {
            "suggestions": [str(s) for s in result["suggestions"][:5]],
            "detected_location": detected_location or None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Keyword suggestions failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd generowania słów kluczowych: {str(e)}"
        )
