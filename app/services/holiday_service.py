from datetime import date
from fastapi import HTTPException
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holiday import Holiday
from app.schemas.holiday import NextCutiBersamaOut
from app.models.log_penambahan_kerja import LogPenambahanKerja
from app.models.log_penambahan_kerja_date import LogPenambahanKerjaDate
from datetime import timedelta


async def sync_holidays(year: int, db: AsyncSession) -> int:
    url = f"https://api.kemendesa.link/libur-nasional/api/holidays/{year}.json"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Gagal mengambil data dari API libur nasional")

        data = response.json()

    if not data.get("data"):
        raise HTTPException(status_code=502, detail="Data libur tidak ditemukan")

    holidays = data["data"]
    inserted = 0

    for item in holidays:
        if not item.get("is_cuti_bersama", False):
            continue

        tanggal = date.fromisoformat(item["date"])

        existing = await db.execute(
            select(Holiday).where(Holiday.tanggal == tanggal)
        )
        if existing.scalar_one_or_none():
            continue

        holiday = Holiday(
            nama_libur=item["name"],
            tanggal=tanggal,
            is_cuti_bersama=item.get("is_cuti_bersama", True),
            tahun=year,
        )
        db.add(holiday)
        inserted += 1

    await db.commit()

    return inserted


async def get_next_cuti_bersama(db: AsyncSession) -> NextCutiBersamaOut | None:
    today = date.today()

    result = await db.execute(
        select(Holiday)
        .where(Holiday.is_cuti_bersama == True, Holiday.tanggal >= today)
        .order_by(Holiday.tanggal.asc())
    )
    holidays = result.scalars().all()

    if not holidays:
        return None

    tanggal_mulai = holidays[0].tanggal
    tanggal_selesai = holidays[0].tanggal
    nama_libur = holidays[0].nama_libur

    for h in holidays[1:]:
        if h.tanggal == tanggal_selesai + timedelta(days=1):
            tanggal_selesai = h.tanggal
        else:
            break

    total_hari = (tanggal_selesai - tanggal_mulai).days + 1
    sisa_hari = (tanggal_mulai - today).days

    return NextCutiBersamaOut(
        nama_libur=nama_libur,
        tanggal_mulai=tanggal_mulai,
        tanggal_selesai=tanggal_selesai,
        total_hari=total_hari,
    )

async def get_reserved_cuti_bersama_days(user_id: int, db: AsyncSession) -> int:
    today = date.today()

    result = await db.execute(
        select(Holiday.tanggal).where(
            Holiday.is_cuti_bersama == True,
            Holiday.tanggal >= today,
            Holiday.sudah_dikurangi == False,
        )
    )

    pending_dates = {row[0] for row in result.all()}
    if not pending_dates:
        
        return 0

    result_kerja = await db.execute(
        select(LogPenambahanKerjaDate.tanggal)
        .join(LogPenambahanKerja, LogPenambahanKerja.id_pengajuan_kerja == LogPenambahanKerjaDate.id_pengajuan_kerja)
        .where(
            LogPenambahanKerja.id_user == user_id,
            LogPenambahanKerja.status.in_(["disetujui_hr", "disetujui_direktur"]),
        )
    )
    kerja_dates = {row[0] for row in result_kerja.all()}

    return len(pending_dates - kerja_dates)