"""
routers/saved_searches.py

CRUD endpoints for SavedSearch + manual run trigger.
"""
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, database
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/saved-searches", tags=["saved-searches"])


def _compute_next_run(schedule: str, from_dt: datetime) -> datetime | None:
    """Return the next scheduled run datetime based on schedule string."""
    if schedule == "daily":
        return from_dt + timedelta(days=1)
    if schedule == "weekly":
        return from_dt + timedelta(weeks=1)
    if schedule == "monthly":
        return from_dt + timedelta(days=30)
    return None  # manual — no next run


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[schemas.SavedSearchOut])
def list_saved_searches(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.SavedSearch)
        .filter(models.SavedSearch.user_id == current_user.id)
        .order_by(models.SavedSearch.created_at.desc())
        .all()
    )


# ─── Create ───────────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.SavedSearchOut, status_code=201)
def create_saved_search(
    payload: schemas.SavedSearchCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    next_run = _compute_next_run(payload.schedule, now)
    saved = models.SavedSearch(
        user_id=current_user.id,
        name=payload.name,
        keyword=payload.keyword,
        lat=payload.lat,
        lng=payload.lng,
        radius_km=payload.radius_km,
        limit=payload.limit,
        country_code=payload.country_code,
        filters=payload.filters or {},
        schedule=payload.schedule,
        auto_audit=payload.auto_audit,
        is_active=True,
        next_run_at=next_run,
        created_at=now,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


# ─── Patch (toggle active / change schedule) ──────────────────────────────────

@router.patch("/{search_id}", response_model=schemas.SavedSearchOut)
def patch_saved_search(
    search_id: int,
    payload: schemas.SavedSearchPatch,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    saved = (
        db.query(models.SavedSearch)
        .filter(models.SavedSearch.id == search_id, models.SavedSearch.user_id == current_user.id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Saved search not found")

    if payload.name is not None:
        saved.name = payload.name
    if payload.auto_audit is not None:
        saved.auto_audit = payload.auto_audit
    if payload.is_active is not None:
        saved.is_active = payload.is_active
    if payload.schedule is not None:
        saved.schedule = payload.schedule
        # Recompute next_run when schedule changes
        ref = saved.last_run_at or datetime.now(timezone.utc)
        saved.next_run_at = _compute_next_run(payload.schedule, ref)

    db.commit()
    db.refresh(saved)
    return saved


# ─── Delete ───────────────────────────────────────────────────────────────────

@router.delete("/{search_id}", status_code=204)
def delete_saved_search(
    search_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    saved = (
        db.query(models.SavedSearch)
        .filter(models.SavedSearch.id == search_id, models.SavedSearch.user_id == current_user.id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Saved search not found")
    db.delete(saved)
    db.commit()


# ─── Manual run ───────────────────────────────────────────────────────────────

@router.post("/{search_id}/run", status_code=202)
def run_saved_search(
    search_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Dispatch the scan task immediately and return task_id for polling."""
    saved = (
        db.query(models.SavedSearch)
        .filter(models.SavedSearch.id == search_id, models.SavedSearch.user_id == current_user.id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Saved search not found")

    from ..tasks import scan_places_task  # imported here to avoid circular import

    filters = saved.filters or {}
    task = scan_places_task.delay(
        user_id=current_user.id,
        keyword=saved.keyword,
        lat=saved.lat,
        lng=saved.lng,
        radius_km=saved.radius_km,
        limit=saved.limit,
        country_code=saved.country_code,
        filters=filters,
        auto_audit=saved.auto_audit,
        saved_search_id=saved.id,
    )
    return {"task_id": task.id}
