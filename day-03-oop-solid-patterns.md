# Day 03 — OOP + SOLID + Design Patterns

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

OOP chahar soton dare: **encapsulation**, **abstraction**, **inheritance**, **polymorphism**. SOLID panj ghanun-e ke class-ha ra tamiz va ghabel-e taghir negah midare. Design pattern-ha rah-hal-haye tekrari-an ke hezaran developer ghabl az to emtehan kardan. In se ta ba ham column-e interview-e senior-an — hame ja miporsan — vali inja faghat teoria nist: to Dejban hame-ye ina zendegi daran.

Mesal-e sari': entity-e `Personnel` encapsulation dare (private setter, factory method, SoftDelete ba domain event). `IEndpoint` + auto-discovery OCP-e (class-e jadid bezar, startup ra avaz nakon). MediatR pipeline behaviors Chain of Responsibility-an. `IdempotentDomainEventHandler` ba Scrutor Decorator-e. `IDeviceSyncStrategy` + factory Strategy-e baraye ZK/Tiam/Virdi. In fasl WORLD ra midahad, ba’d hamin pattern-ha ra ba path-e exact pin mikone.

---

# BAKHSH-E AVAL: WORLD — OOP, SOLID, patterns to donya

## 4 soton-e OOP

### 1. Encapsulation

Encapsulation yani data va behavior ra to yek ja negah dari, va dastor-e biruni ra az joziat makhfi koni — biruni faghat az **public API** estefade kone. Hadaf-e vaghe'i in nist ke «field private bashe»; hadaf in-e ke **state-e object hamishe valid bemoone**.

Be zaban-e sade: entity-e `Personnel` field-e `IsDeleted` dare. Age biruni dorost `personnel.IsDeleted = true` bezane, domain event raise nemishe, `DeletedAt` set nemishe, `DeletedBy` gom mishe. Pas field ra `private set` mikoni va ye method `SoftDelete(string deletedBy)` midahi ke **hame-ye kar** ra yekja mikone.

```csharp
// BAD — field-e public, biruni har kari mikhad mikone
public bool IsDeleted { get; set; }

// GOOD — private set, faghat az method-e khode entity avaz mishe
public bool IsDeleted { get; private set; }
public void SoftDelete(string deletedBy)
{
    if (IsDeleted) return;
    IsDeleted = true;
    DeletedAt = DateTime.UtcNow;
    Raise(new PersonnelDeletedDomainEvent(Id, deletedBy));
}
```

**Encapsulation ≠ faghat private.** Mani-ash inke **state-e object hamishe valid-e** — hich rahi nist ke biruni state ra beshkone. Constructor validate mikone, method-ha business rule enforce mikonan.

### Access modifier-ha

| modifier | ki mibine |
|---|---|
| `public` | hameja |
| `private` | faghat haman class |
| `protected` | haman class + derived |
| `internal` | haman assembly |
| `protected internal` | assembly + derived |
| `private protected` | haman assembly + derived |
| `file` (.NET 8+) | haman file |

Dar in stack: repository implementation-ha `internal sealed class`-an — yani faghat haman assembly (Infrastructure) mibine; Application layer faghat interface ra midone.

### Record vs class

`record` immutable by default-e (az .NET 5). Baraye DTO, command, event ideal-e. `class` baraye entity ke state avaz mishe.

```csharp
// Command — record, immutable, ba hash/equality
public record CreatePersonnelCommand(string FirstName, string LastName, ...) : ICommand<Guid>;

// Entity — class, mutable state ba encapsulation
public sealed class Personnel : Entity { ... }
```

---

### 2. Abstraction

Joziat ra poshte ye contract (interface ya abstract class) makhfi kon. Consumer faghat "chi" ra midone, na "chejori."

```csharp
// Consumer faghat in ra midone:
public interface IPersonnelRepository
{
    Task<Personnel?> GetAsync(Guid id, CancellationToken ct);
    void Insert(Personnel personnel);
}

// Implementation-e vagheyi EF dare, SQL mizane, connection pool estefade mikone.
// Handler hichkodom az ina ra nemidone va **nabayd** ham bedone.
```

**Chera mohem?** Farda mitoni implementation ra avaz koni (masalan az EF be Dapper, ya mock to test) bedune avaz kardan-e handler.

**Interface vs abstract class:**

| | Interface | Abstract class |
|---|---|---|
| state (field) | na (ta C# 8) | bale |
| multiple inheritance | bale | na |
| default implementation | C# 8+ | bale |
| constructor | na | bale |
| versioning | **breaking** — method ezafe kon = compile error | method-e jadid virtual + default OK |

Rule-e 2026: interface baraye contract. Abstract class baraye shared behavior + state (masalan `Entity` ba `_domainEvents` list).

---

### 3. Inheritance

Ye class az dige-i extend kone va behavior/state-esh ra beire.

```
Entity (abstract)
  ├── Personnel : ISiteEntity, ISoftDeletable
  ├── Visitor : ISiteEntity, ISoftDeletable
  ├── VisitSchedule : ISiteEntity, ISoftDeletable
  ├── Weapon : ISiteEntity, ISoftDeletable
  └── ...
```

`Entity` yek kar dare: domain event-ha ra jam mikone:

```csharp
public abstract class Entity
{
    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyCollection<IDomainEvent> DomainEvents => [.. _domainEvents];
    protected void Raise(IDomainEvent domainEvent) => _domainEvents.Add(domainEvent);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

Har entity `Raise(new PersonnelCreatedDomainEvent(...))` seda mizane. Outbox interceptor-e EF `DomainEvents` ra mikhone va persist mikone.

**`sealed`** — `Personnel` sealed-e. Yani **hichki azash derive nakone**. Chera? Entity-e domain aggregate nist ke subclass bekhad. Performance ham behtar-e (JIT devirtualize mikone).

**Marker interface** — `ISiteEntity` va `ISoftDeletable` field-e `SiteId` va `IsDeleted` ra tarif mikonan. Inheritance nistan, vali polymorphism-e interface midan:

```csharp
public interface ISiteEntity { Guid SiteId { get; } }
public interface ISoftDeletable { bool IsDeleted { get; } }
```

EF query filter **hame-ye** `ISoftDeletable`-ha ra filter mikone — type ra nemidone, faghat interface ra.

**Composition over inheritance** — in stack az inheritance kam estefade mikone (faghat `Entity` base). Aksar-e reuse az **interface + DI** miyad. In World-best-practice-e: "Prefer composition over inheritance."

---

### 4. Polymorphism

Yek contract, chand piade-sazi. Do jur:

**Subtype polymorphism (runtime):**

```csharp
// Handler-e domain event — hame IDomainEventHandler<T>-an:
DomainEventHandler<PersonnelCreatedDomainEvent>
DomainEventHandler<PersonnelUpdatedDomainEvent>
DomainEventHandler<PersonnelDeletedDomainEvent>

// Outbox processor hame ra yeksan seda mizane:
await handler.Handle(domainEvent, cancellationToken);
```

**Interface polymorphism:**

```csharp
IDeviceSyncStrategy strategy = factory.Create(DeviceBrands.ZK);
await strategy.GetUsersFromDeviceAsync(device);
// ZKDeviceSyncStrategy, TiamDeviceSyncStrategy, VirdiDeviceSyncStrategy
// caller farqi nadare kodom-e
```

**Ad-hoc polymorphism (overloading):**

```csharp
// Method-e yeki, parameter farq:
Task<Personnel?> GetAsync(Guid id, CancellationToken ct);
Task<Personnel?> GetWithDocumentsAsync(Guid id, CancellationToken ct);
```

In overloading nist (esm farq dare), vali concept-e yeki-e: **behavior-e motefavet based on context.**

**Generics (parametric polymorphism):**

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>;
// ICommand<Guid>, ICommand<PersonnelResponse>, ICommand<Success>
// Yek interface, har type
```

---

## SOLID — 5 ghanun-e kamel

SOLID ye checklist-e design-e: age class-ha ra ba in 5 ghanun check koni, taghir-e feature kamtar cascade mikone. Har ghanun ra ba mesal-e Dejban bekhun — mosahebe ham hamin-e: theory + mesal-e vaghe'i.

### S — Single Responsibility Principle

**Ye class bayad faghat yek dalil baraye avaz shodan dashte bashe.**

Be zaban-e sade: ye class yek kar mikone. Age do dalil baraye avaz shodan dashte bashe (masalan business logic + serialization), tekke-ash kon. Interview tip: SRP ra **nagoo** «ye method yek kar» — bego «One reason to change.» Handler avaz mishe age business logic avaz she; Repository avaz mishe age data store avaz she — ina joda-an.

Dorost:

- `CreatePersonnelCommandHandler` — faghat orchestration-e create
- `PersonnelRepository` — faghat data access
- `CreatePersonnelCommandValidator` — faghat validation
- `PersonnelCreatedDomainEventHandler` — faghat reaction be event

Ghalat:

- `IclockController` (~1700 khat) — ZK protocol parsing + DB access + device sync + logging + response building. In 5 ta dalil baraye avaz shodan dare.

---

### O — Open/Closed Principle

**Baraye extension baz, baraye modification baste.**

Yani: feature-e jadid ra ba **ezafe kardan-e code-e jadid** biyar, na ba **avaz kardan-e code-e mojud**.

Behtarin mesal: **`IEndpoint`** plugin system:

```csharp
// EndpointExtensions — yek bar neveshte shode:
assemblies.SelectMany(a => a.GetTypes())
    .Where(type => type.IsAssignableTo(typeof(IEndpoint)))
    .Select(type => ServiceDescriptor.Transient(typeof(IEndpoint), type));
```

Module-ye jadid mikhay? Ye class-e jadid ke `IEndpoint` implement mikone **bezar**. `EndpointExtensions` ra **avaz nakon**. In OCP-e.

Mesal-e dige: **Pipeline behaviors:**

```csharp
config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
```

Cross-cutting concern-e jadid (masalan caching)? Ye behavior-e jadid ezafe kon. Handler-ha ra avaz nakon.

Mesal-e dige: **Device sync strategy:**

Brand-e jadid? `IDeviceSyncStrategy`-e jadid + case to factory. Caller code avaz nemishe.

---

### L — Liskov Substitution Principle

**Subtype bayad be jaye parent-esh ghabel-e estefade bashe bedune shekastan-e behavior.**

Be zaban-e sade: age `FakeTenantContext` be jaye `ITenantContext` bezari, program bayad dorost kar kone.

```csharp
// Production:
services.AddScoped<ITenantContext, TenantContext>();

// Test:
services.AddScoped<ITenantContext>(sp => new FakeTenantContext {
    SiteIds = [testSiteId],
    IsSuperAdmin = true
});
```

Hame-ye DbContext-ha va handler-ha `ITenantContext` ra mesle ghabl estefade mikonan. `FakeTenantContext` LSP ra ne'mat mikone.

**Naghz-e LSP — classic mesal:**

```csharp
class Rectangle { virtual Width, Height }
class Square : Rectangle { override Width → sets both }
```

Code ke `Width = 5; Height = 10; Assert Area == 50` ba Square fail mikone. Square **nabayad** az Rectangle derive kone.

**To in stack:** `Entity` abstract-e. `Personnel` sealed-e. Hichki az `Personnel` derive nemikone → LSP violation impossible.

---

### I — Interface Segregation Principle

**Client nabayad majbur bashe be interface-i ke estefade-ash nemikone.**

Interface-e koochik va focused behtar az interface-e bozorg-e:

| Interface | Method count | Chie |
|---|---|---|
| `IDateTimeProvider` | 1 property | faghat clock |
| `IUnitOfWork` | 2 method | faghat persistence boundary |
| `ISiteEntity` | 1 property | faghat tenant marker |
| `ISoftDeletable` | 1 property | faghat soft delete marker |
| `IPersonnelRepository` | ~5 method | faghat Personnel data access |

**Moghayese:** GateServer `IRepositoryPattern<T>` — generic CRUD baraye hame entity. Client-i ke faghat `GetById` mikhad, majbur-e `Create`, `Delete`, `Update` ra ham bebine. In fat interface-e — naghz-e ISP.

**Rule:** interface-e koochik ba esm-e daqiq. Na `IRepository` baraye hame chiz.

---

### D — Dependency Inversion Principle

**Module-e bala-dasti be abstraction vabaste bashe, na be joziat.**

```csharp
// Handler (Application layer — bala) vabaste be INTERFACE:
internal sealed class CreatePersonnelCommandHandler(
    IPersonnelRepository personnelRepository,  // abstraction
    IUnitOfWork unitOfWork,                     // abstraction
    IACLUserIdGenerator aclUserIdGenerator)     // abstraction

// Implementation (Infrastructure layer — paeen):
internal sealed class PersonnelRepository(PersonnelsDbContext context) : IPersonnelRepository
```

Handler **aslan** `DbContext` ra nemibine. Age farda Dapper bezani, handler avaz nemishe.

**Registration:**

```csharp
services.AddScoped<IPersonnelRepository, PersonnelRepository>();
services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<PersonnelsDbContext>());
```

In **Dependency Injection** (DI) container-e ASP.NET-e. DIP principle-e, DI mechanism-e.

**Chera `PersonnelsDbContext` IUnitOfWork-e?** Chon SaveChanges roye DbContext-e. Handler `IUnitOfWork.SaveChangesAsync()` seda mizane — nemidone EF-e, SQL-e, ya chi.

---

## Design Patterns — guide-e kamel

Pattern yani «rah-hal-e tekrari ba esm». Na inke harja pattern bezani — vali age interview beperse Repository/Mediator/Strategy, bayad ba mesal-e Dejban javab bedi. Inja 11 ta pattern-e asli + chand ta ke inja kam/nist.

### 1. Repository Pattern

**Chie?** Layer-e beyn-e domain va data access. Domain faghat interface ra midone — yani handler `DbContext` ra nemibine.

**World mesal:**

```csharp
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(Guid id);
    void Add(Order order);
}

internal class OrderRepository(DbContext ctx) : IOrderRepository
{
    public Task<Order?> GetByIdAsync(Guid id) => ctx.Orders.FindAsync(id).AsTask();
    public void Add(Order order) => ctx.Orders.Add(order);
}
```

**Dejban mesal:** `IPersonnelRepository` / `PersonnelRepository`. Module-specific, na generic.

**Debate-ye World:** "Repository roye EF lazem-e?" Do camp:
- **Bale:** test-e sade-tar, DIP, domain clean.
- **Na:** EF khodesh repository/UoW-e. Double abstraction.

In stack: **bale** estefade mikone — va in to mosahebe khoob-e: "We use thin repositories for testability and to keep domain logic free of EF concerns."

---

### 2. Unit of Work Pattern

**Chie?** Hame-ye taghirat ra to yek transaction jam mikone va yekja commit mikone.

```csharp
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
```

EF `DbContext` khodesh UoW-e — change tracker taghirat ra track mikone, `SaveChanges` yek transaction commit mikone.

Handler flow:

```csharp
var personnel = await Personnel.CreateAsync(...);
personnelRepository.Insert(personnel);  // track, na save
await unitOfWork.SaveChangesAsync(ct);  // hame yekja commit + outbox
```

---

### 3. Mediator Pattern (MediatR)

**Chie?** Object-ha mostaghim ba ham sohbat nakonan. Az ye vasete (mediator) rad mishan.

Endpoint `ISender.Send(command)` → MediatR → handler. Endpoint handler ra **nemishnase**. Handler endpoint ra nemishnase.

```csharp
// Endpoint:
var result = await sender.Send(new CreatePersonnelCommand(...));

// Handler (to assembly-e dige):
internal sealed class CreatePersonnelCommandHandler : ICommandHandler<CreatePersonnelCommand, Guid>
{
    public async Task<ErrorOr<Guid>> Handle(CreatePersonnelCommand request, CancellationToken ct) { ... }
}
```

MediatR **reflection** ba peida kardan-e handler. Yek `IRequest<T>` → yek handler.

**CQRS** (Command Query Responsibility Segregation) roye in pattern savar-e:
- `ICommand<T>` → write (side-effect)
- `IQuery<T>` → read (safe)

---

### 4. Chain of Responsibility (Pipeline Behaviors)

**Chie?** Request az ye zanjire-ye handler-ha rad mishe. Har halqe mitone process kone ya be ba'di pass kone.

MediatR `IPipelineBehavior<TRequest, TResponse>`:

```csharp
// Validation behavior:
public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
{
    var failures = validators.Select(v => v.Validate(request)).Where(f => f.IsValid == false);
    if (failures.Any()) return errors;
    return await next();  // pass be handler ya behavior-e ba'di
}
```

Zanjir:

```
Request → ExceptionHandling → Logging → Validation → Handler → Response
```

Cross-cutting concern (logging, validation, exception) bedune avaz kardan-e handler.

---

### 5. Decorator Pattern (Scrutor)

**Chie?** Ye object ra ba ye wrapper-e ba behavior-e ezafe wrap kon, bedune avaz kardan-e khode object.

```csharp
// Original handler:
DomainEventHandler<PersonnelCreatedDomainEvent>

// Decorated (idempotent):
IdempotentDomainEventHandler<PersonnelCreatedDomainEvent>
    └── wraps → DomainEventHandler<PersonnelCreatedDomainEvent>
```

Scrutor:

```csharp
services.Decorate(domainEventHandler, closedIdempotentHandler);
```

`IdempotentDomainEventHandler`:

```csharp
internal sealed class IdempotentDomainEventHandler<TDomainEvent>(
    IDomainEventHandler<TDomainEvent> decorated,  // original handler
    PersonnelsDbContext dbContext)
    : DomainEventHandler<TDomainEvent>
{
    public override async Task Handle(TDomainEvent domainEvent, CancellationToken ct)
    {
        // age ghablan process shode, skip
        if (await OutboxConsumerExistsAsync(...)) return;
        // vagarna original ra seda bezan
        await decorated.Handle(domainEvent, ct);
        // va yas kon ke process shode
        await InsertOutboxConsumerAsync(...);
    }
}
```

**Farq ba inheritance:** inheritance class-e jadid misaze. Decorator-e motefavet ra mitoni **runtime** compose koni. Mesle lego.

---

### 6. Strategy Pattern

**Chie?** Algorithm-e motefavet ra runtime entekhab kon.

```csharp
public interface IDeviceSyncStrategy
{
    Task<ErrorOr<Success>> GetUsersFromDeviceAsync(Device device);
    Task<ErrorOr<Success>> SyncUsersToDeviceAsync(Device device, ...);
}
```

Har brand implementation-e khodesh:

- `ZKDeviceSyncStrategy` — SDK-e ZK, COM, STA thread
- `TiamDeviceSyncStrategy` — gRPC, SemaphoreSlim
- `VirdiDeviceSyncStrategy` — SDK-e Virdi

DCC ham: `IFileStorage` → `LocalFileStorage` vs `S3FileStorage`.

---

### 7. Factory Pattern

**Chie?** Object-sazi ra be ye method/class delegate kon.

**Simple Factory — device sync:**

```csharp
public IDeviceSyncStrategy Create(DeviceBrands brand) => brand switch
{
    DeviceBrands.Virdi => serviceProvider.GetRequiredService<VirdiDeviceSyncStrategy>(),
    DeviceBrands.ZK    => serviceProvider.GetRequiredService<ZKDeviceSyncStrategy>(),
    DeviceBrands.Tiam  => serviceProvider.GetRequiredService<TiamDeviceSyncStrategy>(),
    _ => throw new ArgumentOutOfRangeException(...)
};
```

**Static Factory Method — entity:**

```csharp
public static async Task<Personnel> CreateAsync(
    string personnelCode, string firstName, ...,
    IACLUserIdGenerator aclUserIdGenerator)
{
    var personnel = new Personnel { Id = Guid.NewGuid(), ... };
    personnel.Raise(new PersonnelCreatedDomainEvent(personnel.Id));
    return personnel;
}
```

Constructor-e `Personnel` **private**-e — faghat az `CreateAsync` / `CreateSuperAdminAsync` mishe sakhte. In invariant-ha ra enforce mikone (masalan ACLUserId generate she).

**Farq-e Factory Method vs Abstract Factory:**

- Factory Method: ye method ye object misaze
- Abstract Factory: ye family az object-ha misaze (masalan `IUIFactory` → `WinButton + WinTextbox` ya `MacButton + MacTextbox`)

In stack factory method dare, abstract factory nadare.

---

### 8. Observer / Event Pattern

**Chie?** Vaghti chizi etefagh miofte, interested party-ha motale' mishan bedune coupling-e mostaghim.

Domain entity event raise mikone:

```csharp
personnel.Raise(new PersonnelCreatedDomainEvent(personnel.Id));
```

Outbox processor (observer) event ra peida mikone va handler-ha ra seda mizane:

```csharp
// Domain event handler — dakhele haman module:
PersonnelDeletedDomainEventHandler → publish PersonnelSoftDeleted (integration event)

// Integration event handler — module-ye dige:
PersonnelSoftDeletedIntegrationEventHandler (to Visitors module) → soft-delete copy
```

Do sath event:
1. **Domain event** — dakhele aggregate boundary (haman module, haman transaction)
2. **Integration event** — beyn-e module-ha (MassTransit / inbox)

---

### 9. Options Pattern

**Chie?** Configuration ra strongly-typed bind kon be ye class.

```csharp
public class OutboxOptions
{
    public int IntervalInSeconds { get; init; }
    public int BatchSize { get; init; }
}
```

Registration:

```csharp
services.Configure<OutboxOptions>(configuration.GetSection("Visitors:Outbox"));
```

Injection:

```csharp
internal sealed class ProcessOutboxJob(IOptions<OutboxOptions> outboxOptions) : IJob
{
    // outboxOptions.Value.BatchSize
}
```

**Chera na `configuration.GetValue<int>("BatchSize")`?** Type-safe, testable, refactorable.

**IOptions vs IOptionsSnapshot vs IOptionsMonitor:**

| | lifetime | reload |
|---|---|---|
| `IOptions<T>` | singleton | na |
| `IOptionsSnapshot<T>` | scoped | bale (per request) |
| `IOptionsMonitor<T>` | singleton | bale (callback) |

Scoped handler-ha `IOptions` estefade mikonan (config az startup mikhone, restart baraye change).

---

### 10. Template Method Pattern

**Chie?** Base class skeleton-e algorithm ra tarif mikone, subclass step-ha ra override mikone.

```csharp
public abstract class DomainEventHandler<TDomainEvent> : IDomainEventHandler<TDomainEvent>
{
    // Template: cast + delegate to abstract
    public Task Handle(IDomainEvent domainEvent, CancellationToken ct) =>
        Handle((TDomainEvent)domainEvent, ct);

    // Subclass in ra override mikone:
    public abstract Task Handle(TDomainEvent domainEvent, CancellationToken ct);
}
```

Haman `IntegrationEventHandler<T>` ham.

---

### 11. Result Pattern (Railway-oriented)

**Chie?** Be jaye throw-e exception, natije ra **explicit** return kon.

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>;
```

`ErrorOr<T>` az library-e ErrorOr miyad. Handler ya `T` barmigardone (success), ya `List<Error>` (failure). Exception nist — flow-e explicit-e.

```csharp
// Handler:
return personnel.Id;  // success → ErrorOr<Guid>.From(id)
return Errors.Personnel.NotFound;  // failure

// Endpoint:
result.Match(
    id => Results.Ok(new { id }),   // success path
    ApiResults.Problem              // failure → ProblemDetails
);
```

**Chera na exception?** Exception baraye **exceptional** cases (network down). Business error (duplicate national code) expected-e — flow control ba exception anti-pattern-e.

---

### Pattern-haye digei ke to donya hastan vali inja kam/nistan

- **Singleton** — DI container handle mikone (`AddSingleton`). Dasti singleton pattern lazem nist.
- **Builder** — kam. `WebApplicationBuilder`, `Host.CreateDefaultBuilder`. Entity builder nadare (factory method dare).
- **Adapter** — `AccessTokenQueryMiddleware` ye jur adapter-e: query string ra be header adapt mikone.
- **Proxy** — YARP khodesh proxy-e. To code-e C# proxy pattern kam.
- **Specification** — Ardalis.Specification library. In stack query-ha LINQ-e dasti, specification pattern formal nist (jox `Specification` value object to Armory).
- **State Machine** — kam. Entity status az string-e (`"Open"`, `"Closed"`). Formal state pattern nist.
- **Visitor** — hich.
- **Flyweight** — hich.
- **Bridge** — hich.
- **Abstract Factory** — hich.

---

# BAKHSH-E DOVOM: DEJBAN — OOP va patterns to in proje

In bakhsh neshan mide hamin SOLID/pattern-ha koja pin shodan — az `Entity` base ta Scrutor decorator. Aval az asos shoru' kon: domain event infrastructure ye class-e koochik-e.

## Entity base class — hame-ye entity-ha

```csharp
public abstract class Entity
{
    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyCollection<IDomainEvent> DomainEvents => [.. _domainEvents];
    protected void Raise(IDomainEvent domainEvent) => _domainEvents.Add(domainEvent);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

- `abstract` — mishe derive kard, na instantiate
- `_domainEvents` **private** — biruni add/remove nemitone
- `DomainEvents` public **read-only** — biruni faghat mikhone
- `Raise` **protected** — faghat khode entity va derived seda mizane
- `ClearDomainEvents` public — outbox interceptor ba'd az save pak mikone

In yek class-e 20 khatti ke kole domain event infrastructure-e Dejban ra drive mikone. SRP: faghat event lifecycle.

---

## Personnel entity — mesal-e kamel-e encapsulation

```csharp
public sealed class Personnel : Entity, ISiteEntity, ISoftDeletable
{
    private Personnel() { }  // EF needs it, nobody else

    public Guid Id { get; private set; }
    public string FirstName { get; private set; } = null!;
    public bool IsDeleted { get; private set; }
    // ... 30+ property, hame private set

    public static async Task<Personnel> CreateAsync(...) { ... }
    public static async Task<Personnel> CreateSuperAdminAsync(...) { ... }
    public void Update(...) { ... }
    public void SoftDelete(string deletedBy) { ... }
    public void Restore() { ... }
    public void AddEmploymentHistory(...) { ... }
    public PersonnelDocument AddDocument(...) { ... }
    public bool RemoveDocument(Guid documentId) { ... }
}
```

**Pattern-ha-ye in ye class:**

1. **Private constructor** — `new Personnel()` az biruni compile nemishe. Faghat `CreateAsync`.
2. **Private setters** — `FirstName` ra biruni set nemikone. Faghat `Update()`.
3. **Factory method** — `CreateAsync` invariant-ha ra enforce mikone (ACLUserId generate). Do factory: normal + superadmin.
4. **Behavior method** — `Update()` aval check mikone aya chizi avaz shode. Age na → **hich event raise nemishe**. In optimization-e ke domain-e.
5. **Domain events** — `Raise(new PersonnelCreatedDomainEvent(...))` to factory. `Raise(new PersonnelUpdatedDomainEvent(...))` to Update.
6. **`sealed`** — derive mamnoo'.
7. **ISiteEntity + ISoftDeletable** — marker interface baraye query filter.

**Smell-e koochik:** `AvatarImage` va `SignatureImage` `public set`-an (`{ get; set; }`), hame-ye baghie `private set`. In inconsistency momkene dalili dashte bashe (file upload joda az entity update), vali age bakhay tamiz bashe bayad method dashte bashe (`SetAvatar(string path)`).

---

## CQRS — Command va Query joda

```csharp
// Command — write:
public interface ICommand : IRequest<ErrorOr<Success>>, IBaseCommand;
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;

// Query — read:
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

**Command handler:**

```csharp
internal sealed class CreatePersonnelCommandHandler(
    IPersonnelRepository personnelRepository,
    IUnitOfWork unitOfWork,
    IACLUserIdGenerator aclUserIdGenerator)
    : ICommandHandler<CreatePersonnelCommand, Guid>
{
    public async Task<ErrorOr<Guid>> Handle(CreatePersonnelCommand request, CancellationToken ct)
    {
        var personnel = await Personnel.CreateAsync(..., aclUserIdGenerator);
        personnelRepository.Insert(personnel);
        await unitOfWork.SaveChangesAsync(ct);
        return personnel.Id;
    }
}
```

**Query handler:**

```csharp
internal sealed class GetPersonnelsQueryHandler(...)
    : IQueryHandler<GetPersonnelsQuery, PagedList<PersonnelResponse>>
{
    // AsNoTracking, Select projection, no side-effects
}
```

Command: tracked entity, SaveChanges, domain events. Query: AsNoTracking, projection, no mutation.

---

## IEndpoint — OCP to amal

```csharp
public interface IEndpoint
{
    void MapEndpoint(IEndpointRouteBuilder app);
}
```

Auto-discovery:

```csharp
assemblies.SelectMany(a => a.GetTypes())
    .Where(type => type.IsAssignableTo(typeof(IEndpoint)))
    .Select(type => ServiceDescriptor.Transient(typeof(IEndpoint), type));
```

Module-ye jadid: ye class bezar ke `IEndpoint` implement mikone. Tamum. Startup code avaz nemishe. OCP.

---

## Pipeline behaviors — Chain of Responsibility to amal

```csharp
services.AddMediatR(config =>
{
    config.RegisterServicesFromAssemblies(moduleAssemblies);
    config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
    config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
    config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
});
```

Har request az in zanjir rad mishe:
1. Exception handling (catch + log)
2. Request logging (start/end/duration)
3. Validation (FluentValidation)
4. **Handler** (business logic)

Behavior-e jadid (caching, authorization) = class-e jadid + `AddOpenBehavior`. Handler-ha avaz nemishan.

---

## Device sync — Strategy + Factory to amal

```csharp
// Factory:
public IDeviceSyncStrategy Create(DeviceBrands brand) => brand switch
{
    DeviceBrands.Virdi => serviceProvider.GetRequiredService<VirdiDeviceSyncStrategy>(),
    DeviceBrands.ZK => serviceProvider.GetRequiredService<ZKDeviceSyncStrategy>(),
    DeviceBrands.Tiam => serviceProvider.GetRequiredService<TiamDeviceSyncStrategy>(),
};

// Caller:
var strategy = factory.Create(device.Brand);
await strategy.SyncUsersToDeviceAsync(device, users);
```

Brand-e jadid = strategy-e jadid + case to factory. Caller avaz nemishe.

DCC ham hamin: `IFileStorage` → `LocalFileStorage` / `S3FileStorage`. Config set mikone kodom:

```csharp
if (string.Equals(storageProvider, "S3"))
    services.AddSingleton<IFileStorage>(sp => sp.GetRequiredService<S3FileStorage>());
else
    services.AddSingleton<IFileStorage>(sp => sp.GetRequiredService<LocalFileStorage>());
```

---

## Decorator — IdempotentDomainEventHandler

Scrutor `services.Decorate(...)` — original handler ra wrap mikone:

```csharp
internal sealed class IdempotentDomainEventHandler<TDomainEvent>(
    IDomainEventHandler<TDomainEvent> decorated,
    PersonnelsDbContext dbContext)
    : DomainEventHandler<TDomainEvent>
{
    public override async Task Handle(TDomainEvent domainEvent, CancellationToken ct)
    {
        if (await OutboxConsumerExistsAsync(...)) return;  // ghablan process shode
        await decorated.Handle(domainEvent, ct);            // original
        await InsertOutboxConsumerAsync(...);                // yas kon
    }
}
```

DI container vaghti `IDomainEventHandler<PersonnelCreated>` resolve mikone, `IdempotentDomainEventHandler` mide ke dakhel-esh original handler ra dare. **Transparent** — handler aslan nemidone decorated shode.

---

## Module system — Plugin architecture

Har module (`VisitorsModule`, `PersonnelsModule`, `ArmoryModule`, ...) ye static method `AddXxxModule` dare ke DI, endpoints, consumers, outbox/inbox ra register mikone:

```csharp
public static class PersonnelsModule
{
    public static IServiceCollection AddPersonnelsModule(this IServiceCollection services, IConfiguration config)
    {
        services.AddInfrastructure(config);
        // DbContext, repositories, outbox, inbox, consumers, decorators
        return services;
    }
}
```

**OCP:** module-ye jadid = file-e jadid. `Program.cs` faghat `.AddXxxModule()` ra seda mizane.

---

## Marker interface-ha — runtime filtering

```csharp
public interface ISiteEntity { Guid SiteId { get; } }
public interface ISoftDeletable { bool IsDeleted { get; } }
```

EF query filter hame-ye entity-hayi ke in interface ra daran filter mikone — runtime polymorphism:

```csharp
foreach (var entityType in modelBuilder.Model.GetEntityTypes())
{
    if (typeof(ISoftDeletable).IsAssignableFrom(entityType.ClrType))
        // apply WHERE is_deleted = false
}
```

---

## Chi **nadari** (ta resume dorough nashe)

- Abstract Factory pattern
- State pattern formal (entity status string-e)
- Specification pattern formal (Ardalis.Specification)
- Visitor pattern
- Builder pattern (baraye entity)
- Domain service class (domain logic dakhele entity + handler-e)
- Value object formal (Specification to Armory hast, vali baghie kam)
- Rich domain model (entity-ha behavior daran, vali gahi anemic — faqat getter/setter + handler logic)

---

## Smell-ha

1. **`AvatarImage` / `SignatureImage` public set** — inconsistent ba baghie-ye private set
2. **`IclockController` ~1700 khat** — naghz-e SRP. Bayad split she
3. **Entity-e `Update` 30+ parameter** — bayad command object ya parameter object bashe
4. **GateServer generic `IRepositoryPattern<T>`** — fat interface, naghz-e ISP
5. **String-based status** (`"Open"`, `"Closed"`) — formal enum ya state pattern behtar
6. **Gahi anemic domain** — handler logic mikone, entity faqat setter. Mix-e rich va anemic
7. **Factory switch** — brand-e jadid bayad case ezafe kone (minor OCP violation)

---

## 25 soal-e mosahabe

1. **4 soton-e OOP?** Encapsulation, Abstraction, Inheritance, Polymorphism
2. **Encapsulation chie?** Data + behavior yekja, state ra valid negah dar
3. **Abstraction chie?** Joziat ra makhfi kon, contract expose kon
4. **Inheritance vs composition?** Composition flexible-tar; "has-a" over "is-a"
5. **Polymorphism?** Yek contract, chand implementation. Runtime dispatch
6. **Abstract class vs interface?** Abstract: shared state + behavior. Interface: pure contract
7. **`sealed` chera?** Derive mamnoo', performance (devirtualize), design intent
8. **SRP?** Yek dalil baraye change
9. **OCP?** Baraye extension baz, modification baste. IEndpoint mesal
10. **LSP?** Subtype be jaye parent bedune break
11. **ISP?** Interface-e koochik, na fat
12. **DIP?** Vabaste be abstraction, na concrete
13. **DI chie?** Mechanism-e inject-e dependency az birune
14. **Repository pattern?** Layer-e beyn-e domain va data. Test + DIP
15. **UoW?** Hame-ye change yekja commit
16. **Mediator?** Object-ha mostaghim sohbat nakonan. MediatR
17. **CQRS?** Command (write) va Query (read) joda
18. **Decorator?** Wrap-e object ba behavior-e ezafe. Scrutor
19. **Strategy?** Algorithm-e motefavet runtime. IDeviceSyncStrategy
20. **Factory method?** `Personnel.CreateAsync(...)` — constructor private
21. **Observer?** Entity raise, handler react. Domain events
22. **Chain of Responsibility?** Pipeline behaviors. Validation → Logging → Handler
23. **Options pattern?** Config → strongly-typed class. IOptions<T>
24. **ErrorOr?** Result pattern. Na exception baraye business error
25. **Anemic vs rich domain?** Anemic: entity faqat data, logic to service. Rich: entity behavior dare

---

## Resume

**short:**

> Applied SOLID principles and GoF patterns across a modular monolith: repository+UoW for persistence, MediatR CQRS with pipeline behaviors (validation, logging, exception), Scrutor decorators for idempotent event handlers, and strategy+factory for multi-brand device sync.

**bullets:**

- Designed encapsulated domain entities with private constructors, factory methods, and domain event raising (Entity base class)
- Enforced OCP via IEndpoint plugin model and MediatR pipeline behaviors for cross-cutting concerns
- Implemented Strategy pattern for device brand abstraction (ZK/Tiam/Virdi) and file storage (Local/S3)
- Used Scrutor Decorator to wrap domain event handlers with idempotency checks transparently

**skills:** `OOP, SOLID, Design Patterns, Clean Architecture, Repository, UoW, CQRS, MediatR, Decorator, Strategy, Factory, DI`

---

## File-haye mohem

| chi | koja |
|---|---|
| Entity base | `Dejban.Common.Domain/Entity.cs` |
| IDomainEvent | `Dejban.Common.Domain/IDomainEvent.cs` |
| ICommand/IQuery | `Dejban.Common.Application/Messaging/ICommand.cs` |
| Personnel entity | `Personnels.Domain/Personnels/Personnel.cs` |
| Personnel repository (interface) | `Personnels.Domain/Personnels/IPersonnelRepository.cs` |
| Personnel repository (impl) | `Personnels.Infrastructure/Personnels/PersonnelRepository.cs` |
| UnitOfWork impl | `Personnels.Infrastructure/Database/PersonnelsDbContext.cs` |
| Command handler | `Personnels.Application/Personnels/CreatePersonnel/CreatePersonnelCommandHandler.cs` |
| IEndpoint + auto-discovery | `Dejban.Common.Presentation/Endpoints/IEndpoint.cs` + `EndpointExtensions.cs` |
| Pipeline behaviors | `Dejban.Common.Application/Behaviors/ValidationPipelineBehavior.cs` |
| MediatR registration | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| Idempotent decorator | `Personnels.Infrastructure/Outbox/IdempotentDomainEventHandler.cs` |
| Scrutor decoration | `Personnels.Infrastructure/PersonnelsModule.cs` |
| Device strategy factory | `ACLServer/Infrastructure/Strategies/DeviceSyncStrategyFactory.cs` |
| ZK strategy | `ACLServer/Infrastructure/Strategies/ZKDeviceSyncStrategy.cs` |
| File storage strategy | `DCC/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Options pattern | `ACLServer/Abstractions/BindingContracts/VehicleAccessOptions.cs` |
| ITenantContext | `Common/Tenancy/ITenantContext.cs` |
| IDateTimeProvider | `Dejban.Common.Application/Clock/IDateTimeProvider.cs` |
| ISiteEntity / ISoftDeletable | `Common/Tenancy/ISiteEntity.cs` / `ISoftDeletable.cs` |
| Fat controller (smell) | `ACLServer/Controllers/IclockController.cs` |
| GateServer generic repo | `GateServer/Application/Abstractions/Repositories/Patterns/IRepositoryPattern.cs` |

---

Day 03 tamum. Ba'd: Day 04 — SQL + PostgreSQL. Fehrest: [README.md](./README.md).
