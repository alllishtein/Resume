# Day 04 — SQL + Relational DB (PostgreSQL)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Data-ye system to PostgreSQL-e. Har table rabete dare (FK), har query filter-e tenant va soft-delete dare, index-haye partial unique baraye code melli + soft-delete sakhtim, va transaction-haye Serializable + `FOR UPDATE` baraye write-haye sensitive darim. EF Core baraye CRUD, Dapper baraye SQL-e dasti (inbox).

---

# BAKHSH-E AVAL: WORLD — SQL va DB to donya

## Relational DB chiye?

Data to table-ha ba rabete-ye tarif-shode (FK). Query ba SQL. Constraint enforce mikone ke data valid bemoone.

| model | mesal | ghovvat | za'f |
|---|---|---|---|
| Relational | PostgreSQL, MySQL, SQL Server | consistency, join, constraint, ad-hoc query | schema-change, scale-out sakht |
| Document | MongoDB | flexible schema, nested | join zaif, consistency dast-saz |
| Key-value | Redis | latency-e kam | query nist |
| Object store | MinIO/S3 | blob | search nadare |

Aksar-e system-ha polyglot-an: Postgres baraye source of truth, Redis baraye cache, MinIO baraye file.

**Chera Postgres?** Open-source, `jsonb`, partial index, `FOR UPDATE`, `timestamptz`, Docker-e sade. EF Core + Npgsql.

## Mafahim-e paye

```
PostgreSQL instance
  └── database
        └── schema (namespace)
              └── table
                    └── row (ye record)
                          └── column (ye field)
```

Schema ye namespace-e dakhele DB. Mesle folder. Default `public`. Mitoni `visitors`, `personnels` joda dashte bashi — logical isolation bedune DB-e joda.

## Type-haye mohem

| type | baraye chi |
|---|---|
| `uuid` | PK-e globally unique |
| `text` | string-e bedune limit (Postgres text = varchar performance-e yeki) |
| `varchar(n)` | string ba max length |
| `integer` / `bigint` | adad-e sahih |
| `boolean` | true/false |
| `timestamp with time zone` | tarikh + sa'at + zone. **Hamishe `timestamptz`** |
| `jsonb` | binary JSON. Index-pazir. Document-e koochik dakhele row |

**Rule:** `timestamp` (bedune zone) = dam-e mosahebe. Hamishe `timestamptz`.

**uuid v4 vs v7:** v4 random — index page-split. v7 time-ordered — locality behtar. .NET 9+ `Guid.CreateVersion7()`. Age v4 dari, mosahebe-point.

## Key-ha

**PK** — identity-e row. 1 ta, NOT NULL. Mamulan `uuid` ya `integer IDENTITY`.

**FK** — rabete. `HostId → Personnel.Id`. Integrity ra enforce mikone: child bedune parent nist.

**Unique** — yek value, yek row. Mitone NULL dashte bashe (Postgres chand NULL ejaze mide).

**Composite** — chand column ba ham. `(SiteId, VisitCode)` — yek visit code per site.

## ON DELETE

| behavior | chi mishe |
|---|---|
| Restrict | hazf-e parent **rad** mishe age child bashe |
| SetNull | child.FK = NULL mishe |
| Cascade | child ham **hazf** mishe |

**Rule:** Cascade ra default nakon. Data-ye amniati/tarikhi Cascade nemikhad. Restrict safe-tar-e.

## Normalization (1NF–3NF)

- **1NF:** atomic values. Na list-e CSV to ye column
- **2NF:** hich dependent-e jozi be composite key
- **3NF:** hich transitive dependency. Host name to schedule copy nashe, FK bede

Denormalization-e agahane: snapshot-e companion to jsonb (tarikhi bayad bamoone), copy-e personnel to module-e dige (bounded context; join-e cross-module mamnoo').

## SELECT, WHERE, JOIN

```sql
SELECT v.id, v.first_name, vt.name
FROM visitors v
INNER JOIN visitor_types vt ON vt.id = v.visitor_type_id
WHERE v.is_deleted = false AND v.site_id = @siteId
ORDER BY v.created_at DESC
LIMIT 10 OFFSET 20;
```

**JOIN types:**

- INNER — har do taraf bayad match
- LEFT — chap hamishe, rast momkene NULL
- RIGHT — bar'aks-e LEFT (kam estefade)
- FULL — union-e do taraf
- CROSS — cartesian (mamulan bug)

**EXISTS** baraye semi-join sari-tar-e: "aya in visitor blacklist-e?" → `WHERE EXISTS (SELECT 1 FROM black_lists b WHERE b.national_code = v.national_code)`. Avalin match baste mishe.

**Rule:** `SELECT *` to production nakon. Column-e extra IO va network.

## NULL

`NULL ≠ NULL`. `WHERE col = NULL` hich row nist. Bayad `IS NULL`.

`COALESCE(a, b)` — aval-i ke NULL nist. `NULLIF(col, '')` — '' → NULL.

Unique constraint chand NULL ra to Postgres ejaze mide. Vali `''` empty string yek value-e — do row ba `''` unique ra moshkune.

## Index

Index = sakhtar-e kenari ke lookup ra O(log n) mikone be jaye O(n) seq scan.

**B-tree (default):** equality + range (`=`, `<`, `>`, `BETWEEN`, `LIKE 'abc%'`). `LIKE '%abc'` B-tree **nist**.

**Unique index:** constraint + lookup.

**Partial index (`WHERE ...):** index faghat roye subset. Koochik-tar, unique-e narm-tar. Talayi baraye soft-delete: unique `national_code WHERE is_deleted = false`.

**Composite:** `(site_id, status)` — left-prefix rule: `WHERE site_id = ?` khoob. `WHERE status = ?` bedune site_id **khoob nist**. Selective/equality aval, range dovom.

**GIN:** baraye `jsonb`, full-text, array.

**Covering / index-only:** age SELECT faghat column-haye index ra mikhad, heap nemikhone.

**Cost-e index:** har INSERT/UPDATE index ra update mikone. Index-e ezafe roye write-heavy table (inbox) momkene slow bashe.

## EXPLAIN ANALYZE

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM visitors WHERE national_code = '0012345678' AND is_deleted = false;
```

| node | yani |
|---|---|
| Seq Scan | kole table — bad baraye table-e bozorg |
| Index Scan | khoob |
| Bitmap Heap Scan | chand match az index |
| Nested Loop / Hash Join | noe join |

`cost` estimate-e planner. `actual time` haghighat. `ANALYZE` (command) statistic ra update mikone.

## ACID

| | mani |
|---|---|
| **Atomicity** | hame ya hich |
| **Consistency** | constraint-ha hold |
| **Isolation** | concurrent tx-ha kam ham ra mibinand |
| **Durability** | commit = permanent |

`SaveChanges` = 1 transaction. Outbox interceptor haman transaction: event + entity ya hichkodom.

## Isolation level + MVCC

Postgres MVCC: har row version dare. Reader blocker-e writer nist.

| level | dirty read | non-repeatable | phantom |
|---|---|---|---|
| Read Committed (default) | na | **bale** | **bale** |
| Repeatable Read | na | na | to PG ~ snapshot |
| Serializable | na | na | na |

- **Non-repeatable:** do SELECT-e yek row, beyneshun UPDATE-e kesi-e dige
- **Phantom:** do SELECT-e range, row-e jadid zaher mishe
- **Write skew:** do tx state-e valid mikhanand, ba ham invalid. Serializable abort mikone (`40001`)

Serializable geran-tar-e vali safe-tar. Default Read Committed.

## Lock

**`FOR UPDATE`** — row lock-e exclusive ta commit. Worker-e dovom wait mikone.

**`FOR UPDATE SKIP LOCKED`** — worker-e dovom row-haye lock-nashode ra migire. Baraye parallel consume-e queue.

**Deadlock:** A lock row1 wait row2, B lock row2 wait row1. Postgres yeki ra abort (`40P01`). Retry.

**Advisory lock:** `pg_advisory_lock(id)` — lock-e manteqi, na roye row.

**Lock timeout:** `SET lock_timeout = '2s'` — behtar az wait-e bi-payan.

## Sequence / IDENTITY vs Guid

- **Guid:** globally unique, random (v4 → page split), ya time-ordered (v7)
- **IDENTITY:** sequential, compact, khoob baraye index locality
- **Sequence:** `CREATE SEQUENCE`, `nextval()` — concurrent-safe counter

Hybrid: PK uuid, display code IDENTITY.

## Connection pooling

Connection-ha geran-an. Pool reuse mikone. Default ~100. Npgsql `NpgsqlDataSource` singleton.

Leak: DbContext dispose nashe, transaction baz bemoone. `await using` mohem-e.

Starvation: handler-e slow + pool koochik = request-ha wait.

## SQL injection

```sql
-- BAD
$"WHERE first_name = '{searchTerm}'"
-- searchTerm = "' OR 1=1 --" → hame row
```

**Defa:** parameterized query. EF LINQ automatic. Dapper `new { Id = x }`. Hichvaght concat.

## Pagination: OFFSET vs keyset

OFFSET: `LIMIT 10 OFFSET 10000` — Postgres 10010 row mikhone, 10000 mindaze. Page-e bozorg slow.

Keyset: `WHERE (created_at, id) < (@last_created, @last_id) ORDER BY ... LIMIT 10` — index-friendly, stable.

OFFSET baraye admin grid-e koochik. Keyset baraye infinite scroll ya data-ye bozorg.

## GROUP BY, window, CTE

```sql
-- tedad per site
SELECT site_id, COUNT(*) FROM visits GROUP BY site_id HAVING COUNT(*) > 10;

-- CTE
WITH open AS (SELECT * FROM reservations WHERE status = 'Open')
SELECT host_id, COUNT(*) FROM open GROUP BY host_id;

-- window: akharin visit-e har visitor
SELECT * FROM (
  SELECT v.*, ROW_NUMBER() OVER (PARTITION BY visitor_id ORDER BY created_at DESC) rn
  FROM visits v
) t WHERE rn = 1;
```

`HAVING` ba'd az GROUP (filter roye aggregate). `WHERE` ghabl. Window `COUNT(*) OVER()` total ra bedune query-e dovom mide.

## JSONB

Postgres `jsonb` = binary JSON. Index + containment (`@>`) support.

Khoob baraye: document-e koochik, list-e id, snapshot.
Bad baraye: entity-e mostaghel (FK/constraint nadare).

## VACUUM

MVCC row-e ghadimi ra negah midare. VACUUM pak mikone. Autovacuum default on. Table-e write-heavy (inbox update-e ziad) bayad monitor.

Bloat: index-e random uuid + update ziad → index-e bozorg. `REINDEX CONCURRENTLY`.

## Chizayi ke vojud dare vali kam estefade mishe

- **Materialized view** — pre-computed query, refresh periodic
- **Partitioning** — table-e bozorg ra ba range/list tekke kon (age/date)
- **Logical replication** — CDC, copy-e real-time be system-e dige
- **pg_trgm** — `LIKE '%foo%'` sari ba GIN index
- **Full-text search** — `to_tsvector` + `ts_query`
- **Row-level security** — Postgres-level tenant isolation
- **Foreign data wrapper** — query-e remote DB

---

# BAKHSH-E DOVOM: DEJBAN — SQL to in proje

## Architecture-ye DB

**Microservices = DB-e joda:**

| container | DB |
|---|---|
| `identitydb` | `payamgostar_identity` |
| `dejbandb` | `payamgostar_dejban` |
| `dccdb` | `payamgostar_dcc` |
| `aclserverdb` | `payamgostar_aclserver` |
| `requesttrackerdb` | `payamgostar_requesttracker` |
| `reportingdb` | `payamgostar_reporting` |
| `gateserverdb` | `payamgostar_gateserver` |

Beyn-e microservice-ha: **hich FK / join-e cross-DB**. Integration = MassTransit event.

**Dakhele Dejban = 1 DB, chand schema:**

| schema | module |
|---|---|
| `visitors` | Visitors |
| `personnels` | Personnels |
| `vehicles` | Vehicles |
| `armory` | Armory |
| `inventory` | Inventory |
| `cash_logistics` | CashLogistics |
| `security_patrols` | SecurityPatrols |
| `weigh_bridge` | WeighBridge |

Har module DbContext-e khodesh + `HasDefaultSchema(...)`. Join-e cross-schema **momken** vali **nemikonid** — bounded context. Copy-e read-model az event.

Jomle-ye mosahebe: "Database-per-service across microservices, schema-per-module inside the modular monolith, on a single PostgreSQL instance."

## Naming

```csharp
.UseSnakeCaseNamingConvention()
```

C# `NationalCode` → SQL `national_code`. EF automatic. Dapper dasti.

## Unique-e filtered — pattern-e talayi

```csharp
builder.HasIndex(e => e.NationalCode)
    .HasFilter("\"national_code\" IS NOT NULL AND \"national_code\" != ''")
    .IsUnique(true);
```

Yani:
- Mehman bedune code melli → unique trigger nemikone
- Code melli tekrari beyn-e **zende-ha** mamnoo'
- Soft-delete shode, dobare haman code → OK (BlackList `is_deleted = false` ham dare)

**In pattern ra to mosahebe blackboard kon.** Partial unique + soft delete + NULL handling — kheili miporsan.

## FK-haye Visitors

VisitSchedule:
- `CreatorId` → Personnel (Restrict)
- `HostId` → Personnel (Restrict)
- `VisitReasonId` → VisitReason (Restrict)
- `ReservationId` → VisitReservation (SetNull, optional)

VisitorVisitSchedule:
- unique `(VisitorId, VisitScheduleId)`
- unique `(SiteId, VisitCode)` — shomare per site
- FK Restrict
- `VisitorCardId` SetNull

Restrict default-e domain: hazf-e Host nabayad visit-ha ra besuzone.

## Composite index-ha

```csharp
builder.HasIndex(x => new { x.SiteId, x.Status });
builder.HasIndex(x => new { x.SiteId, x.ScheduledStart });
```

List-e reservation-haye ye site ba status ya calendar. Left-prefix: `WHERE site_id = $1` ham az `(site_id, status)` sood mibare.

## Query filter: tenant + soft delete

```csharp
modelBuilder.ApplyTenantQueryFilters(this);
modelBuilder.ApplySoftDeleteQueryFilters();
```

Automatic `WHERE is_deleted = false AND site_id = ANY($tenant_ids)`.

`IgnoreQueryFilters()` = in WHERE-ha **miran** — khatarnak. Bayad dasti tenant/soft-delete check koni.

Query filter defense in depth-e, na jaye authorization. `X-Site-Id` header ja'l-pazir-e; `TenantIds` bayad az claim ∩ header biad.

## Read path: projection + AsNoTracking

GetVisitors:

```csharp
visitorsQuery
    .AsNoTracking()
    .Select(vit => new {
        vit.Id, vit.FirstName,
        VisitorType = new { vit.VisitorType.Id, vit.VisitorType.Name }
    });
```

`AsNoTracking` — change tracker off. List-e GET hatman. `Select` — faghat column-e lazem, 1 SQL join. **In pattern-e read model-e.**

## Search

```csharp
vit.FirstName.ToLower().Contains(query.SearchTerm.ToLower())
```

SQL: `WHERE LOWER(first_name) LIKE '%term%'`. 

Moshkel: `%term%` B-tree nemizane, `LOWER(column)` expression index mikhad. Table-e koochik OK, 1M row seq scan. To mosahebe in ra **khodet** bego.

Alternative: `pg_trgm` GIN, full-text, ya prefix `term%`.

## Pagination

`PagedList.CreateAsync`:

```csharp
var totalCount = query.Count();    // SYNC!
var items = query.Skip(...).Take(pageSize).ToList();  // SYNC!
```

**Smell:** esm `Async`, raftar sync. `Count()` va `ToList()` thread ra block mikonan. Bayad `CountAsync` + `ToListAsync` + CancellationToken.

OFFSET-e bozorg = slow. Keyset baraye data-ye bozorg.

## JSONB

```csharp
builder.OwnsMany(e => e.Companions, c => c.ToJson());
builder.Property(x => x.EntryDeviceIds).HasColumnType("jsonb");
```

Companions = snapshot-e tarikhi, table-e 3NF nakhastim. Device ids = list-e koochik.

## Inbox SQL (Dapper)

```sql
SELECT id, content, site_ids, is_super_admin
FROM visitors.inbox_messages
WHERE processed_on_utc IS NULL
ORDER BY occurred_on_utc
LIMIT {BatchSize}
FOR UPDATE
```

`FOR UPDATE` = row lock ta commit. Worker-e dovom wait mikone. `SKIP LOCKED` nadarid — multi-instance serialize mishe.

Transaction + Dapper parameterized.

## Card number generator

```csharp
await context.Database.BeginTransactionAsync(IsolationLevel.Serializable);
var last = await sequences.OrderByDescending(x => x.CardNumber).FirstOrDefaultAsync();
next = parse(last) + 1;
// ...
await CommitAsync();
```

Serializable + retry 10 bar ba delay. `CreateExecutionStrategy` baraye transient. Do request-e hamzaman: har do `last = 10000001` → abort + retry.

Smell: `SEQUENCE` sade-tar bood. Table-e sequence + Serializable = bottleneck.

## Advisory lock

`EfParkingOccupancyStore.cs`:

```csharp
await context.Database.ExecuteSqlRawAsync(
    "SELECT pg_advisory_xact_lock({0})", [lockKey], cancellationToken);
```

Lock-e manteqi baraye parking occupancy. Lock ta end of transaction. Parameterized.

## Copy-e table beyn-e module

`visitors.personnels`, `visitors.sites`, `visitors.units` — read model. Event az Personnels → inbox Visitors → upsert.

Na `JOIN personnels.personnels` cross-module. FK-e `HostId` be copy. Eventual consistency: host-e taze copy nashe → FK fail.

## Chi **nadari**

- pg_trgm / full-text search
- Materialized view
- Partitioning
- Row-level security
- uuid v7 (v4 dari — page split)
- SKIP LOCKED to inbox
- Covering index (INCLUDE)
- Expression index baraye LOWER()

## Smell-ha

1. `PagedList.CreateAsync` sync-e (Count/ToList)
2. OFFSET pagination — deep page slow
3. `ToLower().Contains` — seq scan
4. Inbox `FOR UPDATE` bedune `SKIP LOCKED` — multi-instance serialize
5. Card number MAX+1 + Serializable — SEQUENCE behtar
6. `LIMIT {BatchSize}` string interpolation — int-e vali pattern-e khatar
7. Visitor partial unique bedune `is_deleted`, BlackList ba `is_deleted` — inconsistency
8. Index roye `is_deleted` boolean — kam-selective
9. `IgnoreQueryFilters` — tenant leak risk
10. uuid v4 PK — page split
11. `text` bedune max baraye first_name — 10MB theoretically
12. Copy table + FK — eventual consistency race

## 25 soal-e mosahabe

1. PK vs unique? — PK = 1, NOT NULL, identity. Unique mitone chand ta
2. FK chi ra zemanat mikone? — referential integrity
3. Restrict vs Cascade? — Restrict rad, Cascade hazf
4. INNER vs LEFT? — INNER match, LEFT chap hamishe
5. `WHERE col = NULL` chera khali? — three-valued; `IS NULL`
6. Partial unique chie? — unique roye subset (soft delete)
7. Index chie? — B-tree lookup, cost roye write
8. `%term%` chera index nemizane? — leading wildcard; trgm
9. Composite left-prefix? — `(a,b)` baraye `a` va `a,b`; na `b`
10. EXPLAIN Seq Scan? — bad baraye table-e bozorg + selective WHERE
11. ACID? — Atomic, Consistent, Isolated, Durable
12. Read Committed vs Serializable? — RC phantom; Serializable abort
13. MVCC? — version row; reader blocker-e writer nist
14. Deadlock? — cycle lock; DB abort; retry
15. FOR UPDATE? — row lock ta commit
16. SKIP LOCKED? — parallel worker row-e azad
17. N+1? — 1+N query; Include ya projection
18. OFFSET moshkelesh? — geran baraye deep page; keyset
19. SQL injection? — concat; parameterized
20. Schema vs database? — schema namespace; DB isolation
21. jsonb? — document-e koochik; FK nadare
22. timestamptz? — hamishe; zone-aware
23. Query filter? — global WHERE; IgnoreQueryFilters khatar
24. 23505 unique_violation? — race; map be 409
25. DB-per-service vs schema-per-module? — har do darim

## Whiteboard SQL — 5 tamrin

**1.** Visitor-haye zende-ye ye site, page 2, search family:

```sql
SELECT id, first_name, last_name FROM visitors.visitors
WHERE is_deleted = false AND site_id = @siteId
  AND last_name ILIKE '%' || @q || '%'
ORDER BY created_at DESC LIMIT 10 OFFSET 10;
```

**2.** Visitor-ha-i ke to blacklist-an:

```sql
SELECT v.id FROM visitors.visitors v
WHERE v.is_deleted = false
  AND EXISTS (SELECT 1 FROM visitors.black_lists b
    WHERE b.is_deleted = false AND b.national_code = v.national_code);
```

**3.** Tedad reservation Open per host, > 5:

```sql
SELECT host_id, COUNT(*) FROM visitors.visit_reservations
WHERE status = 'Open' GROUP BY host_id HAVING COUNT(*) > 5;
```

**4.** Akharin visit-e har visitor:

```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY visitor_id ORDER BY id DESC) rn
  FROM visitors.visitor_visit_schedules
) t WHERE rn = 1;
```

**5.** Inbox poll baraye 2 worker:

```sql
SELECT id, content FROM visitors.inbox_messages
WHERE processed_on_utc IS NULL
ORDER BY occurred_on_utc LIMIT 20 FOR UPDATE SKIP LOCKED;
```

## Resume

**short:**

> Modeled a multi-schema PostgreSQL design for a modular monolith (schema-per-module, database-per-microservice), with partial unique indexes, tenant/soft-delete query filters, and transactional inbox processing (FOR UPDATE).

**bullets:**

- Designed filtered unique indexes: national/passport codes unique among live rows, allowing NULL/empty and soft-deleted reuse
- Used Serializable + retry for card-number generation, Dapper FOR UPDATE for inbox batches
- Read path: AsNoTracking projections, composite indexes on (site_id, status|date), OFFSET pagination

**skills:** `PostgreSQL, SQL, Indexing, Transactions, Isolation levels, MVCC, Npgsql, Dapper, EF Core`

## File-haye mohem

| chi | koja |
|---|---|
| DbContext + schema | `...Visitors.Infrastructure/Database/VisitorsDbContext.cs` |
| Unique/FK visitor | `.../Visitors/VisitorConfiguration.cs` |
| Tenant filter | `Common/Tenancy/TenantQueryFilterExtensions.cs` |
| Soft delete filter | `Common/Tenancy/SoftDeleteQueryFilterExtensions.cs` |
| Inbox SQL | `.../Inbox/ProcessInboxJob.cs` |
| Card generator | `.../Visitors/VisitorCardNumberGenerator.cs` |
| Pagination | `Common/Abstractions/Queries/PagedList.cs` |
| List query | `.../GetVisitors/GetVisitorsQueryHandler.cs` |
| Docker DBs | `docker-compose.yml` |

---

Day 04 tamum. Ba'd: Day 05 — ASP.NET Core pipeline / DI. Fehrest: [README.md](./README.md).
