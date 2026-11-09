# فرانت‌اند: Trace مرورگر و لاگ کانتینر

Compose فرانت در مخزن `dejban_frontend_new` است، شبکه `dejban-frontend`، جدا از `backend`. کانتینرها: `frontend-nginx`، `frontend-main`، `frontend-dejban`، `frontend-gate`، `frontend-dcc`، `frontend-access-control`.

دو کانال جدا:

| کانال | منبع | مقصد |
|---|---|---|
| Trace درخواست API | مرورگر / Axios | Alloy `:4318` از طریق Nginx `/otel/` → Tempo |
| Log فرآیند Node/Nginx | stdout کانتینر | Alloy `loki.source.docker` → Loki |

`console.log` داخل Chrome به Loki نمی‌رود مگر از مرورگر OTLP/log جدا ارسال شود. این پیاده‌سازی روی **درخواست‌های HTTP Axios** و **stdout کانتینر** متمرکز است.

## Tracing مرورگر

فایل: `packages/api-client/src/browserTracing.ts`  
اتصال: interceptor در `packages/api-client/src/axiosInstance.ts`

رفتار:

1. فقط در `window` (نه SSR)
2. OpenTelemetry Web SDK + exporter OTLP HTTP
3. هر درخواست Axios یک span از نوع CLIENT
4. تزریق `traceparent` / `tracestate`
5. پایان span با `http.status_code`؛ وضعیت خطا برای 4xx/5xx
6. URL شامل `/otel/` span نمی‌شود (جلوگیری از حلقه)

`service.name` از pathname:

| Path | service.name |
|---|---|
| `/dejban` | `frontend-dejban` |
| `/gate` | `frontend-gate` |
| `/dcc` | `frontend-dcc` |
| `/access-control` | `frontend-access-control` |
| سایر (اپ main) | `frontend-main` |

آدرس exporter پیش‌فرض: `{origin}/otel/v1/traces`  
بازنویسی: `NEXT_PUBLIC_OTEL_EXPORTER_URL` یا `VITE_OTEL_EXPORTER_URL`

مرورگر باید از **همان originی که Nginx است** باز شود (پورت `FRONTEND_PORT` پیش‌فرض 3080، یا دامنه production). باز کردن مستقیم پورت 3000 کانتینر Next مسیر `/otel` ندارد.

## Nginx

`docker/nginx/default.conf.template`:

```nginx
location /otel/ {
  proxy_pass http://$otel_collector/;
}
```

`/otel/v1/traces` → `http://<collector>/v1/traces`.

متغیر Compose: `OTEL_COLLECTOR` پیش‌فرض `host.docker.internal:4318`.

`/api/` همچنان به ApiGateway می‌رود؛ `traceparent` روی آن مسیر حفظ می‌شود.

## لاگ Docker فرانت

Alloy فقط کانتینرهایی را نگه می‌دارد که `__meta_docker_container_name` با `/frontend-.*` جور باشد. Labelها: `container`، `job=frontend-docker`.

کوئری Loki:

```logql
{job="frontend-docker"}
```

```logql
{container="frontend-dejban"}
```

برای این مسیر، فرانت و Alloy باید روی یک daemon باشند و mount سوکت Docker در Alloy برقرار باشد.
