from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.user import ExecutiveOut
from app.schemas.pengajuan import PersetujuanQueueCutiOut
from app.schemas.hr import HRDashboardRingkasanOut, HRDashboardPersetujuanOut, HRListCutiKaryawanMendatangOut, HRRekapitulasiOut, HRLogCutiOut, HRRingkasanKaryawanOut, HRTabelKaryawanOut, HRTabelDepartemenOut, HRManajemenJatahCutiRingkasanOut, HRDaftarCutiKaryawanOut, EditKaryawanRequest, EditKaryawanResponse
from app.services.hr_service import get_dashboard_ringkasan_hr, get_persetujuan, get_list_cuti_karyawan_mendatang, get_rekapitulasi_cuti, get_cuti_log, get_ringkasan_karyawan, get_tabel_karyawan, get_tabel_departemen, get_manajemen_jatah_cuti, get_daftar_cuti_karyawan, edit_karyawan
from app.services.export_excel_service import export_cuti_excel
from app.services.tambah_cuti_service import tambah_sisa_cuti
from app.schemas.log_cuti_ekstra import LogCutiEkstraCreate, LogCutiEkstraOut

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
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_dashboard_ringkasan_hr(db, current_user.role)

## list cuti karyawan mendatang
@router.get("/list-cuti-mendatang", response_model=list[HRListCutiKaryawanMendatangOut])
async def get_list_cuti_mendatang(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_list_cuti_karyawan_mendatang(db)


## persetujuan
## ringkasan persetujuan
@router.get("/persetujuan", response_model=HRDashboardPersetujuanOut)
async def get_dashboard_persetujuan(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_persetujuan(db)


## rekap cuti
## rekapitulasi
@router.get("/rekapitulasi", response_model=list[HRRekapitulasiOut])
async def get_rakapitulasi(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_rekapitulasi_cuti(db)

## log cuti
@router.get("/log-cuti", response_model=list[HRLogCutiOut])
async def get_log_cuti(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_cuti_log(db)


# ## data karyawan
# ## ringkasan
@router.get("/ringkasan-karyawan", response_model=HRRingkasanKaryawanOut)
async def get_ringkasan_data_karyawan(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_ringkasan_karyawan(db)

## tabel karyawan
@router.get("/tabel-karyawan", response_model=list[HRTabelKaryawanOut])
async def get_data_tabel_karyawan(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_tabel_karyawan(db)

## tabel departemen
@router.get("/tabel-departemen", response_model=list[HRTabelDepartemenOut])
async def get_data_tabel_departemen(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_tabel_departemen(db)


## manajemen jatah cuti
## ringkasan
@router.get("/manajemen-jatah-cuti", response_model=HRManajemenJatahCutiRingkasanOut)
async def get_data_manajemen_jatah_cuti(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_manajemen_jatah_cuti(db)

## daftar cuti karyawan
@router.get("/daftar-cuti-karyawan", response_model=list[HRDaftarCutiKaryawanOut])
async def get_data_cuti_karyawan(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_daftar_cuti_karyawan(db)


## export excel cuti
@router.get("/export-cuti")
async def export_cuti(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    year: Optional[int] = Query(default=None, description="Tahun periode cuti"),
):
    target_year = year if year else date.today().year
    file_bytes = await export_cuti_excel(target_year, db)

    filename = f"rekap_cuti_{target_year}.xlsx"

    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


## tambah sisa cuti
@router.post("/tambah-cuti", response_model=LogCutiEkstraOut)
async def tambah_cuti(
    data: LogCutiEkstraCreate,
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await tambah_sisa_cuti(data.id_user, data.jumlah_hari, data.keterangan, current_user.id_user, db)


## edit karyawan
@router.put("/karyawan/{user_id}", response_model=EditKaryawanResponse)
async def update_karyawan(
    user_id: int, data: EditKaryawanRequest,
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    update_date = data.model_dump(exclude_unset=True)
    message = await edit_karyawan(user_id, update_date, db)

    return EditKaryawanResponse(detail=message)

