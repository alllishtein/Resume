# Day 32 — Polly (resilience)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Polly** library-e resilience toye .NET-e: mige «age in kar fail shod, *chejori* dobare / sabr / cut / fallback kon». Classic pattern-ha: **Retry**, **Circuit Breaker**, **Timeout**, **Bulkhead**, **Fallback**.

To Dejban do jaye mohem:

1. **Polly sarih (package `Polly` 8.6.5)** — faghat **ACLServer**: `RetryPolicies.GetDefaultRetryPolicy` ba `WaitAndRetryAsync(3, 2^n saniye)` dor-e `SaveChangesAsync` vaghti access-log az device (ZK / Tiam / Virdi) miad. Yani transient DB blip → 3 bar dobare, ba log Warning.

2. **Resilience-e messaging (MassTransit)** — hame microservice-ha: `UseMessageRetry` exponential + `UseCircuitBreaker` ru-ye Rabbit bus. In *API*-ash Polly nist, ama *mafhum*-ash haman resilience-e — Day 20 omigh-tar; inja az zaviye-ye «chera / chejori fekr koni» miayim.

HttpClient-haye proje (DccHttpClient, MediaMTX, …) alan `AddStandardResilienceHandler` / Polly HTTP handler **nadaran** — gap-e possible baraye mosahebe.

**Band-e gharardad-e jadid:** in fasl ghasdan ravoontar va sade-tar tozih mide — bishtar «farz kon / yani chi / chera», kamtar telegram.

---

# BAKHSH-E AVAL: WORLD — resilience be zaban-e adam

## Farz kon — restaurant dobare

Day 31 goftim health = «ashpazkhune baz-e?».  
Inja: mosafer order dade, ashpaz **moment** gas qat shode.

| bedune resilience | ba resilience |
|---|---|
| waiter mige «fail» → mosafer miravad | waiter 2–3 bar sabr + dobare order |
| age ashpazkhune atish gerefte | waiter diga order nemifreste (circuit open) |
| age ashpaz 10 daghighe javab nemide | timeout → mosafer wait-e bi-payan nadare |

**Yani chi?** Software dependency (DB, HTTP, gRPC, broker) *hamishe* 100% nist. Resilience = design baraye «fail-e movaghat» bedune crash-e kolli system.

---

## Chera retry hame chiz nist?

Retry faghat baraye **transient** failure ma'ni dare:

| transient (retry OK) | permanent (retry BAD) |
|---|---|
| network blip | 400 validation |
| DB deadlock / timeout kotah | 401/403 auth |
| 503 / connection reset | business rule fail |
| lock contention | bug-e code |

**Chera retry-e permanent bad-e?**  
Bar-e bihoode + delay + shayad duplicate side-effect (do bar charge, do bar email) age idempotent nabashi.

**Ghaede-ye sade:**  
Retry kon chizi ke «shayad ba'dan khub she».  
Retry nakon chizi ke «hamishe hamin javab-e».

---

## Pattern-haye asli Polly (WORLD)

### 1) Retry

«Fail shod → sabr → dobare.»

- **fixed:** har bar 2s  
- **exponential:** 2s, 4s, 8s…  
- **jitter:** ye random kuchik ezafe ta hame client-ha hamzaman nazanan (thundering herd)

```csharp
// Polly v7/v8 classic style (mesal zehni)
Policy
  .Handle<HttpRequestException>()
  .OrResult<HttpResponseMessage>(r => (int)r.StatusCode == 503)
  .WaitAndRetryAsync(3, attempt => TimeSpan.FromSeconds(Math.Pow(2, attempt)));
```

**Yani chi?** 3 attempt ezafe (plus avval = 4 try kole), delay 2^attempt.

### 2) Circuit Breaker

«Chand bar fail → diga call nakon ye moddat → ba'd yek test (half-open).»

Halat-ha:

| state | ma'ni-ye sade |
|---|---|
| **Closed** | normal — call miravad |
| **Open** | fail ziad → call-ha *fori* fail (bedune zadan be dependency) |
| **Half-open** | ye/chand call test — age OK → Closed |

**Chera?** Age DB murde, 1000 thread retry = storm. Circuit = «boro nafas bekesh».

### 3) Timeout

«Bishtar az X saniye wait nakon.»  
Prevent hung request.

### 4) Bulkhead / isolation

«Chand thread/concurrent call max.»  
Ta yek dependency kond, hame thread-haye app ro nakhorad.

### 5) Fallback

«Age fail → javab-e bedune plan B» (cache, default, empty list, message-e dustane).

### 6) Hedging (pishrafte)

«Do request parallel; avalin javab.» — kamtar to enterprise classic; bishtar cloud.

---

## Polly v7 vs v8 (kholase-ye mosahebe)

| | v7 | v8 |
|---|---|---|
| API | `Policy.Handle…` | `ResiliencePipeline` / `ResiliencePipelineBuilder` |
| DI | dasti / extensions | `AddResiliencePipeline` (Microsoft.Extensions.Resilience) |
| HTTP | `AddPolicyHandler` | `AddStandardResilienceHandler` |

Dejban ACL **Polly 8.6.5** package dare ama code-ash hanuz style-e **classic** `Policy<T>.Handle…WaitAndRetryAsync` estefade mikone (API ke ba Polly 8 ham kar mikone via compatibility).

**Yani chi?** Version package ≠ hatman API-e jadid. To mosahebe begu: «we use Polly retry policies around SaveChanges; pipeline API-e v8 hanooz migrate nashode.»

---

## Stack ba resilience — olgu-ye zehni

```
Caller
  → Timeout
    → Retry (transient)
      → Circuit Breaker
        → Bulkhead
          → Actual call (HTTP/DB/gRPC)
```

Tartib mohem-e: timeout birun, retry vasat, circuit nazdik dependency — debate dare; important ine **fekr koni** chejori compose mishan, na hafz-e yek tartib-e moghadas.

MassTransit ino barat to bus filter chain mizane (retry + CB). Polly to code-e dasti `ExecuteAsync` mizane.

---

## Idempotency — dust-e retry

**Farz kon:** `SaveChanges` success shod ama response timeout → client retry → dobare insert?

Age operation **idempotent** nist → duplicate.

Pas:

- inbox / unique key (Day 23)  
- upsert  
- idempotency key HTTP  
- ya faghat retry roye amal-haye safe (read) / controlled write  

ACL retry dor-e `SaveChanges` — farz: same change tracker, dobare save mamulan no-op ya same row update; ama deadlock retry ma'ni dare. Smell: `Handle<Exception>()` *hame* exception — hatta bug!

---

# BAKHSH-E DOVOM: DEJBAN — koja resilience hast?

## Naqshe-ye sade

| koja | chi | technology |
|---|---|---|
| ACLServer `RetryPolicies` | retry `SaveChanges` ba'd access-log device | **Polly** sarih |
| Dejban.Api + digar services MassTransit | message retry + circuit breaker | **MassTransit** (mafhum resilience) |
| `Task.Delay(10000)` ghabl Migrate | wait-e DB | **hack** — behtar Polly/retry (Day 31) |
| DccHttpClient / MediaMTX HttpClient | call HTTP | **bedune** Polly handler (gap) |
| gRPC ZK/Tiam/Virdi | sidecar calls | check kon — resilience sarih kam |

---

## Qesmat 1 — Polly to ACLServer (daqiq)

### File

`Microservices/ACLServer/Abstractions/Resilience/RetryPolicies.cs`

```csharp
public static IAsyncPolicy<T> GetDefaultRetryPolicy<T>(ILogger logger)
{
    return Policy<T>
        .Handle<Exception>()
        .WaitAndRetryAsync(3, retryAttempt =>
            TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)),
            onRetry: (exception, timeSpan, retryCount, context) =>
            {
                logger.LogWarning(exception.Exception,
                    "Retry {RetryCount} after {Delay}s due to {Message}",
                    retryCount, timeSpan.TotalSeconds, exception.Exception.Message);
            });
}
```

### Yani chi, khat be khat?

1. `Policy<T>` — policy-e typed (inja `T` = `int` chon `SaveChangesAsync` → `int`).  
2. `Handle<Exception>()` — **har** exception → retry candidate. (Smell: ghaliz; behtar `DbUpdateException` / timeout.)  
3. `WaitAndRetryAsync(3, …)` — max **3** retry ba'd az fail-e avval.  
4. Delay = `2^retryAttempt` saniye → attempt1: 2s, attempt2: 4s, attempt3: 8s.  
5. `onRetry` → Serilog Warning ba shomare va delay — Day 30 visible.

### Farz kon — access log miad

Device (Tiam) event mide → handler user access log minevise → `SaveChangesAsync`.

**Bedune Polly:** deadlock / transient Npgsql → exception → log Error → log-e taradod **gom** (ya nime).

**Ba Polly:**

```
SaveChanges fail
  → wait 2s → retry 1
  → fail → wait 4s → retry 2
  → fail → wait 8s → retry 3
  → hanuz fail → exception bubble → catch biruni LogError
```

**Chera inja?**  
Access log high-churn + concurrent device events → transient DB conflict mamul-e. Retry = kamtar data loss.

### Koja seda mishe?

Mesal-ha (pattern yeksan):

- `TiamSDKEventHandlers/RealtimeAccessLogEventHandler`  
- `VirdiSDKEventHandlers/RealtimeAccessLogEventHandler`  
- `ZKSDKEventHandlers/GetRealtimeAccessLogEventHandler`  
- `VirdiSDKEventHandlers/TerminalConnectedEventHandler`  
- `IclockController` (ye masir SaveChanges)

```csharp
await RetryPolicies
    .GetDefaultRetryPolicy<int>(_logger)
    .ExecuteAsync(async () => await _context.SaveChangesAsync());
```

**Yani chi?** Har bar ye policy-e **jadid** sakhte mishe (static factory) → Execute. Stateless — OK. Alternative: singleton pipeline share.

Package: `ACLServer.csproj` → `Polly` + `Directory.Packages.props` version **8.6.5**.

---

## Qesmat 2 — MassTransit retry + circuit breaker (resilience bedune «using Polly»)

Hameja mesl-e Dejban `InfrastructureConfiguration`:

```csharp
cfg.UseMessageRetry(r => r.Exponential(
    retryLimit: 5,
    minInterval: TimeSpan.FromSeconds(1),
    maxInterval: TimeSpan.FromMinutes(5),
    intervalDelta: TimeSpan.FromSeconds(2)
));

cfg.UseCircuitBreaker(cb =>
{
    cb.TrackingPeriod = TimeSpan.FromMinutes(1);
    cb.TripThreshold = 15;
    cb.ActiveThreshold = 10;
    cb.ResetInterval = TimeSpan.FromMinutes(5);
});
```

### Yani chi be zaban-e sade?

**Message retry:** consumer exception → MassTransit message ro ba delay exponential dobare Consume mikone (ta 5). Transient DB/network → shans-e success.

**Circuit breaker:** to ye daqiqe, age fail ziad (≥15 ba shart-e active threshold) → circuit open → consume pause ~5 daghighe → dependency recover.

**Chera inja Polly package nist?**  
MassTransit khodesh in middleware ro dare. Mafhum yeksan-e; implementation joda.

**Ertebat ba Day 20/21/23:**  
Retry + outbox + inbox = se laye. Retry *side-effect* duplicate momken; inbox idempotent = safety.

---

## Qesmat 3 — Day 31 Delay vs Polly

```csharp
await Task.Delay(10000); // ghabl Migrate
context.Database.Migrate();
```

**Farz kon:** DB 3 saniye ba'd ready. 10s sleep = waste.  
**Farz kon:** DB 15 saniye ba'd ready. 10s sleep = hanuz fail.

**Behtar (WORLD + Polly):**

```csharp
// mesal zehni — to code alan nist
await Policy
  .Handle<NpgsqlException>()
  .WaitAndRetryAsync(5, n => TimeSpan.FromSeconds(2))
  .ExecuteAsync(() => { context.Database.Migrate(); return Task.CompletedTask; });
```

Ya Compose `depends_on: service_healthy` (Day 31) + kam retry.

**Yani chi baraye mosahebe?**  
«We currently use a fixed delay before Migrate; a Polly retry or health-gated start would be cleaner.»

---

## Qesmat 4 — HttpClient bedune resilience (gap-e honest)

`AddDccHttpClient` → `AddHttpClient<DccHttpClient>` — BaseAddress set, **bedune** policy handler.

MediaMTX ham `AddHttpClient<MediaMTXHttpClient>()`.

**Farz kon:** DCC restart 2 saniye. Upload document → 1 fail → user error. Ba Polly retry 503 → shayad success.

**WORLD modern .NET 8+:**

```csharp
services.AddHttpClient<DccHttpClient>(...)
    .AddStandardResilienceHandler(); // Microsoft.Extensions.Http.Resilience
```

**Dejban alan:** nist. Gap ≠ «bad» — priority; ama mosahebe midune.

---

## Se dastan — ba ham

### A) Device access log (Polly)

```
Device event → ACL handler → SaveChanges
  fail transient → Polly 2s/4s/8s → success → SignalR hub notify
```

### B) Integration event (MassTransit)

```
Publish → Rabbit → Consumer
  fail → MT exponential retry (5)
  fail storm → circuit open → pause
```

### C) Migrate boot (hack)

```
Start → sleep 10s → Migrate
  (behtar: healthy wait + Polly)
```

---

## Smell-ha (kamel + tozih)

1. **`Handle<Exception>()`** — bug NullReference ham retry mishe → delay bihoode + mask-e bug.  
2. **Policy per call** — OK kuchek; scale → prefer shared pipeline.  
3. **Retry bedune jitter** — hame handler-ha hamzaman 2s/4s/8s → spike.  
4. **Retry write bedune idempotency fikr** — duplicate risk.  
5. **MT retry + non-idempotent consumer** — Day 23.  
6. **Circuit numbers tribal** — 15/10/5min undocumented for ops.  
7. **HttpClient bi-resilience** — transient HTTP fail = user pain.  
8. **Delay 10s** jaygozin-e retry nist.  
9. **Log Warning har retry** — khoob; age storm → log flood (rate limit?).  
10. **Polly v8 package + v7-style API** — confusing for new hire.  
11. **Retry around SaveChanges only** — read queries / gRPC na.  
12. **Catch biruni swallow** — ba'd az exhaust retry, bazi handler-ha LogError va continue — access log gom, app nemimirad (tradeoff).

---

## Debug checklist (sade)

1. Log: `Retry {RetryCount} after {Delay}s` — miad?  
2. Ba'd 3 retry hanuz fail? → root cause DB (lock, disk, connection).  
3. MT: consumer chand bar Consume? → Activity / MT log.  
4. Circuit open? → message pause; dependency health (Day 31).  
5. Duplicate row ba'd retry? → idempotency gap.  
6. Exception type: validation? → nabayad retry shode bashe (smell Handle-all).  
7. HttpClient fail — policy dari? (alan na).  

---

## 25 soal-e mosahebe

1. Polly chie?  
2. Transient vs permanent?  
3. Exponential backoff chie?  
4. Jitter chera?  
5. Circuit breaker states?  
6. Retry vs CB farq?  
7. Timeout koja?  
8. Bulkhead chie?  
9. Fallback mesal?  
10. Idempotency + retry?  
11. Dejban koja Polly sarih dare?  
12. `WaitAndRetryAsync(3, 2^n)` yani chand try?  
13. Chera dor-e SaveChanges ACL?  
14. Smell-e `Handle<Exception>`?  
15. MassTransit UseMessageRetry adad-ha?  
16. TripThreshold 15 yani?  
17. Polly vs MT resilience — fargh API?  
18. HttpClient resilience gap?  
19. `AddStandardResilienceHandler` chie?  
20. Polly v7 vs v8?  
21. Day 31 Delay vs Polly?  
22. Thundering herd?  
23. Retry storm + murde dependency?  
24. Log onRetry chera?  
25. Ideal stack timeout+retry+CB?

---

## Senario-ha (ba tozih-e ravoon)

### A) Deadlock kotah ru SaveChanges

Do device event hamzaman update user. Deadlock → Polly retry → yeki success.  
**Yani:** classic transient.

### B) Column missing (migration faramush)

Har SaveChanges fail → 3 retry → hanuz fail.  
**Yani:** retry permanent error ro «fix» nemikone — faghat delay ezafe. Fix = schema (Day 31 migrationesho).

### C) Rabbit consumer, DB down 2 daghighe

MT retry + shayad CB open. Message nemisuzad (queue). Ba'd recover Consume.  
**Yani:** resilience + durable broker.

### D) DCC restart mid-upload

Bedune HTTP Polly → user error. Ba resilience → retry → OK.  
**Yani:** gap-e proje.

### E) Circuit open, dependency healthy shode

ResetInterval 5min → half-open trial. Age OK → closed.  
**Yani:** automatic recovery path.

---

## Mini lab

1. Open `RetryPolicies.cs` — delay formula hesab kon (2,4,8).  
2. Find 3 call-site `GetDefaultRetryPolicy`.  
3. Read MT `UseMessageRetry` + `UseCircuitBreaker` to Dejban InfrastructureConfiguration.  
4. Grep `AddStandardResilienceHandler` — expect empty.  
5. Compare: Polly ACL vs MT bus — table khodet.  
6. Fekr kon: `Handle<DbUpdateException>()` behtar-e? chera?  
7. Day 31 Delay — ba Polly rewrite zehni.  

---

## Resume

**kutah:**

> Applied resilience patterns across Dejban: explicit Polly exponential retries around EF `SaveChanges` in ACL device/access-log handlers, and MassTransit exponential message retry plus circuit breaker on RabbitMQ consumers; can discuss gaps such as HttpClient resilience and replacing startup sleep with retry.

**bullet-ha:**

- Implemented Polly `WaitAndRetryAsync` (3×, exponential 2ⁿs) with warning logs for transient DB saves in ACLServer  
- Configured MassTransit `UseMessageRetry` (5× exponential) and `UseCircuitBreaker` (trip 15 / reset 5m) across services  
- Distinguished library Polly usage vs bus-level resilience; noted HttpClient without standard resilience handlers  

**skill-ha:** `Polly, Retry, Exponential Backoff, Circuit Breaker, MassTransit Resilience, Transient Fault Handling, EF Core, .NET, Observability`

---

## File-haye mohem

| chi | koja |
|---|---|
| Polly retry factory | `ACLServer/Abstractions/Resilience/RetryPolicies.cs` |
| Call-site mesal | `…/TiamSDKEventHandlers/RealtimeAccessLogEventHandler.cs` |
| Package | `ACLServer.csproj` + `Directory.Packages.props` (Polly 8.6.5) |
| MT retry+CB Dejban | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| MT digar services | `*/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| HttpClient DCC | `Common/Abstractions/Extensions/ServiceCollectionExtensions.cs` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 20 MassTransit | UseMessageRetry / CB — omigh messaging |
| 21–23 Outbox/Inbox | idempotency ba retry |
| 27 gRPC | call sidecar — resilience candidate |
| 30 Serilog | onRetry Warning |
| 31 Health/Docker | Delay vs retry; healthy depends |
| 07 YARP | gateway timeout ≠ Polly app |

---

## Chejori digest koni (ravesh-e sade)

1. WORLD: transient + 5 pattern (25 min) — **farz kon restaurant**  
2. Polly ACL code khat-be-khat (20 min)  
3. MT retry/CB adad-ha (15 min)  
4. Gap HttpClient + Delay (10 min)  
5. Smell Handle-all + idempotency (15 min)  
6. 25 soal seda (20 min)  
7. Resume paragraph (5 min)

---

## Glossary (sade)

| kalame | ma'ni-ye yek khati |
|---|---|
| Transient fault | fail-e movaghat ke shayad khub she |
| Retry | dobare try ba delay |
| Exponential backoff | delay 2^n (ya shabih) |
| Jitter | random ezafe roye delay |
| Circuit breaker | ba'd fail ziad, call-ha cut |
| Open / Closed / Half-open | halat-haye CB |
| Timeout | max wait |
| Bulkhead | limit concurrent |
| Fallback | plan B javab |
| Thundering herd | hame hamzaman retry |
| Resilience pipeline | chain-e policy-ha (Polly v8) |
| `ExecuteAsync` | run delegate zir-e policy |

---

## Deep dive — hesab-e delay ACL

`retryAttempt` to Polly WaitAndRetry mamulan az 1:

| retry # | delay |
|---|---|
| 1 | 2¹ = 2s |
| 2 | 2² = 4s |
| 3 | 2³ = 8s |

Worst-case wait ezafi ≈ 2+4+8 = **14s** + time-e khod-e SaveChanges-ha.

**Chera exponential?**  
Age DB overload-e, sabr-e bishtar = shans-e recover; fixed 100ms × 3 = hanuz storm.

**Jitter mesal:** `2^n + random(0..500ms)` — ACL alan nadare.

---

## Deep dive — Circuit Breaker adad-haye Dejban

| param | meghdar | ma'ni-ye sade |
|---|---|---|
| TrackingPeriod | 1 min | panjere-ye shomaresh fail |
| TripThreshold | 15 | ba'd ~15 fail → open |
| ActiveThreshold | 10 | shart-e «traffic kafi» ghabl trip |
| ResetInterval | 5 min | chand vaght open bemanad |

**Farz kon:** 3 fail to 1 min — trip nemishe (kamtar az 15).  
**Farz kon:** 20 fail sari' — open → consumer-ha message process nemikonan ta reset.

Ops bayad bedune: «message delay 5 min momken» ≠ «message lost» (age queue durable).

---

## Deep dive — Compose-e policy (zehni)

```csharp
// WORLD mesal — na copy-paste be Dejban
var pipeline = new ResiliencePipelineBuilder()
    .AddTimeout(TimeSpan.FromSeconds(10))
    .AddRetry(new RetryStrategyOptions {
        MaxRetryAttempts = 3,
        Delay = TimeSpan.FromSeconds(1),
        BackoffType = DelayBackoffType.Exponential
    })
    .AddCircuitBreaker(new CircuitBreakerStrategyOptions {
        BreakDuration = TimeSpan.FromSeconds(30)
    })
    .Build();

await pipeline.ExecuteAsync(async ct => await SaveAsync(ct));
```

**Yani chi?** API-e Polly v8 / Microsoft.Extensions.Resilience. Dejban ACL hanuz classic `Policy<T>`.

---

## Anti-pattern (ba tozih)

```csharp
// BAD: retry hame chiz
.Handle<Exception>()

// BETTER: transient-ha
.Handle<DbUpdateException>()
.Or<NpgsqlException>(ex => ex.IsTransient)

// BAD: retry POST create bedune idempotency key
// GOOD: upsert / inbox / Id client-generated

// BAD: retry bi-timeout → hung forever ba chand attempt
// GOOD: timeout + retry bounded

// BAD: CB tripThreshold = 1 → har blip circuit open
// GOOD: threshold ba traffic real tune
```

---

## Interview 60s (ravoon)

> «We use Polly in ACLServer to retry EF SaveChanges with exponential backoff when device access logs hit transient DB errors—three retries at 2, 4, and 8 seconds with warning logs. Across services, MassTransit adds exponential message retry and a circuit breaker on the RabbitMQ bus so consumers back off when a dependency is unhealthy. I’d tighten Polly to transient exceptions only, and I’d consider standard HttpClient resilience for DCC calls; startup still uses a fixed delay before Migrate instead of a retry loop.»

---

## Quick self-test

1. Polly package koja? → ACLServer  
2. Chand retry? → 3  
3. Delay formula? → 2^n seconds  
4. Execute chi? → SaveChangesAsync  
5. Handle chi? → Exception (smell)  
6. MT retryLimit? → 5  
7. TripThreshold? → 15  
8. ResetInterval? → 5 min  
9. HttpClient Polly? → no (gap)  
10. Delay 10s = Polly? → no  

---

## Final checklist

- [ ] Transient vs permanent  
- [ ] 5 pattern WORLD  
- [ ] ACL RetryPolicies khat-be-khat  
- [ ] Call-site device handlers  
- [ ] MT retry + CB  
- [ ] Fargh Polly vs MT API  
- [ ] Smells + gaps  
- [ ] Resume 60s  

---

## Extra — «resilience» ra chejori to mosahebe tozih bedi (ravoon)

Begu:

«Resilience yani system transient failure ro *expect* mikone. Retry baraye blip, circuit breaker baraye dependency murde, timeout baraye hang. To proje-ye ma Polly sarih baraye SaveChanges-e ACL hast; baraye message-ha MassTransit hamin idea ro mide. Ideal ine exception filter dorost, idempotent handler, va HTTP client ham policy dashte bashe.»

---

## Extra — Farz kon thundering herd

100 handler AccessLog hamzaman fail (DB failover).  
Bedune jitter: hame 2s ba'ddobare → 100 SaveChanges yekja → DB dobare mirize.

Ba jitter: 2s±random → load pakhsh.

**Yani chi?** Exponential *kafi nist*; jitter = professional touch. ACL gap-e kuchik.

---

## Extra — Retry + SignalR notify

To handler: avval SaveChanges ba Polly, *ba'd* `_deviceHub.Clients.All.RealtimeAccessLog(...)`.

**Chera in tartib?**  
Age avval hub ba'd save fail → UI log neshu midahad ke DB nadare.  
Age save OK ba'd hub fail → DB hast, UI delay — acceptable-tar; SignalR mitune reconnect (Day 26).

---

## Extra — Aya MassTransit az Polly estefade mikone?

Tarikhi: version-haye ghadimi Polly dashhtan. MT 8 khodesh middleware retry/CB dare.  
**Baraye mosahebe:** «conceptually same patterns; our explicit Polly package usage is ACL SaveChanges.»  
Na darke «MassTransit = Polly» — daghigh nist.

---

## Extra — gRPC sidecar (Day 27) + Polly

Call ZK/Tiam/Virdi mitune timeout/network fail. Alan retry sarih mesl-e ACL SaveChanges *hamishe* nist. Candidate: Polly dor-e gRPC call ya deadline + retry transient StatusCode.

**Yani:** resilience checklist per integration boundary (DB, HTTP, gRPC, messaging).

---

## Extra — Monitoring

onRetry Warning → Seq (Day 30).  
Metric ideal: `resilience_retries_total{operation="SaveChanges"}`.  
Alan: log-based. Health (Day 31) ≠ «chand retry dashim» — complementary.

---

## Map — decision tree «bayad retry konam?»

```
Fail shod
  ├─ business / validation / auth → NA, return error
  ├─ transient network/DB → balé, bounded retry + backoff
  ├─ dependency prolonged down → CB open / fail fast + alert
  └─ unknown → log + measure; default conservative (kam retry)
```

---

## Map — Dejban reality

```
ACL device path ──Polly──► SaveChanges
MT consumers ──MT Retry+CB──► Consume
Boot Migrate ──Delay 10s──► (improve: retry)
Http DCC/MediaMTX ──none──► (gap)
```

---

## Lab aha (sade)

1. Break DB short → bebin Warning Retry miad  
2. Wrong schema → 3 retry + Error (waste) → Handle tighten  
3. Stop Rabbit dependency hard → CB behavior (observe pause)  
4. Sketch AddStandardResilienceHandler for DccHttpClient  

---

## What Day 32 is *not*

- Full Polly v8 pipeline migration guide  
- Chaos engineering toolkit  
- YARP gateway retry (separate)  
- Quartz job retry detail (Day 29)  

Focus: **mafhum resilience + Polly ACL + MT twin + gaps**.

---

## Resume keywords (ATS)

`Polly` · `Retry` · `Exponential backoff` · `Circuit breaker` · `Transient fault handling` · `MassTransit` · `Resilience` · `EF Core` · `.NET` · `Observability`

---

## Band-e gharardad-e jadid — chejori in fasl neveshte shode

> **Tozihat ravoontar va sade-tar.** Ghabl code → dastan; ba'd yani chi; ba'd chera; ba'd smell.

In ruz:

- restaurant / device log / thundering herd ba zaban-e adam  
- farq-e honest Polly sarih vs MassTransit  
- gap-ha bedune shame (HttpClient, Delay, Handle-all)  
- jomle-haye mosahebe ke mituni seda koni  

Hamin sabk Day 33+ ham.

---

## 10 jomle ke bayad betuni seda koni (fluency drill)

1. Polly = library-e policy baraye transient fault.  
2. Retry faghat transient; validation na.  
3. Exponential + optional jitter.  
4. Circuit: Closed → Open → Half-open.  
5. ACL: WaitAndRetry 3× dor-e SaveChanges access-log.  
6. Delay 2,4,8 saniye; log Warning.  
7. Smell: Handle\<Exception\> ghaliz-e.  
8. MT: retry 5 exponential + CB trip 15.  
9. Polly package ≠ MT API; mafhum yeksan.  
10. HttpClient resilience hanuz gap-e.

---

## Khoruj-e zehni (ye paragraph baraye khodet)

> Midunam resilience yani expect-e fail-e movaghat. To Dejban Polly sarih to ACL baraye SaveChanges-e device log hast ba exponential retry; roye bus MassTransit hamin fekr ro ba message retry va circuit breaker peiyade karde. Midunam Handle-all va Delay-e Migrate va HttpClient bi-policy smell/gap-an va mitunam to mosahebe behtarishun ro pishnahad bedam.

Age in paragraph mal-e to shod — Day 32 done.

---

*Day 32 tamum. Ba'd: Day 33 — OpenAPI + Scalar (amade). Fehrest: [README.md](./README.md).*
