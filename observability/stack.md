# پشته Grafana (Compose بک‌اند)

تعریف سرویس‌ها در `docker-compose.yml`. پورت‌های اضافی توسعه در `docker-compose.development.yml`. استقرار production پیش‌فرض: `docker-compose.yml` + `docker-compose.docker-production.yml`.

## سرویس‌ها و نسخه (از Compose)

| سرویس | Image | نقش | پورت داخلی | Publish روی host |
|---|---|---|---|---|
| `grafana` | `grafana/grafana:11.5.2` | UI | 3000 | **3000:3000** (فایل پایه) |
| `alloy` | `grafana/alloy:v1.8.3` | دریافت OTLP و Docker logs | 4317 gRPC، 4318 HTTP، 12345 UI Alloy | **4318:4318** در فایل پایه؛ در development همچنین 4317 و 12345 |
| `loki` | `grafana/loki:3.7.0` | ذخیره log | 3100 | فقط development: 3100 |
| `tempo` | `grafana/tempo:2.7.2` | ذخیره trace | 3200 HTTP، 4317 OTLP | فقط development: 3200 |
| `prometheus` | `prom/prometheus:v3.5.0` | ذخیره metric؛ `web.enable-remote-write-receiver` روشن است | 9090 | فقط development: 9090 |

Volumeهای ماندگار: `grafana-data`، `loki-data`، `tempo-data`، `prometheus-data`.

شبکه: `backend` (bridge، subnet `10.10.0.0/24`).

## Grafana

- کاربر: `admin`
- رمز: `GRAFANA_ADMIN_PASSWORD` در `.env`؛ اگر نباشد پیش‌فرض `admin`
- `GF_AUTH_ANONYMOUS_ENABLED=false`
- Datasourceها از `Observability/grafana/provisioning/datasources/datasources.yaml` لود می‌شوند:

| Name | UID | URL داخل شبکه Docker |
|---|---|---|
| Prometheus | `prometheus` | `http://prometheus:9090` (isDefault) |
| Loki | `loki` | `http://loki:3100` |
| Tempo | `tempo` | `http://tempo:3200` |

**نکته URL Loki:** مقدار باید `http://loki:3100` باشد، نه `http://loki:3100/loki`. Grafana خودش مسیر `/loki/api/v1/...` را اضافه می‌کند. اگر `/loki` در URL datasource باشد، درخواست `.../loki/loki/api/...` می‌شود و پاسخ **404** است.

پوشه `Observability/grafana/provisioning/dashboards/` خالی است (فقط `.gitkeep`). داشبورد از پیش provision نشده؛ کار عملیاتی با **Explore** است.

## Alloy — `Observability/alloy/config.alloy`

1. `otelcol.receiver.otlp` روی `0.0.0.0:4317` و `:4318`
2. `otelcol.processor.batch`
3. logs → exporter Loki → `http://loki:3100/loki/api/v1/push`
4. traces → OTLP به `tempo:4317` با TLS insecure
5. metrics → Prometheus remote-write به `http://prometheus:9090/api/v1/write`
6. `discovery.docker` + `loki.source.docker` برای کانتینرهایی که نامشان با `/frontend-` شروع می‌شود؛ label `job=frontend-docker`

Socket: `/var/run/docker.sock` به صورت read-only به کانتینر Alloy mount می‌شود. فرانت و بک‌اند باید روی **یک Docker Engine** باشند.

## Loki — `Observability/loki/loki-config.yaml`

- `auth_enabled: false`
- `common.path_prefix: /loki` مسیر **دیسک** است، پیشوند HTTP API نیست
- schema v13 / tsdb، filesystem
- `allow_structured_metadata: true`
- `volume_enabled: true` — API حجم لاگ Grafana 11 (`/loki/api/v1/index/volume`) بدون این کلید 404 می‌دهد

## Tempo — `Observability/tempo/tempo.yaml`

- HTTP listen: 3200
- OTLP gRPC/HTTP روی 4317/4318 داخل خود Tempo
- ذخیره local: `/var/tempo/wal` و `/var/tempo/blocks`
- **نگهداری بلوک: 24 ساعت** (`block_retention`)

## Prometheus — `Observability/prometheus/prometheus.yml`

- scrape فقط `localhost:9090` (خود Prometheus)
- متریک اپ از **remote write** Alloy می‌آید، نه از scrape جداگانه هر microservice

## متغیر محیطی سرویس‌های اپ

در `docker-compose.docker-production.yml` و `docker-compose.docker-development.yml` برای ApiGateway و میکروسرویس‌ها:

```text
OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4317
```

همان کلید در `GlobalAppsettings/globalAppsettings.Docker.json` و `globalAppsettings.DockerDevelopment.json` هم هست. کد exporter از **IConfiguration** همین کلید را به URI gRPC می‌دهد تا به `localhost:4317` داخل کانتینر نرود.
