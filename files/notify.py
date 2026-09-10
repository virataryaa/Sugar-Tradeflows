"""
Sugar TDM Pipeline — email notification.
Called by run_pipeline.bat:  python notify.py <ok|failed> <pushed|failed|skipped>
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

LOG_DIR  = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "run_log.txt"
EMAIL_TO = "virat.arya@etgworld.com"

SUMMARIES = [
    ("summary_tdm_sugar_exports.json",    "Sugar Exports"),
    ("summary_tdm_sugar_imports.json",    "Sugar Imports"),
    ("summary_tdm_sugar_imports_eu.json", "Sugar EU Imports"),
    ("summary_tdm_sugar_exports_eu.json", "Sugar EU Exports"),
]


DATA_DIR = Path(__file__).parent / "data"

_MONTH = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def ym_str(ym: int) -> str:
    return f"{_MONTH[ym % 100]}-{ym // 100}"


def _latest_per_reporter(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_ym"] = df["YEAR"] * 100 + df["MONTH"]
    latest_ym = df.groupby("REPORTER")["_ym"].max().rename("_latest_ym")
    return df.merge(latest_ym, on="REPORTER").query("_ym == _latest_ym") \
             .groupby(["REPORTER", "_latest_ym"])["QTY1"].sum().reset_index() \
             .sort_values("QTY1", ascending=False).reset_index(drop=True)


def reporter_table(path: Path) -> str:
    if not path.exists():
        return "  [file not found]"
    try:
        agg = _latest_per_reporter(pd.read_parquet(path))
        w = max(len(r) for r in agg["REPORTER"]) + 1
        lines = [f"  {'Reporter':<{w}}  Latest", f"  {'-'*w}  {'-'*9}"]
        for _, row in agg.iterrows():
            lines.append(f"  {row['REPORTER']:<{w}}  {ym_str(int(row['_latest_ym']))}")
        return "\n".join(lines)
    except Exception as e:
        return f"  [error: {e}]"


def eu_table(path: Path) -> str:
    if not path.exists():
        return "  [file not found]"
    try:
        df = pd.read_parquet(path)
        latest_ym = int((df["YEAR"] * 100 + df["MONTH"]).max())
        return f"  Latest period : {ym_str(latest_ym)}"
    except Exception as e:
        return f"  [error: {e}]"


def load(filename: str) -> dict | None:
    path = LOG_DIR / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def fmt_section(s: dict) -> str:
    net = s["net_new"]
    net_str = f"+{net:,}" if net > 0 else f"{net:,}"

    if s["new_periods"]:
        detail = f"  ->  new periods: {', '.join(s['new_periods'])}"
    elif net == 0:
        detail = "  ->  no new periods (data unchanged)"
    else:
        detail = ""

    return (
        f"  {s['name']} ({s['file']})\n"
        f"    Total rows  : {s['total_rows']:,}\n"
        f"    Net new     : {net_str} rows{detail}\n"
        f"    Latest data : {s['latest_period']}"
    )


def build_body(status: str, git_status: str) -> str:
    status_str = "OK" if status == "ok" else "ERROR"
    git_map = {
        "pushed":  "pushed successfully",
        "failed":  "push FAILED — check log",
        "skipped": "skipped (ingest did not complete)",
    }
    git_str = git_map.get(git_status, git_status)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sep = "=" * 60

    lines = [
        f"Sugar TDM Pipeline — {status_str}",
        f"Run time : {now}",
        "",
        sep,
        "DATASET SUMMARY",
        sep,
    ]

    for fname, label in SUMMARIES:
        s = load(fname)
        if s:
            lines.append(fmt_section(s))
        else:
            lines.append(f"  {label}  —  [summary not available]")
        lines.append("")

    lines += [
        sep, "SUGAR EXPORTS — top exporters, latest available month", sep,
        reporter_table(DATA_DIR / "tdm_sugar_exports.parquet"), "",
        sep, "SUGAR IMPORTS — top importers, latest available month", sep,
        reporter_table(DATA_DIR / "tdm_sugar_imports.parquet"), "",
        sep, "EU-28 IMPORTS — latest available month", sep,
        eu_table(DATA_DIR / "tdm_sugar_imports_eu.parquet"), "",
        sep,
        f"GitHub  : {git_str}",
        f"Log     : {LOG_FILE}",
        sep,
    ]

    return "\n".join(lines)


def send(subject: str, body: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(body)
        tmp = f.name
    try:
        ps = (
            f"$body = Get-Content '{tmp}' -Raw -Encoding UTF8; "
            f"$o = New-Object -ComObject Outlook.Application; "
            f"$m = $o.CreateItem(0); "
            f"$m.To = '{EMAIL_TO}'; "
            f"$m.Subject = '{subject}'; "
            f"$m.Body = $body; "
            f"$m.Send()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            timeout=60,
        )
    finally:
        os.unlink(tmp)


def main() -> None:
    status     = sys.argv[1] if len(sys.argv) > 1 else "failed"
    git_status = sys.argv[2] if len(sys.argv) > 2 else "skipped"

    label    = "OK" if status == "ok" else "FAILED"
    date_str = datetime.now().strftime("%d/%m/%Y")
    subject  = f"Sugar TDM Pipeline - {label} [{date_str}]"
    body     = build_body(status, git_status)

    send(subject, body)


if __name__ == "__main__":
    main()
