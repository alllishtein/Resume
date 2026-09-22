# Day 18 — Modular DI (`AddXxxModule`)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Modular monolith DI = **composition root** (`Program.cs`) + **per-module extension methods** (`AddPersonnelsModule`, `AddVisitorsModule`, …). Shared cross-cutting: `AddApplication` (MediatR + validators) va `AddInfrastructure` (auth, MassTransit, Quartz, Redis, tenant, outbox interceptor). Har module: DbContext + schema, repos, `IUnitOfWork` alias, outbox/inbox options + Quartz job config, domain/integration handlers + **Scrutor `Decorate` idempotent**, `AddEndpoints`. MassTransit consumers az module be shared `AddInfrastructure(... moduleConfigureConsumers[])` pass mishan. Config per module: `modules.personnels.json`. Module jadid = class `XxxModule` + yek khat to `Program` — OCP. Standalone microservices (Identity/ACL) ye `AddInfrastructure` monolitik daran, na 8 module.

---

# BAKHSH-E AVAL: WORLD — Modular DI to donya

## Composition root chie?

Yekja ke **hameye** service-ha register mishan va app build mishe — usually `Program.cs` / `Startup`.

```csharp
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddFoo();
builder.Services.AddBar();
var app = builder.Build();
```

**Ghaede:** Domain/Application **nabayad** `IServiceCollection` bebinan. Faghat Infrastructure/API composition root DI midone.

---

## Chera «god Program.cs» bad-e?

```csharp
// ❌ 2000 line Program — register every repo of every feature
services.AddScoped<IVisitorRepository, VisitorRepository>();
services.AddScoped<IPersonnelRepository, PersonnelRepository>();
// × 400...
```

Moshkel:
- Merge conflict
- Onboarding: koja chi register shode?
- Nemishe module ra mentally extract kard
- Test host hard (partial wiring)

**Solution:** group registrations into **modules** / extension methods.

---

## Module pattern (extension method)

```csharp
public static class CatalogModule
{
    public static IServiceCollection AddCatalogModule(
        this IServiceCollection services,
        IConfiguration config)
    {
        services.AddDbContext<CatalogDbContext>(...);
        services.AddScoped<IProductRepository, ProductRepository>();
        services.Configure<CatalogOptions>(config.GetSection("Catalog"));
        return services;
    }
}

// Program:
builder.Services.AddCatalogModule(builder.Configuration);
```

**Maziat:** encapsulation of wiring; Program stays a **table of contents**.

---

## Layers of registration (typical Clean / modular monolith)

```
1. Framework / host     — Kestrel, logging, config
2. Shared kernel        — auth, tenancy, bus, cache
3. Application          — MediatR handlers from ALL modules
4. Per-module Infra     — DbContext, repos, jobs, endpoints
5. Presentation glue    — MapEndpoints, middleware pipeline
```

Order matters for some overrides; usually shared first, modules next.

---

## Service lifetimes (dobare — critical)

| lifetime | instance | use |
|---|---|---|
| **Transient** | har resolve | light/stateless; IEndpoint mappers |
| **Scoped** | per request (scope) | DbContext, repos, handlers |
| **Singleton** | app lifetime | cache, Channel, interceptors (careful), MT bus |

**Classic bug:** Singleton → Scoped (DbContext) captive dependency.

Module registers almost everything **Scoped** except Channel/options monitors/singletons intentional.

---

## `Add` vs `TryAdd` vs `TryAddEnumerable`

```csharp
services.AddScoped<IFoo, Foo>();           // always add (duplicates possible)
services.TryAddScoped<IFoo, Foo>();      // skip if IFoo already registered
services.TryAddEnumerable(descriptor);   // multiple impls of same service type
```

**TryAdd** = shared kernel safe: first wins. Modules don't overwrite `ITenantContext`.

**TryAddEnumerable** = Day 17 `IEndpoint` many implementations.

---

## Decorator pattern + Scrutor

```csharp
services.AddScoped<INotifier, EmailNotifier>();
services.Decorate<INotifier, LoggingNotifier>();
// resolve INotifier → LoggingNotifier(EmailNotifier)
```

Use cases: caching, logging, **idempotency**, transactions.

Dejban: `IdempotentDomainEventHandler<T>` wraps real handler — check outbox_message_consumers before run (Day 23/24).

---

## Options pattern per module

```csharp
services.Configure<OutboxOptions>(config.GetSection("Visitors:Outbox"));
```

```json
{
  "Visitors": {
    "Outbox": { "IntervalInSeconds": 5, ... }
  }
}
```

Har module section joda → tune interval bedune affect digar modules.

---

## Assembly scanning

```csharp
services.AddMediatR(cfg =>
    cfg.RegisterServicesFromAssemblies(moduleAssemblies));

services.AddValidatorsFromAssemblies(moduleAssemblies, includeInternalTypes: true);

services.AddEndpoints(presentationAssembly); // custom scan IEndpoint
```

**Maziat:** kam dasti register. **Khatar:** unexpected types picked up; startup slower; need clear marker interfaces.

---

## Autofac / Lamar / Pure MS.DI

| | |
|---|---|
| **MS.DI** | built-in; Dejban uses this + Scrutor |
| **Autofac modules** | `Load(ContainerBuilder)` classic modular |
| **Lamar** | structuremap successor |

Interview: «modular DI» = pattern, na library. Dejban = extension methods on `IServiceCollection`.

---

## Feature flags / optional modules

```csharp
if (config.GetValue<bool>("Modules:Inventory:Enabled"))
    services.AddInventoryModule(config);
```

Dejban typically **hame modules always on** in one deployable. Extract to microservice later = cut module + own host.

---

## Testing composition

```csharp
var services = new ServiceCollection();
services.AddPersonnelsModule(testConfig);
services.AddSingleton<ITenantContext>(fakeTenant);
var sp = services.BuildServiceProvider();
// assert can resolve IPersonnelRepository
```

Ya `WebApplicationFactory` full host.

---

## Anti-patterns

1. Domain project references `Microsoft.Extensions.DependencyInjection` for registration
2. Circular module deps (Personnels → Visitors → Personnels)
3. Register concrete only — hard to test
4. Multiple `AddDbContext` same type accidental
5. Singleton Channel writer + scoped consumer misuse
6. Copy-paste AddDomainEventHandlers across 8 modules (DRY debt — acceptable isolation)
7. Register MassTransit consumers twice
8. Config magic strings without section constants

---

## Chizaei ke donya dare, Dejban kam/nist

- Autofac `Module` classes
- Dynamic module enable/disable
- Shared generic `AddModule<TModule>()` base
- Central module manifest / plugin DLL load
- One IdempotentHandler package shared (instead of 8 copies per schema)

---

# BAKHSH-E DOVOM: DEJBAN — Modular DI to in proje

## Big picture — `Program.cs` composition root

```csharp
// Dejban.Api/Program.cs (simplified order)

// --- Config ---
builder.Configuration.AddJsonFile(... globalAppsettings ...);
builder.Configuration.AddModuleConfiguration([
    "visitors", "personnels", "security_patrols", "vehicles",
    "armory", "cash_logistics", "inventory", "weigh_bridge"]);

// --- Application (ALL module Application assemblies) ---
Assembly[] moduleApplicationAssemblies = [
    Visitors.Application.AssemblyReference.Assembly,
    Personnels.Application.AssemblyReference.Assembly,
    // ... 8 modules
];
builder.Services.AddApplication(moduleApplicationAssemblies);

// --- Shared Infrastructure + MassTransit consumer delegates ---
builder.Services.AddInfrastructure(
    DiagnosticsConfig.ServiceName,
    [
        GlobalConsumers.ConfigureGlobalConsumers,
        VisitorsModule.ConfigureConsumers,
        PersonnelsModule.ConfigureConsumers,
        SecurityPatrolsModule.ConfigureConsumers,
        VehiclesModule.ConfigureConsumers,
        ArmoryModule.ConfigureConsumers,
        CashLogisticsModule.ConfigureConsumers,
        InventoryModule.ConfigureConsumers,
        WeighBridgeModule.ConfigureConsumers
    ],
    [ /* ConfigureReceiveEndpoints per module */ ],
    databaseConnectionString,
    redisConnectionString,
    builder.Configuration);

builder.Services.AddPresentation(builder.Configuration);

// --- Per-module ---
builder.Services.AddVisitorsModule(builder.Configuration);
builder.Services.AddPersonnelsModule(builder.Configuration);
builder.Services.AddSecurityPatrolsModule(builder.Configuration);
builder.Services.AddVehiclesModules(builder.Configuration); // note plural name smell
builder.Services.AddArmoryModule(builder.Configuration);
builder.Services.AddCashLogisticsModule(builder.Configuration);
builder.Services.AddInventoryModule(builder.Configuration);
builder.Services.AddWeighBridgeModule(builder.Configuration);

// --- Pipeline ---
app.UseAuthentication();
app.UseAuthorization();
app.UseTenantContext();
app.MapEndpoints(); // all IEndpoint from all modules
```

**Yad begir:** MediatR handlers az Application assemblies (shared AddApplication). Endpoints/repos/DbContext az AddXxxModule.

---

## `AddApplication` — shared CQRS wiring

```csharp
// Dejban.Common.Application/ApplicationConfiguration.cs
public static IServiceCollection AddApplication(
    this IServiceCollection services,
    Assembly[] moduleAssemblies)
{
    Dapper.DefaultTypeMap.MatchNamesWithUnderscores = true;

    services.AddMediatR(config =>
    {
        config.RegisterServicesFromAssemblies(moduleAssemblies);
        config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
        config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
        config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
    });

    services.AddValidatorsFromAssemblies(moduleAssemblies, includeInternalTypes: true);
    // Mapster scan...
    return services;
}
```

**Yek** MediatR pipeline baraye hame modules. Handler `CreatePersonnelCommandHandler` automatic register az Personnels.Application assembly.

---

## `AddInfrastructure` — shared platform

```csharp
// Dejban.Common.Infrastructure/InfrastructureConfiguration.cs
services.AddApiVersioningAndExplorer();
services.AddAuthenticationInternal(configuration);
services.AddAuthorizationInternal();
services.TryAddScoped<ITenantContext, TenantContext>();
services.TryAddSingleton<IDateTimeProvider, DateTimeProvider>();
services.TryAddSingleton<IEventBus, EventBus>();
services.TryAddSingleton<InsertOutboxMessagesInterceptor>();
services.TryAddScoped<IDbConnectionFactory, DbConnectionFactory>();
services.AddQuartz(...);
services.AddCacheServices(redis)...AddTokenBlackList...
services.AddMassTransit(configure =>
{
    foreach (var configureConsumers in moduleConfigureConsumers)
        configureConsumers(configure);

    configure.UsingRabbitMq((context, cfg) =>
    {
        cfg.UseTenantContextFilters(context);
        cfg.UseMessageRetry(...);
        cfg.UseCircuitBreaker(...);
        foreach (var configureReceive in moduleConfigureReceiveEndpoints)
            configureReceive(cfg, context);
        cfg.ConfigureEndpoints(context);
    });
});
```

**Chera consumers array?** MassTransit **yek** bus per process. Modules nemitunan separately `AddMassTransit` — collide. Pas har module `ConfigureConsumers` static Action mide → composition root collect → yek `AddMassTransit`.

---

## Module config files

```csharp
// ConfigurationExtensions.cs
internal static void AddModuleConfiguration(
    this IConfigurationBuilder configurationBuilder,
    string[] modules)
{
    foreach (string module in modules)
    {
        configurationBuilder.AddJsonFile($"modules.{module}.json", false, true);
        configurationBuilder.AddJsonFile($"modules.{module}.Development.json", true, true);
    }
}
```

Mesal `modules.personnels.json`:

```json
{
  "Personnels": {
    "Outbox": { "IntervalInSeconds": ..., "BatchSize": ... },
    "Inbox": { ... }
  }
}
```

Bind:

```csharp
services.Configure<OutboxOptions>(configuration.GetSection("Personnels:Outbox"));
services.Configure<InboxOptions>(configuration.GetSection("Personnels:Inbox"));
```

Global secrets/connection: `globalAppsettings.json` (Postgres, Redis, Rabbit, Jwt).

---

## Anatomy of `AddXxxModule` (template)

Har 8 module hamin skeleton:

```csharp
public static class PersonnelsModule
{
    public static IServiceCollection AddPersonnelsModule(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDomainEventHandlers();
        services.AddIntegrationEventHandlers();
        services.AddInfrastructure(configuration);
        services.AddEndpoints(Presentation.AssemblyReference.Assembly);
        return services;
    }

    public static Action<IRegistrationConfigurator> ConfigureConsumers =>
        configure =>
        {
            configure.AddConsumer<IntegrationEventConsumer<SiteSoftDeleted>>();
            configure.AddConsumer<IntegrationEventConsumer<UnitSoftDeleted>>();
            // ... module-specific events + request clients
        };

    public static Action<IRabbitMqBusFactoryConfigurator, IRegistrationContext>
        ConfigureReceiveEndpoints => (cfg, context) => { /* rarely used */ };

    private static void AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        // 1) DbContext + schema migration history + outbox interceptor
        services.AddDbContext<PersonnelsDbContext>((sp, options) =>
            options.UseNpgsql(
                    configuration.GetConnectionString("Postgres"),
                    npgsql => npgsql.MigrationsHistoryTable(
                        HistoryRepository.DefaultTableName, Schemas.Personnels))
                .AddInterceptors(sp.GetRequiredService<InsertOutboxMessagesInterceptor>())
                .UseSnakeCaseNamingConvention());

        // 2) Repositories
        services.AddScoped<IPersonnelRepository, PersonnelRepository>();
        // ... many

        // 3) UoW = same DbContext instance
        services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<PersonnelsDbContext>());

        // 4) Options + Quartz job configuration
        services.Configure<OutboxOptions>(configuration.GetSection("Personnels:Outbox"));
        services.Configure<InboxOptions>(configuration.GetSection("Personnels:Inbox"));
        services.ConfigureOptions<ConfigureProcessOutboxJob>();
        services.ConfigureOptions<ConfigureProcessInboxJob>();

        // 5) Module-specific extras (generators, import store, MediaMTX, …)
    }

    private static void AddDomainEventHandlers(...) { /* scan + Decorate */ }
    private static void AddIntegrationEventHandlers(...) { /* scan + Decorate */ }
}
```

---

## DbContext per module — DI detail

```csharp
services.AddDbContext<PersonnelsDbContext>(...);
services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<PersonnelsDbContext>());
```

- 8 DbContext types → 8 scoped registrations (OK — different types)
- Handlers in Personnels inject `Personnels` `IUnitOfWork` (Application abstraction per module)
- **Cannot** inject Visitors `IUnitOfWork` into Personnels handler — different interface namespace / type

Same physical Postgres DB, different EF models/schemas (Day 13).

---

## Repository registration

```csharp
services.AddScoped<IVisitorRepository, VisitorRepository>();
services.AddScoped<ISiteRepository, SiteRepository>();
services.AddScoped<IPersonnelRepository, PersonnelRepository>(); // local copy!
```

**Mohem:** `IPersonnelRepository` to Visitors module ≠ Personnels module interface — **joda types** (joda Domain projects). DI conflict nist. Event sync copies data.

---

## Domain + Integration handler registration + Scrutor

```csharp
private static void AddDomainEventHandlers(this IServiceCollection services)
{
    Type[] domainEventHandlers = Application.AssemblyReference.Assembly
        .GetTypes()
        .Where(t => t.IsAssignableTo(typeof(IDomainEventHandler)))
        .ToArray();

    foreach (Type domainEventHandler in domainEventHandlers)
    {
        services.TryAddScoped(domainEventHandler);

        Type domainEvent = domainEventHandler
            .GetInterfaces()
            .Single(i => i.IsGenericType)
            .GetGenericArguments()
            .Single();

        Type closedIdempotentHandler =
            typeof(IdempotentDomainEventHandler<>).MakeGenericType(domainEvent);

        services.Decorate(domainEventHandler, closedIdempotentHandler);
    }
}
```

Integration handlers: scan **Presentation** assembly (`IIntegrationEventHandler`), same Decorate with `IdempotentIntegrationEventHandler<>`.

**Decorate resolve chain:**
```
caller → IdempotentXxxHandler → real Handler
```

Idempotent checks `{schema}.outbox_message_consumers` / inbox consumers via Dapper (per-module SQL schema name inside copied class — e.g. `armory.outbox_message_consumers`).

**Smell:** `IdempotentDomainEventHandler` **copied per module** (schema string differs). Scrutor package shared; handler class not fully DRY.

---

## Endpoints registration (Day 17 link)

```csharp
services.AddEndpoints(Presentation.AssemblyReference.Assembly);
```

Module owns Presentation assembly reference. `MapEndpoints` later flattens all.

---

## MassTransit consumers — module → host

```csharp
// PersonnelsModule
public static Action<IRegistrationConfigurator> ConfigureConsumers =>
    configure =>
    {
        configure.AddConsumer<IntegrationEventConsumer<SiteCreated>>();
        configure.AddConsumer<IntegrationEventConsumer<SiteSoftDeleted>>();
        configure.AddConsumer<IsContractorRegistrationNumberUniqueConsumer>();
        // request/response consumers...
    };
```

Visitors also:

```csharp
configure.AddRequestClient<HasApprovedRequestStep>();
configure.AddConsumer<IntegrationEventConsumer<PersonnelSoftDeleted>>();
configure.AddConsumer<IntegrationEventConsumer<AccessLogCreated>>();
```

Inventory minimal:

```csharp
configure.AddConsumer<IntegrationEventConsumer<UnitSoftDeleted>>();
```

**Composition:** host arrays order ≈ registration order. Endpoint name formatter kebab-case.

Empty `ConfigureReceiveEndpoints` common — `ConfigureEndpoints(context)` convention-based enough.

---

## Module-specific extras (mesal-ha)

| module | extra DI |
|---|---|
| **Visitors** | `Channel<VisitScheduleChangeEvent>` singleton Reader/Writer (SSE/realtime) |
| **Personnels** | `IACLUserIdGenerator`, `IMediaMTXService`, `IPersonnelImportSessionStore`, `PersonnelImportPlanner`, `IDoorApi` |
| **Armory** | many asset/weapon repos |
| **Vehicles** | assignment/maintenance repos |
| **Inventory** | warehouse/transfer repos (filters incomplete smell from Day 15/16) |

Channel pattern:

```csharp
var channel = Channel.CreateUnbounded<VisitScheduleChangeEvent>();
services.AddSingleton(channel);
services.AddSingleton(channel.Reader);
services.AddSingleton(channel.Writer);
```

Producer scoped handler writes; background/SSE reads — classic.

---

## Quartz jobs wiring

```csharp
services.ConfigureOptions<ConfigureProcessOutboxJob>();
services.ConfigureOptions<ConfigureProcessInboxJob>();
```

`IConfigureOptions<QuartzOptions>` adds job+trigger per module with interval from `OutboxOptions`/`InboxOptions`. Shared `AddQuartz` + `AddQuartzHostedService` once in common Infrastructure.

Har module → own `ProcessOutboxJob` / `ProcessInboxJob` types (schema-specific SQL).

---

## Interceptor shared singleton

```csharp
services.TryAddSingleton<InsertOutboxMessagesInterceptor>();
// each DbContext:
.AddInterceptors(sp.GetRequiredService<InsertOutboxMessagesInterceptor>())
```

Yek interceptor type, hame DbContexts. Reads `TenantContextAccessor` at SaveChanges (Day 16).

---

## Project / layer dependencies (DI implications)

```
API → Infrastructure (each module) → Application → Domain
                 ↘ Common.* 
Presentation ← referenced by Infrastructure for endpoints + integration handlers
```

`AddXxxModule` zende to **Infrastructure** project — only layer allowed to know EF + DI concrete.

Domain: **zero** DI registration.

---

## Checklist — module jadid ezafe kon

1. Create Domain / Application / Infrastructure / Presentation projects
2. `AssemblyReference` dar Application + Presentation
3. `XxxDbContext` + schema + configs
4. `XxxModule.cs` ba template bala
5. `modules.xxx.json` (+ Development)
6. `Program`:  
   - add Application assembly to array  
   - `AddModuleConfiguration` name  
   - `ConfigureConsumers` / ReceiveEndpoints arrays  
   - `services.AddXxxModule(config)`
7. Migrationesho / server schema (no migration commit — repo rule)
8. Verify Scalar endpoints + consumers connect

**Program changes = intentional thin** — list of modules. Core OCP still holds for endpoints/handlers inside module.

---

## Standalone services contrast

```csharp
// IdentityServer — single AddInfrastructure style
services.AddDbContext<ApplicationDbContext>();
services.AddMassTransit(...); // local
// Controllers, not IEndpoint scan
```

No `AddPersonnelsModule`. Microservice = yek bounded context = yek composition.

Dejban.Api = **many** bounded contexts **one** host.

---

## Naming inconsistencies (honest)

| item | note |
|---|---|
| `AddVehiclesModules` | plural «Modules» — typo/legacy vs others `AddXxxModule` |
| `IPersonnelRepository` × N | same name different namespaces — OK |
| Idempotent handler copies | 8 near-duplicate classes |
| `ConfigureReceiveEndpoints` empty | boilerplate still required in arrays |

---

## Connection to other days

| day | rabt |
|---|---|
| 03 OOP | OCP module + Decorate |
| 05 Pipeline/DI | lifetimes, TryAdd |
| 09 Architecture | modular monolith wiring |
| 10 MediatR | AddApplication behaviors |
| 13 EF | per-module DbContext register |
| 14 UoW | `AddScoped<IUnitOfWork>(sp => DbContext)` |
| 17 IEndpoint | `AddEndpoints` inside module |
| 19–23 | outbox/inbox options + consumers |
| 24 Decorator | Scrutor Decorate deep dive |
| 20 MassTransit | ConfigureConsumers aggregation |

---

## Smell-ha

1. **Copy-paste** AddDomainEventHandlers / AddIntegrationEventHandlers × 8
2. **Idempotent*Handler** duplicated per schema
3. **AddVehiclesModules** naming
4. **Program still grows** with each module (acceptable TOC)
5. **No feature flag** to disable Inventory
6. **ConfigureReceiveEndpoints** empty stubs noise
7. **commented** `AddConsumers(Presentation.Assembly)` — manual consumer list instead
8. **Infrastructure references Presentation** — for handlers/endpoints (pragmatic; purists dislike)
9. **Global MediatR** — any module handler callable; no module boundary enforcement at Send
10. **Channel unbounded** Visitors — memory risk if consumer slow
11. **TryAddScoped handler then Decorate** — order sensitive; wrong order breaks idempotency
12. **Multiple IUnitOfWork types** — easy wrong inject if using wrong using
13. **Quartz SchedulerId Guid** each startup — OK multi-instance care
14. **Inventory filters** missing — module DI complete but EF tenancy incomplete
15. **PublicApi / cross-module interfaces** (`IDoorApi`) — registration easy to forget

---

## Debug checklist

| symptom | check |
|---|---|
| 404 endpoint | module `AddEndpoints` + `AddXxxModule` called? |
| Handler not found MediatR | Application assembly in `AddApplication` array? |
| Consumer never runs | `ConfigureConsumers` in host array? |
| Decorate exception startup | Scrutor package? handler registered before Decorate? |
| Wrong schema migrations | `MigrationsHistoryTable(..., Schemas.X)` |
| Options null | `modules.x.json` loaded? section name match? |
| DbContext dispose | captive singleton holding scoped? |
| Duplicate consumer | registered in two modules' ConfigureConsumers? |

---

## 25 soal-e mosahebe

1. Composition root chie?
2. Chera AddXxxModule?
3. OCP chejori ba module?
4. Add vs TryAdd?
5. TryAddEnumerable?
6. Scoped vs Singleton DbContext?
7. Chera IUnitOfWork factory to DbContext?
8. MediatR koja register?
9. Chera consumers array be AddInfrastructure?
10. Nemishe per-module AddMassTransit?
11. Scrutor Decorate chie?
12. Idempotent handler cherā decorate?
13. Module json config?
14. AssemblyReference pattern?
15. Domain DI midone? (no)
16. 8× IPersonnelRepository conflict? (no — different types)
17. Channel singleton use case?
18. Quartz job per module chejori?
19. Chejori module jadid add?
20. Extract module to microservice?
21. Captive dependency?
22. Infrastructure → Presentation ref smell?
23. Feature flag modules?
24. Autofac Module vs extension method?
25. Validate DI at startup? (`ValidateOnBuild` / `ValidateScopes`)

---

## Senario whiteboard

### A) New CashLogistics endpoint

```
Only CashLogistics.Presentation + Application
AddCashLogisticsModule already calls AddEndpoints
Program unchanged
```

### B) New entire module «Parking»

```
Program: +assembly, +AddModuleConfiguration, +ConfigureConsumers, +AddParkingModule
Shared AddInfrastructure gains one more Action in arrays
```

### C) Forgot ConfigureConsumers in array

```
AddParkingModule registers handlers/repos
Events published but nobody consumes in this host
→ silent missing sync
```

### D) Decorate without TryAddScoped handler

```
Scrutor throws / resolve fails
```

### E) Two modules AddConsumer same closed type carelessly

```
MT may register duplicate receive endpoints — careful design
```

---

## Mini lab

1. Open `Program.cs` — list every `Add*Module`
2. Open `PersonnelsModule.cs` — map 5 steps of AddPersonnelsModule
3. Breakpoint `AddInfrastructure` MassTransit foreach consumers
4. `modules.visitors.json` vs `Configure<OutboxOptions>` section
5. Find `services.Decorate` — F12 IdempotentDomainEventHandler
6. Compare IdentityServer DI — no modules
7. Sketch Parking module checklist on paper

---

## Resume

**short:**

> Composed a modular monolith DI surface: shared `AddApplication`/`AddInfrastructure` for MediatR, auth, MassTransit, and Quartz, plus per-bounded-context `AddXxxModule` extensions that register schema-scoped DbContexts, repositories, outbox/inbox jobs, Scrutor-decorated idempotent handlers, and Minimal API endpoints — keeping the host `Program` as a thin module catalog.

**bullets:**

- Standardized module template: handlers + infrastructure + `AddEndpoints` + static `ConfigureConsumers` for the shared bus
- Wired `IUnitOfWork` to each module DbContext; options from `modules.{name}.json`
- Used Scrutor `Decorate` for idempotent domain/integration event handlers per schema
- Aggregated module MassTransit registrations into one `AddMassTransit` call with tenant filters and retry/circuit-breaker

**skills:** `Dependency Injection, Modular Monolith, Composition Root, Scrutor, MediatR, MassTransit, EF Core DbContext, Options Pattern, Quartz.NET, Clean Architecture`

---

## File-haye mohem

| chi | koja |
|---|---|
| Composition root | `Dejban.Api/Program.cs` |
| AddApplication | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| AddInfrastructure | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| Module config loader | `Dejban.Api/Extensions/ConfigurationExtensions.cs` |
| modules.*.json | `Dejban.Api/modules.*.json` |
| PersonnelsModule | `Personnels.Infrastructure/PersonnelsModule.cs` |
| VisitorsModule | `Visitors.Infrastructure/VisitorsModule.cs` |
| VehiclesModule | `Vehicles.Infrastructure/VehiclesModule.cs` |
| InventoryModule | `Inventory.Infrastructure/InventoryModule.cs` |
| ArmoryModule | `Armory.Infrastructure/ArmoryModule.cs` |
| (+ CashLogistics, SecurityPatrols, WeighBridge) | `*.Infrastructure/*Module.cs` |
| Idempotent decorator sample | `Armory.Infrastructure/Outbox/IdempotentDomainEventHandler.cs` |
| AddEndpoints | `Dejban.Common.Presentation/.../EndpointExtensions.cs` |
| Presentation Add* | `Dejban.Api/Extensions/ServiceCollectionExtension.cs` |

---

## Chejori digest koni

1. Program.cs ra mesle fehrest bekhoon (10 min)
2. Yek Module.cs complete (Personnels) line-by-line (25 min)
3. Follow ConfigureConsumers → AddMassTransit (10 min)
4. modules.personnels.json ↔ Configure OutboxOptions (5 min)
5. Decorate + IdempotentHandler (15 min)
6. 25 soal (20 min)
7. Checklist module jadid roye kaghaz (5 min)

---

## Deep dive — ValidateScopes / ValidateOnBuild

```csharp
builder.Host.UseDefaultServiceProvider(o =>
{
    o.ValidateScopes = true;      // captive dependency detect
    o.ValidateOnBuild = true;     // resolve all singletons at startup
});
```

Development gold. Age Singleton accidentally depends on Scoped DbContext → fail fast at boot, na runtime random.

Dejban may not always enable — miduni as tool.

---

## Deep dive — mediatR cross-module Send

```csharp
// Technically possible from Visitors handler:
await sender.Send(new SomePersonnelsOnlyCommand());
```

DI/MediatR **enforce nemikone** module boundary. Convention + code review + (optional) architecture tests (NetArchTest Day 56).

Integration between modules = **events**, na cross-module command Send. Smell age direct Send across modules.

---

## Deep dive — IConfigureOptions for Quartz

```csharp
// Conceptual ConfigureProcessOutboxJob
public class ConfigureProcessOutboxJob : IConfigureOptions<QuartzOptions>
{
    // reads OutboxOptions.IntervalInSeconds
    // q.AddJob<ProcessOutboxJob>(...)
    // q.AddTrigger(t => t.WithSimpleSchedule(s => s.WithIntervalInSeconds(...)))
}
```

`ConfigureOptions<T>` runs when QuartzOptions built. Har module own job type + own interval section.

Conflict: two jobs same job key → Quartz error. Naming must include module.

---

## Deep dive — connection string sharing

Hame modules:

```csharp
configuration.GetConnectionString("Postgres")
```

Yek DB. Schema isolation logical. Connection pooling shared via Npgsql.

`NpgsqlDataSource` singleton in common Infra for Dapper (`IDbConnectionFactory`) — parallel path to EF.

---

## Deep dive — GlobalConsumers

```csharp
GlobalConsumers.ConfigureGlobalConsumers
```

Host-level consumers na bound to one module (diagnostics, cross-cutting). Array **first** often — order rarely matters for MT registration but documentation clarity.

---

## Dependency graph (mental)

```
                    Program (API)
                   /      |      \
          AddApplication  AddInfrastructure  AddPresentation
                 |              |
         (8 App asms)    MT+Auth+Quartz+Redis
                              |
              +---------------+(callbacks)
              |  ConfigureConsumers×8
              v
        AddVisitorsModule ... AddWeighBridgeModule
              |
         DbContext, Repos, Endpoints, Handlers+Decorate
```

---

## Comparison — modular monolith DI vs microservice DI

| | Modular monolith (Dejban.Api) | Microservice (Identity) |
|---|---|---|
| Hosts | 1 | 1 per service |
| Modules | 8 AddXxxModule | 1 implicit |
| DbContexts | 8 | 1 |
| Bus | 1 shared MT | 1 local MT |
| Deploy | all or nothing | independent |
| Program TOC | long module list | short |

Extract Visitors later: copy VisitorsModule + Presentation/App/Domain into new host; remove from Dejban.Api arrays; events remain contract.

---

## Common interview follow-ups (javab kootah)

**Q: Chera Scrutor na manual factory?**  
A: Decorate keeps open/closed; handler code unaware of idempotency.

**Q: Chera handlers Transient/Scoped?**  
A: Scoped — may use scoped DbContext/UoW; Transient endpoint mappers OK.

**Q: Options monitor reload?**  
A: `IOptionsMonitor` can hot-reload json; jobs usually read at configure time — know staleness.

**Q: Circular DI?**  
A: A→B→A constructor — fail at resolve. Fix: events, mediate interface, lazy.

---

## Expand — Visitors Channel flow

```
VisitSchedule changed (handler)
  → channel.Writer.WriteAsync(evt)
SSE / background reader
  → channel.Reader.ReadAllAsync()
  → push to connected clients
```

DI: Writer+Reader singletons same channel instance. Bound to Visitors module lifetime = process lifetime.

---

## Expand — Public API inside module

```csharp
services.AddScoped<IDoorApi, DoorApi>();
```

Application/other modules sometimes need sync query API without full event. Still registered inside owning module. Prefer events for write side-effects.

---

## Chejori «composition» ra roye resume beggi

> «Thin composition root cataloging bounded contexts via `AddXxxModule`, with shared platform services registered once and module-specific DbContexts/repos/jobs/endpoints encapsulated behind extension methods.»

---

*Day 18 tamum. Ba'd: Day 19 — Dapper (outbox/inbox) — amade. Fehrest: [README.md](./README.md).*
