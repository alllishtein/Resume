"""Aggregate GitLab events and write a self-contained Chart.js report."""

from __future__ import print_function

import json
import logging
import sys
import time
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv

from gitlab_client import GitLabClient

from settings import (
    DATA_DIR,
    PROJECT_CACHE_PATH,
    RAW_EVENTS_PATH,
    REPORT_PATH,
    SUMMARY_PATH,
    load_gitlab_settings,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger("generate_report")

PROJECT_LOOKUP_DELAY_SECONDS = 0.1
REQUEST_TIMEOUT_SECONDS = 60


def load_events() -> List[Dict[str, Any]]:
    if not RAW_EVENTS_PATH.is_file():
        raise RuntimeError("Missing %s. Run fetch_events.py first." % RAW_EVENTS_PATH)
    with RAW_EVENTS_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise RuntimeError("events_raw.json must be a JSON list.")
    events = [item for item in payload if isinstance(item, dict)]
    LOGGER.info("Loaded %s events from %s", len(events), RAW_EVENTS_PATH)
    return events


def load_project_cache() -> Dict[str, str]:
    if not PROJECT_CACHE_PATH.is_file():
        return {}
    try:
        with PROJECT_CACHE_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("Ignoring unreadable project cache: %s", exc)
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): str(value) for key, value in payload.items()}


def save_project_cache(names: Dict[str, str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PROJECT_CACHE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(names, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def resolve_project_names(events: List[Dict[str, Any]]) -> Dict[str, str]:
    """Map project id to path_with_namespace.

    User events often carry only project_id. Names are resolved so the report
    can rank projects. Failures fall back to project:<id>.
    """
    names = load_project_cache()
    needed = set()
    for event in events:
        project = event.get("project")
        if isinstance(project, dict):
            label = project.get("path_with_namespace") or project.get("name_with_namespace") or project.get("name")
            project_id = event.get("project_id")
            if label and project_id is not None:
                names[str(project_id)] = str(label)
        project_id = event.get("project_id")
        if project_id is not None and str(project_id) not in names:
            needed.add(str(project_id))

    if not needed:
        return names

    try:
        base_url, token = load_gitlab_settings()
    except RuntimeError as exc:
        LOGGER.warning("Project names will use ids because GitLab settings are unavailable: %s", exc)
        return names

    client = GitLabClient(token)
    LOGGER.info("Resolving %s project names", len(needed))
    for index, project_id in enumerate(sorted(needed, key=lambda value: int(value) if value.isdigit() else value)):
        if index:
            time.sleep(PROJECT_LOOKUP_DELAY_SECONDS)
        url = "%s/api/v4/projects/%s" % (base_url, project_id)
        try:
            response = client.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        except RuntimeError as exc:
            LOGGER.warning("Project %s lookup failed: %s", project_id, exc)
            names[project_id] = "project:%s" % project_id
            continue
        if response.status_code != 200:
            LOGGER.warning("Project %s lookup returned HTTP %s", project_id, response.status_code)
            names[project_id] = "project:%s" % project_id
            continue
        body = response.json()
        label = ""
        if isinstance(body, dict):
            label = str(
                body.get("path_with_namespace")
                or body.get("name_with_namespace")
                or body.get("name")
                or ""
            )
        names[project_id] = label or ("project:%s" % project_id)

    save_project_cache(names)
    return names


def project_label(event: Dict[str, Any], names: Dict[str, str]) -> str:
    project = event.get("project")
    if isinstance(project, dict):
        label = project.get("path_with_namespace") or project.get("name_with_namespace") or project.get("name")
        if label:
            return str(label)
    project_id = event.get("project_id")
    if project_id is None:
        return "(no project)"
    return names.get(str(project_id), "project:%s" % project_id)


def build_frame(events: List[Dict[str, Any]], names: Dict[str, str]) -> pd.DataFrame:
    rows = []
    for event in events:
        rows.append(
            {
                "created_at": event.get("created_at"),
                "action_name": event.get("action_name") or "(unknown)",
                "project": project_label(event, names),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["created_at", "action_name", "project", "month"])
    frame["created_at"] = pd.to_datetime(frame["created_at"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["created_at"])
    frame["month"] = frame["created_at"].dt.strftime("%Y-%m")
    frame["action_name"] = frame["action_name"].astype(str)
    frame["project"] = frame["project"].astype(str)
    return frame


def counts_frame(frame: pd.DataFrame, column: str, dimension: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["dimension", "key", "count"])
    grouped = frame.groupby(column).size().reset_index()
    grouped.columns = ["key", "count"]
    grouped.insert(0, "dimension", dimension)
    grouped["count"] = grouped["count"].astype(int)
    return grouped.sort_values(["count", "key"], ascending=[False, True])


def summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    parts = [
        counts_frame(frame, "month", "month").sort_values("key"),
        counts_frame(frame, "action_name", "action"),
        counts_frame(frame, "project", "project"),
    ]
    summary = pd.concat(parts, ignore_index=True)
    return summary[["dimension", "key", "count"]]


def month_series(frame: pd.DataFrame) -> List[Dict[str, Any]]:
    if frame.empty:
        return []
    counted = frame.groupby("month").size()
    start = pd.Period(counted.index.min(), freq="M")
    end = pd.Period(counted.index.max(), freq="M")
    full_index = pd.period_range(start, end, freq="M").astype(str)
    filled = counted.reindex(full_index, fill_value=0)
    return [{"month": str(month), "count": int(count)} for month, count in filled.items()]


def action_series(frame: pd.DataFrame) -> List[Dict[str, Any]]:
    if frame.empty:
        return []
    counted = frame.groupby("action_name").size().sort_values(ascending=False)
    return [{"action": str(action), "count": int(count)} for action, count in counted.items()]


def project_series(frame: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
    if frame.empty:
        return []
    counted = frame.groupby("project").size().sort_values(ascending=False).head(limit)
    return [{"project": str(project), "count": int(count)} for project, count in counted.items()]


def stats_for(frame: pd.DataFrame, months: List[Dict[str, Any]], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = int(len(frame))
    if not months:
        most_month = "—"
    else:
        best = max(months, key=lambda item: (item["count"], item["month"]))
        most_month = "%s (%s)" % (best["month"], best["count"])
    if not actions:
        most_action = "—"
    else:
        best_action = max(actions, key=lambda item: (item["count"], item["action"]))
        most_action = "%s (%s)" % (best_action["action"], best_action["count"])
    return {
        "total": total,
        "most_active_month": most_month,
        "most_common_action": most_action,
    }


def html_document(payload: Dict[str, Any]) -> str:
    embedded = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitLab activity report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"></script>
  <style>
    :root {
      --bg: #f4f1ea;
      --ink: #1c1915;
      --muted: #5e584e;
      --card: #fffdf8;
      --line: #e4dccb;
      --accent: #0f6e6e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    main { max-width: 1100px; margin: 0 auto; padding: 32px 20px 64px; }
    h1 { font-size: 32px; margin: 0 0 8px; }
    .lede { color: var(--muted); margin: 0 0 24px; }
    .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
    .stat, .panel {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px 18px;
    }
    .stat span { display: block; color: var(--muted); font-size: 13px; }
    .stat strong { display: block; margin-top: 6px; font-size: 22px; }
    .grid { display: grid; grid-template-columns: 1.4fr 0.8fr; gap: 12px; }
    .panel h2 { margin: 0 0 12px; font-size: 16px; }
    .full { margin-top: 12px; }
    canvas { width: 100%; max-height: 360px; }
    @media (max-width: 800px) {
      .stats, .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <h1>GitLab activity</h1>
    <p class="lede" id="range"></p>
    <section class="stats">
      <article class="stat"><span>Total events</span><strong id="total"></strong></article>
      <article class="stat"><span>Most active month</span><strong id="month"></strong></article>
      <article class="stat"><span>Most common action</span><strong id="action"></strong></article>
    </section>
    <section class="grid">
      <article class="panel">
        <h2>Activity per month</h2>
        <canvas id="byMonth"></canvas>
      </article>
      <article class="panel">
        <h2>Action types</h2>
        <canvas id="byAction"></canvas>
      </article>
    </section>
    <article class="panel full">
      <h2>Top 10 projects</h2>
      <canvas id="byProject"></canvas>
    </article>
  </main>
  <script>
    const REPORT = __EMBEDDED__;
    document.getElementById("total").textContent = REPORT.total;
    document.getElementById("month").textContent = REPORT.most_active_month;
    document.getElementById("action").textContent = REPORT.most_common_action;
    document.getElementById("range").textContent =
      "Personal activity across every project. " + REPORT.total + " events.";

    const palette = ["#0f6e6e", "#c46b3a", "#2f5d50", "#d4a017", "#6d4c7d", "#3d6b99", "#8c4a3a", "#4f7d4a", "#9a6b2f", "#355c7d"];

    new Chart(document.getElementById("byMonth"), {
      type: "line",
      data: {
        labels: REPORT.by_month.map((item) => item.month),
        datasets: [{
          label: "Events",
          data: REPORT.by_month.map((item) => item.count),
          borderColor: "#0f6e6e",
          backgroundColor: "rgba(15, 110, 110, 0.15)",
          fill: true,
          tension: 0.25,
          pointRadius: 3
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });

    new Chart(document.getElementById("byAction"), {
      type: "doughnut",
      data: {
        labels: REPORT.by_action.map((item) => item.action),
        datasets: [{
          data: REPORT.by_action.map((item) => item.count),
          backgroundColor: REPORT.by_action.map((_, index) => palette[index % palette.length])
        }]
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } }
    });

    new Chart(document.getElementById("byProject"), {
      type: "bar",
      data: {
        labels: REPORT.by_project.map((item) => item.project),
        datasets: [{
          label: "Events",
          data: REPORT.by_project.map((item) => item.count),
          backgroundColor: "#c46b3a"
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  </script>
</body>
</html>
""".replace("__EMBEDDED__", embedded)


def main() -> int:
    load_dotenv()
    try:
        events = load_events()
        names = resolve_project_names(events)
        frame = build_frame(events, names)
        summary = summary_table(frame)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        summary.to_csv(SUMMARY_PATH, index=False)
        LOGGER.info("Wrote %s", SUMMARY_PATH)

        months = month_series(frame)
        actions = action_series(frame)
        projects = project_series(frame)
        header = stats_for(frame, months, actions)
        payload = {
            "total": header["total"],
            "most_active_month": header["most_active_month"],
            "most_common_action": header["most_common_action"],
            "by_month": months,
            "by_action": actions,
            "by_project": projects,
        }
        REPORT_PATH.write_text(html_document(payload), encoding="utf-8")
        LOGGER.info("Wrote %s", REPORT_PATH)
    except (RuntimeError, ValueError, OSError, pd.errors.ParserError) as exc:
        LOGGER.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
