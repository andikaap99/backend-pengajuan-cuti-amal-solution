from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.log_cuti import PengajuanCutiCreate, PengajuanCutiOut, RiwayatCutiOut, EmpDashboardPengajuanOngoingOut, EmpDashboardRingkasanOut
from app.services.cuti_service import create_pengajuan_cuti, get_my_cuti, get_my_ongoing_cuti, get_my_ringkasan_cuti
from app.services.minus_cuti_service import kurangi_jatah_cuti
from app.services.kalender_service import get_my_kalender_cuti, get_kalender_cuti_tim
from app.schemas.kalender import CutiSayaOut 
from app.schemas.user import ActivityOut
from app.services.activity_service import get_recent_activities

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
@router.get("/cuti/ongoing", response_model=list[EmpDashboardPengajuanOngoingOut])
async def get_all_cuti_ongoing(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_my_ongoing_cuti(current_user.id_user, db)


## routes liat ringkasan cuti dashboard
@router.get("/cuti/ringkasan", response_model=EmpDashboardRingkasanOut)
async def get_ringkasan_cuti(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_my_ringkasan_cuti(current_user.id_user, db)


@router.get("/kalender-cuti-saya", response_model=list[CutiSayaOut])
async def get_kalender(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    return await get_my_kalender_cuti(current_user.id_user, db)


@router.get("/kalender-cuti-tim", response_model=list[CutiSayaOut])
async def get_kalender_tim(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    return await get_kalender_cuti_tim(current_user.id_user, db)


@router.get("/activities", response_model=list[ActivityOut])
async def get_activities_recent(
    current_user: Annotated[User, Depends(require_role("karyawan", "pm", "hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
): 

    return await get_recent_activities(current_user.id_user, db)