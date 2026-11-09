# استقرار، استفاده از Grafana و محدودیت‌ها

## بالا آوردن پشته بک‌اند

Production (نمونه مطابق `deploy/deploy.sh`):

```bash
docker compose -f docker-compose.yml -f docker-compose.docker-production.yml up -d
```

Development با پورت‌های Loki/Tempo/Prometheus روی host:

```bash
docker compose -f docker-compose.yml -f docker-compose.development.yml -f docker-compose.docker-development.yml up -d
```

سپس Grafana: `http://<IP-سرور>:3000`  
ورود: `admin` / مقدار `GRAFANA_ADMIN_PASSWORD` (یا `admin` اگر ست نشده).

پس از عوض کردن YAML Grafana/Loki/Alloy:

```bash
docker compose ... up -d alloy grafana loki
```

سرویس‌های API باید recreate شوند تا env `OTEL_EXPORTER_OTLP_ENDPOINT` اعمال شود.

## فرانت Docker

از مخزن فرانت، بعد از build ایمیج‌هایی که `@repo/api-client` جدید دارند:

```bash
docker compose up -d
```

Nginx به `host.docker.internal:4318` می‌زند؛ Alloy باید 4318 را روی host publish کرده باشد.

بررسی:

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "grafana|alloy"
```

انتظار: `0.0.0.0:3000->3000` و `0.0.0.0:4318->4318`.

## کار با Grafana Explore

### Loki — لاگ اپ

Datasource: **Loki**. بازه: Last 15m / 1h.

```logql
{service_name="ACLServer"}
```

```logql
{service_name=~".+"}
```

لاگ stdout فرانت:

```logql
{job="frontend-docker"}
```

اگر نمودار حجم لاگ 404 بدهد و جدول خالی باشد: URL datasource را `http://loki:3100` چک کنید و `volume_enabled: true` در Loki.

از جزئیات یک خط لاگ، لینک TraceID به Tempo می‌رود اگر فیلد در JSON باشد.

### Tempo — مسیر درخواست

Datasource باید **Tempo** باشد (نه Loki).

Search: Service Name = `frontend-dejban` یا `ApiGateway`.  
TraceQL:

```
{ resource.service.name = "frontend-dejban" }
```

```
{ resource.service.name = "ApiGateway" }
```

```
{}
```

بازه را حداقل یک ساعت بگذارید. نگهداری Tempo در این پیکربندی **۲۴ ساعت** است.

Waterfall سالم: span فرانت → Gateway → microservice. اگر فقط از Gateway به بعد است، مرورگر `traceparent` نفرستاده یا صفحه از origin بدون `/otel` باز شده. اگر Tempo کلاً خالی است، OTLP سرویس‌ها به Alloy نرسیده (endpoint داخل کانتینر اشتباه).

### Prometheus

```promql
up
```

متریک HTTP وابسته به نام‌گذاری exporter است؛ از Metrics browser همان datasource استفاده کنید.

## عیب‌یابی کوتاه

| مشاهده | علت محتمل |
|---|---|
| Grafana روی :3000 باز نمی‌شود | پورت در Compose publish نشده یا firewall |
| Loki 404 | URL datasource با `/loki` اضافه، یا `volume_enabled` خاموش |
| لاگ سرویس هست، Trace نیست | exporter gRPC به `localhost:4317` داخل کانتینر؛ env `http://alloy:4317` نیست |
| Trace از Gateway هست، فرانت نیست | Axios/build قدیمی، یا origin بدون Nginx `/otel` |
| `{job="frontend-docker"}` خالی | سوکت Docker به Alloy نرسیده، یا `container_name` با `frontend-` شروع نمی‌شود |
| Trace دیروز نیست | `block_retention: 24h` در Tempo |

لاگ Collector:

```bash
docker logs --tail 80 $(docker ps -qf name=alloy)
```

## محدودیت‌های این نسخه (صریح)

- داشبورد JSON از پیش در Grafana provision نشده است؛ ارائه عملیاتی با Explore است.
- Prometheus اپ‌ها را scrape نمی‌کند؛ فقط remote-write از Alloy.
- لاگ `console` مرورگر جمع‌آوری نمی‌شود.
- Retention Tempo ۲۴ ساعت است؛ Loki retention جدا در این فایل‌ها به‌صورت نامحدود filesystem است تا دیسک پر شود.
- Loki بدون احراز هویت است؛ Grafana روی 3000 و OTLP روی 4318 روی host باز هستند — برای اینترنت عمومی مناسب نیستند مگر پشت فایروال/VPN.
- Seq و Jaeger در Compose کامنت مانده‌اند و بخشی از این مسیر نیستند.

## چک‌لیست ارائه

1. Grafana login روی پورت 3000  
2. Loki: لاگ یک microservice بعد از یک API واقعی  
3. Loki: `{job="frontend-docker"}` بعد از ترافیک UI  
4. Tempo: یک Trace با سرویس `frontend-*` و `ApiGateway` و سرویس مقصد  
5. کلیک TraceID از لاگ به Tempo  
