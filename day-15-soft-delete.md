# Day 15 — Soft Delete

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Soft delete = row **nemire** az DB; flag `IsDeleted = true` (+ `DeletedAt`). Query-ha automatic `WHERE is_deleted = false` mibinan (EF **global query filter**). Delete-e domain = method `SoftDelete()` ke flag + domain event mizane. Cascade beyne module-ha ba **integration event** (`PersonnelSoftDeleted`, `SiteSoftDeleted`, …). Unique code-ha ba **partial index** (`WHERE is_deleted = false`) — soft-deleted row code ra blok **nemikone**.

---

# BAKHSH-E AVAL: WORLD — Soft Delete to donya

## Hard vs Soft vs Archive

| style | chi mishe | SQL | recover |
|---|---|---|---|
| **Hard delete** | row miravad | `DELETE FROM ...` | backup / audit only |
| **Soft delete** | flag | `UPDATE ... SET is_deleted = true` | `Restore()` possible |
| **Archive / temporal** | move ya history table | insert archive + delete/flag | explicit |

**Soft delete** baraye master data (personnel, site, visitor, vehicle) common-e: audit, undo, FK integrity, «dobare hamin national code».

**Hard delete** baraye:
- join/link tables (assignment, inbox consumer)
- PII purge / GDPR «right to be forgotten» (sometimes hard after soft)
- high-volume logs (optional retention job)

---

## Chera soft delete?

1. **Accident recovery** — user ghalat delete → restore
2. **Audit / legal** — «ki key delete kard?»
3. **Referential integrity** — child rows + history nemishe yekja hard-delete
4. **Business reuse** — national code after soft-delete again creatable (partial unique)
5. **Cross-module sync** — event: digar module-ha copy-ha ra soft-delete konan

**Gheymat:**
- har query bayad filter konad (ya global filter)
- table bozorg mishe (deleted rows mimunan)
- unique / FK design harder
- report-ha bayad decide konand: include deleted ya na
- `IgnoreQueryFilters` = risk-e bug (deleted data «zende» mibine)

---

## Soft delete to product / UX

User «Delete» mizane — mentally expect «raft». Backend soft mikone. Implications:

| UX expectation | Backend reality | chejori manage |
|---|---|---|
| Gone forever | row hast | copy: «baiyghani shod» / recycle later |
| Undo 5s | Restore() | toast with undo calling Restore API |
| Search by national code finds old | filtered out | OK; admin recycle searches IgnoreFilters |
| Same code re-register | partial unique allows | show success create |

API design choice:
- `DELETE` → soft (REST-ish common in enterprise)
- `POST /personnels/{id}/soft-delete` → explicit
- `PATCH { "isDeleted": true }` → **avoid** (anemic, bypasses domain)

Dejban: command `DeletePersonnel` → SoftDelete domain — HTTP verb often DELETE mapped to soft.

---

## Lifecycle state machine (conceptual)

```
[Active] --SoftDelete--> [SoftDeleted]
[SoftDeleted] --Restore--> [Active]
[SoftDeleted] --PurgeJob--> [Gone]   // hard delete / GDPR — Dejban kam
[Active] --Remove()--> [Gone]        // accident path — avoid
```

EmploymentStatus (Active/Terminated/…) **orthogonal**:
- Terminated + not soft-deleted = still in lists, business inactive
- Soft-deleted = hidden from normal queries regardless of employment status

---

## Index design beyond unique

```sql
-- optional helper for admin recycle bin queries
CREATE INDEX ix_personnels_deleted
  ON personnels.personnels (deleted_at)
  WHERE is_deleted = true;
```

Live queries rarely need `is_deleted` index — filter removes them early; selective enough with site_id indexes.

Composite thinking:
- `(site_id)` for tenant lists
- unique `(national_code) WHERE NOT is_deleted`
- FK Restrict on Site/Unit → cannot hard-delete parent while children exist (soft parent first)

---

## Concurrency

Two admins delete same personnel:
1. Both GetAsync succeed (not deleted yet)
2. Both SoftDelete — second idempotent: after first SaveChanges, second Get may NotFound; if same tracked instance, second SoftDelete early-returns before Raise → **one** domain event. Good.

Restore vs recreate race: Restore old row + Create new same national → unique violation. Catch Postgres `23505` / validate.

---

## Observability + security

Log/enrich: `PersonnelId`, `SiteId`, `DeletedBy`, soft-delete flag. Metric per module. Trace: domain event → outbox → consumer.

Security:
- Soft-deleted rows still **PII** in DB/backups
- Restore authorization ≥ Delete
- IgnoreQueryFilters admin APIs = high privilege
- Exports default-exclude deleted

---

## Model-e classic

```csharp
public interface ISoftDeletable
{
    bool IsDeleted { get; }
}

public class Customer : ISoftDeletable
{
    public Guid Id { get; private set; }
    public bool IsDeleted { get; private set; }
    public DateTime? DeletedAt { get; private set; }
    public string? DeletedBy { get; private set; }

    public void SoftDelete(string deletedBy)
    {
        if (IsDeleted) return; // idempotent

        IsDeleted = true;
        DeletedAt = DateTime.UtcNow;
        DeletedBy = deletedBy;
        // Raise domain event...
    }

    public void Restore()
    {
        if (!IsDeleted) return;

        IsDeleted = false;
        DeletedAt = null;
        DeletedBy = null;
    }
}
```

**Encapsulation:** `IsDeleted` ba `private set`. Biruni `customer.IsDeleted = true` **nabayad** — domain event / audit / invariant gom mishe.

---

## Global query filter (EF Core)

Bedune filter:

```csharp
await db.Customers.Where(c => !c.IsDeleted).ToListAsync();
// har query dasti — faramosh = bug
```

Ba filter:

```csharp
modelBuilder.Entity<Customer>()
    .HasQueryFilter(c => !c.IsDeleted);

// ya named (EF Core 10+):
modelBuilder.Entity<Customer>()
    .HasQueryFilter("SoftDelete", c => !c.IsDeleted);
```

Har `DbSet<Customer>` query automatic `AND is_deleted = false` midahad.

### IgnoreQueryFilters

```csharp
// admin: deleted-ha ra bebin
await db.Customers
    .IgnoreQueryFilters()
    .Where(c => c.IsDeleted)
    .ToListAsync();
```

**Khatar:** `IgnoreQueryFilters()` **hame** filter-ha ra mikoshe — soft-delete **va** tenant. Age multi-tenant dari, bayad dasti `SiteId` check koni — full detail: **[Day 16 — Multi-tenancy](./day-16-multi-tenancy.md)** (`TenantFilter`, `X-Site-Id`, `ITenantContext`).

---

## Partial unique index

Problem:

```
Personnel A: national_code = 001, is_deleted = false
Soft-delete A
Personnel B: national_code = 001  → UNIQUE violation age index full bashe
```

Solution — PostgreSQL filtered unique:

```sql
CREATE UNIQUE INDEX ux_personnel_national_code
  ON personnels.personnels (national_code)
  WHERE is_deleted = false;
```

EF:

```csharp
builder.HasIndex(e => e.NationalCode)
    .IsUnique()
    .HasFilter("\"is_deleted\" = false");
```

**Interview gold:** soft delete + unique → **partial/filtered unique**, na full unique.

---

## Cascade soft delete

```
Site soft-deleted
  → Units soft-deleted
  → Personnels soft-deleted
  → Visitors module copy soft-deleted
  → Vehicles assignments cleaned / personnel copy soft-deleted
```

Do style:

| style | chejori |
|---|---|
| **In-process** | yek DbContext, load children, SoftDelete each |
| **Event-driven** | `SiteSoftDeleted` publish → har module handler |

Modular monolith Dejban = **event-driven** (schema joda, cross-module join nist).

---

## Bulk soft delete

```csharp
// A) Domain-aware (events fire) — load + SoftDelete()
await context.Personnels
    .Where(p => p.SiteId == siteId && !p.IsDeleted)
    .ForEachAsync(p => p.SoftDelete("System"));

// B) Fast bulk — NO domain events, NO ChangeTracker per row
await context.Personnels
    .Where(p => p.SiteId == siteId && !p.IsDeleted)
    .ExecuteUpdateAsync(s => s
        .SetProperty(p => p.IsDeleted, true)
        .SetProperty(p => p.DeletedAt, DateTime.UtcNow));
```

| | ForEach + SoftDelete | ExecuteUpdate |
|---|---|---|
| Domain events | yes | **no** |
| Performance | slower (track) | fast SQL |
| Interceptor/outbox | yes | skip unless manual |
| Use when | cascade business | pure data flag / cleanup |

**Dejban:** cascade personnel ziad az style **A** estefade mikone (events matter).

---

## Hard delete exceptions

Bazi ja `ExecuteDeleteAsync` / `Remove` — intentional:

- link tables (blacklist hard wipe by personnel)
- vehicle ownership cleanup
- inbox/outbox consumers
- «purge after soft» jobs

Soft + hard mix OK — **document** kon koja kodom.

---

## Soft delete vs status enum

```csharp
// Status: Active / Suspended / Terminated
// Soft delete: «az UI/list raft, vali data hast»
```

Status = business lifecycle. Soft delete = persistence concern («deleted from system»). Mitunan **hamzaman** bashan (`EmploymentStatus` + `IsDeleted`).

---

## Chizaei ke to donya hastan vali inja kam/nist

- **EF soft-delete interceptor** automatic on `Remove()` → SoftDelete (Dejban explicit method)
- **Temporal tables** (SQL Server) / Postgres system versioning
- **Hard purge job** scheduled (retention policy)
- **DeletedBy** always filled (tu Dejban Personnel commented out in places)
- **Admin «show deleted» UI** consistent across modules

---

# BAKHSH-E DOVOM: DEJBAN — Soft Delete to in proje

## Marker: `ISoftDeletable`

```csharp
// File: Common/Tenancy/ISoftDeletable.cs
namespace Common.Tenancy;

public interface ISoftDeletable
{
    bool IsDeleted { get; }
}
```

Minimal — faghat read. Domain entity `private set` + `SoftDelete()` method midahad.

**Mesal Personnels module:**

```csharp
public sealed class Personnel : Entity, ISiteEntity, ISoftDeletable
{
    public bool IsDeleted { get; private set; }
    public DateTime? DeletedAt { get; private set; }

    public void SoftDelete(string deletedBy)
    {
        if (IsDeleted) return;

        IsDeleted = true;
        DeletedAt = DateTime.UtcNow;
        // DeletedBy = deletedBy;  // commented in current code

        Raise(new PersonnelDeletedDomainEvent(Id, deletedBy));
    }

    public void Restore()
    {
        if (!IsDeleted) return;

        IsDeleted = false;
        DeletedAt = null;
        Raise(new PersonnelRestoredDomainEvent(Id));
    }
}
```

`Site`, `Unit`, visitor entities, vehicles sites, … ham `ISoftDeletable`.

Named filter keys:

```csharp
// File: Common/Tenancy/GlobalQueryFilterNames.cs
public static class GlobalQueryFilterNames
{
    public const string SoftDeleteFilter = "SoftDeleteFilter";
    public const string TenantFilter = "TenantFilter";
}
```

Named filters = soft-delete va tenant **jodagan** — later mituni yeki ra ignore koni (EF named filters).

---

## ApplySoftDeleteQueryFilters (reflection)

```csharp
// File: Common/Tenancy/SoftDeleteQueryFilterExtensions.cs

public static void ApplySoftDeleteQueryFilters(this ModelBuilder modelBuilder)
{
    foreach (var entityType in modelBuilder.Model.GetEntityTypes())
    {
        if (!typeof(ISoftDeletable).IsAssignableFrom(entityType.ClrType))
            continue;

        // Skip if SoftDeleteFilter already registered
        if (entityType.GetDeclaredQueryFilters()
                .Any(f => Equals(f.Key, GlobalQueryFilterNames.SoftDeleteFilter)))
            continue;

        // reflection → ApplySoftDeleteFilter<TEntity>
        var method = typeof(SoftDeleteQueryFilterExtensions)
            .GetMethod(nameof(ApplySoftDeleteFilter), BindingFlags.NonPublic | BindingFlags.Static)!
            .MakeGenericMethod(entityType.ClrType);

        method.Invoke(null, [modelBuilder]);
    }
}

private static void ApplySoftDeleteFilter<TEntity>(ModelBuilder modelBuilder)
    where TEntity : class, ISoftDeletable
{
    // e => !e.IsDeleted
    modelBuilder.Entity<TEntity>()
        .HasQueryFilter(GlobalQueryFilterNames.SoftDeleteFilter, lambda);
}
```

**Chera reflection?** Har entity type generic method mikhad — loop runtime.

**Koja seda mishe?** `OnModelCreating` aksar DbContext-ha:

- Personnels, Visitors, Vehicles, Armory, CashLogistics, SecurityPatrols, WeighBridge
- IdentityServer, ACLServer, RequestTracker

**Smell:** `InventoryDbContext` → `ApplySoftDeleteQueryFilters()` **nadare**. Inconsistent ba baghiye modules.

---

## Command path: DeletePersonnel

```csharp
// DeletePersonnelCommandHandler
var personnel = await personnelRepository.GetAsync(request.PersonnelId, ct);

if (personnel is null)
    return PersonnelErrors.NotFound(...);

if (personnel.IsDeleted)
    return PersonnelErrors.AlreadyDeleted(...); // Error.Conflict

personnel.SoftDelete(request.DeletedBy);
await unitOfWork.SaveChangesAsync(ct);
```

Flow:

```
API Delete
  → MediatR DeletePersonnelCommand
  → SoftDelete() → PersonnelDeletedDomainEvent
  → SaveChanges
       → InsertOutboxMessagesInterceptor (domain events → outbox)
  → Quartz/job publish
  → PersonnelDeletedDomainEventHandler → eventBus.Publish(PersonnelSoftDeleted)
  → digar modules IntegrationEventHandler
```

Domain → Integration bridge:

```csharp
// PersonnelDeletedDomainEventHandler
await eventBus.PublishAsync(
    new PersonnelSoftDeleted(
        domainEvent.Id,
        domainEvent.OccurredOnUtc,
        domainEvent.PersonnelId,
        domainEvent.DeletedBy),
    cancellationToken);
```

---

## Cross-module cascade (mesal Vehicles)

```csharp
// PersonnelDeletedIntegrationEventHandler (Vehicles.Presentation)
var personnel = await personnelRepository.GetAsync(integrationEvent.PersonnelId)
    ?? throw ...;

// clean assignments / ownerships (mix soft + hard)
await vehicleAssignmentRepository.DeleteByPersonnelIdAsync(...);
await vehicleRepository.DeleteOwnershipsByPersonnelIdAsync(...);
// some owned vehicles: vehicle.Delete() + Remove (hard)
await vehicleResponsiblePersonRepository.DeleteByPersonnelIdAsync(...);

personnel.SoftDelete(); // local copy in Vehicles schema
await unitOfWork.SaveChangesAsync(ct);
```

**Pattern:** har module **read-model / local copy** az Site/Unit/Personnel dare. Soft-delete event → local SoftDelete. Na shared table.

Mesal digar:

| event | consumer (sample) |
|---|---|
| `SiteSoftDeleted` | Personnels, Visitors, Armory, CashLogistics, … → `site.SoftDelete()` + `SoftDeleteBySiteIdAsync` |
| `UnitSoftDeleted` | same → `SoftDeleteByUnitIdAsync` |
| `PersonnelSoftDeleted` | Vehicles, SecurityPatrols, Visitors blacklist, … |

---

## Repo cascade helpers

```csharp
// Personnels.Infrastructure/Personnels/PersonnelRepository.cs
public async Task SoftDeleteBySiteIdAsync(Guid siteId, CancellationToken ct = default)
{
    await context.Personnels
        .Where(p => p.SiteId == siteId && !p.IsDeleted)
        .ForEachAsync(p => p.SoftDelete("System"), ct);
}
```

Visitors/Armory/… copies: similar `ForEachAsync(p => p.SoftDelete())`.

BlackList:

```csharp
// Soft: domain SoftDelete per row
public async Task SoftDeleteByPersonnelIdAsync(Guid personnelId, ...)
{
    var list = await context.BlackLists
        .Where(x => x.PersonnelId == personnelId && !x.IsDeleted)
        .ToListAsync(ct);
    foreach (var x in list) x.SoftDelete();
}

// Hard: IgnoreQueryFilters + ExecuteDelete
public async Task DeleteByPersonnelIdAsync(Guid personnelId, ...)
{
    await context.BlackLists
        .IgnoreQueryFilters()
        .Where(x => x.PersonnelId == personnelId || x.CreatorId == personnelId)
        .ExecuteDeleteAsync(ct);
}
```

Do API = do intent (business soft vs purge).

---

## Filtered unique indexes (Personnels)

```csharp
// PersonnelConfiguration.cs
builder.Property(e => e.IsDeleted)
    .IsRequired()
    .HasDefaultValue(false);

builder.HasIndex(e => e.PersonnelCode)
    .IsUnique()
    .HasFilter("\"is_deleted\" = false");

builder.HasIndex(e => e.NationalCode)
    .IsUnique()
    .HasFilter("\"is_deleted\" = false");

builder.HasIndex(e => e.ACLUserId)
    .IsUnique()
    .HasFilter("\"is_deleted\" = false");

builder.HasIndex(e => new { e.SiteId, e.AccessCode })
    .IsUnique()
    .HasFilter("\"access_code\" IS NOT NULL AND \"is_deleted\" = false");
```

**Ma'na:**
- live rows: unique national/personnel/ACL/access
- soft-deleted: code free for new hire
- empty access_code: out of unique (NULL/empty filter)

Site/Unit configs ham `HasFilter("\"is_deleted\" = false")` baraye name uniqueness.

---

## IgnoreQueryFilters — koja va chera

| place | reason |
|---|---|
| `BlackListRepository.DeleteByPersonnelIdAsync` | purge including already soft-deleted |
| `DeliveryPersonRepository` GetIds / DeleteByPersonnel | find all copies even deleted |
| Patrol group/shift personnel repos | join / sync with deleted rows |
| RequestTracker public ticket | cross-tenant/admin paths — **must** re-check `!IsDeleted` dasti |
| Reporting | optional include soft-deleted columns |

**Rule of thumb:**

```csharp
.IgnoreQueryFilters()
.Where(x => !x.IsDeleted)   // soft-delete dasti
.Where(x => allowedSites.Contains(x.SiteId)) // tenant dasti
```

Age dasti check nakoni → **tenant leak** + **ghost deleted rows**.

---

## Restore

Domain `Restore()` + `PersonnelRestoredDomainEvent` hast. Full restore **command/handler cascade** across modules kamtar mature az delete path — interview: «delete event-driven mature; restore often incomplete».

---

## Identity / ACL / RequestTracker

Hamon `ApplySoftDeleteQueryFilters()` roye `ApplicationDbContext`. Pattern yeksan — `ISoftDeletable` entities filtered. Identity handlers sometimes DbContext direct (Day 14) vali filter still applies.

---

## Deep dive — SQL ke EF generate mikone

Ba SoftDeleteFilter + TenantFilter ([Day 16](./day-16-multi-tenancy.md)):

```sql
SELECT p.*
FROM personnels.personnels AS p
WHERE p.is_deleted = FALSE
  AND p.site_id = ANY(@tenantIds)   -- ya OR superadmin unscoped
```

`GetAsync(id)`:

```sql
SELECT ... WHERE id = @id AND is_deleted = FALSE AND site_id = ANY(...)
```

Pas soft-deleted ya wrong-site → **null** (mesl NotFound). Handler `AlreadyDeleted` branch rarely via normal Get — magar:
- same request tracked entity already loaded with IgnoreQueryFilters
- race: deleted between get and check (unlikely with filter)
- explicit IgnoreQueryFilters path

---

## Deep dive — domain event payload

```csharp
public sealed class PersonnelDeletedDomainEvent : DomainEvent
{
    public Guid PersonnelId { get; }
    public string DeletedBy { get; }
    // Id + OccurredOnUtc az base
}
```

Integration:

```csharp
public sealed class PersonnelSoftDeleted : IntegrationEvent
{
    public Guid PersonnelId { get; init; }
    public string DeletedBy { get; init; }
}
```

Naming: domain `PersonnelDeleted*` (dakhel module) vs integration `PersonnelSoftDeleted` (cross-module — explicit soft). Site/Unit: `SiteSoftDeleted`, `UnitSoftDeleted`.

Consumers register to MassTransit / inbox:

```csharp
configure.AddConsumer<IntegrationEventConsumer<SiteSoftDeleted>>();
configure.AddConsumer<IntegrationEventConsumer<UnitSoftDeleted>>();
configure.AddConsumer<IntegrationEventConsumer<PersonnelSoftDeleted>>();
```

---

## Deep dive — Site / Unit SoftDelete (Personnels module)

```csharp
// Site — similar pattern
public void SoftDelete(/* ... */)
{
    if (IsDeleted) return;
    IsDeleted = true;
    DeletedAt = DateTime.UtcNow;
    // raise domain event → SiteSoftDeleted integration
}

// Handler SiteSoftDeleted in same + other modules:
site.SoftDelete();
await personnelRepository.SoftDeleteBySiteIdAsync(siteId, ct);
// units may soft-delete too depending on module
```

Cascade depth:
1. Site soft
2. Units soft (per module copy)
3. Personnels soft (ForEach SoftDelete → more events!)
4. Visitors/Vehicles/Armory/… react to PersonnelSoftDeleted / SiteSoftDeleted

**Event storm risk:** Site delete → N personnels each raising PersonnelDeletedDomainEvent → N integration publishes. Acceptable for moderate N; huge site → consider bulk flag + single summary event (future optimization).

---

## Deep dive — idempotency

```csharp
if (IsDeleted) return; // SoftDelete
if (!IsDeleted) return; // Restore
```

Integration handler dobare soft-delete → no-op. Inbox consumer retry safe (ba inbox idempotency Day 23).

`AlreadyDeleted` Conflict error = **user-facing** duplicate click on UI delete — not for event handlers (handlers should be quiet no-op).

---

## Deep dive — UI / API semantics

| API | expected |
|---|---|
| DELETE /personnels/{id} | SoftDelete; 200/204; later GET 404 |
| GET list | never shows IsDeleted=true |
| Admin «recycle bin» | IgnoreQueryFilters + IsDeleted + permission |
| Restore | rare endpoint; unique conflict possible |

FE: after delete invalidate TanStack Query keys — list refetch bedune row.

---

## Deep dive — reporting

Reporting module sometimes builds dynamic SQL with `filterSoftDeleted: true/false` fallback — age column `is_deleted` nabashe, retry bedune filter. Practical vali fragile: mixed tables. Prefer schema knowing which tables soft-deletable.

---

## Senario whiteboard

### 1) Rehire same national code

```
P1 national=001 active
SoftDelete P1
Create P2 national=001 → OK (partial unique)
P1 still in DB is_deleted=true
```

### 2) Forget query filter on new entity

```
New entity implements ISoftDeletable
Forgot — ApplySoftDeleteQueryFilters uses reflection on ISoftDeletable
→ actually auto-applied IF interface implemented + OnModelCreating calls Apply*
Inventory: Apply* missing entirely → smell
```

### 3) ExecuteUpdate without events

```
Bulk SetProperty IsDeleted=true
Outbox empty
Other modules stale copies still «alive»
→ only use when no fan-out needed
```

### 4) Hard Remove by mistake

```
context.Personnels.Remove(p); SaveChanges
→ physical DELETE
→ FK may Restrict fail
→ or orphan history
→ prefer SoftDelete method
```

---

## Comparison — soft delete strategies

| strategy | Dejban? | note |
|---|---|---|
| IsDeleted flag | **yes** | main |
| DeletedAt only (null = live) | no | flag clearer for indexes |
| Status=Deleted enum | partial | EmploymentStatus separate |
| Shadow state EF | no | explicit properties |
| Interceptor convert Remove | no | explicit SoftDelete() |
| Separate archive table | no | |
| Temporal tables | no | |

---

## Glossary soft-delete

| kalame | ma'ni |
|---|---|
| Soft delete | flag, row mimone |
| Hard delete | DELETE SQL |
| Tombstone | deleted marker row |
| Partial / filtered unique | unique among live |
| Global query filter | auto WHERE |
| Cascade soft delete | children soft via events |
| Purge | later hard delete job |
| Restore | clear flag |
| Idempotent delete | second call no-op |

---

## Mini lab

1. Delete personnel az UI; SQL: `SELECT is_deleted, deleted_at FROM ...`
2. List API — id nabayad biad
3. `IgnoreQueryFilters` query in LINQPad/IDE — row hast
4. Follow Rabbit/inbox: Vehicles personnel copy IsDeleted
5. Try recreate same national code — should succeed

---

## Common bugs

| bug | symptom | fix |
|---|---|---|
| Remove() instead of SoftDelete | FK error or gone row | domain method |
| Unique without filter | cannot rehire | HasFilter is_deleted=false |
| ExecuteUpdate cascade | other modules stale | domain SoftDelete + events |
| IgnoreQueryFilters | deleted in lists / leaks | re-add Where |
| AlreadyDeleted never hits | expected with filters | OK or use Ignore for admin |
| DeletedBy null | audit gap | set in SoftDelete |
| Restore without unique check | conflict 23505 | validate before Restore |

---

## Connection to previous / next days

| day | rabt |
|---|---|
| 03 OOP | encapsulation SoftDelete method |
| 04 SQL | partial unique indexes |
| 12 DDD | SoftDelete raises domain event |
| 13 EF | named HasQueryFilter |
| 14 Repo | SoftDeleteBySiteId on repos |
| **[16 Tenant](./day-16-multi-tenancy.md)** | TenantFilter + SoftDeleteFilter together; IgnoreQueryFilters risk; super-admin unscoped |
| 19–23 Messaging | SoftDeleted integration events + outbox/inbox |

---

## Smell-ha

1. **Inventory bedune soft-delete filter** — inconsistent
2. **DeletedBy commented** on Personnel SoftDelete — audit incomplete
3. **ForEachAsync SoftDelete** on large site — memory/tracker heavy; no bulk ExecuteUpdate when events not needed in read-models
4. **IgnoreQueryFilters without re-applying tenant** — security smell
5. **Mix hard Remove + soft SoftDelete** in same handler — correct sometimes, confusing without comments
6. **Restore cascade incomplete** vs delete cascade rich
7. **`if (personnel.IsDeleted)` after GetAsync** — query filter already hides deleted → Get returns null unless IgnoreFilters; AlreadyDeleted path rarely hits via normal Get (unless tracked same request / race)
8. **Duplicate SoftDeleteBy\* across 6+ module PersonnelRepository copies** — DRY smell (acceptable for modular isolation)
9. **Reporting dual path** filterSoftDeleted true/false fallback — fragile
10. **No automatic Convert Remove→SoftDelete** — developer must call SoftDelete (good for explicitness, bad if someone calls `Remove`)

---

## 25 soal-e mosahebe

1. **Soft delete chie?** — Flag instead of DELETE
2. **Chera?** — Recover, audit, FK, reuse keys
3. **Global query filter?** — Auto `WHERE is_deleted = false`
4. **IgnoreQueryFilters?** — Bypass all filters — re-check tenant/soft manually
5. **Partial unique?** — Unique among live rows only
6. **Chera na full unique?** — Soft-deleted would block reuse
7. **Domain SoftDelete vs IsDeleted = true?** — Encapsulation + events
8. **Idempotent SoftDelete?** — `if (IsDeleted) return`
9. **Cascade cross-module?** — Integration events
10. **ExecuteUpdate vs SoftDelete()?** — Bulk no events vs domain path
11. **Hard delete koja?** — Links, purge, logs
12. **Named query filters?** — SoftDeleteFilter vs TenantFilter separate keys
13. **Soft delete + multi-tenancy?** — Two filters; Ignore kills both
14. **DeletedAt / DeletedBy?** — Audit columns
15. **Restore?** — Clear flag; may need unique conflict check
16. **List API deleted?** — IgnoreQueryFilters + IsDeleted filter + auth
17. **Index on IsDeleted?** — Optional; filter already excludes most queries
18. **GDPR?** — Soft ≠ erase; need purge policy
19. **EF Remove accident?** — Physical delete if someone Remove() — conventions/interceptor optional guard
20. **Testing soft delete?** — Assert IsDeleted + event published; query without Ignore returns empty
21. **Event storm on Site delete?** — N personnel events; bulk alternative
22. **AlreadyDeleted vs NotFound?** — filter hides deleted → usually NotFound
23. **ISoftDeletable minimal?** — only getter; mutation via methods
24. **Inbox retry + SoftDelete?** — idempotent domain method
25. **Reporting soft-deleted rows?** — explicit include flag + auth

---

## Resume

**short:**

> Implemented soft-delete persistence across a modular monolith: `ISoftDeletable` entities, named EF Core global query filters, filtered unique indexes, domain `SoftDelete`/`Restore` methods that raise events, and cross-module cascade via `*SoftDeleted` integration events.

**bullets:**

- Centralized soft-delete filters with `ApplySoftDeleteQueryFilters` reflection over `ISoftDeletable` entity types
- Encapsulated delete in domain (`Personnel.SoftDelete`) producing domain → integration events for other modules' local copies
- Designed PostgreSQL partial unique indexes (`WHERE is_deleted = false`) for national/personnel/access codes
- Used `IgnoreQueryFilters` only for purge/admin paths with explicit re-filtering where required

**skills:** `Soft Delete, EF Core Global Query Filters, Partial Unique Indexes, Domain Events, Integration Events, PostgreSQL, Clean Architecture`

---

## File-haye mohem

| chi | koja |
|---|---|
| ISoftDeletable | `Common/Tenancy/ISoftDeletable.cs` |
| Filter names | `Common/Tenancy/GlobalQueryFilterNames.cs` |
| Apply filters | `Common/Tenancy/SoftDeleteQueryFilterExtensions.cs` |
| Personnel SoftDelete/Restore | `Personnels.Domain/Personnels/Personnel.cs` |
| Delete command | `Personnels.Application/.../DeletePersonnelCommandHandler.cs` |
| Domain→integration | `.../PersonnelDeletedDomainEventHandler.cs` |
| Integration contract | `Common/EventBus/Contracts/Events/PersonnelSoftDeleted.cs` (+ Site/Unit) |
| Filtered indexes | `Personnels.Infrastructure/Personnels/PersonnelConfiguration.cs` |
| SoftDeleteBySiteId | `Personnels.Infrastructure/Personnels/PersonnelRepository.cs` |
| Vehicles cascade | `Vehicles.Presentation/Personnels/PersonnelDeletedIntegrationEventHandler.cs` |
| BlackList soft/hard | `Visitors.Infrastructure/Visitors/BlackListRepository.cs` |
| DbContext apply | e.g. `PersonnelsDbContext.OnModelCreating` |
| Inventory gap | `InventoryDbContext` (no ApplySoftDelete) |

---

## Day 16 preview — chera ba soft-delete joft mishe?

Soft-delete filter = «row haye zende». Tenant filter = «row haye site-e man». Har do **named** (`SoftDeleteFilter`, `TenantFilter`) — EF mitone yeki ra ignore kard (modern API).

**Admin query pattern:**

```csharp
db.Personnels
    .IgnoreQueryFilters()
    .Where(p => p.IsDeleted && tenantIds.Contains(p.SiteId));
```

Bedune `SiteId` dasti → **data leak** az site digar. **[Day 16](./day-16-multi-tenancy.md)** middleware `TenantContext` + claim + header ra kamel mifrestad.

**EF layer:** [Day 13 — global filters](./day-13-ef-core-npgsql.md) | **Repo bypass:** [Day 14](./day-14-repository-unit-of-work.md)

---

*Day 15 tamum. Ba'd: [Day 16 — Multi-tenancy (`X-Site-Id`)](./day-16-multi-tenancy.md) (amade). Fehrest: [README.md](./README.md).*
