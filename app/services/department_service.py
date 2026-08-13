from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.departemen import Departemen


async def get_all_departements(db: AsyncSession) -> list[Departemen]:
    result = await db.execute(select(Departemen))
    return result.scalars().all()
