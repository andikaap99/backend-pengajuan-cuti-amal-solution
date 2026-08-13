from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.departemen import DepartemenOut
from app.services.department_service import get_all_departements

router = APIRouter(prefix="/departemen", tags=["Departemen"])


@router.get("", response_model=list[DepartemenOut])
async def get_departements(db: Annotated[AsyncSession, Depends(get_db)]):
    return await get_all_departements(db)
