from datetime import date, datetime, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models import Base, Departemen, LogCuti, LogCutiDate, LogPenambahanKerja, LogPenambahanKerjaDate, User, UserPM


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


async def seed_departemen(db: AsyncSession) -> None:
    for i, nama in enumerate(["Manajemen Perusahaan", "Project & Product Development", "IT Support Operation"], start=1):
        db.add(Departemen(id_departemen=i, nama_departemen=nama))
    await db.commit()


async def make_user(
    db: AsyncSession,
    username: str,
    role: str,
    id_departemen: int = 2,
    nama: str | None = None,
    sisa_cuti: int = 12,
    total_cuti: int = 12,
    status: str = "Aktif",
    email: str | None = None,
) -> User:
    user = User(
        username=username,
        nama=nama or username,
        password="x",
        role=role,
        status=status,
        id_departemen=id_departemen,
        total_cuti=total_cuti,
        sisa_cuti=sisa_cuti,
        email=email,
    )
    db.add(user)
    await db.flush()
    return user


async def assign_pm(db: AsyncSession, karyawan: User, pm: User) -> None:
    db.add(UserPM(id_karyawan=karyawan.id_user, id_pm=pm.id_user))
    await db.flush()


async def add_log_cuti(
    db: AsyncSession,
    user: User,
    status: str,
    dates: list[date],
    keterangan: str = "tes",
    jenis: str = "cuti tahunan",
) -> LogCuti:
    log = LogCuti(
        id_user=user.id_user,
        jenis_cuti=jenis,
        keterangan_cuti=keterangan,
        status=status,
        tanggal_pengajuan=datetime.now(),
    )
    db.add(log)
    await db.flush()
    for d in sorted(dates):
        db.add(LogCutiDate(id_log_cuti=log.id_log_cuti, tanggal=d))
    await db.commit()
    await db.refresh(log)
    return log


async def add_log_kerja(
    db: AsyncSession,
    user: User,
    status: str,
    dates: list[date],
    keterangan: str = "kerja",
) -> LogPenambahanKerja:
    log = LogPenambahanKerja(
        id_user=user.id_user,
        keterangan_pengajuan=keterangan,
        status=status,
        tanggal_pengajuan=datetime.now(),
    )
    db.add(log)
    await db.flush()
    for d in sorted(dates):
        db.add(LogPenambahanKerjaDate(id_pengajuan_kerja=log.id_pengajuan_kerja, tanggal=d))
    await db.commit()
    await db.refresh(log)
    return log


def future(*offsets: int) -> list[date]:
    today = date.today()
    return [today + timedelta(days=o) for o in offsets]
