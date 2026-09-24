from datetime import date
from io import BytesIO
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from starlette.datastructures import UploadFile
from weasyprint import HTML

from app.core.config import mail_settings, settings
from app.models.log_cuti import LogCuti
from app.models.log_penambahan_kerja import LogPenambahanKerja
from app.models.user import User
from app.services.date_format_service import format_tanggal_grouped

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"

STATUS_LABELS = {
    "menunggu_pm": "Menunggu persetujuan PM",
    "disetujui_pm": "Disetujui PM",
    "ditolak_pm": "Ditolak PM",
    "menunggu_hr": "Menunggu persetujuan HR",
    "disetujui_hr": "Disetujui HR",
    "ditolak_hr": "Ditolak HR",
    "menunggu_direktur": "Menunggu persetujuan Direktur",
    "disetujui_direktur": "Disetujui Direktur",
    "ditolak_direktur": "Ditolak Direktur",
}

ROLE_LABELS = {
    "karyawan": "Karyawan",
    "pm": "Project Manager",
    "hr_manager": "Human Resources",
    "direktur": "Direktur",
    "staff_hr": "Staff HR",
}


def _get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=mail_settings.MAIL_USERNAME,
        MAIL_PASSWORD=mail_settings.MAIL_PASSWORD,
        MAIL_FROM=mail_settings.MAIL_FROM,
        MAIL_SERVER=mail_settings.MAIL_SERVER,
        MAIL_PORT=mail_settings.MAIL_PORT,
        MAIL_STARTTLS=mail_settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=mail_settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


## notifikasi teks hanya untuk status yang belum final
async def send_status_email(
    log_cuti: LogCuti,
    user_pengaju: User,
    current_user: User,
    new_status: str,
    pending_pm_names: list[str] | None = None,
) -> None:
    if not user_pengaju.email:
        return

    tanggal_cuti = sorted([ld.tanggal for ld in log_cuti.tanggal_list])
    durasi = len(tanggal_cuti)
    tgl_str = format_tanggal_grouped(tanggal_cuti)
    role_penyetuju = ROLE_LABELS.get(current_user.role, current_user.role)

    if new_status.startswith("ditolak"):
        subject = f"Ditolak {role_penyetuju} ({current_user.nama}) - {user_pengaju.nama}"
        body = (
            f"Halo {user_pengaju.nama},\n\n"
            f"Pengajuan cuti Anda telah ditolak oleh {role_penyetuju} ({current_user.nama}).\n\n"
            f"Detail Pengajuan:\n"
            f"- Jenis Cuti: {log_cuti.jenis_cuti}\n"
            f"- Tanggal: {tgl_str} ({durasi} hari)\n"
        )
        if log_cuti.alasan_penolakan:
            body += f"- Alasan Penolakan: {log_cuti.alasan_penolakan}\n"
        body += "\nTerima kasih.\nSalam,\nTim HR Amal Solution"
    else:
        status_label = STATUS_LABELS.get(new_status, new_status)
        subject = f"Diacc {role_penyetuju} ({current_user.nama}) - {user_pengaju.nama}"
        body = (
            f"Halo {user_pengaju.nama},\n\n"
            f"Pengajuan cuti Anda telah diacc oleh {role_penyetuju} ({current_user.nama}).\n"
        )

        if new_status == "menunggu_hr":
            body += f"Sekarang sedang menunggu persetujuan HR.\n\n"
        elif new_status == "menunggu_pm" and pending_pm_names:
            body += f"Masih menunggu persetujuan PM: {', '.join(pending_pm_names)}.\n\n"
        else:
            body += f"Sekarang sedang {status_label}.\n\n"

        body += (
            f"Detail Pengajuan:\n"
            f"- Jenis Cuti: {log_cuti.jenis_cuti}\n"
            f"- Tanggal: {tgl_str} ({durasi} hari)\n\n"
            f"Terima kasih.\nSalam,\nTim HR Amal Solution"
        )

    message = MessageSchema(
        subject=subject,
        recipients=[user_pengaju.email],
        body=body,
        subtype="plain",
    )

    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


## notifikasi ke approver saat ada pengajuan baru
async def send_pengajuan_notification(
    user_pengaju: User,
    approver: User,
    jenis_pengajuan: str,
    tanggal: list[date],
    keterangan: str,
) -> None:
    if not approver.email:

        return

    tanggal_sorted = sorted(tanggal)
    durasi = len(tanggal_sorted)
    tgl_str = format_tanggal_grouped(tanggal_sorted)

    subject = f"Pengajuan {jenis_pengajuan} Baru - {user_pengaju.nama}"
    body = (
        f"Halo {approver.nama},\n\n"
        f"Karyawan {user_pengaju.nama} telah mengajukan {jenis_pengajuan}.\n\n"
        f"Detail Pengajuan:\n"
        f"- Tanggal: {tgl_str} ({durasi} hari)\n"
        f"- Keterangan: {keterangan}\n\n"
        f"Silakan proses pengajuan ini di halaman approval.\n\n"
        f"Terima kasih."
    )

    message = MessageSchema(
        subject=subject,
        recipients=[approver.email],
        body=body,
        subtype="plain",
    )

    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


## notifikasi status pengajuan kerja ke karyawan
async def send_penambahan_kerja_status_email(
    log_kerja: LogPenambahanKerja,
    user_pengaju: User,
    current_user: User,
    new_status: str,
    pending_pm_names: list[str] | None = None,
) -> None:
    if not user_pengaju.email:

        return

    tanggal_kerja = sorted([ld.tanggal for ld in log_kerja.tanggal_list])
    durasi = len(tanggal_kerja)
    tgl_str = format_tanggal_grouped(tanggal_kerja)
    role_penyetuju = ROLE_LABELS.get(current_user.role, current_user.role)

    if new_status.startswith("ditolak"):
        subject = f"Ditolak {role_penyetuju} ({current_user.nama}) - {user_pengaju.nama}"
        body = (
            f"Halo {user_pengaju.nama},\n\n"
            f"Pengajuan penambahan kerja Anda telah ditolak oleh {role_penyetuju} ({current_user.nama}).\n\n"
            f"Detail Pengajuan:\n"
            f"- Tanggal: {tgl_str} ({durasi} hari)\n"
            f"- Keterangan: {log_kerja.keterangan_pengajuan}\n"
        )
        if log_kerja.alasan_penolakan:
            body += f"- Alasan Penolakan: {log_kerja.alasan_penolakan}\n"
        body += "\nTerima kasih."
    else:
        status_label = STATUS_LABELS.get(new_status, new_status)
        subject = f"Diacc {role_penyetuju} ({current_user.nama}) - {user_pengaju.nama}"
        body = (
            f"Halo {user_pengaju.nama},\n\n"
            f"Pengajuan penambahan kerja Anda telah diacc oleh {role_penyetuju} ({current_user.nama}).\n"
        )

        if new_status == "menunggu_hr":
            body += f"Sekarang sedang menunggu persetujuan HR.\n\n"
        elif new_status == "menunggu_pm" and pending_pm_names:
            body += f"Masih menunggu persetujuan PM: {', '.join(pending_pm_names)}.\n\n"
        else:
            body += f"Sekarang sedang {status_label}.\n\n"

        body += (
            f"Detail Pengajuan:\n"
            f"- Tanggal: {tgl_str} ({durasi} hari)\n"
            f"- Keterangan: {log_kerja.keterangan_pengajuan}\n\n"
            f"Terima kasih."
        )

    message = MessageSchema(
        subject=subject,
        recipients=[user_pengaju.email],
        body=body,
        subtype="plain",
    )

    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


## generate pdf surat konfirmasi, dipanggil saat status final disetujui
async def generate_surat_cuti(
    log_cuti: LogCuti,
    user_pengaju: User,
    current_user: User,
) -> None:
    if not user_pengaju.email:
        
        return

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("surat_cuti.html")

    durasi = len(log_cuti.tanggal_list)
    tanggal_list = sorted([ld.tanggal for ld in log_cuti.tanggal_list])

    html_content = template.render(
        nama_karyawan=user_pengaju.nama,
        departemen=getattr(user_pengaju.user_departemen, "nama_departemen", "-"),
        jenis_cuti=log_cuti.jenis_cuti,
        tanggal_list=[t.strftime("%d %B %Y") for t in tanggal_list],
        durasi=durasi,
        keterangan=log_cuti.keterangan_cuti,
        disetujui_oleh=current_user.nama,
        role_penyetuju=ROLE_LABELS.get(current_user.role, current_user.role),
        tanggal_approval=date.today().strftime("%d %B %Y"),
    )

    pdf_bytes = HTML(string=html_content).write_pdf()

    pdf_buffer = BytesIO(pdf_bytes)
    pdf_buffer.seek(0)
    file_attachment = UploadFile(filename="surat_konfirmasi_cuti.pdf", file=pdf_buffer)

    message = MessageSchema(
        subject=f"Cuti Disetujui - {user_pengaju.nama}",
        recipients=[user_pengaju.email],
        body=f"Halo {user_pengaju.nama},\n\nSelamat! Pengajuan cuti Anda telah disetujui secara final.\nBerikut terlampir surat konfirmasi cuti Anda.\n\nSalam,\nTim HR Amal Solution",
        subtype="plain",
        attachments=[file_attachment],
    )

    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


## notifikasi reset password ke karyawan
async def send_reset_password_email(user: User) -> None:
    if not user.email:
        return

    subject = "Reset Password - Amal Solution"
    body = (
        f"Halo {user.nama},\n\n"
        f"Password Anda telah direset oleh admin.\n"
        f"Password baru Anda: untukdevajaya\n\n"
        f"Silakan login dan segera ubah password Anda.\n\n"
        f"Salam,\nTim HR Amal Solution"
    )

    message = MessageSchema(
        subject=subject,
        recipients=[user.email],
        body=body,
        subtype="plain",
    )

    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


## notifikasi link reset password ke email
async def send_forgot_password_email(user: User, token: str) -> None:
    if not user.email:
        return

    reset_link = f"{settings.BACKEND_URL}/auth/reset-password-page?token={token}"

    subject = "Reset Password - Amal Solution"
    body = (
        f"Halo {user.nama},\n\n"
        f"Anda telah meminta reset password.\n"
        f"Klik link berikut untuk reset password Anda:\n\n"
        f"{reset_link}\n\n"
        f"Link ini berlaku selama 30 menit dan hanya bisa digunakan satu kali.\n"
        f"Jika Anda tidak meminta reset password, abaikan email ini.\n\n"
        f"Salam,\nTim HR Amal Solution"
    )

    message = MessageSchema(
        subject=subject,
        recipients=[user.email],
        body=body,
        subtype="plain",
    )

    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


## notifikasi password berhasil diubah
async def send_password_changed_notification(user: User, password_baru: str) -> None:
    if not user.email:
        return

    subject = "Password Berhasil Diubah - Amal Solution"
    body = (
        f"Halo {user.nama},\n\n"
        f"Password Anda telah berhasil diubah.\n"
        f"Password baru Anda: {password_baru}\n\n"
        f"Jika Anda tidak melakukan perubahan ini, segera hubungi tim HR.\n\n"
        f"Salam,\nTim HR Amal Solution"
    )

    message = MessageSchema(
        subject=subject,
        recipients=[user.email],
        body=body,
        subtype="plain",
    )

    fm = FastMail(_get_mail_config())
    await fm.send_message(message)