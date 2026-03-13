from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session

import os
import secrets
import resend
import httpx
from jose import JWTError, jwt

from .. import models, schemas
from ..database import get_db
from ..dependencies import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    create_password_reset_token,
    SECRET_KEY,
    ALGORITHM
)
from ..templates.forgot_password_email import get_forgot_password_email_html

router = APIRouter(prefix="/api/auth", tags=["auth"])

from ..main import limiter

def send_verification_email(email: str, token: str):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Wysyłam link aktywacyjny na {email}: https://znajdzfirmy.pl/verify?token={token}")


def verify_turnstile(token: str | None):
    secret = os.getenv("TURNSTILE_SECRET_KEY")
    if not secret:
        return
    if not token:
        raise HTTPException(status_code=403, detail="Brak tokenu weryfikacji.")
    try:
        res = httpx.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": secret, "response": token},
            timeout=10.0
        )
        if not res.json().get("success"):
            raise HTTPException(status_code=403, detail="Weryfikacja Cloudflare Turnstile nie powiodła się.")
    except httpx.RequestError:
        raise HTTPException(status_code=403, detail="Błąd połączenia z serwerem weryfikacji.")


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/day")
def register(request: Request, user_in: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    verify_turnstile(user_in.cf_turnstile_response)
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    token_str = secrets.token_urlsafe(32)

    user = models.User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role="user",
        is_verified=False,
        verification_token=token_str,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    background_tasks.add_task(send_verification_email, user.email, token_str)

    return {"message": "Konto utworzone. Sprawdź e-mail i odbierz link weryfikacyjny."}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Nieprawidłowy lub wygasły token weryfikacji.")
        
    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Konto zweryfikowane pomyślnie"}


@router.post("/login", response_model=schemas.Token)
def login(request: Request, user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    verify_turnstile(user_in.cf_turnstile_response)
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
def forgot_password(req: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    success_msg = {"message": "Jeśli konto istnieje, wysłaliśmy link na Twój adres e-mail."}
    
    if not user:
        return success_msg

    token = create_password_reset_token(user)
    
    try:
        resend.api_key = os.getenv("RESEND_API_KEY")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/auth/reset-password?token={token}"
        
        params = {
            "from": os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"),
            "to": [req.email],
            "subject": "Reset hasła w znajdzfirmy.pl",
            "html": get_forgot_password_email_html(reset_link)
        }
        resend.Emails.send(params)
    except Exception as e:
        print(f"Failed to send reset email: {str(e)}")
        
    return success_msg


@router.post("/reset-password")
def reset_password(req: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(req.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        token_hash = payload.get("hash")
        
        if not user_id or token_type != "password_reset":
            raise HTTPException(status_code=400, detail="Nieprawidłowy lub wygasły token.")
            
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=400, detail="Nieprawidłowy lub wygasły token.")
            
        current_hash_slice = user.hashed_password[-10:] if user.hashed_password else ""
        if token_hash != current_hash_slice:
            raise HTTPException(status_code=400, detail="Token został już użyty lub hasło zostało zmienione.")
            
        user.hashed_password = hash_password(req.new_password)
        db.commit()
        
        return {"message": "Hasło zostało pomyślnie zmienione."}
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Nieprawidłowy lub wygasły token.")
