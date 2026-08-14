from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.user import ExecutiveOut

router = APIRouter(prefix="/direktur", tags=["Direktur"])


@router.get("", response_model=list[ExecutiveOut])
async def get_all_direktur(
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.role == "direktur"))
    return result.scalars().all()
