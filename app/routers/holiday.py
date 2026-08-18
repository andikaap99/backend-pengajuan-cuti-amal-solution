from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.db import get_db
from app.models.user import User
from app.schemas.holiday import NextCutiBersamaOut
from app.services.holiday_service import sync_holidays, get_next_cuti_bersama

router = APIRouter(prefix="/holidays", tags=["Holidays"])


@router.post("/sync")
async def sync_holidays_endpoint(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    year = date.today().year
    inserted = await sync_holidays(year, db)
    return {"detail": f"Berhasil sync {inserted} data libur tahun {year}"}


@router.get("/next", response_model=Optional[NextCutiBersamaOut])
async def get_next_cuti_bersama_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_next_cuti_bersama(db)
