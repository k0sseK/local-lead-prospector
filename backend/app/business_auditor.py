import httpx
from bs4 import BeautifulSoup
import re
import logging
import time
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Domeny/fragmenty które nigdy nie są prawdziwymi emailami kontaktowymi
_FAKE_EMAIL_FRAGMENTS = [
    "example.com", "email.com", "yourdomain", "domain.com",
    "sentry.io", "wixpress.com", "wordpress.org", "wordpress.com",
    "noreply", "no-reply", "donotreply", "mailer-daemon",
    "@2x.", ".png", ".jpg", ".gif",  # URLe z @ w środku
]

# Podstrony do sprawdzenia jeśli na homepage nie ma emaila
_CONTACT_SUBPATHS = [
    "/contact", "/kontakt", "/kontakty", "/kontaktiere-uns",
    "/about", "/o-nas", "/o-firmie", "/uber-uns",
    "/impressum", "/impressum.html",
    "/datenschutz",
]


def _extract_email_from_soup(soup: BeautifulSoup) -> str | None:
    """
    Szuka emaila w kolejności:
    1. Linki mailto: (najbardziej wiarygodne)
    2. Tekst strony (regex)
    Zwraca pierwszy wiarygodny email lub None.
    """
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip().lower()
            if email and EMAIL_REGEX.match(email) and not _is_fake_email(email):
                return email

    text_content = soup.get_text(separator=" ")
    for em in EMAIL_REGEX.findall(text_content):
        em = em.lower()
        if not _is_fake_email(em):
            return em

    return None


def _is_fake_email(email: str) -> bool:
    return any(fragment in email for fragment in _FAKE_EMAIL_FRAGMENTS)


async def _try_subpages_for_email(
    client: httpx.AsyncClient,
    base_url: str,
    headers: dict,
) -> str | None:
    """
    Próbuje znaleźć email na typowych podstronach kontaktowych.
    Sprawdza max 4 podstrony, zatrzymuje się przy pierwszym znalezionym emailu.
    """
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    checked = 0
    for subpath in _CONTACT_SUBPATHS:
        if checked >= 4:
            break
        subpage_url = urljoin(origin, subpath)
        try:
            resp = await client.get(subpage_url, headers=headers, timeout=6.0)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                email = _extract_email_from_soup(soup)
                if email:
                    logger.debug("Found email on subpage %s: %s", subpath, email)
                    return email
            checked += 1
        except Exception:
            checked += 1
            continue

    return None


async def audit_lead(lead_data: dict) -> dict:
    """
    Collects raw audit data from Google Places info and website.
    Returns only raw facts — no interpretation or selling points.
    AI analysis is handled separately by ai_analyzer.py.
    """
    raw_data = {
        "rating": lead_data.get("rating"),
        "reviews_count": lead_data.get("reviews_count"),
        "has_website": bool(lead_data.get("website_uri")),
        "has_ssl": False,
        "load_time": None,
        "has_viewport": None,
        "has_title": None,
        "has_h1": None,
        "missing_seo_tags": [],
        "email": None,
        "website_reachable": None,
        "cms": None,
        "social_media": [],
        "has_meta_description": False,
    }

    website_uri = lead_data.get("website_uri")
    if not website_uri:
        return raw_data  # No website to audit

    url = website_uri
    if not url.startswith("http"):
        url = "http://" + url

    if url.startswith("https://"):
        raw_data["has_ssl"] = True

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        start_time = time.time()

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # Sprawdź czy strona obsługuje HTTPS jeśli jeszcze nie
            if not raw_data["has_ssl"]:
                https_url = url.replace("http://", "https://", 1)
                try:
                    ssl_check = await client.get(https_url, headers=headers)
                    if ssl_check.status_code < 400:
                        raw_data["has_ssl"] = True
                        url = https_url
                except Exception:
                    pass

            response = await client.get(url, headers=headers)
            raw_data["load_time"] = round(time.time() - start_time, 2)
            raw_data["website_reachable"] = True

            # Sprawdź SSL po finalnym redirectcie
            if str(response.url).startswith("https://"):
                raw_data["has_ssl"] = True

            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")

                # Viewport (RWD)
                viewport = soup.find("meta", attrs={"name": "viewport"})
                raw_data["has_viewport"] = bool(viewport)
                if not viewport:
                    raw_data["missing_seo_tags"].append("viewport")

                # SEO tags
                title = soup.find("title")
                h1 = soup.find("h1")
                meta_desc = soup.find("meta", attrs={"name": "description"})

                raw_data["has_title"] = bool(title)
                raw_data["has_h1"] = bool(h1)
                raw_data["has_meta_description"] = bool(meta_desc)

                if not title:
                    raw_data["missing_seo_tags"].append("title")
                if not h1:
                    raw_data["missing_seo_tags"].append("h1")
                if not meta_desc:
                    raw_data["missing_seo_tags"].append("meta_description")

                # CMS detection
                if "wp-content" in html_content:
                    raw_data["cms"] = "WordPress"
                elif "_next" in html_content:
                    raw_data["cms"] = "Next.js"
                elif "cdn.shopify" in html_content:
                    raw_data["cms"] = "Shopify"
                elif "squarespace.com" in html_content:
                    raw_data["cms"] = "Squarespace"
                elif "wix.com" in html_content or "wixstatic.com" in html_content:
                    raw_data["cms"] = "Wix"

                # Social media
                for a_tag in soup.find_all("a", href=True):
                    href_lower = a_tag["href"].lower()
                    if "facebook.com" in href_lower and "facebook" not in raw_data["social_media"]:
                        raw_data["social_media"].append("facebook")
                    elif "instagram.com" in href_lower and "instagram" not in raw_data["social_media"]:
                        raw_data["social_media"].append("instagram")
                    elif "linkedin.com" in href_lower and "linkedin" not in raw_data["social_media"]:
                        raw_data["social_media"].append("linkedin")

                # Email — najpierw homepage, potem podstrony kontaktowe
                raw_data["email"] = _extract_email_from_soup(soup)
                if not raw_data["email"]:
                    raw_data["email"] = await _try_subpages_for_email(client, url, headers)

    except Exception as e:
        logger.warning(f"Error auditing {url}: {e}")
        raw_data["website_reachable"] = False

    return raw_data
