# Day 14 — Repository + Unit of Work

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Repository = abstraction baraye **load/save-e entity**. Unit of Work = **yek transaction boundary** baraye chand change. Tu Dejban: repo-ha **specific** hastan (na generic `IRepository<T>`), va `IUnitOfWork` = **hamoon DbContext** (scoped). Handler: `repo.Insert` → `unitOfWork.SaveChangesAsync`. Query-ha ziad az `GetQueryable()` + LINQ to EF estefade mikonan — practical, vali EF leak smell.

---

# BAKHSH-E AVAL: WORLD — Repository + UoW to donya

## Chera Repository?

Bedune abstraction:

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

Ba Repository:

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

**Maziat:**
- Application/Domain az EF concrete depend **nemikone** (ideally)
- Test: mock `IOrderRepository`
- Swap storage later (rare, vali possible)

**Ghalat-e common:** Repository = dump CRUD baraye har table. Behtar: **aggregate-oriented** — methods ke domain lazem dare.

---

## Unit of Work chie?

Problem: chand repo, yek transaction.

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
| **Explicit UoW** | `IUnitOfWork` + repos share same DbContext/session |
| **DbContext as UoW** | EF DbContext khodesh UoW-e ← **Dejban** |
| **UoW wraps repos** | `uow.Orders`, `uow.Products` (classic Fowler) |

EF Change Tracker = in-memory unit of work. `SaveChanges` = flush + transaction.

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

**World trend (DDD):** specific repos per aggregate. Generic often anemic + leaky.

---

## IQueryable smell

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

**Pure alternative:** Specification / query object / dedicated query methods on repo (no `IQueryable` on interface).

---

## Repository anti-patterns

1. **SaveChanges dakhel-e repo** — UoW boundary blur; chand repo = chand commit
2. **Repo per table** — ignore aggregate
3. **Returning `DbSet` / tracked entities everywhere** — accidental updates
4. **God repository** — 50 methods
5. **Generic repo + business methods mixed** — confusion

---

## Testing

```csharp
var repo = Substitute.For<IOrderRepository>();
var uow = Substitute.For<IUnitOfWork>();
var handler = new CreateOrderHandler(repo, uow);

await handler.Handle(cmd, ct);

repo.Received(1).Insert(Arg.Any<Order>());
await uow.Received(1).SaveChangesAsync(ct);
```

Age `IQueryable` leak → mock sakht (in-memory EF ya integration test).

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **Classic UoW with repo properties** (`uow.Visitors`)
- **Specification pattern** for queries
- **Generic `IRepository<T>` to Dejban modules** — GateServer dare, Dejban na
- **Repo method per query** bedune `IQueryable` — partial
- **Separate read store / query repos (CQRS Level 3)** — nist

---

# BAKHSH-E DOVOM: DEJBAN — Repository + UoW to in proje

## Pattern-e kolli (8 module)

```
Domain:        IVisitorRepository, IPersonnelRepository, ...
Application:   IUnitOfWork  (+ handlers use both)
Infrastructure: VisitorRepository : IVisitorRepository
                VisitorsDbContext : DbContext, IUnitOfWork
DI:            AddScoped<IVisitorRepository, VisitorRepository>()
               AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<VisitorsDbContext>())
```

**Yek scope = yek DbContext = yek UoW.** Repo va UoW **hamoon instance**-e tracker.

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

*Day 14 tamum. Ba'd: Day 15 — Soft Delete. Fehrest: [README.md](./README.md).*
