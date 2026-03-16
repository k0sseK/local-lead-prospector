import httpx
from bs4 import BeautifulSoup
import os
import re
import logging
import time
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# ── Playwright scraper service (optional fallback for SPA sites) ─────────────
PLAYWRIGHT_SERVICE_URL = os.getenv("PLAYWRIGHT_SERVICE_URL", "")
PLAYWRIGHT_API_SECRET = os.getenv("PLAYWRIGHT_API_SECRET", "")

# HTML shorter than this likely means the page is JS-rendered (empty SPA shell)
_MIN_MEANINGFUL_HTML_LENGTH = 2000

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


class TechDetector:
    """Wappalyzer-style technology fingerprinting from HTML + headers."""

    # (tech_name, [signals_in_html_or_scripts])
    SIGNATURES: dict[str, list[tuple[str, list[str]]]] = {
        "CMS": [
            ("WordPress",   ["wp-content", "wp-json", "wp-includes"]),
            ("Wix",         ["wixsite.com", "wix.com", "_wixCIDX", "wixstatic.com"]),
            ("Squarespace", ["squarespace.com", "static1.squarespace"]),
            ("Webflow",     ["webflow.com"]),
            ("Shopify",     ["cdn.shopify", "myshopify.com"]),
            ("Joomla",      ["/components/com_", "Joomla!"]),
            ("Drupal",      ["Drupal.settings", "drupal.js"]),
            ("PrestaShop",  ["prestashop", "PrestaShop"]),
            ("Magento",     ["Mage.Cookies", "mage/", "MAGE_"]),
            ("Ghost",       ["ghost.io", "ghost/core"]),
            ("Webnode",     ["webnode.com", "webnode.cz"]),
            ("Weebly",      ["weebly.com", "weeblysite.com"]),
        ],
        "Analytics": [
            ("Google Analytics",  ["gtag/js", "ga.js", "analytics.js", "googletagmanager.com/gtag", "'G-", '"G-', "'UA-", '"UA-']),
            ("Google Tag Manager",["gtm.js", "GTM-", "googletagmanager.com/gtm"]),
            ("Hotjar",            ["hotjar.com", "hj.src"]),
            ("Mixpanel",          ["mixpanel.com", "mixpanel.init"]),
            ("Microsoft Clarity", ["clarity.ms", "clarity.js"]),
            ("Matomo",            ["matomo.js", "piwik.js", "matomo.php"]),
            ("Plausible",         ["plausible.io"]),
            ("Facebook Pixel",    ["fbq(", "connect.facebook.net/en_US/fbevents"]),
        ],
        "Marketing/Ads": [
            ("Google Ads",      ["googleadservices.com", "conversion.js", "google_conversion"]),
            ("TikTok Pixel",    ["analytics.tiktok.com", "tiktok.com/i/pixel"]),
            ("LinkedIn Insight",["snap.licdn.com", "linkedin.com/insight"]),
        ],
        "Chat/Support": [
            ("Intercom",  ["intercom.io", "widget.intercom.io"]),
            ("Zendesk",   ["zendesk.com", "zopim.com", "zopim"]),
            ("Tawk.to",   ["tawk.to"]),
            ("LiveChat",  ["livechatinc.com"]),
            ("Crisp",     ["crisp.chat", "client.crisp.chat"]),
            ("Tidio",     ["tidio.co", "tidiochat.com"]),
        ],
        "E-commerce": [
            ("WooCommerce", ["woocommerce", "wc-cart", "wc_add_to_cart"]),
            ("IdoSell",     ["iai-shop.com", "idosell.com"]),
            ("Shoper",      ["shoper.pl"]),
        ],
        "Frameworks/JS": [
            ("React",     ["react-dom", "__reactFiber", "data-reactroot"]),
            ("Next.js",   ["__NEXT_DATA__", "_next/static"]),
            ("Vue.js",    ["__vue", "vue.runtime", "vue.min.js"]),
            ("Nuxt.js",   ["__nuxt", "_nuxt/"]),
            ("Angular",   ["ng-version", "angular.min.js", "ng-app"]),
            ("jQuery",    ["jquery.min.js", "jquery.js", "/jquery-"]),
            ("Bootstrap", ["bootstrap.min.css", "bootstrap.min.js", "bootstrap.bundle"]),
        ],
        "SEO Tools": [
            ("Yoast SEO", ["yoast", "wpseo_"]),
            ("RankMath",  ["rank-math", "rankMath"]),
            ("SEOPress",  ["seopress"]),
        ],
        "Payments": [
            ("PayU",        ["payu.pl", "secure.payu.com", "openpayu"]),
            ("Przelewy24",  ["przelewy24.pl", "p24.pl"]),
            ("Stripe",      ["stripe.com/v3", "stripe.js", "js.stripe.com"]),
            ("PayPal",      ["paypal.com/sdk", "paypalobjects.com"]),
        ],
    }

    @classmethod
    def detect(cls, html: str, headers: dict, soup: BeautifulSoup) -> dict[str, list[str]]:
        results: dict[str, list[str]] = {}

        # Normalize header keys to lowercase
        norm_headers = {k.lower(): v for k, v in headers.items()}
        server_header = norm_headers.get("server", "").lower()
        powered_by = norm_headers.get("x-powered-by", "").lower()

        # Hosting — header-based signals
        hosting: list[str] = []
        if "cf-ray" in norm_headers or "cloudflare" in server_header:
            hosting.append("Cloudflare")
        if "ovh" in server_header or "ovh" in powered_by:
            hosting.append("OVH")
        if "home.pl" in server_header or "home.pl" in powered_by:
            hosting.append("home.pl")
        if "cyberfolks" in server_header or "cyberfolks" in powered_by:
            hosting.append("Cyberfolks")
        if hosting:
            results["Hosting"] = hosting

        # Build extended search corpus: raw HTML + all script srcs + link hrefs
        script_srcs = " ".join(tag.get("src", "") for tag in soup.find_all("script", src=True))
        link_hrefs  = " ".join(tag.get("href", "") for tag in soup.find_all("link", href=True))
        corpus = html + " " + script_srcs + " " + link_hrefs

        for category, techs in cls.SIGNATURES.items():
            found: list[str] = []
            for tech_name, signals in techs:
                for signal in signals:
                    if signal in corpus:
                        found.append(tech_name)
                        break
            if found:
                results[category] = found

        return results

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


def _looks_like_empty_spa(html: str, soup: BeautifulSoup) -> bool:
    """
    Heuristic: if body text content is very short but the HTML contains
    JS framework markers, the page is likely a client-side rendered SPA
    whose content didn't load via httpx.
    """
    if len(html) >= _MIN_MEANINGFUL_HTML_LENGTH:
        return False

    body = soup.find("body")
    if body and len(body.get_text(strip=True)) < 200:
        spa_markers = ["__NEXT_DATA__", "_next/static", "__nuxt", "_nuxt/",
                       "data-reactroot", "__vue", "ng-version", "ng-app",
                       "id=\"app\"", "id=\"root\"", "id=\"__next\""]
        for marker in spa_markers:
            if marker in html:
                return True
    return False


async def _scrape_with_playwright(url: str) -> dict | None:
    """
    Calls the Playwright scraper microservice to render JS-heavy pages.
    Returns {html, load_time_ms, final_url} or None if the service is
    unavailable or the scrape fails.
    """
    if not PLAYWRIGHT_SERVICE_URL:
        return None

    headers = {}
    if PLAYWRIGHT_API_SECRET:
        headers["X-Internal-Secret"] = PLAYWRIGHT_API_SECRET

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                f"{PLAYWRIGHT_SERVICE_URL}/scrape",
                json={"url": url, "timeout": 15},
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                logger.info(
                    "Playwright rendered %s (%d ms, %d chars)",
                    url, data.get("load_time_ms", 0), len(data.get("html", "")),
                )
                return data
            else:
                logger.warning(
                    "Playwright service returned %d for %s: %s",
                    resp.status_code, url, resp.text[:200],
                )
    except Exception as exc:
        logger.warning("Playwright service unreachable for %s: %s", url, exc)

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
        "technologies": {},
        "scraper_used": "httpx",
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

                # ── Playwright fallback for SPA sites ────────────────────
                if _looks_like_empty_spa(html_content, soup):
                    logger.info("Detected empty SPA shell for %s — trying Playwright", url)
                    pw_result = await _scrape_with_playwright(url)
                    if pw_result and len(pw_result.get("html", "")) > len(html_content):
                        html_content = pw_result["html"]
                        soup = BeautifulSoup(html_content, "html.parser")
                        raw_data["scraper_used"] = "playwright"
                        raw_data["load_time"] = round(pw_result["load_time_ms"] / 1000, 2)
                        # Update SSL from final URL after redirects
                        if pw_result.get("final_url", "").startswith("https://"):
                            raw_data["has_ssl"] = True

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

                # Technographic fingerprinting
                technologies = TechDetector.detect(html_content, dict(response.headers), soup)
                raw_data["technologies"] = technologies

                # CMS — keep legacy field populated from tech detection for backwards compat
                cms_list = technologies.get("CMS", [])
                if cms_list:
                    raw_data["cms"] = cms_list[0]

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
