# Instrumentation بک‌اند (.NET)

## نقطهٔ مشترک

کلاس `Common.Observability.ObservabilityExtensions` در پروژه `Common`.

اگر `OTEL_EXPORTER_OTLP_ENDPOINT` خالی باشد، telemetry ثبت نمی‌شود (no-op). اگر مقدار داشته باشد:

- **Traces:** ASP.NET Core + HttpClient + MassTransit (`DiagnosticHeaders.DefaultListenerName`)
- **Metrics:** ASP.NET Core + HttpClient
- **Export:** `UseOtlpExporter(OtlpExportProtocol.Grpc, new Uri(endpoint))`

لاگ ساخت‌یافته جداگانه است: `WriteToObservabilityOtlp` روی Serilog، پروتکل gRPC، همان endpoint، با `service.name` اختیاری.

نویز Outbox/Inbox MassTransit با `FilterOutboxNoise` از Serilog حذف می‌شود (فیلتر روی `commandText`).

## سرویس‌هایی که `AddObservabilityTelemetry` را صدا می‌زنند

| سرویس | `service.name` در Resource |
|---|---|
| ApiGateway | `ApiGateway` |
| IdentityServer | `IdentityServer` |
| ACLServer | `ACLServer` |
| DCC | `DCC` |
| Reporting | `Reporting` |
| GateServer | `GateServer` |
| RequestTracker | `RequestTracker` |
| BaskoolService | `BaskoolService` |

هر کدام معمولاً `WriteToObservabilityOtlp(..., "<همان نام>")` هم روی Serilog دارند.

## Dejban.Api

ماژول دژبان علاوه بر الگوی بالا، در `Dejban.Common.Infrastructure.InfrastructureConfiguration` OpenTelemetry جدا دارد (وقتی همان کلید endpoint ست باشد):

- AspNetCore، HttpClient
- Entity Framework Core
- Redis
- Npgsql
- MassTransit

این برای waterfall عمیق‌تر داخل Dejban است (DB / Redis / bus).

## نقش ApiGateway در مسیر درخواست

Gateway با YARP درخواست `/api/...` را به سرویس مقصد می‌فرستد. Instrumentation ASP.NET روی درخواست ورودی `traceparent` را می‌خواند و Trace را ادامه می‌دهد. سرویس پایین‌دست دوباره ASP.NET است و همان context را می‌گیرد.

در Tempo انتظار این است:

1. span کلاینت: `frontend-*`
2. span سرور: `ApiGateway`
3. span سرور: `Dejban.Api` یا `ACLServer` یا …

اگر YARP برای hop خروجی span جدا نسازد، باز هم دو span سرور در یک Trace دیده می‌شوند؛ این برای پاسخ به «درخواست به کجا رسید» کافی است.

## پیکربندی محیط

| فایل | مقدار نمونه |
|---|---|
| `globalAppsettings.json` / Development / Production | `http://localhost:4317` (Alloy روی host در حالت development) |
| `globalAppsettings.Docker.json` | `http://alloy:4317` |
| `globalAppsettings.DockerDevelopment.json` | `http://alloy:4317` |
| Compose overlay Docker | env `OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4317` |

`globalAppsettings-sample.json` مقدار خالی دارد تا telemetry در نمونه خاموش بماند.

## آنچه بک‌اند عمداً انجام نمی‌دهد

- ارسال مستقیم به Loki/Tempo بدون Alloy
- احراز هویت روی Loki (`auth_enabled: false` در این استقرار)
- داشبورد Stimulsoft به‌جای Grafana برای این سیگنال‌ها
