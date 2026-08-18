from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base


class Holiday(Base):
    __tablename__ = "holidays"

    ## define kolom
    id_holiday = Column(Integer, primary_key=True, index=True)
    nama_libur = Column(String(100), nullable=False)
    tanggal = Column(Date)
    is_cuti_bersama = Column(Boolean)
    tahun = Column(Integer)
