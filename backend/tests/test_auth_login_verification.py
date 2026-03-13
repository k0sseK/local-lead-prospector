import pytest
from fastapi.testclient import TestClient

from app import models
from app.database import get_db
from app.dependencies import hash_password
from app.main import app
from app.templates.verification_email import get_verification_email_html

@pytest.fixture()
def client(db, monkeypatch):
    monkeypatch.setenv("DISABLE_TURNSTILE", "1")

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def _create_user(db, *, email: str, password: str, is_verified: bool):
    user = models.User(
        email=email,
        hashed_password=hash_password(password),
        role="user",
        plan="free",
        is_verified=is_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_rejects_unverified_user(client, db):
    email = "pending@test.local"
    password = "SuperSecretPass123"
    _create_user(db, email=email, password=password, is_verified=False)

    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
            "cf_turnstile_response": "test-token",
        },
    )

    assert response.status_code == 403
    assert "zweryfikowane" in response.json()["detail"].lower()


def test_login_allows_verified_user(client, db):
    email = "verified@test.local"
    password = "SuperSecretPass123"
    _create_user(db, email=email, password=password, is_verified=True)

    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
            "cf_turnstile_response": "test-token",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body.get("access_token"), str)
    assert body["access_token"]


def test_verification_email_template_includes_action_link_and_cta():
    verify_link = "https://example.com/auth/verify?token=abc123"

    html = get_verification_email_html(verify_link)

    assert "Potwierdź e-mail" in html
    assert verify_link in html
    assert f'href="{verify_link}"' in html


def test_verification_email_template_includes_safety_and_branding_copy():
    html = get_verification_email_html("https://example.com/auth/verify?token=xyz")

    assert "znajdzfirmy" in html
    assert "Bez aktywacji" in html
    assert "Przycisk nie działa?" in html
