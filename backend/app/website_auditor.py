import httpx
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

async def audit_website(url: str) -> dict:
    """
    Audits a website for SSL and emails.
    """
    result = {
        "has_ssl": False,
        "email": None
    }
    
    if not url:
        return result
        
    # Ensure URL has protocol
    if not url.startswith("http"):
        url = "http://" + url  # start with HTTP, allow redirect to HTTPS if exists

    if url.startswith("https://"):
        result["has_ssl"] = True
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # First, check if the website explicitly supports HTTPS even if the provided URL is HTTP.
            if not result["has_ssl"]:
                https_url = url.replace("http://", "https://", 1)
                try:
                    ssl_check_response = await client.get(https_url, headers=headers)
                    if ssl_check_response.status_code < 400:
                        result["has_ssl"] = True
                        url = https_url # continue auditing with the secure URL
                except Exception:
                    pass # ignore HTTPS upgrade failure

            response = await client.get(url, headers=headers)
            
            # Additional check checking final URL just in case of redirect
            if str(response.url).startswith("https://"):
                result["has_ssl"] = True
            
            if response.status_code == 200:
                html_content = response.text
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Check mailto: links first, they are more reliable
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if href.startswith('mailto:'):
                        email = href.replace('mailto:', '').split('?')[0].strip()
                        if email and EMAIL_REGEX.match(email):
                            result["email"] = email
                            return result
                
                # Fallback: search in text
                text_content = soup.get_text(separator=" ")
                emails = EMAIL_REGEX.findall(text_content)
                
                # Filter out obvious fake emails common in websites
                valid_emails = []
                for em in emails:
                    em_lower = em.lower()
                    if not any(fake in em_lower for fake in ['example.com', 'email.com', 'yourdomain']):
                        valid_emails.append(em)
                        
                if valid_emails:
                    # Take the first one that looks okay
                    result["email"] = valid_emails[0]
                    
    except Exception as e:
        logger.warning(f"Error auditing {url}: {e}")
        
    return result
