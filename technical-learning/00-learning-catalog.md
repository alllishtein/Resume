# کاتالوگ یادگیری — پیشنهاد فاز A

این فهرست سندهایی است که باید بعد از کشف نوشته شوند. خود این فایل یکی از همان سندهای فناوری نیست. هر ردیف یک فایل جدا خواهد بود. پیش‌نیاز یعنی سند دیگری که بهتر است زودتر خوانده شود، نه وابستگی زمان کامپایل.

وضعیت هر ردیف فقط در `00-progress.md` معتبر است. این کاتالوگ موضوع و پیش‌نیاز را نگه می‌دارد.

شاهدهای فاز C درس جدید نیستند: `00-login-execution-path.md`، `00-personnel-list-execution-path.md`، `00-execution-path-index.md`، `00-yarp-config-investigation.md`، و `00-api-path-case-investigation.md`. آخری هنوز اجرای end-to-end ندارد.

این کاتالوگ نام فناوری و پیش‌نیاز را نگه می‌دارد. اتصال درخواست از `Program.cs` تا handler در `00-execution-path-index.md` است، بخش «اتصال‌های تأییدشده». آن جدول را اینجا تکرار نکنید. هر ردیف پایین، وقتی نوشته شود، باید به همان اتصال‌هایی ارجاع بدهد که واقعاً از آن فناوری رد می‌شوند.

| فناوری | کجا در مسیر اجرا دیده می‌شود |
|---|---|
| `01-dotnet-aspnetcore` | `Program.cs` هر سه میزبان، `MapControllers`، `MapEndpoints` |
| `04-yarp` | `AddReverseProxy` تا `auth-login-route-v1` و `personnel-routes-v1` |
| `05-jwt-identity` | `AuthController.Login` تا `LoginCommandHandler` |
| `06-tenancy-authorization` | `X-Site-Id`، `TenantContextMiddleware`، فیلتر `SiteId`، `RequireAuthorization` و StaffView |
| `07-modular-monolith` | ثبت هشت ماژول در `Dejban.Api`، outbox، `PersonnelCreated` به Visitors و سرویس‌های جدا |
| `08-cqrs-mediatr` | `ISender.Send` در هر دو مسیر |
| `09-ef-core-postgresql` | `PersonnelsDbContext` و `ApplicationDbContext` |
| `25-api-client-auth` | `signInWithPassword` و `getStaffWithPagination` |
| `28-nginx-edge` | `location /api/` قبل از gateway |
| `30-request-paths` | خلاصهٔ همان دو مسیر، با ارجاع به سندهای شاهد |

شاهدها در `00-source-evidence-index.md` با مسیر دقیق آمده‌اند. اینجا فقط کافی است معلوم باشد سند به کدام بخش مخزن تکیه می‌کند.

## ترتیب پیشنهادی نوشتن

1. سندهای 01 تا 03، چون بقیه روی میزبان، پیکربندی، و Compose سوار می‌شوند.
2. سند 30، مسیر درخواست، تا بقیهٔ فناوری‌ها یک داستان مشترک داشته باشند.
3. سندهای هویت، دژبان، و داده.
4. سندهای فرانت‌اند.
5. سندهای دستگاه، گزارش، و بازیابی.

## پلتفرم بک‌اند

| شناسه | فایل آینده | موضوع | پیش‌نیاز | شاهد اصلی |
|---|---|---|---|---|
| `01-dotnet-aspnetcore` | `01-dotnet-aspnetcore.md` | .NET 10، generic host، `WebApplication`، middleware، minimal API در برابر controller | — | `Program.cs` سرویس‌ها، `TargetFramework` برابر `net10.0` |
| `02-configuration` | `02-configuration.md` | `GlobalAppsettings`، `appsettings` محیطی، override با environment در Compose | 01 | `AddJsonFile` در `ApiGateway/Program.cs` و `Dejban.Api/Program.cs`؛ `docker/compose.backend.yml` |
| `03-docker-compose` | `03-docker-compose.md` | ادغام سه‌فایلی `start-offline.sh` در برابر Compose جداگانهٔ داده و اپ، شبکه، healthcheck، تصویر بدون tag در برابر کیت DR | 02 | `docker-compose.yml`، `docker-compose.docker-development.yml`، `docker/compose.data.yml`، `docker/compose.backend.yml` |

## ورودی سیستم

| شناسه | فایل آینده | موضوع | پیش‌نیاز | شاهد اصلی |
|---|---|---|---|---|
| `04-yarp` | `04-yarp.md` | YARP 2.3. `LoadFromMemory` صدا زده می‌شود ولی `IdentityServerRoutes.routes` خالی است. route فعال از JSON است. مقصد داکر با sample فرق دارد | 01، 02 | `ApiGateway/Program.cs`، `appsettings.Docker.json`، `IdentityServerRoutes.cs` |
| `05-jwt-identity` | `05-jwt-identity.md` | ASP.NET Core Identity و JWT. access و refresh. این سرویس Duende نیست | 01، 04 | `AuthController.Login`، `TokenProvider`، `AddCustomJwtAuth`، `signInWithPassword` |
| `06-tenancy-authorization` | `06-tenancy-authorization.md` | سایت به‌عنوان tenant، فیلتر EF، `X-Site-Id`، policy و YARP `anonymous`/`default` | 05 | `TenantContextMiddleware.cs`، `TenantQueryFilterExtensions.cs`، `AddAuthorizationInternal`، routeهای YARP |

## دژبان

| شناسه | فایل آینده | موضوع | پیش‌نیاز | شاهد اصلی |
|---|---|---|---|---|
| `07-modular-monolith` | `07-modular-monolith.md` | یک پردازه، هشت ماژول، schema جدا، integration event، مرز compile-time | 01 | `Dejban.Api/Program.cs`، `PersonnelsModule`، `ModuleTests`، قراردادهای `Common.EventBus.Contracts` |
| `08-cqrs-mediatr` | `08-cqrs-mediatr.md` | MediatR 12.5، `ICommand`/`IQuery`، سه pipeline دژبان، تفاوت با domain/integration event | 07 | `ApplicationConfiguration.cs`، `GetPersonnels`، `CreatePersonnel`، outbox |
| `09-ef-core-postgresql` | `09-ef-core-postgresql.md` | EF/Npgsql 10، هشت schema، `PersonnelsDbContext`، فیلتر tenant، `PagedList`، outbox interceptor، `Migrate()` | 03، 07، 08 | `PersonnelsModule`، `PersonnelConfiguration`، `PagedList.cs`، `MigrationExtensions` |
| `10-dapper` | `10-dapper.md` | Dapper 2.1.66 کنار EF؛ outbox/inbox، import claim، گزارش blacklist گشت، `ReplicaHealer` | 09 | `DbConnectionFactory`، `ProcessOutboxJob`، `PatrolReportService`، `GenericArrayHandler` |
| `11-messaging` | `11-messaging.md` | MassTransit 8.5.7، RabbitMQ، outbox Quartz دژبان در برابر Bus Outbox هویت، inbox، tenant headers | 07، 08، 09، 10 | `InfrastructureConfiguration`، `PersonnelCreatedDomainEventHandler`، `CreateSiteCommandHandler`، inbox jobs |
| `12-quartz` | `12-quartz.md` | Quartz 3.15.1 in-memory؛ outbox/inbox هر ماژول؛ import پرسنل؛ تفاوت interval Personnels | 11، 10 | `InfrastructureConfiguration`، `ConfigureProcess*Job`، `modules.*.json` |

## سرویس‌های اطراف

| شناسه | فایل آینده | موضوع | پیش‌نیاز | شاهد اصلی |
|---|---|---|---|---|
| `13-signalr` | `13-signalr.md` | ASP.NET Core SignalR؛ hubهای Identity/ACL/Ticket/Gate/Baskool؛ کلاینت 8.x؛ بدون backplane | 04، 05 | `MapHub`، `IHubContext`، `server-clock.js`، `use-ticket-hub.js`، Nginx/YARP |
| `14-grpc-devices` | `14-grpc-devices.md` | gRPC 2.71؛ proto Virdi/ZK/Tiam/SSM؛ ACL کلاینت؛ *GrpcServer خارج Compose؛ stream رویداد | 13، 03 | `Common/Protos`، `*GrpcClientWrapper`، `DeviceGrpcServices`، `MapGrpcService` |
| `15-hangfire` | `15-hangfire.md` | Hangfire 1.8.22؛ RT Postgres schema hangfire + sweeper؛ ACL MemoryStorage + devices_queue؛ dashboard hardened | 12، 11، 14 | `AddHangfire`/`AddHangfireServer`، `StepSubstitutionSweeper`، `DeviceSyncService`، `UseHardenedHangfireDashboard` |
| `16-dcc-s3` | `16-dcc-s3.md` | DCC؛ AWSSDK.S3 3.7.419؛ Local/S3؛ MinIO `dcc-files`؛ presign؛ `/files`→DCC | 03، 04، 09 | `IFileStorage`، `S3FileStorage`، `FileService`، `DccHttpClient`، YARP PublicFiles |
| `17-reporting` | `17-reporting.md` | **Skipped / Out of Scope** — Reporting خارج از محدودهٔ یادگیری | — | — |
| `18-mediamtx-baskool` | `18-mediamtx-baskool.md` | **Skipped / Out of Scope** — Baskool و MediaMTX اختصاصی | — | — |
| `19-redis` | `19-redis.md` | Redis؛ HybridCache 10؛ blacklist توکن؛ fallback Memory؛ health دژبان | 03، 05 | `AddCacheServices`، `TokenBlackListService`، `UseTokenRevoke`، Compose `redis` |
| `20-observability` | `20-observability.md` | Serilog+فیلتر outbox؛ OTEL tracing فقط دژبان؛ health؛ متریک in-process gateway؛ Seq/Jaeger comment | 01، 03، 19 | `UseSerilog`، `AddOpenTelemetry`، `RequestMetricsMiddleware`، GlobalAppsettings |
| `21-postgres-dr` | `21-postgres-dr.md` | هفت Postgres+volume؛ کیت DR standby/promote/PITR؛ backup daemon در tree غایب؛ بدون auto connection failover | 03، 09 | `infrastructure/postgres-dr/*`، `compose.data.yml`، `MigrationExtensions` |

## فرانت‌اند

| شناسه | فایل آینده | موضوع | پیش‌نیاز | شاهد اصلی |
|---|---|---|---|---|
| `22-turborepo` | `22-turborepo.md` | npm workspaces، Turborepo 2.10 فعال، `@repo/*`، CI/Docker `turbo run build`، تفکیک Next turbopack | — | `package.json` ریشه، `turbo.json`، `.gitlab-ci.yml`، `docker/Dockerfile.next` |
| `23-nextjs` | `23-nextjs.md` | Next.js 16 App Router؛ چهار اپ؛ `basePath`؛ standalone؛ گارد کلاینت؛ داده Axios/RQ | 22 | `apps/*/src/app`، `next.config.mjs`، `global-config.js`، login/staff paths |
| `24-vite-access-control` | `24-vite-access-control.md` | Vite 6 SPA؛ React Router 8؛ SWR؛ AuthGuard؛ base `/access-control`؛ مسیر access-group | 22، 23 | `vite.config.js`، `main.jsx`، `routes/sections`، `actions/access-group.js`، Dockerfile |
| `25-api-client-auth` | `25-api-client-auth.md` | `@repo/api-client` interceptors؛ JWT localStorage؛ refresh 401؛ `@repo/auth`؛ AuthGuard/GuestGuard؛ `X-Site-Id` | 05، 23، 24 | `axiosInstance.ts`، `tokenStorage.ts`، `AuthContext.tsx`، guards، main sign-in |
| `26-client-state` | `26-client-state.md` | RQ vs SWR؛ Zustand سایت/تب/api-key؛ invalidate staff؛ site→resetQueries؛ RHF محلی | 23، 24، 25 | `client-provider.jsx`، `staff.service.js`/`staff.keys.js`، ACL actions/stores |
| `27-mui-i18n` | `27-mui-i18n.md` | MUI 7 ThemeProvider؛ Rtl stylis؛ i18next fa-IR/en-US؛ Jalali； LanguagePopover | 23، 24، 26 | `theme-provider.jsx`، `right-to-left.jsx`، `use-locales.js`، `locales-config.js` |
| `28-nginx-edge` | `28-nginx-edge.md` | لبه فرانت؛ `/api`→YARP؛ UI basePath؛ WS hubs؛ default vs nginx-only vs ACL conf | 04، 22، 23، 24 | `default.conf.template`، `nginx-only.conf.template`، Compose فرانت |
| `29-scanner-agent` | `29-scanner-agent.md` | **Skipped / Out of Scope** — Not relevant to the learner's current goals. | — | — |

## برش عرضی

| شناسه | فایل آینده | موضوع | پیش‌نیاز | شاهد اصلی |
|---|---|---|---|---|
| `30-request-paths` | `30-request-paths.md` | دو مسیر login و GetPersonnels. صفحهٔ پرسنل در فاز C به `StaffListView` تصحیح شد | 04، 05، 08، 25، 28 | `00-login-execution-path.md` و `00-personnel-list-execution-path.md` |
| `31-testing` | `31-testing.md` | xUnit، FluentAssertions، Testcontainers، NetArchTest، Playwright، Vitest؛ تفکیک وجود/پیکربندی/اجرا | 07، 22 | ده `*Tests.csproj`؛ `BlackListScheduleTests`؛ `LayerTests`؛ Visitors Integration factory؛ Playwright `Login.spec.ts`؛ `.gitlab-ci.yml` فرانت بدون گام تست |
| `32-excel-import` | `32-excel-import.md` | ClosedXML در پرسنل، خودرو، و هویت؛ فقط بعد از خواندن call site | 08 | `PackageReference` در csprojهای نام‌برده. call site هنوز در فاز A باز نشده |

## سندهایی که عمداً ردیف مستقل نگرفتند

این‌ها یا مصرفشان ثابت نشد، یا داخل سند دیگری جا می‌شوند:

- Polly و Scrutor و MSAL: تا وقتی call site پیدا شود سند جدا ندارند. پرسش باز در سند کشف است.
- `Azure.Identity` در Reporting: همین وضعیت.
- C4 این سامانه: پیش‌نویسش در `00-project-discovery.md` است. اگر مصاحبهٔ معماری جدا لازم شد، از همان سند گسترش پیدا می‌کند و فایل تازه فقط با تصمیم فاز بعد اضافه می‌شود.
- هر ماژول دامنه (بازدیدکننده، خودرو، گشت، انبار، نقدی، مهمات، باسکول): الگوی فنی‌شان در سند 07 یکی است. سند دامنه فقط اگر رفتار کسب‌وکار آن ماژول موضوع یادگیری باشد ساخته می‌شود، نه به‌خاطر تکرار همان لایه‌ها.

## قالب اجباری هر سند فناوری

وقتی سند از `Planned` خارج می‌شود باید این‌ها را داشته باشد. وضعیت معتبر در `00-progress.md` است. فاز AC درس `29-scanner-agent` را `Skipped` کرد.

ردیف‌های `Skipped` فایل درس نمی‌گیرند مگر محدوده عوض شود.

- توضیح عمومی فناوری، بعد نقشش در همین مخزن
- شاهد با مسیر و نماد
- وابستگی و مصرف‌کننده
- جریان اجرا جایی که از کد قابل پیگیری است
- رابطه با سندهای همسایه، نه کپی متن آن‌ها
- مزیت، محدودیت، و سوءبرداشت رایج
- دقیقاً 10 سؤال مصاحبه با پاسخ فارسی، به‌همراه follow-up
- نمودار Mermaid فقط اگر با شاهد این مخزن بخواند
- بخش مرور

زبان سندها فارسی است. شناسه، نام پکیج، و نام نوع‌ها انگلیسی می‌مانند.
