import httpx
from bs4 import BeautifulSoup
import re
import logging
import time

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

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

    # 2. Website Audit
    url = website_uri
    if not url.startswith("http"):
        url = "http://" + url

    if url.startswith("https://"):
        raw_data["has_ssl"] = True

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        start_time = time.time()

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # Check if the website explicitly supports HTTPS
            if not raw_data["has_ssl"]:
                https_url = url.replace("http://", "https://", 1)
                try:
                    ssl_check_response = await client.get(https_url, headers=headers)
                    if ssl_check_response.status_code < 400:
                        raw_data["has_ssl"] = True
                        url = https_url
                except Exception:
                    pass

            response = await client.get(url, headers=headers)
            raw_data["load_time"] = round(time.time() - start_time, 2)
            raw_data["website_reachable"] = True

            # Check SSL one more time after final redirect
            if str(response.url).startswith("https://"):
                raw_data["has_ssl"] = True

            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")

                # Check viewport (RWD)
                viewport = soup.find("meta", attrs={"name": "viewport"})
                raw_data["has_viewport"] = bool(viewport)
                if not viewport:
                    raw_data["missing_seo_tags"].append("viewport")

                # Check SEO tags
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
                    
                # Detect CMS
                if "wp-content" in html_content:
                    raw_data["cms"] = "WordPress"
                elif "_next" in html_content:
                    raw_data["cms"] = "Next.js"
                elif "cdn.shopify" in html_content:
                    raw_data["cms"] = "Shopify"

                # Extract Email and Social Media
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    
                    # Social media checks
                    href_lower = href.lower()
                    if "facebook.com" in href_lower and "facebook" not in raw_data["social_media"]:
                        raw_data["social_media"].append("facebook")
                    elif "instagram.com" in href_lower and "instagram" not in raw_data["social_media"]:
                        raw_data["social_media"].append("instagram")
                    elif "linkedin.com" in href_lower and "linkedin" not in raw_data["social_media"]:
                        raw_data["social_media"].append("linkedin")
                        
                    if href.startswith('mailto:') and not raw_data["email"]:
                        email = href.replace('mailto:', '').split('?')[0].strip()
                        if email and EMAIL_REGEX.match(email):
                            raw_data["email"] = email

                if not raw_data["email"]:
                    text_content = soup.get_text(separator=" ")
                    emails = EMAIL_REGEX.findall(text_content)
                    valid_emails = []
                    for em in emails:
                        if not any(fake in em.lower() for fake in ['example.com', 'email.com', 'yourdomain']):
                            valid_emails.append(em)
                    if valid_emails:
                        raw_data["email"] = valid_emails[0]

    except Exception as e:
        logger.warning(f"Error auditing {url}: {e}")
        raw_data["website_reachable"] = False

    return raw_data
