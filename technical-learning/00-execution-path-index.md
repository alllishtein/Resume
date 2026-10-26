# نمایهٔ مسیر اجرا

این فایل درس فناوری نیست. سه میزبان را به middleware، endpoint، handler، و داده وصل می‌کند تا درس‌های بعدی از `Program.cs` شروع کنند و وسط pipeline حدس نزنند. جزئیات login در `00-login-execution-path.md` و جزئیات فهرست پرسنل در `00-personnel-list-execution-path.md` است.

هیچ‌کدام از این ترتیب‌ها با اجرای پردازه چک نشده‌اند. ترتیب از روی محل صدا زدن متدها در `Program.cs` است. اثری که فقط حدس زمان اجرا باشد، در همان بند `inferred` یا اجرا‌نشده نوشته شده است.

## Gateway

فایل: `ApiGateway/Program.cs`

ثبت سرویس، قبل از `Build`:

1. `AddJsonFile` برای `globalAppsettings.json` و `globalAppsettings.{Environment}.json` با `optional: false`.
2. `AddDefaultCors` و `AddCustomJwtAuth`.
3. `AddTrustedForwardedHeaders` و `AddCustomRateLimiters` و `AddCustomCachePolicies`.
4. یک بار `AddReverseProxy`، بعد `LoadFromMemory(IdentityServerRoutes.routes, [])`، بعد هشت `LoadFromConfig`. کلیدها در `ApiGateway/Abstractions/Constants/ConfigConstants.cs` هستند: `ReverseProxy:IdentityServer`، `RequestTracker`، `DCC`، `ACLServer`، `Dejban`، `Reporting`، `GateServer`، `PublicFiles`.

Pipeline بعد از `Build`، فقط قدم‌هایی که به login و فهرست پرسنل مربوط‌اند:

1. `UseForwardedHeaders`
2. middlewareای که برای مسیر غیر از `CameraAuthApi` داخل lambda دوباره `UseHttpsRedirection` را صدا می‌زند. این الگو در درس 01 به‌عنوان مشکل ثبت شده است. اثرش روی یک درخواست واقعی اجرا نشد.
3. `UseCors`
4. اگر provider فایل عمومی Local نباشد، `UseStaticFiles` برای `/files` اجرا نمی‌شود. در JSON داکر provider برابر `MinIO` است، پس شاخهٔ static برای آن محیط داخل `if` نمی‌رود. این از روی شرط کد و مقدار JSON است، نه از روی پردازهٔ در حال اجرا.
5. `UseRateLimiter`
6. `AccessTokenQueryMiddleware` و `UseTokenRevoke`
7. `UseAuthentication` و `UseAuthorization`
8. `UseOutputCache`
9. `ClientIpForwardingMiddleware` و `ProxyErrorHandlingMiddleware` و `RequestMetricsMiddleware`
10. `MapReverseProxy`

endpointهای خود gateway، مثل `/health/reporting-routes`، قبل از `MapReverseProxy` مپ شده‌اند و به دژبان یا هویت forward نمی‌شوند. health گزارش section اشتباه `Reporting:Routes` را می‌خواند. routeهای واقعی زیر `ReverseProxy:Reporting` هستند. این تفاوت کلید است. وضعیت 503 بودنش اجرا نشد و `inferred` می‌ماند.

## هویت

فایل: `Microservices/IdentityServer/Program.cs`

برای Login این ترتیب مهم است:

1. `UseExceptionHandler`
2. `UseAuthentication`
3. `UseTenantContext` بین authentication و authorization
4. `UseAuthorization`
5. `MapHub` برای `/timeserverhub` و `/useractivityhub`
6. `MapControllers`

ورود به hubها نمی‌رود. `AuthController.Login` با `MapControllers` به MediatR می‌رسد. رفتار اعتبارسنجی با `ValidationBehavior<,>` در `IdentityServer/Abstractions/Extensions/ServiceCollectionExtensions.cs` ثبت شده است. داده از `ApplicationDbContext` و ASP.NET Identity است.

## دژبان

فایل: `Microservices/Dejban/API/Dejban.Api/Program.cs`

ثبت، قبل از `Build`:

1. آرایهٔ صریح `moduleApplicationAssemblies` برای هشت Application، بعد `AddApplication`
2. `AddInfrastructure` با `ConfigureConsumers` و `ConfigureReceiveEndpoints` هر ماژول
3. `AddModuleConfiguration` و `AddPresentation`
4. هشت متد صریح مثل `AddPersonnelsModule` که endpoint و DbContext همان ماژول را ثبت می‌کند

جزئیات مرز ماژول و پیام بین‌ماژولی در درس `07-modular-monolith.md` است.

Pipeline برای `GetPersonnels`:

1. `UseCors`
2. `ApplyMigrations` و `ApplySeedData` و `ApplyMediaMTXAsync` فقط هنگام بالا آمدن. جزو هر GET نیستند، ولی قبل از `MapEndpoints` await می‌شوند و بالا آمدن را معطل می‌کنند. `Task.Delay` داخل migration در درس 01 است.
3. `UseExceptionHandler`
4. `UseLogContext` و `UseSerilogRequestLogging`
5. `UseAuthentication`
6. `UseAuthorization`
7. `UseTenantContext` بعد از authorization
8. `MapEndpoints`

`GetPersonnels` یک `IEndpoint` است. `RequireAuthorization` دارد. `ISender.Send` به `GetPersonnelsQueryHandler` می‌رود. `ValidationPipelineBehavior` این query را نمی‌گیرد، چون قیدش `IBaseCommand` است.

داده: `PersonnelRepository.GetQueryable` سپس `PersonnelsDbContext` با فیلتر tenant و soft delete روی مدل. اتصال `UseNpgsql` در `PersonnelsModule`. schema برابر `personnels`.

`AddSignalR` در presentation هست. `MapHub` در این `Program.cs` نیست، پس این GET از hub رد نمی‌شود.

## فرق دو pipeline که باید حفظ شود

| موضوع | هویت | دژبان |
|---|---|---|
| ورود HTTP | controller و `MapControllers` | `IEndpoint` و `MapEndpoints` |
| جای tenant | بین authentication و authorization | بعد از authorization |
| اعتبارسنجی MediatR برای این دو درخواست | `ValidationBehavior` روی Login | behavior فرمان روی `GetPersonnelsQuery` نیست |
| پروکسی | `auth-login-route-v1` به `http://identityserver` در DockerDevelopment | `personnel-routes-v1` به `http://dejban` |

هر دو پشت همان gateway و همان `location /api/` در Nginx هستند. حروف مسیر در `00-api-path-case-investigation.md` جدا شده است و اجرای end-to-end هنوز `Runtime verification pending` است.

## اتصال‌های تأییدشده

این جدول فقط جایی را فهرست می‌کند که مرحلهٔ بعد از روی import، ثبت DI، یا کلید پیکربندی به مرحلهٔ قبل وصل شده است. match حروف مسیر و bind نام فیلد در این جدول نیستند، چون اجرا نشده‌اند.

| از | به | چه چیزی وصل می‌کند | شاهد | سند |
|---|---|---|---|---|
| صفحهٔ ورود main | `signInWithPassword` | import از `src/auth/view/jwt` و `context/jwt` | `apps/main/src/app/auth/jwt/sign-in/page.jsx`، `jwt-sign-in-view.jsx`، `action.js` | `00-login-execution-path.md` |
| `signInWithPassword` | Axios | `apiClient.post(endpoints.auth.login)` از `@repo/api-client` | `packages/api-client/src/axiosInstance.ts`، `endpoints.auth.login` | همان |
| Axios داکر | Nginx | base برابر `/api/v1` و `location /api/` | `dejban_frontend_new/docker-compose.yml`، `docker/nginx/default.conf.template` | همان و `00-api-path-case-investigation.md` |
| Nginx | YARP | `proxy_pass` به `API_GATEWAY`، پیش‌فرض پورت `7036` | template و `docker/compose.backend.yml` | همان |
| ثبت gateway | route ورود | `LoadFromConfig("ReverseProxy:IdentityServer")` و کلید `auth-login-route-v1` | `ApiGateway/Program.cs`، `ConfigConstants.IdentityServerProxy`، `appsettings.DockerDevelopment.json` | `00-yarp-config-investigation.md` |
| route ورود | هویت | cluster `identity-server-cluster`، آدرس DockerDevelopment برابر `http://identityserver`، بدون transform مسیر | همان JSON | `00-login-execution-path.md` |
| `Program.cs` هویت | `AuthController.Login` | `MapControllers` و `[HttpPost("Login")]` | `Microservices/IdentityServer/Program.cs`، `AuthController.cs` | همان |
| `Login` | `LoginCommandHandler.Handle` | `ISender.Send` و `IRequestHandler<LoginCommand, ErrorOr<object>>` بعد از `RegisterServicesFromAssemblyContaining<ApplicationAssemblyReference>` | `ServiceCollectionExtensions.AddApplication`، `LoginCommandHandler.cs` | همان |
| صفحهٔ پرسنل | `getStaffWithPagination` | import صفحه به `StaffListView`، view به `useGetStaffWithPagination`، service به `./staff.http` | `staff/page.jsx`، `staff-list-view.jsx`، `staff.service.js` | `00-personnel-list-execution-path.md` |
| HTTP پرسنل | Axios | `endpoints.staff.list` و `export default apiClient` | `apps/dejban/src/lib/api.js` | همان |
| ثبت gateway | route پرسنل | `LoadFromConfig("ReverseProxy:Dejban")` و کلید `personnel-routes-v1` | `ConfigConstants.DejbanProxy`، JSON داکر، مقصد `http://dejban` | همان و سند YARP |
| `Program.cs` دژبان | `GetPersonnels.MapEndpoint` | `AddEndpoints` به‌صورت Transient و `MapEndpoints` | `PersonnelsModule`، `EndpointExtensions`، `GetPersonnels.cs` | `00-execution-path-index.md` و درس `01` |
| endpoint پرسنل | `GetPersonnelsQueryHandler.Handle` | `ISender.Send` و `IQueryHandler<GetPersonnelsQuery, PagedList<object>>` داخل اسمبلی‌ای که به `AddApplication` داده شده | `Dejban.Api/Program.cs`، `ApplicationConfiguration.cs`، handler | `00-personnel-list-execution-path.md` |
| handler | PostgreSQL | `IPersonnelRepository.GetQueryable` به `PersonnelsDbContext` با `UseNpgsql` و schema برابر `personnels` | `PersonnelRepository.cs`، `PersonnelsModule.cs`، `PersonnelsDbContext.cs` | همان و درس `09-ef-core-postgresql.md` |
| `GetPersonnels` تا صفحه | `PagedList.CreateAsync` | `AsNoTracking` + projection؛ سپس `Count()` و `Skip`/`Take`/`ToList()` همگام | `GetPersonnelsQueryHandler.cs`، `PagedList.cs` | درس `09-ef-core-postgresql.md` |
| Quartz outbox پرسنل | PostgreSQL + handlers | `ProcessOutboxJob` با Dapper `QueryAsync`/`ExecuteAsync` روی `personnels.outbox_messages`؛ handler دامنه جدا | `ProcessOutboxJob.cs`، `IDbConnectionFactory`، `IdempotentDomainEventHandler` | درس `10-dapper.md`، `11-messaging.md`، `12-quartz.md` |
| Startup تا trigger outbox | `ConfigureProcessOutboxJob` | `AddQuartz` → `ConfigureOptions` → `AddJob`/`AddTrigger` با `Personnels:Outbox` (2s/200) | `InfrastructureConfiguration.cs`، `PersonnelsModule`، `modules.personnels.json` | درس `12-quartz.md` |
| Quartz import پرسنل | `PersonnelImportBatchProcessor` | `ProcessPersonnelImportJob` هر 2s؛ `SKIP LOCKED` claim | `ConfigureProcessPersonnelImportJob`، `ProcessPersonnelImportJob.cs` | درس `12-quartz.md` و `10-dapper.md` |
| ساعت سرور UI | `TimeHub` / broadcast | `serverClock` → `/timeserverhub` + JWT → `ServerTime`؛ هر دقیقه `TimeBroadcastHostedService` | `server-clock.js`، `TimeHub.cs`، YARP `timeserver-hub` | درس `13-signalr.md` |
| تیکت real-time | `TicketRealtimeNotifier` | command → `TicketSyncService` → group `user:{id}` → `TicketUpdated` | `TicketHub.cs`، `use-ticket-hub.js` | درس `13-signalr.md` |
| وضعیت گیت | `IHubContext<GateConnectionStatusHub>` | `Clients.All.SendAsync("ReceiveGateStatus")`؛ کلاینت gate listen می‌کند | `EventHandelerCommands` / `GateStatusCheckerService`، `gate.service.js` | درس `13-signalr.md` (پروکسی Nginx باز) |
| رویداد ZK تا ACL | gRPC stream | `ZKGrpcServer` → `SubscribeToEvents` → `ZKGrpcClientWrapper` → `ZKStartupService` → MediatR/SignalR | `zk_service.proto`، `ZKGrpcClientWrapper`، `ZKStartupService` | درس `14-grpc-devices.md` و `13-signalr.md` |
| sync کاربر Tiam | unary gRPC | strategy چک `OnlineTerminals` سپس `SendUserToDeviceAsync` | `TiamDeviceSyncStrategy`، `TiamGrpcClientWrapper` | درس `14-grpc-devices.md` |
| جانشینی گام تیکت | Hangfire recurring | cron هر ۵ دقیقه → `StepSubstitutionSweeper.ProcessDueAsync` → `ISubstitutionOpenTaskService` | `Program.cs` RequestTracker، `StepSubstitutionSweeper.cs` | درس `15-hangfire.md` |
| sync کاربران دستگاه | Hangfire enqueue | API/consumer → `DeviceSyncService` → `devices_queue` → strategy gRPC → SignalR | `DeviceSyncService.cs`، handlers/consumers ACL | درس `15-hangfire.md`، `14-grpc-devices.md` |
| آپلود سند پرسنل | HTTP به DCC | handler → `DccHttpClient.UploadFileAsync` → `FileService` → `IFileStorage.SaveAsync` → `Files` + `PersonnelDocument` | `UploadPersonnelDocumentCommandHandler`، `FileService`، `S3FileStorage`/`LocalFileStorage` | درس `16-dcc-s3.md` |
| دانلود با presign | DCC سپس MinIO | auth روی DCC → `CreateGetUrlAsync` → کلاینت مستقیم به PublicEndpoint | `GetPresignedDownloadUrlQueryHandler`، `GetPersonnelDocumentDownloadUrlQueryHandler` | درس `16-dcc-s3.md` |
| فایل عمومی لبه | YARP `/files` | transform به `Files/public` روی DCC → `OpenReadAsync` فقط `public/` | gateway PublicFiles، `FilesController.GetPublicFile` | درس `16-dcc-s3.md`، `04-yarp.md` |
| Logout تا 401 | Redis/HybridCache | `RevokeAsync(access)` → `UseTokenRevoke` روی gateway/هویت → `IsRevokedAsync` | `LogoutCommandHandler`، `TokenBlackListService`، `TokenRevokeMiddleware` | درس `19-redis.md`، `05-jwt-identity.md` |
| claim سایت از سرویس دیگر | HybridCache + bus | `RemoteClaimService.GetOrCreateAsync(userId)` → `GetUserSiteClaims`؛ invalidate با `UserSiteClaimsCache` | `RemoteClaimService.cs`، `UserSiteClaimsCache.cs` | درس `19-redis.md` |
| درخواست دژبان + مشاهده‌پذیری | Serilog / OTEL / health | ExceptionHandler → LogContext TraceId → SerilogRequestLogging → auth/tenant/endpoint؛ OTEL AspNetCore span؛ health جدا | `Dejban.Api/Program.cs`، `InfrastructureConfiguration` | درس `20-observability.md` |
| فشار API روی لبه | in-process metrics | `/api/*` → `RequestMetricsMiddleware` → `RequestMetricsStore`؛ خواندن با `/api/v1/gateway/request-metrics` | gateway Middleware + `Program.cs` | درس `20-observability.md`، `04-yarp.md` |
| آماده‌سازی DR primary | اسکریپت روی Server 1 | primaryهای Compose در حال اجرا → `prepare-primary.sh` → نقش/slot/pg_hba | `infrastructure/postgres-dr/scripts/prepare-primary.sh` | درس `21-postgres-dr.md` |
| بالا آوردن standby | Compose DR Server 2 | `standby-entrypoint` → `pg_basebackup` → streaming WAL | `docker-compose.standby.yml`، `standby-entrypoint.sh` | درس `21-postgres-dr.md` |
| failover دستی | promote + config اپ | `promote.sh` → تغییر Host در `appsettings.Docker.json` / env | `promote.sh`، جدول README | درس `21-postgres-dr.md` |
| build محلی فرانت | Turborepo | `npm run build` → `turbo run build` → script `build` هر workspace دارای آن | `dejban_frontend_new/package.json`، `turbo.json`، `apps/*/package.json` | درس `22-turborepo.md` |
| deploy CI فرانت | سرور + pm2 | push `master` → SSH → `npm ci` → `turbo run build --concurrency=1` → `pm2 … npm -- start` | `.gitlab-ci.yml` | درس `22-turborepo.md` |
| image تک‌اپ Next | Docker filter | `Dockerfile.next` → `turbo run build --filter=${APP_NAME}` → کپی `.next/standalone` | `docker/Dockerfile.next`، `docker-compose.yml` | درس `22-turborepo.md` |
| shell Next تا کلاینت | RootLayout → ClientInit | `async` layout سرور → `ConfigRegistry.set` + Auth/Query providers | `apps/*/src/app/layout.jsx`، `client-init.jsx` | درس `23-nextjs.md` |
| داشبورد محافظت‌شده | AuthGuard | `dashboard/layout` کلاینت → بدون session `window.location` به sign-in | `apps/dejban/src/app/dashboard/layout.jsx`، `auth-guard.jsx` | درس `23-nextjs.md` |
| صفحه staff تا Axios | PageGuard → RQ | `staff/page` → `StaffListView` → `useGetStaffWithPagination` → `apiClient` | staff page/view/service، `axiosInstance.ts` | درس `23-nextjs.md`، `00-personnel-list-execution-path.md` |
| Vite SPA bootstrap | HTML → Router | `index.html` → `main.jsx` → `ConfigRegistry` + `RouterProvider` basename `/access-control` | `apps/access-control/index.html`، `src/main.jsx` | درس `24-vite-access-control.md` |
| داشبورد ACL محافظت‌شده | AuthGuard | `dashboardRoutes` path `/` → `AuthGuard` → `DashboardLayout` + lazy outlet | `routes/sections/dashboard.jsx` | درس `24-vite-access-control.md` |
| Access Group list تا API | SWR → Axios | `AccessGroupListView` → `useGetAccessGroups` → `fetcher` → `/accessgroups/getaccessgroups` | `access-group-list-view.jsx`، `actions/access-group.js`، `lib/api.js` | درس `24-vite-access-control.md` |
| Login تا token + session | action → getMe | `signInWithPassword` → `tokenStorage.setAccess` → `checkUserSession` → `GET /auth/getme` | `action.js`، `AuthContext.tsx`، main `JwtSignInView` | درس `25-api-client-auth.md`، `00-login-execution-path.md` |
| 401 تا refresh/retry | Axios interceptor | 401 → `POST /auth/refresh` (cookie) → `setAccess` → retry؛ یا clear + redirect sign-in | `axiosInstance.ts` | درس `25-api-client-auth.md` |
| درخواست + سایت | request interceptor | Bearer از localStorage؛ `X-Site-Id` از `useSiteStore` | `axiosInstance.ts`، `site-storage.js` | درس `25-api-client-auth.md` |
| عوض سایت تا خالی شدن RQ | ClientProvider | `useSiteStore.subscribe` → `cancelQueries` + `resetQueries` | `client-provider.jsx` | درس `26-client-state.md` |
| Staff mutation تا refetch | invalidate | `useSoftDeleteStaff`/`useCreateStaff` → `invalidateQueries(staffKeys.all)` | `staff.service.js`، `staff.keys.js` | درس `26-client-state.md` |
| Access Group SWR refresh | mutate دستی | delete/page → `localMutate()` روی SWR key لیست | `access-group-list-view.jsx`، `actions/access-group.js` | درس `26-client-state.md` |
| API Key list Zustand | store action | `getAPIKeys` → `allAPIKeys` در store → جدول UI | `api-key-actions-store.js`، `api-key-list-view.jsx` | درس `26-client-state.md` |
| Bootstrap UI Next | layout providers | `detectLanguage` → I18n → Settings → Localization → Theme+Rtl | `apps/dejban/src/app/layout.jsx`، theme/locales packages | درس `27-mui-i18n.md` |
| تعویض زبان هدر | LanguagePopover | `onChangeLang` → i18n + `settings.direction` + dayjs + `document.dir`/Rtl | `language-popover.jsx`، `use-locales.js`، `right-to-left.jsx` | درس `27-mui-i18n.md` |
| تاریخ فارسی در picker | LocalizationProvider | fa-IR → `AdapterMomentJalaali`؛ en → `AdapterDayjs` | `localization-provider.jsx` | درس `27-mui-i18n.md` |
| مرورگر تا API از لبه | Nginx → gateway | `/api/v1/...` → `location /api/` → `https://${API_GATEWAY}` → YARP | `default.conf.template`، Compose `API_GATEWAY` | درس `28-nginx-edge.md`، `00-api-path-case-investigation.md` |
| مرورگر تا اپ dejban | Nginx → Next | `/dejban/` → `frontend_dejban:3000` | `default.conf.template` upstream | درس `28-nginx-edge.md`، `23-nextjs.md` |
| ACL SPA از لبه | دو لایه nginx | لبه `/access-control/` → کانتینر ACL؛ داخل `try_files` → `index.html` | `default.conf.template`، `access-control.conf` | درس `28-nginx-edge.md`، `24-vite-access-control.md` |
| SignalR از لبه | regex hubs | مثلاً `/timeserverhub` → gateway؛ `gateStatusHub` در regex نیست | `default.conf.template` | درس `28-nginx-edge.md`، `13-signalr.md` |
| `GetPatrolReport` | `PatrolReportService` | EF برای board/event؛ Dapper برای blacklist روی `visitors` و `personnels` | `GetPatrolReportQueryHandler.cs`، `PatrolReportService.cs` | درس `10-dapper.md` |
| Domain handler تا Rabbit | `IEventBus` / MassTransit | `PersonnelCreatedDomainEventHandler` → `EventBus.PublishAsync` → `IBus.Publish` + tenant publish filter | `PersonnelCreatedDomainEventHandler.cs`، `EventBus.cs`، `InfrastructureConfiguration` | درس `11-messaging.md` |
| Rabbit تا Visitors replica | inbox + Quartz | `IntegrationEventConsumer<PersonnelCreated>` → `visitors.inbox_messages` → `ProcessInboxJob` → `PersonnelCreatedIntegrationEventHandler` | `VisitorsModule.ConfigureConsumers`، consumer/handler Visitors | درس `11-messaging.md` |
| Rabbit تا کاربر هویت | `PersonnelCreatedConsumer` | `IConsumer<PersonnelCreated>` مستقیم؛ ساخت `ApplicationUser` | `IdentityServer/.../PersonnelCreatedConsumer.cs` | درس `11-messaging.md` |
| SiteCreated هویت تا Personnels | inbox پرسنل | `IPublishEndpoint.Publish(SiteCreated)` + Bus Outbox → `IntegrationEventConsumer` → `SiteCreatedIntegrationEventHandler` | `CreateSiteCommandHandler`، Personnels inbox/handler | درس `11-messaging.md` |
| ایجاد پرسنل تا Visitors | bus | `PersonnelCreatedDomainEvent` → outbox → `PersonnelCreatedDomainEventHandler` → `IEventBus.PublishAsync(PersonnelCreated)` → `PersonnelCreatedIntegrationEventHandler` | `InsertOutboxMessagesInterceptor`، handlerهای Personnels و Visitors | درس `07-modular-monolith.md` و `08-cqrs-mediatr.md` |
| `CreatePersonnel` endpoint | `CreatePersonnelCommandHandler` | `ISender.Send` و pipeline با `IBaseCommand`؛ بعد `SaveChanges` و outbox | `CreatePersonnel.cs`، `CreatePersonnelCommand.cs`، behaviors در `ApplicationConfiguration` | درس `08-cqrs-mediatr.md` |
| ایجاد سایت هویت تا Personnels | bus | `CreateSiteCommandHandler` با `Publish(SiteCreated)` → `SiteCreatedIntegrationEventHandler` در Personnels | `IdentityServer/.../CreateSiteCommandHandler.cs`، `Personnels/.../SiteCreatedIntegrationEventHandler.cs` | همان |
| Unit blacklist Visitors | `BlackListSchedule.IsActiveDuring` | `[Fact]` → `Compile()` Expression → FluentAssertions؛ بدون DB | `BlackListScheduleTests.cs`، `BlackListSchedule.cs` | درس `31-testing.md` |
| Architecture لایه Visitors | NetArchTest | `Types.InAssembly` → `NotHaveDependencyOn` → `ShouldBeSuccessful` | `LayerTests.cs`، `TestResultExtensions.cs` | درس `31-testing.md`، `07-modular-monolith.md` |
| Integration CreateVisitor (validation) | host + containers | collection fixture → Postgres/Redis Start → `ISender.Send` → ErrorOr Validation | `IntegrationTestWebAppFactory.cs`، `CreateVisitorTests.cs` | درس `31-testing.md`، `08-cqrs-mediatr.md` |
| اسکریپت E2E فرانت | Playwright | `npm run test:e2e` → `turbo run test:e2e` → `playwright test` (workspaceهایی که script دارند) | ریشه `package.json`، `turbo.json`، `apps/main|dejban/package.json` | درس `31-testing.md`، `22-turborepo.md` |
| CI فرانت (بدون تست) | build فقط | push `master` → SSH → `npm ci` → `turbo run build` → pm2؛ گام test نیست | `.gitlab-ci.yml` | درس `31-testing.md`، `22-turborepo.md` |

کاتالوگ فناوری در `00-learning-catalog.md` به همین جدول ارجاع می‌دهد. درس‌های 01، 04، و 30 جای این جدول را نمی‌گیرند. مسیرهای تست بالا از روی پیکربندی/سورس‌اند؛ runner در فاز AD اجرا نشد.
