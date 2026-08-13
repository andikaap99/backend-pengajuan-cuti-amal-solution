from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Departemen(Base):
    __tablename__ = "departemen"

    ## define kolom
    id_departemen = Column(Integer, primary_key=True, index=True)
    nama_departemen = Column(String(35), nullable=False)

    ## relasi ke tabel lain
    user_departemen = relationship("User", back_populates="user_departemen")
