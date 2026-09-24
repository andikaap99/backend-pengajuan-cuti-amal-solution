from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogCuti(Base):
    __tablename__ = "log_cuti"

    ## define kolom
    id_log_cuti = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    jenis_cuti = Column(String(30), nullable=False)
    keterangan_cuti = Column(Text, nullable=False)
    pengganti = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    status = Column(Enum(
        "menunggu_pm", "disetujui_pm", "ditolak_pm",
        "menunggu_hr", "disetujui_hr", "ditolak_hr",
        "menunggu_direktur", "disetujui_direktur", "ditolak_direktur",
        "cuti_bersama"
        ), nullable=False)
    tanggal_pengajuan = Column(DateTime, default=datetime.now)
    alasan_penolakan = Column(Text, nullable=True)
    diproses_hr = Column(ForeignKey("users.id_user"), nullable=True)
    diproses_direktur = Column(ForeignKey("users.id_user"), nullable=True)
    processed_at_hr = Column(DateTime, nullable=True)
    processed_at_direktur = Column(DateTime, nullable=True)
    edited_at = Column(DateTime, nullable=True)

    ## relasi dari tabel ini
    user_log = relationship("User", foreign_keys=[id_user], back_populates="user_log")
    user_backup = relationship("User", foreign_keys=[pengganti], back_populates="user_backup")
    hr_log = relationship("User", foreign_keys=[diproses_hr], back_populates="hr_log")
    direktur_log = relationship("User", foreign_keys=[diproses_direktur], back_populates="direktur_log")

    ## relasi tanggal cuti individual
    tanggal_list = relationship("LogCutiDate", back_populates="log_cuti", cascade="all, delete-orphan")

    ## relasi approval PM (many to many)
    approval_pm_list = relationship("LogCutiApprovalPM", back_populates="log_cuti", cascade="all, delete-orphan")
