import httpx
from bs4 import BeautifulSoup
import re
import logging
import time

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

async def audit_lead(lead_data: dict) -> dict:
    """
    Audits a business both using its Google Places info and its website logic (if available).
    Returns a unified report dict.
    """
    report = {
        "selling_points": [],
        "has_ssl": False,
        "email": None
    }
    
    # 1. Google Places Data Audit
    rating = lead_data.get("rating")
    reviews_count = lead_data.get("reviews_count")
    website_uri = lead_data.get("website_uri")
    
    if rating is not None and rating < 4.5:
        report["selling_points"].append({
            "type": "google",
            "issue": "rating",
            "message": "Ocena poniżej 4.5 odstrasza klientów."
        })
        
    if reviews_count is not None and reviews_count < 20:
        report["selling_points"].append({
            "type": "google",
            "issue": "reviews_count",
            "message": "Zbyt mała liczba opinii (brak social proof)."
        })
        
    if not website_uri:
        report["selling_points"].append({
            "type": "google",
            "issue": "website",
            "message": "Brak strony www to utrata klientów szukających w Google."
        })
        return report # Skip website audit
        
    # 2. Website Audit
    url = website_uri
    if not url.startswith("http"):
        url = "http://" + url
        
    if url.startswith("https://"):
        report["has_ssl"] = True

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # First, check if the website explicitly supports HTTPS
            if not report["has_ssl"]:
                https_url = url.replace("http://", "https://", 1)
                try:
                    ssl_check_response = await client.get(https_url, headers=headers)
                    if ssl_check_response.status_code < 400:
                        report["has_ssl"] = True
                        url = https_url
                except Exception:
                    pass
            
            response = await client.get(url, headers=headers)
            load_time = time.time() - start_time
            
            # Check SSL one more time after final redirect
            if str(response.url).startswith("https://"):
                report["has_ssl"] = True
                
            if not report["has_ssl"]:
                report["selling_points"].append({
                    "type": "website",
                    "issue": "ssl",
                    "message": "Przeglądarki oznaczają stronę jako niebezpieczną (Brak komunikacji HTTPS/SSL)."
                })
                
            if load_time > 2.0:
                report["selling_points"].append({
                    "type": "website",
                    "issue": "speed",
                    "message": "Strona ładuje się zbyt wolno, co wpływa na wysoki współczynnik odrzuceń."
                })
                
            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Check viewport (RWD)
                viewport = soup.find("meta", attrs={"name": "viewport"})
                if not viewport:
                    report["selling_points"].append({
                        "type": "website",
                        "issue": "rwd",
                        "message": "Strona prawdopodobnie nie jest zoptymalizowana pod urządzenia mobilne (brak RWD)."
                    })
                    
                # Check SEO tags
                title = soup.find("title")
                h1 = soup.find("h1")
                if not title or not h1:
                    report["selling_points"].append({
                        "type": "website",
                        "issue": "seo",
                        "message": "Krytyczne błędy SEO utrudniające pozycjonowanie (Brak Title / H1)."
                    })
                
                # Extract Email
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if href.startswith('mailto:'):
                        email = href.replace('mailto:', '').split('?')[0].strip()
                        if email and EMAIL_REGEX.match(email):
                            report["email"] = email
                            break
                            
                if not report["email"]:
                    text_content = soup.get_text(separator=" ")
                    emails = EMAIL_REGEX.findall(text_content)
                    valid_emails = []
                    for em in emails:
                        if not any(fake in em.lower() for fake in ['example.com', 'email.com', 'yourdomain']):
                            valid_emails.append(em)
                    if valid_emails:
                        report["email"] = valid_emails[0]
                        
    except Exception as e:
        logger.warning(f"Error auditing {url}: {e}")
        report["selling_points"].append({
            "type": "website",
            "issue": "unreachable",
            "message": f"Strona www jest niedostępna lub odrzuca połączenia ({str(e.__class__.__name__)})."
        })
        
    return report
