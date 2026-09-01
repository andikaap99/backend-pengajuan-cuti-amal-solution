from datetime import date
from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogPenambahanKerja(Base):
    __tablename__ = "log_penambahan_kerja"

    ## define kolom
    id_pengajuan_kerja = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    tanggal_mulai = Column(Date, nullable=False)
    tanggal_selesai = Column(Date, nullable=False)
    keterangan_pengajuan = Column(Text, nullable=False)
    status = Column(Enum("menunggu_pm", "disetujui_pm", "ditolak_pm"), nullable=False)
    diproses_pm = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    processed_at_pm = Column(Date, nullable=True)

    ## relasi dari tabel ini
    user_log = relationship("User", foreign_keys=[id_user], back_populates="user_penambahan_kerja")
    pm_log = relationship("User", foreign_keys=[diproses_pm], back_populates="pm_penambahan_kerja")

