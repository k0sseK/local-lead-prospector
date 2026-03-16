"""
Playwright Scraper Microservice

Headless Chromium browser for rendering JavaScript-heavy pages (SPAs).
Called by the main backend as a fallback when httpx returns thin HTML.
"""

import os
import time
import logging

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, HttpUrl
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_SECRET = os.getenv("API_SECRET", "")

app = FastAPI(title="Playwright Scraper", docs_url=None, redoc_url=None)

# ── Shared browser instance ──────────────────────────────────────────────────
_browser = None


async def _get_browser():
    global _browser
    if _browser is None or not _browser.is_connected():
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("Chromium browser launched")
    return _browser


# ── Request / Response schemas ───────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    url: HttpUrl
    timeout: int = 15  # seconds


class ScrapeResponse(BaseModel):
    html: str
    load_time_ms: int
    final_url: str
    status_code: int | None = None


# ── Auth dependency ──────────────────────────────────────────────────────────

def _verify_secret(x_internal_secret: str | None = Header(None)):
    if API_SECRET and x_internal_secret != API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid internal secret")


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/scrape", response_model=ScrapeResponse, dependencies=[])
async def scrape(req: ScrapeRequest, x_internal_secret: str | None = Header(None)):
    _verify_secret(x_internal_secret)

    browser = await _get_browser()
    context = None
    try:
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720},
            java_script_enabled=True,
        )
        page = await context.new_page()

        # Block heavy resources — we only need the rendered DOM
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg,webp,ico,woff,woff2,ttf,eot,mp4,webm,ogg,mp3}",
            lambda route: route.abort(),
        )

        start = time.monotonic()
        response = await page.goto(
            str(req.url),
            wait_until="networkidle",
            timeout=req.timeout * 1000,
        )
        # Extra wait for late-binding JS frameworks (React hydration, etc.)
        await page.wait_for_timeout(1500)

        html = await page.content()
        elapsed_ms = int((time.monotonic() - start) * 1000)

        return ScrapeResponse(
            html=html,
            load_time_ms=elapsed_ms,
            final_url=str(page.url),
            status_code=response.status if response else None,
        )

    except Exception as exc:
        logger.warning("Scrape failed for %s: %s", req.url, exc)
        raise HTTPException(status_code=422, detail=f"Scrape failed: {exc}")
    finally:
        if context:
            await context.close()
