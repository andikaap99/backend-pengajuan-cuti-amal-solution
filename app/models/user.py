from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    ## define kolom
    id_user = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), nullable=False)
    nama = Column(String(100), nullable=False)
    status = Column(Enum("Aktif", "Cuti"), default="Aktif")
    password = Column(Text, nullable=False)
    role = Column(Enum("karyawan", "pm", "hr", "direktur"), nullable=False)
    id_departemen = Column(Integer, ForeignKey("departemen.id_departemen"), nullable=False)
    id_pm = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    total_cuti = Column(Integer, default=12)
    sisa_cuti = Column(Integer, default=12)
    email = Column(String(100), nullable=True)
    no_telp = Column(String(20), nullable=True)
    tanggal_bergabung = Column(Date, nullable=True)

    ## relation dari tabel ini
    user_departemen = relationship("Departemen", back_populates="user_departemen")
    manager = relationship("User", remote_side="User.id_user", foreign_keys=[id_pm], back_populates="project_manager")
    project_manager = relationship("User", back_populates="manager")

    ## relation ke tabel lain
    user_log = relationship("LogCuti", foreign_keys="LogCuti.id_user", back_populates="user_log")
    user_backup = relationship("LogCuti", foreign_keys="LogCuti.pengganti", back_populates="user_backup")
    pm_log = relationship("LogCuti", foreign_keys="LogCuti.disetujui_pm", back_populates="pm_log")
    hr_log = relationship("LogCuti", foreign_keys="LogCuti.disetujui_hr", back_populates="hr_log")
    direktur_log = relationship("LogCuti", foreign_keys="LogCuti.disetujui_direktur", back_populates="direktur_log")
    user_tambah_cuti = relationship("LogCutiEkstra", back_populates="user_tambah_cuti")
