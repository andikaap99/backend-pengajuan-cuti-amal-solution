from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogReassignmentApproval(Base):
    __tablename__ = "log_reassignment_approval"

    id_reassignment = Column(Integer, primary_key=True, index=True)
    id_log_cuti = Column(Integer, ForeignKey("log_cuti.id_log_cuti"), nullable=True)
    id_pengajuan_kerja = Column(Integer, ForeignKey("log_penambahan_kerja.id_pengajuan_kerja"), nullable=True)
    id_pm_lama = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    id_pm_baru = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    alasan = Column(Text, default="perubahan assignment PM", nullable=False)
    waktu_perubahan = Column(DateTime, default=datetime.utcnow, nullable=False)

    ## relasi
    log_cuti = relationship("LogCuti")
    log_penambahan_kerja = relationship("LogPenambahanKerja")
    pm_lama = relationship("User", foreign_keys=[id_pm_lama])
    pm_baru = relationship("User", foreign_keys=[id_pm_baru])
