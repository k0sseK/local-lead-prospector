import json
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


DEFAULT_AUDIT_CONDITIONS = """\
- Jeśli ocena Google (rating) mieści się w przedziale 4.0–4.7, NIE mów że jest tragiczna. Zamiast tego podkreśl, że jest pole do poprawy by zdominować konkurencję i przyciągnąć więcej klientów.
- Jeśli brak strony www — to poważny problem, podkreśl utratę klientów.
- Jeśli brak SSL — wspomnij o ostrzeżeniach przeglądarek.
- Jeśli wolne ładowanie (load_time > 2s) — wspomnij o współczynniku odrzuceń.
- Jeśli brakuje tagów SEO — wspomnij o widoczności w wyszukiwarce."""


async def generate_ai_analysis(raw_data: dict, company_name: str, user_settings=None, audit_template=None, target_language: str = "polskim") -> dict:
    """
    Sends raw audit data to Gemini AI and returns structured selling points + email draft.
    Returns: {"selling_points": [...], "email_draft": "..."}
    """
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set in .env")
        return {
            "selling_points": ["Brak klucza API Gemini — analiza AI niedostępna."],
            "email_draft": "",
        }

    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel("gemini-2.5-flash")

        if user_settings:
            sender_block = (
                f"Napisz e-mail w imieniu {user_settings.sender_name} "
                f"z firmy {user_settings.company_name}. "
                f"Oferujesz: {user_settings.offer_description}. "
                f"Bezwzględnie zachowaj następujący ton wypowiedzi: {user_settings.tone_of_voice}. "
                f"Użyj zebranych błędów z audytu, aby zaproponować swoje usługi."
            )
        else:
            sender_block = (
                "Napisz profesjonalnego, nienachalnego e-maila sprzedażowego w tonie formalnym. "
                "Proponuj współpracę w tonie partnerskim, nie agresywnym. "
                "W podpisie użyj placeholderów [Twoje Imię] i [Nazwa Twojej Firmy]."
            )

        audit_conditions = (
            audit_template.prompt
            if audit_template and audit_template.prompt.strip()
            else DEFAULT_AUDIT_CONDITIONS
        )
        audit_name = audit_template.name if audit_template else "SEO i marketing cyfrowy"

        prompt = f"""Jesteś ekspertem ds. {audit_name}. Analizujesz dane zebrane z audytu firmy "{company_name}".

Oto surowe dane z audytu:
{json.dumps(raw_data, indent=2, ensure_ascii=False)}

Instrukcje audytu:
{audit_conditions}

Na podstawie powyższych danych i instrukcji:

1. Wygeneruj 2-3 mądre, biznesowe punkty zaczepienia (Selling Points) — krótkie obserwacje, które mogą posłużyć jako argument sprzedażowy w rozmowie z klientem.

2. {sender_block}
   E-mail powinien:
   - Być skierowany do właściciela firmy "{company_name}"
   - Zawierać konkretne odniesienia do znalezionych problemów
   - Napisz e-mail w języku: {target_language}

Odpowiedz WYŁĄCZNIE w formacie JSON z następującą strukturą:
{{
  "selling_points": ["punkt 1", "punkt 2", "punkt 3"],
  "email_draft": "treść kompletnego maila"
}}"""

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )

        result = json.loads(response.text)

        # Validate structure
        if "selling_points" not in result or "email_draft" not in result:
            raise ValueError("Invalid response structure from Gemini")

        return {
            "selling_points": result["selling_points"],
            "email_draft": result["email_draft"],
        }

    except Exception as e:
        logger.error(f"Gemini AI analysis failed: {e}")
        return {
            "selling_points": [f"Analiza AI niedostępna: {str(e)}"],
            "email_draft": "",
        }
