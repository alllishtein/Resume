# Day 10 — Microservices vs Modular Monolith + DDD Layering

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Architecture-e ye system = chejori code ra split mikoni, chejori deploy mikoni, va chejori service-ha ba ham sohbat mikonan. Dejban **do ta** architecture dare: **modular monolith** (8 module to yek process) + **microservices** (7 ta service-e joda). In fasl tozih mide chera in entekhab shode, DDD layering chejori enforce mishe, va boundary-ha chejoori hefz mishan.

---

# BAKHSH-E AVAL: WORLD — Architecture + DDD to donya

## 3 architecture style

### 1. Monolith

Kole code to **yek deployable**, **yek database**, **yek process**.

```
┌─────────────────────────┐
│        Monolith          │
│  Users  Orders  Payment  │
│         ┌───┐            │
│         │ DB│            │
│         └───┘            │
└─────────────────────────┘
```

**Maziat:** Sade. Yek deploy. Yek debug. Transaction-e local. Refactor asan.
**Moshkel:** Scale kole app lazem. Team conflict. Deploy-e yek feature = deploy-e hame. Code coupling roshd mikone.

### 2. Microservices

Har domain/feature ye **service-e joda** ba **DB-e joda** va **deploy-e joda**.

```
┌──────┐  ┌──────┐  ┌──────┐
│Users │  │Orders│  │Payment│
│ ┌──┐ │  │ ┌──┐ │  │ ┌──┐  │
│ │DB│ │  │ │DB│ │  │ │DB│  │
│ └──┘ │  │ └──┘ │  │ └──┘  │
└──┬───┘  └──┬───┘  └──┬────┘
   │         │         │
   └─────────┴─────────┘
         Message Queue
```

**Maziat:** Independent deploy. Scale per-service. Team autonomy. Technology freedom.
**Moshkel:** Network latency. Distributed transaction (saga). Debugging sakht. Ops overhead (Docker, K8s, monitoring). Data consistency (eventual).

### 3. Modular Monolith

**Module-ha** dakhel-e yek process, vali **boundary-e strict** daran. Yek DB, vali **schema-e joda**. Communication async (event) ya defined API.

```
┌─────────────────────────────┐
│         Single Process       │
│ ┌───────┐ ┌───────┐ ┌─────┐│
│ │Users  │ │Orders │ │Pay  ││
│ │schema │ │schema │ │schma││
│ └───┬───┘ └───┬───┘ └──┬──┘│
│     └─────────┴────────┘   │
│          ┌───┐              │
│          │ DB│ (1 DB, N schema)
│          └───┘              │
└─────────────────────────────┘
```

**Maziat:** Monolith-e sade + microservice-e boundary. Refactor → split be microservice age lazem she. Transaction-e local momken. Deploy sade.
**Moshkel:** Scale kole app (mesle monolith). Module boundary enforce sakht (bayad tooling/test).

### Comparison

| | Monolith | Modular Monolith | Microservices |
|---|---|---|---|
| Deploy | 1 unit | 1 unit | N unit |
| DB | 1 | 1 (N schema) | N (per-service) |
| Communication | method call | event/API in-process | HTTP/gRPC/queue |
| Transaction | local | local (per-module) ya saga | distributed saga |
| Scale | kole app | kole app | per-service |
| Team | 1 big team | feature teams | service teams |
| Complexity | code | code + conventions | infrastructure |
| Split later | sakht | **asan** ← in maziat-e | already split |

**Key insight:** Modular monolith "best of both" nist — "good enough of both" hast. Baraye team-e kuchik ke microservice overhead na mikhad vali boundary mikhad, ideal-e.

---

## Clean Architecture

Uncle Bob (Robert C. Martin) — layer-ha az birun be darun depend mikonan, na bar'aks.

```
┌─────────────────────────────────┐
│         Presentation            │  ← Controllers, Endpoints, UI
│    ┌────────────────────────┐   │
│    │     Infrastructure     │   │  ← DB, Cache, External APIs
│    │   ┌────────────────┐   │   │
│    │   │   Application  │   │   │  ← Use cases, CQRS handlers
│    │   │  ┌──────────┐  │   │   │
│    │   │  │  Domain   │  │   │   │  ← Entities, Value Objects, Events
│    │   │  └──────────┘  │   │   │
│    │   └────────────────┘   │   │
│    └────────────────────────┘   │
└─────────────────────────────────┘
```

**Dependency Rule:** Dependencies FAGHAT be samte darun:
- Domain → hichchi (pure, no dependency)
- Application → Domain
- Infrastructure → Application + Domain
- Presentation → Application (+ sometimes Infrastructure)

**Domain HICHVAGHT az Infrastructure depend nakone.** Interface to Application, implementation to Infrastructure. DI wire mikone.

---

## DDD — Domain-Driven Design

### Strategic DDD (high-level)

| concept | chi |
|---|---|
| **Bounded Context** | ye model ke dar yek boundary ma'ni dare. "User" to Identity ≠ "User" to Billing |
| **Ubiquitous Language** | team va code haman zaban ra estefade mikonan. "Visitor" na "Guest" |
| **Context Map** | chejori bounded context-ha ba ham communicate mikonan |
| **Anti-corruption Layer** | translate between contexts, na direct dependency |

### Tactical DDD (code-level)

| concept | chi |
|---|---|
| **Entity** | identity dare (ID). Personnel, Visitor |
| **Value Object** | identity nadare, immutable. VehiclePlate, Address, Money |
| **Aggregate** | cluster of entities ke together consistent hastand. Root entity = entry point |
| **Aggregate Root** | tanha entity ke az birun accessible-e. CRUD faghat az root |
| **Domain Event** | chizi ke to domain etefagh oftade. PersonnelCreated, VisitApproved |
| **Domain Service** | logic ke be hich entity belong nakone |
| **Repository** | abstraction baraye data access. IVisitorRepository |
| **Factory** | create complex aggregates. `Personnel.CreateAsync(...)` |
| **Specification** | query logic ra encapsulate kon |

### Aggregate Rules

1. Reference aggregate root by **ID only** (na navigation property be dige aggregate)
2. Aggregate root **consistency boundary**-e — hame-ye invariant-ha check mishan
3. One transaction = one aggregate (ya saga baraye cross-aggregate)
4. Small aggregates preferred — na 100 entity to yek aggregate

---

## Outbox / Inbox Pattern (overview)

Cross-boundary communication reliable nabud: entity save shod, event send nashod = inconsistency.

**Outbox:**
1. Entity save + event insert → **same transaction**
2. Background job → read outbox → publish to queue
3. Mark as processed

**Inbox:**
1. Consumer receives from queue → insert to inbox table
2. Background job → read inbox → process handler
3. Idempotent: duplicate message = skip

```
Module A                    RabbitMQ              Module B
┌──────────────┐           ┌──────┐           ┌──────────────┐
│ SaveChanges  │           │      │           │              │
│ + outbox row │──Quartz──►│ msg  │──────────►│ inbox row    │
│ (same tx)    │           │      │           │ + Quartz job │
└──────────────┘           └──────┘           └──────────────┘
```

---

## CQRS kholase (detail = Day 11)

**Command Query Responsibility Segregation:**
- **Command** → write (change state). Return success/error.
- **Query** → read (no side effect). Return data.

Separate model baraye read va write. Write model rich (domain logic). Read model optimized (flat DTO, denormalized).

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **Explicit Aggregate Root** base class — Dejban `Entity` dare, `AggregateRoot` nadare
- **Specification pattern** — query builder encapsulated. Dejban repository method per query
- **Saga pattern (orchestrator)** — distributed transaction coordinator. Dejban choreography events dare, formal saga nist
- **Event sourcing** — state = replay events. Dejban CRUD, na event-sourced
- **Shared kernel** — small shared library beyn-e bounded contexts. Dejban `Common.Domain` sade-tar-e
- **Anti-corruption layer** — explicit translator beyn-e contexts. Dejban integration event payload mapping dare
- **Database per module** — fully separate DB. Dejban schema-per-module (softer isolation)
- **API gateway per BFF** — separate gateway per client type. Dejban yek gateway
- **Service registry / discovery** — Consul, Eureka. Dejban static config
- **Contract testing** — Pact. Dejban nadare

---

# BAKHSH-E DOVOM: DEJBAN — Architecture to in proje

## Hybrid architecture

Dejban ye **hybrid**-e: modular monolith + microservices.

```
                    ┌─────────────────────────────┐
                    │       Dejban.Api             │
                    │  ┌────────┐ ┌──────────┐    │
                    │  │Visitors│ │Personnels│    │
                    │  │(schema)│ │(schema)  │    │
                    │  └────────┘ └──────────┘    │
                    │  ┌────────┐ ┌──────────┐    │
                    │  │Vehicles│ │Armory    │    │
                    │  └────────┘ └──────────┘    │
                    │  ┌──────────┐ ┌──────────┐  │
                    │  │CashLogis.│ │Inventory │  │
                    │  └──────────┘ └──────────┘  │
                    │  ┌──────────┐ ┌──────────┐  │
                    │  │SecPatrol │ │WeighBrdg │  │
                    │  └──────────┘ └──────────┘  │
                    │         1 DB, 8 schemas      │
                    └──────────────┬───────────────┘
                                  │
              ┌───────────────────┼────────────────────┐
              │                   │                    │
    ┌─────────▼──┐  ┌────────────▼──┐  ┌──────────────▼──┐
    │Identity    │  │ ACLServer     │  │ DCC             │
    │Server      │  │               │  │                 │
    │(own DB)    │  │(own DB)       │  │(own DB + MinIO) │
    └────────────┘  └───────────────┘  └─────────────────┘
    ┌────────────┐  ┌───────────────┐  ┌─────────────────┐
    │Request     │  │ GateServer    │  │ Reporting       │
    │Tracker     │  │               │  │(reads all DBs)  │
    │(own DB)    │  │(own DB)       │  │                 │
    └────────────┘  └───────────────┘  └─────────────────┘
```

**Chera in split?**

| molem | architecture | dalil |
|---|---|---|
| Dejban (8 module) | Modular monolith | Business domain-e nazdik, shared team, sade-tar deploy, transaction local |
| IdentityServer | Microservice | Security isolation, independent lifecycle |
| ACLServer | Microservice | Device communication, different scale needs |
| DCC | Microservice | File storage, different technology (MinIO) |
| RequestTracker | Microservice | Workflow engine, complex state machine |
| GateServer | Microservice | Hardware integration, real-time |
| Reporting | Microservice | Heavy queries, different read pattern, reads all DBs |

---

## 8 Dejban module — Clean Architecture enforced

Har module **5 ta csproj**:

```
Dejban.Modules.Visitors.Domain              ← entities, events, value objects
Dejban.Modules.Visitors.Application         ← commands, queries, handlers, DTOs
Dejban.Modules.Visitors.Infrastructure      ← DbContext, repos, outbox/inbox, EF config
Dejban.Modules.Visitors.Presentation        ← IEndpoint, integration event handlers
Dejban.Modules.Visitors.IntegrationEvents   ← event contracts (shared)
```

**Plus 4 shared project:**

```
Dejban.Common.Domain          ← Entity base, IDomainEvent, ISoftDeletable
Dejban.Common.Application     ← ICommand, IQuery, pipeline behaviors
Dejban.Common.Infrastructure  ← outbox interceptor, Dapper, OpenTelemetry, MassTransit
Dejban.Common.Presentation    ← IEndpoint, endpoint discovery
```

**Project reference rule:**

```
Domain       → Common.Domain (only)
Application  → Domain + IntegrationEvents + Common.Application
Infrastructure → Application + Presentation + Common.Infrastructure
Presentation → Application + Common.Presentation + Common.Infrastructure
```

**Domain hichvaght Infrastructure/Presentation ra nemishine.** Application hichvaght Infrastructure ra nemishine. DI to `Dejban.Api` wire mikone.

### Chera separate csproj (na faghat folder)?

**Compile-time enforcement.** Age developer to Visitors.Application ye `using Dejban.Modules.Personnels.Domain` bezane → **compile error**. Folder convention in ra nemitone enforce kone.

---

## Microservices — folder-based Clean Architecture

Standalone service-ha (IdentityServer, ACLServer, ...) **yek csproj** daran ba folder-ha:

```
IdentityServer/
├── Domain/           ← entities (ApplicationUser, ...)
├── Application/      ← commands, queries, handlers
├── Infrastructure/   ← DbContext, services, providers
├── Controllers/      ← MVC controllers
├── Abstractions/     ← extensions, helpers, behaviors
└── Program.cs
```

**Fargh ba Dejban modules:**

| | Dejban Module | Standalone Microservice |
|---|---|---|
| Project count | 5 csproj | 1 csproj |
| Boundary enforce | compile-time (reference) | convention only |
| API style | Minimal API (IEndpoint) | MVC Controllers |
| Outbox | custom table + Quartz | MassTransit EF Outbox |
| DB | schema in shared DB | own PostgreSQL DB |
| Deploy | part of Dejban.Api | separate process |

---

## Domain layer — chi daresh

### Entity base

```csharp
// File: Dejban.Common.Domain/Entity.cs

public abstract class Entity
{
    private readonly List<IDomainEvent> _domainEvents = [];

    public IReadOnlyCollection<IDomainEvent> DomainEvents => [.. _domainEvents];

    public void ClearDomainEvents() => _domainEvents.Clear();

    protected void Raise(IDomainEvent domainEvent) => _domainEvents.Add(domainEvent);
}
```

Hame-ye domain entity-ha az `Entity` inherit mikonan. `Raise()` event ra be list ezafe mikone. `InsertOutboxMessagesInterceptor` ba'd az `SaveChanges` event-ha ra az `ChangeTracker` extract mikone va be outbox table insert mikone.

**Na `AggregateRoot`:** Dejban formal aggregate root **nadare**. Hame `Entity` hastan. In yani boundary-e consistency code convention-e, na type system enforce.

### Domain events

```csharp
// File: Dejban.Common.Domain/DomainEvent.cs

public abstract class DomainEvent : IDomainEvent
{
    public Guid Id { get; } = Guid.NewGuid();
    public DateTime OccurredOnUtc { get; } = DateTime.UtcNow;
}
```

```csharp
// File: Visitors.Domain/Visitors/VisitorCreatedDomainEvent.cs

public sealed class VisitorCreatedDomainEvent(Guid visitorId) : DomainEvent
{
    public Guid VisitorId { get; } = visitorId;
}
```

Raise from entity:

```csharp
// File: Visitors.Domain/Visitors/Visitor.cs

public static Visitor Create(/* ... */)
{
    var visitor = new Visitor { /* ... */ };
    visitor.Raise(new VisitorCreatedDomainEvent(visitor.Id));
    return visitor;
}
```

### Value objects

Na explicit `ValueObject` base class. `record` estefade mishe:

```csharp
// File: Vehicles.Domain/Vehicles/VehiclePlate.cs

public record VehiclePlate
{
    public string Value { get; init; }
    public PlateType Type { get; init; }

    public static ErrorOr<VehiclePlate> CreatePlate(string number, PlateType type)
    {
        if (string.IsNullOrWhiteSpace(number))
            return VehicleErrors.NotAllowToEmpty("Plate");
        return type switch
        {
            PlateType.Normal => ValidateNormalPlate(number),
            PlateType.Diplomatic => ValidateDiplomaticPlate(number),
            // ...
        };
    }
}
```

`record` = value equality (content-based, na reference-based). Immutable (`init`). Factory validation. In ye value object-e.

### Factory methods + encapsulation

```csharp
// File: Personnels.Domain/Personnels/Personnel.cs

public sealed class Personnel : Entity, ISoftDeletable
{
    private Personnel() { }  // private constructor

    public Guid Id { get; private set; }                    // private setter
    public string PersonnelCode { get; private set; }
    public string FirstName { get; private set; }
    // ...

    public static async Task<ErrorOr<Personnel>> CreateAsync(
        /* required params */,
        IACLUserIdGenerator aclUserIdGenerator,
        CancellationToken ct)
    {
        var personnel = new Personnel { /* ... */ };
        // invariant checks
        if (/* bad */) return PersonnelErrors.Something;
        personnel.Raise(new PersonnelCreatedDomainEvent(personnel.Id));
        return personnel;
    }

    public ErrorOr<Updated> Update(/* ... */)
    {
        // invariant validation
        // update private fields
        Raise(new PersonnelUpdatedDomainEvent(Id));
        return Result.Updated;
    }
}
```

**Pattern:**
- `private` constructor → `new Personnel()` az birun compile error
- `private set` → property az birun change nemishe
- `static Create(Async)` → factory method ba validation
- `Update()` method → controlled mutation ba invariant check
- `Raise(event)` → domain event after successful mutation

**Architecture test enforce mikone:**

```csharp
// File: Visitors.ArchitectureTests/Domain/DomainTests.cs

public void Entities_ShouldHave_PrivateParameterlessConstructor() { /* ... */ }
public void Entities_ShouldOnlyHave_PrivateConstructors() { /* ... */ }
public void DomainEvent_ShouldHave_DomainEventPostfix() { /* ... */ }
```

### ISoftDeletable

```csharp
// Domain convention:
public interface ISoftDeletable
{
    bool IsDeleted { get; }
    DateTime? DeletedOnUtc { get; }
}
```

EF global query filter → `entity.IsDeleted == false` automatic. Soft delete = update, na physical delete.

---

## Application layer — chi daresh

### Command / Query interfaces

```csharp
// File: Dejban.Common.Application/Messaging/ICommand.cs

public interface ICommand : IRequest<ErrorOr<Success>>, IBaseCommand;
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
```

```csharp
// File: Dejban.Common.Application/Messaging/IQuery.cs

public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

Hame-ye command/query `ErrorOr<T>` return mikonan → explicit error handling, na exception (Day 15).

### Command example

```csharp
// Command:
public sealed record DeleteVisitorDocumentCommand(Guid VisitorId, Guid DocumentId) : ICommand;

// Handler:
internal sealed class DeleteVisitorDocumentCommandHandler(
    IVisitorRepository repo,
    IUnitOfWork unitOfWork)
    : ICommandHandler<DeleteVisitorDocumentCommand>
{
    public async Task<ErrorOr<Success>> Handle(DeleteVisitorDocumentCommand command, CancellationToken ct)
    {
        var visitor = await repo.GetAsync(command.VisitorId, ct);
        if (visitor is null) return VisitorErrors.NotFound(command.VisitorId);

        visitor.RemoveDocument(command.DocumentId);
        await unitOfWork.SaveChangesAsync(ct);
        return Result.Success;
    }
}
```

### Domain event handler → integration event

```csharp
// File: Personnels.Application/Personnels/CreatePersonnel/PersonnelCreatedDomainEventHandler.cs

internal sealed class PersonnelCreatedDomainEventHandler(ISender sender, IEventBus eventBus)
    : DomainEventHandler<PersonnelCreatedDomainEvent>
{
    public override async Task Handle(PersonnelCreatedDomainEvent domainEvent, CancellationToken ct)
    {
        // 1. Query full personnel data
        var result = await sender.Send(new GetPersonnelQuery(domainEvent.PersonnelId), ct);

        // 2. Map to integration event
        var mapped = result.Value.Adapt<PersonnelResponse>();

        // 3. Publish to RabbitMQ
        await eventBus.PublishAsync(new PersonnelCreated(/* fields */), ct);
    }
}
```

**Pattern:** Domain event (internal) → domain event handler → publish integration event (external).

### MediatR pipeline behaviors

```csharp
// File: Dejban.Common.Application/ApplicationConfiguration.cs

config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));  // outermost
config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));          // closest to handler
```

Har command/query az in 3 behavior rad mishe ghabl az handler.

---

## Infrastructure layer — chi daresh

### DbContext per module

8 ta DbContext, har kodum yek schema:

| module | schema | tables |
|---|---|---|
| Visitors | `visitors` | visitors, visit_schedules, sites, personnels, units, outbox_messages, inbox_messages |
| Personnels | `personnels` | personnels, sites, units, personnel_documents, ... |
| Vehicles | `vehicles` | vehicles, vehicle_groups, sites, ... |
| Armory | `armory` | weapons, weapon_assignments, sites, ... |
| CashLogistics | `cash_logistics` | cash_transfers, sites, ... |
| Inventory | `inventory` | warehouses, items, sites, units, ... |
| SecurityPatrols | `security_patrols` | patrol_routes, checkpoints, sites, ... |
| WeighBridge | `weigh_bridge` | weigh_records, sites, ... |

```csharp
// File: Visitors.Infrastructure/Database/VisitorsDbContext.cs

public sealed class VisitorsDbContext(/* ... */) : DbContext(options), IUnitOfWork, ITenantDbContext
{
    internal DbSet<Visitor> Visitors { get; set; }
    internal DbSet<Site> Sites { get; set; }         // read-model copy
    internal DbSet<Personnel> Personnels { get; set; } // read-model copy

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema(Schemas.Visitors);  // "visitors"
        modelBuilder.ApplyConfiguration(new VisitorConfiguration());
        modelBuilder.ApplyConfiguration(new OutboxMessageConfiguration());
        modelBuilder.ApplyConfiguration(new InboxMessageConfiguration());
        modelBuilder.ApplyTenantQueryFilters(this);
    }
}
```

**`internal DbSet`** — faghat Infrastructure access dare, na Presentation/Application.

**Schema constant:**

```csharp
// File: Visitors.Infrastructure/Database/Schemas.cs

internal static class Schemas
{
    internal const string Visitors = "visitors";
}
```

**Migration history ham schema-scoped:**

```csharp
options.UseNpgsql(...)
    .MigrationsHistoryTable(HistoryRepository.DefaultTableName, Schemas.Visitors);
```

### Repository

```csharp
// File: Visitors.Infrastructure/Visitors/VisitorRepository.cs

internal sealed class VisitorRepository(VisitorsDbContext context) : IVisitorRepository
{
    public async Task<Visitor?> GetAsync(Guid id, CancellationToken ct)
        => await context.Visitors
            .Include(v => v.Documents)
            .FirstOrDefaultAsync(v => v.Id == id, ct);

    public void Insert(Visitor visitor) => context.Visitors.Add(visitor);
}
```

`IVisitorRepository` to Application layer (interface), `VisitorRepository` to Infrastructure (implementation). DI wire mikone.

### Outbox / Inbox tables

Har module `outbox_messages` va `inbox_messages` table dare to khodesh schema. Quartz job per module.

### IUnitOfWork

```csharp
// DbContext khodesh IUnitOfWork implement mikone:
services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<VisitorsDbContext>());
```

Command handler `IUnitOfWork.SaveChangesAsync()` seda mizane → kole changes + outbox messages to yek transaction.

---

## Presentation layer — chi daresh

### IEndpoint — Minimal API

```csharp
// File: Dejban.Common.Presentation/Endpoints/IEndpoint.cs

public interface IEndpoint
{
    void MapEndpoint(IEndpointRouteBuilder app);
}
```

```csharp
// File: Visitors.Presentation/Visitors/VisitorDocuments.cs

internal sealed class VisitorDocuments : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        app.MapPost("/api/v{version:apiVersion}/Visitors/{visitorId:guid}/Documents",
            async (Guid visitorId, ISender sender, /* ... */) =>
            {
                var result = await sender.Send(new UploadVisitorDocumentCommand(visitorId, /* ... */));
                return result.Match(Results.Ok, CustomResults.Problem);
            })
            .RequireAuthorization()
            .WithTags(Tags.Visitors);
    }
}
```

### Endpoint discovery + mapping

```csharp
// File: Dejban.Common.Presentation/Endpoints/EndpointExtensions.cs

public static IServiceCollection AddEndpoints(this IServiceCollection services, params Assembly[] assemblies)
{
    // Scan assemblies for IEndpoint, register as Transient
}

public static IApplicationBuilder MapEndpoints(this WebApplication app)
{
    IEnumerable<IEndpoint> endpoints = app.Services.GetRequiredService<IEnumerable<IEndpoint>>();
    foreach (var endpoint in endpoints)
        endpoint.MapEndpoint(builder);
}
```

### Integration event handlers (ham to Presentation)

```csharp
// File: Visitors.Presentation/Sites/SiteCreatedIntegrationEventHandler.cs

public sealed class SiteCreatedIntegrationEventHandler(
    ISiteRepository siteRepository, IUnitOfWork unitOfWork)
    : IntegrationEventHandler<SiteCreated>
{
    public override async Task Handle(SiteCreated integrationEvent, CancellationToken ct)
    {
        if (await siteRepository.GetAsync(integrationEvent.SiteId, ct) is not null)
            return;  // idempotent

        var site = Site.Create(/* from event */);
        siteRepository.Insert(site);
        await unitOfWork.SaveChangesAsync(ct);
    }
}
```

**Chera to Presentation?** Chon integration event az birun miad (az dige module ya service). Presentation = external interface (HTTP + events).

---

## Read-model copy pattern

Har module `Site`, `Unit`, `Personnel` entity-e **khodesh** ra dare — na reference be dige module.

```
Personnels module: Site (full fields, source of truth)
    → PersonnelCreated event → RabbitMQ
Visitors module: Site (subset fields, read-model copy)
    → SiteCreated event → upsert to visitors.sites
Vehicles module: Site (subset fields, read-model copy)
    → SiteCreated event → upsert to vehicles.sites
```

**Chera copy?** Module boundary. Visitors DbContext faghat `visitors` schema ra midone. Na mitone `personnels.sites` ra query kone (even though haman DB-e). Copy = loose coupling.

**Trade-off:** Data duplication + eventual consistency. Site name avaz mishe → SiteUpdated event → all modules update copy. Ye lahze stale.

---

## Module registration — Dejban.Api

```csharp
// File: Dejban.Api/Program.cs

// 1. Assemblies
Assembly[] moduleApplicationAssemblies = [
    Dejban.Modules.Visitors.Application.AssemblyReference.Assembly,
    Dejban.Modules.Personnels.Application.AssemblyReference.Assembly,
    // ... all 8
];

// 2. Shared layers
builder.Services.AddApplication(moduleApplicationAssemblies);
builder.Services.AddInfrastructure(serviceName, consumers, endpoints,
    dbConnection, redis, config);
builder.Services.AddPresentation(config);

// 3. Per-module registration
builder.Services.AddVisitorsModule(config);
builder.Services.AddPersonnelsModule(config);
builder.Services.AddVehiclesModules(config);
builder.Services.AddSecurityPatrolsModule(config);
builder.Services.AddArmoryModule(config);
builder.Services.AddCashLogisticsModule(config);
builder.Services.AddInventoryModule(config);
builder.Services.AddWeighBridgeModule(config);

// 4. Pipeline
app.MapEndpoints();  // discover + map all IEndpoint from all modules
```

**Har `AddXxxModule`:**
1. DbContext + schema config
2. Repositories (scoped)
3. Domain event handlers + Scrutor idempotent decorator
4. Integration event handlers
5. Quartz inbox/outbox jobs
6. Options (outbox/inbox interval)
7. Endpoints (IEndpoint scan)

---

## Event flow — 2-stage pipeline

```
Entity.Create()
    → Raise(PersonnelCreatedDomainEvent)              ← domain event
    → SaveChanges
        → InsertOutboxMessagesInterceptor              ← outbox table (same tx)
    → ProcessOutboxJob (Quartz, every N seconds)
        → DomainEventHandlersFactory.Invoke()
        → PersonnelCreatedDomainEventHandler
            → eventBus.PublishAsync(PersonnelCreated)  ← integration event → RabbitMQ
    → IntegrationEventConsumer<PersonnelCreated>       ← other module
        → INSERT INTO visitors.inbox_messages          ← inbox table
    → ProcessInboxJob (Quartz, every N seconds)
        → IntegrationEventHandler<PersonnelCreated>
            → siteRepository.Insert(Personnel.Create()) ← read-model copy
            → unitOfWork.SaveChangesAsync()
    → IdempotentDomainEventHandler / IntegrationEventHandler
        → check outbox_consumers / inbox_consumers    ← dedup
```

**Idempotent:** har event ID track mishe. Duplicate process → skip. (Day 40 detail)

---

## Anti-pattern-ha va boundary violation-ha

### 1. Inventory → Personnels domain reference

```xml
<!-- Inventory.Domain.csproj -->
<ProjectReference Include="..\..\Personnels\Dejban.Modules.Personnels.Domain\..." />
```

```csharp
// Warehouse.cs
using Dejban.Modules.Personnels.Domain.Sites;
public Site Site { get; private set; } = null!;
```

EF ignore mikone (`builder.Ignore(e => e.Site)`), vali compile-time dependency hast. **Behtar:** Inventory khodesh `Site` type dashte bashe (mesle baghie module-ha).

### 2. Presentation → Infrastructure reference

Hame-ye module-ha: `Presentation.csproj` → refs `Common.Infrastructure`. Chon `IntegrationEventHandler` base class to Infrastructure-e. Clean Architecture violation (Presentation bayad faghat Application ra beshine).

### 3. Infrastructure → Presentation reference

`Infrastructure.csproj` → refs `Presentation.csproj`. Chon handler scan baraye integration event-ha to Presentation-e va Infrastructure bayad register-eshun kone. Circular-like dependency.

### 4. Architecture test gap

```csharp
// File: Dejban.ArchitectureTests/Layers/ModuleTests.cs
// otherModules array is EMPTY → test doesn't enforce zero cross-module deps!
```

Test bayad check kone ke Visitors.Domain az Personnels.Domain reference nadare. Alan check **nemikone**.

### 5. Reporting reads all schemas directly

Reporting service 9 ta DbContext register mikone ke haman production schema-ha ra mikhonan. Bypass mikone module API-ha. Read-only vali tight coupling.

### 6. Na AggregateRoot

Entity base dare vali `AggregateRoot` type nadare. Hame-ye entity-ha event raise mitonan — na faghat root. DDD purist in ra violation midone.

---

## Smell-ha

1. **Na formal AggregateRoot** — hame entity event raise mikone
2. **Inventory → Personnels domain reference** — cross-module compile dependency
3. **Presentation ↔ Infrastructure circular** — Clean Architecture violation
4. **Architecture test gap** — otherModules empty, cross-module deps na-checked
5. **Reporting direct schema read** — bypass module boundary
6. **Read-model copy maintenance** — 8 module × Site/Unit/Personnel copy = duplication
7. **Na domain service** — complex cross-entity logic kojast?
8. **Na specification pattern** — query logic to repository methods, na reusable
9. **Schema-only isolation** — yek DB, cross-schema `JOIN` technically possible (even if na used)
10. **Single deploy** — 8 module yek process, yek down = hame down
11. **Microservice-ha folder-based** — boundary enforce convention only, na compile-time
12. **Na contract testing** — integration event contract change = runtime failure

---

## 20 soal-e mosahebe

1. **Monolith vs Microservice?** — Monolith: yek deploy, sade. Micro: joda deploy, complex ops
2. **Modular monolith chie?** — Module boundary to yek process. Split later. Best of both
3. **Chera Dejban modular monolith?** — Team kuchik, shared DB ok, boundary lazem, ops sade
4. **Chera IdentityServer microservice?** — Security isolation, independent lifecycle, different scale
5. **Clean Architecture?** — Layer-ha be darun depend. Domain pure. Infrastructure outside
6. **Dependency rule?** — Domain → nothing. Application → Domain. Infra → App. Presentation → App
7. **Chera separate csproj per layer?** — Compile-time dependency enforcement. Na convention
8. **DDD Entity vs Value Object?** — Entity: identity (ID). VO: equality by value, immutable
9. **Aggregate Root?** — Entry point to aggregate. Consistency boundary. Transaction scope
10. **Domain Event chie?** — Chizi ke domain-e etefagh oftad. PersonnelCreated. Decouple
11. **Outbox pattern chie?** — Entity + event same tx. Background publish. Reliable messaging
12. **Chejori module-ha communicate mikonan?** — Integration event via RabbitMQ. Na direct call
13. **Read-model copy chie?** — Each module its own Site/Personnel copy. Eventually consistent
14. **Eventual consistency?** — Write → event → propagate → stale window. Trade-off
15. **CQRS chie?** — Separate read/write model. Command → write. Query → read
16. **Bounded context chie?** — Model boundary. "User" in Identity ≠ "User" in Billing
17. **Factory method?** — Static method on entity. Validation + creation + event raise
18. **IUnitOfWork?** — Save all changes atomically. DbContext implements it
19. **Chejori az modular monolith be microservice migrate mikoni?** — Extract module → own DB → own deploy → event same
20. **Anti-corruption layer?** — Translate between contexts. Integration event payload mapping

---

## Resume

**short:**

> Designed a hybrid architecture combining a modular monolith (8 Clean Architecture modules with schema-per-module isolation) and 7 independent microservices, communicating via MassTransit/RabbitMQ integration events with transactional outbox/inbox and read-model synchronization.

**bullets:**

- Architected 8-module modular monolith with compile-time enforced Clean Architecture (5 csproj per module: Domain, Application, Infrastructure, Presentation, IntegrationEvents)
- Implemented DDD tactical patterns: Entity base with domain events, Value Objects via records with factory validation, private constructors/setters for encapsulation
- Designed schema-per-module isolation (8 PostgreSQL schemas, 1 DB) with tenant query filters and schema-scoped migration history
- Built 2-stage event pipeline: domain events → outbox (same transaction) → Quartz publish → RabbitMQ → inbox → idempotent handler → read-model sync
- Separated 7 microservices (Identity, ACL, DCC, RequestTracker, Gate, Reporting) for security isolation, device integration, and independent scaling

**skills:** `Modular Monolith, Microservices, Clean Architecture, DDD, Bounded Context, Domain Events, Outbox/Inbox Pattern, Schema Isolation, CQRS, Event-Driven Architecture`

---

## File-haye mohem

| chi | koja |
|---|---|
| Entity base | `Dejban.Common.Domain/Entity.cs` |
| DomainEvent base | `Dejban.Common.Domain/DomainEvent.cs` |
| ICommand / IQuery | `Dejban.Common.Application/Messaging/ICommand.cs` |
| ApplicationConfiguration | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| InfrastructureConfiguration | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| OutboxInterceptor | `Dejban.Common.Infrastructure/Outbox/InsertOutboxMessagesInterceptor.cs` |
| IEndpoint | `Dejban.Common.Presentation/Endpoints/IEndpoint.cs` |
| Endpoint discovery | `Dejban.Common.Presentation/Endpoints/EndpointExtensions.cs` |
| VisitorsModule DI | `Visitors.Infrastructure/VisitorsModule.cs` |
| VisitorsDbContext | `Visitors.Infrastructure/Database/VisitorsDbContext.cs` |
| Schema constant | `Visitors.Infrastructure/Database/Schemas.cs` |
| Visitor entity | `Visitors.Domain/Visitors/Visitor.cs` |
| VehiclePlate VO | `Vehicles.Domain/Vehicles/VehiclePlate.cs` |
| Personnel factory | `Personnels.Domain/Personnels/Personnel.cs` |
| Domain event example | `Visitors.Domain/Visitors/VisitorCreatedDomainEvent.cs` |
| Domain event handler | `Personnels.Application/CreatePersonnel/PersonnelCreatedDomainEventHandler.cs` |
| Integration handler | `Visitors.Presentation/Sites/SiteCreatedIntegrationEventHandler.cs` |
| Inbox consumer | `Visitors.Infrastructure/Inbox/IntegrationEventConsumer.cs` |
| Idempotent decorator | `Visitors.Infrastructure/Outbox/IdempotentDomainEventHandler.cs` |
| Event contracts | `Common/EventBus/Contracts/Events/` |
| Architecture tests | `Visitors.ArchitectureTests/Domain/DomainTests.cs` |
| Module test (gap) | `Dejban.ArchitectureTests/Layers/ModuleTests.cs` |
| Dejban.Api Program | `Dejban.Api/Program.cs` |
| Reporting DbContexts | `Reporting/Infrastructure/Persistence/VisitorsDbContext.cs` |
| Inventory violation | `Inventory.Domain/Warehouses/Warehouse.cs` |

---

*Day 10 tamum. Ba'd: Day 11 — CQRS + MediatR + Pipeline Behaviors. Fehrest: [README.md](./README.md).*
