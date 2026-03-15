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

        has_sender_info = user_settings and (
            user_settings.sender_name or user_settings.company_name or user_settings.offer_description
        )
        if has_sender_info:
            parts = []
            if user_settings.sender_name and user_settings.company_name:
                parts.append(f"Napisz e-mail w imieniu {user_settings.sender_name} z firmy {user_settings.company_name}.")
            elif user_settings.sender_name:
                parts.append(f"Napisz e-mail w imieniu {user_settings.sender_name}.")
            elif user_settings.company_name:
                parts.append(f"Napisz e-mail w imieniu firmy {user_settings.company_name}.")
            if user_settings.offer_description:
                parts.append(f"Oferujesz: {user_settings.offer_description}.")
            tone = user_settings.tone_of_voice or "formalny"
            parts.append(f"Bezwzględnie zachowaj następujący ton wypowiedzi: {tone}.")
            parts.append("Użyj zebranych błędów z audytu, aby zaproponować swoje usługi.")
            sender_block = " ".join(parts)
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

        # Format technologies as a readable section for Gemini
        technologies: dict = raw_data.get("technologies") or {}
        CATEGORY_HINTS = {
            "Analytics":      "brak śledzenia użytkowników i konwersji",
            "Marketing/Ads":  "brak remarketingu i płatnych kampanii",
            "Chat/Support":   "brak obsługi klienta online / live chat",
            "E-commerce":     "brak platformy sklepowej",
            "SEO Tools":      "brak narzędzi SEO on-site",
            "Payments":       "brak systemu płatności online",
            "CMS":            "nieznany CMS / strona statyczna",
            "Frameworks/JS":  "brak informacji o stosie technicznym",
            "Hosting":        "brak informacji o hostingu",
        }
        tech_lines = []
        for category, hint in CATEGORY_HINTS.items():
            found = technologies.get(category, [])
            if found:
                tech_lines.append(f"  {category}: {', '.join(found)}")
            else:
                tech_lines.append(f"  {category}: [brak] — {hint}")
        technologies_section = "Wykryte technologie:\n" + "\n".join(tech_lines)

        prompt = f"""Jesteś ekspertem ds. {audit_name}. Analizujesz dane zebrane z audytu firmy "{company_name}".

Oto surowe dane z audytu:
{json.dumps(raw_data, indent=2, ensure_ascii=False)}

{technologies_section}

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


async def generate_sequence_drafts(
    company_name: str,
    initial_email_draft: str,
    selling_points: list,
    user_settings=None,
    target_language: str = "polskim",
) -> list[dict]:
    """
    Generates 3 follow-up email drafts for a drip sequence:
      Step 1 (day 1): initial outreach — derived from existing audit email draft
      Step 2 (day 3): gentle follow-up if no reply
      Step 3 (day 7): final follow-up / last chance
    Returns: [{"subject": "...", "body": "..."}, ...]
    """
    if not GEMINI_API_KEY:
        return _fallback_sequence_drafts(company_name, initial_email_draft, target_language)

    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        sender_info = ""
        if user_settings:
            parts = []
            if user_settings.sender_name and user_settings.company_name:
                parts.append(f"{user_settings.sender_name} z firmy {user_settings.company_name}")
            elif user_settings.sender_name:
                parts.append(user_settings.sender_name)
            elif user_settings.company_name:
                parts.append(f"firmy {user_settings.company_name}")
            if parts:
                sender_info = f"Nadawca: {', '.join(parts)}."

        tone = (user_settings.tone_of_voice or "formalny") if user_settings else "formalny"

        prompt = f"""Jesteś ekspertem od zimnych maili B2B.
Przygotowałeś/aś już pierwszego e-maila do firmy "{company_name}" na podstawie audytu strony:

--- PIERWSZE WIADOMOŚĆ (gotowa) ---
{initial_email_draft}
---

Kluczowe punkty zaczepienia: {', '.join(selling_points) if selling_points else 'brak'}
{sender_info}
Ton: {tone}

Teraz napisz dwa e-maile follow-up (jeśli brak odpowiedzi):
- E-mail #2 (wysyłany po 3 dniach): krótkie, uprzejme przypomnienie — nie powtarzaj całej argumentacji, tylko zaznacz że czekasz na odpowiedź.
- E-mail #3 (wysyłany po 7 dniach): ostatni kontakt — powiedz że to ostatnia wiadomość, zostaw drzwi otwarte.

Napisz wszystkie 3 maile w języku: {target_language}

Odpowiedz WYŁĄCZNIE w formacie JSON:
{{
  "step1": {{"subject": "temat maila 1", "body": "treść maila 1"}},
  "step2": {{"subject": "temat maila 2", "body": "treść maila 2"}},
  "step3": {{"subject": "temat maila 3", "body": "treść maila 3"}}
}}

Dla step1 skopiuj dosłownie treść pierwszego maila podaną powyżej, ale dodaj dobry temat (subject)."""

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )

        result = json.loads(response.text)
        return [
            {"subject": result["step1"]["subject"], "body": result["step1"]["body"]},
            {"subject": result["step2"]["subject"], "body": result["step2"]["body"]},
            {"subject": result["step3"]["subject"], "body": result["step3"]["body"]},
        ]

    except Exception as e:
        logger.error(f"generate_sequence_drafts failed: {e}")
        return _fallback_sequence_drafts(company_name, initial_email_draft, target_language)


def _fallback_sequence_drafts(company_name: str, initial_email_draft: str, target_language: str) -> list[dict]:
    return [
        {
            "subject": f"Propozycja współpracy — {company_name}",
            "body": initial_email_draft or f"Dzień dobry,\n\nChciałem/am się skontaktować w sprawie potencjalnej współpracy z {company_name}.\n\nPozdrawiam",
        },
        {
            "subject": f"Re: Propozycja współpracy — {company_name}",
            "body": f"Dzień dobry,\n\nPozwalam sobie przypomnieć o mojej wcześniejszej wiadomości.\nCzy mieli Państwo chwilę na zapoznanie się z moją propozycją?\n\nBędę wdzięczny/a za odpowiedź.\n\nPozdrawiam",
        },
        {
            "subject": f"Ostatni kontakt — {company_name}",
            "body": f"Dzień dobry,\n\nTo moja ostatnia wiadomość w tej sprawie.\nJeśli kiedykolwiek będą Państwo zainteresowani współpracą, zapraszam do kontaktu.\n\nPozdrawiam serdecznie",
        },
    ]
