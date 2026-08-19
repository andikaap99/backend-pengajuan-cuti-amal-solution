from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.user import ExecutiveOut
from app.schemas.pm import PMDashboardRingkasanOut, PMDashboardTimOut, PMPersetujuanRingkasanTimOut, PMPersetujuanQueueCutiOut, PMHistoryPersetujuanOut, PMRekapCutiRingkasanOut, PMRekapCutiDetailJatah
from app.services.pm_service import get_dashboard_ringkasan, get_dashboard_tim, get_ringkasan_tim, get_queue_card, get_history_cuti_tim, get_rekap_cuti_ringkasan, get_rekap_cuti_detail

router = APIRouter(prefix="/pm", tags=["Project Manager"])


@router.get("", response_model=list[ExecutiveOut])
async def get_all_pm(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(User).where(User.role == "pm"))

    return result.scalars().all()


## persetujuan
## ringkasan tim
@router.get("/ringkasan-tim", response_model=PMPersetujuanRingkasanTimOut)
async def get_ringkasan_tim_endpoint(
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    return await get_ringkasan_tim(current_user.id_user, db)


## queue card
@router.get("/queue-card", response_model=list[PMPersetujuanQueueCutiOut])
async def get_queue_card_endpoint(
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    return await get_queue_card(current_user.id_user, db)


## history pengajuan tim
@router.get("/history-cuti-tim", response_model=list[PMHistoryPersetujuanOut])
async def get_cuti_tim_history(
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_history_cuti_tim(current_user.id_user, db)



# ### rekap cuti ringkasan tim
# @router.get("/rekap-cuti-ringkasan", response_model=PMRekapCutiRingkasanOut)
# async def get_rekap_cuti_ringkasan_endpoint(
#     current_user: Annotated[User, Depends(require_role("pm"))],
#     db: Annotated[AsyncSession, Depends(get_db)]
# ):
#     return await get_rekap_cuti_ringkasan(current_user.id_user, db)


# ### rekap cuti detail jatah per anggota tim
# @router.get("/rekap-cuti-detail", response_model=list[PMRekapCutiDetailJatah])
# async def get_rekap_cuti_detail_endpoint(
#     current_user: Annotated[User, Depends(require_role("pm"))],
#     db: Annotated[AsyncSession, Depends(get_db)]
# ):
#     return await get_rekap_cuti_detail(current_user.id_user, db)


### dashboard ringkasan PM
## dashboard ringkasan pm
@router.get("/dashboard", response_model=PMDashboardRingkasanOut)
async def get_ringkasan_dashboard(
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_dashboard_ringkasan(current_user.id_user, db)

## cuti anggota tim
@router.get("/dashboard-tim", response_model=list[PMDashboardTimOut])
async def get_tim_dashboard(
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_dashboard_tim(current_user.id_user, db)