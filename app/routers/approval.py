### ==kode baru==
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, require_role
from app.db import get_db
from app.models.log_cuti import LogCuti
from app.models.log_cuti_approval_pm import LogCutiApprovalPM
from app.models.log_penambahan_kerja_approval_pm import LogPenambahanKerjaApprovalPM
from app.models.user import User
from app.schemas.approval import ApprovalRequest, ApprovalResponse
from app.schemas.log_cuti import ApprovalPMDetail
from app.schemas.pengajuan import PersetujuanQueueCutiOut
from app.schemas.penambahan_kerja import PenambahanKerjaQueueOut, PenambahanKerjaApprovalRequest, PenambahanKerjaApprovalResponse, PenambahanKerjaApprovalPMDetail
from app.services.approval_service import process_approval, get_queue_card
from app.services.penambahan_kerja_service import get_penambahan_kerja_queue, get_penambahan_kerja_queue_hr, get_penambahan_kerja_queue_direktur, process_penambahan_kerja, process_penambahan_kerja_hr, process_penambahan_kerja_direktur

router = APIRouter(prefix="/approval", tags=["Approval"])


## queue card
@router.get("/approval-queue", response_model=list[PersetujuanQueueCutiOut])
async def get_queue(
    current_user: Annotated[User, Depends(require_role("pm", "hr_manager", "direktur", "staff_hr"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_queue_card(current_user, db)

## approval
@router.post("/approval{log_cuti_id}", response_model=ApprovalResponse)
async def approve_or_decline(
    log_cuti_id: int, data: ApprovalRequest,
    current_user: Annotated[User, Depends(require_role("pm", "hr_manager", "direktur", "staff_hr"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks
):

    return await process_approval(log_cuti_id, current_user, data, db, background_tasks)


## detail approval PM untuk satu pengajuan cuti
@router.get("/approval-pm-detail/{log_cuti_id}", response_model=list[ApprovalPMDetail])
async def get_approval_pm_detail(
    log_cuti_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(LogCutiApprovalPM, User.nama).join(User, LogCutiApprovalPM.id_pm == User.id_user).where(
            LogCutiApprovalPM.id_log_cuti == log_cuti_id
        )
    )
    rows = result.all()

    return [
        ApprovalPMDetail(
            nama_pm=row[1],
            status=row[0].status,
            processed_at=row[0].processed_at,
        )
        for row in rows
    ]


## detail approval PM untuk satu pengajuan penambahan kerja
@router.get("/penambahan-kerja-pm-detail/{log_id}", response_model=list[PenambahanKerjaApprovalPMDetail])
async def get_approval_pm_detail_penambahan_kerja(
    log_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(LogPenambahanKerjaApprovalPM, User.nama).join(User, LogPenambahanKerjaApprovalPM.id_pm == User.id_user).where(
            LogPenambahanKerjaApprovalPM.id_pengajuan_kerja == log_id
        )
    )
    rows = result.all()

    return [
        PenambahanKerjaApprovalPMDetail(
            nama_pm=row[1],
            status=row[0].status,
            processed_at=row[0].processed_at,
        )
        for row in rows
    ]


## queue penambahan kerja (PM, HR, Direktur)
@router.get("/penambahan-kerja-queue")
async def get_queue_penambahan_kerja(
    current_user: Annotated[User, Depends(require_role("pm", "hr_manager", "staff_hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role == "direktur":
        return await get_penambahan_kerja_queue_direktur(db, current_user.id_user)
    if current_user.role in ("hr_manager", "staff_hr"):
        return await get_penambahan_kerja_queue_hr(db, current_user.id_user)

    return await get_penambahan_kerja_queue(current_user.id_user, db)


## approval penambahan kerja (PM, HR, Direktur)
@router.post("/penambahan-kerja/{log_id}", response_model=PenambahanKerjaApprovalResponse)
async def approve_or_decline_penambahan_kerja(
    log_id: int, data: PenambahanKerjaApprovalRequest,
    current_user: Annotated[User, Depends(require_role("pm", "hr_manager", "staff_hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks
):
    if current_user.role == "direktur":
        return await process_penambahan_kerja_direktur(log_id, current_user, data.action, data.alasan, db, background_tasks)
    if current_user.role in ["hr_manager", "staff_hr"]:
        return await process_penambahan_kerja_hr(log_id, current_user, data.action, data.alasan, db, background_tasks)

    return await process_penambahan_kerja(log_id, current_user.id_user, data.action, data.alasan, db, background_tasks)
