from sqlalchemy import Column, Date, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class LogCutiEkstra(Base):
    __tablename__ = "log_cuti_ekstra"

    ## define kolom
    id_log_cuti_ekstra = Column(Integer, primary_key=True, index=True)
    id_penambah = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    jumlah_hari = Column(Integer, default=1)
    keterangan = Column(Text, nullable=False)
    added_at = Column(Date, nullable=False)

    ## relasi dari tabel ini
    user_tambah_cuti = relationship("User", back_populates="user_tambah_cuti")

    ## relasi ke tabel lain