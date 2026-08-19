from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User



## fungsi mengurangi jatah cuti
async def kurangi_jatah_cuti(user_id: int, durasi: int, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    if user.sisa_cuti < durasi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sisa cuti tidak cukup")

    user.sisa_cuti -= durasi
    db.add(user)
    await db.flush()