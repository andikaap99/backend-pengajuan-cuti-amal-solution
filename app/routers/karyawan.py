from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.log_cuti import PengajuanCutiCreate, PengajuanCutiOut, RiwayatCutiOut, PengajuanOngoingOut, RingkasanCutiOut
from app.services.leave_service import create_pengajuan_cuti, get_my_cuti, get_my_ongoing_cuti, get_my_ringkasan_cuti

router = APIRouter(prefix="/karyawan", tags=["Karyawan"])


## routes pengajuan cuti
@router.post("/cuti", response_model=PengajuanCutiOut)
async def submit_cuti(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    data: PengajuanCutiCreate
):
    
    return await create_pengajuan_cuti(data, current_user.id_user, db)


## routes liat riwayat cuti all
@router.get("/cuti", response_model=list[RiwayatCutiOut])
async def get_all_cuti(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    return await get_my_cuti(current_user.id_user, db)


## routes liat riwayat cuti yang ongoing (belum acc)
@router.get("/cuti/ongoing", response_model=list[PengajuanOngoingOut])
async def get_all_cuti_ongoing(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_my_ongoing_cuti(current_user.id_user, db)


## routes liat ringkasan cuti dashboard
@router.get("/cuti/ringkasan", response_model=RingkasanCutiOut)
async def get_ringkasan_cuti(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_my_ringkasan_cuti(current_user.id_user, db)