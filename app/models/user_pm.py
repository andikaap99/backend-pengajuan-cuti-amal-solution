from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserPM(Base):
    __tablename__ = "user_pm"

    ## define kolom
    id_user_pm = Column(Integer, primary_key=True, index=True)
    id_karyawan = Column(Integer, ForeignKey("users.id_user"), nullable=False)
    id_pm = Column(Integer, ForeignKey("users.id_user"), nullable=False)

    ## relation many-to-many karyawan-pm via junction table
    karyawan = relationship("User", foreign_keys=[id_karyawan], back_populates="karyawan_pm_list")
    pm = relationship("User", foreign_keys=[id_pm], back_populates="pm_karyawan_list") 