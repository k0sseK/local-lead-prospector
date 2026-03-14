import html
import logging
import os

import resend
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from ..main import limiter
from .auth import verify_turnstile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["contact"])


class ContactFormPayload(BaseModel):
    name: str
    email: EmailStr
    message: str
    cf_turnstile_response: str | None = None


@router.post("/contact")
@limiter.limit("5/hour")
def contact(request: Request, payload: ContactFormPayload):
    verify_turnstile(payload.cf_turnstile_response)

    safe_name = html.escape(payload.name)
    safe_email = html.escape(str(payload.email))
    safe_message = html.escape(payload.message).replace("\n", "<br>")

    resend.api_key = os.getenv("RESEND_API_KEY", "")
    if not resend.api_key:
        logger.error("Brak RESEND_API_KEY — nie można wysłać wiadomości z formularza kontaktowego.")
        raise HTTPException(
            status_code=500,
            detail="Błąd konfiguracji serwera. Spróbuj ponownie później.",
        )

    try:
        resend.Emails.send(
            {
                "from": os.getenv("RESEND_FROM_EMAIL", "Formularz kontaktowy <formularz@znajdzfirmy.pl>"),
                "to": ["kontakt@znajdzfirmy.pl"],
                "reply_to": str(payload.email),
                "subject": f"Wiadomość od {safe_name} – formularz kontaktowy",
                "html": f"""
                    <p><strong>Imię i nazwisko:</strong> {safe_name}</p>
                    <p><strong>E-mail:</strong> {safe_email}</p>
                    <hr>
                    <p><strong>Wiadomość:</strong></p>
                    <p>{safe_message}</p>
                """,
            }
        )
        logger.info("Wiadomość z formularza kontaktowego wysłana od %s", payload.email)
    except Exception as exc:
        logger.error("Błąd wysyłki maila kontaktowego: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Nie udało się wysłać wiadomości. Spróbuj ponownie.",
        )

    return {"message": "Wiadomość została wysłana. Odezwiemy się wkrótce!"}
