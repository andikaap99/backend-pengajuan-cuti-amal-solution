from sqlalchemy import Column, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogPenambahanKerjaDate(Base):
    __tablename__ = "log_penambahan_kerja_dates"

    id = Column(Integer, primary_key=True, index=True)
    id_pengajuan_kerja = Column(Integer, ForeignKey("log_penambahan_kerja.id_pengajuan_kerja", ondelete="CASCADE"), nullable=False)
    tanggal = Column(Date, nullable=False)

    log_penambahan_kerja = relationship("LogPenambahanKerja", back_populates="tanggal_list")
