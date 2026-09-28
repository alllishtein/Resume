# رزومه — نسخه حرفه‌ای (بر اساس استک Dejban)

> **راهنما:** موارد داخل `[...]` را با اطلاعات واقعی خودت عوض کن.  
> فرض این نسخه: روی کل کتابچه‌های Day 00–67 مسلطی و می‌توانی در مصاحبه با مثال از پروژه توضیح بدهی.

---

## [نام و نام خانوادگی]

**Full-Stack .NET / React Developer**

📍 [شهر] · 📧 [email] · 📱 [موبایل] · 🔗 [LinkedIn / GitHub]

---

### خلاصه حرفه‌ای

توسعه‌دهنده فول‌استک با تمرکز روی **بک‌اند سازمانی با C# / ASP.NET Core** و **فرانت‌اند با React / Next.js** در پلتفرم چندسرویسی امنیت و کنترل دسترسی (ماژولار مونولیت + میکروسرویس). تجربه کار با معماری **CQRS / DDD / Event-driven**، پیام‌رسانی **MassTransit + RabbitMQ**، کش و Realtime (**Redis / HybridCache / SignalR**)، و فرانت‌اند مدرن (**TanStack Query، RHF+Zod، MUI، Turborepo**). قادر به توضیح end-to-end یک request از مرورگر تا Gateway، دامنه، دیتابیس و event — و دفاع از تصمیم‌های معماری در مصاحبه.

---

### مهارت‌های فنی

#### Backend / .NET
- C# (async/await، concurrency، GC)
- ASP.NET Core (Pipeline، DI، Minimal APIs، Options، Health Checks)
- **CQRS** با MediatR + Pipeline Behaviors
- **DDD**: Aggregate، Domain Event، Value Object، Soft Delete
- EF Core + Npgsql (multi-schema)، Repository / Unit of Work، Dapper
- **Transactional Outbox / Inbox** (custom + MassTransit EF Outbox)، Idempotent Handler
- MassTransit + RabbitMQ (Publish/Consume + **Request/Response**)
- JWT Bearer، Token Blacklist، ASP.NET Identity، Permission Claims
- YARP Reverse Proxy، Rate Limiting، Output Caching، API Versioning
- Redis / HybridCache، SignalR، gRPC
- MinIO / S3، Polly، Serilog + Seq + OpenTelemetry
- Quartz / Hangfire، Mapster، FluentValidation + ErrorOr
- Factory / Strategy، Decorator (Scrutor)
- PostgreSQL (**LISTEN/NOTIFY**)، گزارش‌گیری (read-model + capability ticket)

#### Frontend
- JavaScript، React 19، Next.js 16 (App Router، basePath، rewrites)
- Turborepo / npm workspaces، Vite + React Router (SPA)
- TanStack Query (incl. **useInfiniteQuery**)، Axios (single-flight refresh + httpOnly cookie)
- React Hook Form + Zod، Zustand + immer
- MUI 7 + Emotion + RTL، i18next + Jalali
- Auth Guards / component-level permissions، SignalR client
- material-react-table، SWR (parallel stack)
- MapLibre، TipTap، Recharts / ApexCharts، jsPDF
- Playwright، Vitest

#### Architecture & Delivery
- Microservices vs Modular Monolith، System Design پایه
- Multi-tenancy (`X-Site-Id`)
- Docker / Compose، GitLab CI، PM2
- xUnit، NetArchTest، Testcontainers، Bogus
- Algorithms / Big-O (آمادگی مصاحبه)

---

### پروژه شاخص — پلتفرم امنیت و دسترسی (Dejban)

**نقش:** Full-Stack Developer · **استک:** .NET 10 · Next.js · PostgreSQL · Redis · RabbitMQ · MinIO

پلتفرم سازمانی چندسایته برای پرسنل، بازدیدکننده، خودرو، ACL/دستگاه، گیت، کارتابل، انبار/تسلیحات، گزارش و فایل.

**نمونه‌هایی که می‌توانی در مصاحبه باز کنی (با جزئیات کتابچه):**

- طراحی و کار روی **ماژولار مونولیت** (چند bounded context در یک process) کنار میکروسرویس‌های جدا (Identity، ACL، DCC، Reporting، Gateway)
- پیاده‌سازی جریان‌های **CQRS** با MediatR، Validation، و انتشار Domain/Integration Event
- تضمین پیام‌رسانی قابل‌اطمینان با **Transactional Outbox / Inbox** و پردازش Idempotent
- احراز هویت end-to-end: JWT + refresh (httpOnly) + blacklist + permission claims + گارد UI
- Realtime: SignalR سمت سرور/کلاینت؛ الگوی **Postgres LISTEN/NOTIFY → SignalR** برای رویدادهای DB-origin
- Gateway با YARP + Rate Limit / Output Cache؛ نسخه‌بندی API
- فرانت مونوریپو (Turborepo): چند اپ Next با `basePath`/`rewrites`، Query+Axios service folders، جداول سروری MRT، فرم‌های RHF+Zod
- تست: xUnit + Architecture Tests، Testcontainers، Playwright E2E؛ دیپلوی FE با GitLab CI + PM2

---

### نقاط قوت مصاحبه‌ای (یک خطی)

| موضوع | جمله‌ای که آماده داری |
|---|---|
| Outbox | «پیام و state کسب‌وکار در یک تراکنش؛ بعد dispatcher می‌فرستد تا dual-write از بین برود.» |
| Modular Monolith | «مرز دامنه مثل میکروسرویس، دیپلوی یک process؛ وقتی نیاز شد extract می‌کنیم.» |
| Multi-tenancy | «Scope سایت از `X-Site-Id` + claim؛ روی HTTP و تا حدی روی bus.» |
| FE data | «Server state با TanStack Query؛ UI state با Zustand؛ فرم با RHF+Zod.» |
| Auth FE | «Access در memory/storage؛ refresh در httpOnly؛ single-flight روی 401.» |

---

### تحصیلات

- [مقطع، رشته، دانشگاه، سال]

---

### زبان

- فارسی: بومی
- انگلیسی: [سطح — مثلاً خواندن مستندات فنی / Intermediate]

---

### نسخه انگلیسی Summary (برای LinkedIn / اپلای بین‌المللی)

Full-stack developer focused on **C# / ASP.NET Core** backends and **React / Next.js** frontends in a multi-service access-control platform (modular monolith + microservices). Hands-on with **CQRS/DDD**, **MassTransit/RabbitMQ** (including request/response), **Transactional Outbox/Inbox**, **Redis/HybridCache**, **SignalR**, **gRPC**, and a Turborepo FE stack (**TanStack Query**, RHF+Zod, MUI, Playwright). Comfortable explaining end-to-end request flow and defending architectural trade-offs in interviews.

---

### نکات استفاده

1. اعداد سال تجربه و نام شرکت را فقط اگر واقعی است اضافه کن.  
2. از لیست مهارت‌ها فقط چیزهایی را در نسخه کوتاه رزومه بگذار که تیک چک‌لیست را زده‌ای.  
3. برای هر آگهی، ۳–۵ بولت پروژه را با کلیدواژه‌های همان آگهی پررنگ کن.  
4. فایل چک‌لیست: [`mastery-checklist.md`](./mastery-checklist.md)
