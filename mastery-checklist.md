# چک‌لیست تسلط — کتابچه Dejban (Day 00–67)

**هدف:** هر ردیف را وقتی می‌توانی **بدون نگاه به کتابچه** در ~۱ دقیقه توضیح بدهی + یک مثال از کد/جریان پروژه بگویی، تیک بزن.

**قانون تیک:**

- [ ] هنوز نخوانده / بلد نیستم
- [x] مسلطم (مصاحبه OK)

**پیشنهاد:** اول Backend پایه → Messaging → Infra → Auth → FE → Testing → Tech 60–67.

پیشرفت کلی: **۰ / ۶۸** (Day 00–67)

---

## فاز ۰ — Orientation

- [ ] **Day 00** — نقشه پروژه، lifecycle request، glossary، سه ریپو

---

## فاز ۱ — پایه Backend

- [ ] **Day 01** — HTTP / REST / Web
- [ ] **Day 02** — C# async / concurrency / GC
- [ ] **Day 03** — OOP + SOLID + patterns
- [ ] **Day 04** — SQL + relational DB
- [ ] **Day 05** — ASP.NET Core pipeline / DI
- [ ] **Day 06** — JWT Bearer + token blacklist
- [ ] **Day 07** — YARP Reverse Proxy
- [ ] **Day 08** — System design (پایه)

---



## فاز ۲ — معماری دامنه

- [ ] **Day 09** — Microservices vs Modular Monolith + DDD layering
- [ ] **Day 10** — CQRS + MediatR + Pipeline Behaviors
- [ ] **Day 11** — FluentValidation + ErrorOr
- [ ] **Day 12** — Aggregate / Domain Event / Value Object
- [ ] **Day 13** — EF Core + Npgsql (multi-schema, migrations)
- [ ] **Day 14** — Repository + Unit of Work
- [ ] **Day 15** — Soft Delete
- [ ] **Day 16** — Multi-tenancy (`X-Site-Id`)
- [ ] **Day 17** — Minimal APIs + `IEndpoint`
- [ ] **Day 18** — Modular DI (`AddXxxModule`)

---



## فاز ۳ — Messaging & Consistency

- [ ] **Day 19** — Dapper (outbox/inbox)
- [ ] **Day 20** — MassTransit + RabbitMQ (pub/sub)
- [ ] **Day 21** — Transactional Outbox (custom Dejban)
- [ ] **Day 22** — MassTransit EF Outbox
- [ ] **Day 23** — Inbox + Idempotent Handler
- [ ] **Day 24** — Decorator (Scrutor)

---



## فاز ۴ — Infra & Platform

- [ ] **Day 25** — HybridCache + Redis
- [ ] **Day 26** — SignalR (server)
- [ ] **Day 27** — gRPC (ZK / Tiam / Virdi)
- [ ] **Day 28** — MinIO / S3
- [ ] **Day 29** — Quartz + Hangfire
- [ ] **Day 30** — Serilog + Seq + OpenTelemetry
- [ ] **Day 31** — Health + Docker + EF migration / migrationesho
- [ ] **Day 32** — Polly
- [ ] **Day 33** — OpenAPI + Scalar
- [ ] **Day 34** — Options pattern
- [ ] **Day 35** — Factory + Strategy (device sync)

---



## فاز ۵ — Identity، فایل، گزارش

- [ ] **Day 36** — ASP.NET Identity
- [ ] **Day 37** — Permission claims
- [ ] **Day 38** — Excel import
- [ ] **Day 39** — Stimulsoft + ImageSharp
- [ ] **Day 40** — Auth end-to-end
- [ ] **Day 41** — Files/Documents (Dejban → DCC)

---



## فاز ۶ — Frontend

- [ ] **Day 42** — Next.js 16 + React 19
- [ ] **Day 43** — Turborepo + workspaces
- [ ] **Day 44** — TanStack Query + Axios
- [ ] **Day 45** — React Hook Form + Zod
- [ ] **Day 46** — Zustand + immer
- [ ] **Day 47** — MUI 7 + Emotion + RTL
- [ ] **Day 48** — i18next + Jalali
- [ ] **Day 49** — Auth UI / Guards / `componentId`
- [ ] **Day 50** — SignalR client
- [ ] **Day 51** — FE patterns (`*.http` / keys / service)
- [ ] **Day 52** — material-react-table
- [ ] **Day 53** — SWR
- [ ] **Day 54** — Vite + React Router SPA
- [ ] **Day 65** — Next.js basePath + rewrites *(با Day 42/54 بخوان)*
- [ ] **Day 66** — useInfiniteQuery + refresh single-flight *(با Day 40/44)*
- [ ] **Day 67** — MapLibre + TipTap + Charts + jsPDF

---



## فاز ۷ — تست و CI

- [ ] **Day 55** — Playwright + Vitest
- [ ] **Day 56** — xUnit + NetArchTest
- [ ] **Day 57** — Testcontainers + Bogus
- [ ] **Day 58** — GitLab CI + PM2

---



## فاز ۸ — مصاحبه الگوریتم

- [ ] **Day 59** — Algorithms + Big-O

---



## فاز ۹ — Tech عمیق (رزومه / مصاحبه)

- [ ] **Day 60** — Mapster
- [ ] **Day 61** — Postgres LISTEN/NOTIFY → SignalR
- [ ] **Day 62** — MassTransit Request/Response
- [ ] **Day 63** — Rate limiting + Output cache + API versioning
- [ ] **Day 64** — Reporting read-model + capability tickets

---



## خودآزمایی سریع (قبل از ارسال رزومه)

وقتی این‌ها را تیک زدی، نسخه کامل مهارت‌های `resume-professional.md` را استفاده کن:

### Backend must-pass

- [ ] Outbox را در ۳۰ ثانیه توضیح می‌دهم
- [ ] تفاوت Modular Monolith و Microservice را با مثال Dejban می‌گویم
- [ ] JWT + blacklist + refresh را end-to-end می‌کشم
- [ ] YARP نقش Gateway را می‌گویم
- [ ] SignalR vs LISTEN/NOTIFY را مقایسه می‌کنم
- [ ] MassTransit Publish vs Request/Response را فرق می‌گذارم



### Frontend must-pass

- [ ] Server state (Query) vs Client state (Zustand) را فرق می‌گذارم
- [ ] RHF + Zod را با مثال می‌گویم
- [ ] Guard / componentId را توضیح می‌دهم
- [ ] basePath + rewrites را می‌گویم
- [ ] single-flight refresh + httpOnly را توضیح می‌دهم
- [ ] MRT server pagination را می‌گویم



### Delivery must-pass

- [ ] Docker / health / migrationesho را در حد مصاحبه بلدم
- [ ] Playwright vs xUnit vs Testcontainers را لایه‌بندی می‌کنم
- [ ] GitLab CI + PM2 جریان FE را بلدم

---



## لاگ پیشرفت شخصی


| تاریخ | Days تیک‌خورده (شماره) | یادداشت |
| ----- | ---------------------- | ------- |
|       |                        |         |
|       |                        |         |


---



## لینک‌ها

- رزومه: `[resume-professional.md](./resume-professional.md)`
- فهرست کتابچه‌ها: `[README.md](./README.md)`

