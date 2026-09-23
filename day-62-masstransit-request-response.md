# Day 62 — MassTransit Request/Response

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**MassTransit request/response** olgu-i-e ke ye service az tarigh-e broker (RabbitMQ) ye soal mifreste be service-e dge va **montazer-e javab mimune**. Bar khalaf-e `Publish` ke fire-and-forget-e, `IRequestClient<T>.GetResponse<R>()` ye temporary queue misaze, payam ro mifreste, va ta zamani ke javab biad ya timeout beshe block mikone. Dejban in ro baraye **cross-service query** estefade mikone: `RemoteClaimService` az IdentityServer claim-haye user ro miporse, `EndpointSyncService` az 6 ta service endpoint-hashun ro jam mikone, va consumer-haye uniqueness check az service-haye dge verify mikonan. In pattern "RPC over messaging"-e — coupling-e kamtar az HTTP dare chon URL/port lazem nist, vali risk-e hang/timeout dare ke bayad manage beshe.

---

# BAKHSH-E AVAL: WORLD — chera request/response over messaging

## Farz kon

Farz kon to ye sazeman do ta department dari. Ye rah ine ke az Department B telephone bezani (HTTP — mostaghim, sync, bayad number/address-eshun ro beduni). Ye rah-e dge ine ke ye nameh befrest va begi "javab ro baraye in shomare-ye mahal befrest" (request/response over broker — address-eshun ro niaz nadari, broker route mikone, vali montazer-e javab-i). Publish mesle poster zadan-e to lobby-e: hame mibinan, kesi javab nemide. Request/response mesle nameh ba envelope-e javab-e.

## Yani chi — mekanik-e IRequestClient

Vaghti `client.GetResponse<R>(message)` seda mizani, in etefagh-ha miofte:

```
1. MassTransit ye temporary reply queue misaze (ya az shared reply queue estefade mikone)
2. Message ro ba header-e "ReplyTo: temporary-queue" be exchange-e broker publish mikone
3. Consumer-e target message ro migire, process mikone, va ba context.RespondAsync(response) javab mide
4. Response be temporary queue miad
5. GetResponse return mikone ba Response<R>
```

**Fargh ba Publish:**

| | `Publish` | `GetResponse` |
|---|---|---|
| Direction | one-way (fire-and-forget) | two-way (request → response) |
| Blocking | na — return mide bedun-e montazer | are — await mikone ta javab biad |
| Reply queue | nadare | temporary ya shared queue |
| Timeout | nadare (message dar queue mimune) | explicit timeout — ba'd az un exception |
| Use case | event notification, command dispatch | cross-service query, validation |

---

## Chera az broker va na az HTTP?

| meghyas | Request/Response (broker) | HTTP (HttpClient) |
|---|---|---|
| Discovery | broker route mikone (exchange/queue name) | URL + port + DNS lazeme |
| Coupling | contract-e message — esm-e type | URL + version + path |
| Retry/resilience | broker khodesh queue dare; MassTransit retry/timeout dare | Polly ya HttpClient retry |
| Load balancing | competing consumers (chand instance) | load balancer lazeme |
| Monitoring | broker dashboard (RabbitMQ management) | distributed tracing |
| Complexity | medium — broker dependency | low (vali service mesh age scale koni) |
| Latency | bishtare (broker overhead + serialize) | kamtar (direct TCP) |

**Key Request/Response:**
- Service-ha az ham IP/port nemidunand (loosely coupled)
- Broker ghablan baraye Publish hast — reuse
- Load balance-e khodkar ba competing consumers

**Key HTTP:**
- Latency critical bashe
- External service ke broker nadare
- Simple setup bedun-e broker dependency

Dejban **har do** estefade mikone: HTTP baraye external call-ha, MassTransit R/R baraye internal cross-service query.

---

## Timeout — mohem-tarin risk

```csharp
var response = await client.GetResponse<UserSiteClaimsResponse>(
    new GetUserSiteClaims(userId),
    cancellationToken,
    timeout: TimeSpan.FromSeconds(5));
```

Age consumer down bashe ya kond bashe va to 5 sanie javab nade, `RequestTimeoutException` throw mishe. In **kheili mohem-e** — bedun-e explicit timeout, default-e MassTransit 30 sanie-ye va UI request hang mikone.

**Risk-haye timeout:**
1. Consumer down → message dar queue mimune → timeout ba'd az 30s → UX khraab
2. Consumer kond → javab dare miad vali dir → timeout → response-e consumer gom mishe (reply queue momkene expire shode bashe)
3. **Cascade hang:** Service A → R/R be Service B → R/R be Service C — age C kond bashe, B hang mikone, A ham hang mikone
4. **Thread starvation:** age ziad GetResponse await koni bedun-e proper timeout, ASP.NET thread pool por mishe

**Best practice:**
- Hamishe explicit timeout bezar (5-10s baraye interactive, 30s baraye background)
- Fallback ya cache dashte bash (mesle RemoteClaimService ke local cache dare)
- Circuit breaker pattern age service mokerraran fail mikone

---

## Request/Response internals — RabbitMQ

```
Producer                    RabbitMQ                    Consumer
   │                          │                          │
   │──Publish(msg)───────────▶│                          │
   │  Headers:                │──Deliver(msg)───────────▶│
   │   ReplyTo: temp-queue    │                          │
   │   MessageId: guid        │                          │  process...
   │                          │                          │
   │                          │◀──Respond(response)──────│
   │◀──Deliver(response)──────│  CorrelationId: guid     │
   │                          │                          │
```

- **ReplyTo:** address-e queue ke response bayad bere
- **MessageId/CorrelationId:** baraye match kardan-e response ba request-e asli
- **Temporary queue:** MassTransit ye exclusive, auto-delete queue misaze ke ba'd az response pak mishe (ya az shared bus reply queue estefade mikone ke efficient-tar-e)

---

## Consumer side — chetori javab midim

```csharp
public class GetUserSiteClaimsConsumer : IConsumer<GetUserSiteClaims>
{
    public async Task Consume(ConsumeContext<GetUserSiteClaims> context)
    {
        var claims = await FetchClaimsFromDb(context.Message.UserId);

        await context.RespondAsync(new GetUserSiteClaimsResponse
        {
            UserSiteClaims = claims
        });
    }
}
```

**Nokte-ha:**
- `context.RespondAsync` javab ro be ReplyTo queue mifreste — automatic
- Age exception throw beshe va `RespondAsync` seda zade nashe, **requester timeout mikone** — na error migire
- Baraye error handling, mishe `context.RespondAsync(new ErrorResponse(...))` befrestim va requester `GetResponse<Success, Error>()` estefade kone

---

# BAKHSH-E DOVOM: DEJBAN — tech proof

## 1) RemoteClaimService — claims + cache

```csharp
public sealed class RemoteClaimService(
    IClientFactory clientFactory,
    ICacheService cacheService) : IClaimService
{
    private readonly IRequestClient<GetUserSiteClaims> _client =
        clientFactory.CreateRequestClient<GetUserSiteClaims>();

    public async Task<HashSet<SiteClaimDTO>> GetUserSiteClaimsAsync(
        string userId, CancellationToken cancellationToken = default)
    {
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
    }
}
```

**Zincir-e in service:**

1. **`IClientFactory.CreateRequestClient<T>()`** — MassTransit factory ke ye `IRequestClient` misaze baraye type-e `GetUserSiteClaims`. In factory khodesh endpoint-e consumer ro az convention peyda mikone (exchange name = type name)
2. **`cacheService.GetOrCreateAsync`** — avval to **local cache** negah mikone (HybridCache — Day 25); age nabud, lambda ro ejra mikone ke R/R call mizane
3. **`localCacheExpiration: 2s`** — claim-ha faghat 2 sanie cache mishan. Chera enghad kutah? Chon claim-ha security-critical-an va age avaz beshan, bayad sari reflect beshe
4. **`tags: [CacheTags.UserSiteClaims]`** — vaghti claim avaz beshe, tag invalidate mishe va cache pak mishe
5. **`response.Message.UserSiteClaims`** — typed response — compile-time safe

**Pattern-e mohem:** R/R **hamrah ba cache**. Bedun-e cache, har request-e HTTP ke claim check lazem dare ye R/R call mide — baraye 100 request dar sanie, 100 R/R call-e ke kheili sangin-e. Ba 2s cache, faghat har 2 sanie ye R/R call mire va baghiye az cache mikhunand.

---

## 2) EndpointSyncService — multiple request clients

```csharp
internal sealed class EndpointSyncService(
    ApplicationDbContext dbContext,
    IRequestClient<GetDejbanServiceEndpoints> dejbanRequestClient,
    IRequestClient<GetACLServiceEndpoints> aclRequestClient,
    IRequestClient<GetRequestTrackerServiceEndpoints> requestTrackerRequestClient,
    IRequestClient<GetDCCServiceEndpoints> dccRequestClient,
    IRequestClient<GetReportingServiceEndpoints> reportingRequestClient,
    IRequestClient<GetGateServiceEndpoints> gateRequestClient,
    IEnumerable<EndpointDataSource> endpointDataSources,
    IApiVersionDescriptionProvider versionProvider)
```

In service **6 ta `IRequestClient`** dare — ye dune baraye har service-e Dejban. Vaghti `SyncAsync` seda zade mishe:

```csharp
var tasks = new[]
{
    SafeRequestAsync(dejbanRequestClient, "Dejban", cancellationToken),
    SafeRequestAsync(aclRequestClient, "ACLServer", cancellationToken),
    SafeRequestAsync(requestTrackerRequestClient, "RequestTracker", cancellationToken),
    SafeRequestAsync(gateRequestClient, "GateServer", cancellationToken),
    SafeRequestAsync(dccRequestClient, "DCC", cancellationToken),
    SafeRequestAsync(reportingRequestClient, "Reporting", cancellationToken)
};

var responses = await Task.WhenAll(tasks);
```

**Pattern-e mohem:**

1. **`Task.WhenAll`** — hame-ye 6 ta request **parallel** miran — na sequential. In total latency ro az 6×timeout be 1×timeout kam mikone
2. **`SafeRequestAsync`** — wrapper ke exception ro catch mikone va `null` bargardune:

```csharp
private static async Task<ServiceEndpointDTO?> SafeRequestAsync<T>(
    IRequestClient<T> client, string serviceName, CancellationToken ct)
    where T : class, IServiceEndpoints, new()
{
    try
    {
        var response = await client.GetResponse<GetServiceEndpointsResponse>(
            new T(), ct, timeout: TimeSpan.FromSeconds(5));
        return new ServiceEndpointDTO(serviceName, response.Message.Endpoints ?? []);
    }
    catch { return null; }
}
```

3. **Graceful degradation:** age ye service down bashe, `null` bargardune va sync edame mide ba baghiye-ye service-ha. Faghat `allServicesResponded = false` mishe ke prevent mikone az delete kardan-e endpoint-haye un service (chon nemidune kodum-ha valid hastan va kodum-ha gom shodan)
4. **Timeout 5s** — explicit baraye har request
5. **Pattern na domain:** in code endpoint-ha ro baraye permission system sync mikone — vali **pattern-esh** (multiple R/R + WhenAll + graceful null + timeout) baraye har ja ke az chand service data jam mikoni ghabel estefade-ye

---

## Consumer side — mesal-e Dejban

```csharp
public class GetDejbanServiceEndpointsConsumer
    : IConsumer<GetDejbanServiceEndpoints>
{
    public async Task Consume(ConsumeContext<GetDejbanServiceEndpoints> context)
    {
        var endpoints = CollectEndpoints(); // reflection ru-ye endpoint-ha
        await context.RespondAsync(new GetServiceEndpointsResponse(endpoints));
    }
}
```

Har service ye consumer dare ke endpoint-haye khodesh ro collect mikone va respond mikone. ACL, RequestTracker, DCC, Reporting, GateServer — hame hamun pattern.

---

## Fargh ba Day 20 — Publish/Subscribe

Day 20 = pub/sub + consumers. Message publish mishe, consumer(s) process mikonan, kasi montazer-e javab nist.

Day 62 = request/response. Message ferestad mishe, **ye** consumer javab mide, requester montazer-e javab-e.

| | Day 20 Pub/Sub | Day 62 R/R |
|---|---|---|
| Direction | one-way | two-way |
| Consumer count | 1+ (fanout) | exactly 1 (competing) |
| Requester blocks? | na | are |
| Use case | event, command | query, validation |
| Mesal-e Dejban | UserCreated, DoorCreated | GetUserSiteClaims, GetServiceEndpoints |

---

## Smell-ha va risk-ha

1. **Chatty R/R to request path:** age har HTTP request 5 ta R/R call dashte bashe, latency ziad mishe. Cache ya batch lazeme
2. **Infinite timeout:** default 30s — age set nakoni va consumer down bashe, 30s hang mikone
3. **Cascade failure:** A → R/R → B → R/R → C — age C down bashe, hame hang mikonan. Circuit breaker lazeme
4. **No error response:** age consumer exception throw kone, response nemide — requester timeout mikone. Behtar-e explicit error response befrestim
5. **Bus as DB:** R/R baraye query-e sade khobie; age mikhay business transaction beyn-e service-ha dash bashi, saga pattern lazeme (Day 20)
6. **Coupling-e implicit:** requester type-e message ro midune — age consumer type ro avaz kone ya rename kone, requester break mishe. Contract versioning lazeme
7. **Multiple R/R to loop:** age to ye loop 100 bar R/R bezani, 100 ta round-trip be broker — batch request behtar-e

---

## Debug checklist

1. **Timeout exception?** → consumer down-e ya kond-e? RabbitMQ management → check queue depth
2. **Response wrong type?** → `GetResponse<WrongType>()` — MassTransit deserialize fail → timeout
3. **Consumer exception?** → check consumer log — age crash kone, message be `_error` queue mire va response nemiad
4. **Duplicate response?** → competing consumer: do instance respond mikonan → faghat avvalin miad (do-vomi gom mishe)
5. **Message not delivered?** → exchange bind doroste? `AddConsumer<T>` to DI set shode?
6. **Performance kond?** → RabbitMQ-e under pressure? Network latency? Consumer-e sangin?
7. **Connection refused?** → RabbitMQ connection string check kon; broker up-e?

---

## 25 soal-e mosahebe (ba javab-e kutah)

1. **IRequestClient chie?** → MassTransit interface baraye send-e request va receive-e typed response.
2. **GetResponse chikar mikone?** → Message ro publish mikone ba ReplyTo header va await-e response.
3. **vs Publish?** → Publish one-way-e; GetResponse two-way ba response.
4. **Timeout chie?** → Max wait baraye response; ba'd exception.
5. **Default timeout?** → 30 sanie.
6. **CreateRequestClient chie?** → IClientFactory method ke client baraye ye message type misaze.
7. **Consumer chetori respond mikone?** → `context.RespondAsync(response)`.
8. **vs HTTP?** → R/R loosely coupled (na URL); HTTP direct-tar va sari-tar.
9. **Hang risk chie?** → Consumer down → request montazer → thread blocked.
10. **Cascade failure?** → A→B→C: age C down bashe, B va A ham hang mikonan.
11. **Task.WhenAll pattern?** → Multiple R/R parallel — latency = max(individual).
12. **SafeRequestAsync chie?** → Wrapper ke exception catch mikone va null bargardune.
13. **Chera cache ba R/R?** → Har request R/R sangin-e; cache load ro kam mikone.
14. **localCacheExpiration 2s chera?** → Claims security-critical — stale nabayad bashe.
15. **CacheTags chie?** → Tag baraye targeted cache invalidation.
16. **Reply queue chie?** → Temporary queue ke response rush miad.
17. **CorrelationId chie?** → Match-e response ba request.
18. **allServicesResponded flag?** → Prevent-e delete vaghti service down-e.
19. **Contract coupling chie?** → Requester va consumer bayad message type ro share konan.
20. **Competing consumer?** → Chand instance-e consumer — broker ye kodum ro entekhab mikone.
21. **Error response?** → `GetResponse<Success, Error>()` baraye typed error.
22. **Saga vs R/R?** → R/R baraye query; saga baraye multi-step transaction.
23. **Day 20 link?** → Pub/sub baraye event; R/R baraye query.
24. **EndpointSyncService chand client dare?** → 6 ta IRequestClient.
25. **Performance overhead?** → Broker round-trip + serialize — bishtare az direct HTTP.

---

## Senario-ha

### A) User login → claim check
User login mikone → JWT sakhte mishe → har request-e authenticated-e claim-ha lazeme → `RemoteClaimService.GetUserSiteClaimsAsync(userId)` → avval cache check → age 2s gozashte, R/R be IdentityServer → consumer claim-ha ro az DB mikhoone → respond → cache update → handler claim-ha ro check mikone.

### B) Endpoint sync — startup
`EndpointSyncHostedService` har chand daghighe `SyncAsync` seda mizane → 6 ta R/R parallel → har service endpoint-hashun ro bargardune → IdentityServer hame ro jam mikone → claim-haye endpoint ro sync mikone (insert/update/delete).

### C) Ye service down-e
EndpointSync → 6 ta R/R → ACLServer down-e → SafeRequestAsync catch mikone → `null` → `allServicesResponded = false` → endpoint-haye ACL delete nemishan (safe) → baghiye-ye 5 service sync mishan.

### D) Timeout-e RemoteClaimService
IdentityServer under pressure-e → GetResponse 5s timeout → exception → cacheService-e lambda fail mikone → caller error migire → HTTP 500 be client. **Fix:** circuit breaker ya fallback be last-known claims.

### E) Chatty R/R
Ye handler baraye har item to ye list R/R mizane: `foreach(var item in items) await client.GetResponse(...)` — 100 item = 100 round-trip. **Fix:** batch request pattern: ye message ba list befrest va ye response ba list bargardune.

---

## Resume

**kutah:**

> Cross-service **request/response** with MassTransit `IRequestClient` over RabbitMQ — claims resolution with local cache, parallel endpoint sync across 6 services with graceful degradation, explicit timeouts.

**bullet-ha:**

- Built `RemoteClaimService` with `IRequestClient` and 2-second local cache (`GetOrCreate` + `CacheTags`) for cross-service claim resolution
- Designed `EndpointSyncService` with 6 parallel `IRequestClient` calls via `Task.WhenAll`, graceful null-return on timeout, and safe endpoint pruning only when all services respond
- Applied explicit 5-second timeouts on all request clients to prevent cascade hangs
- Implemented consumer-side `RespondAsync` pattern across all service boundary queries

**skill-ha:** `MassTransit` · `Request/Response` · `IRequestClient` · `RabbitMQ` · `Caching` · `Timeout` · `Microservices` · `CQRS`

---

## Interview 60s

> «Besides pub/sub, we use MassTransit request/response when a service needs a synchronous answer from another. The main example is RemoteClaimService — it creates a request client for GetUserSiteClaims, sends over RabbitMQ, and caches the response for 2 seconds locally. EndpointSyncService fans out 6 request clients in parallel with Task.WhenAll, each with a 5-second timeout and graceful null-return, so a single downed service doesn't block sync. The key risk is cascade hangs if timeouts aren't set, and chatty loops if you call R/R per item instead of batching.»

---

## File-haye mohem

| chi | koja |
|---|---|
| RemoteClaimService | `Common/Claims/RemoteClaimService.cs` |
| CacheTags | `Common/Caching/CacheTags.cs` |
| EndpointSyncService | `IdentityServer/Infrastructure/Services/EndpointSyncService.cs` |
| EndpointSyncHostedService | `IdentityServer/Infrastructure/HostedServices/EndpointSyncHostedService.cs` |
| Consumer mesalha | `ACLServer/.../GetACLServiceEndpointsConsumer.cs`, `Dejban/.../GetDejbanServiceEndpointsConsumer.cs`, `DCC/.../GetDCCServiceEndpointsConsumer.cs` |
| Contract messages | `Common/EventBus/Contracts/Requests/` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 20 MassTransit | Pub/Sub consumers — in ruz R/R-e |
| 25 HybridCache | `cacheService.GetOrCreateAsync` — local + Redis |
| 06 JWT | claim-ha ke R/R resolve mikone, baraye JWT authorization estefade mishe |
| 18 DI | `IRequestClient` va `IClientFactory` register mishe to DI |
| 07 YARP | endpoint-haye sync-shode baraye permission system estefade mishan |

---

## Deep dive — IClientFactory vs IRequestClient injection

Do rah baraye R/R client gereftan:

**1. `IClientFactory.CreateRequestClient<T>()`** — runtime creation:
```csharp
private readonly IRequestClient<GetUserSiteClaims> _client =
    clientFactory.CreateRequestClient<GetUserSiteClaims>();
```
Dejban az in estefade mikone. `IClientFactory` injected mishe va client to constructor sakhte mishe.

**2. Direct `IRequestClient<T>` injection:**
```csharp
public class MyService(IRequestClient<GetUserSiteClaims> client) { ... }
```
MassTransit khodesh `IRequestClient<T>` ro resolve mikone. EndpointSyncService az in estefade mikone (6 ta IRequestClient to constructor).

Fargh: IClientFactory flexible-tar-e (mishe runtime type entekhab koni); direct injection sade-tar-e va testable-tar-e (mock-able).

---

## Deep dive — reply queue strategy

MassTransit do strategy dare:

1. **Temporary queue (per-request):** baraye har GetResponse ye exclusive auto-delete queue misaze. Clean vali overhead dare
2. **Bus endpoint reply queue (shared):** ye queue baraye hame-ye response-ha. MassTransit ba CorrelationId response ro be dorost-e requester route mikone. Efficient-tar-e — Dejban az in estefade mikone

Config:

```csharp
services.AddMassTransit(x =>
{
    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.UseInMemoryOutbox(context); // outbox baraye publish
        // reply queue khodkar az bus endpoint estefade mikone
    });
});
```

---

## Deep dive — error handling to R/R

**Age consumer exception throw kone:**
- MassTransit message ro be `_error` queue move mikone
- Response be requester **nemire**
- Requester timeout mikone va `RequestTimeoutException` migire

**Behtar-in rah:**

```csharp
// Consumer:
try { ... await context.RespondAsync(success); }
catch (Exception ex)
{
    await context.RespondAsync(new ErrorResponse(ex.Message));
}

// Requester:
var (success, error) = await client.GetResponse<SuccessResponse, ErrorResponse>(message);
if (success.IsCompletedSuccessfully)
    return (await success).Message;
else
    return (await error).Message; // handle error
```

Dejban in pattern ro estefade nakarde — SafeRequestAsync faghat catch mikone va null bargardune. Vali baraye production-grade, typed error response behtar-e.

---

## Deep dive — IRequestClient va DI lifetime

`IRequestClient<T>` ke MassTransit register mikone **scoped**-e — yani baraye har HTTP request ye instance sakhte mishe. In OK-e baraye controller/handler. Vali age to **singleton** (masalan BackgroundService) lazem dashte bashi, bayad `IClientFactory` estefade koni va khodet besazi — chon scoped service to singleton inject nemishe.

`RemoteClaimService` khodesh chie? → `IClaimService` ma'mulan scoped register mishe. `EndpointSyncService` ham scoped-e (az hosted service ba scope seda zade mishe).

---

## Extra — MassTransit mediator (in-process R/R)

Age do ta handler to **hamun process** bashan (masalan Dejban modular monolith), mishe az MassTransit mediator estefade koni — R/R bedun-e broker:

```csharp
services.AddMediator(x => { x.AddConsumer<MyConsumer>(); });
```

In **sari-tar**-e chon az broker rad nemishe. Dejban az in estefade nakarde (MediatR darand baraye in-process), vali concept-esh mohem-e baraye mosahebe.

---

## Extra — retry policy ru-ye R/R

MassTransit retry policy mishe set koni:

```csharp
cfg.UseRetry(r => r.Interval(3, TimeSpan.FromSeconds(1)));
```

Vali in baraye **consumer** side-e (retry-e process kardan-e message). Baraye **requester** side, age timeout beshe, khodet bayad retry koni (ba Polly ya dasti loop). MassTransit khodesh requester retry nadare — faghat timeout exception mide.

---

## Extra — monitoring-e R/R

RabbitMQ Management dashboard:
- **Queue depth:** age request queue por bashe, consumer kond-e ya down-e
- **Reply queue:** age reply queue-ha jam beshan, requester-ha timeout mikonan
- **Consumer count:** age 0 bashe, hich consumer respond nemikone
- **Message rate:** throughput-e request va response

---

## Extra — batch request pattern

Be ja-ye:
```csharp
foreach (var id in userIds)
    claims[id] = await client.GetResponse<Resp>(new GetClaims(id));
```

Behtar:
```csharp
var response = await client.GetResponse<BatchResp>(new GetClaimsBatch(userIds));
```

Ye round-trip be ja-ye N ta. Dejban in ro implement nakarde baraye claims (chon cache 2s handle mikone), vali baraye dge pattern-ha (masalan bulk validation) mohem-e.

---

## Deep dive — RemoteClaimService to zincir-e authentication

Vaghti ye HTTP request be har service-e Dejban miad (masalan ACLServer, Dejban API, RequestTracker), in etefagh miofte:

```
1. JWT token to header-e Authorization hast
2. ASP.NET Authentication middleware JWT ro validate mikone
3. Claims az JWT extract mishe (userId, sub, ...)
4. Authorization middleware check mikone ke user permission dashte bashe
5. Permission check → IClaimService.GetUserSiteClaimsAsync(userId)
6. IClaimService = RemoteClaimService (az Common inject shode)
7. RemoteClaimService:
   a. Cache check (local 2s) → hit? return
   b. Miss → IRequestClient<GetUserSiteClaims>.GetResponse(...)
   c. IdentityServer consumer claim-ha ro az DB mikhoone
   d. Response → cache store → return
8. Authorization decide mikone: allow/deny
```

**Yani:** har HTTP request-i ke be har service miad, **potential** ye R/R call dare be IdentityServer. Bedun-e cache, in bottleneck-e asli mishe. Ba cache-e 2s, bish az 99% az request-ha az local cache mikhunand va R/R call nadaran.

**Risk:** age IdentityServer kamel down bashe va cache expire beshe, **hame-ye service-ha** authorization failure migiran. In ye **single point of failure**-e. Fix: longer cache fallback ya local claim store.

---

## Deep dive — contract versioning to R/R

Message type-haye R/R (masalan `GetUserSiteClaims`, `GetUserSiteClaimsResponse`) to **Common** project-e ke share mishe beyn-e hame-ye service-ha. In yani:

- Age field-e jadid be response ezafe koni, **backward compatible**-e (consumer-e ghadimi field ro ignore mikone)
- Age field remove koni, **breaking change**-e — hame-ye requester-ha ke un field ro mikhundan, break mishan
- Age message type ro **rename** koni, queue name avaz mishe va consumer-e ghadimi peida nemishe

**Best practice:**
- Faghat field **ezafe** kon, hargez remove nakon (deprecate kon va null begozar)
- Message type ro rename nakon — age type jadid mikhay, ye type-e jadid besaz va do ta consumer negah dar (versioned)
- Common project ro careful release kon — hame-ye service-ha bayad hamzaman update beshan

---

## Deep dive — R/R va distributed tracing

MassTransit ba OpenTelemetry integration dare — har R/R call ye span-e jadid to distributed trace misaze. In kheili mohem-e baraye debug:

```
HTTP Request (trace-id: abc)
  └── MassTransit Send GetUserSiteClaims (span-id: def)
       └── MassTransit Consume GetUserSiteClaims (span-id: ghi)
            └── DB Query (span-id: jkl)
       └── MassTransit Response (span-id: mno)
```

Dejban OpenTelemetry-e kamel set nakarde, vali MassTransit khodesh header-haye trace ro propagate mikone. Age farda Jaeger ya Zipkin set koni, R/R call-ha trace mishe.

---

## Deep dive — R/R va outbox pattern

MassTransit ye "transactional outbox" dare ke message-ha ro avval to DB save mikone va ba'd asynchronous publish mikone. Vali baraye **R/R in outbox be dard nemikhoret** — chon requester **hamun lahze** montazer-e javab-e. Age message to outbox save beshe va 5 sanie ba'd publish beshe, requester ghablan timeout karde.

**Gha'ede:** outbox baraye Publish (fire-and-forget); direct send baraye R/R. Dejban ham injuri tanzimshe.

---

## Deep dive — multiple response types

MassTransit mishe **chand ta response type** dashte bashe:

```csharp
// Requester:
var (success, notFound) = await client
    .GetResponse<SuccessResponse, NotFoundResponse>(request);

if (success.IsCompletedSuccessfully)
    return (await success).Message;
else
    return Problem((await notFound).Message.Reason);

// Consumer:
if (found)
    await context.RespondAsync(new SuccessResponse(data));
else
    await context.RespondAsync(new NotFoundResponse("Not found"));
```

In pattern kheili behtar-e az inke consumer exception throw kone va requester timeout bokone. Dejban in ro estefade nakarde — SafeRequestAsync faghat catch mikone va null mide. Vali baraye production-grade, typed multi-response behtar-e.

---

## Deep dive — R/R performance benchmarks

Typical latency-e R/R ba RabbitMQ:

| senario | latency |
|---|---|
| Broker local, consumer local, simple response | 1-5ms |
| Broker remote (same DC), consumer remote | 5-15ms |
| Consumer sangin (DB query + compute) | 20-200ms |
| Broker under pressure (full queue) | 100ms+ |
| Network issue / reconnect | seconds |

Compare ba HTTP:
| senario | latency |
|---|---|
| Direct HTTP, same machine | <1ms |
| HTTP, same DC | 1-5ms |

R/R overhead ~2-5ms bala-tar-e az direct HTTP chon broker middleware-e. Baraye interactive request ke latency critical bashe, in fargh mohem-e. Baraye background sync (EndpointSync), bi-ahamiyat-e.

---

## Extra — testing-e R/R

MassTransit ye **InMemoryTestHarness** dare:

```csharp
[Fact]
public async Task GetUserSiteClaims_Returns_Claims()
{
    await using var harness = new InMemoryTestHarness();
    harness.Consumer<GetUserSiteClaimsConsumer>();
    await harness.Start();

    var client = harness.GetRequestClient<GetUserSiteClaims>();
    var response = await client.GetResponse<GetUserSiteClaimsResponse>(
        new GetUserSiteClaims("user-id"));

    Assert.NotEmpty(response.Message.UserSiteClaims);
}
```

In test bedun-e RabbitMQ-e vaghei run mishe — in-memory broker. Kheili sari-e va baraye CI/CD ideal-e.

---

## Extra — R/R ba gRPC jaygozin-e

Ba'zi team-ha be ja-ye R/R over broker, az **gRPC** baraye cross-service query estefade mikonan:

| | R/R (MassTransit) | gRPC |
|---|---|---|
| Transport | broker (RabbitMQ) | direct TCP (HTTP/2) |
| Discovery | exchange/queue name | service URL |
| Load balance | competing consumers | client-side ya service mesh |
| Performance | bishtare overhead | kamtar overhead |
| Resilience | broker queue buffer | direct — fail = fail |
| Contract | C# class (shared) | .proto file (code-gen) |

Dejban baraye device SDK az gRPC estefade mikone (Day 27) va baraye inter-service query az R/R. Do ta tool-e mokhtalef baraye do ta use case.

---

## Extra — saga pattern — key faraghtar az R/R beri

Vaghti ye operation-e cross-service **transactional** bashe (masalan "create user + assign claims + notify services"), R/R kafi nist chon:
- Age step 2 fail kone, step 1 bayad rollback beshe
- R/R in coordination ro nadare

**Saga** (MassTransit State Machine ya Choreography) in masir ro manage mikone. Dejban saga nadare — vali concept-esh baraye mosahebe mohem-e.

---

## Extra — connection recovery

MassTransit khodesh connection recovery dare — age RabbitMQ restart beshe:
1. Detect-e disconnect
2. Exponential backoff retry
3. Re-establish connection
4. Re-declare exchanges/queues
5. Resume consume/publish

Requester-e ke to in gap R/R bezane, timeout mikone va exception migire. Ba'd az recovery, R/R dobare kar mikone. **Client code niaz be retry nadare** — MassTransit transport-level recovery dare.

---

## Masir-e vaghei — EndpointSync

```
1. EndpointSyncHostedService timer tick (har 5 daghighe)
2. SyncAsync() seda zade mishe
3. 6 ta SafeRequestAsync parallel (Task.WhenAll)
4. Har request:
   a. GetResponse<GetServiceEndpointsResponse>(new T(), ct, 5s timeout)
   b. Consumer endpoint-haye khodesh ro collect mikone (reflection ru-ye endpoints)
   c. RespondAsync(response)
   d. Ya timeout → catch → null
5. allEndpoints jam mishe
6. age allServicesResponded:
   a. endpoint-haye jadid → Insert
   b. endpoint-haye update shode → Update
   c. endpoint-haye hazf shode → Delete
7. age !allServicesResponded:
   a. Insert + Update only
   b. **Delete skip mishe** (ta endpoint-haye service-e down gom nashan)
8. SaveChangesAsync
```

In pattern-e **defensive sync** — data-ye down service ro pak nemikone.

---

## Deep dive — chera RemoteClaimService Common-e

`RemoteClaimService` to `Common` project-e — na to ye service-e khas. Chera? Chon **har service** ke authorization lazem dare, bayad claim check kone. ACLServer, RequestTracker, Dejban API, DCC, Reporting — hameye in-ha `IClaimService` inject mikonan. Age `RemoteClaimService` to ye service khas bud, baghiye bayad reference-esh mikardan ke coupling mide.

Ba Common:
- Har service faghat `Common` reference mikone (ke ghablan ham dare)
- `IClaimService` register mishe to DI-e har service
- `IClientFactory` ke to Common inject mishe, az MassTransit-e har service miad
- Consumer (`GetUserSiteClaimsConsumer`) faghat to IdentityServer-e — baghiye faghat requester-an

**Pattern:** "shared client, single consumer" — ye contract to Common, client-esh ham to Common, consumer to ye service.

---

## Deep dive — EndpointSyncService va allServicesResponded guard

In ye olgu-ye kheili mohem-e ke arzesh-e deghghat dare:

```csharp
if (allServicesResponded)
{
    // endpoint-haye ke to flatEndpoints nistan → delete
    foreach (var existingClaim in existingClaims)
    {
        if (!currentEndpointValues.Contains(existingClaim.Value))
            claimsToRemove.Add(existingClaim);
    }
}
```

**Chera in guard lazeme?** Farz kon ACLServer down-e. ACLServer endpoint-hash to `flatEndpoints` nist. Bedun-e guard, code fekr mikone "in endpoint-ha hazf shodan" va delete mikone — **hame-ye ACL permission-ha** gom mishan. Admin-ha access-eshun be ACL panel ro az dast midan. Vaghti ACL dobare bala biad, endpoint-ha sync mishan vali permission-haye role/user **ghablan delete shodeye** va bayad dasti dobare set beshan.

Ba guard: age **hamey-e** service-ha javab dadan, **un vaght** confident-im ke endpoint-haye hazf-shode vaghean hazf shodan (na inke service down bude). Age hatta ye service javab nade, delete skip mishe va faghat insert/update anjam mishe.

In ye pattern-e **defensive programming**-e ke baraye production critical-e.

---

## Khoruj-e zehni

> In ruz ra vaghti digeri kardi ke betuni bedune look-up, fargh-e Publish va GetResponse ro begui, RemoteClaimService zincir-e cache + R/R ro trace koni, va EndpointSyncService parallel pattern ro tozih bedi.

Age in paragraph mal-e to shod — Day 62 done.

**Nokte-ye akhar:** R/R over messaging ye tool-e — na silver bullet. Baraye har cross-service call bayad tashkhis bedi ke HTTP, R/R, ya pub/sub behtar-e. Table-e decision ro yadet bashe.

In ye signal-e khoob-e baraye mosahebe ke neshun mide tool-ha ro ba trade-off-hashun mishenasi, na inke hameja az yek pattern estefade koni.

---

## Anti-pattern-ha

```csharp
// BAD: R/R bedun-e timeout
await client.GetResponse<Resp>(msg); // default 30s!
// GOOD: explicit timeout
await client.GetResponse<Resp>(msg, ct, timeout: TimeSpan.FromSeconds(5));

// BAD: R/R to tight loop
foreach (var item in items)
    await client.GetResponse<Resp>(new Req(item.Id));
// GOOD: batch request

// BAD: R/R baraye fire-and-forget event
await client.GetResponse<Ack>(new UserCreated(...));
// GOOD: await publishEndpoint.Publish(new UserCreated(...));

// BAD: consumer ke exception throw mikone bedun-e respond
// GOOD: try/catch + RespondAsync(error)
```

---

## Mini lab

1. `RemoteClaimService` ro bekhun — zincir-e cache + R/R ro trace kon
2. `EndpointSyncService.SyncAsync` ro bekhun — 6 ta parallel R/R
3. `SafeRequestAsync` ro bebin — graceful null return
4. Ye consumer (masalan `GetACLServiceEndpointsConsumer`) ro bebin — `RespondAsync`
5. `CacheTags.cs` ro bebin — ye const string baraye invalidation
6. RabbitMQ management dashboard ro baz kon — queue-haye reply ro bebin

---

## Glossary

| kalame | ma'ni |
|---|---|
| IRequestClient\<T\> | MassTransit interface baraye R/R |
| GetResponse | method ke request mifreste va response migire |
| CreateRequestClient | IClientFactory method ke client misaze |
| RespondAsync | consumer method baraye ferestadan-e response |
| Reply queue | queue ke response rush miad |
| CorrelationId | match-e response ba request |
| Timeout | max wait baraye response |
| RequestTimeoutException | exception vaghti timeout beshe |
| Competing consumer | chand instance-e consumer ke broker ye-kodum ro entekhab mikone |
| SafeRequestAsync | wrapper ke exception catch mikone va null bargardune |
| CacheTags | tag baraye targeted cache invalidation |
| Task.WhenAll | parallel execution-e multiple async task |
| Graceful degradation | system ke ba failure-e partial kar mikone |

---

## Self-test-e sari

1. IRequestClient chi mikone? → Request mifreste, typed response migire
2. vs Publish? → Publish one-way; R/R two-way
3. RemoteClaimService cache-esh chand sanie? → 2s local
4. EndpointSyncService chand ta client dare? → 6 ta (parallel)
5. SafeRequestAsync chi return mikone vaghti fail beshe? → null
6. Default timeout chie? → 30s (Dejban explicit 5s set karde)
7. Cascade hang chie? → A→B→C: C down → hame hang
8. Consumer chetori respond mikone? → context.RespondAsync(response)
9. Day 20 link? → Pub/sub; in R/R-e
10. allServicesResponded flag chie? → Prevent-e delete vaghti service down

Age 8/10 ya bishtar dorost bud → beri sar-e Day 63.

---

## Resume keywords (ATS)

`MassTransit` · `Request/Response` · `IRequestClient` · `RabbitMQ` · `Microservices` · `Caching` · `Cross-service Communication` · `Timeout` · `Graceful Degradation` · `.NET`

---

## In che chizi-e Day 62 *nist*

- Rahnama-ye kamel-e MassTransit nist — un Day 20-e; inja faghat R/R-e
- Rahnama-ye RabbitMQ setup nist — farz mikoni broker run-e
- Saga pattern nist — faghat mention shode
- Consumer-haye publish/subscribe nist — un Day 20-e
- Identity domain nist — faghat pattern-e technical-e R/R

---

## Extra — R/R va concurrency-e consumer

Vaghti chand ta instance az consumer run bashe (scale-out), RabbitMQ **ye kodum** ro entekhab mikone (round-robin default). In yani:

- Load balance-e khodkar-e bedun-e load balancer
- Age ye instance busy bashe, dge-i request ro migire (prefetch count)
- Age ye instance crash kone, message requeue mishe va dge-i migire

Config-e prefetch:

```csharp
cfg.Host("rabbitmq://localhost");
cfg.PrefetchCount = 16; // chand ta message hamzaman process kone
```

Baraye R/R, prefetch mohem-e — age consumer 1 ta 1 ta process kone, burst-e request-ha queue mishan va requester timeout mikone. Prefetch-e bala concurrent processing mide vali resource-e bishtar mikhore.

---

## Extra — R/R ba circuit breaker (Polly)

```csharp
var policy = Policy
    .Handle<RequestTimeoutException>()
    .CircuitBreakerAsync(
        exceptionsAllowedBeforeBreaking: 5,
        durationOfBreak: TimeSpan.FromSeconds(30));

var claims = await policy.ExecuteAsync(() =>
    client.GetResponse<Resp>(msg, ct, timeout: TimeSpan.FromSeconds(5)));
```

Age 5 bar timeout beshe, circuit **open** mishe va ta 30 sanie **hich request-i** nemire (immediately fail mikone). In prevent-e cascade hang mikone va be down service vaght-e recovery mide. Dejban in ro implement nakarde vali pattern-esh mohem-e.

---

## Extra — fargh-e R/R ba gRPC streaming

| | R/R | gRPC Unary | gRPC Streaming |
|---|---|---|---|
| Pattern | request → response | request → response | request → stream of responses |
| Transport | broker | direct HTTP/2 | direct HTTP/2 |
| Use case | cross-service query | cross-service query | realtime data feed |
| Dejban | claims, endpoints | device SDK (Day 27) | SSMHub (Day 26) |

R/R va gRPC unary conceptually yeksan-an (question → answer), vali transport-eshun farghe.

---

## Extra — health check baraye R/R

Mishe ye health check besazi ke check kone consumer alive-e:

```csharp
public class ClaimServiceHealthCheck : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(...)
    {
        try
        {
            await client.GetResponse<PingResponse>(new Ping(), ct,
                timeout: TimeSpan.FromSeconds(2));
            return HealthCheckResult.Healthy();
        }
        catch { return HealthCheckResult.Unhealthy("Claim service unreachable"); }
    }
}
```

Dejban in health check ro nadare vali baraye production-e vaghei lazeme — ta monitoring system befahme consumer down-e.

---

## Extra — message headers va metadata

MassTransit khodesh header-ha ro set mikone:

| header | chi-e |
|---|---|
| MessageId | unique id-e message |
| CorrelationId | baraye match-e request va response |
| ConversationId | trace-e kamel-e conversation |
| ReplyTo | address-e queue ke response bayad bere |
| ContentType | serialization format (default: application/vnd.masstransit+json) |
| SentTime | timestamp-e send |

In header-ha baraye debug va monitoring kheili mofid-an — to RabbitMQ management mishe message-ha ro inspect koni.

---

## Extra — R/R va retry semantic

Vaghti R/R timeout mishe, **aya message gom shode?** Na lazeman — momkene consumer hanuz dare process mikone. Pas:

1. Requester timeout mikone → user error migire
2. Consumer process ro tamum mikone → response be reply queue mifreste
3. Reply queue momkene expire shode bashe → response gom mishe
4. Ya reply queue hanuz hast → response miad vali requester ghablan rafteh

**Natije:** consumer momkene **side effect dashte bashe** (DB write) ke ba'd az requester timeout anjam shode. In baraye **query** OK-e (idempotent), vali baraye **command** (masalan "create user") khatarnake — momkene duplicate beshe.

**Gha'ede:** R/R baraye **query** estefade kon, na baraye **command** ke side effect dare. Baraye command-e cross-service, pub/sub + idempotent consumer behtar-e.

---

## Extra — MassTransit R/R va Kubernetes

To Kubernetes ke pod-ha scale-up/down mishan:

- Consumer pod-e jadid → khodkar be RabbitMQ vasl mishe → shoru be consume
- Consumer pod delete mishe → graceful shutdown → message requeue
- Requester pod → timeout → R/R call-e dge ba consumer-e dge

**Nokte:** vaghti pod-e consumer scale-down mishe, in-flight message-ha bayad requeue beshan. MassTransit graceful shutdown dare ke in ro handle mikone — `StopAsync` montazer-e tamum shodan-e in-flight consume mishe ghabl az shutdown.

---

## Checklist-e nahaei

- [ ] IRequestClient + GetResponse + timeout
- [ ] RemoteClaimService: R/R + cache + CacheTags
- [ ] EndpointSyncService: 6 parallel + SafeRequestAsync + graceful null
- [ ] Consumer: RespondAsync pattern
- [ ] vs Publish (Day 20)
- [ ] vs HTTP
- [ ] Smell-ha: chatty loop, no timeout, cascade hang
- [ ] 25 soal ba javab
- [ ] Resume bullet-ha

---

## Extra — R/R va idempotency key

Age requester retry kone (masalan user dobare click mikone), do ta request mifreste va consumer do bar process mikone. Baraye query-ha in OK-e (idempotent). Vali age R/R baraye command estefade beshe (ke Dejban nakarde — vali momkene team-haye dge konan), bayad **idempotency key** to message bashe va consumer duplicate check kone:

```csharp
// Message:
public record CreateOrder(Guid IdempotencyKey, string CustomerId, ...);

// Consumer:
if (await db.Orders.AnyAsync(o => o.IdempotencyKey == msg.IdempotencyKey))
{
    await context.RespondAsync(new OrderAlreadyExists());
    return;
}
```

---

## Extra — R/R monitoring metrics

Metric-hayi ke bayad track koni:

| metric | chie | threshold |
|---|---|---|
| `masstransit_request_duration_seconds` | latency-e R/R | < 100ms baraye interactive |
| `masstransit_request_timeout_total` | tedad-e timeout | < 1% az total |
| `masstransit_consumer_duration_seconds` | processing time-e consumer | depends on query |
| `rabbitmq_queue_messages_ready` | message-haye dar saf | < 100 (age bala bere, consumer kond-e) |
| `masstransit_bus_reconnect_total` | reconnect be broker | 0 dar halat-e normal |

---

## Extra — chera R/R baraye "query" va na "command"

Summary-e gha'ede:

- **Query** (read, no side-effect): R/R OK-e. Timeout = "nemiduni", retry safe-e
- **Command** (write, side-effect): R/R risk-e. Timeout ≠ "anjam nashode" — momkene anjam shode bashe. Retry = duplicate risk
- **Event** (notification): Publish, na R/R. Kesi montazer-e javab nist

Dejban in gha'ede ro riayat karde — R/R faghat baraye claim query va endpoint query. Write-haye cross-service az Publish (Day 20) estefade mikonan.

To mosahebe age beporsad "when would you use request/response over messaging instead of HTTP?" javab bedah: "When the services already share a broker for pub/sub and I want to avoid URL coupling. The main win is load-balanced competing consumers and broker-level topology routing. The trade-off is slightly higher latency and explicit timeout management."

---

*Day 62 tamum. Ba'di: Day 63 — Rate limiting + Output cache + API versioning. Fehrest: [README.md](./README.md).*
