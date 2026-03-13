from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import os
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

router = APIRouter(prefix="/api/auth", tags=["auth"])

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


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    verify_turnstile(user_in.cf_turnstile_response)
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
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
            "subject": "Reset hasła - Local Lead Prospector",
            "html": f"<p>Kliknij poniższy link, aby zresetować hasło:</p><p><a href='{reset_link}'>{reset_link}</a></p><p>Link straci ważność za 15 minut.</p>"
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
