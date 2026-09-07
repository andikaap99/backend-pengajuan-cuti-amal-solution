from datetime import date
from io import BytesIO
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from starlette.datastructures import UploadFile
from weasyprint import HTML

from app.core.config import mail_settings
from app.models.log_cuti import LogCuti
from app.models.user import User

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
    "hr": "Human Resources",
    "direktur": "Direktur",
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


### send_status_email - notifikasi teks hanya untuk status yang belum final
async def send_status_email(
    log_cuti: LogCuti,
    user_pengaju: User,
    current_user: User,
    new_status: str,
) -> None:
    if not user_pengaju.email:
        return

    durasi = (log_cuti.tanggal_selesai - log_cuti.tanggal_mulai).days + 1
    role_penyetuju = ROLE_LABELS.get(current_user.role, current_user.role)

    if new_status.startswith("ditolak"):
        subject = f"Ditolak {role_penyetuju} - {user_pengaju.nama}"
        body = (
            f"Halo {user_pengaju.nama},\n\n"
            f"Pengajuan cuti Anda telah ditolak oleh {role_penyetuju}.\n\n"
            f"Detail Pengajuan:\n"
            f"- Jenis Cuti: {log_cuti.jenis_cuti}\n"
            f"- Tanggal: {log_cuti.tanggal_mulai} s/d {log_cuti.tanggal_selesai} ({durasi} hari)\n"
        )
        if log_cuti.alasan_penolakan:
            body += f"- Alasan Penolakan: {log_cuti.alasan_penolakan}\n"
        body += "\nTerima kasih.\nSalam,\nTim HR Amal Solution"
    else:
        status_label = STATUS_LABELS.get(new_status, new_status)
        subject = f"Diacc {role_penyetuju} - {user_pengaju.nama}"
        body = (
            f"Halo {user_pengaju.nama},\n\n"
            f"Pengajuan cuti Anda telah diacc oleh {role_penyetuju}.\n"
            f"Sekarang sedang {status_label}.\n\n"
            f"Detail Pengajuan:\n"
            f"- Jenis Cuti: {log_cuti.jenis_cuti}\n"
            f"- Tanggal: {log_cuti.tanggal_mulai} s/d {log_cuti.tanggal_selesai} ({durasi} hari)\n\n"
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


### generate_surat_cuti - generate PDF surat konfirmasi, dipanggil saat status final disetujui
async def generate_surat_cuti(
    log_cuti: LogCuti,
    user_pengaju: User,
    current_user: User,
) -> None:
    if not user_pengaju.email:
        return

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("surat_cuti.html")

    durasi = (log_cuti.tanggal_selesai - log_cuti.tanggal_mulai).days + 1

    html_content = template.render(
        nama_karyawan=user_pengaju.nama,
        departemen=getattr(user_pengaju.user_departemen, "nama_departemen", "-"),
        jenis_cuti=log_cuti.jenis_cuti,
        tanggal_mulai=log_cuti.tanggal_mulai.strftime("%d %B %Y"),
        tanggal_selesai=log_cuti.tanggal_selesai.strftime("%d %B %Y"),
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