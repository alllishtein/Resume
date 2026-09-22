# Day 30 — Serilog + Seq + OpenTelemetry

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Observability** yani beduni system to production chi kar mikone bedune debugger. Se sotun: **Logs** (che etefagh oftad), **Traces** (ye request az koja ta koja raft), **Metrics** (chand ta / cheghad tool). To Dejban:

**Serilog** logging-e asosli-e hame service-ha-st — `UseSerilog` + config az `GlobalAppsettings` (Console + **Seq** sink, enrich MachineName/ThreadId/FromLogContext). Har service property-e `Application` dare ta to Seq filter she. `UseSerilogRequestLogging` HTTP request-ha ro log mikone. Dejban ezfe: filter-e noise-e Outbox/Inbox EF, middleware-e **TraceId** to LogContext, va MediatR **RequestLoggingPipelineBehavior** (Module + ErrorOr).

**OpenTelemetry** (ala'an bishtar to **Dejban.Api** via `AddInfrastructure`) tracing misaze: ASP.NET, HttpClient, EF, Redis, Npgsql, MassTransit — export ba **OTLP** (`OTEL_EXPORTER_OTLP_ENDPOINT`, ma'mulan Jaeger). `DiagnosticsConfig.ServiceName = "Dejban.Api"`.

**Seq** UI-e log (port 5341); compose-esh comment-e — local/optional. Jaeger ham optional. In fasl: chera in stack, chejori config mishe, chejori TraceId log ro be trace vasl mikone, va smell-ha.

---

# BAKHSH-E AVAL: WORLD — observability sade

## Chera log-e Console kaf nist?

| Console-only | centralized |
|---|---|
| multi-service = 10 terminal | yek UI (Seq) |
| bere search sakht | filter Application / TraceId |
| restart = gom | persist (age volume) |

Production = sink-haye structured + correlation.

---

## Logs vs Traces vs Metrics

| | soal | mesal |
|---|---|---|
| **Log** | chi gofte shod? | `Processing request CreatePersonnel` |
| **Trace** | path-e request? | Gateway→Dejban→Postgres→Rabbit |
| **Metric** | chand / cheghad? | req/s, p95 latency, error % |

Har se lazem-an. Log bedune TraceId = needle in haystack. Trace bedune log = miduni kond bude, nemiduni chera.

---

## Structured logging

```csharp
// BAD
logger.LogInformation("User " + userId + " created");

// GOOD
logger.LogInformation("User {UserId} created", userId);
```

Property-ha searchable (Seq JSON). Serilog message template hamin olgu ro dare.

---

## Serilog — mafahim

| mafhum | ma'ni |
|---|---|
| **Sink** | koja benevise (Console, File, Seq, …) |
| **Enricher** | property ezafe (MachineName, LogContext) |
| **MinimumLevel** | Information / Warning / … + Override per namespace |
| **LogContext** | scope property (TraceId, Module) |
| **ReadFrom.Configuration** | hame az appsettings |

```csharp
builder.Host.UseSerilog((ctx, cfg) =>
    cfg.ReadFrom.Configuration(ctx.Configuration));
```

---

## Seq chie?

**Seq** (Datalust) = server-e log ba UI-e ghavi baraye structured events. App ba HTTP ingest mifreste (`serverUrl`). Query mesal:

```
Application = "Dejban.Api" and TraceId = "..."
Module = "Personnels" and @Level = "Error"
```

Fargh ba ELK: setup sade-tar baraye .NET teams; ELK ghavitar/gerun-tar.

---

## OpenTelemetry (OTel)

Standard vendor-neutral baraye traces/metrics/logs. To .NET:

```
Activity (span) → TracerProvider → Exporter (OTLP) → Jaeger / Tempo / …
```

Instrumentation packages automatically span misazan baraye ASP.NET, HttpClient, EF, …

**TraceId** = id-e kol-e journey. **SpanId** = yek ghadam. Parent-child = tree.

Propagation: header `traceparent` (W3C) beyn service-ha.

---

## Correlation — gold pattern

```
HTTP request
  → ASP.NET creates Activity (OTel)
  → middleware PushProperty("TraceId", Activity.Current.TraceId)
  → hame Serilog events in request TraceId daran
  → Seq: filter TraceId → dastan-e kamel
  → Jaeger: haman TraceId → timeline spans
```

Bedune in: log-ha orphan, trace-ha bi-matn.

---

## Log levels — rough guide

| level | key |
|---|---|
| Trace/Debug | dev deep |
| Information | business flow normal |
| Warning | recoverable odd |
| Error | failed operation |
| Fatal | process dying |

Override: namespace-haye noisy (EF Outbox poll) → Warning ta Seq por nashe.

---

## PII va amniat-e log

Log nakon: password, full JWT, national id raw, card PAN.  
Smell: `Console.WriteLine` request FullName to production (Dejban GetModuleName — lab).  
Seq auth: ACCEPT_EULA + admin user; ingestion open = risk to LAN.

---

# BAKHSH-E DOVOM: DEJBAN — chejori piade shode

## 1) Config-e moshtarak — GlobalAppsettings

`GlobalAppsettings/globalAppsettings*.json` Serilog-e asosli:

```json
"Serilog": {
  "Using": [ "Serilog.Sinks.Console", "Serilog.Sinks.File", "Serilog.Sinks.Seq" ],
  "MinimumLevel": {
    "Default": "Information",
    "Override": {
      "Microsoft": "Information",
      "Dejban.Modules.Personnels.Infrastructure.Outbox": "Warning",
      "Dejban.Modules.Personnels.Infrastructure.Inbox": "Warning"
      // … hame 8 module Outbox/Inbox → Warning
    }
  },
  "WriteTo": [
    { "Name": "Console" },
    { "Name": "Seq", "Args": { "serverUrl": "http://localhost:5341" } }
  ],
  "Enrich": [ "FromLogContext", "WithMachineName", "WithThreadId" ]
},
"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"
```

**Chera Outbox/Inbox Warning?** Quartz har chand saniye log Information mizad → Seq spam. Override = signal/noise.

Dejban.Api GlobalAppsettings ro ba `PhysicalFileProvider` load mikone (path relative to env). Service-haye dge Serilog-e khodeshun + Properties.

---

## 2) Per-service Application name

```json
// IdentityServer / ACL / DCC / …
"Serilog": {
  "Properties": {
    "Application": "IdentityServer"
  }
}
```

Seq: `Application = "ACLServer"`. Bedune in, hame log-ha mix.

---

## 3) Bootstrap — olgu-ye Program.cs

```csharp
builder.Host.UseSerilog((context, loggerConfig) =>
    loggerConfig.ReadFrom.Configuration(context.Configuration));

// … pipeline
app.UseSerilogRequestLogging();
```

In olgu to Identity, ACL, DCC, RequestTracker, Reporting, Gate, Dejban, … hast.

GrpcServers: `Log.Logger = new LoggerConfiguration().ReadFrom...CreateLogger();` + `UseSerilog()`.

---

## 4) Dejban.Api — filter-e EF outbox noise

```csharp
builder.Host.UseSerilog((context, loggerConfig) =>
    loggerConfig.ReadFrom.Configuration(context.Configuration)
    .Filter.ByExcluding(logEvent =>
        logEvent.Properties.TryGetValue("commandText", out var commandText) &&
        commandText != null &&
        (commandText.ToString().Contains("OutboxState") ||
         commandText.ToString().Contains("InboxState") ||
         commandText.ToString().Contains("OutboxMessage"))));
```

Hatta age level Information bashe, SQL-haye MT/EF outbox state az log kharej mishan. Do-layer noise control: MinimumLevel Override + Filter.

---

## 5) TraceId → Serilog (middleware)

```csharp
// LogContextTraceLoggingMiddleware
string? traceId = Activity.Current?.TraceId.ToString();
using (LogContext.PushProperty("TraceId", traceId))
{
    await next.Invoke(context);
}
```

```csharp
app.UseExceptionHandler();
app.UseLogContext();              // TraceId
app.UseSerilogRequestLogging(); // HTTP timing/status
app.UseAuthentication();
```

`Enrich: FromLogContext` → hame sink-ha TraceId migiran.

**Note:** age Activity.Current null bashe (OTel off / ghabl az create), TraceId null — smell edge.

---

## 6) MediatR RequestLoggingPipelineBehavior

```csharp
Activity.Current?.SetTag("request.module", moduleName);
Activity.Current?.SetTag("request.name", requestName);

using (LogContext.PushProperty("Module", moduleName))
{
    logger.LogInformation("Processing request {RequestName}", requestName);
    var result = await next();
    if (result.IsError)
        using (LogContext.PushProperty("Error", result.Errors, true))
            logger.LogError("Completed request {RequestName} with error", requestName);
    else
        logger.LogInformation("Completed request {RequestName}", requestName);
}
```

Yani chi?

- Har command/query ErrorOr → start/complete log  
- Module az namespace (`…Modules.Personnels…`)  
- Error-ha destructure be Seq  
- Tag ru-ye **span** baraye Jaeger filter  

**Smell:** `Console.WriteLine` dakhel-e `GetModuleName` — debug leftover; prod noise/PII path risk.

---

## 7) ProblemDetails + requestId

```csharp
context.ProblemDetails.Extensions.Add(
    "requestId", context.HttpContext.TraceIdentifier);
```

FE/error UI mitune requestId neshun bede; Ops ba TraceIdentifier (ASP.NET) search — **deghat:** TraceIdentifier ≠ hatman OTel TraceId (fargh mumkene). Ideal: ham TraceId OTel be client bargardune. Gap-e honest.

---

## 8) OpenTelemetry — Dejban.Common.Infrastructure

```csharp
services
    .AddOpenTelemetry()
    .ConfigureResource(resource => resource.AddService(serviceName))
    .WithTracing(tracing =>
    {
        tracing
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddEntityFrameworkCoreInstrumentation()
            .AddRedisInstrumentation()
            .AddNpgsql()
            .AddSource(MassTransit.Logging.DiagnosticHeaders.DefaultListenerName);

        tracing.AddOtlpExporter(); // mikhune OTEL_EXPORTER_OTLP_ENDPOINT
    });
```

`serviceName` az `DiagnosticsConfig.ServiceName` → `"Dejban.Api"`.

| instrumentation | chi cover |
|---|---|
| AspNetCore | incoming HTTP spans |
| HttpClient | outbound HTTP (DCC, …) |
| EF Core | queries |
| Redis | cache calls |
| Npgsql | raw SQL/ADO |
| MassTransit source | bus publish/consume |

**Metrics (`WithMetrics`)** to in snippet nist — tracing-first. Packages OTel to `Dejban.Common.Infrastructure.csproj` hastan.

Service-haye dge ke `AddInfrastructure`-e Dejban nadaran, **OTel full wire nist** — Serilog daran, distributed trace kamtar. Architecture smell / roadmap.

---

## 9) Seq + Jaeger to Docker

`docker-compose*.yml` — service-haye `seq` va `jaeger` **comment**:

```yaml
# seq: datalust/seq  ports 5341, 8081
# jaeger: all-in-one  4317 OTLP, 16686 UI
```

Yani: developer local Seq/Jaeger nasb mikone ya uncomment. Config default `localhost:5341` / `4317` hamin farz ro dare.

---

## 10) Packages (csproj)

Hame microservice-haye asosli:

- `Serilog.AspNetCore`  
- `Serilog.Sinks.Console` / `File` / `Seq`  

Dejban Common Infrastructure ezfe:

- `OpenTelemetry.*` (Hosting, AspNetCore, Http, EF, Redis, OTLP)  
- `Npgsql.OpenTelemetry`  

---

## Flow — ye CreatePersonnel (zehni)

```
Browser → YARP → Dejban.Api
  Activity start (AspNetCore) TraceId=T
  UseLogContext → Serilog TraceId=T
  UseSerilogRequestLogging → HTTP log
  MediatR behavior → Module=Personnels, Processing…
  EF SaveChanges → EF span child
  Outbox insert
  Completed request
  (ba'd) Quartz outbox → MassTransit span → Rabbit
Jaeger: tree T
Seq: Application=Dejban.Api TraceId=T Module=Personnels
```

---

## Smell-ha

1. Seq/Jaeger compose comment — onboarding «chera log nemire Seq?»  
2. Console.WriteLine to GetModuleName  
3. TraceIdentifier vs OTel TraceId to ProblemDetails  
4. OTel faghat Dejban path — digar services weak  
5. No WithMetrics yet  
6. File sink to Using list, WriteTo File hamishe nist (depends env)  
7. Seq ingestion bedune auth to LAN  
8. Log level Information + high traffic = cost  
9. Enrich ThreadId noisy  
10. Filter ByExcluding string Contains — fragile  
11. Activity.Current null → TraceId null logs  
12. PII to Error property destructure  

---

## Debug checklist

1. Seq up? `http://localhost:5341`  
2. Application property dorost?  
3. Outbox spam? Override Warning  
4. TraceId to event? UseLogContext order ghabl SerilogRequestLogging  
5. Jaeger UI `16686` — service Dejban.Api  
6. OTEL endpoint reachable?  
7. ErrorOr fail → LogError + Error property  
8. Multi-service: Propagation — HttpClient instrumentation automatic for outbound  

---

## 25 soal-e mosahebe

1. Observability se sotun?  
2. Structured logging?  
3. Serilog sink?  
4. Seq vs ELK?  
5. LogContext?  
6. Enricher?  
7. MinimumLevel Override chera?  
8. OTel chie?  
9. TraceId vs SpanId?  
10. OTLP?  
11. Chejori log ro be trace vasl mikoni?  
12. UseSerilogRequestLogging?  
13. Activity.SetTag?  
14. Chera outbox log Warning?  
15. ProblemDetails requestId?  
16. Instrumentation list Dejban?  
17. Propagation beyn services?  
18. PII to log?  
19. Metrics vs traces?  
20. Sampling (concept)?  
21. Dashboard Seq query mesal?  
22. Fargh ILogger ba Log.Logger?  
23. Filter ByExcluding?  
24. Multi-service Application property?  
25. Chejori OTel be Identity ezafe koni?

---

## Senario-ha

### A) 500 az FE  
ProblemDetails requestId → Seq search → TraceId → stack/Module → Jaeger span EF slow.

### B) Seq por az Beginning to process outbox  
Override Warning — noise kam.

### C) Jaeger empty  
OTEL endpoint down / compose jaeger comment / exporter fail silent.

### D) Log bedune TraceId  
Middleware order / Activity null.

### E) Cross-service  
Dejban HttpClient to DCC — HttpClient instrumentation continue trace (age DCC OTel dashte bashe; alan DCC bishtar log-only).

---

## Mini lab

1. Uncomment/run Seq — create personnel — filter Application + Module  
2. Breakpoint LogContextTraceLoggingMiddleware — TraceId  
3. Force ErrorOr fail — Seq Error property  
4. Run Jaeger — hit API — bebin AspNetCore + EF spans  
5. Temporary remove Override Outbox — spam bebin  
6. Find Filter ByExcluding OutboxMessage  

---

## Resume

**kutah:**

> Standardized structured logging with Serilog across microservices (Console + Seq, shared GlobalAppsettings levels/enrichers), correlated request logs via TraceId LogContext and MediatR module logging, and enabled OpenTelemetry tracing on Dejban.Api (ASP.NET, EF, Redis, Npgsql, MassTransit) exporting OTLP for Jaeger.

**bullet-ha:**

- Configured Serilog from shared GlobalAppsettings with Seq sink and per-module outbox/inbox level overrides  
- Enriched logs with TraceId middleware and Module/Error properties in MediatR pipeline  
- Wired OpenTelemetry tracing instrumentations + OTLP exporter keyed by service name `Dejban.Api`  
- Reduced EF/MassTransit outbox noise with Serilog filters and minimum-level overrides  

**skill-ha:** `Serilog, Seq, OpenTelemetry, OTLP, Distributed Tracing, Structured Logging, ASP.NET Core, Observability, Jaeger, Log Correlation`

---

## File-haye mohem

| chi | koja |
|---|---|
| Global Serilog + OTEL URL | `GlobalAppsettings/globalAppsettings*.json` |
| UseSerilog / filter | `Dejban.Api/Program.cs` |
| TraceId middleware | `Dejban.Api/Middleware/LogContextTraceLoggingMiddleware.cs` |
| Request logging behavior | `Dejban.Common.Application/Behaviors/RequestLoggingPipelineBehavior.cs` |
| OTel registration | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| Service name | `Dejban.Api/OpenTelemetry/DiagnosticsConfig.cs` |
| Seq/Jaeger compose | `docker-compose*.yml` (commented) |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 05 Pipeline | UseSerilog / middleware order |
| 10 MediatR | RequestLoggingPipelineBehavior |
| 11 ErrorOr | error logged as property |
| 20–23 Messaging | MassTransit OTel source; outbox noise |
| 25 Redis | Redis instrumentation |
| 29 Jobs | job logs need Application + correlation |
| 31 Health | digar sotun ops |

---

## Chejori digest koni

1. Logs/Traces/Metrics (10 min)  
2. GlobalAppsettings Serilog (15 min)  
3. TraceId middleware + behavior (20 min)  
4. AddOpenTelemetry block (20 min)  
5. Lab Seq + Jaeger (30 min)  
6. 25 soal (20 min)

---

## Glossary

| kalame | ma'ni |
|---|---|
| Serilog | structured logger .NET |
| Sink | output destination |
| Seq | log server + UI |
| Enricher | auto property |
| LogContext | async-local scope props |
| OpenTelemetry | observability standard |
| OTLP | export protocol |
| TraceId | id-e journey |
| Span | yek unit of work |
| Instrumentation | auto-span library |

---

## Deep dive — order-e middleware

```
ExceptionHandler → LogContext(TraceId) → SerilogRequestLogging → Auth → Tenant → Endpoints
```

Age SerilogRequestLogging ghabl az LogContext bashe, request log momkene TraceId nadashte bashe (bastegi be timing Activity). Dejban LogContext ghabl — khub.

---

## Deep dive — OTLP endpoint env

`AddOtlpExporter()` standard env vars:

- `OTEL_EXPORTER_OTLP_ENDPOINT`  
- optional protocol/headers  

GlobalAppsettings value `http://localhost:4317` = Jaeger gRPC OTLP. Age exporter fail, app ma'mulan edame mide — traces gom, log mimune.

---

## Deep dive — Sampling (concept)

100% trace to prod = gerun. Head-based sampling (1%) common. Dejban default exporter bedune custom sampler to code — ba'dan `AlwaysOn` vs `TraceIdRatioBased`. Interview: tradeoff completeness vs cost.

---

## Anti-pattern-ha

```csharp
// BAD
Log.Information($"User {user.Password} login"); // PII + string interp

// GOOD
Log.Information("User {UserId} login succeeded", user.Id);
```

```csharp
// BAD: faghat Console.WriteLine debug
// GOOD: ILogger + level
```

```csharp
// BAD: har Outbox tick Information
// GOOD: Warning override ya log only on error/batch>0
```

---

## Interview 60s

> «We use Serilog everywhere with shared config shipping to Seq, enrich logs with TraceId from the current Activity, and log each MediatR request with module context. On Dejban.Api we enable OpenTelemetry tracing for ASP.NET, EF, Redis, Npgsql and MassTransit, exporting OTLP so we can follow a request in Jaeger and the same TraceId in Seq.»

---

## Quick self-test

1. Seq default URL? → localhost:5341  
2. OTLP default? → localhost:4317  
3. ServiceName Dejban? → Dejban.Api  
4. TraceId az koja? → Activity.Current  
5. Module property koja? → RequestLoggingPipelineBehavior  
6. Outbox log level? → Warning override  
7. UseSerilogRequestLogging chi? → HTTP request log  
8. Metrics wired? → na (tracing only snippet)  
9. Compose Seq? → commented  
10. Filter OutboxMessage? → ByExcluding commandText  

---

## Final checklist

- [ ] Serilog config global + Application  
- [ ] Seq role  
- [ ] TraceId correlation  
- [ ] MediatR logging behavior  
- [ ] OTel instrumentations + OTLP  
- [ ] noise control outbox  
- [ ] resume  

---

## Extra — File sink

`Using` list File dare; WriteTo to Development sample bishtar Console+Seq. File baraye air-gap / forensic. Rolling file policy to appsettings env-specific ezafe mishe.

---

## Extra — MassTransit + OTel

`AddSource(MassTransit.Logging.DiagnosticHeaders.DefaultListenerName)` span-haye publish/consume. Ba TraceId, zincir HTTP→outbox→bus visible. Age consumer service OTel nadare, tree nime-kare — hamin dalil roadmap baraye Identity/ACL.

---

## Extra — ILogger\<T\> vs static Log

DI `ILogger<T>` → category = type name (filter-friendly). Static `Log.Logger` early bootstrap / GrpcServer. Prefer ILogger to app code.

---

## Extra — health vs observability

Health Checks (Day 31) = «zende-am?» boolean. Observability = «chon raftam / chera kond». Complementary.

---

## Map — log event anatomy (Seq)

```
@Timestamp
@Level = Information
@Message = Processing request CreatePersonnelCommand
Application = Dejban.Api
TraceId = 4bf9…
Module = Personnels
MachineName = …
ThreadId = …
```

---

## Map — span tree (Jaeger)

```
Dejban.Api: POST /api/...
  ├─ MediatR tags request.module=Personnels
  ├─ EF SaveChanges
  ├─ Npgsql SELECT/INSERT
  └─ (later) MassTransit publish …
```

---

## Decision — che chizi log konam?

| event | level |
|---|---|
| Handler start/end | Information |
| Validation fail | Warning/Information |
| Unexpected exception | Error |
| Outbox empty tick | Debug/Warning suppress |
| Auth fail | Warning (+ reason code) |
| Every SQL | faghat Debug temporary |

---

## Lab aha

1. Seq query TraceId az yek 500  
2. Jaeger same id  
3. Spam outbox ba Override off  
4. Console.WriteLine GetModuleName to output  
5. Stop Seq — app still runs (sink fail resilient-ish)  

---

## What Day 30 is *not*

- Full ELK / Grafana Loki setup  
- Metrics dashboards Prometheus (ba'd)  
- FE RUM / browser tracing  
- Complete OTel on every microservice (honest gap)  

Focus: **Serilog+Seq practice + Dejban OTel tracing + correlation**.

---

## Resume keywords (ATS)

`Serilog` · `Seq` · `OpenTelemetry` · `OTLP` · `distributed tracing` · `structured logging` · `log correlation` · `Jaeger` · `ASP.NET Core` · `observability`

---

## Gap-e roadmap (honest to mosahebe)

1. Wire OTel to Identity/ACL/DCC mesle Dejban  
2. WithMetrics + Prometheus  
3. Remove Console.WriteLine az GetModuleName  
4. Return OTel TraceId to ProblemDetails  
5. Uncomment Seq/Jaeger to compose + docs  

Inha weakness nistan age beduni — neshun mide ownership.

---

## Extra — performance

Serilog async sink / batch to Seq. Synchronous Console to hot path = latency. RequestLogging har request = OK. EF instrumentation overhead — accept for ops.

---

## Extra — multi-tenant to logs?

Tenant/SiteId enrich optional — Dejban TenantContext hast (Day 16) ama LogContext Push SiteId standard nist to middleware. Gap: filter logs by site. Easy win: PushProperty SiteIds az TenantContext.

---

## Extra — Serilog request logging fields

`UseSerilogRequestLogging` be default method, path, status, elapsed ro minevise. Mituni `options.EnrichDiagnosticContext` ezafe koni (UserId, SiteId). Dejban default kafi-e; enrichment asli TraceId + Module-e.

---

## Extra — dual write log + trace

Yek ErrorOr fail:

1. LogError ba Error property → Seq  
2. Activity tags / status → Jaeger span error  

Ops: az Seq TraceId copy → Jaeger search. In «two pane debugging» standard-e.

---

## Extra — GrpcServer logging

ZK/Tiam/Virdi GrpcServers Serilog CreateLogger + Console (+ File to config). Seq Using list daran. OTel gRPC instrumentation to in process-ha separate effort — device sidecar logs bishtar local/Seq.

---

## Extra — GlobalExceptionHandler

Unhandled exception → ProblemDetails + log Error (pipeline Day 05). requestId ezafe mishe. Correlation: TraceId to LogContext age middleware ghabl resid.

---

## Senario F — «log miad Console, Seq na»

1. Seq down / port 5341  
2. WriteTo Seq arg URL eshtebah (Docker service name vs localhost)  
3. Firewall  
4. Using sink assembly load fail  

App crash nemikone ma'mulan — faghat event lose.

---

*Day 30 tamum. Ba'd: Day 31 — Health Checks + Docker + EF migration workflow (amade). Fehrest: [README.md](./README.md).*
