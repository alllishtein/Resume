# Observability و Monitoring در دژبان

این پوشه مستند پیاده‌سازی مشاهده‌پذیری سامانه دژبان است: جمع‌آوری **log**، **trace** و **metric** از فرانت‌اند و بک‌اند، و نمایش آن‌ها در Grafana.

مخاطب: ارائه پروژه، استقرار، نگهداری، و پشتیبانی.

## مسئله

سامانه چند پردازه است (Nginx، اپ‌های Next.js، ApiGateway/YARP، Identity، Dejban، ACL، DCC، Reporting، Gate، RequestTracker). بدون استاندارد مشترک، هر خطا فقط در `docker logs` یک کانتینر دیده می‌شود و مسیر درخواست از کلیک کاربر تا دیتابیس گم می‌شود.

هدف پیاده‌سازی:

1. دیدن لاگ سرویس‌ها در یک UI (Grafana / Loki)
2. دیدن مسیر یک درخواست HTTP از مرورگر تا microservice مقصد (Grafana / Tempo)
3. همبسته‌کردن log و trace با `TraceId`
4. متریک ASP.NET از طریق Prometheus

## اسناد

| فایل | محتوا |
|---|---|
| [architecture.md](architecture.md) | معماری، جریان داده، استاندارد OTLP و `traceparent` |
| [stack.md](stack.md) | Grafana، Alloy، Loki، Tempo، Prometheus و Compose |
| [backend.md](backend.md) | Instrumentation در سرویس‌های .NET |
| [frontend.md](frontend.md) | Tracing مرورگر، Axios، Nginx `/otel`، لاگ کانتینر فرانت |
| [operations.md](operations.md) | استقرار، پورت‌ها، Grafana Explore، کوئری‌ها، محدودیت‌ها |
| [support-guide.md](support-guide.md) | آموزش پشتیبان: از گزارش کاربر تا Loki/Tempo و تشخیص محل خطا |

## نتیجه قابل ارائه

پس از استقرار Compose بک‌اند + فرانت Docker:

- Grafana روی `http://<host>:3000`
- Explore → **Loki**: لاگ Serilog سرویس‌ها و stdout کانتینرهای `frontend-*`
- Explore → **Tempo**: waterfall یک درخواست (`frontend-dejban` → `ApiGateway` → `Dejban.Api` / `ACLServer` / …)
- Explore → **Prometheus**: متریک‌هایی که از OTLP به Prometheus remote-write می‌رسند

جزئیات اجرا در [operations.md](operations.md) است.
