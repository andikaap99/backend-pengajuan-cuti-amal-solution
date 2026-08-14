from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.log_cuti import LogCutiCreate, LogCutiOut, RiwayatCutiOut
from app.services.leave_service import create_leave_request, get_my_leaves

router = APIRouter(prefix="/karyawan", tags=["Karyawan"])


@router.post("/cuti", response_model=LogCutiOut)
async def submit_leave(
    data: LogCutiCreate,
    current_user: Annotated[User, Depends(require_role("karyawan", "hr", "pm"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await create_leave_request(data, current_user.id_user, db)

@router.get("/cuti", response_model=list[RiwayatCutiOut])
async def get_my_leave_history(
    current_user: Annotated[User, Depends(require_role("karyawan", "hr", "pm"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_my_leaves(current_user.id_user, db)