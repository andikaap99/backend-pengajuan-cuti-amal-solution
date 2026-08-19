from app.models.user import User


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