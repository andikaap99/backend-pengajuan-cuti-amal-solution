from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db import get_db
from app.models.user import User
from app.schemas.approval import ApprovalRequest, ApprovalResponse
from app.services.approval_service import process_approval, get_queue_card
from app.schemas.pengajuan import PersetujuanQueueCutiOut
from app.schemas.penambahan_kerja import PenambahanKerjaQueueOut, PenambahanKerjaApprovalRequest, PenambahanKerjaApprovalResponse
from app.services.penambahan_kerja_service import get_penambahan_kerja_queue, process_penambahan_kerja

router = APIRouter(prefix="/approval", tags=["Approval"])


## queue card
@router.get("/approval-queue", response_model=list[PersetujuanQueueCutiOut])
async def get_queue(
    current_user: Annotated[User, Depends(require_role("pm", "hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_queue_card(current_user, db)

## approval
@router.post("/approval{log_cuti_id}", response_model=ApprovalResponse)
async def approve_or_decline(
    log_cuti_id: int, data: ApprovalRequest,
    current_user: Annotated[User, Depends(require_role("pm", "hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks
):

    return await process_approval(log_cuti_id, current_user, data, db, background_tasks)


## queue penambahan kerja
@router.get("/penambahan-kerja-queue")
async def get_queue_penambahan_kerja(
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await get_penambahan_kerja_queue(current_user.id_user, db)


## approval penambahan kerja
@router.post("/penambahan-kerja/{log_id}", response_model=PenambahanKerjaApprovalResponse)
async def approve_or_decline_penambahan_kerja(
    log_id: int, data: PenambahanKerjaApprovalRequest,
    current_user: Annotated[User, Depends(require_role("pm"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):

    return await process_penambahan_kerja(log_id, current_user.id_user, data.action, data.alasan, db)
