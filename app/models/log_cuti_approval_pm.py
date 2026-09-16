from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogCutiApprovalPM(Base):
    __tablename__ = "log_cuti_approval_pm"

    ## define kolom
    id_approval = Column(Integer, primary_key=True, index=True)
    id_log_cuti = Column(Integer, ForeignKey("log_cuti.id_log_cuti"), nullable=False)
    id_pm = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    status = Column(Enum("menunggu", "disetujui", "ditolak"), default="menunggu", nullable=False)
    processed_at = Column(DateTime, nullable=True)

    ## relasi
    log_cuti = relationship("LogCuti", back_populates="approval_pm_list")
    pm = relationship("User", foreign_keys=[id_pm], back_populates="approval_pm_logs")
