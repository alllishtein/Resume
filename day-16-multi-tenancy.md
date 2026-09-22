# Day 16 — Multi-tenancy (`X-Site-Id`)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Multi-tenancy** yani yek software, chand mostajar — data-ha bayad joda bashan. To Dejban tenant = **Site** (markaz / padegan / project). User to JWT claim-e `site` dare (list-e site-hayi ke ejaze dare). UI site-e selected ra to Zustand + localStorage negah midare va har API call header **`X-Site-Id`** mifreste.

Middleware az JWT + header → `TenantContext` (AsyncLocal) misaze. Har `DbContext` ke `ITenantDbContext` hast, EF **named global query filter** `TenantFilter` mizare: `SiteId IN TenantIds` — magar SuperAdmin bedune site select → hame. Hamin context to **MassTransit headers** va **Outbox/Inbox** ham propagate mishe ta background job-ha ham filter ra dorost dashte bashan. Soft-delete (Day 15) + tenant = **do filter-e joda**; `IgnoreQueryFilters()` bedune re-check = **tenant leak**.

---

# BAKHSH-E AVAL: WORLD — Multi-tenancy to donya

## Multi-tenancy chie?

Yek software, **chand mostajar (tenant)** — data-ha bayad joda bashan. Tenant ≠ User. Tenant = **boundary-e data**. User mitone be chand tenant access dashte bashe (multi-site user).

Mesal-ha:

- SaaS: har company = tenant
- Hospital chain: har hospital = tenant
- **Dejban:** har **Site** (markaz / padegan / contractor site) = tenant scope

---

## Se model-e classic izolasyon

| model | chejori | maziat | moshkel |
|---|---|---|---|
| **DB-per-tenant** | har tenant DB joda | izolasyon ghavi, backup asan | cost, migration × N |
| **Schema-per-tenant** | yek DB, schema joda | mid-izolasyon | Postgres schema limit / ops |
| **Shared DB + discriminator** | yek table, column `TenantId` / `SiteId` | simple ops, cheap | **bug = data leak**; har query bayad filter |

**Dejban:** shared PostgreSQL + **SiteId column** + EF global filter. (Schema-per-**module** dare — Day 13 — vali na schema-per-tenant.)

Modular monolith Dejban = 8 schema (Personnels, Visitors, …) dar **yek** DB. Tenant = `SiteId` roye entity-ha, na schema joda per site.

---

## Chera multi-tenancy sakht-e?

In domain jaye «yek bug = leak amniati»-e:

1. **Yek faramoshi** (`WHERE site_id = …`) = leak be tenant digar — amniati / hoghughi.
2. **Background jobs** HttpContext nadaran — context bayad **serialize** she.
3. **SuperAdmin** gahi hame site, gahi yek site — logic dual.
4. **Cross-tenant report** — intentional override ba auth ghavi.
5. **Messaging** — consumer bayad haman tenant scope-e publisher ra dashte bashe.
6. **Cache keys** — Redis key bedune siteId = cross-tenant pollution.
7. **Unique indexes** — often per-tenant (`(SiteId, AccessCode)` unique).

Interview: «chejori guarantee mikoni developer faramosh nakone?» → **global query filter** + tests + code review + (ideally) integration tests ba 2 tenant.

---

## Approaches baraye enforce

### 1) Application-level (dasti)

```csharp
await db.Orders.Where(o => o.TenantId == currentTenant).ToListAsync();
```

Har query. Faramosh = leak. **Anti-pattern** baraye large codebase.

### 2) Repository always injects tenant

```csharp
public IQueryable<Order> GetQueryable()
    => db.Orders.Where(o => o.TenantId == _tenant.Id);
```

Behtar, vali `IgnoreQueryFilters` / raw SQL / Dapper still leak.

### 3) EF Global Query Filter ← **Dejban**

```csharp
modelBuilder.Entity<Order>()
    .HasQueryFilter(o => tenantIds.Contains(o.SiteId));
```

Automatic. Developer normal LINQ minevise; SQL `AND site_id = ANY(...)` midahad.

### 4) Row-Level Security (Postgres RLS)

DB-level policy. Ghavi-tar. Dejban **estefade nemikone** (EF filter kafi + ops simpler). RLS = topic-e mosahebe advanced.

### 5) Separate DB / connection string per tenant

Enterprise SaaS. Dejban nist.

---

## Tenant resolution — az koja miad?

| source | mesal |
|---|---|
| **Subdomain** | `acme.app.com` → tenant Acme |
| **Path** | `/t/acme/orders` |
| **Header** | `X-Tenant-Id` / **`X-Site-Id`** ← Dejban |
| **JWT claim** | `tenant_id` / `site` claims ← Dejban (authorization of which sites allowed) |
| **API key** | mapped to tenant |

**Dejban hybrid:**

- JWT `site` claims = **allowed** sites (identity)
- Header `X-Site-Id` = **selected** working site(s) (UI choice)
- Effective = intersection (ya SuperAdmin override)

---

## SuperAdmin / God mode

Har multi-tenant system ye «didan-e hame» mikhad. Pattern-haye common:

```
IF SuperAdmin AND no site selected → no SiteId filter (see all)
IF SuperAdmin AND site selected → filter to that site
IF normal user → filter to (allowed ∩ selected); never outside allowed
```

In exact-e Dejban-e (`BuildScopedTenantPredicate`).

**Khatar:** SuperAdmin + empty header = query bozorg / slow. UI bayad site force kone baraye normal ops (FE often forces one site).

---

## Multi-site user

User mitone be Site A va B access dashte bashe:

```
JWT sites: [A, B]
Header X-Site-Id: A
→ Effective: [A]

Header empty (non-super):
→ Effective: [A, B]  // hameye allowed
```

Ya UI faghat yek select mikone (Dejban FE currently **slice(0,1)** — backend multi support dare).

---

## Tenant + Soft delete (do filter)

Do filter **jodagan** AND mishan:

```sql
SELECT * FROM personnels
WHERE is_deleted = false          -- SoftDeleteFilter
  AND site_id = ANY(@tenantIds)   -- TenantFilter
```

`IgnoreQueryFilters()` → **hardoon do** miran. Bayad dasti:

```csharp
.IgnoreQueryFilters()
.Where(p => !p.IsDeleted)
.Where(p => allowedSites.Contains(p.SiteId))
```

Ya named ignore (EF Core):

```csharp
.IgnoreQueryFilters([GlobalQueryFilterNames.TenantFilter])
// SoftDeleteFilter still active
```

ACL DeviceSyncRepository in pattern ra dare — **faghat TenantFilter** ignore, soft-delete mimone. In advanced va important-e.

---

## Tenant propagation beyond HTTP

HTTP request AsyncLocal set mikone. Vali path-haye digar HttpContext nadaran:

| path | problem | solution |
|---|---|---|
| MediatR in same request | OK — same AsyncLocal | — |
| MassTransit publish | consumer thread digar | headers `X-Tenant-SiteIds` / `X-IsSuperAdmin` |
| Outbox job (Quartz) | no HTTP | persist SiteIds on OutboxMessage row |
| Inbox job | no HTTP | persist + restore before handler |
| `Task.Run` / fire-forget | AsyncLocal may not flow | avoid; or pass explicitly |
| Hangfire | separate worker | serialize tenant in job args |

**Gold rule:** harja DbContext query mizani, `ITenantContext` bayad filled bashe.

---

## Authorization vs Tenancy

| | Tenancy filter | Authorization |
|---|---|---|
| soal | «kodom **data** mibinam?» | «in **action** ejaze dare?» |
| enforce | EF query filter | policies / permissions / roles |
| fail | empty result / not found | 403 Forbidden |

Mituni data-ye site ra bebini vali `DeletePersonnel` permission nadashte bashi — va baraks (rare).

Dejban: `SiteAccessAuthorizationHandler` check mikone header sites ⊆ user sites. Separate az EF filter.

---

## Anti-patterns

In-ha ra to review / mosahebe zud flag kon:

1. **Trust client SiteId blindly** bedune intersect ba JWT — spoof
2. **Cache without site in key** — `personnel:123` vs `personnel:{site}:123`
3. **Global static TenantId** — thread-unsafe / test hell
4. **Filter only in UI** — API must enforce
5. **`IgnoreQueryFilters()` in hot path** without re-filter
6. **Logging PII across tenants** in shared log without site tag
7. **FK across tenants** accidentally (Site A personnel on Site B unit)
8. **Seed/migration using production DbContext** without design-time empty tenant

---

## Testing multi-tenancy

```csharp
// Arrange: two sites, two personnels
TenantContextAccessor.SetContext([siteA], isSuperAdmin: false);
var listA = await handler.Handle(new GetPersonnelsQuery(), ct);
// Assert all SiteId == siteA

TenantContextAccessor.SetContext([siteB], false);
var listB = await ...
// Assert no overlap with listA
```

Integration test ba Testcontainers + 2 tenants = resume gold.

---

## Chizaei ke to donya hastan vali Dejban kam/nist

- PostgreSQL **RLS**
- DB-per-tenant
- Subdomain tenant resolution
- Auto `HasQueryFilter` via interceptor on SaveChanges validating SiteId on insert
- Full multi-select site UI (FE currently single)
- Tenant-aware HybridCache key convention documented everywhere
- Automatic deny when header site ∉ JWT (partially via SiteAccess handler — depends on policy registration)

---

# BAKHSH-E DOVOM: DEJBAN — Multi-tenancy to in proje

Pipeline-e Dejban injuri-e: FE site select → axios `X-Site-Id` → YARP → middleware `TenantContext` → EF `TenantFilter`. Outbox/Inbox ham SiteIds ra persist mikonan ta Quartz job-ha filter ra gom nakonan. Diagram-e zir ra **blackboard** kon — mosahebe.

## Big picture — request lifecycle

```
[FE] User picks Site in dashboard layout
      → useSiteStore.setSiteIds([siteId])
      → localStorage selectedSiteId

[FE] axios interceptor
      → headers['X-Site-Id'] = siteIds.join(',')
      → Authorization: Bearer …

[YARP] gateway forward (headers preserved)

[API] UseAuthentication → JWT valid
[API] UseTenantContext() middleware
      → userSiteIds from claim "site"
      → headerSiteIds from X-Site-Id
      → isSuperAdmin from role claim "{siteId}|{roleName}"
      → effectiveSiteIds = rules below
      → TenantContextAccessor.SetContext(effective, isSuperAdmin)

[DI] TenantContext : ITenantContext reads Accessor
[DI] PersonnelsDbContext(tenantContext) : ITenantDbContext
      TenantIds => tenantContext.SiteIds

[EF] every query on ISiteEntity
      → HasQueryFilter TenantFilter
      → SQL: site_id = ANY(...) OR (superadmin AND count=0)

[Handler] normal LINQ — tenant automatic

[SaveChanges] InsertOutboxMessagesInterceptor
      → OutboxMessage.SiteIds / IsSuperAdmin snapshot

[finally middleware] TenantContextAccessor.Clear()
```

---

## Marker interfaces

```csharp
// Common/Tenancy/ISiteEntity.cs — entity belongs to ONE site
public interface ISiteEntity
{
    Guid SiteId { get; }
}

// Common/Tenancy/ISite.cs — the site aggregate itself
public interface ISite
{
    Guid Id { get; }
}

// Common/Tenancy/ISiteEntities.cs — entity linked to MANY sites
public interface ISiteEntities<TSite> where TSite : ISite
{
    ICollection<TSite> Sites { get; }
}
```

**Mesal:**
- `Personnel : ISiteEntity, ISoftDeletable` → filter on `Personnel.SiteId`
- Entity ba `ICollection<Site> Sites` → filter `Sites.Any(s => TenantIds.Contains(s.Id))`
- Related entity bedune SiteId vali navigation be ISiteEntity → filter via navigation.`SiteId`

```csharp
// Domain shorthand per module:
public interface ISiteEntities : global::Common.Tenancy.ISiteEntities<Site>;
```

---

## ITenantContext + AsyncLocal

```csharp
// ITenantContext.cs
public interface ITenantContext
{
    HashSet<Guid> SiteIds { get; }
    bool IsSuperAdmin { get; }
}

// TenantContext.cs — DI-friendly wrapper
public sealed class TenantContext : ITenantContext
{
    public HashSet<Guid> SiteIds => TenantContextAccessor.Current?.SiteIds ?? [];
    public bool IsSuperAdmin => TenantContextAccessor.Current?.IsSuperAdmin ?? false;
}

// TenantContextAccessor.cs — ambient context
public static class TenantContextAccessor
{
    private static readonly AsyncLocal<TenantInfo?> _current = new();

    public static void SetContext(HashSet<Guid> siteIds, bool isSuperAdmin)
        => _current.Value = new TenantInfo(siteIds, isSuperAdmin);

    public static void Clear() => _current.Value = null;
}
```

**Chera AsyncLocal?**
- Per-async-flow storage (request-safe)
- Middleware set → DbContext / handlers / filters mikhanand bedune HttpContext pass
- Jobs/consumers ham `SetContext` mikonan

**Smell:** static ambient — testing bayad Clear koni; forget Clear = leak be request ba'di (middleware finally Clear dare).

DI registration (typical):

```csharp
services.AddScoped<ITenantContext, TenantContext>();
```

DbContext scoped → same request → same TenantIds snapshot via property getters (evaluated at **query compile/execution** time against dbContext instance fields — expression captures `dbContext` constant).

---

## Header parsing — `X-Site-Id`

```csharp
// Common/Abstractionsis/Extensions/HttpContextAccessorExtensions.cs
private const string SiteIdHeaderName = "X-Site-Id";

public static HashSet<Guid> GetHeaderSiteIds(this HttpContext httpContext)
{
    var siteIdHeader = httpContext.Request.Headers[SiteIdHeaderName];
    var siteIds = new HashSet<Guid>();

    foreach (var header in siteIdHeader)
    {
        if (string.IsNullOrWhiteSpace(header)) continue;
        foreach (var idStr in header.Split(",", ...))
            if (Guid.TryParse(idStr, out var siteId))
                siteIds.Add(siteId);
    }
    return siteIds;
}
```

Supports **comma-separated multi-site** header. FE currently often sends **one**.

DCC / Reporting / FileService ham `X-Site-Id` forward mikonan (service-to-service).

---

## JWT site claims

```csharp
// CustomClaims.Site = "site"
public static HashSet<Guid> GetUserSiteIds(this ClaimsPrincipal? principal)
{
    var siteClaims = principal?.FindAll(CustomClaims.Site) ?? [];
    return [.. siteClaims
        .Select(c => Guid.TryParse(c.Value, out var id) ? id : (Guid?)null)
        .Where(id => id.HasValue)
        .Select(id => id!.Value)];
}
```

`CustomClaimsTransformation` (Identity) site claim-ha ra enrich mikone az claim service.

Role format for super-admin detection:

```
claim type: role
claim value: "{siteGuid}|{RoleName}"
```

Middleware:

```csharp
var userSiteRoles = user.Claims
    .Where(c => c.Type == CustomClaims.Role)
    .Select(c => c.Value.Split('|', 2))
    .Where(parts => parts.Length == 2 && Guid.TryParse(parts[0], out _))
    .Select(parts => parts[1])
    .ToHashSet();

bool isSuperAdmin = userSiteRoles.Any(x =>
    x.Equals(_superAdminRoleName, StringComparison.OrdinalIgnoreCase));
```

Role name az config: `SuperAdminSettings:AdminRoleName` (default constant).

---

## TenantContextMiddleware — maghz-e effective sites

```csharp
// Common/Tenancy/TenantContextMiddleware.cs
public async Task InvokeAsync(HttpContext context)
{
    try
    {
        var user = context.User;
        if (user.Identity?.IsAuthenticated == true)
        {
            var userSiteIds = user.GetUserSiteIds();
            var headerSiteIds = context.GetHeaderSiteIds();
            // ... isSuperAdmin as above ...

            HashSet<Guid> effectiveSiteIds;
            if (headerSiteIds.Count == 0)
            {
                // no header → all sites user is allowed to see
                effectiveSiteIds = userSiteIds;
            }
            else if (isSuperAdmin)
            {
                // SuperAdmin may target ANY site via header (even outside JWT sites)
                effectiveSiteIds = headerSiteIds;
            }
            else
            {
                // Normal user: cannot escalate beyond JWT sites
                effectiveSiteIds = [.. userSiteIds.Intersect(headerSiteIds)];
            }

            TenantContextAccessor.SetContext(effectiveSiteIds, isSuperAdmin);
        }

        await _next(context);
    }
    finally
    {
        TenantContextAccessor.Clear();
    }
}
```

### Jadval-e truth (yaad begir)

| Auth | Header | SuperAdmin | Effective TenantIds | Filter behavior |
|---|---|---|---|---|
| yes | empty | no | userSiteIds | SiteId ∈ user sites |
| yes | empty | **yes** | userSiteIds (often all) | if Count>0 → filter; wait — SuperAdmin empty header uses userSiteIds; **unscoped all** only when TenantIds.Count==0 AND IsSuperAdmin |
| yes | [A] | no | user ∩ [A] | only A if allowed |
| yes | [A] | yes | [A] | scoped to A even for super |
| yes | [Evil] | no | ∅ (intersect empty) | **no rows** (safe fail) |
| yes | [Evil] | yes | [Evil] | Super can open any site id |
| no | * | — | context not set | TenantIds=[] IsSuperAdmin=false → filter match fails for site entities |

**Mohem — SuperAdmin «see all»:**

```csharp
// BuildScopedTenantPredicate:
// (IsSuperAdmin && TenantIds.Count == 0) || siteMatch
```

Pas SuperAdmin + **empty** TenantIds → unscoped. Vali middleware vaghti header empty-e, `effectiveSiteIds = userSiteIds` — age SuperAdmin JWT all sites dare, Count > 0 → **filter be hameye user sites**, na «literally unfiltered».

Age SuperAdmin JWT site claim **khali** bashe + header empty → Count=0 + IsSuperAdmin → **true unscoped see-all**.

In nuance ra mosahebe bemal.

Pipeline registration:

```csharp
app.UseTenantContext(); // after Authentication
```

Dejban.Api, Reporting, DCC, … .

---

## SiteAccessAuthorizationHandler

Layer-e digar (policy):

```csharp
var headerSiteIds = httpContextAccessor.GetHeaderSiteIds();
if (headerSiteIds.Count <= 0) return; // no succeed yet

var userSiteIds = context.User.GetUserSiteIds();
if (!headerSiteIds.All(userSiteIds.Contains)) return; // deny

context.Succeed(requirement);
```

**Note:** SuperAdmin spoof path — in handler SuperAdmin exception **nadare**. Age policy hard require SiteAccess, SuperAdmin header outside JWT fail mishe. Depend on which endpoints use the policy. EF layer SuperAdmin header override dare; auth handler maybe stricter — **smell / know your policies**.

---

## EF TenantFilter — expression trees

```csharp
// TenantQueryFilterExtensions.ApplySingleSiteFilter
// Conceptual filter:
e => (db.IsSuperAdmin && db.TenantIds.Count == 0)
     || db.TenantIds.Contains(e.SiteId)
```

Named:

```csharp
modelBuilder.Entity<TEntity>()
    .HasQueryFilter(GlobalQueryFilterNames.TenantFilter, lambda);
```

### Three apply strategies

1. **`ISiteEntity`** → `Contains(e.SiteId)`
2. **`ISiteEntities<TSite>`** → `e.Sites.Any(s => TenantIds.Contains(s.Id))`
3. **Related navigation** to ISiteEntity (reference, not collection) → `Contains(e.Nav.SiteId)`

Loop reflection + MakeGenericMethod — mesl SoftDelete extensions.

### DbContext wiring

```csharp
public sealed class PersonnelsDbContext(
    DbContextOptions<PersonnelsDbContext> options,
    ITenantContext tenantContext)
    : DbContext(options), IUnitOfWork, ITenantDbContext
{
    public HashSet<Guid> TenantIds => tenantContext.SiteIds;
    public bool IsSuperAdmin => tenantContext.IsSuperAdmin;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // ... configurations ...
        modelBuilder.ApplyTenantQueryFilters(this);
        modelBuilder.ApplySoftDeleteQueryFilters();
    }
}
```

**Order:** tenant + soft-delete both applied. Named keys joda → selective ignore possible.

**Inventory smell (Day 15/13):** InventoryDbContext tenant/soft filters incomplete — data izolasyon weaker in that module.

**Site entity smell:** `Site : ISite, ISoftDeletable` — **not** `ISiteEntity`. `context.Sites` may **not** auto-filter by TenantIds. List sites often relies on app query / claims. Related entities filtered; root Site table careful bash.

---

## Frontend — site selection + axios

```javascript
// packages/ui/src/auth/utils/site-storage.js
const useSiteStore = create((set, get) => ({
  selectedSiteIds: readStoredSiteIds(),
  setSiteIds: (siteIds) => {
    const ids = normalizeSiteIds(siteIds); // currently slice(0, 1) — SINGLE
    localStorage.setItem(SITE_KEY, ids[0]);
    set({ selectedSiteIds: ids });
  },
  getSiteIds: () => get().selectedSiteIds.length
    ? get().selectedSiteIds
    : readStoredSiteIds(),
}));
```

```typescript
// packages/api-client/src/axiosInstance.ts
const siteIds = getSelectedSiteIds();
if (siteIds.length > 0) {
  config.headers['X-Site-Id'] = siteIds.join(',');
}
```

Dashboard layout site picker → `setSiteIds`. Guards wait `siteReady` (selectedSiteIds.length > 0 ya no site claims).

**FE vs BE:**
- BE: multi GUID comma OK
- FE store: **force one** site (`slice(0, 1)`)
- Comment to axios mige «chand markaz» — code single. Smell / future multi.

Reporting `report.http.js` ham site header midahad.

---

## MassTransit propagation

```csharp
// Publish / Send filter
context.Headers.Set("X-Tenant-SiteIds", string.Join(",", siteIds));
context.Headers.Set("X-IsSuperAdmin", isSuperAdmin);

// Consume filter
TenantContextAccessor.SetContext(parsedSiteIds, isSuperAdmin);
try { await next.Send(context); }
finally { TenantContextAccessor.Clear(); }
```

```csharp
cfg.UseTenantContextFilters(context);
// → UseConsumeFilter + UsePublishFilter + UseSendFilter
```

Consumer DbContext queries → haman tenant scope-e publisher HTTP request.

---

## Outbox / Inbox persistence (critical)

HTTP AsyncLocal after request **miravad**. Domain event outbox row bayad tenant ra **save** konad:

```csharp
// InsertOutboxMessagesInterceptor
SiteIds = [.. tenantInfo?.SiteIds ?? []],
IsSuperAdmin = tenantInfo?.IsSuperAdmin ?? false,
```

```csharp
// ProcessOutboxJob / ProcessInboxJob before handlers:
TenantContextAccessor.SetContext([.. message.SiteIds], message.IsSuperAdmin);
```

Bedune in: job ba TenantIds=[] → SuperAdmin false → **zero rows** ya wrong scope → silent bugs / missed cascade soft-delete.

IntegrationEventConsumer sometimes reads `TenantContextAccessor.Current` to copy into inbox row when receiving from bus.

**In connection Day 19–23** — tenancy × messaging = advanced Dejban.

---

## Write path — SiteId on create

Filter faghat **read** ra constrain mikone. On insert:

```csharp
var personnel = Personnel.Create(..., siteId: request.SiteId, ...);
```

Bayad validate:
1. `request.SiteId` ∈ TenantContext.SiteIds (ya SuperAdmin)
2. Unit belongs to same Site
3. FE lockedSiteId often forces form site = selected site

Age na check: user mitone SiteId digar dar body beftriste — **IDOR / tenant write leak**. Filter on next read hide mikone vali **row wrong site** to DB hast.

Interview: «query filter write-ha ra protect nemikone — validation lazeme.»

---

## Unique indexes per site

Az Day 04/15:

```csharp
builder.HasIndex(e => new { e.SiteId, e.AccessCode })
    .IsUnique()
    .HasFilter("\"access_code\" IS NOT NULL AND \"is_deleted\" = false");
```

Access code unique **per site**, na global. Multi-tenant modeling classic.

---

## IgnoreQueryFilters — named vs all

```csharp
// ALL filters gone (soft + tenant) — dangerous
.IgnoreQueryFilters()

// EF Core named — only tenant (ACL pattern)
.IgnoreQueryFilters([GlobalQueryFilterNames.TenantFilter])
```

Device sync / plate reader / cross-site device ops often need devices across sites with service identity — named ignore + careful auth.

RequestTracker public tickets: IgnoreQueryFilters + **manual** `!site.IsDeleted` — pattern from Day 15.

---

## Service-to-service

```csharp
// DccHttpClient — forward tenant
request.Headers.TryAddWithoutValidation(
    "X-Site-Id", string.Join(",", ids));
```

File upload/download to DCC same site scope. Reporting Controllers read `X-Site-Id` for Stimulsoft datasets.

---

## Design-time / migrations

```csharp
internal sealed class DesignTimeTenantContext : ITenantContext
{
    public HashSet<Guid> SiteIds => [];
    public bool IsSuperAdmin => true; // or false — team choice
}
```

Factory for `dotnet ef` — DbContext ctor needs ITenantContext.

---

## Connection to other days

| day | rabt |
|---|---|
| 05 Pipeline | middleware order: Auth → TenantContext |
| 06 JWT | `site` / `role` claims |
| 07 YARP | header forward |
| 13 EF | named HasQueryFilter |
| 15 Soft delete | second filter; Ignore risk |
| 19–23 Outbox/Inbox/MT | tenant snapshot + restore |
| 25 HybridCache | key must include site |
| 40 Auth E2E | site picker + guards |
| 49 Auth UI | componentId + siteReady |

---

## Smell-ha (kamel)

1. **Site root not ISiteEntity** — Sites query may be unscoped by TenantFilter
2. **Inventory** missing ApplyTenantQueryFilters
3. **Write validation** SiteId not always centralized (handler-dependent)
4. **SiteAccessHandler** vs SuperAdmin EF rules inconsistent
5. **FE single-site** vs BE multi-site header support
6. **SuperAdmin see-all** depends on empty TenantIds — middleware fills userSiteIds when header empty → may never hit Count==0 path
7. **Ambient AsyncLocal** — easy to forget in new background path
8. **Cache keys** without site — check Redis usage per feature
9. **Dapper/raw SQL** bypasses EF filters entirely — must add `site_id` manually (outbox SQL OK; reports careful)
10. **Logging** SiteIds not always in scope enricher
11. **Public endpoints** (RequestTracker) special-case IgnoreQueryFilters
12. **Intersect empty** → empty results look like «no data» not «forbidden» — UX confusion (404 vs 403)
13. **Header spoof** for non-super stopped by intersect; SuperAdmin can open arbitrary GUID — ensure site exists checks
14. **Multiple modules copy Site/Unit/Personnel** — each schema filtered independently; event must carry enough ids
15. **Tests** often skip tenant setup → false greens

---

## Debug checklist (vaghti «data nemiad»)

1. Browser Network: `X-Site-Id` set-e?
2. JWT decode: `site` claims include that id?
3. SuperAdmin or not?
4. `TenantContextAccessor.Current` at breakpoint?
5. SQL log: `site_id = ANY(...)` present?
6. Soft-deleted?
7. Wrong module schema / read-model not synced?
8. Job path: OutboxMessage.SiteIds empty?

---

## 25 soal-e mosahebe

1. Multi-tenancy chie?
2. Shared DB + discriminator vs DB-per-tenant?
3. Chera global query filter?
4. `X-Site-Id` vs JWT `site` claim — fargh?
5. Effective siteIds chejori hesab mishe?
6. SuperAdmin + empty header?
7. SuperAdmin + selected header?
8. Normal user + header outside JWT?
9. AsyncLocal chie? Chera?
10. Chera middleware finally Clear?
11. Write path chejori secure mishe?
12. IgnoreQueryFilters risk?
13. Named IgnoreQueryFilters?
14. Tenant + soft-delete do filter?
15. Outbox cherā SiteIds save mikone?
16. MassTransit headers?
17. ISiteEntity vs ISiteEntities?
18. Related-entity tenant filter?
19. Postgres RLS miduni?
20. Cache key design?
21. IDOR ba SiteId to body?
22. Empty result vs 403?
23. FE single vs BE multi?
24. Dapper bypass?
25. Chejori test mikoni isolation?

---

## Senario-haye whiteboard (practice)

### A) Leak attempt

```
User JWT sites: [A]
X-Site-Id: B
→ Intersect = [] → queries return empty
→ Cannot read B
```

### B) SuperAdmin audit

```
SuperAdmin, X-Site-Id: B
→ Effective [B], filter scoped to B
→ Works even if B not in personal day-to-day sites
```

### C) Cascade soft-delete across modules

```
HTTP Site A → SoftDelete Site
→ Outbox SiteIds=[A]
→ Job restores TenantContext [A]
→ Handlers load local Site/Personnel with filters OK
```

### D) Forget restore context in new Hangfire job

```
TenantIds=[] IsSuperAdmin=false
→ Contains never true
→ SoftDeleteBySiteId updates 0 rows
→ Bug silent
```

---

## Resume

**short:**

> Designed shared-database site multi-tenancy for a modular monolith: JWT site claims plus `X-Site-Id` header resolved in middleware into an AsyncLocal `TenantContext`, enforced by named EF Core global query filters, and propagated through MassTransit headers and transactional outbox/inbox so background processors keep the same tenant scope.

**bullets:**

- Resolved effective tenant as JWT∩header for users and header-priority for SuperAdmin, with scoped-vs-unscoped predicate `(IsSuperAdmin && no sites) || SiteId ∈ TenantIds`
- Applied reflection-based `ApplyTenantQueryFilters` for `ISiteEntity`, multi-site `ISiteEntities<>`, and related navigations
- Snapshotted `SiteIds`/`IsSuperAdmin` on outbox messages and restored them in Quartz inbox/outbox jobs
- Wired FE Zustand site store → axios `X-Site-Id` on every API call; documented FE single-select vs BE multi-header capability

**skills:** `Multi-tenancy, EF Core Global Query Filters, ASP.NET Core Middleware, AsyncLocal, JWT Claims, MassTransit Filters, Outbox Pattern, Axios Interceptors, Zustand, Security Isolation`

---

## File-haye mohem

| chi | koja |
|---|---|
| ITenantContext / TenantContext | `Common/Tenancy/` |
| TenantContextAccessor + TenantInfo | `Common/Tenancy/TenantContextAccessor.cs` |
| Middleware | `Common/Tenancy/TenantContextMiddleware.cs` |
| UseTenantContext | `TenantContextMiddlewareExtensions.cs` |
| Query filters | `Common/Tenancy/TenantQueryFilterExtensions.cs` |
| Filter names | `GlobalQueryFilterNames.cs` |
| ISiteEntity / ISite / ISiteEntities | `Common/Tenancy/` |
| Header helpers | `Common/Abstractions/Extensions/HttpContextAccessorExtensions.cs` |
| GetUserSiteIds | `Common/Authentication/ClaimPrincipalExtensions.cs` |
| CustomClaims.Site | `Common/Authentication/CustomClaims.cs` |
| SiteAccess handler | `Common/Authorization/SiteAccessAuthorizationHandler.cs` |
| PersonnelsDbContext | `Personnels.Infrastructure/Database/PersonnelsDbContext.cs` |
| MT filters | `TenantContextPublishFilter` / `ConsumeFilter` / `MassTransitExtensions` |
| Outbox snapshot | `InsertOutboxMessagesInterceptor.cs` + `OutboxMessage.cs` |
| Job restore | `*/Inbox/ProcessInboxJob.cs`, `*/Outbox/ProcessOutboxJob.cs` |
| FE store | `packages/ui/src/auth/utils/site-storage.js` |
| FE axios | `packages/api-client/src/axiosInstance.ts` |
| DCC forward | `Common/FileService/DccHttpClient.cs` |

---

## Chejori in fasl ra «digested» koni (1 session)

1. Middleware truth table ra roye kaghaz bekesh (5 min)
2. PersonnelsDbContext + TenantQueryFilterExtensions ra IDE open (15 min)
3. Browser DevTools → yek GET personnel → header `X-Site-Id` verify (5 min)
4. Breakpoint `TenantContextMiddleware` + SQL log (15 min)
5. OutboxMessage row ba'd az SoftDelete — SiteIds column (10 min)
6. 25 soal ra boland javab bede (20 min)

---

## Deep dive — expression filter chejori SQL mishe?

EF global filter expression `dbContext.TenantIds.Contains(e.SiteId)` ra be parameterized SQL tabdil mikone. `TenantIds` property har query **evaluate** mishe (na compile-time constant). Yani:

- Request 1: TenantIds = {A} → `WHERE site_id = @pA` (ya `= ANY(@p)`)
- Request 2: TenantIds = {B} → parameter avaz — **hamon compiled model**, data digar

In cherā DbContext instance to expression `Expression.Constant(dbContext)` capture mishe — filter closes over live context.

**Pitfall:** age `TenantIds` ra `new HashSet` return koni har get (copy), behavior OK; age mutable set ra mid-request avaz koni, queries ba'di avaz mishan — Dejban set az middleware fixed-e per request.

---

## Deep dive — role claim format

```
type:  role
value: "3f2a…-guid-of-site|SuperAdmin"
```

Chera `site|role`?
- User mitone Role X dar Site A, Role Y dar Site B dashte bashe
- SuperAdmin detection: **any** site slot ba admin role name → flag `IsSuperAdmin = true` (global flag, na per-site)
- Permission/endpoint claims often via `site_claims` / transformation (Day 06 / 37)

**Smell nuance:** `IsSuperAdmin` boolean global-e. User SuperAdmin on Site A theoretically opens header Site Z (EF path). Organizational trust on SuperAdmin role assignment.

---

## Deep dive — component guard + siteReady (FE)

```javascript
// component-guard.jsx (conceptual)
const selectedSiteIds = useSiteStore(s => s.selectedSiteIds);
const siteReady = selectedSiteIds.length > 0
  || (!loading && !(siteClaims || []).length);

// age user site claim dare vali select nakarde → UI wait / block
```

Bedune siteReady: API bedune `X-Site-Id` → middleware `effective = userSiteIds` (multi) → list mixed sites — UX confusing. Layout often auto-selects first site when exactly one option.

---

## Deep dive — YARP / gateway

Gateway bayad `X-Site-Id` ra **forward** konad (default header forward usually OK). Age transform header drop konad → tenant context wrong.

Check YARP `AddTransforms` / header removes. Day 07 reminder: sensitive headers + hop-by-hop.

Auth cookie/Bearer ham forward. Tenant bedune auth → middleware context set **nemikone** (only when authenticated).

---

## Deep dive — create personnel validation sketch

```csharp
// Pseudo — pattern you want in handlers
var siteId = request.SiteId;
if (!tenant.IsSuperAdmin && !tenant.SiteIds.Contains(siteId))
    return Error.Forbidden(...);

var unit = await units.GetAsync(request.UnitId, ct);
if (unit is null || unit.SiteId != siteId)
    return Error.Validation(...);
```

EF filter alone **does not** block insert of wrong SiteId. Add FluentValidation `MustAsync` or handler check.

---

## Comparison table — Dejban vs textbook SaaS

| topic | Textbook SaaS | Dejban |
|---|---|---|
| Tenant key | TenantId (GUID/slug) | SiteId |
| Resolution | subdomain | JWT + `X-Site-Id` |
| Isolation | often RLS or DB-per | EF filter |
| Super user | support impersonation | SuperAdmin flag + header |
| Background | hangfire args | Outbox columns + MT headers |
| FE | tenant switcher | site switcher (single) |
| Modules | one app | modular monolith + copies |

---

## Glossary — tenancy words

| kalame | ma'ni |
|---|---|
| Tenant | boundary-e data (inja Site) |
| Discriminator | column SiteId |
| Ambient context | AsyncLocal TenantInfo |
| Effective sites | natije-ye JWT ∩ header / Super rules |
| Named query filter | SoftDeleteFilter / TenantFilter keys |
| Tenant leak | didan/neveshtan data-ye site digar |
| Impersonation | SuperAdmin acting in a site |
| Propagation | header/outbox copy of tenant |
| Scoped vs unscoped | filtered vs see-all SuperAdmin |
| IDOR | change id/siteId in body to access others |

---

## Mini lab (dasti — optional)

1. Login user limited to Site A
2. DevTools: edit request `X-Site-Id` = Site B GUID
3. Expect: empty list / not found (intersect)
4. Login SuperAdmin, same spoof to B → data B (if exists)
5. Soft-delete one personnel, confirm disappears from list, still in DB `is_deleted=true`
6. Breakpoint ProcessOutboxJob — see SetContext

---

## Common bugs seen in this codebase class

| bug | symptom | fix |
|---|---|---|
| Forgot UseTenantContext | all sites visible or weird | add middleware after auth |
| Job without SetContext | cascade deletes 0 rows | restore from message |
| IgnoreQueryFilters for convenience | leak | named ignore + manual where |
| FE no site selected | mixed multi-site data | force picker |
| Body SiteId ≠ header | orphan row other site | validate on write |
| Cache key no site | wrong site data flash | include siteId in key |

---

*Day 16 tamum. Ba'd: Day 17 — Minimal APIs + `IEndpoint` (amade). Fehrest: [README.md](./README.md).*
