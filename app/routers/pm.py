from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.user import ExecutiveOut
from app.schemas.pm import PMPersetujuanRingkasanTimOut, PMPersetujuanQueueCutiOut
from app.services.pm_service import get_ringkasan_tim, get_queue_card

router = APIRouter(prefix="/pm", tags=["Project Manager"])


@router.get("", response_model=list[ExecutiveOut])
async def get_all_pm(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(User).where(User.role == "pm"))
    return result.scalars().all()


@router.get("/ringkasan-tim", response_model=PMPersetujuanRingkasanTimOut)
async def get_ringkasan_tim_endpoint(
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return await get_ringkasan_tim(current_user.id_user, db)


@router.get("/queue-card", response_model=list[PMPersetujuanQueueCutiOut])
async def get_queue_card_endpoint(
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return await get_queue_card(current_user.id_user, db)
