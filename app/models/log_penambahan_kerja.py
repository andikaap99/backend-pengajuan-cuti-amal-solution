from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogPenambahanKerja(Base):
    __tablename__ = "log_penambahan_kerja"

    ## define kolom
    id_pengajuan_kerja = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    keterangan_pengajuan = Column(Text, nullable=False)
    status = Column(Enum("menunggu_pm", "disetujui_pm", "ditolak_pm", "menunggu_hr", "disetujui_hr", "ditolak_hr", "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"), nullable=False)
    alasan_penolakan = Column(Text, nullable=True)
    processed_at_hr = Column(DateTime, nullable=True)
    processed_at_direktur = Column(DateTime, nullable=True)
    tanggal_pengajuan = Column(DateTime, default=datetime.now)
    diproses_hr = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    diproses_direktur = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    keterangan_disetujui_hr = Column(Text, nullable=True)

    ## relasi dari tabel ini
    user_log = relationship("User", foreign_keys=[id_user], back_populates="user_penambahan_kerja")
    approval_pm_list = relationship("LogPenambahanKerjaApprovalPM", back_populates="log_penambahan_kerja", cascade="all, delete-orphan")

    ## relasi tanggal kerja individual
    tanggal_list = relationship("LogPenambahanKerjaDate", back_populates="log_penambahan_kerja", cascade="all, delete-orphan")

