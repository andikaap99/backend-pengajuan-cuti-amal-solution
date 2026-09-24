from datetime import date, datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogCutiDate(Base):
    __tablename__ = "log_cuti_dates"

    id = Column(Integer, primary_key=True, index=True)
    id_log_cuti = Column(Integer, ForeignKey("log_cuti.id_log_cuti", ondelete="CASCADE"), nullable=False)
    tanggal = Column(Date, nullable=False)

    log_cuti = relationship("LogCuti", back_populates="tanggal_list")
