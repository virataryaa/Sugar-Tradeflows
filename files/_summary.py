"""
Shared helper — writes a per-dataset summary JSON after each ingest run.
Read by notify.py to build the email body.
"""
import json
from datetime import datetime
from pathlib import Path

_MONTH = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def write_summary(log_dir: Path, name: str, filename: str,
                  rows_before: int, df, old_ym: set) -> None:
    ym_final = set(zip(df["YEAR"].astype(int), df["MONTH"].astype(int)))
    new_ym   = sorted(ym_final - old_ym)
    latest   = max(ym_final)

    summary = {
        "name":          name,
        "file":          filename,
        "rows_before":   rows_before,
        "net_new":       len(df) - rows_before,
        "total_rows":    len(df),
        "latest_period": f"{_MONTH[latest[1]]}-{latest[0]}",
        "new_periods":   [f"{_MONTH[m]}-{y}" for y, m in new_ym],
        "timestamp":     datetime.now().isoformat(timespec="seconds"),
    }

    slug = Path(filename).stem
    (log_dir / f"summary_{slug}.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
