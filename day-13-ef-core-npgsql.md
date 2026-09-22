# Day 13 — EF Core 10 + Npgsql (multi-schema, migrations)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

EF Core = ORM-e .NET. Tu Dejban: **EF Core 10 + Npgsql 10** roye PostgreSQL. Modular monolith = **1 database, 8 schema**, har module `DbContext`-e khodesh. Soft-delete + multi-tenancy ba **named global query filters**. Domain event-ha ba `SaveChangesInterceptor` miran to outbox. Migration-ha **server-side (migrationesho)** — entity change commit mishe, Migration class to repo commit **nemishe**.

---

# BAKHSH-E AVAL: WORLD — EF Core + PostgreSQL to donya

## ORM chie? Chera EF Core?

| approach | chi | trade-off |
|---|---|---|
| **Raw SQL / Dapper** | control, performance | boilerplate, type-safety kam |
| **EF Core** | LINQ → SQL, change tracking, migrations | abstraction cost, N+1 risk |
| **Hybrid** | EF write + Dapper read/hot path | Dejban in style-e (Day 14) |

EF Core:
1. **DbContext** = session + Unit of Work
2. **Change Tracker** = midone chi Added/Modified/Deleted-e
3. **Migrations** = schema evolution as code
4. **LINQ provider** = `IQueryable` → SQL

---

## DbContext lifecycle

```csharp
services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(connectionString));
```

- Default lifetime: **Scoped** (1 per HTTP request)
- Singleton = disaster (thread-unsafe + stale)
- Transient = no shared Unit of Work

```
Request → resolve DbContext → query/mutate → SaveChanges → dispose
```

---

## Change tracking & SaveChanges

```csharp
var person = await db.Personnels.FirstAsync(p => p.Id == id); // tracked
person.UpdateName("Ali");  // Modified detected
await db.SaveChangesAsync(); // UPDATE ...
```

| state | meaning |
|---|---|
| Detached | na tracked |
| Unchanged | tracked, no change |
| Added | INSERT |
| Modified | UPDATE |
| Deleted | DELETE |

**`AsNoTracking()`** — read-only, faster, no tracker. Query handlers almost always.

---

## Fluent API vs Data Annotations

```csharp
// Annotations (on entity) — couples Domain to EF
[Table("Personnels")]
[Required]
public string Name { get; set; }

// Fluent API (IEntityTypeConfiguration) — Domain stays pure ✅
builder.Property(e => e.Name).IsRequired();
```

**Best practice:** Fluent API to Infrastructure. Domain project EF reference **nadare**.

---

## Relationships

```csharp
builder.HasOne(e => e.Site)
    .WithMany()
    .HasForeignKey(e => e.SiteId)
    .OnDelete(DeleteBehavior.Restrict);  // no cascade wipe
```

| DeleteBehavior | SQL effect |
|---|---|
| Cascade | delete children |
| Restrict / NoAction | FK block |
| SetNull | child FK → null |
| ClientCascade | in-memory only |

**Shadow property:** FK in model bedune property on class:

```csharp
builder.HasMany(v => v.Ownerships)
    .WithOne()
    .HasForeignKey("VehicleId");  // shadow
```

---

## Owned types & JSON columns

```csharp
// Owned — columns in parent table (or owned table)
builder.OwnsOne(v => v.VehiclePlate, plate =>
{
    plate.Property(p => p.Value).HasColumnName("PlateNumber");
});

// JSON — PostgreSQL jsonb
builder.OwnsOne(e => e.SessionInfo, b => b.ToJson());
builder.OwnsMany(e => e.Companions, b => b.ToJson());
```

**Kei JSON?** Nested document, flexible shape, kam query by inner field.  
**Kei Owned columns?** Simple VO, indexed property, filter/sort.

---

## Global query filters

```csharp
modelBuilder.Entity<Personnel>()
    .HasQueryFilter(p => !p.IsDeleted);

// Named filters (.NET 10 / modern EF):
modelBuilder.Entity<Personnel>()
    .HasQueryFilter("SoftDelete", p => !p.IsDeleted);
```

Automatic `WHERE` on every query. Bypass: `.IgnoreQueryFilters()`.

**Use cases:** soft delete, multi-tenancy, multi-language.

---

## Interceptors

```csharp
public class AuditInterceptor : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(...)
    {
        // before SQL: stamp UpdatedAt, collect domain events
        return base.SavingChangesAsync(...);
    }
}

options.AddInterceptors(new AuditInterceptor());
```

Alternatives: override `SaveChanges` on DbContext, domain events manually.

---

## Migrations (World)

```bash
dotnet ef migrations add AddPersonnelsTable -p Infrastructure -s Api
dotnet ef database update
```

Creates:
- `YYYYMMDDHHMMSS_Name.cs` — Up/Down
- `*.Designer.cs`
- `*ModelSnapshot.cs` — full model fingerprint

**Production strategies:**
1. Apply at deploy (`Migrate()`)
2. Generate SQL scripts, DBA review
3. Separate migrator job / migrationesho

**Never** auto-migrate production from every app instance without care (race, lock).

---

## Multi-schema (PostgreSQL)

```sql
CREATE SCHEMA personnels;
CREATE SCHEMA visitors;
-- tables: personnels.personnels, visitors.visitors
```

EF:

```csharp
modelBuilder.HasDefaultSchema("personnels");

options.UseNpgsql(cs, o =>
    o.MigrationsHistoryTable("__EFMigrationsHistory", "personnels"));
```

Har schema history table-e khodesh → module-ha independent migrate mishan.

---

## Performance essentials

| tip | chi |
|---|---|
| `AsNoTracking` | reads |
| `Select` projection | na `SELECT *` |
| `AsSplitQuery` | avoid cartesian explosion on multi-Include |
| `ExecuteUpdate` / `ExecuteDelete` | bulk without load |
| Index + filtered unique | soft-delete friendly uniqueness |
| Avoid N+1 | Include or explicit join / projection |
| Compiled models | startup speed (large models) |

```csharp
await db.Doors
    .Where(d => d.SiteId == siteId)
    .ExecuteUpdateAsync(s => s.SetProperty(d => d.IsDeleted, true));
```

---

## Npgsql specifics

- Provider: `Npgsql.EntityFrameworkCore.PostgreSQL`
- Types: `uuid`, `jsonb`, `uuid[]`, `timestamp with time zone`
- `NpgsqlDataSource` — modern pooling entry (reuse connections)
- Naming: `EFCore.NamingConventions` → snake_case columns

```csharp
new NpgsqlDataSourceBuilder(cs).Build(); // singleton pool
options.UseNpgsql(cs).UseSnakeCaseNamingConvention();
```

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **Compiled models** — faster startup
- **EFCore.BulkExtensions** — massive insert/update
- **Temporal tables** — history built-in
- **FromSqlRaw / SqlQuery** — raw SQL typed — Dejban kam/nist for EF
- **DbContext pooling** (`AddDbContextPool`) — Dejban standard AddDbContext
- **Second-level cache** — EFPlus etc.
- **Multiple providers** (SQL Server + Postgres) — faghat Postgres
- **Explicit MaxPoolSize tuning** on DataSource — defaults

---

# BAKHSH-E DOVOM: DEJBAN — EF Core to in proje

## Version

```xml
<!-- Directory.Packages.props -->
Microsoft.EntityFrameworkCore          10.0.0
Npgsql.EntityFrameworkCore.PostgreSQL  10.0.0
EFCore.NamingConventions               10.0.0-rc.2
Npgsql.OpenTelemetry                   10.0.0
```

---

## Architecture: 1 DB, 8 schema, 8 DbContext

```
payamgostar_dejban (PostgreSQL)
├── personnels.*
├── visitors.*
├── vehicles.*
├── armory.*
├── cash_logistics.*
├── inventory.*
├── security_patrols.*
└── weigh_bridge.*
```

Har module:

| piece | mesal |
|---|---|
| Schema const | `Schemas.Visitors = "visitors"` |
| DbContext | `VisitorsDbContext` |
| History table | `visitors.__EFMigrationsHistory` |
| Interceptor | `InsertOutboxMessagesInterceptor` |
| UoW | `IUnitOfWork` → same DbContext |

Standalone services (Identity, ACL, DCC, Gate, RequestTracker, Reporting own DB) → **public** schema, 1 `ApplicationDbContext`.

---

## Registration pattern (Dejban module)

```csharp
// File: Personnels.Infrastructure/PersonnelsModule.cs

services.AddDbContext<PersonnelsDbContext>((sp, options) =>
    options
        .UseNpgsql(
            configuration.GetConnectionString("Postgres"),
            npgsqlOptions => npgsqlOptions
                .MigrationsHistoryTable(
                    HistoryRepository.DefaultTableName,
                    Schemas.Personnels))
        .AddInterceptors(sp.GetRequiredService<InsertOutboxMessagesInterceptor>())
        .UseSnakeCaseNamingConvention());

services.AddScoped<IUnitOfWork>(sp =>
    sp.GetRequiredService<PersonnelsDbContext>());
```

**Chera MigrationsHistoryTable per schema?**  
Bedune in, hame module-ha `__EFMigrationsHistory` to `public` → conflict. Ba schema: har module migration history-e joda.

---

## DbContext example

```csharp
// File: Personnels.Infrastructure/Database/PersonnelsDbContext.cs

public sealed class PersonnelsDbContext(
    DbContextOptions<PersonnelsDbContext> options,
    ITenantContext tenantContext)
    : DbContext(options), IUnitOfWork, ITenantDbContext
{
    internal DbSet<Personnel> Personnels { get; set; }
    internal DbSet<Site> Sites { get; set; }
    // ...

    public HashSet<Guid> TenantIds => tenantContext.SiteIds;
    public bool IsSuperAdmin => tenantContext.IsSuperAdmin;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema(Schemas.Personnels);

        modelBuilder.ApplyConfiguration(new PersonnelConfiguration());
        // ... configs, outbox, inbox

        modelBuilder.ApplyTenantQueryFilters(this);
        modelBuilder.ApplySoftDeleteQueryFilters();
    }
}
```

**`internal DbSet`** — Application via repository, na direct DbSet from Presentation.

**Smell:** `InventoryDbContext` tenant/soft-delete filter **nadare** — inconsistent.

---

## IEntityTypeConfiguration — rich examples

### Vehicle — OwnsOne + field access + shadow FK

```csharp
// File: Vehicles.Infrastructure/Vehicles/VehicleConfiguration.cs

builder.ToTable("Vehicles");

builder.OwnsOne(v => v.VehiclePlate, plate =>
{
    plate.Property(p => p.Value)
        .HasColumnName("PlateNumber")
        .IsRequired();
});

builder.OwnsOne(v => v.CargoDetails, /* ... */);
builder.OwnsOne(v => v.ConstructionDetails, /* ... */);

builder.HasMany(v => v.Ownerships)
    .WithOne()
    .HasForeignKey("VehicleId");  // shadow

builder.Metadata
    .FindNavigation(nameof(Vehicle.Ownerships))!
    .SetPropertyAccessMode(PropertyAccessMode.Field);
// → EF writes to private _ownerships list (Day 12 encapsulation)

builder.HasOne<Site>()
    .WithMany(s => s.Vehicles)
    .HasForeignKey(v => v.SiteId)
    .OnDelete(DeleteBehavior.Restrict);

builder.Ignore(v => v.DomainEvents);  // na mapped to DB
```

### Personnel — filtered unique + uuid[]

```csharp
// File: Personnels.Infrastructure/Personnels/PersonnelConfiguration.cs

builder.Property(e => e.IsDeleted)
    .IsRequired()
    .HasDefaultValue(false);

builder.HasIndex(e => e.PersonnelCode)
    .IsUnique()
    .HasFilter("\"is_deleted\" = false");

builder.HasIndex(e => e.NationalCode)
    .IsUnique()
    .HasFilter("\"is_deleted\" = false");

builder.PrimitiveCollection(e => e.ContractIds)
    .HasColumnType("uuid[]")
    .IsRequired(false);
```

**Chera filtered unique?** Soft-deleted row ba haman code mojaz. Index: unique among **active** only.

### JSON owned — Site / Session / Companions

```csharp
// Personnels Site:
builder.OwnsOne(e => e.CEO, c => c.ToJson());
builder.OwnsOne(e => e.Supervisor, c => c.ToJson());
builder.OwnsMany(e => e.ContractorBoardMembers, c => c.ToJson());

// Identity ApplicationUserToken:
entity.OwnsOne(e => e.SessionInfo, si => si.ToJson());

// Visitors VisitSchedule:
builder.OwnsMany(e => e.Companions, c => c.ToJson());
```

PostgreSQL `jsonb` — flexible nested docs.

---

## Global query filters

### Soft delete

```csharp
// File: Common/Tenancy/SoftDeleteQueryFilterExtensions.cs

public static void ApplySoftDeleteQueryFilters(this ModelBuilder modelBuilder)
{
    foreach (var entityType in modelBuilder.Model.GetEntityTypes())
    {
        if (!typeof(ISoftDeletable).IsAssignableFrom(entityType.ClrType))
            continue;

        // reflection → HasQueryFilter("SoftDeleteFilter", e => !e.IsDeleted)
    }
}
```

Har entity ke `ISoftDeletable` implement kone → automatic filter.

### Tenant (X-Site-Id)

```csharp
// File: Common/Tenancy/TenantQueryFilterExtensions.cs

// For ISiteEntity:
// SuperAdmin + no site selected → all
// Else → SiteId IN TenantIds (from TenantContext middleware)
```

DbContext inject `ITenantContext` → filter expression property-ha ra mikhone at query time.

**Bypass:** admin tooling / inbox jobs sometimes `IgnoreQueryFilters()` — careful.

---

## Interceptor — transactional outbox

```csharp
// File: Dejban.Common.Infrastructure/Outbox/InsertOutboxMessagesInterceptor.cs

public sealed class InsertOutboxMessagesInterceptor : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(...)
    {
        if (eventData.Context is not null)
            InsertOutboxMessages(eventData.Context);
        return base.SavingChangesAsync(...);
    }

    private static void InsertOutboxMessages(DbContext context)
    {
        var outboxMessages = context.ChangeTracker
            .Entries<Entity>()
            .Select(e => e.Entity)
            .SelectMany(entity =>
            {
                var events = entity.DomainEvents;
                entity.ClearDomainEvents();
                return events;
            })
            .Select(domainEvent => new OutboxMessage { /* serialize */ })
            .ToList();

        context.Set<OutboxMessage>().AddRange(outboxMessages);
    }
}
```

**Same transaction:** entity INSERT + outbox INSERT. Quartz later publish. (Day 12 / 38)

Standalone services: MassTransit EF Outbox tables — different mechanism (Day 39).

---

## NpgsqlDataSource (Dapper path)

```csharp
// File: Dejban.Common.Infrastructure/InfrastructureConfiguration.cs

NpgsqlDataSource npgsqlDataSource =
    new NpgsqlDataSourceBuilder(databaseConnectionString).Build();
services.TryAddSingleton(npgsqlDataSource);
services.TryAddScoped<IDbConnectionFactory, DbConnectionFactory>();
```

EF az connection string use mikone; Dapper az DataSource. Do stack parallel — pool separate. OpenTelemetry: `.AddNpgsql()` + `.AddEntityFrameworkCoreInstrumentation()`.

---

## IUnitOfWork

```csharp
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    EntityEntry<TEntity> Entry<TEntity>(TEntity entity) where TEntity : class;
}

// PersonnelsDbContext : DbContext, IUnitOfWork, ITenantDbContext
services.AddScoped<IUnitOfWork>(sp =>
    sp.GetRequiredService<PersonnelsDbContext>());
```

Command handlers `IUnitOfWork` inject mikonan — Domain/Application az `DbContext` concrete depend **nakonan**.

---

## Features used in practice

| feature | koja |
|---|---|
| `AsNoTracking` | query handlers |
| `Include` / `ThenInclude` | repositories |
| `AsSplitQuery` | GetVisits, CameraAuth, RequestTracker |
| `ExecuteUpdate` / `ExecuteDelete` | Door soft-delete, bulk ops |
| `OwnsOne` / `OwnsMany` | Vehicle, Weighing, Site |
| `ToJson()` | SessionInfo, Companions, ACL configs |
| `PrimitiveCollection` / `uuid[]` | ContractIds |
| `HasConversion<string>()` | enums as text |
| `PropertyAccessMode.Field` | private `_ownerships` |
| Snake_case naming | Dejban + Reporting Dejban contexts |

**Nist:** `FromSqlRaw`, compiled models, bulk extensions, temporal tables.

---

## Reporting — multi-DbContext read model

```csharp
// File: Reporting/Program.cs

builder.Services.AddDbContext<ApplicationDbContext>(/* own Postgres */);

builder.Services.AddDbContext<PersonnelsDbContext>(o =>
    o.UseNpgsql(dejbanConnectionString).UseSnakeCaseNamingConvention());
// + Vehicles, Armory, Visitors, ... (8 schemas)
builder.Services.AddDbContext<IdentityServerDbContext>(o =>
    o.UseNpgsql(identityConnectionString));
```

Reporting **read-only** cross-DB: Dejban schemas + Identity. Bypass module APIs — smell (Day 10) vali pragmatism for Stimulsoft reports.

---

## Migrations workflow — MOHEM

### Policy (workspace rule)

1. **Do:** entity + Fluent config + validators change
2. **Do not commit:** new `Migration` / Designer / ModelSnapshot for schema change
3. Server **migrationesho** ba'd az deploy migration misaze/apply mikone
4. Local testing: temp migration OK → **ghabl az commit pak kon**

### Reality check

Repo **alan** Migration folder + ModelSnapshot dare (historical). Policy baraye **change-haye jadid**: entity-only PR, na migration file.

### Runtime apply (dev)

```csharp
// File: Dejban.Api/Extensions/MigrationExtensions.cs

public static async Task ApplyMigrations(this IApplicationBuilder app)
{
    using var scope = app.ApplicationServices.CreateScope();
    ApplyMigration<VisitorsDbContext>(scope);
    ApplyMigration<PersonnelsDbContext>(scope);
    // ... all 8
}

private static void ApplyMigration<TDbContext>(IServiceScope scope)
    where TDbContext : DbContext
{
    using var context = scope.ServiceProvider.GetRequiredService<TDbContext>();
    context.Database.Migrate();
}
```

Standalone: `DbInitializer` → `MigrateAsync()` + seed.

**Production:** migrationesho / controlled apply — na blindly every replica.

---

## Standalone vs Dejban comparison

| | Dejban modules | Identity / ACL / DCC |
|---|---|---|
| Schema | named (`personnels`, …) | `public` |
| History table | schema-scoped | default public |
| Outbox | custom interceptor + tables | MassTransit EF outbox |
| Naming | snake_case | default / mixed |
| Soft-delete filter | yes (most) | Identity/ACL yes, DCC no |
| Tenant filter | yes | yes |
| Base | `DbContext` + UoW | Identity: `IdentityDbContext` |

---

## Smell-ha

1. **Inventory filters missing** — soft-delete/tenant inconsistent
2. **EF + NpgsqlDataSource dual pools** — na shared connection factory
3. **Reporting direct schema read** — coupling
4. **Migrations in repo vs policy** — historical noise; new PRs shouldn't add them
5. **ApplyMigrations on startup** — race if multi-instance without care
6. **No compiled models** — cold start larger models slower
7. **No FromSqlRaw escape hatch** — complex reports sometimes need it
8. **Filtered index raw SQL string** — tied to snake_case column names
9. **Ignore DomainEvents** per config — easy to forget on new entity
10. **Shadow FK strings** — rename-fragile (`"VehicleId"`)
11. **JSON ToJson hard to index** — query inside jsonb slower
12. **NamingConventions rc.2** — package still RC while EF 10 stable

---

## 20 soal-e mosahebe

1. **DbContext lifetime?** — Scoped. Never Singleton
2. **Change Tracker chie?** — Tracks entity state for SaveChanges
3. **AsNoTracking?** — No tracker, faster reads
4. **OwnsOne vs relationship?** — Owned = part of aggregate; no own identity table (usually)
5. **ToJson()?** — Map owned type to jsonb column
6. **Global query filter?** — Auto WHERE (soft delete, tenant)
7. **IgnoreQueryFilters?** — Bypass — use carefully
8. **Filtered unique index?** — Unique among non-deleted rows
9. **Shadow property?** — FK/column bedune CLR property
10. **SaveChangesInterceptor?** — Hook before/after SQL — outbox
11. **Multi-schema chera?** — Module isolation in one DB
12. **MigrationsHistoryTable per schema?** — Independent migration streams
13. **ExecuteUpdate?** — Bulk UPDATE without loading entities
14. **AsSplitQuery?** — Multiple SQL instead of cartesian Join
15. **N+1 chie?** — Loop queries; fix with Include/projection
16. **Unit of Work = DbContext?** — Yes in Dejban via IUnitOfWork
17. **Snake_case?** — EFCore.NamingConventions ↔ Postgres style
18. **NpgsqlDataSource?** — Modern pooled connection source
19. **Chera migration to PR nist?** — Server migrationesho owns schema apply
20. **IdentityDbContext vs DbContext?** — Identity adds AspNetUsers/Roles tables

---

## Resume

**short:**

> Built EF Core 10 / Npgsql 10 persistence for an 8-schema modular monolith: per-module DbContexts with schema-scoped migration history, named soft-delete and tenant query filters, owned/JSON types, and a SaveChanges interceptor that writes domain events to the transactional outbox.

**bullets:**

- Configured multi-schema PostgreSQL isolation (`HasDefaultSchema` + `MigrationsHistoryTable` per module) with snake_case naming conventions
- Implemented named global query filters for soft delete (`ISoftDeletable`) and site multi-tenancy (`ITenantDbContext`)
- Mapped rich aggregates via Fluent API: `OwnsOne` value objects, `ToJson()` documents, shadow FKs, field-access private collections, filtered unique indexes, `uuid[]` primitive collections
- Wired `InsertOutboxMessagesInterceptor` so domain events persist atomically with `SaveChanges`; used `ExecuteUpdate`/`AsSplitQuery`/`AsNoTracking` on hot paths

**skills:** `EF Core 10, Npgsql, PostgreSQL Schemas, Fluent API, Global Query Filters, Owned Types, JSON Columns, SaveChanges Interceptor, Migrations, Soft Delete, Multi-tenancy`

---

## File-haye mohem

| chi | koja |
|---|---|
| Package versions | `Directory.Packages.props` |
| Module DI + UseNpgsql | `Personnels.Infrastructure/PersonnelsModule.cs` (va siblings) |
| DbContext | `Personnels.Infrastructure/Database/PersonnelsDbContext.cs` |
| Schemas | `*/Infrastructure/Database/Schemas.cs` |
| Soft-delete filters | `Common/Tenancy/SoftDeleteQueryFilterExtensions.cs` |
| Tenant filters | `Common/Tenancy/TenantQueryFilterExtensions.cs` |
| Outbox interceptor | `Dejban.Common.Infrastructure/Outbox/InsertOutboxMessagesInterceptor.cs` |
| NpgsqlDataSource | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| Vehicle Fluent config | `Vehicles.Infrastructure/Vehicles/VehicleConfiguration.cs` |
| Personnel Fluent config | `Personnels.Infrastructure/Personnels/PersonnelConfiguration.cs` |
| ApplyMigrations | `Dejban.Api/Extensions/MigrationExtensions.cs` |
| Reporting multi-context | `Reporting/Program.cs` |
| SessionInfo JSON | `IdentityServer/.../ApplicationUserTokenConfiguration.cs` |
| IUnitOfWork | `*/Application/Abstractions/Data/IUnitOfWork.cs` |

---

## Owned types — deep dive (Dejban patterns)

### OwnsOne as column vs separate table

| mapping | SQL shape | Dejban mesal |
|---|---|---|
| `OwnsOne` + column names | parent table extra columns | `VehiclePlate` → `plate_number` |
| `OwnsOne` nested | still flattened or owned table | `CargoDetails`, `ConstructionDetails` |
| `OwnsMany` + `ToJson()` | one `jsonb` column | `Companions`, `ContractorBoardMembers` |
| Shadow FK on collection | child table, FK string | `Vehicle.Ownerships` → `"VehicleId"` |

**Value object rule (Day 12):** owned type **no** separate identity — part of aggregate root. EF `OwnsOne` = «in-memory composition persisted».

### PropertyAccessMode.Field

Vehicle ownership list private `_ownerships` — EF writes via field, na public property. Config:

```csharp
builder.Metadata.FindNavigation(nameof(Vehicle.Ownerships))!
    .SetPropertyAccessMode(PropertyAccessMode.Field);
```

**Smell:** agar field access forget koni → empty collection on load.

### When **not** to use ToJson()

- Filter/sort heavy on inner field → flattened columns or computed column
- Large array growth unbounded → separate table + index
- Cross-row query on JSON path → slow without GIN index (Dejban mostly stores, na query inside json)

---

## Interceptors — lifecycle + alternatives

```
SaveChangesAsync called
  → SavingChangesAsync (interceptor)  ← InsertOutboxMessages here
  → SQL generated + sent
  → SavedChangesAsync (optional)
```

| approach | pro | con |
|---|---|---|
| `SaveChangesInterceptor` | clean, testable, all DbContexts | order of interceptors matters |
| Override `SaveChanges` on DbContext | simple | duplicate across 8 contexts |
| Domain event dispatch **after** SaveChanges | no same-tx outbox | **lost event** if crash |

Dejban: **before** SQL — collect `DomainEvents` from tracked `Entity`, clear, insert `OutboxMessage` rows → **atomic** with business write.

**Standalone services:** MassTransit EF outbox uses different tables + dispatcher — na `InsertOutboxMessagesInterceptor`.

---

## Naming conventions — snake_case end-to-end

```csharp
options.UseNpgsql(cs).UseSnakeCaseNamingConvention();
```

| CLR | Postgres (typical) |
|---|---|
| `PersonnelCode` | `personnel_code` |
| `IsDeleted` | `is_deleted` |
| `SiteId` | `site_id` |

**Filtered index strings must match DB names:**

```csharp
.HasFilter("\"is_deleted\" = false");  // quoted lowercase
```

**Package:** `EFCore.NamingConventions` 10.0.0-rc.2 — still RC; watch upgrades.

**Reporting:** multiple Dejban DbContexts all `UseSnakeCaseNamingConvention()` when pointing at `payamgostar_dejban`.

**Identity/ACL:** mixed — some default Pascal columns in older tables; new code prefer snake on Dejban side.

---

## Multi-schema — rules of the road

1. **`HasDefaultSchema(Schemas.X)`** on every module DbContext.
2. **`MigrationsHistoryTable(..., schema)`** — har module migration stream joda.
3. **No cross-schema FK** in practice — Site copy per module, sync via event.
4. **Join cross-schema** technically mumken on same connection string — **avoid** (coupling smell); Reporting exception for read-only reports.

Schema name map:

| module | schema const |
|---|---|
| Personnels | `personnels` |
| Visitors | `visitors` |
| Vehicles | `vehicles` |
| Armory | `armory` |
| CashLogistics | `cash_logistics` |
| Inventory | `inventory` |
| SecurityPatrols | `security_patrols` |
| WeighBridge | `weigh_bridge` |

---

## migrationesho — workflow (team policy)

**Commit to git:** entity, `IEntityTypeConfiguration`, validators, handlers.  
**Do NOT commit:** new `*Migration*.cs`, Designer, ModelSnapshot **for schema changes you introduce**.

**Server:** migrationesho after deploy generates/applies migration against target DB.

**Local dev:** `ApplyMigrations()` on Dejban.Api startup runs 8 contexts — convenient, risky if 2 instances race.

**Historical repo:** old Migration folders exist — **new PRs** entity-only. Ghabl az push: pak kon migration-e local test.

**Interview:** «Schema evolution is server-owned so developers don't fight over snapshot merge conflicts and prod apply is controlled.»

---

## Inventory module — filter gap (smell + fix)

`InventoryDbContext.OnModelCreating`:

- ✅ `HasDefaultSchema`, Fluent configs, outbox/inbox tables
- ❌ `ApplySoftDeleteQueryFilters()` — **missing**
- ❌ `ApplyTenantQueryFilters(this)` — **missing**
- ❌ `ITenantContext` inject — DbContext faghat `DbContextOptions`

**Impact:**

| entity | risk |
|---|---|
| No `ISoftDeletable` on Inventory domain yet | soft-delete story incomplete module-wide |
| No tenant filter | warehouse/product queries **cross-site leak** if API bug |
| Reporting reads `inventory` schema direct | same data, separate context |

**Fix direction (conceptual):** align with `PersonnelsDbContext`: inject `ITenantContext`, call both filter extensions, mark site-scoped entities `ISiteEntity`, add `ISoftDeletable` where delete = soft (Day 15 + [Day 16](./day-16-multi-tenancy.md)).

**Cross-link:** [Day 15 — Inventory gap](./day-15-soft-delete.md#smell-ha) | [Day 16 — TenantFilter](./day-16-multi-tenancy.md)

---

## 10 soal-e ezafe (mosahebe)

21. **Chera Fluent API na Data Annotations?** — Domain pure, mapping Infrastructure
22. **DbContextPool chera na darim?** — standard Scoped AddDbContext; pool for high churn APIs optional
23. **Difference Outbox interceptor vs MT EF outbox?** — custom table + Quartz vs MT tables + bus
24. **Chera internal DbSet?** — force repository boundary
25. **JSON companion list query?** — rare; mostly display-only
26. **Migration per schema conflict?** — without history per schema, modules stamp on each other
27. **ExecuteDelete va soft-delete filter?** — global filter applies unless IgnoreQueryFilters
28. **Reporting 9 DbContexts?** — pragmatic Stimulsoft; coupling cost
29. **uuid[] ContractIds?** — Npgsql primitive collection mapping
30. **How test filters?** — integration test with TenantContext fake + assert SQL/site scope

---

*Day 13 tamum. Ba'd: Day 14 — Repository + Unit of Work. Fehrest: [README.md](./README.md). Related: [Day 15 Soft Delete](./day-15-soft-delete.md), [Day 16 Multi-tenancy](./day-16-multi-tenancy.md).*
