from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=schemas.UserSettingsOut)
def get_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    settings = (
        db.query(models.UserSettings)
        .filter(models.UserSettings.user_id == current_user.id)
        .first()
    )
    if settings is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@router.put("", response_model=schemas.UserSettingsOut)
def upsert_settings(
    data: schemas.UserSettingsBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    settings = (
        db.query(models.UserSettings)
        .filter(models.UserSettings.user_id == current_user.id)
        .first()
    )
    if settings is None:
        settings = models.UserSettings(user_id=current_user.id)
        db.add(settings)

    settings.sender_name = data.sender_name
    settings.company_name = data.company_name
    settings.offer_description = data.offer_description
    settings.tone_of_voice = data.tone_of_voice

    settings.email_provider = data.email_provider
    settings.resend_api_key = data.resend_api_key
    settings.smtp_host = data.smtp_host
    settings.smtp_port = data.smtp_port
    settings.smtp_user = data.smtp_user
    settings.smtp_password = data.smtp_password
    settings.smtp_from_email = data.smtp_from_email

    db.commit()
    db.refresh(settings)
    return settings
