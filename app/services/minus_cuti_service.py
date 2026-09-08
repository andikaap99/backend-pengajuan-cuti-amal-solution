from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.tambah_cuti_service import konsumsi_cuti


## fungsi mengurangi jatah cuti
async def kurangi_jatah_cuti(user_id: int, durasi: int, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    await konsumsi_cuti(user, durasi, db)
    await db.flush()
