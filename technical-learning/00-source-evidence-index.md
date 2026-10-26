# نمایهٔ شاهد منبع — فاز A

مسیر بک‌اند نسبت به ریشهٔ `dejban_backend_new` است. مسیر فرانت‌اند نسبت به ریشهٔ `dejban_frontend_new` است. خط‌ها وضعیت فایل در تاریخ 2026-10-25 را نشان می‌دهند و با ویرایش بعدی ممکن است جابه‌جا شوند. نماد مهم‌تر از شمارهٔ خط است.

رمز، connection string کامل، و کلید در این نمایه نیست.

## ورودی و میزبان

| ادعا | مسیر | نماد |
|---|---|---|
| Solution بک‌اند | `PG_Microservices.slnx` | فایل solution |
| شرح کوتاه محصول | `README.md` | PayamGostar Microservices |
| Gateway، YARP، Scalar، rate limit، JWT | `ApiGateway/Program.cs` | `AddReverseProxy`، `LoadFromConfig`، `MapReverseProxy`، `MapScalarApiReference` |
| میزبان هویت، hub زمان و فعالیت | `Microservices/IdentityServer/Program.cs` | `AddInfrastructure`، `MapHub<TimeHub>`، `MapHub<UserActivityHub>`، `MapControllers` |
| میزبان دژبان و هشت ماژول | `Microservices/Dejban/API/Dejban.Api/Program.cs` | `AddApplication`، `AddInfrastructure`، `AddPersonnelsModule` و بقیه، `MapEndpoints` |
| میزبان ACL و hub دستگاه | `Microservices/ACLServer/Program.cs` | `MapHub<DeviceHub>`، `UseHardenedHangfireDashboard` |
| میزبان گزارش | `Microservices/Reporting/Program.cs` | `GetConnectionString("Postgres")`، `"DejbanPostgres"`، `"IdentityPostgres"` |
| میزبان تیکت | `Microservices/RequestTracker/Program.cs` | `MapHub<TicketHub>` |
| میزبان گیت | `Microservices/GateServer/Program.cs` | `MapHub<GateConnectionStatusHub>` |
| باسکول، سرویس ویندوز/systemd | `Microservices/BaskoolService/Program.cs` | `MapHub<BaskoolHub>`، `UseWindowsService` |
| gRPC ZK | `Microservices/ZKGrpcServer/Program.cs` | `MapGrpcService<ZKGrpcService>` |
| gRPC Virdi | `Microservices/VirdiGrpcServer/Program.cs` | `MapGrpcService<VirdiGrpcService>` |
| gRPC Tiam | `Microservices/TiamGrpcServer/Program.cs` | `MapGrpcService<TiamGrpcService>` |
| gRPC مدیریت سرویس | `Microservices/ServerServiceManagement/Program.cs` | `MapGrpcService<ServerServiceManagementGrpc>` |
| MVC محلی مدیریت کلاینت | `Microservices/ClientServiceManagement/Program.cs` | `AddControllersWithViews`، `ServiceManager` |
| TFM `net10.0` | نمونه `Microservices/IdentityServer/IdentityServer.csproj` و `Dejban.Api.csproj` | `TargetFramework` |
| نسخهٔ متمرکز پکیج | `Directory.Packages.props` | `PackageVersion` |

## پکیج‌های استفاده‌شده

نسخه از `Directory.Packages.props` است مگر اینکه خلافش نوشته شود.

| فناوری | نسخهٔ اعلام‌شده | شاهد استفاده |
|---|---|---|
| YARP | `Yarp.ReverseProxy` `2.3.0` | `ApiGateway/Program.cs` |
| EF Core | `Microsoft.EntityFrameworkCore` `10.0.0` | `UseNpgsql` در ماژول‌ها و سرویس‌ها |
| Npgsql EF | `Npgsql.EntityFrameworkCore.PostgreSQL` `10.0.0` | همان `UseNpgsql` |
| ASP.NET Identity | `Microsoft.AspNetCore.Identity.EntityFrameworkCore` `10.0.0` | `IdentityServer/.../ApplicationDbContext.cs` کلاس `ApplicationDbContext : IdentityDbContext` |
| JWT Bearer | `Microsoft.AspNetCore.Authentication.JwtBearer` `10.0.0` | `AddCustomJwtAuth` از `Dejban.Common.Infrastructure/Authentication/AuthenticationExtensions.cs` و `BaskoolService/Program.cs` |
| MediatR | `12.5.0` | `Dejban.Common.Application/ApplicationConfiguration.cs` متد `AddApplication` |
| FluentValidation | `12.1.0` | `AddValidatorsFromAssemblies` در همان فایل |
| Mapster | `7.4.0` | `TypeAdapterConfig.GlobalSettings.Scan` |
| ErrorOr | `2.0.1` | `GetPersonnelsQueryHandler` و `result.Match` در endpoint |
| MassTransit | `8.5.7` به‌همراه RabbitMQ و EF integration | `InfrastructureConfiguration.AddInfrastructure` و `IdentityServer/.../ServiceCollectionExtensions.AddMassTransit` |
| Quartz | `Quartz.Extensions.Hosting` `3.15.1` | `AddQuartz` در `InfrastructureConfiguration`؛ `ProcessOutboxJob : IJob` |
| Hangfire | Core و AspNetCore `1.8.22`؛ PostgreSQL `1.20.12`؛ MemoryStorage `1.8.1.2` | RequestTracker: `UsePostgreSqlStorage`؛ ACL: `UseMemoryStorage` |
| Dapper | `2.1.66` | `using Dapper` در outbox/inbox و `PatrolReportService` |
| Stimulsoft | Reports Engine و Web `2024.3.2` | `using Stimulsoft.Report` در `Reporting/Infrastructure/ReportRepository.cs` |
| AWSSDK.S3 | `3.7.419` | `new AmazonS3Client` در `DCC/Infrastructure/Services/S3FileStorage.cs` |
| gRPC | `Grpc.AspNetCore` `2.71.0`؛ Tools `2.76.0` | `AddGrpc` و `MapGrpcService`؛ proto در `Common/Protos` |
| OpenTelemetry | Exporter OTLP `1.15.3` | `AddOpenTelemetry` در `InfrastructureConfiguration` |
| Serilog | `Serilog.AspNetCore` `10.0.0` | `UseSerilog` در `Program.cs` چند سرویس |
| Scalar | `Scalar.AspNetCore` `2.11.0` | `MapScalarApiReference` در gateway |
| Redis cache | `Microsoft.Extensions.Caching.StackExchangeRedis` `10.0.0` | `AddCacheServices(redisConnectionString)` |
| HealthChecks | NpgSql و Redis `9.0.0` | `AddNpgSql` و `AddRedis` در `Dejban.Api/Program.cs` |
| API versioning | `Asp.Versioning.Mvc.ApiExplorer` `8.1.0` | `[ApiVersion("1.0")]` و `NewApiVersionSet` |
| ClosedXML | `0.105.1` | `PackageReference` در `Dejban.Modules.Personnels.Application.csproj` و IdentityServer و Vehicles.Application. فراخوانی API اکسل در این فاز خط‌به‌خط خوانده نشد |
| xunit | `2.9.3` (+ runner `3.1.5`) | ده `*Tests.csproj`؛ `[Fact]`/`[Theory]` در Unit/Integration/Architecture |
| NetArchTest | `1.3.2` | `Visitors.../LayerTests.cs`، `Dejban.ArchitectureTests/.../ModuleTests.cs` |
| Testcontainers | PostgreSQL و Redis `4.9.0` | `IntegrationTestWebAppFactory` (Visitors + Dejban.IntegrationTests)؛ `InventoryPostgresFixture`؛ SecurityPatrols fixture |
| FluentAssertions | `8.8.0` | assertها + `TestResultExtensions.ShouldBeSuccessful` |
| Bogus | `35.6.5` | `Faker` در BaseIntegrationTest / UnitTests Visitors |
| Mvc.Testing | `10.0.0` | `WebApplicationFactory<Program>` در Integration Visitors |
| Playwright | `^1.61.0` | `apps/main` و `apps/dejban` config + `*.spec.ts` |
| Vitest | `^4.1.0` | dependency ریشه + `apps/main` script `test:unit`؛ suite واحد معنادار در فاز AD یافت نشد |

## پکیج یا سرویس بدون اثبات مصرف در این فاز

| مورد | کجا اعلام شده | چه چیزی ثابت نشد |
|---|---|---|
| Polly `8.6.5` | `Directory.Packages.props` | فراخوانی `ResiliencePipeline` یا `Policy` در فایل‌های خوانده‌شده نبود. MassTransit retry خودش را جداگانه در `UseMessageRetry` دارد |
| Scrutor `7.0.0` | همان فایل | `Scan` از Scrutor دیده نشد |
| `Microsoft.Identity.Client` `4.85.2` | همان فایل | فراخوانی MSAL دیده نشد |
| `Azure.Identity` `1.21.0` | `Microservices/Reporting/Reporting.csproj` | استفاده در Reporting پیدا نشد |
| Seq و Jaeger | سرویس comment در `docker-compose.development.yml` و `docker-compose.docker-development.yml` | سرویس فعال نیستند |
| `ConnectionStrings__AclPostgres` | `docker/compose.backend.yml` سرویس `reporting` | هیچ `AclPostgres` در `Microservices/Reporting` پیدا نشد |
| SWR `^2.3.6` | `apps/dejban/package.json` | یک مسیر خوانده‌شده از React Query استفاده می‌کند، نه SWR |
| `Hangfire.PostgreSql` برای ACL | پکیج مرکزی؛ بلوک comment در `ACLServer/.../ServiceCollectionExtensions.cs` | کد فعال ACL، `UseMemoryStorage` است |

## داده و زیرساخت

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| هفت PostgreSQL، RabbitMQ، Redis، MinIO، MediaMTX | `docker-compose.yml` و `docker/compose.data.yml` | `identitydb` تا `gateserverdb`، `eventbus`، `redis`، `minio`، `mediamtx` |
| پورت‌های `18001` تا `18007` | `docker/compose.data.yml` | نگاشت `18001:5432` تا `18007:5432` |
| هشت سرویس اپ | `docker/compose.backend.yml` | `identityserver`، `dcc`، `reporting`، `requesttracker`، `aclserver`، `dejban`، `gateserver`، `apigateway` |
| gateway منتشرشده | همان فایل | `7036:443` |
| bucket `dcc-files` | `docker-compose.yml` سرویس `minio-init` | دستور `mc mb` |
| CORS MinIO | `Microservices/DCC/Scripts/minio-cors.json` | mount در `minio-init` |
| RabbitMQ definitions | `Common/EventBus/eventbus_init/definitions.json` | volume در سرویس `eventbus` |
| MediaMTX config | `Common/MediaMTX/mediamtx.yml` | volume سرویس `mediamtx` |
| DR و standby | `infrastructure/postgres-dr/README.md` | `docker-compose.standby.yml`، `docker-compose.backup.yml` |
| schema پرسنل | `Microservices/Dejban/Modules/Personnels/Dejban.Modules.Personnels.Infrastructure/Database/Schemas.cs` | `Personnels = "personnels"` |
| history table داخل schema | `.../PersonnelsModule.cs` | `MigrationsHistoryTable(..., Schemas.Personnels)` |
| DbContext پرسنل | `.../Database/PersonnelsDbContext.cs` | `PersonnelsDbContext` |
| اتصال گزارش به دژبان و هویت | `Microservices/Reporting/Infrastructure/ReportRepository.cs` | `GetConnectionString` |

نام دیتابیس‌ها در environment سرویس Compose: `payamgostar_identity`، `payamgostar_requesttracker`، `payamgostar_aclserver`، `payamgostar_dcc`، `payamgostar_reporting`، `payamgostar_dejban`، `payamgostar_gateserver`.

## مسیر HTTP

| ادعا | مسیر | نماد |
|---|---|---|
| ورود | `Microservices/IdentityServer/Controllers/AuthController.cs` | `Login`، route کلاس `/api/v{version:apiVersion}/[controller]` |
| لیست پرسنل | `Microservices/Dejban/Modules/Personnels/Dejban.Modules.Personnels.Presentation/Personnels/GetPersonnels.cs` | `GetPersonnels.MapEndpoint` |
| handler پرسنل | `.../Application/Personnels/GetPersonnels/GetPersonnelsQueryHandler.cs` | `GetPersonnelsQueryHandler.Handle` |
| کشف endpoint | `Microservices/Dejban/Common/Dejban.Common.Presentation/Endpoints/EndpointExtensions.cs` | `IEndpoint` |
| route پروکسی پرسنل | `ApiGateway/appsettings-sample.json` | `personnel-routes-v1`، cluster `dejban-cluster` |
| route پروکسی login | همان فایل | مسیر `/Api/v{apiVersion}/Auth/Login/{**catch-all}`، cluster `identity-server-cluster` |
| مقصد نمونهٔ دژبان | همان فایل، بخش Clusters دژبان | `http://localhost:5042` |
| outbox هویت روی Postgres | `Microservices/IdentityServer/Abstractions/Extensions/ServiceCollectionExtensions.cs` | `AddEntityFrameworkOutbox<ApplicationDbContext>` |
| outbox دژبان با Quartz | `Microservices/Dejban/Modules/Personnels/Dejban.Modules.Personnels.Infrastructure/Outbox/ProcessOutboxJob.cs` | `ProcessOutboxJob` |
| ثبت consumer هویت | همان `ServiceCollectionExtensions` | `PersonnelCreatedConsumer`، `PersonnelUpdatedConsumer`، `PersonnelDeletedConsumer` |
| هدر سایت | `Common/Abstractions/Extensions/HttpContextAccessorExtensions.cs` | `SiteIdHeaderName = "X-Site-Id"` |
| اعمال سایت مؤثر | `Common/Tenancy/TenantContextMiddleware.cs` | `InvokeAsync` |
| JWT داخلی دژبان | `Microservices/Dejban/Common/Dejban.Common.Infrastructure/Authentication/AuthenticationExtensions.cs` | `AddAuthenticationInternal` |

## فرانت‌اند

| ادعا | مسیر | نماد |
|---|---|---|
| workspace و turbo | `package.json` | `workspaces` `apps/*`/`packages/*`؛ `turbo` ^2.10.12؛ scripts → `turbo run` |
| pipeline توربو | `turbo.json` | tasks `build`/`dev`/`start`/`lint`/`check-types`/`test:*`؛ outputs `.next/**`/`dist/**` |
| build فیلترشده Docker | `docker/Dockerfile.next` | `npx turbo run build --filter=${APP_NAME}` |
| Axios و هدرها | `packages/api-client/src/axiosInstance.ts` | `createApiClient`، `apiClient`، `endpoints.auth.login` |
| ورود | `packages/ui/src/auth/context/jwt/action.js` | `signInWithPassword` |
| رجیستری پیکربندی | `packages/config/src/registry.js` | `ConfigRegistry.set` |
| پکیج auth | `packages/auth/src/index.ts` | `AuthProvider`، `useAuth` |
| endpoint پرسنل | `apps/dejban/src/lib/api.js` | `personnels.list = '/Personnels/GetPersonnels'`، `export default apiClient` |
| HTTP پرسنل | `apps/dejban/src/services/personnels/personnels.http.js` | `getPersonnelsList` |
| React Query پرسنل | `apps/dejban/src/services/personnels/personnels.service.js` | `useQuery` / `queryFn` |
| App Router dejban | `apps/dejban/src/app/layout.jsx` و `apps/dejban/src/app/dashboard/layout.jsx` | فایل layout |
| basePath | `apps/dejban/next.config.mjs` | `basePath: '/dejban'`، `output: 'standalone'` |
| Vite access-control | `apps/access-control/vite.config.js` و `src/main.jsx` | `defineConfig`، `createBrowserRouter` |
| Nginx | `docker/nginx/default.conf.template` | `location /api/`، upstreamهای اپ |
| Compose فرانت | `docker-compose.yml` | سرویس‌های `nginx`، `main`، `dejban`، `gate`، `dcc`، `access-control` |
| CI | `.gitlab-ci.yml` | `deploy_to_server`، `npx turbo run build` |
| اسکنر محلی | `tools/scanner-agent/README.md` و `Program.cs` | پورت `19787`، WIA |
| نسخهٔ Next در package اپ | `apps/dejban/package.json` | `"next": "^16.2.6"` |
| MUI، React، Query، Zod، Zustand | همان فایل | dependencyهای `dependencies` |

## مستند خارجی که برای نسخه چک شد

| موضوع | شناسه Context7 | نتیجهٔ قابل‌اتکا برای این فاز |
|---|---|---|
| App Router در Next.js 16.2.9 | `/vercel/next.js/v16.2.9` | `app` با فایل‌های `page` و `layout` route می‌سازد. مخزن از `layout.jsx` استفاده می‌کند |
| YARP 2.3.0 | `/dotnet/yarp/v2.3.0` | `LoadFromConfig` به‌همراه `MapReverseProxy` مسیر را به cluster و آدرس مقصد وصل می‌کند. کد این مخزن چند section جدا و یک `LoadFromMemory` هم دارد |
| Npgsql `UseNpgsql` | `/npgsql/efcore.pg` روی شاخهٔ main | امضای `UseNpgsql(connectionString)` وجود دارد. این سند tag `10.0.0` نبود |

## بازبینی فاز B در 2026-10-26

نمادهای سندهای `01`، `04`، و `30` دوباره از روی فایل باز شدند، نه از روی شمارهٔ خط این نمایه. موردهایی که نسبت به فاز A دقیق‌تر شدند:

- `IdentityServerRoutes.routes` خالی است. routeهای login داخل comment هستند.
- مقصد داکر در `ApiGateway/appsettings.Docker.json` و `appsettings.DockerDevelopment.json` نام سرویس است، مثل `http://dejban`. نمونه و `appsettings.json` برای همان cluster مقدار `http://localhost:5042` دارند.
- `PublicFiles:Provider` در فایل داکر gateway برابر `MinIO` است، ولی route `minio-public-files-v1` به `http://dcc/` و مسیر `/api/v1/Files/public/{**catch-all}` می‌رود.
- health درگاه بخش `Reporting:Routes` را می‌خواند. routeها زیر `ReverseProxy:Reporting` هستند.
- `ValidationPipelineBehavior` دژبان قید `IBaseCommand` دارد و `GetPersonnelsQuery` این قید را ندارد.

## بازبینی فاز C در 2026-10-26

شمارهٔ خط‌های این نمایه دوباره معیار نیستند. نمادهای زیر از روی فایل فعلی چک شدند.

| موضوع | مسیر | نماد |
|---|---|---|
| صفحهٔ ورود | `dejban_frontend_new/apps/main/src/app/auth/jwt/sign-in/page.jsx` | `JwtSignInView` |
| post ورود | `apps/main/src/auth/context/jwt/action.js` | `signInWithPassword` |
| مسیر login در کلاینت | `packages/api-client/src/axiosInstance.ts` | `endpoints.auth.login = '/auth/login'` |
| صفحهٔ پرسنل | `apps/dejban/src/app/dashboard/personnel/staff/page.jsx` | `StaffListView` |
| state صفحه | `apps/dejban/src/sections/staff/view/staff-list-view.jsx` | `pageSize: 10`، `data.items`، `data.totalCount` |
| HTTP پرسنل صفحه | `apps/dejban/src/services/staff/staff.http.js` | `getStaffWithPagination` |
| ثابت لیست | `apps/dejban/src/lib/api.js` | `staff.list = '/Personnels/GetPersonnels'` |
| route ورود داکر | `ApiGateway/appsettings.DockerDevelopment.json` | `auth-login-route-v1` |
| route پرسنل داکر | همان فایل | `personnel-routes-v1`، `http://dejban` |
| آرایهٔ خالی | `ApiGateway/Abstractions/DynamicRoutes/IdentityServerRoutes.cs` | `routes` |
| ادغام provider | سورس tag `Yarp.ReverseProxy` 2.3.0، `ProxyConfigManager.InitialLoadAsync` | `routes.AddRange` |
| match مسیر | همان tag، `ProxyEndpointFactory.CreateEndpoint` | `RoutePatternFactory.Parse` |
| قانون حروف template | Microsoft Learn، Routing، moniker شامل `aspnetcore-10.0` | متن match برابر case-insensitive |
| دو location لبه | `dejban_frontend_new/docker/nginx/default.conf.template` | `location /api/` و `location /Api/` |
| نام‌های صفحهٔ سرور | `Common/Abstractions/Queries/PagedList.cs` | `Items` و `TotalCount` |
| کوئری پرسنل | `.../PersonnelRepository.cs` | `GetQueryable` برمی‌گرداند `context.Personnels` |

سندهای این بازبینی: `00-login-execution-path.md`، `00-personnel-list-execution-path.md`، `00-execution-path-index.md`، `00-yarp-config-investigation.md`، `00-api-path-case-investigation.md`.

اجرای زندهٔ `/api` در برابر `/Api` انجام نشد. bind شدن `username` به `UserName` و camelCase شدن `PagedList` هم باز است.

## بازبینی فاز D در 2026-10-26

- `Yarp.ReverseProxy` در `Directory.Packages.props` برابر `2.3.0` است. `ApiGateway.csproj` همان پکیج را بدون نسخهٔ جدا ارجاع می‌دهد.
- `LoginCommandHandler : IRequestHandler<LoginCommand, ErrorOr<object>>` و `LoginCommand : IRequest<ErrorOr<object>>`. ثبت با `RegisterServicesFromAssemblyContaining<ApplicationAssemblyReference>` در همان `IdentityServer.csproj` است.
- `ValidationBehavior` قید `TResponse : IErrorOr` دارد.
- `GetPersonnelsQueryHandler : IQueryHandler<GetPersonnelsQuery, PagedList<object>>`. اسمبلی Application پرسنل داخل `moduleApplicationAssemblies` به `AddApplication` می‌رود.
- شش فایل `GlobalAppsettings/globalAppsettings*.json` کلید `ReverseProxy` ندارند.
- پروفایل Project هویت `http://localhost:5038` و دژبان `http://localhost:5042` است. در `appsettings.Development.json` مقصد همان clusterها همین پورت‌هاست. پروفایل gateway برابر `https://+:7036` است.

## بازبینی فاز F در 2026-10-26

درس `02-configuration.md`. مقدارها نقل نشدند.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| دو JSON اجباری global | `Microservices/Dejban/API/Dejban.Api/Program.cs` | `AddJsonFile`، `optional: false` |
| عمق مسیر در Development | همان فایل، و `IdentityServer/Program.cs`، و `ApiGateway/Program.cs` | چهار، دو، و یک بار `..` |
| فایل ماژول | `Dejban.Api/Extensions/ConfigurationExtensions.cs` | `modules.{module}.json` اجباری، `modules.{module}.Development.json` اختیاری |
| Inbox پرسنل | `modules.personnels.json` و `modules.personnels.Development.json` | `Personnels:Inbox:BatchSize` برابر 50 و 20 |
| options پرسنل | `PersonnelsModule.cs` | `GetSection("Personnels:Import")` و Outbox و Inbox |
| نبود ConnectionStrings در global | کلیدهای سطح اول `GlobalAppsettings/globalAppsettings.json` و فایل DockerDevelopment | `JwtSettings` هست، `ConnectionStrings` نیست |
| محیط Compose | `docker/compose.backend.yml` | `ASPNETCORE_ENVIRONMENT: DockerDevelopment`، `ConnectionStrings__Postgres` |

درس `03-docker-compose.md`. مقدار رمز و connection string کامل نقل نشد.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| بالا آوردن ادغامی | `infrastructure/offline-mode/start-offline.sh` و `docker/import-and-run.sh` | سه فایل `docker-compose.yml`، `docker-compose.development.yml`، `docker-compose.docker-development.yml`، با `--no-build --pull never` |
| شبکه و volume داده | `docker-compose.yml` | شبکه `backend`، subnet `10.10.0.0/24`، `POSTGRES_DB`، volume روی `/var/lib/postgresql`، Redis بدون volume |
| پورت host | `docker-compose.development.yml` | `18001:5432` تا `18007:5432`، Redis `6379`، gateway در فایل سوم `7036:443` |
| اپ جدا از داده | `docker/compose.data.yml` و `docker/compose.backend.yml` | پروژه‌های `dejban-data` و `dejban-backend`. اتصال با `${DATA_HOST}` و پورت host |
| نبود اسکریپت split | جستجوی `*.sh` برای `compose.data.yml` | هیچ موردی. `offline.sh` در درخت نبود. README کیت DR به آن ارجاع می‌دهد |
| image پستیگرس | فایل پایه، `compose.data.yml`، `infrastructure/postgres-dr/docker-compose.standby.yml` | `postgres`، `postgres:latest`، `${POSTGRES_IMAGE:-postgres:18.1}` |
| Host داخل JSON داکر | `Dejban.Api/appsettings.DockerDevelopment.json` و `IdentityServer/appsettings.DockerDevelopment.json` | `Host=dejbandb` و `Host=identitydb`، بدون قطعهٔ `Port=` |
| مقصد YARP | `ApiGateway/appsettings.DockerDevelopment.json` | `http://dejban` و بقیهٔ نام سرویس‌ها، باسکول `http://host.docker.internal:5053` |
| فرانت جدا | `dejban_frontend_new/docker-compose.yml` | شبکه `dejban-frontend`، `API_GATEWAY` پیش‌فرض `host.docker.internal:7036` |
| 502 به 503 | `ApiGateway/Middleware/ProxyErrorHandlingMiddleware.cs` | وضعیت 502 یا 500 |
| ماژول داخل image | `Dejban.Api.csproj` و `Dejban.Api/Dockerfile` | بدون `CopyToPublishDirectory` و بدون COPY جدا. حضور در image `unresolved` |

درس `05-jwt-identity.md`. مقدار `AccessTokenSecret` و `RefreshTokenSecret` نقل نشد.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| تنظیم JWT | `Common/Abstractions/BindingContracts/JwtSettings.cs` | `SectionName = "JwtSettings"` |
| کپی bearer | `Common/Abstractions/Extensions/ServiceCollectionExtensions.cs` | `AddCustomJwtAuth`، `Get<JwtSettings>()`، `ClockSkew = TimeSpan.Zero` |
| صدور توکن | `IdentityServer/Infrastructure/Providers/TokenProvider.cs` | `CreateAccessToken`، `CreateRefreshToken`، `HmacSha256` |
| login | `AuthController.Login` و `LoginCommandHandler` | `[AllowAnonymous]`، `CheckPasswordSignInAsync`، دو کوکی |
| ذخیرهٔ فرانت | `packages/api-client/src/tokenStorage.ts` و `axiosInstance.ts` | `localStorage` کلید `jwt_access_token`، refresh بدون هدر Bearer |
| هویت دیتابیس | `ApplicationDbContext` | `IdentityDbContext<...>`، بدون Duende |
| ابطال | `LogoutCommandHandler` و `TokenRevokeMiddleware` | gateway و هویت `UseTokenRevoke` دارند. `Dejban.Api/Program.cs` ندارد |
| route | `ApiGateway/appsettings.DockerDevelopment.json` | `auth-login-route-v1` با `anonymous`، `personnel-routes-v1` با `default` |
| عمر و issuer | پنج فایل غیرنمونهٔ `GlobalAppsettings/globalAppsettings*.json` | `ExpirationInMinutes` برابر 15، `SessionExpirationInDays` برابر 7، issuer و audience برابر `https://localhost:7036` |

درس `06-tenancy-authorization.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| شناسایی سایت | `TenantContextMiddleware.cs` و `HttpContextAccessorExtensions.cs` | claim `site`، هدر `X-Site-Id`، نقش `SuperAdmin` |
| accessor | `TenantContextAccessor.cs` | `AsyncLocal`، `SetContext`، `Clear` |
| فیلتر EF | `TenantQueryFilterExtensions.cs` و `PersonnelsDbContext.cs` | `ApplyTenantQueryFilters`، `ISiteEntity.SiteId` |
| claims غنی | `CustomClaimsTransformation.cs` | `IClaimService`، identity به نام `SiteClaims` |
| ثبت authorization | `AuthorizationServiceCollectionExtensions.cs` | handlerها و `AuthorizationPolicyProvider` |
| پرسنل | `GetPersonnels.cs` و `GetPersonnelsQueryHandler.cs` و `UserContext.cs` | `RequireAuthorization`، `permission:staffView` داخل handler |
| YARP special values | پکیج `Yarp.ReverseProxy` 2.3.0 و Learn authn-authz | `anonymous` و `default`، case-insensitive |
| gateway بدون tenancy DI | `ApiGateway/Program.cs` | `AddCustomJwtAuth` هست؛ `AddAuthorizationInternal` و `UseTenantContext` نیست |
| ترتیب pipeline | `Dejban.Api/Program.cs` و `IdentityServer/Program.cs` | دژبان AuthZ قبل از Tenant؛ هویت Tenant قبل از AuthZ |

درس `07-modular-monolith.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| ثبت صریح ماژول‌ها | `Microservices/Dejban/API/Dejban.Api/Program.cs` | `moduleApplicationAssemblies`، هشت `Add*Module` |
| MediatR مشترک | `Dejban.Common.Application/ApplicationConfiguration.cs` | `RegisterServicesFromAssemblies` |
| ماژول پرسنل | `PersonnelsModule.cs` | `AddPersonnelsModule`، schema از `UseNpgsql`، `AddEndpoints` |
| endpoint discovery | `EndpointExtensions.cs` | `IEndpoint` Transient، `MapEndpoints` |
| domain → outbox | `InsertOutboxMessagesInterceptor.cs` | `OutboxMessage` از `IDomainEvent` |
| domain → integration | `PersonnelCreatedDomainEventHandler.cs` | `IEventBus.PublishAsync(PersonnelCreated)` |
| مصرف داخل دژبان | `Visitors/.../PersonnelCreatedIntegrationEventHandler.cs` | `IReplicaHealer` |
| مصرف بیرون دژبان | `IdentityServer/.../PersonnelCreatedConsumer.cs` و مشابه ACL/RequestTracker | `IConsumer<PersonnelCreated>` |
| سایت از هویت | `CreateSiteCommandHandler.cs` → `SiteCreatedIntegrationEventHandler.cs` | `SiteCreated` |
| وابستگی Domain | `Inventory.Domain.csproj` | `ProjectReference` به `Personnels.Domain` |
| ArchitectureTests | `Visitors.../LayerTests.cs`، `Dejban.ArchitectureTests/.../ModuleTests.cs` | لایه‌ها سخت؛ آرایهٔ بین‌ماژولی خالی |
| Public API بی‌مصرف در بازرسی | `IDoorApi`، `DoorApi` | ثبت در Personnels؛ inject بیرونی دیده نشد |

درس `08-cqrs-mediatr.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخهٔ بسته | `Directory.Packages.props` | MediatR 12.5.0، FluentValidation DI 12.1.0، ErrorOr 2.0.1، Scrutor 7.0.0 |
| ثبت دژبان | `ApplicationConfiguration.cs` | `RegisterServicesFromAssemblies`، سه `AddOpenBehavior` |
| قراردادها | `ICommand.cs`، `IQuery.cs` | `IBaseCommand` فقط روی command |
| Validation دژبان | `ValidationPipelineBehavior.cs` | `where TRequest : IBaseCommand` |
| Logging / Exception | `RequestLoggingPipelineBehavior.cs`، `ExceptionHandlingPipelineBehavior.cs` | قید `class` و برای logging مقدار `IErrorOr` |
| Query | `GetPersonnelsQuery` / handler / endpoint | بدون `IBaseCommand` |
| Command | `CreatePersonnelCommand` / handler / endpoint | `ICommand<Guid>`، `SaveChanges`، outbox |
| Domain handler | `IDomainEventHandler`، `PersonnelsModule` Decorate | نه `INotification` |
| هویت | `ServiceCollectionExtensions.AddApplication`، `ValidationBehavior` | یک behavior؛ `LoginCommand : IRequest<ErrorOr<object>>` |
| نبود IPublisher | جستجوی دژبان | هیچ مورد |

درس `09-ef-core-postgresql.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخهٔ EF/Npgsql | `Directory.Packages.props` | EF Core 10.0.0، Npgsql.EF 10.0.0، NamingConventions 10.0.0-rc.2 |
| ثبت پرسنل | `PersonnelsModule.cs` | `AddDbContext`، `UseNpgsql`، `MigrationsHistoryTable`، `InsertOutboxMessagesInterceptor`، `UseSnakeCaseNamingConvention` |
| کلید اتصال | همان + درس 02 | `GetConnectionString("Postgres")` |
| مدل و فیلتر | `PersonnelsDbContext.cs` | `HasDefaultSchema`، `ApplyTenantQueryFilters`، `ApplySoftDeleteQueryFilters` |
| نگاشت پرسنل | `PersonnelConfiguration.cs` | ایندکس فیلترشده، `uuid[]` برای `ContractIds`، FK Restrict/Cascade |
| schemaها | هشت `Schemas.cs` | `personnels` … `weigh_bridge` |
| Query | `GetPersonnelsQueryHandler`، `PersonnelRepository.GetQueryable` | `AsNoTracking`، projection، `PagedList.CreateAsync` |
| Pagination sync | `Common/Abstractions/Queries/PagedList.cs` | `Count()` و `ToList()` بعد از `Task.CompletedTask` |
| Write | `CreatePersonnelCommandHandler` | `Insert`، `SaveChangesAsync`، آپلود DCC |
| Outbox | `InsertOutboxMessagesInterceptor` | `SavingChangesAsync`، `OutboxMessage` |
| Migrate startup | `MigrationExtensions.ApplyMigrations` | هشت `Database.Migrate()` بعد از Delay 10s |
| Bypass فیلتر | `GetPersonnelDocumentsQueryHandler` | `IgnoreQueryFilters` بعد از `AnyAsync` روی پرسنل |
| هویت | `ApplicationDbContext`، `ServiceCollectionExtensions.AddInfrastructure` | `IdentityDbContext`، tenant/soft-delete، بدون snake_case در ثبت دیده‌شده |

درس `10-dapper.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه | `Directory.Packages.props` | Dapper 2.1.66 |
| ارجاع مستقیم | `Dejban.Common.Application.csproj` | `PackageReference Include="Dapper"` |
| underscore map | `ApplicationConfiguration.cs` | `DefaultTypeMap.MatchNamesWithUnderscores = true` |
| factory | `IDbConnectionFactory`، `DbConnectionFactory`، `InfrastructureConfiguration` | `NpgsqlDataSource`، کلید `Postgres` از `Program.cs` |
| type handler | `GenericArrayHandler.cs`، `GuidListHandler.cs` | `SqlMapper.AddTypeHandler` |
| Outbox | `Personnels/.../Outbox/ProcessOutboxJob.cs` | `QueryAsync`، `ExecuteAsync`، `FOR UPDATE` |
| Idempotency | `IdempotentDomainEventHandler.cs` | `ExecuteScalarAsync` EXISTS، `ExecuteAsync` INSERT |
| Import | `PersonnelImportBatchProcessor.ClaimAsync` | `SKIP LOCKED`، `CommandDefinition` |
| گزارش | `PatrolReportService.cs` | SQL `visitors.*` و `personnels.*` با `@boardDate` |
| Replica | `ReplicaHealer.cs` | schema/table از enum، مقادیر پارامتری |
| نبود در Reporting | جستجوی `using Dapper` در Reporting | هیچ مورد |

درس `11-messaging.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه | `Directory.Packages.props` | MassTransit* 8.5.7، Quartz.Extensions.Hosting 3.15.1 |
| ثبت دژبان | `InfrastructureConfiguration.cs` | `RabbitMqTransport`، `UseMessageRetry`، `UseCircuitBreaker`، `UseTenantContextFilters`، `ConfigureEndpoints` |
| IEventBus | `IEventBus.cs`، `EventBus.cs` | `IBus.Publish` / `PublishBatch` |
| Outbox دامنه | `InsertOutboxMessagesInterceptor`، `ProcessOutboxJob`، `OutboxMessage` | schema ماژول، Dapper، Quartz |
| Domain→integration | `PersonnelCreatedDomainEventHandler` | `PublishAsync(PersonnelCreated)` |
| Inbox insert | `IntegrationEventConsumer<>` | `ON CONFLICT DO NOTHING`؛ Visitors `visitors.inbox_messages` |
| Inbox process | `ProcessInboxJob`، `IdempotentIntegrationEventHandler` | handlers Presentation |
| هویت outbox | `ServiceCollectionExtensions.AddMassTransit` | `AddEntityFrameworkOutbox`، `UseBusOutbox`، `UsePostgres` |
| SiteCreated | `CreateSiteCommandHandler` | `IPublishEndpoint.Publish` قبل از `SaveChangesAsync` |
| Site handler پرسنل | `SiteCreatedIntegrationEventHandler` | `Site.Create` + SaveChanges |
| Tenant headers | `TenantContextPublishFilter`، `TenantContextConsumeFilter` | `X-Tenant-SiteIds`، `X-IsSuperAdmin` |
| Interval نمونه | `modules.personnels.json` | Outbox 2s Batch 200؛ Inbox 5s Batch 50 |
| نبود DLQ در کد | جستجوی Dejban | هیچ `DeadLetter` |

درس `12-quartz.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه | `Directory.Packages.props`، `Dejban.Common.Infrastructure.csproj` | `Quartz.Extensions.Hosting` 3.15.1 |
| ثبت | `InfrastructureConfiguration.cs` | `AddQuartz` با SchedulerId/Name تصادفی؛ `AddQuartzHostedService` با `WaitForJobsToComplete` |
| نبود persistent/cluster | جستجوی `UsePersistentStore` / JobStore | هیچ مورد |
| نبود در هویت | جستجوی IdentityServer | هیچ `AddQuartz` |
| ثبت job | `ConfigureProcessOutboxJob` / Inbox / `ConfigureProcessPersonnelImportJob` | `IConfigureOptions<QuartzOptions>`، `AddJob`، `WithSimpleSchedule` |
| Attribute | کلاس‌های `Process*Job` | `[DisallowConcurrentExecution]` |
| Personnels زمان‌بندی | `modules.personnels.json` | Outbox 2s/200؛ Inbox 5s/50؛ Import 2s/200 |
| بقیه ماژول‌ها | `modules.*.json` پایه | Outbox/Inbox 5s/50؛ Development اغلب batch 20 |
| Import اجرا | `ProcessPersonnelImportJob`، `PersonnelImportBatchProcessor` | scope + cancellation؛ catch عمومی |

درس `13-signalr.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| بسته کلاینت بک‌اند | `Directory.Packages.props` | `Microsoft.AspNetCore.SignalR.Client` 10.0.0 |
| بسته فرانت | `apps/dejban/package.json` | `@microsoft/signalr` ^8.0.17 |
| MapHubها | `Program.cs` هویت، ACL، RequestTracker، Gate، Baskool | جدول درس 13 |
| دژبان بدون hub | `Dejban.Api/.../ServiceCollectionExtension.cs` | فقط `AddSignalR()` |
| نبود backplane | جستجوی `AddAzureSignalR` / SignalR Redis | هیچ مورد |
| ساعت | `TimeHub`، `TimeBroadcastHostedService`، `server-clock.js` | رویداد `ServerTime`، JWT |
| تیکت | `TicketHub`، `TicketRealtimeNotifier`، `use-ticket-hub.js` | `TicketUpdated`، group `user:` |
| گیت | `GateConnectionStatusHub`، `Clients.All` + `ReceiveGateStatus` | `JoinGateGroup` برای push استفاده‌نشده |
| Nginx hubs | `default.conf.template` | بدون `gateStatusHub` / `useractivityhub` |
| YARP hubs | `ApiGateway/appsettings*.json` | شامل `timeserverhub`، `tickethub`، `gateStatusHub`، … |
| VehiclePolicy | `VehiclePolicyHub.cs` | `[AllowAnonymous]` |

درس `14-grpc-devices.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه‌ها | `Directory.Packages.props` | Grpc.AspNetCore 2.71.0، Tools 2.76.0، Google.Protobuf 3.33.1 |
| Proto | `Common/Protos/{Virdi,ZK,Tiam,SSM}/` | `VirdiService`، `ZKService`، `TiamService`، `SSM` + Subscribe/Stream |
| سرور | `*GrpcServer/Program.cs` | `AddGrpc`، `MapGrpcService`، reflection در Development |
| HTTP/2 | `VirdiGrpcServer/appsettings.json` | `Kestrel:EndpointDefaults:Protocols=Http2` |
| کلاینت | `ACLServer` wrappers + `AddGrpcClient<SSM.SSMClient>` | `GrpcChannel.ForAddress`، Singleton |
| Flag | `DeviceGrpcServicesSettings`، appsettings Development | Enabled false نمونه؛ strategy/hosted شرطی؛ wrapper همیشه |
| آدرس | `*GrpcClientSettings:ServerAddress` | localhost/host.docker.internal پورت‌های 5050–5054 |
| نبود Compose/YARP | جستجو | هیچ سرویس/route gRPC دستگاه |
| مسیر رویداد | `ZKStartupService` → MediatR → AccessLog / `DeviceHub` | stream + SignalR |
| نبود auth gRPC سرور ZK | جستجو در ZKGrpcServer | هیچ Authorize |

درس `15-hangfire.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه‌ها | `Directory.Packages.props` | Hangfire.Core/AspNetCore 1.8.22؛ PostgreSql 1.20.12؛ MemoryStorage 1.8.1.2 |
| RT ثبت | `RequestTracker/.../ServiceCollectionExtensions.cs` | `UsePostgreSqlStorage` schema `hangfire`؛ `AddHangfireServer` ServerName `request_tracker` |
| RT recurring | `RequestTracker/Program.cs` | `RecurringJob.AddOrUpdate<StepSubstitutionSweeper>("step-substitution-sweeper", …, "*/5 * * * *")` |
| Sweeper | `StepSubstitutionSweeper.ProcessDueAsync` | CTS 20s؛ Sync/Revert؛ AutoApprove Completed |
| ACL ثبت | `ACLServer/.../ServiceCollectionExtensions.cs` | `UseMemoryStorage` فعال؛ بلوک Postgres comment؛ Queues `devices_queue` |
| Job زنجیره | `DeviceSyncService.ChainDeviceJobs` | `Enqueue` / `ContinueJobWith(OnAnyFinishedState)`؛ `[AutomaticRetry(Attempts = 0)]` |
| Dashboard | `*HangfireDashboardExtensions`، `HangfireDashboardAuthFilter` | Enabled؛ loopback یا Basic؛ FixedTimeEquals |
| نبود در دژبان | جستجوی Hangfire در Dejban | هیچ مورد |
| نبود hangfire در gateway | جستجوی ApiGateway | هیچ match |
| WorkerCount | `HangfireSettings:WorkerCount` در appsettings | RT و ACL خوانده می‌شود |

درس `16-dcc-s3.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه S3 | `Directory.Packages.props`، `DCC.csproj` | `AWSSDK.S3` 3.7.419 |
| Provider DI | `DCC/.../ServiceCollectionExtensions.cs` | `Storage:Provider` → `S3FileStorage` یا `LocalFileStorage` |
| S3 client | `S3FileStorage.cs` | `AmazonS3Client`، `ForcePathStyle`، `PublicEndpoint` برای sign |
| API | `FilesController.cs` | Upload/Download/presign/meta/Delete/Restore/Purge/public |
| متادیتا | `FileEntity`، `FileRevision` | `StoragePath`، hash، soft-delete |
| Access | `FileAccessService.CanAccessAsync` | IsPublic؛ RequireSiteMatch؛ role/permission comment |
| کلاینت | `Common/FileService/DccHttpClient.cs` | Upload/Download/presign؛ Search بدون endpoint سرور |
| Gateway `/files` | `appsettings.Docker.json` ReverseProxy PublicFiles | PathPattern به `/api/v1/Files/public/{**}` روی `dcc` |
| `PublicFiles:Mode` | gateway JSON | در `Program.cs` bind نشده |
| MinIO | `docker-compose.yml` / `compose.data.yml` | `minio`، `minio-init`، bucket `dcc-files` |
| Compose DCC | `docker/compose.backend.yml` | `Storage__Provider: S3` و کلیدهای S3 |
| CreatePutUrl | جستجو | فقط تعریف؛ بدون call site |
| Upload anonymous | `FilesController.UploadFile` | `[AllowAnonymous]` |

درس `19-redis.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه‌ها | `Directory.Packages.props`، `Common.csproj` | Hybrid 10.0.0؛ StackExchangeRedis 10.0.0؛ HealthChecks.Redis 9.0.0 |
| ثبت | `Common/.../ServiceCollectionExtensions.AddCacheServices` | Connect → Redis cache؛ catch → Memory؛ `ICacheService` |
| Blacklist | `TokenBlackListService` | پیشوند `revoked:`؛ DisableLocalCache روی Set |
| Middleware | `TokenRevokeMiddleware`، `UseTokenRevoke` | 401 اگر revoked؛ AllowAnonymous رد می‌شود |
| Logout | `LogoutCommandHandler` | `RevokeAsync(accessToken)` |
| دژبان بدون revoke pipeline | `Dejban.Api/Program.cs` | `AddTokenRevokeMiddleware` در Infra؛ بدون `UseTokenRevoke` |
| Claim cache | `RemoteClaimService`، `ClaimService`، `UserSiteClaimsCache` | tag `UserSiteClaims`؛ local 2s |
| Health | `Dejban.Api/Program.cs` | `AddRedis(redisConnectionString)` |
| Compose | `docker-compose.yml` سرویس `redis` | بدون volume فعال |
| نبود SignalR backplane | درس 13 / جستجو | Redis برای SignalR scale-out ثبت نشده |

درس `20-observability.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه‌ها | `Directory.Packages.props` | Serilog.AspNetCore 10.0.0؛ OTLP exporter 1.15.3؛ HealthChecks 9.0.0 |
| Serilog host | `Dejban.Api/Program.cs` و Identity/… | `UseSerilog` + `ByExcluding` commandText outbox؛ `UseSerilogRequestLogging` |
| پیکربندی لاگ | `GlobalAppsettings/globalAppsettings*.json` | WriteTo Console+Seq؛ Override Outbox/Inbox Warning؛ Enrich |
| TraceId | `LogContextTraceLoggingMiddleware` | `Activity.Current?.TraceId` → LogContext |
| OTEL | `InfrastructureConfiguration.cs` | `AddOpenTelemetry` + AspNetCore/Http/EF/Redis/Npgsql/MassTransit source + `AddOtlpExporter` |
| ServiceName | `DiagnosticsConfig.ServiceName` | `"Dejban.Api"` |
| OTLP endpoint کلید | GlobalAppsettings | `OTEL_EXPORTER_OTLP_ENDPOINT` |
| نبود OTEL خارج دژبان | جستجو | فقط Infra دژبان در مسیر خوانده‌شده |
| Health | `Dejban.Api/Program.cs` | `AddNpgSql` + `AddRedis`؛ `MapHealthChecks("health")` |
| Uris unused | جستجوی AddUri در Dejban | پکیج بدون call site |
| Gateway metrics | `RequestMetricsMiddleware` / `RequestMetricsStore` | in-process؛ endpoint `/api/v1/gateway/request-metrics` |
| نبود Serilog gateway | جستجوی ApiGateway | هیچ UseSerilog |
| Seq/Jaeger Compose | `docker-compose.development.yml` | سرویس‌ها comment |
| Exception دژبان | `GlobalExceptionHandler` | LogError؛ Detail فقط Dev/DockerDevelopment |

درس `21-postgres-dr.md`.

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| هفت کلاستر | `clusters.env`، `compose.data.yml` | identity…gate؛ پورت 18001–18007؛ DBهای `payamgostar_*` |
| Volume اپ | `compose.data.yml` / `docker-compose.yml` | مثلاً `dejbandb-data` → `/var/lib/postgresql` |
| Image ناهمسان | درس 03 + README DR | `postgres` / `postgres:latest` / پیش‌فرض `postgres:18.1` |
| کیت جدا | `infrastructure/postgres-dr/README.md` | Compose اپ را عوض نمی‌کند؛ connection دستی |
| Prepare | `scripts/prepare-primary.sh` | replicator؛ pg_hba؛ دو slot؛ بدون restart |
| Standby | `docker-compose.standby.yml`، `standby-entrypoint.sh` | `pg_basebackup`؛ `standby.signal` |
| Promote / PITR / failback | `promote.sh`، `restore-pitr.sh`، `failback.sh` | `pg_promote`؛ کانتینر موقت restore |
| Backup compose | `docker-compose.backup.yml` | entrypoint `backup-daemon.sh` |
| فایل غایب | فهرست `scripts/` | نبود `backup-daemon.sh` و `backup.sh` در tree |
| خارج از replicate | README DR | Redis، MinIO، RabbitMQ |
| Migrate | `MigrationExtensions.ApplyMigrations` | schema؛ نه backup |

درس `22-turborepo.md` (مسیرها نسبت به `dejban_frontend_new`).

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| packageManager / engines | `package.json` | `npm@10.9.2`؛ `node >= 20`؛ نام `pg_frontend` |
| workspaces | همان | `apps/*`، `packages/*` |
| turbo dependency | همان + optional | `turbo` ^2.10.12؛ `@turbo/linux-64` / `@turbo/windows-64` 2.10.12 |
| task graph | `turbo.json` | `dependsOn` `^build`؛ `start`→`build`؛ `dev`/`start` persistent + cache false |
| outputs / env | همان | `.next/**` بدون cache؛ `dist/**`؛ `passThroughEnv` `NEXT_PUBLIC_*` |
| اپ‌ها | `apps/*/package.json` | Next: `next build --turbopack`؛ access-control: `vite build` |
| پکیج مشترک | `packages/*/package.json` | `@repo/ui` lint/check-types؛ auth/config بدون `build` |
| CI | `.gitlab-ci.yml` | `npx turbo run build --concurrency=1 --no-daemon`؛ سپس pm2 `npm start` |
| Docker | `docker/Dockerfile.next` | `npm ci`؛ `turbo run build --filter=${APP_NAME}` |
| Compose جدا | `docker-compose.yml` | شبکه `dejban-frontend`؛ نه همان مسیر CI pm2 |
| نبود pnpm-workspace | جستجوی ریشه فرانت | فایل نیست |
| remote cache اختصاصی | `turbo.json` / env در repo | تنظیم تیم/توکن دیده نشد |

درس `23-nextjs.md` (مسیرها نسبت به `dejban_frontend_new`).

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه Next | `apps/main\|dejban\|gate\|dcc/package.json` | `"next": "^16.2.6"` |
| App Router | `apps/*/src/app/**/page.jsx`، `layout.jsx` | بدون Pages Router محصولی |
| نبود middleware / route handler | جستجوی `apps/**/middleware.*` و `**/route.{js,ts}` | یافت نشد |
| basePath | `apps/dejban\|gate\|dcc/next.config.mjs` | `/dejban`، `/gate`، `/dcc` |
| main بدون basePath | `apps/main/next.config.mjs` | `output: 'standalone'`؛ redirect `/`→`/dejban`؛ rewrites دامنه |
| Root layout سرور | `apps/*/src/app/layout.jsx` | `async function RootLayout`؛ `metadata` |
| Dashboard کلاینت | `apps/dejban/src/app/dashboard/layout.jsx` | `'use client'`؛ `AuthGuard` |
| Config | `apps/*/src/global-config.js`، `app/client-init.jsx` | `createAppConfig`؛ `ConfigRegistry.set` |
| Login UI | `apps/main/src/app/auth/jwt/sign-in/page.jsx` | `JwtSignInView` |
| Login action | `packages/ui/src/auth/context/jwt/action.js` | `signInWithPassword` → `apiClient.post` |
| API base | `packages/api-client/src/axiosInstance.ts` | `resolveBaseUrl` از `NEXT_PUBLIC_SERVER_URL` |
| Staff page | `apps/dejban/.../personnel/staff/page.jsx` | `PageGuard` + `StaffListView` |
| loading / not-found | `apps/dejban/src/app/loading.jsx`، `not-found.jsx` | `SplashScreen`؛ `NotFoundView` |
| Docker args | `docker-compose.yml` | `NEXT_PUBLIC_SERVER_URL=/api/v1`؛ `NEXT_PUBLIC_BASE_PATH` (در next.config خوانده نشد) |
| transpilePackages | `next.config.mjs` هر چهار اپ | `@repo/ui`، `@repo/auth`، `@repo/api-client`، `@repo/config` |

درس `24-vite-access-control.md` (مسیرها نسبت به `dejban_frontend_new`).

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه‌ها | `apps/access-control/package.json` | `vite` ^6.3.5؛ `react` ^19.1.1؛ `react-router` ^8.3.0؛ `swr` ^2.3.6 |
| Vite config | `apps/access-control/vite.config.js` | `base` از `VITE_BASE`؛ port `3033`؛ plugin react-swc |
| Entry HTML | `apps/access-control/index.html` | `#root`؛ `base href="/access-control/"`؛ `config.js` |
| Bootstrap | `apps/access-control/src/main.jsx` | `ConfigRegistry.set`؛ `createBrowserRouter` basename `/access-control`؛ DEV hash token |
| App shell | `apps/access-control/src/app.jsx` | `JwtAuthProvider`؛ بدون ClientProvider/RQ |
| Config env | `apps/access-control/src/global-config.js` | `import.meta.env.VITE_SERVER_URL` و … |
| Routes + AuthGuard | `src/routes/sections/dashboard.jsx` | `AuthGuard` دور layout؛ lazy pages |
| API endpoints | `src/lib/api.js` | `accessGroups.list` = `/accessgroups/getaccessgroups` |
| SWR list | `src/actions/access-group.js` | `useGetAccessGroups` → `useSWR` + `api.fetcher` |
| UI list | `sections/access-group/view/access-group-list-view.jsx` | `AccessGroupListView` |
| Resolve Vite URL | `packages/api-client/src/axiosInstance.ts` | `import.meta.env.VITE_SERVER_URL` |
| Docker SPA | `docker/Dockerfile.access-control`، `docker/nginx/access-control.conf` | turbo filter؛ `try_files` → index.html |
| لبه Compose | `docker-compose.yml`، `default.conf.template` | سرویس `access-control`؛ `location /access-control/` |
| config stub | `public/config.js` | `window.globalConfig`؛ کامنت ممنوعیت API URL |

درس `25-api-client-auth.md` (مسیرها نسبت به `dejban_frontend_new`).

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| Instance Axios | `packages/api-client/src/axiosInstance.ts` | `createApiClient`؛ `apiClient = createApiClient(resolveBaseUrl())` |
| Base URL | همان | `NEXT_PUBLIC_SERVER_URL` سپس `VITE_SERVER_URL` |
| Token storage | `packages/api-client/src/tokenStorage.ts` | `jwt_access_token`؛ get/set/clear |
| Request headers | `axiosInstance.ts` interceptor | `Authorization`؛ `X-Site-Id`؛ `Accept-Language`؛ skip Bearer روی refresh |
| 401 refresh | همان response interceptor | `POST endpoints.auth.refresh`؛ `_retry`؛ `refreshPromise` |
| Retry امن | `packages/api-client/src/apiRetry.ts` | GET/HEAD/OPTIONS؛ نه 401 |
| Auth state | `packages/auth/src/AuthContext.tsx` | `checkUserSession` → getMe؛ `authenticated: !!user` |
| UI re-export | `packages/ui/src/auth/context/jwt/auth-provider.jsx` | `export { AuthProvider } from '@repo/auth'` |
| Login action | `packages/ui/.../jwt/action.js` و کپی `apps/main/.../action.js` | `signInWithPassword`؛ `signOut` |
| AuthGuard / GuestGuard | `packages/ui/src/auth/guard/*.jsx` | hard redirect vs `router.replace` |
| Site header store | `packages/ui/src/auth/utils/site-storage.js` | `useSiteStore`؛ `selectedSiteId` |
| Login call site | `apps/main/.../jwt-sign-in-view.jsx` + `sign-in/layout.jsx` | GuestGuard؛ checkUserSession |
| Dashboard guard | dejban/gate/dcc/access-control layouts/routes | `AuthGuard` |

درس `26-client-state.md` (مسیرها نسبت به `dejban_frontend_new`).

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| RQ provider | `packages/ui/.../client-provider.jsx` | `QueryClient`؛ `gcTime` 5m؛ site → `resetQueries` |
| Staff keys | `apps/dejban/src/services/staff/staff.keys.js` | `staffKeys.all` / `pagination` / `detail` |
| Staff query/mutation | `staff.service.js` | `useGetStaffWithPagination`؛ `invalidateQueries(staffKeys.all)` |
| DCC pattern | `apps/dcc/src/services/dcc/dcc.service.js` | `dccKeys`؛ invalidate lists |
| SWR ACL | `apps/access-control/src/actions/access-group.js` | `useSWR`؛ revalidate* false |
| SWR mutate UI | `access-group-list-view.jsx` | `localMutate()` |
| API key Zustand | `stores/api-key-actions-store.js` + list view | `getAPIKeys`؛ نه SWR در آن صفحه |
| Site persist | `packages/ui/.../site-storage.js` | `selectedSiteId` localStorage |
| Settings persist | `settings-provider.jsx`؛ `SETTINGS_STORAGE_KEY` | `app-settings` |
| Workspace tabs | `apps/dejban/.../workspace-tabs-store.js` | Zustand + in-memory `tabStateMap` TTL |
| swr unused dejban | جستجوی import `swr` در `apps/dejban` | dependency در package.json؛ import نیست |
| بدون RQ در ACL | `apps/access-control/src/app.jsx` | نبود `ClientProvider` |

درس `27-mui-i18n.md` (مسیرها نسبت به `dejban_frontend_new`).

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه‌ها | `apps/dejban/package.json` | `@mui/material` ^7.3.2؛ i18next؛ stylis-plugin-rtl؛ emotion |
| Theme defaults | `packages/ui/src/theme/theme-config.js` | `direction: 'rtl'`؛ `defaultMode: 'light'`؛ IRANSans |
| createTheme | `packages/ui/src/theme/create-theme.js` | colorSchemes light/dark؛ `applySettingsToTheme` |
| ThemeProvider | `packages/ui/src/theme/theme-provider.jsx` | settings + `localeComponents`؛ `Rtl` |
| RTL Emotion | `packages/ui/src/theme/with-settings/right-to-left.jsx` | `rtlPlugin`؛ `document.dir` |
| i18n langs | `apps/dejban/src/locales/locales-config.js` و `packages/ui/.../locales-config.js` | `fa-IR`، `en-US`؛ `fallbackLng`؛ `RTLLanguages` |
| Resources | `i18nResourceLoader` | `langs/${lang}/${namespace}.json` |
| SSR detect | `apps/dejban/src/locales/server.js` | `detectLanguage`؛ cookie `i18next` |
| Client i18n | `apps/dejban/src/locales/i18n-provider.jsx` | localStorage `i18nextLng` |
| Change lang | `packages/ui/src/locales/use-locales.js` | `onChangeLang` → direction + dayjs + refresh |
| Language UI | `language-popover.jsx` + dashboard `layout.jsx` | `LanguagePopover data={allLangs}` |
| Jalali | `packages/ui/src/locales/localization-provider.jsx` | `AdapterMomentJalaali` vs `AdapterDayjs` |
| API lang header | `packages/api-client/src/axiosInstance.ts` | `Accept-Language` |
| بدون عربی | جستجوی supportedLngs / langs | فقط fa و en |
| Sync hook unused | `useLocaleDirectionSync` | تعریف؛ call site اپ یافت نشد |

درس `28-nginx-edge.md` (مسیرها نسبت به `dejban_frontend_new` مگر خلاف).

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| استک کامل | `docker-compose.yml` | سرویس `nginx`؛ mount `default.conf.template`؛ `API_GATEWAY`؛ پورت `3080` |
| استک فقط-nginx | `docker-compose.nginx-only.yml` | mount `nginx-only.conf.template`؛ `HOST_GATEWAY` |
| لبه کامل | `docker/nginx/default.conf.template` | upstreams؛ `/api/` `/Api/` `/files/`؛ regex hubs؛ UI locations |
| فقط-nginx | `docker/nginx/nginx-only.conf.template` | proxy به پورت‌های host؛ `= /` → `/dejban` |
| SPA ACL | `docker/nginx/access-control.conf` + `Dockerfile.access-control` | `try_files`؛ image داخلی |
| WS headers | `default.conf.template` | `map $http_upgrade`؛ timeout 3600s |
| Body limit | همان | `client_max_body_size 100m` |
| بدون TLS لبه | `listen 80` فقط در قالب‌ها | HTTPS فقط به gateway با verify off |
| Hub gap | regex location | نبود `gateStatusHub` / `useractivityhub` |
| شبکه جدا | `docker-compose.yml` کامنت/شبکه | `dejban-frontend`؛ نه شبکه بک‌اند |
| basePath هم‌تراز | next.config / Vite base vs locations | `/dejban` `/gate` `/dcc` `/access-control` |

محدوده: `17-reporting`، `18-mediamtx-baskool`، و `29-scanner-agent` در progress برابر `Skipped`؛ شاهد Reporting/Baskool/Scanner Agent برای درس جدا جمع نشد.

درس `31-testing.md` (فاز AD؛ بدون اجرای runner).

| ادعا | مسیر | نماد یا کلید |
|---|---|---|
| نسخه‌های تست بک‌اند | `Directory.Packages.props` | xunit 2.9.3؛ FluentAssertions 8.8.0؛ NetArchTest 1.3.2؛ Testcontainers 4.9.0؛ coverlet 6.0.4 |
| Unit Visitors | `…Visitors.UnitTests/Visitors/BlackListScheduleTests.cs` | `[Fact]` روی `IsActiveDuring`؛ `VisitorTests` عمدتاً کامنت |
| InternalsVisibleTo | `…Visitors.Application.csproj` | UnitTests + IntegrationTests |
| Architecture لایه | `…Visitors.ArchitectureTests/Layers/LayerTests.cs` | Domain/Application/Presentation قوانین |
| ModuleTests ضعیف | `…Dejban.ArchitectureTests/Layers/ModuleTests.cs` | `otherModules = []` |
| Integration host | `…Visitors.IntegrationTests/.../IntegrationTestWebAppFactory.cs` | Postgres+Redis containers؛ env ConnectionStrings |
| CreateVisitor IT | `…/CreateVisitorTests.cs` | Theory invalid فعال؛ valid کامنت |
| Dejban.IT خالی از سناریو فعال | `…/Dejban.IntegrationTests/CreateVisitor/CreateVisitorTests.cs` | بدنهٔ Fact کامنت |
| RT InMemory | `RequestTracker.UnitTests/.../TestDbContextFactory.cs` | `UseInMemoryDatabase` + `FakeTenantContext` |
| ACL unit | `ACLServer.UnitTests/RelayOpenPolicyTests.cs` | سیاست رله بدون IO |
| Inventory PG fixture | `…Inventory.IntegrationTests/InventoryPostgresFixture.cs` | `postgres:16-alpine` + `MigrateAsync` |
| Playwright main | `apps/main/playwright.config.ts`، `tests/smoke/public/specs/Login.spec.ts` | پروژه‌های smoke/regression/e2e |
| turbo test tasks | `dejban_frontend_new/turbo.json`، ریشه `package.json` | `test:e2e` / `test:unit`؛ `cache: false` |
| CI بدون تست | `dejban_frontend_new/.gitlab-ci.yml` | فقط `turbo run build`؛ بدون playwright/vitest |
| بدون CI بک‌اند در ریشه | جستجوی `.gitlab-ci.yml` زیر `dejban_backend_new` | فایلی یافت نشد |

## شاهدهایی که عمداً باز نشدند

- `GlobalAppsettings/*.json` و connection stringهای کامل برای جلوگیری از ورود secret. در فاز B فقط route و آدرس cluster داخل `ApiGateway/appsettings*.json` خوانده شد. مقدار رمز و کلید JWT نقل نشد.
- فایل‌های `.env` کنار سرویس‌ها.
- `Common/EventBus/eventbus_init/definitions.json` فقط به‌عنوان مسیر mount ثبت شد؛ فهرست exchangeها استخراج نشد.
- بدنهٔ migrationهای EF. وجود `Migrations` و `ModelSnapshot` برای چند context دیده شد، ولی schema از روی آن‌ها بازنویسی نشد.
