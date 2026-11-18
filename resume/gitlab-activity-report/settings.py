"""Shared paths and environment loading."""

import os
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_EVENTS_PATH = DATA_DIR / "events_raw.json"
SUMMARY_PATH = DATA_DIR / "events_summary.csv"
REPORT_PATH = ROOT / "report.html"
PROJECT_CACHE_PATH = DATA_DIR / "project_names.json"


def load_gitlab_settings() -> Tuple[str, str]:
    """Read GITLAB_URL and GITLAB_TOKEN. Raise if either is missing."""
    base_url = (os.environ.get("GITLAB_URL") or "").strip().rstrip("/")
    token = (os.environ.get("GITLAB_TOKEN") or "").strip()
    missing = []
    if not base_url:
        missing.append("GITLAB_URL")
    if not token:
        missing.append("GITLAB_TOKEN")
    if missing:
        raise RuntimeError(
            "Missing %s. Copy .env.example to .env and set both values. "
            "GITLAB_TOKEN must be a personal access token with the read_api scope."
            % " and ".join(missing)
        )
    return base_url, token
