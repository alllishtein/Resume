# Day 14 — Repository + Unit of Work

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Repository** abstraction-e baraye load va save-e entity-ha-st: application midone *chi* mikhad (Get, Insert, …), na inke *chejori* EF ya SQL anjam mishe. **Unit of Work** hamoon **transaction boundary**-e — chand change (chand repo) ya hame commit mishan ya hichkodom. Bedune UoW, age yek Insert ok she va digari fail, data half-written mimune.

To Dejban, repo-ha **specific** hastan (masalan `IVisitorRepository`), na generic `IRepository<T>`. `IUnitOfWork` practically **hamoon DbContext**-e scoped-e: handler `repo.Insert` mikone, ba'd `unitOfWork.SaveChangesAsync`. Samt-e query ziad `GetQueryable()` + LINQ to EF midan — ship kardan sade-tar mishe, vali Application be EF leak mikone (smell-e shenakhte).

---

# BAKHSH-E AVAL: WORLD — Repository + UoW to donya

## Chera Repository?

Age handler mostaghim `DbContext` midone, Application be infrastructure tight couple mishe — test sakht mishe va swap-e storage practically momken nist:

```csharp
// Handler mostaghim DbContext midone → tight coupling
public class CreateOrderHandler(AppDbContext db)
{
    public async Task Handle(...)
    {
        db.Orders.Add(order);
        await db.SaveChangesAsync();
    }
}
```

Ba Repository, handler faghat interface midone; SaveChanges az UoW miad:

```csharp
public interface IOrderRepository
{
    Task<Order?> GetAsync(Guid id, CancellationToken ct = default);
    void Insert(Order order);
}

public class CreateOrderHandler(IOrderRepository orders, IUnitOfWork uow)
{
    public async Task Handle(...)
    {
        orders.Insert(order);
        await uow.SaveChangesAsync(ct);
    }
}
```

**Chera in behtar-e?**

- Application/Domain ideally az EF concrete depend **nemikone** — faghat az contract-e domain.
- Test: `IOrderRepository` ra mock mikoni bedune DB.
- Swap storage later rare-e, vali boundary roshan mimune.

**Ghalat-e common:** Repository ra dump-e CRUD baraye *har table* midunan. Behtar **aggregate-oriented** bashe — method-hayi ke domain vaghean lazem dare (`GetWithLinesAsync`, na `GetAll` + filter dar handler).

---

## Unit of Work chie?

Problem sade-st: chand repo, **yek** transaction. Mikhay Order + OrderLine + Inventory ya hame commit shan ya hichkodom:

```
Insert Order
Insert OrderLine
Update Inventory
→ YA hame commit YA hichkodom
```

```csharp
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}
```

| style | chi |
|---|---|
| **Explicit UoW** | `IUnitOfWork` + repo-ha hamoon session/DbContext ra share mikonan |
| **DbContext as UoW** | EF DbContext khodesh UoW-e ← **Dejban** |
| **UoW wraps repos** | `uow.Orders`, `uow.Products` (classic Fowler) |

To EF, Change Tracker = in-memory unit of work. `SaveChanges` = flush + transaction. Dejban in model ra explicit mikone ba interface-e thin `IUnitOfWork`.

---

## Generic vs Specific repository

```csharp
// Generic — CRUD for any T
public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(Guid id);
    void Add(T entity);
    void Remove(T entity);
}

// Specific — domain language
public interface IOrderRepository
{
    Task<Order?> GetWithLinesAsync(Guid id);
    Task<IReadOnlyList<Order>> GetOpenByCustomerAsync(Guid customerId);
    void Insert(Order order);
}
```

Trend-e DDD to donya: **specific repo per aggregate**. Generic zud anemic va leaky mishe — har query digar be `IQueryable` ya extension-haye EF niaz peyda mikone.

---

## IQueryable smell

Chizi ke Dejban ziad dare:

```csharp
// Interface:
IQueryable<Order> GetQueryable();

// Handler:
await repo.GetQueryable()
    .Include(o => o.Lines)
    .Where(o => o.Status == Open)
    .AsNoTracking()
    .ToListAsync();
```

| maziat | moshkel |
|---|---|
| Flexible queries | Domain/Application depend on EF LINQ |
| Kam boilerplate | Hard to mock; provider-specific |
| Fast to ship | Persistence details leak upward |

**Pure alternative:** Specification, query object, ya method-haye query-e makhsus ru-ye repo — bedune `IQueryable` ru-ye interface. Dejban trade-off ra be tarafe speed of delivery gerefte.

---

## Repository anti-patterns

In-ha ra to mosahebe / code review zud mishnasi:

1. **SaveChanges dakhel-e repo** — boundary-e UoW blur mishe; chand repo = chand commit-e joda.
2. **Repo per table** — aggregate ra ignore mikone (OrderLine joda az Order).
3. **Returning `DbSet` / tracked entities everywhere** — update-haye accidental.
4. **God repository** — 50 method; digar «repository» nist, service dump-e.
5. **Generic repo + business methods mixed** — developer nemidune koja chi ra seda bezane.

---

## Testing

Ba interface-haye clean, unit test sade-st:

```csharp
var repo = Substitute.For<IOrderRepository>();
var uow = Substitute.For<IUnitOfWork>();
var handler = new CreateOrderHandler(repo, uow);

await handler.Handle(cmd, ct);

repo.Received(1).Insert(Arg.Any<Order>());
await uow.Received(1).SaveChangesAsync(ct);
```

Age `IQueryable` leak dashte bashi, mock sakht mishe — ya in-memory EF ya integration test. In yeki az gheymat-haye olgu-ye Dejban-e.

---

## Chizaei ke to donya hastan vali inja kam/nistan

Donya in-ha ra ham dare; Dejban modules kamtar:

- **Classic UoW with repo properties** (`uow.Visitors`) — Fowler-style
- **Specification pattern** baraye query-ha
- **Generic `IRepository<T>`** — GateServer dare, module-haye Dejban na
- **Repo method per query** bedune `IQueryable` — partial
- **Separate read store / query repos (CQRS Level 3)** — nist

---

# BAKHSH-E DOVOM: DEJBAN — Repository + UoW to in proje

To modular monolith, har module (Visitors, Personnels, …) **DbContext-e khodesh** ra dare. Pattern yeksan-e: Domain interface tarif mikone, Infrastructure implement mikone, Application `IUnitOfWork` ra seda mizane. Yek HTTP request = yek DI scope = **yek** DbContext instance ke ham repo-ha azash estefade mikonan ham UoW.

## Pattern-e kolli (8 module)

```
Domain:        IVisitorRepository, IPersonnelRepository, ...
Application:   IUnitOfWork  (+ handlers use both)
Infrastructure: VisitorRepository : IVisitorRepository
                VisitorsDbContext : DbContext, IUnitOfWork
DI:            AddScoped<IVisitorRepository, VisitorRepository>()
               AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<VisitorsDbContext>())
```

**Yek scope = yek DbContext = yek UoW.** Repo va UoW **hamoon instance**-e tracker ra share mikonan — age do DbContext dashte bashi, SaveChanges digar «yek transaction» nist.

---

## IUnitOfWork

```csharp
// Most modules (Visitors, Vehicles, Armory, ...):
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
```

```csharp
// Personnels — Extra (smell):
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    EntityEntry<TEntity> Entry<TEntity>(TEntity entity) where TEntity : class;
}
```

`Entry` → Application depend on EF ChangeTracking. Use case: `LoadAsync` navigation. Behtar: repo method `GetWithCameraAsync`.

---

## DbContext as UoW

```csharp
// VisitorsDbContext.cs
public sealed class VisitorsDbContext(...)
    : DbContext(options), IUnitOfWork, ITenantDbContext
{
    // SaveChangesAsync from DbContext satisfies IUnitOfWork
}
```

```csharp
// VisitorsModule.cs
services.AddDbContext<VisitorsDbContext>(...);
services.AddScoped<IUnitOfWork>(sp =>
    sp.GetRequiredService<VisitorsDbContext>());
services.AddScoped<IVisitorRepository, VisitorRepository>();
```

**Chera factory na `AddScoped<IUnitOfWork, VisitorsDbContext>`?**  
Chon DbContext already registered; factory guarantees **same instance** as repos' injected context.

---

## Repository interface examples

### Visitor

```csharp
// Domain/Visitors/IVisitorRepository.cs
public interface IVisitorRepository
{
    Task<Visitor?> GetAsync(Guid id, CancellationToken cancellationToken = default);
    IQueryable<Visitor> GetQueryable(CancellationToken cancellationToken = default);
    void Insert(Visitor visitor);
    void Remove(Visitor visitor);
    void RemoveRange(IEnumerable<Visitor> visitors);
    IQueryable<VisitorDocument> GetDocumentsQueryable(...);
    void InsertDocument(VisitorDocument document);
    void RemoveDocument(VisitorDocument document);
}
```

### Personnel

```csharp
Task<Personnel?> GetAsync(...);
Task<Personnel?> GetWithDocumentsAsync(...);  // Include in repo
IQueryable<Personnel> GetQueryable(...);
void Insert(Personnel personnel);
Task SoftDeleteByUnitIdAsync(Guid unitId, ...);
Task SoftDeleteBySiteIdAsync(Guid siteId, ...);
```

### Vehicle

```csharp
void Add(Vehicle vehicle, ...);
Task<Vehicle?> GetByIdAsync(...);      // heavy Include graph
Task<Vehicle?> GetByPlateAsync(...);
IQueryable<Vehicle> GetQueryable(...);
Task<IReadOnlyList<Guid>> GetActiveOwnedVehicleIdsByPersonnelIdAsync(...); // AsNoTracking
```

**Interface to Domain** — Clean Architecture: Application → Domain contracts; Infrastructure implements.

---

## Repository implementation

```csharp
// VisitorRepository.cs
internal sealed class VisitorRepository(VisitorsDbContext context) : IVisitorRepository
{
    public async Task<Visitor?> GetAsync(Guid id, CancellationToken ct = default)
        => await context.Visitors.SingleOrDefaultAsync(u => u.Id == id, ct);

    public IQueryable<Visitor> GetQueryable(CancellationToken ct = default)
        => context.Visitors;

    public void Insert(Visitor visitor)
        => context.Visitors.Add(visitor);
}
```

```csharp
// PersonnelRepository — Include inside repo
public async Task<Personnel?> GetWithDocumentsAsync(Guid id, CancellationToken ct = default)
    => await context.Personnels
        .Include(p => p.Documents)
        .SingleOrDefaultAsync(u => u.Id == id, ct);
```

```csharp
// VehicleRepository — graph load
public async Task<Vehicle?> GetByIdAsync(Guid id, CancellationToken ct = default)
    => await dbContext.Vehicles
        .Include(v => v.CargoDetails)
        .Include(v => v.ConstructionDetails)
        .Include(v => v.Ownerships)
        .Include(v => v.Assignments).ThenInclude(a => a.Personnel)
        .FirstOrDefaultAsync(v => v.Id == id, ct);
```

`internal` class — faqat Infrastructure; DI az interface.

---

## Handler flow

```csharp
// CreateVisitorCommandHandler
internal sealed class CreateVisitorCommandHandler(
    IVisitorRepository visitorRepository,
    IVisitorTypeRepository visitorTypeRepository,
    IUnitOfWork unitOfWork,
    ...) : ICommandHandler<CreateVisitorCommand, Guid>
{
    public async Task<ErrorOr<Guid>> Handle(...)
    {
        // ... domain CreateAsync, validations via other repos ...
        visitorRepository.Insert(visitor);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        // ↑ same DbContext → outbox interceptor runs (Day 13/19)
        return visitor.Id;
    }
}
```

```csharp
// CreatePersonnelCommandHandler — same
personnelRepository.Insert(personnel);
await unitOfWork.SaveChangesAsync(cancellationToken);
```

**Ghaede:** Repo **mutate tracker**; UoW **commit**. Repo SaveChanges **nakone**.

---

## Query side — GetQueryable composition

```csharp
// GetVisitorsQueryHandler
IQueryable<Visitor> visitorsQuery =
    visitorRepository.GetQueryable().AsNoTracking();

// filter / sort / project / PagedList
```

```csharp
// CreateVisitor — also uses IQueryable for blacklist
var blackList = await blackListRepository.GetQueryable()
    .Include(x => x.Reason)
    .SingleOrDefaultAsync(...);
```

In = **intentional leak** baraye speed. Trade-off ra bedun.

---

## GateServer — classic generic + separate UoW

```csharp
public interface IRepositoryPattern<T> where T : class
{
    Task CreateAsync(T entity);
    Task Update(T entity);
    void Delete(T entity);
    Task<T> GetById(Guid id);
}

public interface IUnitOfWork
{
    Task<int> SaveChangesAsync();
}

// DI
services.AddScoped<IUnitOfWork, UnitOfWorkPattern>();
```

`UnitOfWorkPattern` wraps `ApplicationDbContext` — DbContext **implements** IUnitOfWork nist.

**Smell:** ba'zi `CreateRangeAsync` dakhel-e repo `SaveChanges` seda mizane → blur.

---

## Identity / ACL — kam/bi repo

| service | pattern |
|---|---|
| **IdentityServer** | handlers inject `ApplicationDbContext` mostaghim |
| **ACLServer** | mostly DbContext; 2 specialized repo (`IDeviceSyncRepository`, `IPlateReaderAccessLogRepository`) |
| **RequestTracker** | DbContext + MediatR (similar) |

Dejban modular monolith = jiddi-tar Clean Architecture. Standalone = pragmatism / Identity framework style.

---

## Connection to previous days

| day | rabt |
|---|---|
| 09 Architecture | repo interface to Domain |
| 10 CQRS | command uses repo+UoW; query often GetQueryable |
| 12 DDD | repo loads aggregate; Insert after factory |
| 13 EF | DbContext = tracker + SaveChanges |
| 19 Dapper | outbox jobs **bypass** repos — raw SQL |

---

## Smell-ha

1. **`IQueryable` on Domain interfaces** — EF leak
2. **Personnels `IUnitOfWork.Entry`** — ChangeTracker in Application
3. **AsNoTracking often in handlers** — inconsistent (sometimes in repo)
4. **Naming inconsistency** — `Insert` vs `Add` vs `Update` across modules
5. **GateServer SaveChanges in repo** — UoW violated
6. **No generic repo in Dejban** — good; but many near-duplicate `IPersonnelRepository` copies per module (read-model)
7. **Identity/ACL skip pattern** — two styles in one org
8. **GetQueryable unused CancellationToken** — noise on signature
9. **Tracked GetAsync for reads** — accidental mutation risk if not careful
10. **Thin UoW** — only SaveChanges; no explicit `BeginTransaction` API (EF has it on Database facade when needed)

---

## 20 soal-e mosahebe

1. **Repository chie?** — Abstraction for aggregate persistence
2. **Unit of Work chie?** — Single commit for multiple changes
3. **Chera EF DbContext = UoW?** — Change tracker + SaveChanges
4. **Generic vs specific repo?** — Specific = DDD language; generic = CRUD
5. **Chera SaveChanges na to repo?** — One commit across repos
6. **IQueryable smell?** — Leaks EF; hard to mock
7. **Specification?** — Encapsulate query without IQueryable on interface
8. **Scoped DbContext?** — One per request; repos share it
9. **Chejori DI same instance?** — `AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<DbContext>())`
10. **AsNoTracking?** — Read-only; no tracker cost
11. **Include koja?** — Repo specialized methods OR handler on IQueryable
12. **Aggregate-oriented repo?** — Methods match domain use cases
13. **Test handler?** — Mock IRepo + IUnitOfWork
14. **Identity bedune repo?** — Pragmatic; couples to EF
15. **Outbox + UoW?** — Same SaveChanges → interceptor writes outbox
16. **Repository vs DAO?** — Repo = domain collection metaphor; DAO = table CRUD
17. **Multiple DbContexts?** — Multiple UoW boundaries (modules) — no cross-module join
18. **SoftDelete in repo?** — ExecuteUpdate / flag methods (Day 15)
19. **Anti-pattern God repo?** — Too many methods; split by aggregate
20. **Clean Architecture repo place?** — Interface Domain/Application; impl Infrastructure

---

## Resume

**short:**

> Implemented per-module Repository and Unit of Work over EF Core: domain-specific repository interfaces, DbContext registered as `IUnitOfWork`, and command handlers that insert aggregates then commit once via `SaveChangesAsync` (triggering the transactional outbox).

**bullets:**

- Defined aggregate-focused contracts (`IVisitorRepository`, `IPersonnelRepository`, `IVehicleRepository`) in Domain with Infrastructure implementations
- Wired `AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<*DbContext>())` so repositories and UoW share one change tracker per request
- Kept writes as `Insert`/`Add` + single `SaveChangesAsync` in MediatR command handlers
- Used `GetQueryable()` as a pragmatic query escape hatch (with known EF coupling trade-off)

**skills:** `Repository Pattern, Unit of Work, EF Core, Clean Architecture, Dependency Injection, Aggregate Persistence, CQRS`

---

## File-haye mohem

| chi | koja |
|---|---|
| IUnitOfWork (Visitors) | `Visitors.Application/Abstractions/Data/IUnitOfWork.cs` |
| IUnitOfWork (Personnels+Entry) | `Personnels.Application/Abstractions/Data/IUnitOfWork.cs` |
| VisitorsDbContext | `Visitors.Infrastructure/Database/VisitorsDbContext.cs` |
| DI registration | `Visitors.Infrastructure/VisitorsModule.cs` |
| IVisitorRepository | `Visitors.Domain/Visitors/IVisitorRepository.cs` |
| VisitorRepository | `Visitors.Infrastructure/Visitors/VisitorRepository.cs` |
| IPersonnelRepository | `Personnels.Domain/Personnels/IPersonnelRepository.cs` |
| PersonnelRepository | `Personnels.Infrastructure/Personnels/PersonnelRepository.cs` |
| IVehicleRepository | `Vehicles.Domain/Vehicles/IVehicleRepository.cs` |
| VehicleRepository | `Vehicles.Infrastructure/Vehicles/VehicleRepository.cs` |
| CreateVisitor handler | `Visitors.Application/.../CreateVisitorCommandHandler.cs` |
| CreatePersonnel handler | `Personnels.Application/.../CreatePersonnelCommandHandler.cs` |
| GetVisitors (IQueryable) | `Visitors.Application/.../GetVisitorsQueryHandler.cs` |
| GateServer generic | `GateServer/.../IRepositoryPattern.cs` + `UnitOfWorkPattern.cs` |
| Identity DbContext direct | `IdentityServer/.../CreateUnitCommandHandler.cs` |

---

## IQueryable smell — deep dive

### Chi mishe vaghti leak mikoni?

```csharp
// Application layer
await visitorRepository.GetQueryable()
    .Where(v => v.NationalCode == code)
    .Include(v => v.VisitorType)
    .AsNoTracking()
    .SingleOrDefaultAsync(ct);
```

Application **EF-specific** (`Include`, `AsNoTracking`) midanad. Test unit ba mock `IQueryable` = in-memory provider ya integration test.

### SQL ke EF misaze

Hamoon query → yek SELECT ba JOIN. **Moshkel performance na IQueryable** — moshkel **boundary** va **testability**.

### Refactor ladder (bedune big-bang)

| level | pattern | effort |
|---|---|---|
| 0 | `GetQueryable()` + handler LINQ | **Dejban default** |
| 1 | Repo method: `GetByNationalCodeWithTypeAsync` | kam, targeted |
| 2 | Query object `VisitorListSpec` to Application | medium |
| 3 | Dapper read model / projection SQL | CQRS read side |
| 4 | Separate read DB | enterprise |

### Specification (world) — mesal

```csharp
public sealed class ActiveVisitorsBySiteSpec : Specification<Visitor>
{
    public ActiveVisitorsBySiteSpec(Guid siteId) =>
        Query.Where(v => v.SiteId == siteId); // internal to infra
}
```

Interface Application **Specification nadare** — faqat method `GetActiveBySiteAsync`.

### Smell-haye IQueryable to handler

- `GetQueryable()` bedune `AsNoTracking` to list → tracker bloat
- `.ToList()` sync (Day 02) → thread block
- `Include` 5 level to handler → graph explosion (N+1 ya wide JOIN)
- Filter tenant **faramosh** ba raw SQL / IgnoreQueryFilters

---

## Transaction va BeginTransaction — chera thin UoW kafi nist?

`SaveChangesAsync` = **implicit transaction** (yek batch). Kafi baraye 95% command-ha.

**Explicit transaction** vaghti:

- Chand `SaveChanges` to yek atomic unit (kam to Dejban — prefer yek SaveChanges)
- Raw SQL + EF hamzaman
- Serializable isolation (card generator)
- Dapper inbox + mark processed

```csharp
await using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.ReadCommitted, ct);
try
{
    // mutations ...
    await db.SaveChangesAsync(ct);
    await tx.CommitAsync(ct);
}
catch
{
    await tx.RollbackAsync(ct);
    throw;
}
```

**ExecutionStrategy:** kole block dakhele `ExecuteAsync` ta retry transient (deadlock, serialization failure).

**Outbox:** interceptor roye `SavingChanges` — outbox row **haman** transaction. Repo Insert + UoW SaveChanges = outbox automatic (Day 13).

**Anti-pattern:** `BeginTransaction` to repo — boundary bayad Application/ handler bashe.

---

## Dejban module map — repo + UoW (8 module)

| module | DbContext | IUnitOfWork | repo style |
|---|---|---|---|
| Visitors | `VisitorsDbContext` | factory → same instance | `IVisitorRepository` + GetQueryable |
| Personnels | `PersonnelsDbContext` | factory | `IPersonnelRepository` + **Entry smell** |
| Vehicles | `VehiclesDbContext` | factory | heavy `GetByIdAsync` graph |
| Armory | `ArmoryDbContext` | factory | weapon/asset repos |
| Inventory | `InventoryDbContext` | factory | products/assets |
| CashLogistics | `CashLogisticsDbContext` | factory | stations/paths |
| SecurityPatrols | `SecurityPatrolsDbContext` | factory | patrol shifts |
| WeighBridge | `WeighBridgeDbContext` | factory | traffic/weigh |

Har module **Presentation + Application + Domain + Infrastructure** — repo interface to **Domain** (Visitors, Personnels) ya Application abstractions (ba'zi modules).

**Cross-module:** `Visitors` copy `personnels`, `sites`, `units` — repo `IPersonnelRepository` to Visitors module baraye **read model**, na join be `personnels.personnels`.

---

## Armory + Inventory — mesal-ha

### Delete ba GetQueryable (bulk soft/command)

Pattern:

```csharp
await cartridgeDefinitionRepository.GetQueryable()
    .Where(x => ids.Contains(x.Id))
    .ExecuteUpdateAsync(setters => setters.SetProperty(...), ct);
```

Repo **query root** mide; handler filter. `ExecuteUpdate` EF 7+ — bedune load to memory.

### Inventory `GetProductQueryHandler`

```csharp
var product = await productRepository.GetQueryable()
    .AsNoTracking()
    .SingleOrDefaultAsync(p => p.Id == id, ct);
```

Read single — mitone `GetByIdAsync` to repo ham bashe (consistency).

---

## Vehicles — aggregate load

`VehicleRepository.GetByIdAsync` — Cargo, Construction, Ownerships, Assignments+Personnel. **Yek ja Include** ta handler graph nafahme.

Write path: `Add(vehicle)` + `SaveChangesAsync` — ownership lines via aggregate root.

---

## Personnels — IUnitOfWork.Entry smell

```csharp
unitOfWork.Entry(personnel).Reference(p => p.Camera).LoadAsync(ct);
```

Application layer **EF API** midanad. Behtar:

```csharp
await personnelRepository.GetWithCameraAsync(id, ct);
```

Interview: «Repo vs UoW responsibility?» — Repo load/save aggregate; UoW commit; **na** expose ChangeTracker unless pragmatic shortcut.

---

## GateServer — generic repo vs Dejban (jadval)

| aspect | GateServer | Dejban modules |
|---|---|---|
| Repo | `IRepositoryPattern<T>` generic | `IVisitorRepository` specific |
| UoW | `UnitOfWorkPattern` wrapper class | DbContext implements `IUnitOfWork` |
| DbContext | does not implement IUnitOfWork interface directly | `VisitorsDbContext : DbContext, IUnitOfWork` |
| Query | mix | `GetQueryable()` pervasive |
| SaveChanges in repo | **sometimes** (smell) | **no** — handler only |

```csharp
// GateServer — UnitOfWorkPattern.cs
public async Task<int> SaveChangesAsync()
    => await _context.SaveChangesAsync();
```

Sade — faqat delegate. Dejban factory pattern **same scoped DbContext** guarantee mikone.

**Onboarding:** developer az GateServer miad → faghat CRUD generic. Dejban → domain language + MediatR.

---

## Identity / ACL — chera DbContext?

IdentityServer command handlers:

```csharp
public class CreateUnitCommandHandler(ApplicationDbContext db) { ... }
```

**Dalil-ha (pragmatic):** Identity template, ASP.NET Identity integration, kam aggregate boundary. **Cost:** test = in-memory EF ya integration; Clean Architecture kamtar strict.

ACL: specialized repos baraye sync-heavy paths; baghie DbContext.

**Org reality:** do style — mosahebe «tradeoff pragmatism vs purity».

---

## Testing — unit, integration, repo

### Handler unit (preferred)

```csharp
var visitors = Substitute.For<IVisitorRepository>();
var uow = Substitute.For<IUnitOfWork>();
var handler = new CreateVisitorCommandHandler(visitors, ..., uow);

await handler.Handle(cmd, ct);

visitors.Received(1).Insert(Arg.Any<Visitor>());
await uow.Received(1).SaveChangesAsync(ct);
```

### Query ba IQueryable — integration

```csharp
await using var ctx = CreateVisitorsDbContext(options);
SeedVisitors(ctx);
var repo = new VisitorRepository(ctx);
var query = repo.GetQueryable().Where(...);
var list = await query.ToListAsync();
```

In-memory provider **limitations** — Postgres-specific filter/partial index test na.

### Fake repo bedune EF

```csharp
class FakeVisitorRepo : IVisitorRepository
{
    private readonly List<Visitor> _data = [];
    public IQueryable<Visitor> GetQueryable() => _data.AsQueryable();
}
```

`Include` / global filter simulate **nemishe** — faqat logic-e sade.

---

## Outbox + Inbox va repo boundary

| path | repo? | note |
|---|---|---|
| Command handler | **bale** | Insert aggregate → SaveChanges → outbox row |
| ProcessOutboxJob | **na** | Dapper/SQL update processed |
| ProcessInboxJob | **na** | Dapper poll + scope + handlers (may use repos inside scope) |
| Integration event handler | **bale** | e.g. upsert read-model personnel |

**Lesson:** repo = domain writes; infrastructure jobs = raw SQL OK for mechanical tables.

---

## Read-model repos to Visitors

`DoorRepository`, `PersonnelRepository` (Visitors.Infrastructure) — copy tables. Methods:

- `GetQueryable()` baraye lookup
- Upsert az inbox handler

Na aggregate root Personnels — **BC boundary**.

---

## Naming inconsistency — cheat sheet

| verb | modules |
|---|---|
| `Insert` | Visitors, Personnels |
| `Add` | Vehicles |
| `CreateAsync` | GateServer generic |
| `Remove` / `RemoveRange` | Visitors |
| `SoftDeleteBySiteIdAsync` | Personnels |

Greenfield: yek convention (`Insert` aggregate, `Add` child entity optional). Refactor cost bala — document in booklet.

---

## Debug checklist («SaveChanges fail / double commit»)

1. Handler 2 bar `SaveChangesAsync`? — usually OK (2 tx) — intentional?
2. Repo dakhel SaveChanges? — GateServer smell
3. Multiple DbContext to yek request? — 2 UoW — data inconsistency
4. Tracked entity from GetAsync + query update — accidental
5. Outbox duplicate — same SaveChanges?
6. Transaction isolation — serialization failure loop?
7. Tenant filter — insert SiteId set?
8. Soft delete — Remove vs SoftDelete method?

---

## Senario whiteboard

### A) Create visitor + blacklist check

Handler: `blackListRepository.GetQueryable()...` + `visitorRepository.Insert` + `SaveChangesAsync`. **Yek UoW** — blacklist read, visitor write, outbox.

### B) Cross-module personnel name

**Na** join — read `visitors.personnels` copy. Stale name until event processed.

### C) Refactor GetQueryable

Extract `GetVisitorsQueryHandler` filter to `GetPagedVisitorsAsync` on repo — handler 10 line kam, test harder unless integration.

---

## Mini lab (1 session)

1. Open `VisitorsModule.cs` — trace `AddScoped<IUnitOfWork>` factory.
2. Compare `IVisitorRepository` vs `GateServer/IRepositoryPattern.cs`.
3. Read `CreateVisitorCommandHandler` — Insert + SaveChanges.
4. Read `GetVisitorsQueryHandler` — GetQueryable composition.
5. Find one `ExecuteUpdateAsync` on GetQueryable (Armory/Inventory).
6. Personnels `IUnitOfWork` — find `Entry` usage (grep).
7. Sketch test doubles for one command handler.

---

## 15 soal-e ezafe

21. **`ExecuteUpdateAsync` vs load+update?** — SQL UPDATE bedune hydrate
22. **Repo return `IQueryable` — thread-safe?** — DbContext scoped; query execute later on same scope
23. **Chand SaveChanges to yek handler?** — 2 transaction unless explicit tx
24. **`AddDbContext` + factory UoW chera?** — single instance guarantee
25. **Read-only repo layer?** — optional; Dejban query = same repo GetQueryable
26. **Aggregate root repo only?** — VisitorDocument methods on IVisitorRepository OK if part of aggregate
27. **DbContext as anti-repo?** — Identity style; speed vs purity
28. **TransactionScope?** — distributed; na baraye single Postgres module
29. **Repo + raw SQL?** — rare; Dapper jobs separate
30. **Soft delete to repo?** — `SoftDeleteByUnitIdAsync` batch (Day 15)
31. **Outbox without repo?** — interceptor on any SaveChanges
32. **Testing GetQueryable Include?** — integration
33. **Generic repo + Specification?** — world combo; Dejban na
34. **Unit of Work Fowler vs EF?** — EF tracker = UoW
35. **Multiple aggregates one SaveChanges?** — yek tx if same context; domain rule prefer one aggregate per command

---

## Chejori digest koni

1. World: repo vs UoW diagram (10 min)
2. Dejban: yek command + yek query trace (20 min)
3. GateServer vs Dejban jadval (5 min)
4. IQueryable refactor ladder (10 min)
5. 20+15 soal (25 min)
6. Mini lab 1–4 (30 min)

---

## Resume — paragraph-e bolang (optional)

> Designed module-scoped Repository and Unit of Work boundaries in a modular monolith: domain-specific repository interfaces, EF Core DbContext registered as `IUnitOfWork` via scoped factory, and MediatR command handlers that mutate through repositories then commit once—aligning transactional outbox emission with aggregate persistence. Pragmatically exposed `GetQueryable()` for read composition while documenting EF leakage trade-offs, contrasted with GateServer’s generic repository pattern and Identity’s direct DbContext usage.

---

*Day 14 tamum. Ba'd: Day 15 — Soft Delete (amade). Fehrest: [README.md](./README.md).*
