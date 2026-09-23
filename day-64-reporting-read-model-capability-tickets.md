# Day 64 — Reporting read-model + capability tickets

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Reporting service** ye microservice-e ke hich domain write-i nadare — khodesh entity-i nemisaze, chizi update nemikone. Dar avaz, **chand ta EF DbContext** be hamun Postgres-e share-shode register mikone (har kodum ba schema-ye module-e khodesh) va faghat **read** mikone. In ye olgu-ye pragmatic-e CQRS-lite-e: write-ha mal-e module-ha-n (Personnels, Vehicles, Visitors, …), read-ha mal-e Reporting-e. Ba'd vaghti Stimulsoft (Day 39) mikhad report neshun bede, nabayad JWT-e user ro to URL-e designer/viewer bezarim — in ye masir-e leak-e amniati-e. Baraye hamin ye **capability ticket** (opaque short-lived token ba TTL) mint mikonim va to URL mizarim.

Do ta olgu-ye kamel inja dari: **multi-context read model** va **capability ticket pattern**. Har do tashun resume-worthy-an va to mosahebe kheili khoob jur-dar miyan.

---

# BAKHSH-E AVAL: WORLD — read model va capability ticket

## Farz kon

Ye ketabkhane-ye bozorg (Reporting) ke hich ketabi nanevisht — faghat az ghafase-haye module-ha (Personnels, Visitors, Armory, …) ketab-ha ro mikhune va neshun mide. Kilid-e vorud-esh (capability ticket) 5 daghighe e'tebar dare — na kilid-e khoone (JWT).

## CQRS chikar mikone?

| | Write side | Read side |
|---|---|---|
| **mas'uliat** | validate, enforce rules, save | query, project, return |
| **model** | domain entity rich | flat DTO / projection |
| **consistency** | strong (transaction) | eventual ya stale-ok |
| **store** | module DB | same DB / replica / materialized view |

CQRS-e kamel (full) ye store-e joda baraye read dare (event-sourced), vali **CQRS-lite** mige: man az hamun DB mikhunam, vali ba ye DbContext-e mokhtas-e read ke write nemikonam.

## Chera multi DbContext?

To ye system-e modular/microservice:
- Har module ye schema dare (masalan `personnels`, `visitors`, `vehicles`)
- Reporting mikhad az **hame**-ye in schema-ha bekhune
- Age ye mega-DbContext besazi ke hame-ye entity-ha ro dashte bashe, coupling-e shidid peyda mikoni
- Raah-e behtar: **har module ye read-only DbContext dare** — Reporting hamashun ro register mikone

```
Reporting Process
├── PersonnelsDbContext    → schema: personnels
├── VisitorsDbContext      → schema: visitors
├── VehiclesDbContext      → schema: vehicles
├── ArmoryDbContext        → schema: armory
├── CashLogisticsDbContext → schema: cash_logistics
├── SecurityPatrolsDbContext → schema: security_patrols
├── WeighBridgeDbContext   → schema: weigh_bridge
├── InventoryDbContext     → schema: inventory
└── IdentityServerDbContext → identity DB (joda)
```

## Read-only DbContext — yani chi?

Ye DbContext ke:
1. `AsNoTracking` default-e (ya dasti gozashte mishe)
2. Hich `SaveChanges` nadare (ya throw mikone)
3. Migration-i tolid nemikone (module-e asli owner-e migration-e)
4. Connection string-esh read replica mitune bashe (ya hamun primary)

**Smell:** age Reporting tasadofi benevisad to schema-ye ye module-e dge, data integrity kharab mishe.

## Capability ticket — yani chi?

Farz kon mikhay ye link be user bedi ke to browser baz kone va report ro bebine. In link bayad authenticated bashe. Do rah dari:

| raveesh | risk |
|---|---|
| JWT to URL: `/report?access_token=eyJ...` | JWT to server log mire, to Referer header mire, to browser history mimune, to proxy log mimune |
| Capability ticket: `/report?ticket=abc123` | ticket opaque-e, 5 daghighe omr dare, yek bar masraf mishe (ya chand bar to TTL) |

**Capability ticket** ye **opaque string** ke server mint mikone ba'd az inke user authenticate shode, va to ye store-e movaghati (masalan Redis) negah midare. Client in ticket ro to URL mizare; server vaghti request miad, ticket ro az store migire va JWT-e vaghei-e user ro recover mikone.

```
Browser (authenticated)
  │  POST /Design/CreateAccessTicket
  │  Authorization: Bearer <JWT>
  │◄── { ticket: "abc123", expiresInSeconds: 300 }
  │
  │  window.open("/Design/ViewReport?reportId=xxx&ticket=abc123")
  │
Server
  │  TryGet("abc123") → { AccessToken: "eyJ...", SiteId: "..." }
  │  Set Authorization header internally
  │  Render Stimulsoft viewer
```

## Capability ticket dar barabar-e design-haye dge

| alternative | mas'ale |
|---|---|
| JWT to query string | leak: log, referrer, history, proxy |
| Cookie-based auth | Stimulsoft AJAX calls momkene cookie ro dorost handle nakone; cross-origin |
| Signed URL (S3-style) | khoobe vali pichide-tar-e; bayad expiry + signature check dashte bashi |
| Session-based | stateful-e; Stimulsoft render momkene to ye process-e dge bashe |

Capability ticket sade-tar az signed URL-e va amniat-e behtari az JWT-in-URL dare.

## TTL va lifecycle

```
CreateAsync(accessToken, siteId)
  → Guid.NewGuid().ToString("N")  →  key = "report-access-ticket:{ticketId}"
  → Redis SET with AbsoluteExpiration = 5 min
  → return ticketId

TryGetAsync(ticketId)
  → Redis GET "report-access-ticket:{ticketId}"
  → age bud: return payload (AccessToken + SiteId)
  → age nabud: return null → 401
```

**5 daghighe** kafi-e ke user report ro baz kone; age kametar bashe, slow connection ya Stimulsoft AJAX-ha momkene fail beshan; age bishtar bashe, window-e attack bozorg-tar mishe.

---

## Security deep dive — chera JWT to URL bad-e

1. **Server access log:** `GET /report?access_token=eyJ...` — hamash to log-e Nginx/YARP/Kestrel save mishe
2. **Referer header:** Stimulsoft momkene ye resource-e external load kone → `Referer: https://site/report?access_token=eyJ...` be un server mire
3. **Browser history:** user browser ro baste → ye nafar-e dge history ro baz mikone → JWT ro mibine
4. **Proxy / CDN logs:** corporate proxy-ha URL-ha ro log mikonan
5. **Shoulder surfing:** JWT to address bar peydas-e

Ba capability ticket, hich kodum az in-ha JWT ro leak nemikonan — faghat ye opaque string ke 5 daghighe omr dare va bedun-e server-side store bi-ma'ni-e.

---

## Consistency model — stale reads

Reporting az **hamun Postgres** mikhune ke module-ha neveshtand. Pas:
- Vaghti ye personnel to PersonnelsService save beshe, Reporting **fori** mitune bekhune-sh
- Vali age read replica bud, ye lag-i hast (usually ms to seconds)
- Reporting hich cache-e query nadare (magar `IReportDataCache` baraye metadata)

**Yani:** eventual consistency inja **zero** ya near-zero-e — in ye maziat-e in olgu bar alayh-e ye warehouse-ye joda ke bayad ETL ya CDC dashte bashi.

---

# BAKHSH-E DOVOM: DEJBAN — chetori piade shode

## Program.cs — inventory-e DbContext-ha

```csharp
// Reporting/Program.cs (simplified)

// Reporting's own DB (report definitions, saved reports)
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Postgres")));

// Dejban module read contexts — same Postgres, different schemas
var dejbanConn = builder.Configuration.GetConnectionString("DejbanPostgres");

builder.Services.AddDbContext<PersonnelsDbContext>(o =>
    o.UseNpgsql(dejbanConn).UseSnakeCaseNamingConvention());
builder.Services.AddDbContext<VehiclesDbContext>(o =>
    o.UseNpgsql(dejbanConn).UseSnakeCaseNamingConvention());
builder.Services.AddDbContext<ArmoryDbContext>(o =>
    o.UseNpgsql(dejbanConn).UseSnakeCaseNamingConvention());
builder.Services.AddDbContext<CashLogisticsDbContext>(o =>
    o.UseNpgsql(dejbanConn).UseSnakeCaseNamingConvention());
builder.Services.AddDbContext<VisitorsDbContext>(o =>
    o.UseNpgsql(dejbanConn).UseSnakeCaseNamingConvention());
builder.Services.AddDbContext<SecurityPatrolsDbContext>(o =>
    o.UseNpgsql(dejbanConn).UseSnakeCaseNamingConvention());
builder.Services.AddDbContext<WeighBridgeDbContext>(o =>
    o.UseNpgsql(dejbanConn).UseSnakeCaseNamingConvention());
builder.Services.AddDbContext<InventoryDbContext>(o =>
    o.UseNpgsql(dejbanConn).UseSnakeCaseNamingConvention());

// Identity DB (separate Postgres instance)
var identityConn = builder.Configuration.GetConnectionString("IdentityPostgres");
builder.Services.AddDbContext<IdentityServerDbContext>(o =>
    o.UseNpgsql(identityConn));
```

**Nokteh:** `UseSnakeCaseNamingConvention()` lazem-e chun module-ha ba `EFCore.NamingConventions` neveshtand — age Reporting nabashe, column name-ha match nemikonan va query-ha fail mishan.

**Do ta connection string:** `DejbanPostgres` (module-ha) va `IdentityPostgres` (auth). `ApplicationDbContext` (Reporting-e khodesh) ro ba `Postgres` connection mizane — un baraye save kardan-e report definition-ha-ye.

---

## ReportRegistryDefaults — naghshe-ye context ↔ schema

```csharp
internal static class ReportRegistryDefaults
{
    private static readonly Dictionary<string, Type> DbContextMap = new()
    {
        ["ArmoryDbContext"]         = typeof(ArmoryDbContext),
        ["PersonnelsDbContext"]     = typeof(PersonnelsDbContext),
        ["CashLogisticsDbContext"]  = typeof(CashLogisticsDbContext),
        ["SecurityPatrolsDbContext"]= typeof(SecurityPatrolsDbContext),
        ["VehiclesDbContext"]       = typeof(VehiclesDbContext),
        ["VisitorsDbContext"]       = typeof(VisitorsDbContext),
        ["WeighBridgeDbContext"]    = typeof(WeighBridgeDbContext),
        ["InventoryDbContext"]      = typeof(InventoryDbContext),
    };
```

In dictionary mostaghim esm-e DbContext ro be Type-esh map mikone. Ba'd `BuildModules` az in estefade mikone:

```csharp
private static Dictionary<int, ModuleInfo> CreateDefaultModules() => new()
{
    { 1, new ModuleInfo { Name = "Armorys",         DbContextType = typeof(ArmoryDbContext),         SchemaName = Schemas.Armory } },
    { 2, new ModuleInfo { Name = "Personnels",      DbContextType = typeof(PersonnelsDbContext),     SchemaName = Schemas.Personnels } },
    { 3, new ModuleInfo { Name = "CashLogistics",   DbContextType = typeof(CashLogisticsDbContext),  SchemaName = Schemas.CashLogistics } },
    { 4, new ModuleInfo { Name = "SecurityPatrols", DbContextType = typeof(SecurityPatrolsDbContext), SchemaName = Schemas.SecurityPatrols } },
    { 5, new ModuleInfo { Name = "Vehicles",        DbContextType = typeof(VehiclesDbContext),       SchemaName = Schemas.Vehicles } },
    { 6, new ModuleInfo { Name = "Visitors",        DbContextType = typeof(VisitorsDbContext),       SchemaName = Schemas.Visitors } },
    { 7, new ModuleInfo { Name = "WeighBridge",     DbContextType = typeof(WeighBridgeDbContext),    SchemaName = Schemas.WeighBridge } },
    { 8, new ModuleInfo { Name = "Inventory",       DbContextType = typeof(InventoryDbContext),      SchemaName = Schemas.Inventory } },
};
```

**8 module, 8 schema, 8 DbContext.** Har module ye `ModuleInfo` dare ke `DbContextType` + `SchemaName` ro negah midare. Stimulsoft vaghti report-e ye entity ro mikhad render kone, az in registry miporse "in entity mal-e kodum module-e?" → az un module DbContext query mizane.

**Entity registry** ham hast:

```csharp
private static Dictionary<int, EntityRegistryItem> CreateDefaultEntities() => new()
{
    { 1, new EntityRegistryItem { ClrEntityName = "Personnel",  DataUrl = "/api/v1/Personnels/GetPersonnels", ModuleId = 2, Parameters = ["fromDate","toDate","searchTerm"] } },
    { 3, new EntityRegistryItem { ClrEntityName = "Vehicle",    DataUrl = "/api/v1/Vehicles/getVehicles",     ModuleId = 5, Parameters = ["fromDate","toDate","searchTerm"] } },
    { 4, new EntityRegistryItem { ClrEntityName = "Visitor",    DataUrl = "/api/v1/Visitors/GetVisitors",     ModuleId = 6, Parameters = ["fromDate","toDate","searchTerm"] } },
    { 5, new EntityRegistryItem { ClrEntityName = "Weapon",     DataUrl = "/api/v1/Weapons",                  ModuleId = 1, Parameters = ["fromDate","toDate","searchTerm"] } },
    // ... more entities
};
```

Do ta rah-e data gereftan: **mostaghim az DB** (via DbContext + schema) ya **az tarigh-e API** (DataUrl ke az gateway mire be module-e asli). Age `DataUrl` set bashe, Reporting ye HTTP call be gateway mizane va JSON migire; vagarna mostaghim query mizane.

---

## ReportRegistryOptions — configurable az appsettings

```csharp
builder.Services.Configure<ReportRegistryOptions>(
    builder.Configuration.GetSection(ReportRegistryOptions.SectionName));
```

`BuildModules` va `BuildEntities` avval default-ha ro load mikonan, ba'd `appsettings.json` override-ha ro apply mikonan. In yani bazi config-ha mishe bedun-e deploy avaz beshe.

---

## IReportAccessTicketStore — interface

```csharp
public sealed record ReportAccessTicketPayload(string AccessToken, string? SiteId);

public interface IReportAccessTicketStore
{
    Task<string> CreateAsync(string accessToken, string? siteId, CancellationToken ct = default);
    Task<ReportAccessTicketPayload?> TryGetAsync(string ticketId, CancellationToken ct = default);
}
```

**Sade va tamiz.** `CreateAsync` ye ticket mint mikone, `TryGetAsync` ticket ro resolve mikone. Payload-esh `AccessToken` (JWT-e asl-e user) va `SiteId` (multi-tenant context) dare.

---

## ReportAccessTicketStore — piade-sazi ba Redis

```csharp
public sealed class ReportAccessTicketStore(IDistributedCache cache) : IReportAccessTicketStore
{
    public static readonly TimeSpan DefaultTtl = TimeSpan.FromMinutes(5);
    private const string KeyPrefix = "report-access-ticket:";

    public async Task<string> CreateAsync(string accessToken, string? siteId, CancellationToken ct)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(accessToken);

        var ticketId = Guid.NewGuid().ToString("N");  // 32 char hex
        var payload = new ReportAccessTicketPayload(accessToken, siteId);
        var json = JsonSerializer.Serialize(payload, JsonOptions);

        await cache.SetStringAsync(
            KeyPrefix + ticketId,
            json,
            new DistributedCacheEntryOptions
            {
                AbsoluteExpirationRelativeToNow = DefaultTtl  // 5 min
            },
            ct);

        return ticketId;
    }

    public async Task<ReportAccessTicketPayload?> TryGetAsync(string ticketId, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(ticketId)) return null;
        var json = await cache.GetStringAsync(KeyPrefix + ticketId, ct);
        if (string.IsNullOrWhiteSpace(json)) return null;
        return JsonSerializer.Deserialize<ReportAccessTicketPayload>(json, JsonOptions);
    }
}
```

**Key points:**
- `IDistributedCache` = Redis (Day 25) — hamun infra-ye cache-e
- `DefaultTtl = 5 min` — hard-coded vali static-e, public-e, testable-e
- `Guid.NewGuid().ToString("N")` = 32-char hex → unguessable enough (128-bit entropy)
- Ticket ro **delete nemikone** ba'd az masraf — to TTL yek ya chand bar ghabel-e estefade-s. Age mikhay single-use bashe, bayad ba'd az `TryGet` delete koni.

**Smell:** ticket reusable-e to TTL — ye attacker ke ticket ro capture kone, 5 daghighe vaght dare. Baraye security-e behtar, `TryGet` bayad **delete** ham kone (single-use). Vali Stimulsoft chand ta AJAX call mizane, pas single-use momkene kharab she.

---

## DesignController — mint kardan-e ticket

```csharp
[Authorize]
public class DesignController : Controller
{
    [HttpPost]
    public async Task<IActionResult> CreateAccessTicket(CancellationToken ct)
    {
        var authHeader = Request.Headers.Authorization.ToString();
        if (string.IsNullOrWhiteSpace(authHeader) ||
            !authHeader.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
            return Unauthorized();

        var accessToken = authHeader["Bearer ".Length..].Trim();
        var siteId = Request.Headers["X-Site-Id"].FirstOrDefault();

        var ticket = await _reportAccessTicketStore.CreateAsync(accessToken, siteId, ct);

        return Ok(new
        {
            ticket,
            expiresInSeconds = (int)ReportAccessTicketStore.DefaultTtl.TotalSeconds  // 300
        });
    }
}
```

**Flow:** FE authenticated-e → POST be CreateAccessTicket → JWT ro az header migire → ticket mint mikone → ticket + TTL ro be FE mide → FE `window.open` ba ticket mizane.

`expiresInSeconds` be FE mige "in ticket 300 sanie zende-s" — FE mitune UX-e "link expired" neshun bede.

---

## ViewReport — masraf kardan-e ticket

```csharp
public IActionResult ViewReport(
    Guid reportId, string? url, string? query,
    [FromQuery(Name = "access_token")] string? accessToken,
    [FromQuery(Name = "siteId")] string? siteId,
    [FromQuery] string? autoPrint)
{
    ApplyAccessTokenFallback(accessToken);
    ApplySiteIdFallback(siteId);
    // ...
}

private void ApplyAccessTokenFallback(string? accessToken)
{
    if (string.IsNullOrWhiteSpace(accessToken)) return;
    if (Request.Headers.ContainsKey("Authorization")) return;
    Request.Headers["Authorization"] = $"Bearer {accessToken}";
}
```

**Wait:** inja `access_token` mostaghim to query pass mishe? In hamun chizi-e ke goftim bad-e!

Dorost-e — in ye **fallback**-e baraye backward compatibility. Dar olgu-ye jadid, FE avval `CreateAccessTicket` seda mizane, ticket migire, ba'd FE mitune `AccessTokenQueryMiddleware` ro ba ticket seda bezane. Vali feli **har do path** support mishan — in ye smell-e ke bayad migrate beshe.

---

## AccessTokenQueryMiddleware — zanjire

```csharp
// Common/Authentication/AccessTokenQueryMiddleware.cs
// Age query-e access_token bud va header nabud → header ro set mikone
```

In middleware ghabl az `UseAuthentication` run mishe. Baraye SignalR ham estefade mishe (Day 26). Reporting ham az hamun middleware estefade mikone.

---

## Stimulsoft integration — Day 39 vs Day 64

| Day 39 | Day 64 |
|---|---|
| Stimulsoft **library** itself | **Architecture** around it |
| StiReport, StiNetCoreDesigner, data binding | Multi-DbContext, ticket store, registry |
| Render/export PDF/Excel | Security of report URLs |
| Font registration (Linux) | Read-model pattern |

In ruz Stimulsoft ro farz migiri ke dari — focus ru-ye **chetori data behesh miresi** va **chetori amn-esh mikoni**.

---

## Stimulsoft font registration (Linux)

```csharp
private static void RegisterStimulsoftFonts()
{
    string[] fontFiles = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        // ...
    ];
    foreach (var f in fontFiles)
        if (File.Exists(f))
            StiFontCollection.AddFontFile(f);
}
```

Linux container-ha Tahoma nadarand — bedun-e in, text-e report collapse mikone ya tohi mire. In ye bug-e DevOps-i-e ke debug-esh sakht-e (report to local khoob-e, to Docker kharab-e).

---

## Data fetching — do masir

```
Entity registry
├── DataUrl set?  YES → HTTP GET via Gateway (IReportApiClient)
│                       → uses JWT from ticket/header
│                       → returns JSON → Stimulsoft dataset
│
└── DataUrl null? → Direct DB query via DbContext
                    → ReportRepository resolves module → schema → DbContext
                    → EF query → DataTable → Stimulsoft dataset
```

**HTTP path:** baraye entity-hayi ke API-e asli complex filtering/projection dare (masalan Personnel ba aggregate-ha), mostaghim az gateway mikhune — in yani auth-e user (az ticket) check mishe va module-e asli access control ro enforce mikone.

**DB path:** baraye entity-haye sade ke flat table-an (Unit, Product), mostaghim az DB mikhune — in sari'-tar-e vali access control-e module ro bypass mikone (faghat Reporting-e Authorize check shode, na module).

**Smell:** DB path module-level access control ro bypass mikone. Age ye user dastresi be "Weapons" nadashte bashe vali Reporting Authorize-esh OK bashe, mitune weapon data ro to report bebine.

---

## Referer recovery — Stimulsoft quirk

```csharp
// Stimulsoft AJAX often drops page query params
moduleId = ResolvePositiveInt(moduleId, "moduleId");
url = FirstNonEmpty(url, GetRefererValue("url"), GetQueryValue("url"));
```

Stimulsoft Designer vaghti AJAX call mizane, momkene query param-ha ro gom kone. DesignController az `Referer` header recover mikone — in ye **defensive pattern** baraye third-party library-hayi ke URL handling-eshun unreliable-e.

---

## Pipeline — middleware chain

```
Request → AccessTokenQueryMiddleware → TokenRevokeMiddleware
       → Authentication → Authorization → TenantContext
       → DesignController
```

**Tartib mohem-e:**
1. `AccessTokenQueryMiddleware` — query/ticket → header
2. `TokenRevokeMiddleware` — blacklisted JWT check (Day 06)
3. `UseAuthentication` → JWT validate
4. `UseAuthorization` → `[Authorize]` check
5. `UseTenantContext` → `X-Site-Id` → TenantContext (Day 16)

---

## Smell-ha

1. **JWT-in-URL fallback** hanuz exist dare — bayad migrate beshe be ticket-only
2. **Ticket reusable to TTL** — na single-use; window-e attack bozorg-tar-e
3. **DB path bypass-e module access control** — Reporting `[Authorize]` check mikone vali module-level permission na
4. **`Clients.All` nist vali `All modules`** — Reporting hame-ye schema-ha ro dare, ye misconfiguration mitune leak bede
5. **No audit trail** baraye ticket usage — kasi nemifahme ki che vaght az ticket estefade kard
6. **Font fallback** — age DejaVu ya Liberation nabashe, report silent break mikone (text tohi)
7. **Mega-registration** — 9 ta DbContext to ye service; age module-e jadid ezafe she, Reporting ham bayad update she
8. **ReportRegistryDefaults hardcoded** — age schema name avaz beshe, bayad code deploy koni

---

## Debug checklist

1. Report render tohi-e? → Font registration check kon (Docker container)
2. 401 vaghti report baz mishe? → Ticket expired? AccessToken middleware run shode?
3. Data tohi-e? → DbContext schema match mikone? Snake case convention?
4. Entity na peydas? → ReportRegistryDefaults in entity ro dare? ModuleId dorost-e?
5. AJAX-e Stimulsoft fail mikone? → `GetRefererValue` ro check kon; double `?` to URL?
6. Tenant data ghaati shode? → `X-Site-Id` az ticket resolve mishe? `ApplySiteIdFallback` seda zade?
7. Report save nemishe? → `ApplicationDbContext` connection dorost-e? (Reporting-e khodesh)
8. Redis connection fail? → Ticket create/get mishe? Cache connection string?

---

## 25 soal-e mosahebe

1. Read model chie? — **A:** query-only projection az data-ye write-side, bedun-e write capability.
2. CQRS-lite chetori farghe ba CQRS-e kamel? — **A:** hamun DB mikhunad ba joda context, na event-sourced ya joda store.
3. Chera multi DbContext to ye service? — **A:** har module schema-ye khodesh dare; ye context per schema = isolation + no coupling.
4. Capability ticket chie? — **A:** opaque short-lived token ke server mint mikone ba'd az authZ, be jaye JWT to URL.
5. Chera JWT to URL bad-e? — **A:** leak az log, referrer, history, proxy.
6. TTL-e ticket chand-e va chera? — **A:** 5 min; kafi baraye render, kam baraye attack window.
7. Ticket single-use-e? — **A:** na, reusable to TTL; smell-e ke bayad fix she.
8. Stimulsoft chikar mikone? — **A:** report engine; Day 39 detail dare; Day 64 architecture-e dor-esh-e.
9. ReportRegistryDefaults chikar mikone? — **A:** map-e module ↔ DbContext ↔ schema.
10. Fargh-e HTTP path va DB path baraye data? — **A:** HTTP az gateway ba user auth; DB mostaghim ba Reporting auth.
11. Smell-e DB path chie? — **A:** module-level access control bypass mishe.
12. Referer recovery chie? — **A:** Stimulsoft AJAX query param gom mikone; az Referer header recover mikonim.
13. Font registration chera lazem-e? — **A:** Linux container-ha Windows font nadarand; Stimulsoft bedun-e font text collapse mikone.
14. `UseSnakeCaseNamingConvention` chera lazem-e? — **A:** module-ha ba snake_case neveshtand; bedun-esh column match nemikone.
15. IdentityServerDbContext chera joda-e? — **A:** Identity ye Postgres-e dge dare; connection string-esh farghe.
16. Consistency lag-e in approach chie? — **A:** near-zero chun hamun DB-e; age read replica bud ms-scale lag.
17. Alternative-e capability ticket chie? — **A:** signed URL, cookie auth, session — har kodum tradeoff dare.
18. `IDistributedCache` chi estefade mishe? — **A:** Redis (Day 25); hamun infra.
19. `EntityRegistryItem.Parameters` chie? — **A:** query param-hayi ke Stimulsoft mitune pass kone (fromDate, toDate, searchTerm).
20. Mega-DbContext chera bad-e? — **A:** tight coupling; migration conflict; hame-ye entity-ha to ye assembly.
21. Age module-e jadid ezafe she chi bayad bokoni? — **A:** DbContext register kon to Program.cs + entry to ReportRegistryDefaults.
22. Fargh-e `ApplicationDbContext` va module context-ha? — **A:** ApplicationDbContext mal-e Reporting-e khodesh-e (saved reports); module-ha faghat read.
23. Audit trail-e ticket chetori piade mishe? — **A:** feli nadare; bayad TryGet log kone + ticket metadata save kone.
24. Token revoke impact ru-ye ticket? — **A:** JWT-e dakhel-e ticket revoke beshe, `TokenRevokeMiddleware` reject mikone.
25. YARP chetori Reporting ro route mikone? — **A:** catch-all path be reporting cluster; Day 07 detail dare.

---

## Senario-ha

### A) Operator report-e personnel ro design mikone
Login → FE authenticated → Click "Design" → FE `POST CreateAccessTicket` → ticket migire → `window.open(/Design/GetReport?moduleId=2&entityId=1&ticket=abc)` → Server `TryGet(abc)` → JWT recover → `SetAuthorizationHeader` → Stimulsoft designer load mishe → data az API path (Personnel has DataUrl) → report render mishe.

### B) Operator saved report ro view mikone
FE `POST CreateAccessTicket` → ticket → `window.open(/Design/ViewReport?reportId=xxx&ticket=abc)` → Server ticket resolve → report az `ApplicationDbContext` load mishe (saved definition) → data az entity path → render.

### C) Ticket expire shode
5 daghighe gozashte → user link ro refresh mikone → `TryGet` return null → `ApplyAccessTokenFallback` null → no Authorization header → `[Authorize]` reject → 401.

### D) Module-e jadid (Calendar) ezafe mishe
1. `CalendarDbContext` register kon to Program.cs
2. Entry to `DbContextMap` va `CreateDefaultModules` ezafe kon
3. Entity-ha to `CreateDefaultEntities` ezafe kon
4. Deploy → Reporting mitune calendar data ro report kone

### E) Schema name eshtebah-e
`ReportRegistryDefaults` mige `Schemas.Personnels` vali DB schema `personnel` (bedun-e s). EF query fail mikone ba "relation not found" — debug: check `ResolveDefaultSchema` va compare ba actual DB schema name.

---

## Jadval-e moghayese — approach-haye reporting

| approach | consistency | coupling | complexity | Dejban |
|---|---|---|---|---|
| Multi-DbContext read | near-zero lag | medium (schema dep) | low | ✅ in use |
| Shared DB views | near-zero | tight (SQL dep) | medium | ❌ |
| Data warehouse + ETL | minutes/hours lag | low | high | ❌ |
| CDC → read store | seconds lag | low | high | ❌ |
| API-only (no DB) | zero lag | lowest | medium | partial |

---

## Anti-pattern-ha

```csharp
// BAD: ye mega DbContext ba hame-ye entity-ha
public class EverythingDbContext : DbContext {
    public DbSet<Personnel> Personnels { get; set; }
    public DbSet<Vehicle> Vehicles { get; set; }
    // 50 more entities...
}

// GOOD: har module ye read context
builder.Services.AddDbContext<PersonnelsDbContext>(...);
builder.Services.AddDbContext<VehiclesDbContext>(...);
```

```csharp
// BAD: JWT mostaghim to URL
window.open($"/report?access_token={jwt}");

// GOOD: avval ticket begir, ba'd ticket to URL
const { ticket } = await api.post('/Design/CreateAccessTicket');
window.open(`/report?ticket=${ticket}`);
```

```csharp
// BAD: Reporting entity write mikone
await personnelsDb.SaveChangesAsync(); // to Reporting service!

// GOOD: Reporting faghat read mikone; write faghat az module-e asli
```

---

## Interview 60s

> «Our Reporting microservice registers multiple EF Core DbContexts pointing to the same Postgres instance — one per module schema (Personnels, Vehicles, Armory, etc.) — as a pragmatic CQRS-lite read model. When the user opens a report in Stimulsoft, we don't put the JWT in the URL; instead, we mint a short-lived capability ticket via Redis (5-minute TTL) and pass that opaque string. The server redeems the ticket to recover the original access token and site context.»

---

## Resume

**kutah:**

> Architected a **CQRS-lite reporting read model** with multiple EF Core DbContexts spanning module schemas, secured report URLs with **Redis-backed capability tickets** (5-min TTL) instead of JWT-in-URL, and integrated Stimulsoft data binding via both API and direct-DB paths.

**bullet-ha:**

- Registered 8+ read-only EF DbContexts per module schema in a single Reporting service for cross-domain data access
- Implemented `IReportAccessTicketStore` with Redis-backed opaque tickets (5-min TTL) to eliminate JWT leakage in report URLs
- Built `ReportRegistryDefaults` mapping module ↔ schema ↔ entity with API and DB data paths
- Resolved Stimulsoft AJAX parameter loss via Referer header recovery in DesignController

**skill-ha:** `CQRS · read model · multi-DbContext · EF Core · capability token · Redis · Stimulsoft · report security · ASP.NET Core`

---

## File-haye mohem

| chi | koja |
|---|---|
| Program.cs (9 DbContext) | `Reporting/Program.cs` |
| ReportRegistryDefaults | `Reporting/Infrastructure/ReportRegistryDefaults.cs` |
| IReportAccessTicketStore | `Common/Reporting/IReportAccessTicketStore.cs` |
| ReportAccessTicketStore | `Common/Reporting/ReportAccessTicketStore.cs` |
| DesignController | `Reporting/Controllers/DesignController.cs` |
| AccessTokenQueryMiddleware | `Common/Authentication/AccessTokenQueryMiddleware.cs` |
| ServiceCollectionExtensions | `Reporting/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| ReportRepository | `Reporting/Infrastructure/ReportRepository.cs` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 04/05 EF + DI | multi-DbContext registration pattern |
| 06/07 JWT + YARP | token in URL, gateway routing |
| 16 Tenancy | X-Site-Id propagation via ticket |
| 25 Redis | IDistributedCache for ticket store |
| 39 Stimulsoft | Report engine itself |
| 18 DI | AddDbContext lifetime (scoped) |

---

## Glossary

| kalame | ma'ni |
|---|---|
| Read model | projection-e read-only az data |
| CQRS | Command Query Responsibility Segregation |
| CQRS-lite | joda-sazi-e read/write bedun-e event sourcing |
| Capability ticket | opaque short-lived token baraye access be resource |
| TTL | Time To Live — omr-e ticket ya cache entry |
| DbContext | EF Core unit-of-work + repository |
| Schema | Postgres namespace baraye table-ha |
| Opaque token | token-i ke client nemitune decode kone |
| Stimulsoft | third-party report engine |
| IDistributedCache | abstraction baraye Redis/Memcached |
| Snake case | naming_convention ke EF column name-ha ro map mikone |
| Referer | HTTP header ke URL-e ghabli ro dare |

---

## Deep dive — multi-tenancy to Reporting

`ApplySiteIdFallback` az ticket ya query `X-Site-Id` ro recover mikone va to request header set mikone. `UseTenantContext` middleware in header ro mikhune va `TenantContext` ro fill mikone. Ba'd vaghti module DbContext-ha query mikonan, age tenant filter-e global query filter darand (Day 16), data-ye tenant-e dorost return mishe. Vali age module-e asli global filter nadare ya Reporting az DB path mostaghim mikhune, tenant isolation bypass mishe — **in ye risk-e**.

---

## Deep dive — ReportApiClient va Gateway

Baraye entity-hayi ke `DataUrl` darand, `ReportApiClient` ye HTTP GET be gateway mizane. In client az `IHttpClientFactory` estefade mikone ba named client `"Gateway"`. JWT-e user (az ticket ya header) be gateway pass mishe — gateway be module route mikone — module access control enforce mikone. In masir **amn-tar**-e az DB path chun module-e asli authorization ro check mikone.

---

## Deep dive — MassTransit to Reporting

Reporting MassTransit ham dare — vali na baraye data sync. `GetReportingServiceEndpointsConsumer` ye consumer-e ke be service discovery javab mide. Outbox ham dare baraye reliability. Vali data-ye report az MassTransit nemiad — mostaghim az DB ya API miad.

---

## Self-test-e sari

1. Chand ta DbContext Reporting dare? → 9+ (8 module + 1 ApplicationDbContext + Identity)
2. DefaultTtl chand-e? → 5 daghighe
3. Ticket to koja save mishe? → Redis (IDistributedCache)
4. Chera snake_case convention lazem-e? → Module-ha ba un neveshtan; bedun-esh column mismatch
5. Fargh-e DB path va API path? → DB mostaghim, API az gateway ba user auth
6. Capability ticket single-use-e? → Na, reusable to TTL (smell)
7. Font registration chera? → Linux container Windows font nadare
8. ReportRegistryDefaults configurable-e? → Baleh, az appsettings override mishe
9. JWT leak az koja? → Log, Referer, history, proxy
10. Reporting write mikone? → Na, faghat read (+ save report definitions to own DB)

Age 8/10 ya bishtar dorost bud → beri sar-e Day 65.

---

## Extra — signed URL vs capability ticket

Signed URL (masalan AWS S3 presigned) ye URL-e ke signature-e cryptographic dare — server bedun-e store mitune validate kone. Capability ticket ye opaque ID-e ke server to store donbalesh migarde. Fargh-eshun: signed URL stateless-e (amn-tar baraye CDN), capability ticket stateful-e (sade-tar baraye implement, vali Redis dependency dare). Dejban az capability ticket estefade mikone chun Stimulsoft URL handling-esh unpredictable-e va signed URL momkene corrupt beshe.

---

## Extra — why not a data warehouse

Ye data warehouse (Snowflake, BigQuery) baraye reporting ideal-e — vali overhead-e ETL pipeline, schema sync, va infra cost dare. Dejban ye on-prem system-e ke database size-esh manageable-e (na petabyte). Multi-DbContext approach latency-e near-zero dare va complexity-e operational-e kami dare. Vaghti scale bozorg-tar beshe, ye warehouse or materialized view arzesh-e barresi dare.

---

## Extra — testing strategy

- **Unit test:** `ReportRegistryDefaults.BuildModules` ba custom `ReportRegistryOptions` — check kon ke override-ha dorost apply mishan
- **Unit test:** `ReportAccessTicketStore` ba mock `IDistributedCache` — check kon TTL set mishe, TryGet null baraye expired
- **Integration test:** `DesignController.CreateAccessTicket` ba `WebApplicationFactory` — check kon 200 + ticket returned
- **Contract test:** entity registry `DataUrl`-ha bayad ba actual module API-ha match konan — in ye cross-service contract-e

---

## Extra — production incident pattern

**Bug:** Report to dev khoob-e, to Docker tohi-e.
**Root cause:** Font nasbod → Stimulsoft text ro ba zero-width render kard → PDF tohi be nazar miad.
**Fix:** Dockerfile-e Reporting: `RUN apt-get install -y fonts-dejavu fonts-liberation`.
**Lesson:** Age report-e visuali dari, hamishe font availability ro to CI/CD check kon.

---

## Checklist-e nahaei

- [ ] Multi-DbContext pattern va chera
- [ ] ReportRegistryDefaults module ↔ schema mapping
- [ ] Capability ticket lifecycle (create → store → redeem)
- [ ] Security: JWT-in-URL vs ticket
- [ ] DB path vs API path tradeoff
- [ ] Stimulsoft Referer recovery
- [ ] Font registration baraye Linux
- [ ] Smell-ha (reusable ticket, DB bypass, mega-registration)
- [ ] Resume bullets + interview 60s

---

## Resume keywords (ATS)

`CQRS` · `read model` · `multi-DbContext` · `EF Core` · `capability token` · `Redis` · `Stimulsoft` · `report security` · `ASP.NET Core` · `PostgreSQL` · `multi-schema` · `short-lived token` · `distributed cache`

---

## Chejori digest koni

1. CQRS-lite concept + farghe ba full CQRS (10 daghighe)
2. Multi-DbContext to Program.cs + ReportRegistryDefaults (15 daghighe)
3. Capability ticket flow: create → store → redeem (15 daghighe)
4. Security tradeoff: JWT-in-URL vs ticket (10 daghighe)
5. Smell-ha + debug checklist (10 daghighe)
6. 25 soal (20 daghighe)

---

*Day 64 tamum. Ba'di: Day 65 — Next.js basePath + rewrites. Fehrest: [README.md](./README.md).*
