# gitlab-activity-report

Personal GitLab activity report for the last two years. It reads **your** events from `GET /api/v4/events` (every project on the instance), not a single repository.

The Dejban backend and frontend live on `http://192.168.1.8`. Point `GITLAB_URL` at that host and use a personal access token for your own user. The feed then includes every project you acted on.

## Setup

Python 3.6 or newer.

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Meaning |
|---|---|
| `GITLAB_URL` | Instance origin, for example `http://192.168.1.8` |
| `GITLAB_TOKEN` | Personal access token with the `read_api` scope |

Create the token in GitLab under **User Settings → Access Tokens**. A project token or a token limited to one repository will not return your full activity.

The client sends the token as `PRIVATE-TOKEN`. If GitLab answers 401, it retries once with `Authorization: Bearer` (OAuth access tokens on this instance).

## Run

```bash
bash run.sh
```

`run.sh` installs `requirements.txt`, then runs:

1. `fetch_events.py` — pages through `/api/v4/events` with `per_page=100`, follows `X-Next-Page`, waits 0.3s between pages, writes `data/events_raw.json`.
2. `generate_report.py` — aggregates with pandas into `data/events_summary.csv` and writes `report.html`.

Open `report.html` in a browser. Charts load Chart.js from the jsDelivr CDN, and the aggregated series are embedded in the page.

## Output

`data/events_summary.csv` has three dimensions in one table:

| dimension | key | count |
|---|---|---|
| `month` | `YYYY-MM` | events that month |
| `action` | `action_name` | events with that action |
| `project` | `path_with_namespace` | events on that project |

The HTML header shows total events, the most active month, and the most common action. Charts: monthly line, action doughnut, top 10 projects.

`data/`, `.env`, and `report.html` are gitignored.
