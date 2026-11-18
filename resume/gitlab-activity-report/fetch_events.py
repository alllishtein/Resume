"""Download the authenticated user's GitLab events for the last two years."""

from __future__ import print_function

import json
import logging
import sys
import time
from datetime import date
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from gitlab_client import GitLabClient
from settings import DATA_DIR, RAW_EVENTS_PATH, load_gitlab_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger("fetch_events")

PER_PAGE = 100
PAGE_DELAY_SECONDS = 0.3
REQUEST_TIMEOUT_SECONDS = 60
MAX_PAGES = 5000


def two_years_ago(today: Optional[date] = None) -> date:
    """Return the calendar date two years before today, clamped for Feb 29."""
    current = today or date.today()
    try:
        return current.replace(year=current.year - 2)
    except ValueError:
        return current.replace(year=current.year - 2, day=28)


def event_is_recent(event: Dict[str, Any], after: date) -> bool:
    """Keep events whose created_at date is on or after the cutoff."""
    created_raw = event.get("created_at")
    if not isinstance(created_raw, str) or len(created_raw) < 10:
        return False
    return created_raw[:10] >= after.isoformat()


def request_page(client: GitLabClient, url: str, params: Dict[str, Any]) -> Any:
    """GET one page. Network failures become RuntimeError."""
    return client.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)


def explain_status(response: requests.Response) -> None:
    """Raise a specific error for auth and other non-200 responses."""
    if response.status_code == 200:
        return
    if response.status_code == 401:
        raise RuntimeError(
            "GitLab rejected GITLAB_TOKEN (HTTP 401). "
            "Create a personal access token with the read_api scope and put it in .env."
        )
    if response.status_code == 403:
        raise RuntimeError(
            "GitLab refused the events request (HTTP 403). The token needs the read_api scope."
        )
    body = response.text[:300]
    raise RuntimeError("GitLab events request failed with HTTP %s: %s" % (response.status_code, body))


def fetch_events(base_url: str, token: str, after: date) -> List[Dict[str, Any]]:
    """Page through GET /api/v4/events until X-Next-Page is empty.

    /api/v4/events is the authenticated user's own activity on every project.
    Nothing here filters to a single repository.
    """
    client = GitLabClient(token)
    url = base_url.rstrip("/") + "/api/v4/events"
    params: Dict[str, Any] = {
        "per_page": PER_PAGE,
        "after": after.isoformat(),
        "sort": "asc",
    }

    first_response = request_page(client, url, dict(params, page=1))
    if first_response.status_code == 400:
        LOGGER.warning("Server rejected the after parameter; filtering the last two years locally.")
        params.pop("after", None)
        first_response = None
    elif first_response.status_code != 200:
        explain_status(first_response)

    events: List[Dict[str, Any]] = []
    page = "1"
    pages_fetched = 0
    server_filters_by_date = "after" in params

    while page:
        pages_fetched += 1
        if pages_fetched > MAX_PAGES:
            raise RuntimeError("Stopped after %s pages to avoid an unbounded loop." % MAX_PAGES)

        LOGGER.info("Fetching events page %s", page)
        if first_response is not None and page == "1":
            response = first_response
            first_response = None
        else:
            response = request_page(client, url, dict(params, page=page))
        explain_status(response)
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Expected a JSON list from /api/v4/events, got %s" % type(payload).__name__)

        kept = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            if server_filters_by_date or event_is_recent(item, after):
                kept.append(item)
        events.extend(kept)

        next_page = (response.headers.get("X-Next-Page") or "").strip()
        LOGGER.info("Page %s returned %s events; next page=%s", page, len(payload), next_page or "<end>")
        if not next_page or not payload:
            break
        page = next_page
        time.sleep(PAGE_DELAY_SECONDS)

    return events


def save_events(events: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with RAW_EVENTS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(events, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    LOGGER.info("Saved %s events to %s", len(events), RAW_EVENTS_PATH)


def main() -> int:
    load_dotenv()
    try:
        base_url, token = load_gitlab_settings()
    except RuntimeError as exc:
        LOGGER.error("%s", exc)
        return 2

    after = two_years_ago()
    LOGGER.info("Loading all personal activity since %s from %s", after.isoformat(), base_url)
    try:
        events = fetch_events(base_url, token, after)
        save_events(events)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        LOGGER.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
