from datetime import date, timedelta

BULAN_INDONESIA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


def format_tanggal_grouped(dates: list[date]) -> str:
    ## kelompokkan tanggal berurutan menjadi rentang, mis. "1-3 Januari"
    if not dates:
        return "-"

    all_dates = sorted(dates)

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
