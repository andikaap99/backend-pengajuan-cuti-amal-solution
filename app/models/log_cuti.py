from datetime import date
from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogCuti(Base):
    __tablename__ = "log_cuti"

    ## define kolom
    id_log_cuti = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    jenis_cuti = Column(String(30), nullable=False)
    tanggal_mulai = Column(Date, nullable=False)
    tanggal_selesai = Column(Date, nullable=False)
    keterangan_cuti = Column(Text, nullable=False)
    pengganti = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    status = Column(Enum(
        "menunggu_pm", "disetujui_pm", "ditolak_pm",
        "menunggu_hr", "disetujui_hr", "ditolak_hr",
        "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"
        ), nullable=False)
    tanggal_pengajuan = Column(Date, default=date.today)
    alasan_penolakan = Column(Text, nullable=True)
    disetujui_pm = Column(ForeignKey("users.id_user"), nullable=True)
    disetujui_hr = Column(ForeignKey("users.id_user"), nullable=True)
    disetujui_direktur = Column(ForeignKey("users.id_user"), nullable=True)
    approved_at_pm = Column(Date, nullable=True)
    approved_at_hr = Column(Date, nullable=True)
    approved_at_direktur = Column(Date, nullable=True)

    ## relasi dari tabel ini
    user_log = relationship("User", foreign_keys=[id_user], back_populates="user_log")
    user_backup = relationship("User", foreign_keys=[pengganti], back_populates="user_backup")
    pm_log = relationship("User", foreign_keys=[disetujui_pm], back_populates="pm_log")
    hr_log = relationship("User", foreign_keys=[disetujui_hr], back_populates="hr_log")
    direktur_log = relationship("User", foreign_keys=[disetujui_direktur], back_populates="direktur_log")

    ## relasi ke tabel lain
