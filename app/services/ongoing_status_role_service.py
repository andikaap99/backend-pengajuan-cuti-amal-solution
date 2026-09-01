from app.models.user import User
from app.models.log_cuti import LogCuti
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


## fungsi untuk get status sesuai role
def get_ongoing_statuses(user: User) -> list[str]:
    match user.role:
        case "karyawan":
            if user.id_departemen != 1:
                return ["menunggu_pm", "disetujui_pm", "menunggu_hr"]
            else:
                return ["menunggu_hr"]
        case "pm":
            return ["menunggu_hr"]
        case "hr":
            return ["menunggu_direktur"]
        
    return []


## fungsi untuk get status ditolak sesuai role
def get_rejected_statuses(user: User) -> list[str]:
    match user.role:
        case "karyawan":
            if user.id_departemen != 1:
                return ["ditolak_pm", "ditolak_hr"]
            else:
                return ["ditolak_hr"]
        case "pm":
            return ["ditolak_hr"]
        case "hr":
            return ["ditolak_direktur"]
        
    return []

