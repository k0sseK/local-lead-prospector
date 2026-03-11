from typing import List

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
    settings.default_email_language = data.default_email_language

    db.commit()
    db.refresh(settings)
    return settings


# ─── Audit Templates ──────────────────────────────────────────────────────────

@router.get("/templates", response_model=List[schemas.AuditTemplateOut])
def list_templates(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.AuditTemplate)
        .filter(models.AuditTemplate.user_id == current_user.id)
        .order_by(models.AuditTemplate.created_at)
        .all()
    )


@router.post("/templates", response_model=schemas.AuditTemplateOut, status_code=201)
def create_template(
    data: schemas.AuditTemplateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if data.is_default:
        # Wyczyść poprzedni domyślny
        db.query(models.AuditTemplate).filter(
            models.AuditTemplate.user_id == current_user.id,
            models.AuditTemplate.is_default == True,
        ).update({"is_default": False})

    template = models.AuditTemplate(
        user_id=current_user.id,
        name=data.name,
        prompt=data.prompt,
        is_default=data.is_default,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/templates/{template_id}", response_model=schemas.AuditTemplateOut)
def update_template(
    template_id: int,
    data: schemas.AuditTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    template = (
        db.query(models.AuditTemplate)
        .filter(
            models.AuditTemplate.id == template_id,
            models.AuditTemplate.user_id == current_user.id,
        )
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Szablon nie znaleziony.")

    if data.is_default is True:
        db.query(models.AuditTemplate).filter(
            models.AuditTemplate.user_id == current_user.id,
            models.AuditTemplate.is_default == True,
        ).update({"is_default": False})

    if data.name is not None:
        template.name = data.name
    if data.prompt is not None:
        template.prompt = data.prompt
    if data.is_default is not None:
        template.is_default = data.is_default

    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    deleted = (
        db.query(models.AuditTemplate)
        .filter(
            models.AuditTemplate.id == template_id,
            models.AuditTemplate.user_id == current_user.id,
        )
        .delete()
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Szablon nie znaleziony.")
    db.commit()
