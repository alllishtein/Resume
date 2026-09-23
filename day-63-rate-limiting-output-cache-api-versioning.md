# Day 63 — Rate Limiting + Output Cache + API Versioning

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Se ta feature-ye ASP.NET ke to **ApiGateway**-e Dejban kenar-e ham kar mikonan: **rate limiting** (sliding window per IP — auth 6/30s + global 500/min), **output caching** (20s response cache baraye GET-ha), va **API versioning** (Asp.Versioning ba URL segment `/api/v{version}/...`). In se ta to pipeline-ye YARP reverse proxy neshast-an va be tartib-e khass ejra mishan: `UseRateLimiter()` → authentication → authorization → `UseOutputCache()` → `MapReverseProxy()`. Har kodum ye labye-e protection ya optimization-e ke frontend na dide va backend kam dide — vali gateway hamaro kentar-e. In ruz se ta topic-e mokhtalef-e ke chon hameye to ye file va ye pipeline-an, ba ham yad migiri.

---

# BAKHSH-E AVAL: WORLD — rate limiting

## Farz kon

Farz kon ye darvaze dari ke bala-yesh neveshte "har nafar har 30 sanie faghat 6 bar mitune bezane". Age ziad-tar bezane, bayad montazer bemune. In rate limiting-e — jelo-ye abuse, brute-force, va DDoS ro migire. Bejaye inke hame-ye request-ha ro pass bedi va server overload beshe, ye had-e moshakhkhas bezar va ba'd azash 429 bede.

## Yani chi — rate limiting algorithms

Chand ta algorithm baraye rate limiting vojud dare. Har kodum ye model-e fardi dare baraye inke chejuri request-ha ro count mikone va limit enforce mikone:

| algorithm | chetori kar mikone | pros | cons |
|---|---|---|---|
| **Fixed window** | counter har N sanie reset mishe | sade-tarin implementation | burst-e double to marze window (edge spike) |
| **Sliding window** | panjereh-ye motemavel ba N segment; jam-e segment-ha > limit → reject | smooth-tar; spike-e fixed ro nadare | bishtare memory (per segment counter) |
| **Token bucket** | token-ha ba rate-e saabet tolid mishan; har request ye token masraf mikone | burst-e controlled — token-haye jam-shode ejaze midan | pichideh-tar baraye tune |
| **Concurrency** | had-e tedad-e request-haye **hamzaman** (dar yek lahze) | resource protection (DB pool, file lock) | rate ro control nemikone; faghat depth |

**Dejban:** sliding window ro baraye har do policy entekhab karde — ham baraye auth (6 request / 30 sanie) ham baraye global (500 request / 1 daghighe).

## Sliding window — deep dive

Farz kon window 30 sanie-ye va `SegmentsPerWindow = 6` (har segment 5 sanie). Vaghti request miad, ASP.NET counter-e segment-e fe'li ro check mikone va **jam-e hame-ye 6 segment** ro hesab mikone. Age jam ≥ `PermitLimit` (masalan 6), request reject mishe ba 429.

```
Time:   |--5s--|--5s--|--5s--|--5s--|--5s--|--5s--|
Seg:      1      2      3      4      5      6
Reqs:     1      2      0      1      1      1   = 6  → next request → 429
```

Chera in behtar az fixed window-e? Fixed window counter-esh sar-e marze window reset mishe — yani momkene 6 request to 1 sanie-ye akhar-e window-e ghabli va 6 ta to 1 sanie-ye avval-e window-e jadid biad = 12 to 2 sanie! Sliding in spike ro smooth mikone chon window hamisheh motemavel-e.

Vali `SegmentsPerWindow = 1` (ke Dejban baraye global policy set karde) ma'nasho in-e ke effectively **ye fixed window** dari! Chon faghat 1 segment dari, sliding hich kari nemikone. In ye trade-off-e: simplicity + kam memory baraye global policy ke limit-esh bala-tar-e (500/min) va precision-esh kam-ahamiyat-tar-e.

## Partition key — IP

Rate limit bayad **per-client** bashe. Key-e partition bayad ye chiz bashe ke client ro moshakhkhas kone — ma'mulan IP. Vali Dejban poshte YARP/Nginx-e, pas IP-ye vaghei to `X-Forwarded-For` header-e, na `RemoteIpAddress` ke hamishe IP-e proxy-e:

```csharp
var clientIp = httpContext.Request.Headers["X-Forwarded-For"]
    .FirstOrDefault()?.Split(',')[0].Trim()
    ?? httpContext.Connection.RemoteIpAddress?.ToString()
    ?? "unknown";
```

**`Split(',')[0]`** — X-Forwarded-For momkene chain bashe: `client, proxy1, proxy2` — avvali IP-e vaghei-e client-e. Vali in trust-based-e: age attacker khodesh ye fake X-Forwarded-For header bozare chi? Bayad trusted proxy list dashte bashi (`ForwardedHeaders` middleware ba `KnownProxies`). Dejban in layer-e extra ro farz mikone ke Nginx/YARP dorost set mikonan.

**Fallback `"unknown"`** — age hich IP-i peida nashe (rare — masalan Unix socket connection), hame-ye request-haye unknown share-e ye limiter mishan ke momkene accidentally restrict kone. In ye known trade-off-e.

## 429 Too Many Requests — protocol

Vaghti rate limit zarbe mikhore, server **429** bargardune (na 403 — ke authorization-e, na 500 — ke server error-e). Va `Retry-After` header bozare ke client bedune **key** dobare emtehan kone. In RFC 6585 standard-e.

Dejban-e code:

```csharp
options.OnRejected = (context, _) =>
{
    if (context.Lease.TryGetMetadata(MetadataName.RetryAfter, out var retryAfter))
    {
        context.HttpContext.Response.Headers.RetryAfter =
            ((int)retryAfter.TotalSeconds).ToString(NumberFormatInfo.InvariantInfo);
    }

    string currentLanguage = context.HttpContext.Request.Headers
        .AcceptLanguage.ToString();
    string errorMessage = currentLanguage
        .Equals("en-US", StringComparison.OrdinalIgnoreCase)
        ? "Too many requests. Please try again later"
        : "تعداد درخواست‌ها بیش از حد مجاز است. لطفاً بعدا تلاش کنید";

    context.HttpContext.Response.StatusCode =
        StatusCodes.Status429TooManyRequests;
    context.HttpContext.Response.WriteAsJsonAsync(new { Title = errorMessage });

    return new ValueTask();
};
```

**Nokte-ha:**

1. `TryGetMetadata(MetadataName.RetryAfter, ...)` — sliding window metadata ro mide; age nade (masalan concurrency limiter), header set nemishe
2. **Bilingual error:** az `Accept-Language` header entekhab mikone — Farsi ya English. Vali default Farsi-e — yani age client header set nakone (ke aksar browser-ha set nemikonan), Farsi migire. In baraye Dejban ke Iranian product-e monasebe, vali baraye public API khub nist
3. `WriteAsJsonAsync(new { Title = errorMessage })` — JSON response, na plain text. FE mitune parse kone va toast neshun bede

## Chera do ta policy — Auth va Global?

Dejban **do labye** protection dare:

1. **Auth_RateLimiter_PerIp** → 6 request / 30 sanie — sakht — baraye endpoint-haye hassas ke anonymous hastan va brute-force target mishan
2. **GlobalLimiter** → 500 request / 1 daghighe — lax-tar — baraye hame-ye request-ha (authenticated + anonymous)

Auth policy **joda** va **explicit** be route-ha attach mishe to YARP config (appsettings.json). Global limiter **implicit** — hame-ye request-ha azash rad mishan.

## Kodum route-ha Auth policy daran?

Az YARP appsettings.json:

```json
"auth-login-route-v1": {
    "ClusterId": "identity-server-cluster",
    "AuthorizationPolicy": "anonymous",
    "RateLimiterPolicy": "Auth_RateLimiter_PerIp",
    "Match": { "Path": "/Api/v{apiVersion}/Auth/Login/{**catch-all}" }
},
"auth-refresh-route-v1": {
    "RateLimiterPolicy": "Auth_RateLimiter_PerIp",
    "Match": { "Path": "/Api/v{apiVersion}/Auth/Refresh/{**catch-all}" }
},
"auth-cameraauth-route-v1": {
    "RateLimiterPolicy": "Auth_RateLimiter_PerIp",
    "Match": { "Path": "/Api/v{apiVersion}/Auth/CameraAuth/{**catch-all}" }
},
"ticket-public-create": {
    "RateLimiterPolicy": "Auth_RateLimiter_PerIp",
    "Match": { "Path": "/Api/v{apiVersion}/Tickets/CreatePublicTicket" }
}
```

Yani: Login, Refresh, CameraAuth, va public ticket endpoint-ha — hame anonymous hastan va target-e brute-force/spam. Ba'ghi-ye endpoint-ha authenticated hastan va GlobalLimiter kafie.

---

# BAKHSH-E DOVOM: WORLD — output caching

## Farz kon

Ye soal ke javab-esh avaz nemishe — masalan list-e shahrestan-ha ya enum-ha. Har bar ke FE form load mikone, in API seda mizane. 100 user dar 20 sanie = 100 query be DB baraye hamin data. Output cache mige: "avvalin response ro negah midar, 19.99 sanie ba'di az cache bargardun."

## Yani chi — technical

Output cache ye **HTTP response cache to middleware**-e. Farghe-sh ba application-level cache (masalan HybridCache) in-e ke **kol-e HTTP response** ro cache mikone — status code + headers + body — na faghat data. Vaghti request biad va cache hit bashe, hich code-i ejra nemishe — response mostaghim az middleware miad.

## Jadval-e moghayese — Output Cache vs HybridCache (Day 25)

| | Output Cache | HybridCache |
|---|---|---|
| **Chi cache mishe?** | HTTP response kamel (status + headers + body) | data/object to application code |
| **Koja run mishe?** | middleware — ghabl az endpoint code | to handler/service — ba'd az endpoint match |
| **Key** | URL + query + VaryBy headers (auto) | custom key (masalan `$"staff:{id}"`) |
| **Invalidation** | time-based ya tag-based via `IOutputCacheStore` | tag-based, explicit `RemoveAsync` |
| **Granularity** | per-endpoint/route | per-data-piece |
| **Use case** | GET-haye public/shared ke response yeki-e | data-haye per-user ya computed values |
| **Dejban** | gateway → `Default_CachePolicy` 20s | har service → `ICacheService` wrapper |
| **Concurrent miss** | faghat ye request be backend mire, badi-ha montazer | stampede mitune pish biad (bedun-e lock) |

**Kholasat:** output cache baraye "macro" optimization-e — kol-e response ro baraye hame share mikone. HybridCache baraye "micro" optimization-e — data-ye khass ro per-key cache mikone. Dejban az **har do** estefade mikone.

## Khatare output cache — data leak

Age ye GET endpoint response-ye **per-user** bargardune (masalan dashboard-e shakhsi), va output cache biaad response ro cache kone bedun-e `VaryByHeader("Authorization")`, user A response-ye user B ro migire. In **security bug**-e.

**Fix:** ya `VaryBy` header ezafe kon, ya in endpoint ro az cache exclude kon. Dejban `Default_CachePolicy` ro be route-haye khass attach mikone (az YARP config), na be hame-ye GET-ha — pas in risk manage shode.

---

# BAKHSH-E SEVOM: WORLD — API versioning

## Farz kon

Ye API dari ke mobile app, web app, va third-party client-ha azash estefade mikonan. Mikhay field-e `FullName` ro split koni be `FirstName` va `LastName` to response. Bedun-e versioning: hame-ye client-ha break mishan. Ba versioning: v1 hamchenan `FullName` dare, v2 jadid `FirstName` + `LastName`.

## Strategy-haye versioning — WORLD

| strategy | mesal | pros | cons |
|---|---|---|---|
| **URL segment** | `/api/v1/staff` | vazehi, cache-friendly, bookmark-able | URL avaz mishe — CDN/proxy bayad update beshe |
| **Query string** | `/api/staff?api-version=1.0` | backward compatible (default version) | kam-vazehi; google index moshkel |
| **Header** | `X-Api-Version: 1.0` | URL tamiz mimune | developer kamtar midune; debug sakht-tar |
| **Media type** | `Accept: application/vnd.api.v1+json` | most RESTful | pichideh; tooling support zayif |

**Dejban:** URL segment — `/api/v{version:apiVersion}/...`. In vazehi-tarin-e baraye team: to URL mibini kodum version-e. Cache-friendly-e chon URL farghe. Va Scalar/OpenAPI per-version document misaze.

## Asp.Versioning — package

Ghabl az .NET 7, API versioning az `Microsoft.AspNetCore.Mvc.Versioning` bud. Ba'd az .NET 7, **Asp.Versioning** package joda shod va community-maintained shod. Dejban az `Asp.Versioning.Http` estefade mikone baraye Minimal APIs.

```xml
<PackageReference Include="Asp.Versioning.Http" Version="..." />
```

Key classes:
- `ApiVersion` — version object (major, minor)
- `ApiVersionSet` — group-e version-haye ye endpoint
- `IApiVersionDescriptionProvider` — list-e hame-ye version-ha (baraye OpenAPI)

---

# BAKHSH-E CHAHAROM: DEJBAN — code-e vaghei

## AddCustomRateLimiters — line by line

```csharp
public static IServiceCollection AddCustomRateLimiters(
    this IServiceCollection services)
{
    services.AddRateLimiter(options =>
    {
        // Policy 1: Auth — sakht — 6 request / 30s / per IP
        options.AddPolicy("Auth_RateLimiter_PerIp", httpContext =>
        {
            var clientIp = httpContext.Request.Headers["X-Forwarded-For"]
                .FirstOrDefault()?.Split(',')[0].Trim()
                ?? httpContext.Connection.RemoteIpAddress?.ToString()
                ?? "unknown";

            return RateLimitPartition.GetSlidingWindowLimiter(clientIp,
                _ => new SlidingWindowRateLimiterOptions
                {
                    PermitLimit = 6,
                    Window = TimeSpan.FromSeconds(30),
                    SegmentsPerWindow = 6,   // 6 segment × 5s = 30s
                    QueueLimit = 0           // no queueing — reject fori
                });
        });

        // Policy 2: Global — hame-ye request-ha — 500/min / per IP
        options.GlobalLimiter = PartitionedRateLimiter
            .Create<HttpContext, string>(httpContext =>
        {
            var clientIp = httpContext.Request.Headers["X-Forwarded-For"]
                .FirstOrDefault()?.Split(',')[0].Trim()
                ?? httpContext.Connection.RemoteIpAddress?.ToString()
                ?? "unknown";

            return RateLimitPartition.GetSlidingWindowLimiter(clientIp,
                _ => new SlidingWindowRateLimiterOptions
                {
                    PermitLimit = 500,
                    Window = TimeSpan.FromMinutes(1),
                    SegmentsPerWindow = 1,   // effectively fixed window
                    QueueLimit = 0
                });
        });

        // OnRejected — 429 + Retry-After + bilingual
        options.OnRejected = (context, _) =>
        {
            if (context.Lease.TryGetMetadata(
                    MetadataName.RetryAfter, out var retryAfter))
            {
                context.HttpContext.Response.Headers.RetryAfter =
                    ((int)retryAfter.TotalSeconds)
                    .ToString(NumberFormatInfo.InvariantInfo);
            }

            string currentLanguage = context.HttpContext.Request
                .Headers.AcceptLanguage.ToString();
            string errorMessage = currentLanguage
                .Equals("en-US", StringComparison.OrdinalIgnoreCase)
                ? "Too many requests. Please try again later"
                : "تعداد درخواست‌ها بیش از حد مجاز است. لطفاً بعدا تلاش کنید";

            context.HttpContext.Response.StatusCode =
                StatusCodes.Status429TooManyRequests;
            context.HttpContext.Response.WriteAsJsonAsync(
                new { Title = errorMessage });

            return new ValueTask();
        };
    });

    return services;
}
```

In code-e vaghei-e to `ServiceCollectionExtensions.cs` — API Gateway-e Dejban. Nokte-haye mohem:

- **Do ta IP resolution-e copy-paste** — ham to Auth policy ham to Global. In duplicate code-e ke DRY nabude. Mitunest ye helper method bashe. Vali chon lambda-ye majza-ye-i to `AddPolicy` va `Create` hastan, refactor-esh ye kam awkward-e.
- **`NumberFormatInfo.InvariantInfo`** — ta "." bejaye "," to adad bashe (farsi locale)
- **`ValueTask`** — chon synchronous-e va allocation nadare

## AddCustomCachePolicies

```csharp
public static IServiceCollection AddCustomCachePolicies(
    this IServiceCollection services)
{
    services.AddOutputCache(options =>
    {
        options.AddPolicy("Default_CachePolicy",
            builder => builder.Expire(TimeSpan.FromSeconds(20)));
    });
    return services;
}
```

Sade: ye policy ba 20s TTL. Hich VaryBy nadare — yani response baraye hame yeki-e (ke baraye shared data doroste). Hich tag ham nadare — yani manual invalidation nadarim; faghat wait baraye expire.

## Pipeline order — Program.cs kamel

```csharp
// Registration
builder.Services.AddCustomRateLimiters()
    .AddCustomCachePolicies();

// Pipeline
app.UseRateLimiter();                                    // 1
app.UseMiddleware<AccessTokenQueryMiddleware>();          // 2
app.UseTokenRevoke();                                    // 3
app.UseAuthentication();                                 // 4
app.UseAuthorization();                                  // 5
app.UseOutputCache();                                    // 6
app.MapReverseProxy();                                   // 7
```

**Chera in tartib?**

| # | middleware | chera inja? |
|---|---|---|
| 1 | RateLimiter | **avvalin check** — age reject beshe, hich resource-i masraf nashe |
| 2 | AccessTokenQuery | token az query string be Authorization header (baraye SignalR negotiate) |
| 3 | TokenRevoke | age token blacklisted bashe → 401 zud |
| 4 | Authentication | JWT validate |
| 5 | Authorization | permission check |
| 6 | OutputCache | age response cache dare, YARP call nashe → latency ~0ms |
| 7 | ReverseProxy | YARP request ro be backend forward mikone |

**Critical rule:** RateLimiter **ghabl** az Auth — ta unauthenticated request-ha ham limit bekhoran. OutputCache **ba'd** az Auth — ta cached response permission-checked bashe (ya VaryBy bashe).

**Link Day 07 YARP:** `MapReverseProxy()` hamun pipeline-e ke request-ha ro be IdentityServer, ACLServer, Dejban, DCC, RequestTracker, Reporting, GateServer forward mikone.

## Versioning — endpoint pattern-e vaghei

Az `VisitorDocuments.cs` — ye typical Dejban endpoint:

```csharp
internal sealed class VisitorDocuments : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var versionSet = app.NewApiVersionSet()
            .HasApiVersion(new ApiVersion(1, 0))
            .ReportApiVersions()
            .Build();

        app.MapPost("/api/v{version:apiVersion}/Visitors/{visitorId:guid}/Documents",
            async (Guid visitorId, [FromForm] UploadVisitorDocumentCommand request,
                   IFormFile? file, ISender sender) =>
            {
                request.VisitorId = visitorId;
                if (file is not null) request.File = file;
                var result = await sender.Send(request);
                return result.Match(Results.Ok, ApiResults.Problem);
            })
            .RequireAuthorization()
            .WithApiVersionSet(versionSet)
            .WithTags(Tags.Visitors)
            .WithMetadata(new EndpointDescriptionAttribute("ارباب رجوع | آپلود سند"))
            .DisableAntiforgery()
            .MapToApiVersion(new ApiVersion(1, 0));
    }
}
```

**Pattern:**

1. `NewApiVersionSet()` → ye version group misaze
2. `HasApiVersion(1, 0)` → in endpoint v1 support mikone
3. `v{version:apiVersion}` to route → URL-based versioning
4. `.WithApiVersionSet(versionSet)` → version set attach mishe
5. `.MapToApiVersion(1, 0)` → in handler baraye v1-e (age v2 ham bud, handler-e jadid ba `MapToApiVersion(2, 0)`)
6. `.ReportApiVersions()` → response header: `api-supported-versions: 1.0`

**Hame-ye** Dejban endpoint-ha in pattern ro daran — 100+ endpoint dar 10+ module.

## EndpointSyncService — version expansion

EndpointSyncService (Day 62) endpoint-ha ro collect mikone baraye permission system. Vaghti route pattern `{version:apiVersion}` dare, bayad expand beshe be version-haye vaghei:

```csharp
private ServiceEndpointDTO CollectLocalEndpoints(string serviceName)
{
    var endpoints = endpointDataSources
        .SelectMany(es => es.Endpoints)
        .OfType<RouteEndpoint>();

    var results = new List<EndpointDTO>();

    foreach (var e in endpoints)
    {
        var rawPattern = e.RoutePattern.RawText ?? string.Empty;
        var description = e.Metadata.OfType<EndpointDescriptionAttribute>()
            .FirstOrDefault()?.Description ?? string.Empty;
        var methods = e.Metadata.OfType<HttpMethodMetadata>()
            .FirstOrDefault()?.HttpMethods ?? [];

        if (rawPattern.StartsWith("/openapi", StringComparison.OrdinalIgnoreCase))
            continue;

        if (rawPattern.Contains("{version:apiVersion}"))
        {
            foreach (var version in versionProvider.ApiVersionDescriptions)
            {
                var expanded = rawPattern.Replace(
                    "v{version:apiVersion}",
                    $"v{version.ApiVersion.MajorVersion}");
                foreach (var method in methods)
                    results.Add(new EndpointDTO(
                        $"{method}:{expanded}", description));
            }
        }
        else { /* non-versioned endpoint — add as-is */ }
    }
    return new ServiceEndpointDTO(serviceName, results);
}
```

Yani `/api/v{version:apiVersion}/Visitors/{visitorId}/Documents` tabdil mishe be `POST:/api/v1/Visitors/{visitorId}/Documents` to permission system. In bridge-e bein-e versioning va RBAC.

---

## Smell-ha va risk-ha

| # | smell | tozih | fix |
|---|---|---|---|
| 1 | **`"unknown"` IP** | age proxy X-Forwarded-For set nakone, hame share limiter | ForwardedHeaders middleware ba KnownProxies |
| 2 | **Output cache + auth response** | per-user data leak age VaryBy nadashte bashe | VaryByHeader ya exclude az cache |
| 3 | **SegmentsPerWindow = 1** | global limiter effectively fixed window-e | afzayesh segment age precision lazeme |
| 4 | **Auth policy unnamed attach** | faramush koni be route attach koni → global apply mishe (lax) | naming convention + test |
| 5 | **Bilingual default Farsi** | client bedun-e Accept-Language → Farsi error | detect culture ya default English |
| 6 | **No distributed rate limit** | multi-instance gateway → har instance joda count | Redis-backed limiter |
| 7 | **DRY violation** | IP resolution 2 bar copy-paste shode | extract helper method |
| 8 | **Output cache nadare tag** | manual invalidation momken nist — faghat time expire | tag ezafe kon + `EvictByTagAsync` |

---

## Debug checklist

| # | moshkel | check kon |
|---|---|---|
| 1 | 429 migiri unexpectedly? | X-Forwarded-For header ro check kon — momkene shared IP bashe |
| 2 | 429 nemigirim vali bayad begiram? | policy name dorost attach shode? YARP route config `"RateLimiterPolicy"` spelling? |
| 3 | Cached response stale-e? | 20s gozashte? `Default_CachePolicy` attach shode? |
| 4 | Version not supported? | URL `/api/v2/...` vali endpoint faghat v1 dare → "unsupported API version" |
| 5 | Retry-After header nist? | concurrency limiter metadata nade — faghat sliding/fixed mide |
| 6 | Pipeline order eshtebah? | UseRateLimiter ghabl az UseOutputCache bashe |
| 7 | Rate limit to test kar nemikone? | development mode exception dari? `AllowAnonymous` rate limit ro bypass nemikone |
| 8 | Output cache kar nemikone? | faghat **GET** va response 200 cache mishe; POST cache nemishe |

---

## 25 soal-e mosahebe (ba javab-e kutah)

1. **Rate limiting chie?** → Had-e tedad-e request to ye bazeh-ye zamani.
2. **Sliding window vs fixed?** → Sliding smooth-tar; fixed spike to marze window.
3. **Token bucket chie?** → Token tolid rate saabet; burst ba token-haye jam-shode.
4. **429 yani chi?** → HTTP Too Many Requests.
5. **Retry-After header?** → Be client mige chand sanie montazer bemune.
6. **Partition key?** → Field-i ke rate limit per-X mishe (IP/user/key).
7. **X-Forwarded-For chera?** → IP-e vaghei poshte reverse proxy.
8. **QueueLimit=0?** → Hich request-i queue nashe; fori reject.
9. **Chera Auth policy sakht-tar?** → Login brute-force prevention.
10. **Chera Global 500/min?** → DDoS/abuse protection baraye kol-e API.
11. **Output cache chie?** → HTTP response kamel cache mishe to middleware.
12. **vs HybridCache?** → Output: response; Hybrid: data to code.
13. **20s expire chera?** → Trade-off: freshness vs load reduction.
14. **VaryBy chie?** → Cache key-e joda per header/query/user.
15. **Khatare cache-e auth response?** → Data leak — user A mibine user B ro.
16. **API versioning chera?** → Backward compatibility vaghti API avaz mishe.
17. **URL vs header versioning?** → URL vazehi/cacheable; header tamiz-tar.
18. **Asp.Versioning?** → NuGet package baraye API versioning to ASP.NET.
19. **ReportApiVersions?** → Response header: supported/deprecated versions.
20. **MapToApiVersion?** → In endpoint baraye in version respond mikone.
21. **Pipeline order chera mohem?** → RateLimiter avval, OutputCache ba'd az Auth.
22. **YARP inja chikare?** → Gateway ke se ta middleware rush neshast-an.
23. **Distributed rate limit?** → Redis-backed limiter baraye multi-instance.
24. **SegmentsPerWindow?** → Tedad-e subdivision-e window to sliding.
25. **Concurrency limiter?** → Had-e request-haye hamzaman, na rate.

---

## Senario-ha

### A) Brute-force login

Attacker 10 bar dar 5 sanie `/api/v1/auth/login` POST mikone ba password-haye random. Auth policy: 6/30s. Ba'd az request-e 6om, request-e 7om 429 migire ba `Retry-After: 25` (25 sanie munde ta window slide kone). Attacker bayad 25s montazer bemune ya IP avaz kone. Vaghti ba rate limit ham sari amadan, account lockout (Day 06) layer-e dovom-e.

### B) Shared Wi-Fi problem

Yek office ba 50 nafar — hame az ye public IP mian. Global limiter: 500/min. 50 user * 10 req/min = 500 req/min. Nazdik-e be limit! Age ye nafar ziad request bezane, badi-ha 429 migiran. **Fix:** partition by user ID (az JWT) bejaye IP baraye authenticated request-ha. Dejban faqat IP estefade mikone — in ye known limitation-e.

### C) Cached GET — performance win

FE har bar form load mikone `/api/v1/Regions/GetAll` call mikone. Request-e avval: gateway → YARP → backend → DB query → response (50ms). Cache mishe. Request-e 2om ta 20om (dar 20s): gateway → output cache → response (0.5ms). Backend **asl seda zade nashe**. 100x speed up baraye in endpoint.

### D) Stale cache after write

Admin ye shahrestan ezafe mikone (POST). 10 sanie ba'd user form ro load mikone → GET response az cache → shahrestan-e jadid nist. 10 sanie dge → cache expire → fresh response → shahrestan miad. **Trade-off:** 20s max staleness baraye load reduction. Baraye data-ye critical, output cache nabayad estefade beshe — HybridCache ba explicit invalidation behtar-e.

### E) API version migration

Team mikhad `GET /api/v1/Staff` response ro avaz kone. v2 misazan ba response-e jadid. Mobile app-e ghadimi ke update nashe hanuz v1 call mikone va kar mikone. App-e jadid v2 call mikone. Vaghti v1 deprecated beshe, `api-deprecated-versions: 1.0` header miad va client warning mibine.

---

## Deep dive — rate limiter internals-e ASP.NET

`AddRateLimiter` az `System.Threading.RateLimiting` package estefade mikone. Class hierarchy:

```
RateLimiter (abstract)
├── SlidingWindowRateLimiter
├── FixedWindowRateLimiter
├── TokenBucketRateLimiter
└── ConcurrencyLimiter
```

Vaghti request miad:
1. `RateLimiterMiddleware` az DI, `PartitionedRateLimiter` ro migire
2. `AttemptAcquire` ya `AcquireAsync` seda mizane
3. `RateLimitLease` bargasht mide — `IsAcquired` = true ya false
4. Age true → `next()` call mishe → request pass
5. Age false → `OnRejected` callback → 429

**Memory model:** har partition (IP) ye `SlidingWindowRateLimiter` instance dare ke to `ConcurrentDictionary` negah dashte mishe. `Dispose` mishe vaghti expire beshe va request-e jadid nayad.

## Deep dive — output cache va YARP interaction

Output cache to gateway ye layer-e **bala-tar** az YARP-e. Vaghti cache hit:

```
Request → RateLimiter ✓ → Auth ✓ → OutputCache HIT → Response (YARP skip)
```

Vaghti cache miss:

```
Request → RateLimiter ✓ → Auth ✓ → OutputCache MISS → YARP → Backend → Response → Cache store
```

**YARP khodesh cache nadare.** YARP ye transport-e — request ro forward mikone. Cache az ASP.NET output cache middleware-e.

## Deep dive — distributed rate limiting

ASP.NET built-in rate limiter **in-process**-e. Agar gateway horizontal scale beshe (2+ instance), har instance joda count mikone:

```
Instance A: 400 req/min → OK (< 500)
Instance B: 400 req/min → OK (< 500)
Total actual: 800 req/min — 60% bishtar az intended limit!
```

**Rah-e hal-ha:**

1. **Redis-backed limiter** — ye counter-e shared to Redis. Package-haye third-party masalan `RedisRateLimiting` in ro piade mikonan
2. **Sticky sessions** — load balancer hame-ye request-haye ye IP ro be ye instance befresfe. Vali failover moshkel dare
3. **Accept the overshoot** — limit ro proportion taqsim kon (500/N instances)

Dejban alan single-instance gateway dare pas in moshkel pish nayumade. Vali scale-up plan bayad distributed limiter dashte bashe.

## Deep dive — output cache tag-based invalidation

Dejban `Default_CachePolicy` faghat time-based-e. Vali ASP.NET output cache tag-based invalidation ham dare:

```csharp
options.AddPolicy("RegionList", builder =>
    builder.Expire(TimeSpan.FromSeconds(60))
           .Tag("regions"));

// Ba'd az write:
await outputCacheStore.EvictByTagAsync("regions", ct);
```

In baraye scenario-ye "admin data avaz kard → cache fori invalid beshe" ideal-e. Dejban az in estefade nakarde — vali ye improvement-e ke mitune ezafe beshe baraye data-ye ke kamtar avaz mishe vali vaghti avaz mishe, bayad fori reflect beshe.

## Deep dive — fargh-e gateway rate limit va per-service rate limit

| | Gateway rate limit | Per-service rate limit |
|---|---|---|
| **Koja?** | ApiGateway | Har service joda |
| **IP** | X-Forwarded-For (vaghei) | gateway IP (hame yeki!) |
| **Scope** | cross-service (kol-e traffic) | per-service |
| **Dejban** | ✓ har do policy | ✗ service-ha rate limit nadaran |

**Defense in depth:** ideally ham gateway ham service-ha bayad rate limit dashte bashan. Gateway overall protection mide, service per-endpoint granular limit. Dejban faqat gateway layer dare.

---

## Extra — rate limiting va WebSocket (SignalR)

Rate limiter faghat ru-ye **HTTP request-ha** kar mikone. SignalR lifecycle:

1. **Negotiate** → HTTP POST → rate limit apply mishe ✓
2. **WebSocket upgrade** → HTTP → rate limit ✓
3. **WS messages** → not HTTP → rate limit ✗

Yani: connection setup limit mikhore, vali message-haye dakhel-e WS beneshan rate limit nemishan. Baraye message-level limiting, to hub code bayad logic bezari (masalan throttle per-client message rate).

## Extra — Retry-After do format

`Retry-After` header az RFC 7231:

1. **Seconds:** `Retry-After: 30` — 30 sanie montazer bemun
2. **HTTP-date:** `Retry-After: Wed, 22 Sep 2026 20:30:00 GMT`

Dejban az seconds format estefade mikone. Client-e khoob (Axios interceptor to React) in header ro mikhune va ba `setTimeout` retry mikone. Client-e bad ignore mikone va dobare 429 migire.

## Extra — concurrency limiter alternative

Age mikhay limit koni ke **faghat N ta request hamzaman** process beshe (na rate — tedad dar zaman):

```csharp
RateLimitPartition.GetConcurrencyLimiter(key,
    _ => new ConcurrencyLimiterOptions
    {
        PermitLimit = 10,
        QueueLimit = 5   // 5 ta queue mishan, ba'd reject
    });
```

Use case: ye endpoint ke query-e sangin be DB mizane — mikhay max 10 concurrent query dashte bashi ta DB overload nashe. Dejban estefade nakarde vali concept mohem-e.

## Extra — versioning deprecation flow

```csharp
var versionSet = app.NewApiVersionSet()
    .HasApiVersion(new ApiVersion(2, 0))               // current
    .HasDeprecatedApiVersion(new ApiVersion(1, 0))      // deprecated
    .ReportApiVersions()
    .Build();
```

Response header: `api-supported-versions: 2.0` va `api-deprecated-versions: 1.0`. FE mitune warning neshun bede: "Please update to v2". In sunset pattern-e ke gradual migration ro facilitate mikone.

## Extra — output cache baraye POST?

Default: output cache **faghat GET va HEAD** ro cache mikone. POST, PUT, DELETE cache nemishan chon side-effect daran (RFC 7234). Age mikhay POST response cache beshe (rare), bayad explicit `CacheOutput` attribute bezari. Dejban in karo nakarde — faghat GET cache mishe.

## Extra — monitoring rate limit to production

Baraye inke beduni chand request 429 khord-an:

```csharp
options.OnRejected = (context, _) =>
{
    logger.LogWarning("Rate limit hit — IP: {IP}, Path: {Path}",
        clientIp, context.HttpContext.Request.Path);
    // ... rest of rejection logic
};
```

Va ya az ASP.NET metrics:

```
dotnet-counters monitor --counters Microsoft.AspNetCore.RateLimiting
```

Dejban alan `OnRejected` log nadare — ye improvement-e ke bayad ezafe beshe baraye observability.

## Extra — chera SegmentsPerWindow mohem-e

`SegmentsPerWindow` mostagiman accuracy-e sliding window ro ta'yin mikone. Farz kon window 30s bashe:

| segments | har segment | accuracy | memory |
|---|---|---|---|
| 1 | 30s | = fixed window (bad) | minimal |
| 3 | 10s | medium | 3 counters |
| 6 | 5s | high (Dejban Auth) | 6 counters |
| 30 | 1s | very high | 30 counters |

Dejban baraye Auth policy `SegmentsPerWindow = 6` (5s resolution) estefade karde — khoob-e. Baraye Global `SegmentsPerWindow = 1` — chon limit 500/min kheili bala-tar-e va spike-e edge to fixed window qabel-e tahammol-e.

**Rule of thumb:** segment count ro bala bebar vaghti limit paine va precision mohem-e (masalan auth). Payin negah dar vaghti limit bala-ye va memory-e zamani mohem-tare.

## Extra — CORS va rate limit interaction

To pipeline-ye Dejban, `UseCors()` **ghabl** az `UseRateLimiter()`-e (dar khat-e 60 va 109 Program.cs). In yani:

1. CORS preflight (OPTIONS request) **rate limit nakhore** → chon browser automatic OPTIONS mizane va reject-esh bad UX dare
2. Vali actual request (POST/GET) rate limit mikhore ✓

Age CORS ba'd az rate limiter bud, OPTIONS ham 429 mikhord va browser-e user error midad bedun-e inke request-e vaghei ro befresfe. Pipeline order inja critical-e.

## Extra — rate limit va health check endpoint

Dejban ye `/health/reporting-routes` endpoint dare ke `AllowAnonymous`-e. Age in endpoint rate limit bekhore, monitoring system false alarm mide. GlobalLimiter in endpoint ro ham check mikone — vali chon health check kam call mishe (har 30s az load balancer), ba 500/min limit problem nemishe. Vali best practice in-e ke health endpoint-ha ro az rate limit exclude koni:

```csharp
options.AddPolicy("NoLimit", _ =>
    RateLimitPartition.GetNoLimiter("health"));

app.MapGet("/health", handler).RequireRateLimiting("NoLimit");
```

## Extra — output cache va ETag/conditional GET

Output cache mitune ba `ETag` ham kar kone:

```csharp
options.AddPolicy("WithETag", builder =>
    builder.Expire(TimeSpan.FromSeconds(60))
           .SetVaryByHeader("If-None-Match"));
```

Client `If-None-Match` header ba ETag-e ghabli mifresfe → age data avaz nashode → 304 Not Modified (bejaye kol-e response). In baraye bandwidth save mohem-e. Dejban in ro piade nakarde — faghat simple time-based expire.

## Extra — versioning va Swagger/Scalar separation

Dejban to gateway har service ye Scalar document joda dare:

```csharp
options.AddDocument("v1", "IdentityServer",
    routePattern: "/identityserverscalar/openapi/{documentName}.json");
options.AddDocument("v1", "Dejban",
    routePattern: "/dejbanscalar/openapi/{documentName}.json");
```

Har document `v1` tag khorde — age v2 ezafe beshe, document-e jadid ham bayad ezafe beshe. In integration-e bein-e versioning va API documentation.

## Extra — Nginx rate limit vs ASP.NET rate limit

Dejban poshte Nginx ham hast. Nginx khodesh ham rate limit dare (`limit_req_zone`). Fargh:

| | Nginx rate limit | ASP.NET rate limit |
|---|---|---|
| Layer | L7 proxy (ghabl az app) | application middleware |
| Config | nginx.conf static | C# code dynamic |
| Response | 503 default | 429 + custom body |
| Partition | $binary_remote_addr | any logic (IP, user, ...) |
| Dejban | ✗ (Nginx rate limit off) | ✓ (gateway) |

Dejban faqat az ASP.NET rate limit estefade mikone — chon bilingual error va custom Retry-After lazem dasht ke Nginx be rahat-i nemide. Vali dual-layer (Nginx + ASP.NET) defense in depth-e.

## Extra — chera output cache to gateway va na to service?

Mitunest har service khodesh `UseOutputCache()` dashte bashe. Vali gateway behtar-e chon:

1. **Single point:** hame-ye service-ha az ye cache policy benefit mibarand
2. **YARP skip:** vaghti cache hit bashe, request asl be service nemire — network round-trip save mishe
3. **Consistent:** developer-ha to service lazem nist cache fikr konan — gateway handle mikone

Downside: gateway cache granularity kam-tare (per-route, na per-endpoint logic). Baraye fine-grained caching, HybridCache to service behtar-e (Day 25).

## Deep dive — masir-e vaghei-e ye request dar pipeline

Farz kon FE call mikone: `GET /api/v1/Regions/GetAll`

```
1. Nginx → forward be ApiGateway (port 5000)
2. CORS middleware → Origin check ✓
3. UseRateLimiter() → Global: IP check → 47/500 → ✓
4. AccessTokenQuery → token az query? na → skip
5. TokenRevoke → token blacklisted? na → skip
6. UseAuthentication → JWT validate ✓
7. UseAuthorization → permission check ✓
8. UseOutputCache → cache key = "GET:/api/v1/Regions/GetAll"
   → HIT? → return cached response (0.5ms)
   → MISS? → continue
9. MapReverseProxy → YARP → Dejban service → DB query → response (50ms)
   → response cache mishe baraye 20s
```

**Cache hit path:** step 1-8 = ~2ms. **Cache miss path:** step 1-9 = ~55ms. In 25x speed up-e baraye cached endpoint-ha.

## Deep dive — rate limit va load testing

Vaghti ba k6 ya JMeter load test mikoni, rate limit-e gateway jelo ro migire! Bayad ya rate limit ro vaghti test mikoni disable koni, ya limit ro bala bebari, ya az bypass header estefade koni:

```csharp
options.AddPolicy("Auth_RateLimiter_PerIp", httpContext =>
{
    if (httpContext.Request.Headers.ContainsKey("X-LoadTest-Bypass"))
        return RateLimitPartition.GetNoLimiter("bypass");
    // ... normal logic
});
```

**Vali:** in bypass faghat to development/staging bashe — production NEVER. Dejban in bypass ro nadare — load test ba limit-e bala anjam mishe.

## Masir-e yek version expansion — zincir-e kamel

Vaghti IdentityServer start mishe:

1. `EndpointSyncService.SyncAsync()` call mishe
2. `CollectLocalEndpoints("IdentityServer")` → scan-e hame-ye `RouteEndpoint`-ha
3. Endpoint ba pattern `/api/v{version:apiVersion}/Auth/Login` peida mishe
4. `versionProvider.ApiVersionDescriptions` → `[ApiVersion(1,0)]`
5. Pattern expand mishe: `POST:/api/v1/Auth/Login`
6. In string to permission system save mishe
7. Admin to panel-e role management in endpoint ro mibine va permission assign mikone

In bridge-e bein-e **routing** va **authorization** — versioning to URL nabud, in chain kaar nemikard.

## Deep dive — output cache memory management

Output cache by default **in-memory**-e. Har cached response memory masraf mikone. Age 1000 endpoint dari va har response 10KB bashe, 10MB cache memory-e. In baraye gateway OK-e vali age response-ha bozorg bashan (masalan list-e 5000 nafar ba photo), memory explode mikone.

ASP.NET mitune **size limit** baraye output cache set kone:

```csharp
options.AddPolicy("SizedCache", builder =>
    builder.Expire(TimeSpan.FromSeconds(30))
           .SetResponseBodyMaxSize(1024 * 100)); // max 100KB
```

Dejban in limit ro set nakarde — vali chon faghat shared GET-haye sabuk cache mishan (regions, enums, config-ha), problem nist.

**Alternative:** Redis-backed output cache (`IOutputCacheStore` implementation ba Redis). Baraye multi-instance gateway va ya response-haye bozorg behtar-e. Microsoft ye built-in Redis provider nadare — vali community package-ha hastan.

## Deep dive — API versioning va minimal API vs controller

Dejban az **Minimal API** (`.MapPost`, `.MapGet`) estefade mikone ba `IEndpoint` pattern. Versioning to minimal API ba'd az .NET 7 asan shod. Ghablan ba controller-ha bud:

```csharp
// Controller-based (ghadimi):
[ApiVersion("1.0")]
[Route("api/v{version:apiVersion}/[controller]")]
public class StaffController : ControllerBase { }

// Minimal API (Dejban):
app.MapPost("/api/v{version:apiVersion}/Staff/Create", handler)
    .WithApiVersionSet(versionSet)
    .MapToApiVersion(new ApiVersion(1, 0));
```

Minimal API ro Dejban entekhab karde chon: kam boilerplate-tar-e, testable-tar-e, va ba `IEndpoint` interface pattern match mikone (har endpoint ye file). Versioning to har do approach yeki kar mikone — faqat syntax farghe.

## Deep dive — chera 20 sanie va na 60 ya 5?

20 sanie ye trade-off-e:
- **5s**: kheili taze vali cache hit rate paine — faghat request-haye kheili sari benefit mibarand
- **20s**: balance-e khub — 20 sanie staleness baraye reference data (regions, categories) qabel-e qabul-e
- **60s**: cache hit rate bala vali age data avaz beshe, 1 daghighe miri ta reflect beshe — bad baraye data-ye active

Dejban 20s entekhab karde chon aksar-e cached endpoint-ha reference data-ye (ke kamtar avaz mishe). Baraye data-ye ke sari avaz mishe, output cache estefade nemishe — HybridCache ba explicit invalidation behtar-e.

## Extra — rate limit testing ba curl

```bash
# 7 request dar 5 sanie be login endpoint:
for i in $(seq 1 7); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST https://gateway/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
done

# Expected output:
# 200 (ya 401)
# 200
# 200
# 200
# 200
# 200
# 429  ← request-e 7om reject shod
```

`Retry-After` header to response-e 429 mige chand sanie montazer beshi. Ba `-v` flag mituni header ro bebini.

## Extra — output cache response header

Vaghti output cache hit mishe, response ye `Age` header dare ke mige chand sanie az cache-e:

```
HTTP/1.1 200 OK
Age: 12
Cache-Control: public, max-age=20
```

`Age: 12` yani in response 12 sanie pishe ke cache shode. 8 sanie dge expire mishe. FE mitune in header ro bekhune ta bedune data chand sanie kohn-e.

## Extra — rate limit va microservice-to-microservice call

Rate limit-e Dejban faghat **external** request-ha ro migire (az browser/client be gateway). **Internal** call-haye bein-e service-ha (az MassTransit ya gRPC) az gateway rad nemishan — pas rate limit nemikhoran.

In design-e dorost-e: internal call-ha trust-shode hastan va limit-eshun mantegh nadare. Vali age ye service buggy bashe va ye service-e dge ro spam kone? Baraye in bayad per-service circuit breaker (Polly) ya MassTransit rate limit dashte bashi — na gateway rate limit.

## Mini lab — hands-on tamrin

1. **`ServiceCollectionExtensions.cs`** ro bekhun — do ta policy + OnRejected
2. **`Program.cs`** pipeline order ro trace kon — az `UseRateLimiter` ta `MapReverseProxy`
3. **`appsettings.json`** YARP routes ro search kon baraye `RateLimiterPolicy` — kodum route-ha Auth daran?
4. Ye `IEndpoint` file to Dejban Presentation bebin — `versionSet` pattern
5. `EndpointSyncService.CollectLocalEndpoints` ro bebin — version expansion logic
6. Ba curl 7 bar login endpoint ro bezan — 429 bebin
7. Ye GET endpoint ro 2 bar sari call kon — dovvomi response time ~0ms bashe (cache hit)
8. Response header-e `api-supported-versions` ro check kon to versioned endpoint

## Extra — chera Dejban bilingual error dare va na error code?

Aksar-e API-ha error **code** bargardunand (masalan `RATE_LIMITED`) va FE khodesh translate mikone. Dejban mostaghim **human-readable message** to response mizare (Farsi ya English). In approach sade-tar-e baraye team-e kuchik — vali scale nemikone:

| | Message-based (Dejban) | Code-based (standard) |
|---|---|---|
| FE kaar | fori neshun bede | code → dictionary lookup → neshun bede |
| Zaban ezafe | backend avaz beshe | FE dictionary ezafe beshe |
| Consistency | backend control mikone | FE control mikone |
| Third-party client | message-e hardcoded | code-e stable + client translate |

Baraye Dejban ke internal product-e va FE/BE ye team hastan, message-based OK-e. Baraye public API, code-based standard-tar-e.

## Extra — rate limit va CDN

Age CDN (masalan Cloudflare) jelo-ye gateway bozari, CDN khodesh rate limit dare ke **ghabl** az gateway apply mishe. In yani:

1. CDN DDoS layer-e avval — volumetric attack ro block mikone
2. Gateway rate limit layer-e dovom — application-level abuse ro migire
3. Per-service limit (age bud) layer-e sevom — granular protection

Dejban CDN nadare (internal product). Vali baraye public-facing API, CDN + gateway rate limit = defense in depth.

## Extra — in che chizi-e Day 63 *nist*

- In ruz darbare-ye **WAF** (Web Application Firewall) nist — WAF request content ro check mikone (SQL injection, XSS), rate limit faghat tedad ro
- In ruz darbare-ye **authentication/authorization** nist — un Day 06-e; inja faghat pipeline order-esh ro mibini
- In ruz darbare-ye **YARP routing logic** nist — un Day 07-e; inja faghat interaction-e middleware-ha ba YARP ro mibini
- In ruz darbare-ye **HybridCache implementation** nist — un Day 25-e; inja faghat moghayese-e output cache vs hybrid ro mibini
- In ruz darbare-ye **Polly resilience** nist — circuit breaker va retry policy topic-e jodast
- In ruz darbare-ye **gRPC rate limiting** nist — Dejban gRPC server (TiamGrpc) rate limit nadare chon internal-e

## Checklist-e nahaei

- [ ] Sliding window: Auth 6/30s (6 segments) + Global 500/min (1 segment)
- [ ] IP az X-Forwarded-For + RemoteIpAddress + "unknown" fallback
- [ ] OnRejected: 429 + Retry-After + bilingual (Accept-Language)
- [ ] QueueLimit = 0 baraye har do policy
- [ ] YARP routes: Login/Refresh/CameraAuth/PublicTicket → Auth policy
- [ ] Output cache: 20s Default_CachePolicy — no tags, no VaryBy
- [ ] vs HybridCache (Day 25): response vs data
- [ ] Asp.Versioning: URL segment `/api/v{version:apiVersion}/...`
- [ ] ReportApiVersions → header ba supported/deprecated
- [ ] EndpointSyncService version expansion baraye permission system
- [ ] Pipeline order: RateLimiter → Auth → OutputCache → Proxy

---

## Resume

**kutah:**

> Edge **sliding-window rate limiting** (auth 6/30s, global 500/min per IP with `X-Forwarded-For`) and **output caching** (20s) on the YARP API gateway; **Asp.Versioning** URL-segment versioning across 100+ Minimal API endpoints feeding the permission system.

**bullet-ha:**

- Implemented dual sliding-window rate limiters on API Gateway — strict per-IP for auth endpoints, global per-IP for all traffic — with bilingual 429 + Retry-After
- Added output caching policy with 20-second expiry for cacheable GET responses on the YARP pipeline
- Applied Asp.Versioning URL-segment pattern across 100+ Minimal API endpoints with version-aware endpoint sync into RBAC
- Configured gateway middleware pipeline order: rate limiter → auth → output cache → YARP proxy for optimal short-circuiting

**skill-ha:** `Rate Limiting` · `Sliding Window` · `Output Caching` · `API Versioning` · `Asp.Versioning` · `YARP` · `ASP.NET Core` · `Gateway Pattern` · `429` · `Retry-After`

---

## Interview 60s

> «The API gateway uses ASP.NET's built-in rate limiter with two sliding-window policies — a strict one for auth endpoints at 6 requests per 30 seconds per IP, and a global at 500 per minute. IP comes from X-Forwarded-For since YARP sits behind Nginx. On rejection we return 429 with Retry-After and a bilingual message based on Accept-Language. Output caching sits after auth in the pipeline with a 20-second default policy for GET responses — so cache hits skip the YARP proxy entirely. All services use Asp.Versioning with URL segments; the endpoint sync service expands version placeholders into concrete paths for the permission system.»

---

## File-haye mohem

| chi | koja |
|---|---|
| Rate limit + Output cache extension | `ApiGateway/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Pipeline order | `ApiGateway/Program.cs` |
| YARP route config + policy attach | `ApiGateway/appsettings.json` (RateLimiterPolicy) |
| Endpoint versioning pattern | Har `IEndpoint` to `Dejban.Modules.*.Presentation/` |
| Version expansion | `IdentityServer/.../EndpointSyncService.cs` → `CollectLocalEndpoints` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 07 YARP | Gateway pipeline ke in middleware-ha rush neshast-an |
| 06 JWT | Auth middleware ghabl az OutputCache |
| 25 HybridCache | Data cache (25) vs response cache (in ruz) |
| 62 R/R MassTransit | EndpointSyncService version expansion |
| 26 SignalR | WebSocket rate limit faghat negotiate ro migire |

---

## Glossary

| kalame | ma'ni |
|---|---|
| Rate limiting | had-e request per time unit |
| Sliding window | panjereh-ye motemavel ba segment-ha |
| Fixed window | counter ke sar-e bazeh reset mishe |
| Token bucket | token tolid rate-based; burst allowed |
| 429 | HTTP Too Many Requests |
| Retry-After | header: chand sanie montazer bemun |
| Partition key | key ke rate limit per-X mishe (IP/user) |
| Output cache | HTTP response cache to middleware |
| HybridCache | data/object cache — Day 25 |
| API versioning | support-e chand version-e API hamzaman |
| Asp.Versioning | NuGet package baraye versioning |
| ApiVersionSet | group-e version-haye ye endpoint |
| MapToApiVersion | endpoint be version-e khass map mishe |
| ReportApiVersions | header-e version info to response |
| YARP | reverse proxy middleware — Day 07 |
| QueueLimit | tedad request ke mitune queue beshe |
| OnRejected | callback vaghti rate limit hit mishe |
| VaryBy | output cache key differentiation |
| SegmentsPerWindow | tedad subdivision-e sliding window |

---

## Self-test-e sari

1. Auth limiter chand request dar chand sanie? → 6 / 30s
2. Global limiter? → 500 / 1 min per IP
3. IP az koja miad? → X-Forwarded-For → RemoteIpAddress → "unknown"
4. 429 ba kodum header miad? → Retry-After
5. Output cache chand sanie? → 20s
6. Output cache vs HybridCache? → Response vs data
7. Versioning strategy-e Dejban? → URL segment
8. Pipeline order? → RateLimiter → Auth → OutputCache → Proxy
9. QueueLimit=0 yani chi? → Fori reject; no queue
10. ReportApiVersions chikar mikone? → Header ba supported/deprecated versions

Age 8/10+ → Day 63 done. Beri sar-e Day 64.

---

## Resume keywords (ATS)

`Rate Limiting` · `Sliding Window` · `ASP.NET Core` · `Output Caching` · `HTTP 429` · `Retry-After` · `API Versioning` · `Asp.Versioning` · `YARP` · `API Gateway` · `.NET 9` · `Minimal API`

---

## Khoruj-e zehni

> In ruz ra vaghti digeri kardi ke betuni bedun-e negah kardan tozih bedi: do ta rate limit policy (Auth 6/30s sliding + Global 500/min), partition by IP az X-Forwarded-For, OnRejected ba 429 + Retry-After + bilingual message, output cache 20s ke YARP ro skip mikone, Asp.Versioning ba URL segment, va pipeline order-e gateway.

Age in paragraph mal-e to shod — Day 63 done.

**Nokte-ye akhar:** in se topic (rate limit + output cache + versioning) hamishe to interview **ba ham** mian chon hame to ye pipeline hastan. Vaghti az yeki harf mizani, interviewer montazer-e ke interaction-e ba do ta dge ro ham beduni — masalan "output cache ba'd az auth neshast chon cached response bayad authenticated bashe" ya "rate limiter avval-e chon resource save mikone". In systems thinking-e ke senior engineer ro az junior joda mikone.

---

*Day 63 tamum. Ba'di: Day 64 — Reporting read-model + capability tickets. Fehrest: [README.md](./README.md).*
