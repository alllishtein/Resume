# Day 25 — HybridCache + Redis

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**HybridCache** (.NET) = abstraction ba **L1 in-process memory** + **L2 distributed** (inja Redis via `IDistributedCache`). Dejban wrapper: `ICacheService` / `CacheService` — `GetOrCreateAsync`, `SetAsync`, `RemoveAsync`, `RemoveByTagAsync` + Redis **tag→keys set** baraye invalidation.

Use case-haye asli: (1) **JWT blacklist** — HybridCache mostaghim, `DisableLocalCache` (multi-instance consistency), (2) **User site claims** — `RemoteClaimService` + tag `UserSiteClaims`, invalidate az Identity, (3) **Report data** — key ba site + query hash, tags per report/entity. Redis down → fallback `AddDistributedMemoryCache` (dev resilience) / blacklist fail-open. Chera cache? Hot path O(1); gheymat = stale data + invalidation complexity.

---

# BAKHSH-E AVAL: WORLD — Caching to donya

## Chera cache?

| bedune cache | ba cache |
|---|---|
| har request → DB / RPC | hot path O(1) memory/Redis |
| Identity claim enrichment slow | millisecond |
| Report query heavy | reuse result |

**Gheymat:** stale data, invalidation complexity, memory, stampede, debugging harder. Yani har cache ye tradeoff-e consistency vs latency.

---

## Cache levels

| level | koja | latency | shared? |
|---|---|---|---|
| **L1** | process memory | µs–ms | no (per instance) |
| **L2** | Redis / Memcached | ms | yes (all instances) |
| **L3** | CDN / HTTP cache | — | edge |

**Hybrid** = L1 then L2 then factory (DB).

```
Get(key):
  L1 hit? → return
  L2 hit? → populate L1 → return
  miss → factory() → set L1+L2 → return
```

Multi-instance ASP.NET: L1 alone kafi nist — L2 (Redis) shared truth midahad.

---

## Cache-aside (lazy loading) — common

```csharp
var value = await cache.GetAsync(key);
if (value is null)
{
    value = await db.LoadAsync(...);
    await cache.SetAsync(key, value, ttl);
}
return value;
```

HybridCache `GetOrCreateAsync` = cache-aside + **stampede protection** (single factory flight per key often).

Other patterns: read-through, write-through, write-behind — rarer in app code. Dejban = cache-aside + explicit invalidate on write.

---

## TTL / expiration

| term | ma'ni |
|---|---|
| **Absolute expiration** | die at T+ttl from set |
| **Sliding** | refresh on access (Hybrid options vary) |
| **LocalCacheExpiration** | L1 shorter than L2 typical |

Dejban defaults (`CacheOptions`):

- L1: **5 min**
- L2: **20 min**

Claims: L1 **2 seconds** — fast invalidate feel across instances via L2 + tag remove. Blacklist: L1 **off** (`DisableLocalCache`) — revoke nabayad stale L1 dashte bashe.

---

## Invalidation strategies

| strategy | mesal |
|---|---|
| TTL only | simple; accept staleness |
| Remove by key | `RemoveAsync(userId)` |
| Remove by tag | all keys tagged `UserSiteClaims` |
| Version in key | `user:{id}:v{n}` bump n |
| Event-driven | after SaveChanges publish → listeners invalidate |

**Hard problem:** «which keys does this update affect?» — tags / secondary indexes help. Forget Invalidate = stale permissions until TTL.

---

## Cache stampede (thundering herd)

1000 requests miss same key → 1000 DB queries.

Mitigations:

- HybridCache coalescing / locks per key  
- soft TTL + background refresh  
- probabilistic early expiration  

Factory bayad idempotent-ish bashe — SaveChanges to GetOrCreate = N writes under storm.

---

## Key design

```
{namespace}:{tenant?}:{entity}:{id}:{variant}
```

Examples:

- `revoked:{jti}` — blacklist  
- `userId` alone — claims (simple; collision risk if other features use same)  
- `report-data:{reportId}:site:{siteKey}:q:{hash16}` — report  

**Must include tenant/site** when data is tenant-scoped (Day 16) — ReportDataCache does; bare `userId` is global per user (OK for claims).

Avoid huge keys; avoid storing secrets unencrypted. Cross-tenant leak via bad key = security bug.

---

## Serialization

L2 stores bytes — JSON/MessagePack. Types must be serializable. `DataTable` → Dejban converts to DTO entry then back.

Circular refs / polymorph — careful. Report path: columns rebuild as `string` — type loss.

---

## Consistency models

| model | ma'ni |
|---|---|
| **Eventual** | cache lags DB briefly |
| **Strong** | always read DB (no cache) or transactional cache (rare) |

Authz claims: short L1 + invalidate on write ≈ good enough. Money balances: often **no cache** or careful. Outbox messages ≠ cache — Day 22: cache invalidate after SaveChanges, not in outbox.

---

## Redis primitives (ops literacy)

| structure | use |
|---|---|
| STRING | GET/SET values (IDistributedCache) |
| SET | Dejban tag→key index `tag:{name}` |
| HASH / LIST / STREAM | advanced (not central here) |

TTL on keys. Persistence RDB/AOF — ops choice. Cluster vs single — Dejban typical single/sentinel. SignalR backplane Redis (Day 26) joda az in HybridCache Redis — hamon infra momken, concern joda.

---

## IMemoryCache vs IDistributedCache vs HybridCache

| API | scope |
|---|---|
| `IMemoryCache` | L1 only |
| `IDistributedCache` | L2 only (Redis) |
| **`HybridCache`** | L1+L2 unified API (.NET 9+ / package) |

HybridCache is the modern recommendation for multi-instance ASP.NET. Side-by-side IMemoryCache for same key = divergent truth — smell.

---

## Failure modes

| failure | options |
|---|---|
| Redis down | fail-open (serve without cache / assume not revoked) vs fail-closed |
| L1 stale after other instance update | short L1 TTL + tag invalidation on L2 |
| Network partition | timeouts (blacklist 2s CTS) |

Dejban blacklist: **fail-open** on timeout/error (Day 06) — availability bias. Claims: exception bubbles (caller). Memory fallback mode: multi-instance **not shared** — prod misconfig = security/consistency bug.

---

# BAKHSH-E DOVOM: DEJBAN — HybridCache + Redis to in proje

## Registration — `AddCacheServices`

```csharp
// Common/.../ServiceCollectionExtensions.cs
public static IServiceCollection AddCacheServices(
    this IServiceCollection services, string redisConnectionString)
{
    services.AddHybridCache();

    try
    {
        IConnectionMultiplexer mux = ConnectionMultiplexer.Connect(redisConnectionString);
        services.AddSingleton(mux);
        services.AddStackExchangeRedisCache(options =>
            options.ConnectionMultiplexerFactory = () => Task.FromResult(mux));
    }
    catch
    {
        services.AddSingleton<IConnectionMultiplexer>(_ => null!);
        services.AddDistributedMemoryCache(); // L2 = in-memory fallback
    }

    services.TryAddSingleton<ICacheService, CacheService>();
    services.TryAddSingleton<IReportAccessTicketStore, ReportAccessTicketStore>();
    return services;
}
```

Called from Dejban `AddInfrastructure` (+ Identity/others via shared Common).

**Smell:** swallow connect exception → silent memory mode in prod if Redis misconfigured — monitor. Lab: breakpoint catch path.

---

## `ICacheService` API

```csharp
ValueTask<T> GetOrCreateAsync<T>(
    string key,
    Func<CancellationToken, ValueTask<T>> factory,
    string[]? tags = null,
    TimeSpan? expiration = null,              // L2
    TimeSpan? localCacheExpiration = null,    // L1
    bool disableLocalCache = false,
    CancellationToken cancellationToken = default);

ValueTask SetAsync<T>(...);
ValueTask RemoveAsync(string key, ...);
ValueTask RemoveByTagAsync(string[] tags, ...);
```

App features az `ICacheService` mian; blacklist az `HybridCache` mostaghim — special flags.

---

## `CacheService` — HybridCache + tag index

```csharp
public sealed class CacheService(HybridCache cache, IConnectionMultiplexer? redis) : ICacheService
{
    public async ValueTask<T> GetOrCreateAsync<T>(...)
    {
        var value = await cache.GetOrCreateAsync(
            key, factory,
            CacheOptions.Create(expiration, localCacheExpiration, disableLocalCache),
            tags: tags ?? [],
            cancellationToken: cancellationToken);

        await SetTagsWithKey(tags, key); // Redis SET tag:{tag} → key
        return value;
    }

    public async ValueTask RemoveByTagAsync(string[] tags, CancellationToken ct)
    {
        await cache.RemoveByTagAsync(tags, ct); // Hybrid built-in tag support

        if (redis == null) return;
        // ALSO manually delete keys from Redis SET index + delete tag key
        foreach (var tag in tags)
        {
            var members = await db.SetMembersAsync($"tag:{tag}");
            if (members.Length > 0) await db.KeyDeleteAsync(members...);
            await db.KeyDeleteAsync($"tag:{tag}");
        }
    }
}
```

**Dual tag strategy:** HybridCache tags + custom Redis SET index. Belt and suspenders — understand both when debugging leftover keys. Clearing only one side leaves ghosts — use `ICacheService.RemoveByTagAsync`.

---

## Default TTLs

```csharp
public static HybridCacheEntryOptions DefaultExpiration => new()
{
    LocalCacheExpiration = TimeSpan.FromMinutes(5),
    Expiration = TimeSpan.FromMinutes(20)
};

// disableLocalCache → Flags DisableLocalCache | DisableCompression
```

---

## Use case 1 — Token blacklist (HybridCache direct)

```csharp
// TokenBlackListService — NOT via ICacheService
public async Task<bool> IsRevokedAsync(string key)
{
    using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(2));
    return await cache.GetOrCreateAsync(
        $"revoked:{key}",
        _ => ValueTask.FromResult(false), // miss → not revoked
        new HybridCacheEntryOptions
        {
            Flags = DisableLocalCache | DisableDistributedCacheWrite
        },
        cancellationToken: cts.Token);
}
// on miss: does NOT write false to Redis (DisableDistributedCacheWrite)
// on hit of true: revoked

public async Task RevokeAsync(string key, TimeSpan expireAfter)
{
    await cache.SetAsync($"revoked:{key}", true, new HybridCacheEntryOptions
    {
        Expiration = expireAfter,
        Flags = DisableLocalCache // all instances see Redis
    });
}
```

**Chera DisableLocalCache?** Multi-instance: instance A revokes; B must not trust L1 stale «not revoked».

**Fail-open:** timeout/exception → `false` (allow). Day 06 deep dive.

Linked: `AddTokenBlackList` + `TokenRevokeMiddleware` (Day 06). Day 25 = caching platform; Day 06 = security story — cross-link, don't skip either.

---

## Use case 2 — User site claims (`RemoteClaimService`)

```csharp
return await cacheService.GetOrCreateAsync(
    userId,
    async (ct) =>
    {
        var response = await _client.GetResponse<GetUserSiteClaimsResponse>(
            new GetUserSiteClaims(userId), ct);
        return response.Message.UserSiteClaims;
    },
    tags: [CacheTags.UserSiteClaims],
    localCacheExpiration: TimeSpan.FromSeconds(2),
    cancellationToken: cancellationToken);
```

- Key = `userId`  
- Tag = `UserSiteClaims`  
- L1 very short (2s) — after Identity invalidates L2/tag, L1 dies quick  
- Miss → MassTransit request/response to Identity (`GetUserSiteClaims`)

### Invalidation — `UserSiteClaimsCache` (Identity)

```csharp
InvalidateUsersAsync(ids) → RemoveAsync(userId) each
InvalidateByRoleIdsAsync → resolve userIds from DB → InvalidateUsers
InvalidateByPositionIds / SiteIds → similar graph queries (IgnoreQueryFilters)
InvalidateAllAsync → RemoveByTagAsync([CacheTags.UserSiteClaims])
```

Called from AssignClaims, GrantSites, UpdatePosition, CreateSite super-admin grant, DeleteRoles, …

**Pattern:** write path in Identity **must** invalidate — forget = stale permissions until TTL (20 min L2 worst). **IgnoreQueryFilters** to resolve userIds: soft-deleted links / sites still must invalidate surviving users — safer over-invalidation than stale allow.

---

## Use case 3 — Report data cache

```csharp
// key includes site + query hash — tenant-safe
$"report-data:{reportId}:site:{siteKey ?? "all"}:q:{hash16}"

tags: report-data:report:{id}, report-data:entity:{module}:{entity}
ttl: clamp(DataCacheSeconds, 30, 600)
localCacheExpiration: 30s
```

`DataTable` ↔ serializable `ReportDataCacheEntry` (columns + string rows).

Invalidate: by report tag or entity tag when definitions/data change.

**Type loss:** `FromEntry` rebuilds columns as `typeof(string)`. Downstream must not assume Int32/DateTime column types from cache path — convert explicitly if needed.

---

## CacheTags constants

```csharp
public static class CacheTags
{
    public const string UserSiteClaims = "UserSiteClaims";
}
```

Report tags built inline — could centralize more (smell: magic strings scattered).

---

## Multi-tenancy reminder

| cache | site in key? |
|---|---|
| Claims by userId | N/A (user-scoped) |
| Report data | **yes** `site:{siteKey}` |
| Blacklist jti | global token id |
| Generic feature | **must** add SiteId if data tenant-owned |

Stale cross-tenant leak = security bug — treat key design as authz.

---

## Stampede / GetOrCreate

HybridCache `GetOrCreateAsync` factory should be **idempotent-ish** (same result). Heavy factory under miss storm — still prefer one flight; don't put non-idempotent writes in factory.

Claims factory = RPC to Identity — OK. Don't CreateUser inside GetOrCreate.

---

## Connection to JWT day

Day 06 = blacklist *security* story.  
Day 25 = *caching platform* + other consumers of same Redis/HybridCache.

Overlap intentional — cross-link, don't skip either.

---

## Smell-ha

1. **Redis connect catch → memory** silent  
2. **Blacklist fail-open**  
3. **Claims key = bare userId** — namespace collision if other code uses same key  
4. **Dual tag invalidation** Hybrid + Redis SET — complexity  
5. **Forget Invalidate** on some Identity write paths  
6. **Report DataTable** as stringly rows — type loss  
7. **ICacheService Singleton** holding HybridCache — OK; don't capture scoped DbContext in factory wrongly  
8. **Tag SET without TTL** on `tag:{name}` — can grow; keys deleted on RemoveByTag but orphan risk  
9. **No cache metrics** dashboard standard  
10. **L1 5 min default** long for some admin UIs  
11. **DisableCompression** bundled with disableLocalCache flag combo — check intent  
12. **RemoteClaimService** on every enriched request path — depends on hit rate  

---

## Debug checklist

1. Redis PING / connection string  
2. `redis-cli KEYS revoked:*` after logout  
3. Claims: change role → Invalidate called? → `Remove` / tag  
4. Still stale? wait L1 2s; hard refresh; check wrong userId key  
5. Report wrong site data → inspect key site segment  
6. HybridCache vs ICacheService — which API did feature use?  
7. Fallback memory mode? (IConnectionMultiplexer null)  

---

## 25 soal-e mosahebe

1. HybridCache chie?  
2. L1 vs L2?  
3. Cache-aside?  
4. Stampede?  
5. Chera claims DisableLocal short?  
6. Chera blacklist DisableLocalCache?  
7. Fail-open vs fail-closed?  
8. Tag invalidation?  
9. Key design multi-tenant?  
10. GetOrCreate vs Get+Set?  
11. IDistributedCache role?  
12. Redis down Dejban?  
13. RemoteClaimService flow?  
14. UserSiteClaimsCache invalidate graph?  
15. Report key hash?  
16. TTL absolute?  
17. Serialization issues?  
18. Write-through?  
19. Cache in factory anti-pattern?  
20. Singleton ICacheService?  
21. CDN vs Redis?  
22. Consistency claims after role change?  
23. HybridCache vs IMemoryCache only?  
24. Monitor hit ratio?  
25. Security of caching PII?

---

## Senario-ha

### A) Login enrichment  
Miss claims → MT GetUserSiteClaims → cache set tagged → next requests L1/L2 hit.

### B) AssignClaimsToUser  
InvalidateUsers(userId) → Remove key → next request miss → fresh claims.

### C) Revoke token  
Set `revoked:jti` DisableLocal → all instances IsRevoked true from Redis.

### D) Redis restart empty  
All miss; DB/RPC load spike — stampede risk; warmup optional.

### E) Report same query two sites  
Different keys (`site:A` vs `site:B`) — no cross leak.

---

## Mini lab

1. Trace `AddCacheServices` + `CacheService`  
2. Logout → redis-cli find `revoked:`  
3. Assign claim → breakpoint InvalidateUsers  
4. Breakpoint RemoteClaimService factory (should rare if warm)  
5. Report cache key log / Redis KEYS `report-data:*`  

---

## Resume

**short:**

> Built a HybridCache-on-Redis platform (`ICacheService`) with L1/L2 TTLs and tag-based invalidation, used for JWT revocation (distributed-only entries), cached user site claims with Identity-side invalidation, and tenant-scoped report result caching.

**bullets:**

- Wrapped `Microsoft.Extensions.Caching.Hybrid` with Redis-backed distributed cache and fallback memory mode  
- Implemented tag→key Redis SETs plus `RemoveByTagAsync` for bulk invalidation (`UserSiteClaims`, report tags)  
- Hardened token blacklist with `DisableLocalCache` and short timeouts / fail-open policy  
- Designed report cache keys including `site` and query hash to prevent cross-tenant reuse  

**skills:** `HybridCache, Redis, StackExchange.Redis, Cache-Aside, Cache Invalidation, Tag-Based Eviction, Distributed Caching, ASP.NET Core, Performance`

---

## File-haye mohem

| chi | koja |
|---|---|
| ICacheService | `Common/Caching/ICacheService.cs` |
| CacheService | `Common/Caching/CacheService.cs` |
| CacheOptions | `Common/Caching/CacheOptions.cs` |
| CacheTags | `Common/Caching/CacheTags.cs` |
| TokenBlackListService | `Common/Caching/TokenBlackListService.cs` |
| AddCacheServices | `Common/.../ServiceCollectionExtensions.cs` |
| RemoteClaimService | `Common/Claims/RemoteClaimService.cs` |
| UserSiteClaimsCache | `IdentityServer/.../UserSiteClaimsCache.cs` |
| ReportDataCache | `Reporting/Infrastructure/ReportDataCache.cs` |

---

## Connection to other days

| day | rabt |
|---|---|
| 06 JWT | blacklist on HybridCache |
| 16 Tenancy | site in report keys |
| 18 DI | AddCacheServices in infra |
| 20 MassTransit | GetUserSiteClaims RPC on miss |
| 22 Outbox | cache invalidate **after** SaveChanges (not in outbox) |
| 24 Decorator | optional CachingRepository decorate — not used |
| 26 SignalR | Redis backplane joda az HybridCache (concern joda) |

---

## Chejori digest koni

1. Draw L1→L2→factory (5 min)  
2. Read CacheService + blacklist flags (20 min)  
3. Claims GetOrCreate + Invalidate path (20 min)  
4. Report key design (10 min)  
5. 25 soal (20 min)

---

## Glossary

| kalame | ma'ni |
|---|---|
| L1 / L2 | memory / Redis layers |
| HybridCache | unified L1+L2 API |
| Cache-aside | app loads DB on miss |
| Stampede | many misses one key |
| Tag | label to invalidate groups |
| TTL | time to live |
| Fail-open | on cache error, allow |
| DisableLocalCache | skip L1 for that entry |
| Hit ratio | hits / (hits+misses) |

---

## Deep dive — why claims L1 = 2 seconds?

Identity invalidates Redis/tag on write. Other instances may still hold L1 up to local TTL. **2s** bounds max authz staleness per instance after remote invalidation (plus network). Shorter → more L2 load; longer → longer stale permissions window.

Blacklist cannot afford even 2s L1 after revoke → `DisableLocalCache`.

---

## Deep dive — InvalidateBySiteIds cost

```csharp
// multiple queries: Users.Sites, UserRoles, UserPositions, Roles.Sites, Positions.Sites...
// then Distinct userIds → RemoveAsync each
```

Correct but **heavy** on large sites. Alternative: version stamp `claims:ver` in key — bump version per site (cheaper invalidate, more key churn). Dejban chose explicit user key removal.

---

## Deep dive — HybridCache tags vs Redis SET

Microsoft HybridCache has native `tags` on GetOrCreate + `RemoveByTagAsync`. Dejban **also** maintains `tag:{name}` Redis SETs in `SetTagsWithKey`.

Possible reasons: older behavior / multi-provider / ensure raw Redis key delete. Ops: clearing only one side leaves ghosts — use `ICacheService.RemoveByTagAsync`.

---

## Decision guide — should I cache this?

| data | cache? |
|---|---|
| JWT revoked flag | yes (required for revoke) |
| User claims | yes (hot) |
| Report query result | yes (expensive) |
| Bank balance / stock qty | usually no / short + lock |
| Random GUID lookup once | no |
| Per-request tenant list from JWT | already in token — don't duplicate wrongly |

---

## End-to-end walkthrough — claims miss → hit → invalidate

```
[Gateway] JWT ok → enrich claims
    │
    ▼
RemoteClaimService.GetUserSiteClaimsAsync(userId)
    │
    ├─ L1 hit (same process, <2s old)? → return HashSet<SiteClaimDTO>
    ├─ L2 hit (Redis)? → fill L1 → return
    └─ miss → IRequestClient<GetUserSiteClaims> → Identity
              → store with tag UserSiteClaims
              → SetTagsWithKey → SADD tag:UserSiteClaims {userId}

[Admin] AssignClaimsToUser / GrantSites / …
    │
    ▼
UserSiteClaimsCache.InvalidateUsersAsync([userId])
    → cache.RemoveAsync(userId)   // Hybrid L1+L2
    // OR InvalidateAll → RemoveByTagAsync([UserSiteClaims])
    //    → Hybrid RemoveByTag + Redis KeyDelete members of tag set

[Next request same user]
    → miss → fresh RPC → new cache entry
```

---

## End-to-end — report cache

```
GET report data (site A, query Q)
  key = report-data:{id}:site:A:q:{sha256(Q)[0..16]}
  tags = report-data:report:{id}, report-data:entity:{module}:{entity}
  ttl = clamp(DataCacheSeconds, 30, 600); L1 = 30s
  factory → SQL/DataTable → ToEntry (string columns/rows) → cache
  return FromEntry → DataTable (all string columns)

Invalidate report definition → InvalidateReportAsync(id) → RemoveByTag report tag
Invalidate entity module data → InvalidateEntityAsync → entity tag
```

---

## Blacklist vs ICacheService — two APIs, one Redis

| | TokenBlackListService | CacheService / ICacheService |
|---|---|---|
| inject | `HybridCache` direct | `HybridCache` + optional `IConnectionMultiplexer` |
| key prefix | `revoked:` | caller-defined |
| tags | no | yes + Redis SET |
| DisableLocalCache | **always** | optional flag |
| IsRevoked miss write | **DisableDistributedCacheWrite** (no write `false`) | normal GetOrCreate writes |
| fail policy | catch → false (open) | exception bubbles (caller) |

**Chera blacklist nemire az ICacheService?** Special flags + fail-open + no tags. Mixing would clutter the wrapper.

---

## `DisableDistributedCacheWrite` explained

`IsRevokedAsync` factory returns `false` on miss. Without `DisableDistributedCacheWrite`, HybridCache would **write `false` to Redis** with some TTL — polluting L2 with «not revoked» entries and racing with `RevokeAsync(true)`.

Flags combo:

- read path: DisableLocalCache | DisableDistributedCacheWrite  
- write revoke: DisableLocalCache + Expiration  

---

## ReportAccessTicketStore (sibling)

`AddCacheServices` also registers `IReportAccessTicketStore` / `ReportAccessTicketStore` — short-lived tickets for opening reports (often Stimulsoft / viewer). Same Redis/Hybrid family, different key namespace. When debugging «report won't open», check ticket TTL separately from `ReportDataCache` data TTL.

---

## Ops — redis-cli cheat sheet (lab)

```bash
redis-cli PING
redis-cli KEYS "revoked:*"
redis-cli GET "revoked:<jti>"          # depends on Hybrid serialization format — may be binary
redis-cli SMEMBERS "tag:UserSiteClaims"
redis-cli KEYS "report-data:*"
redis-cli TTL "revoked:<jti>"
```

Note: HybridCache may prefix/encode keys — `KEYS *revoked*` safer than exact. Prod: prefer `SCAN`, not `KEYS`.

---

## Memory fallback mode — consequences

When `ConnectionMultiplexer.Connect` throws at startup:

1. `IConnectionMultiplexer` registered as `null!`  
2. `AddDistributedMemoryCache` — L2 = **in-process**, not shared  
3. `SetTagsWithKey` / Redis half of `RemoveByTag` **no-ops** (`redis == null`)  
4. Hybrid `RemoveByTagAsync` still runs against memory L2  

**Multi-instance with fallback:** each node own cache → blacklist/claims **not shared**. Dev OK; prod misconfig = security/consistency bug. Log/alert on catch path.

---

## Concurrency — GetOrCreate factory rules

Do **not** inside factory:

- mutate shared statics without lock  
- call `SaveChanges` that must happen exactly once (stampede → N writes)  
- capture disposed scoped services incorrectly  

Do:

- pure read / idempotent RPC (GetUserSiteClaims)  
- build DataTable from query  

`UserSiteClaimsCache` is typically **scoped** (DbContext) while `ICacheService` is **singleton** — invalidate methods run in request scope; OK. Factory in RemoteClaimService only uses `IRequestClient` — OK for singleton claim service.

---

## Security checklist (cache)

1. Never cache plaintext passwords / refresh tokens as values  
2. Blacklist keys are jti/ids — OK  
3. Claims DTO may include permission ids — treat Redis ACL / network as sensitive  
4. Report rows may be PII — Redis encryption-in-transit (TLS) + access control  
5. Key must include site for tenant data (report does)  
6. Admin InvalidateAll is powerful — audit who can trigger  

---

## Common bugs (real)

| bug | symptom | fix mindset |
|---|---|---|
| Forgot Invalidate after AssignClaims | user still old perms ≤ L2 TTL | call UserSiteClaimsCache on every write |
| Cached with site=null as `all` then filtered in app | cross-site leak risk | always pass siteKey |
| Used IMemoryCache beside Hybrid for same key | divergent truth | one platform |
| Assumed DataTable types after cache | format exceptions | string columns |
| Relied on L1 after revoke | other instance still allows | DisableLocalCache |
| Redis down, thought shared | nodes disagree | health check Redis |

---

## Mini architecture diagram

```
                    ┌─────────────┐
   ASP.NET apps ───▶│ HybridCache │── L1 Memory (per process)
                    └──────┬──────┘
                           │ L2
                    ┌──────▼──────┐
                    │IDistributed │
                    │   Cache     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Redis OK    Memory fallback   (blacklist flags
         + tag SETs   (dev / fail)      skip L1 always)
```

`ICacheService` sits above HybridCache for app features. `TokenBlackListService` sits beside it on same HybridCache.

---

## Lab extended (45–60 min)

1. **Startup:** breakpoint `AddCacheServices` — Redis connect success or catch?  
2. **Revoke:** logout → `KEYS *revoked*` → confirm TTL ≈ access token remaining / default 15m  
3. **Claims warm:** first API after login → factory hits Identity (log MT). Second within 2s → L1. After 2s → maybe L2 only.  
4. **Invalidate:** AssignClaims → `RemoveAsync(userId)` → next request factory again.  
5. **Tag bomb:** `InvalidateAllAsync` → SMEMBERS empty / keys gone.  
6. **Report:** same query two sites → two keys; change query whitespace → new hash → miss.  
7. **Kill Redis mid-flight:** observe blacklist fail-open; claims may throw/timeout depending on Hybrid behavior — note it.  

---

## Resume (expanded angle)

Agar mosahebe «performance» khast:

> «Hot paths were MultiGet against Identity over MassTransit. We introduced HybridCache with a 2-second local TTL and Redis L2, plus explicit invalidation from Identity when assignments change, so we cut RPC volume without long-lived stale permissions.»

Agar «security» khast:

> «Token revocation cannot use process-local cache. We set DisableLocalCache on blacklist entries and fail open only on Redis timeout with a 2-second CTS — documented tradeoff versus fail-closed.»

---

## Interview 60s

> «We use HybridCache with Redis as L2. ICacheService adds tag-based invalidation. Token blacklist disables L1 so all nodes see revocations. User claims are cached with a UserSiteClaims tag and invalidated from Identity when roles or assignments change. Report caches include site id in the key to stay tenant-safe.»

---

## Quick self-test (javab-e kutah)

1. Default L1/L2 TTL? → 5m / 20m  
2. Claims L1? → 2s  
3. Report L1? → 30s  
4. Blacklist key prefix? → `revoked:`  
5. Tag constant? → `UserSiteClaims`  
6. Redis tag key format? → `tag:{tag}`  
7. Connect fail? → DistributedMemory + null mux  
8. IsRevoked on error? → false  
9. Site in report key? → yes  
10. Query identity in key? → SHA256 hex 16 chars  

Agar 8/10+ OK → Day 26.

---

## Map to resume keywords (ATS)

`HybridCache` · `Redis` · `StackExchange.Redis` · `IDistributedCache` · `cache invalidation` · `tag-based eviction` · `cache-aside` · `distributed caching` · `stampede protection` · `JWT blacklist` · `multi-tenant cache keys`

---

## What Day 25 is *not*

- Not Redis Streams / pub-sub backplane (SignalR Day 26 may use Redis separately)  
- Not full CDN / HTTP caching theory  
- Not replacing EF second-level cache  
- Not Quartz job that warms cache (optional pattern elsewhere)  

Focus: **app-level HybridCache platform + three Dejban consumers**.

---

## Final checklist before mosahebe

- [ ] L1 vs L2 va HybridCache ra ba ye diagram mikesham  
- [ ] fargh-e blacklist flags vs ICacheService  
- [ ] InvalidateUsers vs InvalidateBySiteIds (graph)  
- [ ] chera site to report key  
- [ ] fail-open blacklist + memory fallback risk  
- [ ] dual tag (Hybrid + Redis SET)  
- [ ] resume 4 bullet amade  

---

*Day 25 tamum. Ba'd: Day 26 — SignalR (server) (amade). Fehrest: [README.md](./README.md).*
