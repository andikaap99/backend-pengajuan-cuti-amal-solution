from typing import Literal, Optional

from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    action: Literal["acc", "decline"]
    alasan: Optional[str] = None

class ApprovalResponse(BaseModel):
    detail: str
    status_baru: str