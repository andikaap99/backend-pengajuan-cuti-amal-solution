from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.departemen import Departemen


async def get_all_departements(db: AsyncSession) -> list[Departemen]:
    result = await db.execute(select(Departemen))
    return result.scalars().all()


async def get_departement_by_id(db: AsyncSession, departemen_id: int) -> Departemen:
    result = await db.execute(
        select(Departemen).where(Departemen.id_departemen == departemen_id)
    )
    departemen = result.scalar_one_or_none()
    if not departemen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Departemen tidak ditemukan",
        )
    return departemen


async def create_departemen(db: AsyncSession, nama_departemen: str) -> Departemen:
    existing = await db.execute(
        select(Departemen).where(Departemen.nama_departemen == nama_departemen)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nama departemen sudah ada",
        )

    departemen = Departemen(nama_departemen=nama_departemen)
    db.add(departemen)
    await db.commit()
    await db.refresh(departemen)
    return departemen


async def update_departemen(
    db: AsyncSession, departemen_id: int, nama_departemen: str
) -> Departemen:
    departemen = await get_departement_by_id(db, departemen_id)

    if departemen.nama_departemen != nama_departemen:
        existing = await db.execute(
            select(Departemen).where(Departemen.nama_departemen == nama_departemen)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nama departemen sudah ada",
            )

    departemen.nama_departemen = nama_departemen
    await db.commit()
    await db.refresh(departemen)
    return departemen
