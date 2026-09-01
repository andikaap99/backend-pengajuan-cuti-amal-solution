from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.departemen import DepartemenCreate, DepartemenOut, DepartemenUpdate
from app.services.department_service import (
    create_departemen,
    get_all_departements,
    update_departemen,
)

router = APIRouter(prefix="/departemen", tags=["Departemen"])


@router.get("", response_model=list[DepartemenOut])
async def get_departements(db: Annotated[AsyncSession, Depends(get_db)]):
    return await get_all_departements(db)


@router.post("", response_model=DepartemenOut, status_code=201)
async def create_new_departemen(
    body: DepartemenCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
):
    return await create_departemen(db, body.nama_departemen)


@router.put("/{departemen_id}", response_model=DepartemenOut)
async def edit_departemen(
    departemen_id: int,
    body: DepartemenUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
):
    return await update_departemen(db, departemen_id, body.nama_departemen)
