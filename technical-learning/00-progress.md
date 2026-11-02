# پیگیری پیشرفت یادگیری

فاز جاری: **AD در 2026-10-26.** درس `31-testing` نوشته و `Done` شد. `29-scanner-agent` همچنان `Skipped` است. تحقیق `/api` در برابر `/Api` همچنان `Runtime verification pending` است. تست‌ها و runnerها اجرا نشدند.

معنی وضعیت‌ها:

| وضعیت | معنی |
|---|---|
| `Planned` | در کاتالوگ هست و متن یادگیری ندارد |
| `In progress` | نوشتن شروع شده و هنوز کامل نیست |
| `Evidence verified` | ادعای منبع و پیکربندی با فایل فعلی چک شده است. اجرای زنده لازم نبوده یا جداگانه مانده است |
| `Runtime verification pending` | سند نوشته شده، ولی سؤال اصلی فقط با اجرای درخواست بسته می‌شود |
| `Done` | سند تمام است و شاهدهای لازم همین سند چک شده‌اند |
| `Skipped` | خارج از محدودهٔ یادگیری به‌تصمیم کاربر؛ فایل درس ساخته نمی‌شود |
| `Blocked` | بدون شاهد جدید نباید نوشته شود |

کامل شدن یادگیری یعنی همهٔ ردیف‌های فناوری `Done` باشند. الان این‌طور نیست. فایل‌های `00-*` یا کشف‌اند یا شاهد مسیر، نه درس فناوری.

## سندهای کشف

| فایل | وضعیت | یادداشت |
|---|---|---|
| `00-project-discovery.md` | `Done` | دامنه، C4، حقایق، استنباط، پرسش باز |
| `00-source-evidence-index.md` | `Done` | مسیر و نماد؛ بدون secret |
| `00-learning-catalog.md` | `Done` | 32 سند فناوری، به‌علاوهٔ ارجاع به نمایهٔ اجرا |
| `00-progress.md` | `Done` | همین فایل |

`Done` برای این چهار فایل یعنی فاز A ثبت شده است. با عوض شدن کد باید دوباره با منبع چک شوند.

## سندهای شاهد

این‌ها جزو 32 درس فناوری نیستند.

| فایل | وضعیت | یادداشت |
|---|---|---|
| `00-login-execution-path.md` | `Evidence verified` | اتصال صفحه تا `LoginCommandHandler` در فاز D دوباره با import و `IRequestHandler` چک شد. bind نام JSON، cookie با `Secure`، و match حروف هنوز باز است |
| `00-personnel-list-execution-path.md` | `Evidence verified` | اتصال صفحهٔ staff تا `GetQueryable` چک شد. نام JSON و bind کوئری و match حروف باز است |
| `00-execution-path-index.md` | `Evidence verified` | جدول اتصال‌ها فقط جایی است که DI یا import یا کلید JSON مرحلهٔ بعد را نشان می‌دهد |
| `00-yarp-config-investigation.md` | `Evidence verified` | خالی بودن آرایه و ادغام لیست‌ها در سورس YARP 2.3 با ثبت `Program.cs` می‌خواند. dump route در زمان اجرا نیست |
| `00-api-path-case-investigation.md` | `Runtime verification pending` | لایه‌ها از روی کد و سند routing جدا شده‌اند. جفت‌درخواست‌ها اجرا نشده‌اند |

## سندهای فناوری

| شناسه | وضعیت | مانع شناخته‌شده |
|---|---|---|
| `01-dotnet-aspnetcore` | `Done` | 2026-10-26. `Program.cs` دژبان، هویت، و gateway، `EndpointExtensions`، `MigrationExtensions`، `GetPersonnels`، و `AddCustomJwtAuth` دوباره خوانده شد. Context7 در دسترس نبود. |
| `02-configuration` | `Done` | 2026-10-26. `AddJsonFile` در `Dejban.Api/Program.cs`، `AddModuleConfiguration`، کلیدهای سطح اول global و `appsettings` بدون مقدار، و کلیدهای `ConnectionStrings__` در Compose چک شد. Learn برای ترتیب provider با moniker شامل `aspnetcore-10.0` خوانده شد. مقدار secret نقل نشد. کپی `modules.*.json` داخل image هنوز `unresolved` است. |
| `03-docker-compose` | `Done` | 2026-10-26. `start-offline.sh`، سه فایل Compose ریشه، `docker/compose.data.yml`، `docker/compose.backend.yml`، هشت Dockerfile، و آدرس‌های `appsettings.DockerDevelopment.json` چک شد. رمز نقل نشد. بودن `modules.*.json` داخل image همچنان `unresolved` است. |
| `04-yarp` | `Done` | 2026-10-26. `Program.cs`، `IdentityServerRoutes` (آرایه خالی)، `appsettings.Docker.json`، rate limiter، و `ProxyErrorHandlingMiddleware` چک شد. Context7 در این جلسه نبود. |
| `05-jwt-identity` | `Done` | 2026-10-26. `AddCustomJwtAuth`، `TokenProvider`، `LoginCommandHandler`، `AuthController.Login`، `tokenStorage`، و routeهای login و پرسنل چک شد. راز JWT نقل نشد. Duende در csproj نیست. معنای policy رشته‌ای YARP و bind نام JSON همچنان باز است. |
| `06-tenancy-authorization` | `Done` | 2026-10-26. `TenantContextMiddleware`، `ApplyTenantQueryFilters`، `AddAuthorizationInternal`، `GetPersonnels` و StaffView، و مقادیر YARP `anonymous`/`default` از schema و Learn چک شد. |
| `07-modular-monolith` | `Done` | 2026-10-26. ثبت صریح هشت ماژول، schema جدا، `PersonnelCreated`/`SiteCreated`، ارجاع Inventory→Personnels Domain، و خالی بودن آرایهٔ `ModuleTests` چک شد. تست و bus اجرا نشد. |
| `08-cqrs-mediatr` | `Done` | 2026-10-26. MediatR 12.5.0، سه open behavior دژبان، Validation هویت، `GetPersonnels`/`CreatePersonnel`/`PersonnelCreatedDomainEvent`، نبود `IPublisher` در دژبان چک شد. |
| `09-ef-core-postgresql` | `Done` | 2026-10-26. EF/Npgsql 10.0.0، هشت schema، `PersonnelsDbContext`، `PagedList` sync، outbox interceptor، `Migrate()` در startup، فیلتر tenant/soft-delete چک شد. نسخهٔ زندهٔ سرور Postgres همچنان unresolved. |
| `10-dapper` | `Done` | 2026-10-26. Dapper 2.1.66 در Common.Application؛ outbox/inbox/idempotency، `PersonnelImportBatchProcessor.ClaimAsync`، `PatrolReportService`، `ReplicaHealer`، type handlerها چک شد. Reporting بدون Dapper. |
| `11-messaging` | `Done` | 2026-10-26. MassTransit 8.5.7، Quartz outbox دژبان در برابر EF Bus Outbox هویت، PersonnelCreated/SiteCreated، inbox+idempotency، retry/circuit، tenant filters چک شد. Exchange list و DLQ runtime همچنان unresolved. |
| `12-quartz` | `Done` | 2026-10-26. Quartz.Extensions.Hosting 3.15.1، in-memory، WaitForJobsToComplete، ۸×outbox/inbox + import، Personnels 2s/200 در برابر بقیه 5s/50، DisallowConcurrentExecution محلی چک شد. |
| `13-signalr` | `Done` | 2026-10-26. Hubهای Identity/ACL/Ticket/Gate/Baskool، کلاینت `@microsoft/signalr` 8.x، مسیر Time/Ticket/Gate، نبود Redis SignalR backplane، شکاف Nginx برای `gateStatusHub` چک شد. اتصال زنده اجرا نشد. |
| `14-grpc-devices` | `Done` | 2026-10-26. Grpc.AspNetCore 2.71، protoهای Virdi/ZK/Tiam/SSM، wrapper+stream، MapGrpcService، نبود در Compose/YARP، Enabled=false در Development نمونه چک شد. محل deploy زنده همچنان unresolved. |
| `15-hangfire` | `Done` | 2026-10-26. Hangfire 1.8.22؛ RT `UsePostgreSqlStorage` schema hangfire + recurring sweeper؛ ACL `UseMemoryStorage` + `devices_queue` + `AutomaticRetry(0)`؛ dashboard hardened؛ نبود در دژبان چک شد. چند replica و recovery زنده unresolved. |
| `16-dcc-s3` | `Done` | 2026-10-26. AWSSDK.S3 3.7.419؛ Provider Local/S3؛ MinIO `dcc-files`؛ FileService+presign؛ YARP `/files`→DCC public؛ UploadFile AllowAnonymous؛ CreatePutUrl بدون call site چک شد. دسترسی bucket زنده unresolved. |
| `17-reporting` | `Skipped` | 2026-10-26. خارج از محدوده به‌درخواست کاربر. فایل درس ساخته نشد. |
| `18-mediamtx-baskool` | `Skipped` | 2026-10-26. Baskool/MediaMTX خارج از محدوده. فایل درس ساخته نشد. |
| `19-redis` | `Done` | 2026-10-26. HybridCache 10 + StackExchangeRedis 10؛ blacklist؛ fallback Memory؛ UseTokenRevoke؛ نبود در pipeline دژبان؛ Compose بدون volume چک شد. اتصال زنده unresolved. |
| `20-observability` | `Done` | 2026-11-01 بازنویسی. استک Compose Alloy/Loki/Tempo/Prometheus/Grafana + فایل‌های `Observability/` و پورت development چک شد؛ کانتینرها Up؛ Tempo search خالی؛ Serilog هنوز Seq؛ OTEL فقط tracing دژبان؛ Docker هنوز `jaeger`؛ Grafana datasource provision نیست. |
| `21-postgres-dr` | `Done` | 2026-10-26. هفت Postgres+volume؛ کیت `postgres-dr` (prepare/standby/promote/PITR)؛ Redis/MinIO/Rabbit خارج از replicate؛ `backup-daemon.sh`/`backup.sh` در tree نیست؛ failover connection دستی. اجرای زنده unresolved. |
| `22-turborepo` | `Done` | 2026-10-26. npm workspaces + turbo ^2.10.12؛ `turbo.json`؛ CI `npx turbo run build --concurrency=1`؛ Docker `--filter`؛ تفکیک Next `--turbopack`. Remote cache و hit نرخ unresolved. |
| `23-nextjs` | `Done` | 2026-10-26. main/dejban/gate/dcc با `next` ^16.2.6؛ App Router؛ بدون middleware/route handler؛ AuthGuard کلاینت؛ staff/login تا apiClient. Runtime pending. |
| `24-vite-access-control` | `Done` | 2026-10-26. Vite ^6.3.5؛ React Router basename `/access-control`؛ SWR+`@repo/api-client`؛ AuthGuard؛ Docker nginx `try_files`. Device جزئیات خارج محدوده. Runtime pending. |
| `25-api-client-auth` | `Done` | 2026-10-26. apiClient+tokenStorage+401 refresh؛ AuthProvider/getMe؛ AuthGuard vs PageGuard؛ تفاوت Next/Vite env. Cookie refresh و XSS runtime/exploit ادعا نشد. |
| `26-client-state` | `Done` | 2026-10-26. RQ+ClientProvider+site reset؛ staff keys/invalidate؛ SWR ACL؛ Zustand api-key؛ swr dejban unused. Runtime cache pending. |
| `27-mui-i18n` | `Done` | 2026-10-26. ThemeProvider+Rtl stylis؛ i18next fa/en؛ MUI systemValue جدا؛ Jalali؛ بدون عربی در supportedLngs. Runtime switch pending. |
| `28-nginx-edge` | `Done` | 2026-10-26. default vs nginx-only vs ACL conf؛ proxy API/files/hubs؛ UI upstreams؛ بدون TLS لبه؛ gap gateStatusHub. Runtime pending. |
| `29-scanner-agent` | `Skipped` | 2026-10-26. Not relevant to the learner's current goals. فایل درس ساخته نشد. |
| `30-request-paths` | `Done` | 2026-10-26. یک تصحیح کوچک در فاز C: صفحهٔ پرسنل `StaffListView` است و `useGetPersonnels` مصرف‌کنندهٔ دوم همان URL است. بقیهٔ درس بازنویسی نشد. |
| `31-testing` | `Done` | 2026-10-26. ده `*Tests.csproj`؛ xUnit/FluentAssertions/NetArchTest/Testcontainers/Bogus؛ Playwright specها؛ Vitest فقط script؛ CI فرانت بدون گام تست. `dotnet test`/Playwright/Vitest/Docker اجرا نشد. |
| `32-excel-import` | `Blocked` | تا دیدن call site مربوط به ClosedXML شروع نشود |

شمارش درس فناوری: 32 مورد، 28 مورد `Done`، 0 مورد `Planned`، 3 مورد `Skipped`، 1 مورد `Blocked`، 0 مورد `In progress`. سند شاهد حروف مسیر `Runtime verification pending` است. چهار سند شاهد دیگر `Evidence verified` هستند.

خارج از محدودهٔ آینده (تا تصمیم خلاف): درس Reporting، کارکرد اختصاصی Baskool، Scanner Agent (`29`)، و درس‌هایی که هدف اصلیشان ارتباط/مدیریت دستگاه فیزیکی است. درس‌های `Done` قبلی (مثل 13–15) دست نخورده می‌مانند.

## فاز B

در 2026-10-26 این سه فایل نوشته شد:

- `01-dotnet-aspnetcore.md`
- `04-yarp.md`
- `30-request-paths.md`

هر کدام بعد از بازخوانی منبع `done` شد. اپ، تست، Compose، و کد برنامه عوض نشد. Context7 در این جلسه در دسترس نبود.

## فاز C

در 2026-10-26 سندهای شاهد مسیر نوشته شد. درس‌های 01 و 04 بازنویسی نشدند. در درس 30 فقط معرفی صفحهٔ پرسنل و یک پاسخ مصاحبه اصلاح شد، چون صفحهٔ «پرسنل» `useGetStaffWithPagination` است.

اپ و تست اجرا نشدند. تحقیق حروف مسیر `open` مانده است. تست بعدی در خود `00-api-path-case-investigation.md` است.

## فاز D

در 2026-10-26 سندها با کد فعلی مقابله شدند. اپ و تست اجرا نشدند. کد برنامه عوض نشد.

تصحیح‌ها: قید واقعی `ValidationBehavior`، اتصال `IRequestHandler` و `IQueryHandler`، نبود کلید `ReverseProxy` در `GlobalAppsettings`، و جملهٔ درس 04 که ممکن بود خوانده شود «حافظه جدول route را خالی می‌کند». برنامهٔ تست حروف مسیر به سه لایهٔ فرانت، gateway، و بک‌اند شکسته شد.

## فاز F

در 2026-10-26 درس `01-dotnet-aspnetcore.md` دوباره از نظر بخش‌ها و ده سؤال مصاحبه کامل دیده شد و بازنویسی نشد. بعد `02-configuration.md` نوشته شد. اپ، تست، و درخواست HTTP اجرا نشدند. کد و پیکربندی عوض نشد.

در همان روز `03-docker-compose.md` نوشته شد. image ساخته نشد، کانتینر بالا نیامد، و volume عوض نشد.

## فاز G

در 2026-10-26 درس `05-jwt-identity.md` نوشته شد. اپ و درخواست HTTP اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز H

در 2026-10-26 درس `06-tenancy-authorization.md` نوشته شد. اپ و درخواست HTTP اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز I

در 2026-10-26 درس `07-modular-monolith.md` نوشته شد. اپ، تست ArchitectureTests، و bus اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز J

در 2026-10-26 درس `08-cqrs-mediatr.md` نوشته شد. اپ و تست اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز K

در 2026-10-26 درس `09-ef-core-postgresql.md` نوشته شد. اپ، تست، migration، و اتصال DB اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز L

در 2026-10-26 درس `10-dapper.md` نوشته شد. اپ، تست، و اتصال DB اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز M

در 2026-10-26 درس `11-messaging.md` نوشته شد. اپ، broker، و DB اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز N

در 2026-10-26 درس `12-quartz.md` نوشته شد. اپ و scheduler اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز O

در 2026-10-26 درس `13-signalr.md` نوشته شد. اپ و WebSocket اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز P

در 2026-10-26 درس `14-grpc-devices.md` نوشته شد. سرور gRPC، دستگاه، و RPC زنده اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز Q

در 2026-10-26 درس `15-hangfire.md` نوشته شد. worker Hangfire، Postgres schema hangfire، و dashboard زنده اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز R

در 2026-10-26 درس `16-dcc-s3.md` نوشته شد. MinIO، آپلود/دانلود، و DB زنده اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز S

در 2026-10-26 وضعیت `Skipped` اضافه شد؛ `17-reporting` و `18-mediamtx-baskool` خارج از محدوده علامت خوردند. درس `19-redis.md` نوشته شد. Redis زنده اجرا نشد. کد و پیکربندی عوض نشد.

## فاز T

در 2026-10-26 درس `20-observability.md` نوشته شد. Seq، Jaeger، و OTLP زنده اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز U

در 2026-10-26 درس `21-postgres-dr.md` نوشته شد. کانتینر standby/backup و PITR زنده اجرا نشدند. کد و پیکربندی عوض نشد. درس 22 در همان فاز شروع نشد.

## فاز V

در 2026-10-26 درس `22-turborepo.md` نوشته شد. `npm install`، `turbo run`، Docker build، و CI زنده اجرا نشدند. کد و پیکربندی فرانت/بک‌اند عوض نشد. درس 23 در همان فاز شروع نشد.

## فاز W

در 2026-10-26 درس `23-nextjs.md` نوشته شد. `next dev`/`build` و درخواست مرورگر اجرا نشدند. کد و پیکربندی عوض نشد. درس 24 در همان فاز شروع نشد.

## فاز X

در 2026-10-26 درس `24-vite-access-control.md` نوشته شد. `vite`/`build` و درخواست API زنده اجرا نشدند. کد و پیکربندی عوض نشد. درس 25 در همان فاز شروع نشد.

## فاز Y

در 2026-10-26 درس `25-api-client-auth.md` نوشته شد. Login/refresh زنده و درخواست HTTP اجرا نشدند. کد و پیکربندی عوض نشد. درس 26 در همان فاز شروع نشد.

## فاز Z

در 2026-10-26 درس `26-client-state.md` نوشته شد. اپ و رفتار cache زنده اجرا نشدند. کد و پیکربندی عوض نشد. درس 27 در همان فاز شروع نشد.

## فاز AA

در 2026-10-26 درس `27-mui-i18n.md` نوشته شد. سوئیچ زبان/تم زنده اجرا نشد. کد و پیکربندی عوض نشد. درس 28 در همان فاز شروع نشد.

## فاز AB

در 2026-10-26 درس `28-nginx-edge.md` نوشته شد. کانتینر Nginx و درخواست HTTP اجرا نشدند. کد و پیکربندی عوض نشد.

## فاز AC

در 2026-10-26 به‌درخواست یادگیرنده، `29-scanner-agent` برابر `Skipped` شد: Not relevant to the learner's current goals. فایل درس ساخته نشد. کد برنامه و پیاده‌سازی اسکنر باز نشد و اجرا نشد.

## فاز AD

در 2026-10-26 درس `31-testing.md` نوشته شد. اپ، `dotnet test`، Playwright، Vitest، Docker، و Testcontainers اجرا نشدند. کد برنامه، تست، و CI عوض نشد. `29` و 17–18 همچنان Skip؛ `32` همچنان Blocked.

## فاز بعد

سند فناوری بعدی در کاتالوگ `32-excel-import` است ولی وضعیتش `Blocked` است (call site ClosedXML هنوز باز نشده). هیچ ردیف `Planned` باقی نمانده. تحقیق حروف مسیر همچنان `Runtime verification pending` می‌ماند.

قبل از نوشتن هر سند، شاهد همان ردیف دوباره از روی فایل باز شود.

## کارهایی که در فاز A انجام نشد

- هیچ فایل منبع، Compose، یا دیتابیس عوض نشد.
- تست و اپ اجرا نشد.
- درس، سؤال مصاحبه، و نمودار آموزشی هر فناوری ساخته نشد.
