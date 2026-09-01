from datetime import date, timedelta
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.services.tambah_cuti_service import get_effective_sisa_cuti

BULAN_INDONESIA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


def _format_dates(logs: list[LogCuti]) -> str:
    if not logs:
        return "-"

    all_dates = []
    for log in logs:
        current = log.tanggal_mulai
        while current <= log.tanggal_selesai:
            all_dates.append(current)
            current += timedelta(days=1)

    all_dates.sort()

    groups: list[tuple[date, date]] = []
    for d in all_dates:
        if groups and d == groups[-1][1] + timedelta(days=1):
            groups[-1] = (groups[-1][0], d)
        else:
            groups.append((d, d))

    parts = []
    for start, end in groups:
        bulan = BULAN_INDONESIA[start.month]
        if start == end:
            parts.append(f"{start.day} {bulan}")
        else:
            end_bulan = BULAN_INDONESIA[end.month]
            if start.month == end.month:
                parts.append(f"{start.day}-{end.day} {bulan}")
            else:
                parts.append(f"{start.day} {bulan} - {end.day} {end_bulan} {end.year}")

    return ", ".join(parts)


async def export_cuti_excel(year: int, db: AsyncSession) -> bytes:
    approved_statuses = ["disetujui_hr", "disetujui_direktur"]

    result_users = await db.execute(
        select(User)
        .where(User.role.in_(["karyawan", "pm", "hr"]))
        .order_by(User.nama.asc())
    )
    users = result_users.scalars().all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Rekap Cuti"

    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    ws.merge_cells("A1:G1")
    ws["A1"] = f"Rekap Data Cuti Karyawan - Periode {year}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = Alignment(horizontal="center")

    headers = ["No", "Nama Karyawan", "Total Cuti (hari)", "Total Cuti Diambil", "Sisa Cuti", "Keterangan (Tanggal Cuti)"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    row = 4
    no = 1

    for user in users:
        result_logs = await db.execute(
            select(LogCuti).where(
                LogCuti.id_user == user.id_user,
                LogCuti.status.in_(approved_statuses),
                extract("year", LogCuti.tanggal_mulai) == year,
            )
        )
        logs = result_logs.scalars().all()

        effective_sisa = await get_effective_sisa_cuti(user, year, db)
        cuti_terpakai = user.total_cuti - effective_sisa
        keterangan = _format_dates(logs)

        ws.cell(row=row, column=1, value=no).border = border
        ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")

        ws.cell(row=row, column=2, value=user.nama).border = border
        ws.cell(row=row, column=3, value=user.total_cuti).border = border
        ws.cell(row=row, column=3).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=4, value=cuti_terpakai).border = border
        ws.cell(row=row, column=4).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=5, value=effective_sisa).border = border
        ws.cell(row=row, column=5).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=6, value=keterangan).border = border

        no += 1
        row += 1

    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 50

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
