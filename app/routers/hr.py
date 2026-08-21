from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.user import ExecutiveOut
from app.schemas.pengajuan import PersetujuanQueueCutiOut
from app.schemas.hr import HRDashboardRingkasanOut, HRDashboardPersetujuanOut, HRListCutiKaryawanMendatangOut, HRRekapitulasiOut, HRLogCutiOut, HRRingkasanKaryawanOut, HRTabelKaryawanOut, HRTabelDepartemenOut, HRManajemenJatahCutiRingkasanOut, HRDaftarCutiKaryawanOut
from app.services.hr_service import get_dashboard_ringkasan_hr, get_persetujuan, get_list_cuti_karyawan_mendatang, get_rekapitulasi_cuti, get_cuti_log, get_ringkasan_karyawan, get_tabel_karyawan, get_tabel_departemen, get_manajemen_jatah_cuti, get_daftar_cuti_karyawan
from app.services.persetujuan_service import get_queue_card

router = APIRouter(prefix="/hr", tags=["Human Resources"])


@router.get("", response_model=list[ExecutiveOut])
async def get_all_hr(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.role == "hr"))
    
    return result.scalars().all()


## dashboard
## ringkasan
@router.get("/dashboard", response_model=HRDashboardRingkasanOut)
async def get_dashboard_hr(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_dashboard_ringkasan_hr(db)

## list cuti karyawan mendatang
@router.get("/list-cuti-mendatang", response_model=list[HRListCutiKaryawanMendatangOut])
async def get_list_cuti_mendatang(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_list_cuti_karyawan_mendatang(db)


## persetujuan
## ringkasan persetujuan
@router.get("/persetujuan", response_model=HRDashboardPersetujuanOut)
async def get_dashboard_persetujuan(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_persetujuan(db)

## queue card
@router.get("/queue-card", response_model=list[PersetujuanQueueCutiOut])
async def get_queue(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_queue_card(current_user, db)


## rekap cuti
## rekapitulasi
@router.get("/rekapitulasi", response_model=list[HRRekapitulasiOut])
async def get_rakapitulasi(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_rekapitulasi_cuti(db)

## log cuti
@router.get("/log-cuti", response_model=list[HRLogCutiOut])
async def get_log_cuti(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_cuti_log(db)


# ## data karyawan
# ## ringkasan
@router.get("/ringkasan-karyawan", response_model=HRRingkasanKaryawanOut)
async def get_ringkasan_data_karyawan(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_ringkasan_karyawan(db)

## tabel karyawan
@router.get("/tabel-karyawan", response_model=list[HRTabelKaryawanOut])
async def get_data_tabel_karyawan(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_tabel_karyawan(db)

## tabel departemen
@router.get("/tabel-departemen", response_model=list[HRTabelDepartemenOut])
async def get_data_tabel_departemen(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_tabel_departemen(db)


## manajemen jatah cuti
## ringkasan
@router.get("/manajemen-jatah-cuti", response_model=HRManajemenJatahCutiRingkasanOut)
async def get_data_manajemen_jatah_cuti(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_manajemen_jatah_cuti(db)

## daftar cuti karyawan
@router.get("/daftar-cuti-karyawan", response_model=list[HRDaftarCutiKaryawanOut])
async def get_data_cuti_karyawan(
    current_user: Annotated[User, Depends(require_role("hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_daftar_cuti_karyawan(db)
