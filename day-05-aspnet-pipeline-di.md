# Day 05 — ASP.NET Core Pipeline + Dependency Injection

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Har HTTP request ke be server miad, az ye **pipeline** rad mishe — masalan CORS → logging → exception → auth → tenant → endpoint. In zanjire ra **middleware** misazad: har halqe mitone request ra process kone, `next()` seda bezane, ya short-circuit kone (401/429). Service-haei ke middleware va endpoint lazem daran ra **DI container** inject mikone ba se lifetime (Singleton / Scoped / Transient). In do ta — pipeline + DI — qalb-e ASP.NET Core-an; bedune fahm-e ina, feature-e badi hang midahad.

To Dejban in olgu to ~8 service tekrarme: Gateway rate-limit + TokenRevoke + JWT + YARP; Dejban.Api TenantContext + Minimal API `MapEndpoints`; module-ha ba `AddXxxModule` DI register mishan; MediatR behaviors mesle middleware-e command/query-an; Scrutor decorator baraye idempotent event handler. In fasl WORLD ra midahad, ba’d fargh-e pipeline-ha va smell-ha (mesle `UseTokenRevoke` nadashte-ye Dejban.Api) ra pin mikone.

---

# BAKHSH-E AVAL: WORLD — Pipeline + DI to donya

## Request Pipeline (Middleware)

### Middleware chie?

Middleware ye **zanjire** function-e: request az yeki rad mishe, kar-e khodesh ra mikone, ba’d `next` ra seda mizane; response ham az haman zanjire bargasht mikone. Yani mitoni «ghabl» va «ba'd» az endpoint logic dashte bashi bedune inke hame chiz ra to controller/endpoint tekraar koni.

```
Request  →  CORS  →  Logging  →  Auth  →  Endpoint  →  Response
             ↓          ↓          ↓          ↓
          next()     next()     next()     result
             ↑          ↑          ↑          ↑
          Response   Response   Response   Response
```

**Har middleware:**
1. Request ra process mikone (ya skip)
2. `next()` ra seda mizane (ya short-circuit)
3. Response ra process mikone (ya ignore)

### Tartib MOHEM-e!

Pipeline order = register order. `app.UseX()` ghabl az `app.UseY()` yani X aval run mishe — va in tartib bug-zastarin ghesmat-e ASP.NET-e.

```csharp
// DOROST:
app.UseAuthentication();    // aval: "ki hasti?"
app.UseAuthorization();     // bad: "ejaze dari?"

// GHALAT:
app.UseAuthorization();     // ki hasti ra nadone, ejaze check nemitone!
app.UseAuthentication();
```

### Official recommended order (.NET 10)

```csharp
app.UseExceptionHandler();       // 1. catch hame-ye exception
app.UseHsts();                   // 2. HTTPS header
app.UseHttpsRedirection();       // 3. HTTP → HTTPS
app.UseStaticFiles();            // 4. serve wwwroot (short-circuit)
app.UseRouting();                // 5. match route
app.UseCors();                   // 6. CORS headers
app.UseAuthentication();         // 7. parse JWT / cookie
app.UseAuthorization();          // 8. check policy
app.UseRateLimiter();            // 9. throttle
app.UseOutputCache();            // 10. cache response
// endpoint middleware (custom)
app.MapControllers();            // 11. execute endpoint
app.MapMinimalApis();
```

### Short-circuit

Age middleware `next()` ra seda **nazane**, pipeline injast tamum mishe. Mesal:

- **Auth middleware:** token invalid → 401 return, `next()` seda nazade
- **Rate limiter:** limit exceeded → 429 return
- **Static files:** file peida shod → serve, `next()` seda nazade
- **CORS preflight:** OPTIONS request → 204, `next()` seda nazade

### 3 rah baraye neveshtan-e middleware

**1. Inline (lambda):**
```csharp
app.Use(async (context, next) => {
    // before
    await next();
    // after
});
```

**2. Convention-based (class):**
```csharp
public class MyMiddleware
{
    private readonly RequestDelegate _next;
    public MyMiddleware(RequestDelegate next) => _next = next;

    public async Task InvokeAsync(HttpContext context, ILogger<MyMiddleware> logger)
    {
        logger.LogInformation("Before");
        await _next(context);
        logger.LogInformation("After");
    }
}
// register:
app.UseMiddleware<MyMiddleware>();
```

- Constructor: `RequestDelegate` + singleton service-ha
- `InvokeAsync`: har request seda mishe. Parameter-ha DI resolve mishan (scoped ok)
- Lifetime: **singleton** (yek instance kol-e app). State share nakonid!

**3. IMiddleware (factory-activated):**
```csharp
public class MyMiddleware : IMiddleware
{
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        // ...
        await next(context);
    }
}
// register:
services.AddSingleton<MyMiddleware>();  // ya Scoped/Transient
app.UseMiddleware<MyMiddleware>();
```

- DI-registered → lifetime ra khodet control mikoni
- Scoped dependency mitooni inject koni (convention-based namitooni to constructor)

---

## Dependency Injection (DI)

### DI chie?

Class-e A be interface-e B niaz dare. **Bedune DI:** A khodesh `new B()` misaze → tight coupling, test sakht. **Ba DI:** container B ra misaze va be A mide → DIP + testability. ASP.NET Core DI built-in dare; Lifetime ra dorost entekhab nakoni, captive dependency ya disposed DbContext midari.

```csharp
// ❌ Tight coupling:
public class OrderService {
    private readonly EmailSender _sender = new EmailSender(); // hard dependency
}

// ✅ DI:
public class OrderService {
    private readonly IEmailSender _sender;
    public OrderService(IEmailSender sender) => _sender = sender; // injected
}
```

## 3 Lifetime

Se lifetime-e asli — entekhab-e ghalat = bug-e production (captive dependency, stale DbContext, ya allocation-e bihude):

| lifetime | mesal | kei |
|---|---|---|
| **Singleton** | `AddSingleton<T>()` | 1 instance kol-e app. Config, cache, connection pool |
| **Scoped** | `AddScoped<T>()` | 1 instance per request (per scope). DbContext, UnitOfWork |
| **Transient** | `AddTransient<T>()` | har bar new instance. Stateless, lightweight |

### Captive dependency problem

```csharp
services.AddSingleton<CacheService>();      // lives forever
services.AddScoped<DbContext>();             // lives per-request

public class CacheService(DbContext db) { } // ❌ DbContext captured!
```

**Singleton hold mikone scoped ra** → DbContext-e yek request-e ghadimi, request-e ba'di ham haman ra estefade mikone → data corruption, disposed DbContext.

**Fix:** `IServiceScopeFactory` to singleton, har bar scope besaz:

```csharp
public class CacheService(IServiceScopeFactory scopeFactory)
{
    public async Task DoWork()
    {
        using var scope = scopeFactory.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<DbContext>();
        // fresh DbContext per call
    }
}
```

### Register styles

```csharp
// Interface → Implementation
services.AddScoped<IOrderRepo, OrderRepo>();

// Self-registration
services.AddSingleton<CacheService>();

// Factory delegate
services.AddSingleton<ITokenBlackList>(sp => {
    var cache = sp.GetRequiredService<HybridCache>();
    return new TokenBlackListService(cache, TimeSpan.FromMinutes(15));
});

// TryAdd — faghat age ghablan register nashode
services.TryAddScoped<ITenantContext, TenantContext>();

// Multiple implementations
services.AddScoped<IValidator, NameValidator>();
services.AddScoped<IValidator, EmailValidator>();
// inject: IEnumerable<IValidator> → hame-ye registrations

// Options binding
services.Configure<JwtSettings>(config.GetSection("JwtSettings"));

// Open generic
services.AddTransient(typeof(IRepository<>), typeof(Repository<>));
```

### `TryAdd` vs `Add`

- `Add` → hamishe ezafe mikone (duplicate ok)
- `TryAdd` → faghat age ghablan **haman interface** register nashode

Module-ha `TryAdd` estefade mikonan baraye shared service-ha ke chand module register mikonan. Aval register mishe, baghie skip.

### Keyed services (.NET 8+)

```csharp
services.AddKeyedSingleton<IStorage, S3Storage>("s3");
services.AddKeyedSingleton<IStorage, LocalStorage>("local");

// inject:
public class FileService([FromKeyedServices("s3")] IStorage storage) { }
```

Baraye strategy pattern bedune factory. Dejban in ra **estefade nakarde** — factory/Options estefade karde.

---

## Extension method pattern baraye DI

Hame-ye registration-ha ra to **extension method** organize kon. Clean, re-usable, testable.

```csharp
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration config)
    {
        services.AddDbContext<AppDbContext>(...);
        services.AddScoped<IUnitOfWork, UnitOfWork>();
        services.Configure<SmtpSettings>(config.GetSection("Smtp"));
        return services;
    }

    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(ServiceCollectionExtensions).Assembly));
        return services;
    }
}

// Program.cs — clean:
builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration)
    .AddPresentation(builder.Configuration);
```

---

## MediatR Pipeline Behaviors

MediatR khodesh ye pipeline dare — mesle middleware vali baraye **command/query**.

```
Request → Behavior1 → Behavior2 → Behavior3 → Handler → Response
```

```csharp
public class ValidationBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
{
    private readonly IEnumerable<IValidator<TRequest>> _validators;

    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        // BEFORE handler
        var failures = _validators.Select(v => v.Validate(request)).SelectMany(r => r.Errors);
        if (failures.Any()) return /* error */;

        // CALL handler
        var response = await next();

        // AFTER handler (optional)
        return response;
    }
}
```

Register:
```csharp
cfg.AddOpenBehavior(typeof(ExceptionHandlingBehavior<,>));  // 1st = outermost
cfg.AddOpenBehavior(typeof(LoggingBehavior<,>));             // 2nd
cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));          // 3rd = closest to handler
```

**Tartib = register order:** aval register = aval run (outermost ring).

---

## Endpoint Filters (Minimal API)

Mesle action filter vali baraye minimal API. Chain mishe roye endpoint.

```csharp
app.MapGet("/orders", GetOrders)
    .AddEndpointFilter<AuthFilter>()
    .AddEndpointFilter<RateLimitFilter>();
```

```csharp
public class AuthFilter : IEndpointFilter
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        // before
        if (!context.HttpContext.User.Identity!.IsAuthenticated)
            return Results.Unauthorized();

        return await next(context);  // call handler
    }
}
```

### Endpoint filter vs Middleware

| | Middleware | Endpoint Filter |
|---|---|---|
| scope | **hame-ye** request-ha | **yek** endpoint ya group |
| register | `app.UseMiddleware<T>()` | `.AddEndpointFilter<T>()` |
| access | HttpContext | HttpContext + arguments |
| order | pipeline-wide | per-endpoint chain |
| use case | auth, CORS, logging | permission check, validation |

---

## Background Services

`IHostedService` ya `BackgroundService` baraye long-running task-ha ke ba HTTP request rabti nadaran.

```csharp
public class CleanupService : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            await DoCleanup();
            await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
        }
    }
}
// register:
services.AddHostedService<CleanupService>();
```

**Mohem:** `BackgroundService` singleton-e. Scoped dependency lazem? → `IServiceScopeFactory`.

---

## Options Pattern

Configuration ra strongly-typed bekhun, na magic string.

```json
// appsettings.json
{
    "Jwt": {
        "Secret": "...",
        "ExpirationMinutes": 15
    }
}
```

```csharp
public class JwtOptions
{
    public string Secret { get; set; } = "";
    public int ExpirationMinutes { get; set; }
}

// register:
services.Configure<JwtOptions>(config.GetSection("Jwt"));

// inject:
public class TokenService(IOptions<JwtOptions> options)
{
    var secret = options.Value.Secret;  // strongly typed!
}
```

| interface | lifetime | reload? |
|---|---|---|
| `IOptions<T>` | singleton | ❌ start value |
| `IOptionsSnapshot<T>` | scoped | ✅ per-request |
| `IOptionsMonitor<T>` | singleton | ✅ change callback |

### `IConfigureOptions<T>` — code-based config

```csharp
public class ConfigureQuartzJobs : IConfigureOptions<QuartzOptions>
{
    public void Configure(QuartzOptions options) =>
        options.AddJob<ProcessInboxJob>(...);
}
services.ConfigureOptions<ConfigureQuartzJobs>();
```

Baraye vaghti config compile-time ya logic lazem dare (na JSON).

---

## HttpContext patterns

### `IHttpContextAccessor`

Singleton-e ke `HttpContext`-e current ra mide. Scoped nabud, vali `AsyncLocal<T>` dare.

```csharp
services.AddHttpContextAccessor();

public class CurrentUserService(IHttpContextAccessor accessor)
{
    public Guid UserId => Guid.Parse(accessor.HttpContext!.User.FindFirst("sub")!.Value);
}
```

**Khatarnak to background service** — HttpContext null-e! Faghat to request pipeline estefade kon.

### `HttpContext.Items`

Per-request dictionary. Baraye pass-e data beyn-e middleware va endpoint bedune DI.

```csharp
// Middleware:
context.Items["Agent"] = agent;
// Endpoint:
var agent = (Agent)context.Items["Agent"]!;
```

**Na strongly-typed.** Behtar: custom service ya `AsyncLocal<T>`.

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **`IOptionsSnapshot<T>`** — per-request config reload. Dejban faghat `IOptions<T>` dare.
- **`IOptionsMonitor<T>`** — live change callback. Dejban estefade nakarde.
- **Keyed services** — .NET 8. Dejban nadare (factory estefade karde).
- **`ActivatorUtilities`** — manual DI-aware construction. Dejban nadare.
- **`HttpContext.Features`** — advanced request features. Dejban nadare.
- **Scrutor `services.Scan()`** — assembly scanning baraye auto-register. Dejban nadare (manual register).
- **Health check UI** — dashboard baraye health. Dejban basic `MapHealthChecks` dare.
- **Middleware branching** — `app.Map("/api", ...)`, `app.UseWhen(...)`. Limited to Dejban.
- **Output caching middleware** (.NET 7+) — Dejban Gateway dare, microservice-ha nadaran.

---

# BAKHSH-E DOVOM: DEJBAN — Pipeline + DI to in proje

In bakhsh neshan mide hamin pipeline/DI koja pin shodan — va koja inconsistent-an. Aval overview-e 8 service, ba’d middleware-haye custom.

## Pipeline-ye 8 service

### Common pattern (6 ta microservice)

IdentityServer, ACLServer, DCC, RequestTracker, GateServer, Reporting hame in rah ra miran (ba fargh-haye koochik):

```
CORS → DbInit → OpenAPI(dev) → Serilog → ExceptionHandler → StatusCodePages
→ Localization → TokenRevoke → Authentication → Authorization → TenantContext
→ [optional: Hangfire, SignalR hubs] → MapControllers
```

### ApiGateway — farghi

```
HttpsRedirection(conditional) → CORS → Scalar(dev) → StaticFiles → RateLimiter
→ AccessTokenQueryMiddleware → TokenRevoke → Authentication → Authorization
→ OutputCache → HealthCheck → MapReverseProxy
```

**Fargh-ha:**
- `RateLimiter` ghabl az auth → rate limit anonymous ham
- `OutputCache` ba'd az auth → cache per-user
- `MapReverseProxy` ja-ye `MapControllers` → YARP

### Dejban.Api — modular monolith

```
CORS → Migrations/Seed/MediaMTX → OpenAPI(dev) → HealthChecks
→ ExceptionHandler → LogContext(TraceId) → Serilog → Authentication
→ Authorization → TenantContext → MapEndpoints(minimal API)
```

**Fargh-ha:**
- `UseLogContext()` — custom middleware baraye TraceId push be Serilog
- `MapEndpoints()` — minimal API (na controller)
- **Na `UseTokenRevoke()`** — in middleware register shode vali `UseTokenRevoke()` to pipeline nist!

### Reporting — unique

```
ExceptionHandler → StatusCodePages → StaticFiles → Serilog → Localization
→ CORS → Routing → DbInit → OpenAPI(dev) → AccessTokenQueryMiddleware
→ TokenRevoke → Authentication → Authorization → TenantContext → MapControllers
```

**Fargh:** `ExceptionHandler` **aval** (baghie services CORS aval). `UseRouting()` explicit. StimulSoft report viewer needs `StaticFiles` + `AccessTokenQueryMiddleware`.

---

## Custom middleware-ha

### TokenRevokeMiddleware — IMiddleware

```csharp
// File: Common/Caching/TokenRevokeMiddleware.cs

public sealed class TokenRevokeMiddleware(
    ITokenBlackList tokenBlackList,
    Func<HttpContext, string?> tokenSelector) : IMiddleware
{
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        var token = tokenSelector(context);
        if (token == null) { await next(context); return; }

        if (!await tokenBlackList.IsRevokedAsync(token))
        {
            await next(context);
            return;
        }

        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        // short-circuit — next() seda nazade
    }
}
```

Register:

```csharp
// AddTokenRevokeMiddleware():
services.AddSingleton(provider =>
{
    var tokenBlackList = provider.GetRequiredService<ITokenBlackList>();
    return new TokenRevokeMiddleware(tokenBlackList, bearerTokenSelector);
});

// UseTokenRevoke():
app.UseMiddleware<TokenRevokeMiddleware>();
```

**Chera IMiddleware?** Chon factory delegate ba `Func<HttpContext, string?>` lazem bud. Convention-based nemishod parametric singleton besazand.

**Smell: Dejban.Api `UseTokenRevoke()` nadare!** Token revoke faghat Gateway-e. Age kasi direct be Dejban.Api request bezane → revoked token ghabul mishe.

### AccessTokenQueryMiddleware — convention-based

```csharp
// File: Common/Authentication/AccessTokenQueryMiddleware.cs

public sealed class AccessTokenQueryMiddleware(RequestDelegate next)
{
    public async Task InvokeAsync(HttpContext context)
    {
        await ApplyFromQueryAsync(context, context.Request.Query);
        // fallback: parse Referer URL for StimulSoft window.open
        await next(context);
    }
}
```

`access_token` az query string ya Referer ra be header copy mikone. Baraye SignalR WebSocket va StimulSoft report viewer.

### TenantContextMiddleware — AsyncLocal

```csharp
// File: Common/Tenancy/TenantContextMiddleware.cs

public async Task InvokeAsync(HttpContext context)
{
    // Parse X-Site-Id header + JWT claims → effective site IDs
    TenantContextAccessor.SetContext(effectiveSiteIds, isSuperAdmin);
    await _next(context);
    TenantContextAccessor.Clear();  // cleanup
}
```

`TenantContextAccessor` az `AsyncLocal<T>` estefade mikone — na `HttpContext.Items`. In baraye background job-ha ham kar mikone (async flow maintain mishe).

### LogContextTraceLoggingMiddleware — Serilog enrichment

```csharp
// File: Dejban.Api/Middleware/LogContextTraceLoggingMiddleware.cs

internal sealed class LogContextTraceLoggingMiddleware(RequestDelegate next)
{
    public async Task Invoke(HttpContext context)
    {
        using (LogContext.PushProperty("TraceId", Activity.Current?.TraceId.ToString()))
            await next.Invoke(context);
    }
}
```

Har log message to in scope `TraceId` dare → distributed tracing correlation.

---

## DI architecture — 3-layer pattern

Har service 3 ta extension method dare:

```csharp
// Program.cs:
builder.Services
    .AddPresentation(builder.Configuration)   // controllers, CORS, OpenAPI, JSON
    .AddApplication()                          // MediatR, validators, behaviors
    .AddInfrastructure(builder.Configuration); // DbContext, repos, MassTransit, cache
```

**Clean Architecture dependency rule:** Presentation → Application → Infrastructure. DI hame ra wire mikone.

### AddPresentation — example

```csharp
public static IServiceCollection AddPresentation(this IServiceCollection services, IConfiguration config)
{
    services.AddControllers();              // ya AddEndpoints baraye minimal API
    services.AddDefaultCors(config);        // CORS policy
    services.AddOpenApi();                  // Scalar/Swagger
    services.AddCustomJwtAuth(config);      // JWT Bearer
    services.AddCacheServices(redis);       // HybridCache + Redis
    services.AddTokenRevokeMiddleware();    // token blacklist
    services.AddHttpContextAccessor();
    services.AddSignalR();
    return services;
}
```

### AddApplication — example

```csharp
public static IServiceCollection AddApplication(this IServiceCollection services)
{
    services.AddMediatR(config =>
    {
        config.RegisterServicesFromAssembly(typeof(ServiceCollectionExtensions).Assembly);
        config.AddOpenBehavior(typeof(ValidationBehavior<,>));
    });
    services.AddValidatorsFromAssembly(typeof(ServiceCollectionExtensions).Assembly);
    TypeAdapterConfig.GlobalSettings.Scan(Assembly.GetExecutingAssembly()); // Mapster
    return services;
}
```

### AddInfrastructure — example

```csharp
public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration config)
{
    services.AddDbContext<ApplicationDbContext>((sp, options) =>
        options.UseNpgsql(config.GetConnectionString("Postgres")));
    services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<ApplicationDbContext>());
    services.AddMassTransit(x => { /* consumers, outbox */ });
    services.Configure<OutboxOptions>(config.GetSection("Outbox"));
    return services;
}
```

---

## Dejban modular DI — AddXxxModule

Dejban.Api (modular monolith) har module ra joda register mikone:

```csharp
// File: Dejban.Api/Program.cs

builder.Services
    .AddApplication(assemblies)
    .AddInfrastructure(builder.Configuration, assemblies)
    .AddPresentation(builder.Configuration)
    .AddVisitorsModule(builder.Configuration)
    .AddPersonnelsModule(builder.Configuration)
    .AddVehiclesModule(builder.Configuration)
    .AddSecurityPatrolsModule(builder.Configuration)
    .AddArmoryModule(builder.Configuration)
    .AddCashLogisticsModule(builder.Configuration)
    .AddInventoryModule(builder.Configuration)
    .AddWeighBridgeModule(builder.Configuration);
```

Har `AddXxxModule` chi mikone:

```csharp
// File: Visitors.Infrastructure/VisitorsModule.cs

public static IServiceCollection AddVisitorsModule(this IServiceCollection services, IConfiguration config)
{
    // 1. DbContext
    services.AddDbContext<VisitorsDbContext>((sp, options) =>
        options.UseNpgsql(...)
            .AddInterceptors(sp.GetRequiredService<InsertOutboxMessagesInterceptor>()));

    // 2. Unit of Work (DbContext khodesh)
    services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<VisitorsDbContext>());

    // 3. Repositories (15+ ta)
    services.AddScoped<IVisitorRepository, VisitorRepository>();
    services.AddScoped<IVisitScheduleRepository, VisitScheduleRepository>();
    // ...

    // 4. Channel (SSE notifications)
    var channel = Channel.CreateUnbounded<VisitorNotification>();
    services.AddSingleton(channel);
    services.AddSingleton(channel.Reader);
    services.AddSingleton(channel.Writer);

    // 5. Domain event handlers + Scrutor decorator
    services.TryAddScoped(domainEventHandler);
    services.Decorate(domainEventHandler, closedIdempotentHandler);

    // 6. Quartz inbox/outbox jobs
    services.ConfigureOptions<ConfigureProcessInboxJob>();
    services.ConfigureOptions<ConfigureProcessOutboxJob>();

    // 7. Options
    services.Configure<OutboxOptions>(config.GetSection("Visitors:Outbox"));
    services.Configure<InboxOptions>(config.GetSection("Visitors:Inbox"));

    return services;
}
```

**TryAddScoped baraye shared service-ha:** `ITenantContext`, `IDateTimeProvider`, `IEventBus`, `IDbConnectionFactory` — aval register-konande migire, baghie skip.

---

## Scrutor Decorator — idempotent handler

Scrutor faghat baraye `Decorate<>()` estefade shode (na `Scan()`).

```csharp
// Register original handler:
services.TryAddScoped<IDomainEventHandler<VisitorCreatedEvent>, VisitorCreatedEventHandler>();

// Wrap with decorator:
Type closedIdempotent = typeof(IdempotentDomainEventHandler<>).MakeGenericType(typeof(VisitorCreatedEvent));
services.Decorate(typeof(IDomainEventHandler<VisitorCreatedEvent>), closedIdempotent);
```

Natije: vaghti `IDomainEventHandler<VisitorCreatedEvent>` resolve mishe → `IdempotentDomainEventHandler<VisitorCreatedEvent>` miad ke darunesh `VisitorCreatedEventHandler` dare.

```csharp
// File: Visitors.Infrastructure/Outbox/IdempotentDomainEventHandler.cs

internal sealed class IdempotentDomainEventHandler<TDomainEvent>(
    IDomainEventHandler<TDomainEvent> decorated,      // ← original handler
    IDbConnectionFactory dbConnectionFactory)
    : DomainEventHandler<TDomainEvent>
{
    public override async Task Handle(TDomainEvent domainEvent, CancellationToken ct)
    {
        if (await OutboxConsumerExistsAsync(...)) return;   // already processed → skip
        await decorated.Handle(domainEvent, ct);             // original logic
        await InsertOutboxConsumerAsync(...);                 // mark processed
    }
}
```

**Decorator chain:** resolve → Idempotent → check DB → (age new) → Original handler → insert consumed record.

---

## MediatR Pipeline Behaviors

### Dejban — 3 behavior (order matters!)

```csharp
// File: Dejban.Common.Application/ApplicationConfiguration.cs

config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));  // outermost
config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));          // closest to handler
```

**Flow:**

```
Command → ExceptionHandling → Logging → Validation → Handler → Response
                                                        ↑
                                                   validator.Validate()
                                                   fail? → return errors
```

### Microservice-ha — 1 behavior

ACLServer, DCC, IdentityServer, RequestTracker, Reporting:

```csharp
config.AddOpenBehavior(typeof(ValidationBehavior<,>));
```

Faghat validation. Na exception handling, na logging.

---

## Endpoint Filters — Dejban authorization

5 ta `IEndpointFilter` baraye minimal API authorization:

| filter | chi check mikone |
|---|---|
| `SiteAccessRequirementFilter` | X-Site-Id claim match |
| `EndpointAccessRequirementFilter` | endpoint access claim |
| `RoleRequirementFilter` | role per site |
| `PositionRequirementFilter` | position per site |
| `PermissionRequirementFilter` | permission per site |

```csharp
// File: Common/Authorization/AuthorizationExtensions.cs

public static RouteHandlerBuilder RequireSiteAccess(this RouteHandlerBuilder builder)
    => builder.AddEndpointFilter(new SiteAccessRequirementFilter());

public static RouteHandlerBuilder RequirePermissions(this RouteHandlerBuilder builder, params string[] permissions)
    => builder.AddEndpointFilter(new PermissionRequirementFilter(permissions));
```

Usage to endpoint:

```csharp
app.MapGet("/api/v1/visitors", GetVisitors)
    .RequireAuthorization()
    .RequireSiteAccess()
    .RequirePermissions("visitors/read");
```

**Moghayese ba action filter:** ACLServer az `IAsyncActionFilter` baraye `PlateReaderAgentAuthFilter` estefade karde chon controller-based-e. Dejban.Api minimal API-e → endpoint filter.

---

## Action Filter — PlateReaderAgentAuthFilter

```csharp
// File: ACLServer/Abstractions/Filters/PlateReaderAgentAuthFilter.cs

public async Task OnActionExecutionAsync(ActionExecutingContext context, ActionExecutionDelegate next)
{
    // 1. Extract API key from header
    // 2. Find agent in DB
    // 3. Check rate limit
    if (!rateLimiter.IsAllowed(agent.Id, options.Value.RateLimitPerMinute))
    {
        context.Result = new ObjectResult(...) { StatusCode = 429 };
        return;  // short-circuit
    }
    // 4. Set tenant context
    http.Items[AgentItemKey] = agent;
    TenantContextAccessor.SetContext([agent.SiteId], false);
    await next();
}
```

**HttpContext.Items** baraye pass-e agent be controller. Na DI — per-request Items dictionary.

---

## Background Services

| service | type | chi mikone |
|---|---|---|
| `PlateReaderNotifyHostedService` | BackgroundService | Channel reader → SignalR push |
| `EndpointSyncHostedService` | BackgroundService | Sync endpoint permissions to DB |
| `TimeBroadcastHostedService` | BackgroundService | Server time → SignalR every second |
| `GateListener` | BackgroundService | Socket connection to gate hardware |
| `GateLifecycleService` | BackgroundService | Gate reconnect/health check loop |
| `GateStatusCheckerService` | BackgroundService | Periodic gate status push |
| `ZK/Virdi/TiamStartupService` | IHostedService | Connect to device SDK on startup |

**Hame-ye ina `IServiceScopeFactory` estefade mikonan:**

```csharp
// PlateReaderNotifyHostedService
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    await foreach (var notification in _channelReader.ReadAllAsync(stoppingToken))
    {
        using var scope = _scopeFactory.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IPlateReaderAccessLogRepository>();
        // fresh scoped dependencies per iteration
    }
}
```

**Plus Quartz jobs** ke `IHostedService`-an vali az Quartz scheduler resolve mishan:

```csharp
services.AddQuartz();
services.AddQuartzHostedService(options => options.WaitForJobsToComplete = true);
services.ConfigureOptions<ConfigureProcessInboxJob>();
services.ConfigureOptions<ConfigureProcessOutboxJob>();
```

---

## Options pattern to Dejban

### Registration:

```csharp
// Module-level:
services.Configure<OutboxOptions>(config.GetSection("Visitors:Outbox"));
services.Configure<InboxOptions>(config.GetSection("Visitors:Inbox"));

// Global:
services.Configure<JwtSettings>(config.GetSection("JwtSettings"));
services.AddOptions<VehicleAccessOptions>().BindConfiguration("VehicleAccess");
```

### IConfigureOptions — Quartz scheduling:

```csharp
// File: Visitors.Infrastructure/Inbox/ConfigureProcessInboxJob.cs

internal sealed class ConfigureProcessInboxJob(IOptions<InboxOptions> inboxOptions)
    : IConfigureOptions<QuartzOptions>
{
    public void Configure(QuartzOptions options) =>
        options
            .AddJob<ProcessInboxJob>(configure => configure.WithIdentity(jobName))
            .AddTrigger(configure =>
                configure.ForJob(jobName)
                    .WithSimpleSchedule(schedule =>
                        schedule.WithIntervalInSeconds(_inboxOptions.IntervalInSeconds)
                                .RepeatForever()));
}
```

**Chera `IConfigureOptions`?** Chon Quartz scheduling be inbox interval-e dynamic niaz darin — az `InboxOptions` mikhone va Quartz ra configure mikone.

### Na estefade shode:

| | status |
|---|---|
| `IOptionsSnapshot<T>` | ❌ nist |
| `IOptionsMonitor<T>` | ❌ nist |
| `IOptionsFactory<T>` | ❌ nist |
| Named options | ❌ nist |
| Options validation | ❌ nist (`ValidateDataAnnotations`, `Validate`) |

**Smell:** options validation nist → bad config → runtime error. Behtar: `services.AddOptions<T>().BindConfiguration(...).ValidateDataAnnotations().ValidateOnStart()`.

---

## Factory pattern — IServiceScopeFactory + manual resolve

### DomainEventHandlersFactory — dynamic handler resolution

```csharp
// File: Dejban.Common.Infrastructure/Outbox/DomainEventHandlersFactory.cs

object domainEventHandler = serviceProvider.GetRequiredService(domainEventHandlerType);
```

Outbox processor domain event type ra mikhone, handler type ra az assembly peida mikone, DI resolve mikone. **Service locator pattern** — anti-pattern vali inja lazem-e chon type compile-time maloom nist.

### Endpoint discovery — IServiceProvider

```csharp
// File: Dejban.Common.Presentation/Endpoints/EndpointExtensions.cs

IEnumerable<IEndpoint> endpoints = app.Services.GetRequiredService<IEnumerable<IEndpoint>>();
foreach (var endpoint in endpoints)
    endpoint.MapEndpoint(app);
```

Hame-ye `IEndpoint` implementation-ha ra resolve mikone va map mikone. Assembly scanning + DI resolve.

### Optional dependency — GetService (nullable)

```csharp
// AccessTokenQueryMiddleware.cs
var store = context.RequestServices.GetService<IReportAccessTicketStore>();
// null age register nashode — graceful fallback
```

`GetService` vs `GetRequiredService`: aval null mide, dovom exception mizane.

---

## Smell-ha

1. **Dejban.Api `UseTokenRevoke()` nadare** — direct access = revoked token ghabul mishe
2. **Pipeline order inconsistent beyn-e service-ha** — Reporting ExceptionHandler aval, baghie CORS aval
3. **`IOptionsSnapshot`/`IOptionsMonitor` estefade nashode** — config change = restart lazem
4. **Options validation nist** — bad appsettings → runtime crash
5. **Keyed services estefade nashode** — factory pattern baraye strategy, keyed sade-tar bud
6. **Scrutor `Scan()` estefade nashode** — handler-ha manual register mishan (fragile)
7. **`HttpContext.Items` baraye agent pass** — na type-safe, magic string key
8. **Service locator to DomainEventHandlersFactory** — testability sakht
9. **Reporting 9 ta DbContext register mikone** — tight coupling be hame-ye module-ha
10. **`TryAddScoped` pattern baraye shared services** — first-register-wins, order-dependent

---

## 20 soal-e mosahebe

1. **Middleware pipeline tartib-esh chejori-e?** — register order. Auth ghabl az Authorization. Exception handler aval
2. **Middleware chejori short-circuit mikone?** — `next()` ra seda nazane → pipeline injast tamum
3. **Fargh-e convention-based va IMiddleware?** — convention singleton implicit, IMiddleware DI-registered lifetime control
4. **3 lifetime-e DI?** — Singleton (app), Scoped (request), Transient (per-resolve)
5. **Captive dependency chie?** — singleton hold-e scoped → stale data. Fix: IServiceScopeFactory
6. **TryAdd vs Add?** — TryAdd skip age ghablan register shode. Baraye shared services
7. **Options pattern chie?** — strongly-typed config bind. IOptions/IOptionsSnapshot/IOptionsMonitor
8. **Pipeline behavior chie?** — MediatR middleware. Validation, logging, exception handling
9. **Endpoint filter vs middleware?** — filter per-endpoint, middleware global
10. **BackgroundService chejori scoped dependency migire?** — IServiceScopeFactory → CreateScope
11. **Chera DI extension method?** — organize, re-use, testable, clean Program.cs
12. **Decorator pattern to DI?** — Scrutor Decorate: wrap original implementation. Chain
13. **AddOpenBehavior order?** — aval register = outermost. Akhari = closest to handler
14. **IHttpContextAccessor chie?** — singleton access to current request's HttpContext. AsyncLocal
15. **Chera DbContext scoped-e?** — per-request UoW. Singleton → stale, thread-unsafe. Transient → no UoW
16. **AddHttpClient chie?** — typed HttpClient ba `IHttpClientFactory`. Socket reuse, lifetime management
17. **HttpContext.Items vs DI?** — Items per-request dict (weak typing). DI behtar (strong typing)
18. **Chejori DI test mikoni?** — `ServiceCollection` besaz, configure, build `ServiceProvider`, resolve
19. **Open generic registration?** — `AddScoped(typeof(IRepo<>), typeof(Repo<>))` — any T matched
20. **Service locator chie? Chera bad-e?** — `GetService` manual resolve. Hidden dependency. Hard to test. Prefer constructor injection

---

## Resume

**short:**

> Built ASP.NET Core middleware pipelines across 8 microservices with custom token revocation, tenant context, and distributed trace enrichment middleware — organized via modular DI with Scrutor decorators, MediatR pipeline behaviors, and endpoint filter authorization chains.

**bullets:**

- Designed consistent middleware pipelines (CORS → auth → tenant → endpoint) across 8 services with environment-specific branching
- Implemented IMiddleware-based token revocation with Redis HybridCache, convention-based tenant context via AsyncLocal, and Serilog TraceId enrichment
- Organized DI using Clean Architecture extension methods (`AddPresentation/Application/Infrastructure`) with per-module registration (`AddVisitorsModule`)
- Applied Scrutor decorator pattern for idempotent domain event handling and MediatR open behaviors for cross-cutting validation/logging/exception handling
- Built IEndpointFilter chain for site-scoped permission authorization on Minimal API endpoints

**skills:** `ASP.NET Core Middleware, Dependency Injection, Pipeline Architecture, Scrutor, MediatR Pipeline Behaviors, IEndpointFilter, IHostedService, Options Pattern, IHttpContextAccessor`

---

## File-haye mohem

| chi | koja |
|---|---|
| Gateway pipeline | `ApiGateway/Program.cs` |
| Dejban.Api pipeline | `Dejban.Api/Program.cs` |
| IdentityServer pipeline | `IdentityServer/Program.cs` |
| ACLServer pipeline | `ACLServer/Program.cs` |
| TokenRevokeMiddleware | `Common/Caching/TokenRevokeMiddleware.cs` |
| AccessTokenQueryMiddleware | `Common/Authentication/AccessTokenQueryMiddleware.cs` |
| TenantContextMiddleware | `Common/Tenancy/TenantContextMiddleware.cs` |
| LogContextMiddleware | `Dejban.Api/Middleware/LogContextTraceLoggingMiddleware.cs` |
| Common DI extensions | `Common/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Dejban shared infra | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| Dejban shared app | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| Visitors module DI | `Visitors.Infrastructure/VisitorsModule.cs` |
| Scrutor idempotent | `Visitors.Infrastructure/Outbox/IdempotentDomainEventHandler.cs` |
| MediatR behaviors | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| Validation behavior | `ACLServer/Abstractions/Behaviors/ValidationBehavior.cs` |
| Endpoint filters | `Common/Authorization/SiteAccessRequirementFilter.cs` + siblings |
| Filter extensions | `Common/Authorization/AuthorizationExtensions.cs` |
| Action filter | `ACLServer/Abstractions/Filters/PlateReaderAgentAuthFilter.cs` |
| Background service | `ACLServer/Infrastructure/Services/PlateReaderNotifyHostedService.cs` |
| Quartz config | `Visitors.Infrastructure/Inbox/ConfigureProcessInboxJob.cs` |
| Endpoint discovery | `Dejban.Common.Presentation/Endpoints/EndpointExtensions.cs` |
| Handler factory | `Dejban.Common.Infrastructure/Outbox/DomainEventHandlersFactory.cs` |
| Options (JwtSettings) | `GlobalAppsettings/globalAppsettings.json` |
| AsyncLocal tenant | `Common/Tenancy/TenantContextAccessor.cs` |

---

Day 05 tamum. Ba'd: Day 06 — JWT Bearer + token blacklist. Fehrest: [README.md](./README.md).
