"""
Hardmine — Sugar Flow TDM Pipeline (Prefect)
=============================================
Wraps the three ingest scripts into a Prefect flow.

Usage:
    python pipeline_flow.py              # run once right now
    python pipeline_flow.py --serve      # start scheduler (Mon-Fri 09:30 Amsterdam)
"""

import subprocess
import sys
from pathlib import Path

from prefect import flow, task, get_run_logger
from prefect.schedules import Cron

DIR    = Path(__file__).parent   # .../Sugar Flow/files/
PYTHON = sys.executable


@task(name="Sugar Exports Ingest", retries=1, retry_delay_seconds=60)
def run_exports():
    logger = get_run_logger()
    logger.info("Running sugar_exports_ingest.py ...")
    r = subprocess.run(
        [PYTHON, str(DIR / "sugar_exports_ingest.py")],
        capture_output=True, text=True,
    )
    if r.stdout.strip():
        logger.info(r.stdout.strip())
    if r.returncode != 0:
        logger.error(r.stderr.strip())
        raise RuntimeError(f"sugar_exports_ingest.py failed (exit {r.returncode})")


@task(name="Sugar Imports Ingest", retries=1, retry_delay_seconds=60)
def run_imports():
    logger = get_run_logger()
    logger.info("Running sugar_imports_ingest.py ...")
    r = subprocess.run(
        [PYTHON, str(DIR / "sugar_imports_ingest.py")],
        capture_output=True, text=True,
    )
    if r.stdout.strip():
        logger.info(r.stdout.strip())
    if r.returncode != 0:
        logger.error(r.stderr.strip())
        raise RuntimeError(f"sugar_imports_ingest.py failed (exit {r.returncode})")


@task(name="Sugar EU Imports Ingest", retries=1, retry_delay_seconds=60)
def run_imports_eu():
    logger = get_run_logger()
    logger.info("Running sugar_imports_eu_ingest.py ...")
    r = subprocess.run(
        [PYTHON, str(DIR / "sugar_imports_eu_ingest.py")],
        capture_output=True, text=True,
    )
    if r.stdout.strip():
        logger.info(r.stdout.strip())
    if r.returncode != 0:
        logger.error(r.stderr.strip())
        raise RuntimeError(f"sugar_imports_eu_ingest.py failed (exit {r.returncode})")


@flow(
    name="Sugar Flow TDM Pipeline",
    description="Daily ingest of Sugar Exports, Imports, and EU Imports from TDM.",
)
def sugar_pipeline():
    exports    = run_exports()
    imports    = run_imports(wait_for=[exports])
    imports_eu = run_imports_eu(wait_for=[imports])


if __name__ == "__main__":
    if "--serve" in sys.argv:
        sugar_pipeline.serve(
            name="sugar-flows-daily",
            schedules=[Cron("30 9 * * 1-5", timezone="Europe/Amsterdam")],
        )
    else:
        sugar_pipeline()
