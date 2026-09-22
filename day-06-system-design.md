# Day 06 — System Design

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

System design yani "in system ra chejori misazi ke scale kone, down nayre, va fast bashe?" Interview-e senior jaye in soal-e: "Design a URL shortener" ya "Design a chat system." Vali ghabl az in ke system-e dige-i design koni, bayad betuni system-e **khodet** ra tozih bedi. In fasl hame-ye component-haye Dejban stack ra az did-e system design mibine: API Gateway, 7 microservice, modular monolith, async messaging, caching, storage, observability, deployment. Ba'd concept-haye World ra yad migiri ke to mosahebe betuni harf bezani.

---

# BAKHSH-E AVAL: WORLD — System Design to donya

## Chera system design mohem-e?

Senior interview 2 bakhsh dare: coding + system design. Coding mige "mituni code bezani?" System design mige "mituni fikr koni?" Scale, failure, tradeoff, cost — ina ra code-e LeetCode neshun nemide.

Soal-e typical:
- "Design Twitter/Instagram feed"
- "Design a URL shortener"
- "Design a chat system"
- "Design your current system for 10x traffic"

Baraye javab dadan: **requirement** → **high-level design** → **deep dive** → **tradeoff**.

---

## Concept-haye paye

### Scalability

System mikhad bishtar traffic handle kone. Do rah:

- **Vertical scaling (scale up)** — server-e bozorg-tar. CPU/RAM bishtar. Sade, vali limit dare va geran-e.
- **Horizontal scaling (scale out)** — server-e bishtar. Load balancer jelov. Sakht-tar vali unlimited-e.

Stateless service-ha (JWT auth, na session-e server-side) horizontal scale asan-e. Dejban JWT-e → stateless → scale-out mumken.

### Availability

System che darsad-e vaght bala-st?

| nines | downtime/year |
|---|---|
| 99% (2 nines) | 3.65 ruz |
| 99.9% (3 nines) | 8.76 sa'at |
| 99.99% (4 nines) | 52.6 daghighe |
| 99.999% (5 nines) | 5.26 daghighe |

Baraye availability: redundancy (chand instance), failover (automatic switch), health check, graceful degradation.

### Consistency

Hame-ye node-ha haman data ra mibinand?

- **Strong consistency** — ba'd az write, hame haman chiz ra mikhanand. Postgres default.
- **Eventual consistency** — ba'd az write, ye muddat ta'khir, bad hame consistent mishan. Redis cache, message queue, read-model copy.

Dejban: write-ha strongly consistent (Postgres). Read-model copy-haye beyn-e module-ha **eventually consistent** (outbox → inbox → upsert).

### Latency vs throughput

- **Latency** — zamaan-e ye request (ms). User experience.
- **Throughput** — tedad-e request per second. System capacity.

Trade-off: batch processing throughput ra bala mibare, latency ra bala mibare. Real-time latency ra kam mikone, throughput ra kam mikone.

---

## CAP Theorem

Ye distributed system faghat **do ta** az in 3 ta ra mitone:

- **C**onsistency — hame haman data
- **A**vailability — har request javab migire
- **P**artition tolerance — network partition ra tahammol mikone

To practice: P hamishe lazem-e (network fail mishe). Pas entekhab beyn-e **CP** (consistency, partition-tolerant — masalan Postgres) va **AP** (available, partition-tolerant — masalan Cassandra).

Dejban: **CP**. Postgres strongly consistent. Age DB down bashe, service 503/502 mide (na stale data).

**Mosahebe tip:** CAP oversimplified-e. Begu: "CAP baraye understanding-e khoob-e, vali real systems trade-off-e granular-tar-an. Masalan cache AP-e, DB CP-e, mix mikonim."

---

## Communication patterns

### Synchronous — request/response

Client wait mikone ta server javab bede. HTTP REST, gRPC.

| | REST (HTTP) | gRPC |
|---|---|---|
| format | JSON text | Protobuf binary |
| speed | medium | fast (binary, HTTP/2 multiplex) |
| contract | OpenAPI (optional) | `.proto` file (required) |
| browser | bale | na (gRPC-Web faqat) |
| streaming | SSE yek-tarafe | bidirectional |
| debug | asan (curl, DevTools) | sakht (binary) |

**Kei REST, kei gRPC?** REST baraye public API (browser, mobile). gRPC baraye **internal service-to-service** ke performance mohem-e (device SDK, real-time sync).

### Asynchronous — message queue

Producer message mifreste be queue, consumer mikhoone. Producer wait **nemikone**.

| | RabbitMQ | Kafka |
|---|---|---|
| model | message queue | event log |
| delivery | at-least-once | at-least-once / exactly-once |
| ordering | per-queue | per-partition |
| replay | na (consumed = gone) | bale (offset reset) |
| use case | task dispatch, integration events | event sourcing, analytics, CDC |

**Kei sync, kei async?** Sync vaghti natije **hamin alan** lazem-e (login, list query). Async vaghti "karam ra bokon, man montazer nistam" (send email, sync device, update read-model).

---

## API Gateway pattern

Yek entry point baraye hame-ye service-ha. Client faghat gateway ra midone.

Masooliat-ha:
- **Routing** — request be kodom service
- **Auth** — JWT validation, token revoke
- **Rate limiting** — per-IP, per-route
- **CORS** — cross-origin policy
- **TLS termination** — HTTPS decode
- **Logging/monitoring** — trace har request

Alternative-ha: nginx, Envoy, Kong, AWS ALB, YARP.

**BFF (Backend for Frontend)** — gateway-e khaas baraye har client (web, mobile). Gateway-e faghat yek client ra serve mikone va response ra aggregate/transform mikone. Dejban **BFF nist** — transparent proxy-e.

---

## Caching strategies

| strategy | chi | che vaght |
|---|---|---|
| **Cache-aside** | app aval cache check, miss → DB, set cache | read-heavy, tolerance baraye stale |
| **Write-through** | write be cache + DB hamzaman | consistency mohem |
| **Write-behind** | write be cache, async flush be DB | write-heavy |
| **Read-through** | cache khodesh az DB load mikone | transparency |

**Cache invalidation** — "hardest problem in CS." TTL (zamaan-e expire), event-based (write → invalidate), version key.

**Where to cache:**
- **L1 — in-memory** (IMemoryCache, process-level, fast, na shared)
- **L2 — distributed** (Redis, shared, slower than L1)
- **HybridCache** (.NET 9+) — L1 + L2. Aval memory, miss → Redis, miss → DB.

---

## Database choices

| type | mesal | khoob baraye |
|---|---|---|
| Relational (SQL) | PostgreSQL, MySQL | structured data, ACID, joins |
| Document | MongoDB | flexible schema, nested |
| Key-value | Redis | cache, session, simple lookup |
| Wide-column | Cassandra | write-heavy, time-series |
| Graph | Neo4j | relationship-heavy (social) |
| Object store | MinIO, S3 | files, images, video |
| Search | Elasticsearch | full-text search, logs |
| Time-series | TimescaleDB, InfluxDB | metrics, IoT |

**Polyglot persistence** — har use case DB-e khodesh:
- Transactions → Postgres
- Cache → Redis
- Files → MinIO/S3
- Events → RabbitMQ (va eventually Kafka baraye replay)

---

## Event-driven architecture

Service-ha mostaghim sohbat nakonan. Event publish mikonan, interested party-ha subscribe.

```
PersonnelService → "PersonnelCreated" → RabbitMQ → VisitorService (copy read-model)
                                                  → ACLService (sync to device)
                                                  → RequestTracker (update workflow)
```

**Maziat:** loose coupling, independent deployment, scale-out consumer.
**Moshkel:** eventual consistency, debugging-e sakht (distributed trace lazem), ordering, idempotency.

---

## Microservices vs Monolith

| | Monolith | Microservices | Modular monolith |
|---|---|---|---|
| deploy | 1 unit | N unit | 1 unit, N module |
| DB | 1 | N (per-service) | 1 DB, N schema |
| team | 1 | N | 1 (ya feature team) |
| complexity | code | infrastructure | code (moderate) |
| network | na | bale (latency, failure) | na (in-process) |
| scale | kole app | per-service | kole app (ya split later) |

**Modular monolith** = best of both: module boundary-e tight (mesle microservice), deploy-e sade (mesle monolith), split-e ba'di asan.

---

## Observability — 3 pillar

| pillar | chi | tool |
|---|---|---|
| **Logs** | event-haye text. "User X logged in at T" | Serilog, Seq, ELK |
| **Metrics** | adad-haye zamani. CPU, request count, p99 latency | Prometheus, Grafana |
| **Traces** | ye request az entry ta exit, cross-service | OpenTelemetry, Jaeger |

**Structured logging** — log ra JSON benevis, na text-e flat. Search/filter asan.

**Distributed tracing** — ye `TraceId` az Gateway ta DB. Kond-i ra peida kon.

---

## Common system design interview questions

1. **Design a URL shortener** — hashing, DB, cache, redirect
2. **Design Twitter feed** — fan-out on write vs read, cache timeline
3. **Design a chat system** — WebSocket, message store, presence
4. **Design a file storage** — chunking, dedup, CDN, metadata
5. **Design a rate limiter** — token bucket, sliding window, distributed
6. **Design a notification system** — push, email, SMS, queue, template
7. **Design a search engine** — inverted index, ranking, autocomplete
8. **Design an e-commerce checkout** — payment, inventory lock, saga

**Framework baraye javab:**
1. **Requirements** — functional + non-functional (scale, latency, availability)
2. **Estimation** — users, requests/sec, storage, bandwidth
3. **High-level** — boxes + arrows (client, LB, service, DB, cache, queue)
4. **Deep dive** — database schema, API design, caching, failure handling
5. **Tradeoffs** — why this choice, what's the cost

---

## Chizayi ke to donya hastan vali inja kam/nistan

- **CDN** (Content Delivery Network) — static asset-ha (JS, CSS, image) ra nazdik-e user cache kon. CloudFront, Cloudflare.
- **Service mesh** (Istio, Linkerd) — sidecar proxy baraye mTLS, traffic control, observability. Kubernetes-native.
- **Kubernetes** — container orchestration. Auto-scale, self-heal, rolling deploy.
- **Saga pattern** — distributed transaction across services. Choreography (event) vs orchestration (command).
- **Event sourcing** — state ra az event-ha rebuild kon, na snapshot.
- **CQRS + separate read DB** — write be Postgres, read az Elasticsearch/Redis.
- **Blue-green / canary deployment** — zero-downtime deploy.
- **Sharding** — DB ra horizontal split kon (user_id % N).
- **Read replicas** — Postgres standby baraye read. Write be primary.

---

# BAKHSH-E DOVOM: DEJBAN — System Design to in proje

## Architecture overview

```
┌─────────────────────────────────────────────────────┐
│                    CLIENTS                           │
│  Browser (Next.js SPA)  │  Device (ZK/Tiam/Virdi)  │
│  Kiosk (Gate)           │  Camera (PlateReader)     │
└───────────────┬─────────────────────┬───────────────┘
                │ HTTPS               │ gRPC
        ┌───────▼──────┐     ┌───────▼──────────┐
        │  API Gateway  │     │  gRPC Servers    │
        │  (YARP 2.3)   │     │  ZK/Tiam/Virdi   │
        └───────┬───────┘     └───────┬──────────┘
                │ HTTP                │
    ┌───────────┼───────────────┬─────┘
    ▼           ▼               ▼
┌────────┐ ┌────────┐ ┌─────────────┐
│Identity│ │Dejban  │ │ ACLServer   │
│Server  │ │(modular│ │             │
│        │ │monolith│ │             │
└───┬────┘ └───┬────┘ └──────┬──────┘
    │          │              │
    ▼          ▼              ▼
┌──────────────────────────────────────┐
│         PostgreSQL (7 DBs)           │
│   identity│dejban│acl│dcc│rt│rp│gate │
└──────────────────────────────────────┘
    ┌──────┐  ┌──────────┐  ┌───────┐
    │Redis │  │RabbitMQ  │  │MinIO  │
    │cache │  │events    │  │files  │
    └──────┘  └──────────┘  └───────┘
```

**14 runnable service**, **8 Dockerized**, **7 PostgreSQL database**, **1 Redis**, **1 RabbitMQ**, **1 MinIO**.

---

## Communication — 3 pattern

### 1. HTTP sync — YARP Gateway

Browser → Gateway (HTTPS) → Service (HTTP internal).

60+ YARP route, 9 cluster. Auth, CORS, rate limit, token revoke hame roye Gateway (Day 01).

### 2. gRPC sync — device SDK

ACLServer → ZKGrpcServer/TiamGrpcServer/VirdiGrpcServer.

8 ta `.proto` file to `Common/Protos/`. Binary, fast, bidirectional streaming baraye device event-ha.

```protobuf
service SSM {
  rpc GetACLServicesStatus(GetACLServicesStatusRequest) returns (GetACLServicesStatusResponse);
  rpc StreamServiceLogs (StreamServiceLogsRequest) returns (stream LogEntry);
}
```

ACLServer gRPC **client**-e:

```csharp
_channel = GrpcChannel.ForAddress(grpcSettings.ServerAddress);
_client = new ZKService.ZKServiceClient(_channel);
```

Chera gRPC baraye device? Performance-e binary, streaming baraye real-time event, va contract-e strict `.proto`.

### 3. Async — MassTransit + RabbitMQ

Event-driven integration beyn-e service-ha.

**RabbitMQ** Docker container. Pre-declared queue-ha to `definitions.json`:

```json
"queues": [
    { "name": "site-created", "durable": true },
    { "name": "personnel-created", "durable": true },
    { "name": "visitor-created", "durable": true },
    ...
]
```

**MassTransit** roye RabbitMQ:

```csharp
services.AddMassTransit(x =>
{
    x.AddEntityFrameworkOutbox<ApplicationDbContext>(o => {
        o.UsePostgres();
        o.UseBusOutbox();
    });
    x.AddConsumer<PersonnelCreatedConsumer>();
    x.AddConsumer<VisitorCreatedConsumer>();
    // 20+ consumer
    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.UseMessageRetry(r => r.Exponential(retryLimit: 5, ...));
        cfg.UseCircuitBreaker(cb => { cb.TripThreshold = 15; ... });
        cfg.ConfigureEndpoints(context);
    });
});
```

**Do jur outbox:**

1. **MassTransit EF Outbox** — IdentityServer, ACLServer, RequestTracker. Built-in MassTransit: event ba'd az SaveChanges reliable publish mishe.
2. **Custom outbox/inbox** — Dejban modules (Visitors, Personnels, ...). Quartz job `ProcessOutboxJob` event ra az table mikhone va publish mikone. `ProcessInboxJob` receive mikone va handler ra seda mizane. Idempotent (Day 05 decorator).

**Flow-e ye event:**

```
PersonnelService SaveChanges → outbox table (same tx)
    → ProcessOutboxJob (Quartz, every N sec) → MassTransit publish → RabbitMQ
    → ACLServer consumer → sync user to device
    → VisitorModule inbox → ProcessInboxJob → upsert personnel copy
```

---

## Data storage

### PostgreSQL — database-per-service

7 ta DB, har microservice joda. Dejban 1 DB ba 8 schema (modular monolith — Day 03).

| Service | DB | Port (dev) |
|---|---|---|
| IdentityServer | payamgostar_identity | 18001 |
| RequestTracker | payamgostar_requesttracker | 18002 |
| ACLServer | payamgostar_aclserver | 18003 |
| Dejban | payamgostar_dejban | 18004 |
| DCC | payamgostar_dcc | 18005 |
| Reporting | payamgostar_reporting | 18006 |
| GateServer | payamgostar_gateserver | 18007 |

**Beyn-e service-ha: hich FK / join cross-DB.** Integration = event.
**Dakhele Dejban: schema joda, DbContext joda.** Join cross-schema **momken** vali mamnoo' (convention). Copy read-model.

Connection pooling: `NpgsqlDataSource` singleton per service.

### Redis — cache + token blacklist

Yek Redis baraye hame service-ha.

| use case | mechanism |
|---|---|
| Token blacklist (revoke) | `HybridCache.SetAsync("revoked:{jti}", true, TTL)` |
| Report access ticket | `IDistributedCache.SetStringAsync(ticket, JSON, 5min)` |
| General cache | `HybridCache` (L1 memory + L2 Redis) |

**HybridCache** (.NET 9+):
- Aval check-e in-memory (nanosecond)
- Miss → check Redis (millisecond)
- Miss → DB query + set both
- Stampede protection built-in (yek request DB mizane, baghie wait)

Token revoke: logout → `revoked:{jti}` be Redis ba TTL = token expiry. Har request → middleware check → revoked? → 401.

### MinIO — S3-compatible object storage

```json
"Storage": {
    "Provider": "S3",
    "S3": {
        "Endpoint": "http://minio:9000",
        "Bucket": "dcc-files",
        "ForcePathStyle": true,
        "PresignTtlSeconds": 300
    }
}
```

DCC service file ra to MinIO zakhire mikone. `IFileStorage` interface: `S3FileStorage` (production) vs `LocalFileStorage` (fallback). AWS SDK client.

Public files: YARP `/files/{path}` → DCC → MinIO.

### MediaMTX — video streaming

RTSP/WebRTC baraye camera live view. Docker container, port 8554/8888.

---

## Scalability

### Horizontal scale potential

Stateless service-ha (JWT auth) → scale-out ready. Vali alan **single instance** per service.

Bottleneck-ha baraye scale:

| component | issue |
|---|---|
| Inbox `FOR UPDATE` | multi-instance → serialize (na SKIP LOCKED) |
| Channel SSE singleton | 1 reader, multi-instance → lost events |
| SignalR in-memory | multi-instance → Redis backplane lazem |
| Quartz in-memory store | multi-instance → double job execution |

Baraye scale: `SKIP LOCKED`, Redis backplane, Quartz persistent job store (Postgres).

### Rate limiting

Gateway-level: 6/30s auth, 500/1min global per IP.
ACLServer: in-memory per-agent plate reader limiter.

### Background jobs

**Quartz** (Dejban): outbox + inbox per module. `IntervalInSeconds` configurable. `DisallowConcurrentExecution`.

**Hangfire** (RequestTracker): workflow sweeper. PostgreSQL storage, schema `hangfire`, 2 workers.

---

## Resilience

### Polly — HTTP retry

```csharp
Policy<T>.Handle<Exception>()
    .WaitAndRetryAsync(3, retryAttempt =>
        TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));
```

Exponential backoff: 2s, 4s, 8s. ACLServer device event handler-ha.

### MassTransit — retry + circuit breaker

```csharp
cfg.UseMessageRetry(r => r.Exponential(retryLimit: 5, ...));
cfg.UseCircuitBreaker(cb => {
    cb.TripThreshold = 15;
    cb.ActiveThreshold = 10;
    cb.ResetInterval = TimeSpan.FromMinutes(5);
});
```

15 fail → circuit **open** → 5 min wait → retry. Message-ha be error queue miran.

### EF ExecutionStrategy

Serializable transaction retry baraye `40001 serialization_failure`:

```csharp
var strategy = context.Database.CreateExecutionStrategy();
await strategy.ExecuteAsync(async () =>
{
    await using var tx = await context.Database.BeginTransactionAsync(Serializable, ct);
    // ... whole tx inside
});
```

### Health checks

Dejban: `/health` → Postgres + Redis check. `HealthCheckOptions` + `UIResponseWriter`.

Gateway: `/health/reporting-routes` → config check.

Docker: container-level healthcheck baraye infra.

**Na active YARP health** — service down → 502 Bad Gateway.

---

## Observability

### Serilog + Seq

Global config to `globalAppsettings.json`:

```json
"Serilog": {
    "Using": ["Serilog.Sinks.Console", "Serilog.Sinks.File", "Serilog.Sinks.Seq"],
    "WriteTo": [
        { "Name": "Console" },
        { "Name": "Seq", "Args": { "serverUrl": "http://localhost:5341" } }
    ],
    "Enrich": ["FromLogContext", "WithMachineName", "WithThreadId"]
}
```

Structured JSON log → Seq dashboard. Filter by `TraceId`, `RequestPath`, `UserId`.

### OpenTelemetry

Dejban traces:

```csharp
services.AddOpenTelemetry()
    .ConfigureResource(r => r.AddService(serviceName))
    .WithTracing(tracing =>
    {
        tracing
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddEntityFrameworkCoreInstrumentation()
            .AddRedisInstrumentation()
            .AddNpgsql()
            .AddSource(MassTransit.Logging.DiagnosticHeaders.DefaultListenerName);
        tracing.AddOtlpExporter();
    });
```

Trace az HTTP request → EF query → Redis → MassTransit publish. Jaeger/OTLP collector (Docker, disabled by default).

---

## Deployment

### Docker Compose layering

| file | chi |
|---|---|
| `docker-compose.yml` | Infrastructure: 7 Postgres, RabbitMQ, Redis, MinIO, MediaMTX |
| `docker-compose.development.yml` | Port mapping baraye local dev |
| `docker-compose.docker-development.yml` | Build + run 8 app services + gateway |
| `docker-compose.docker-production.yml` | Production environment |

### Frontend CI/CD — GitLab + PM2

```yaml
# .gitlab-ci.yml
stages: [deploy]
deploy_to_server:
  script:
    - ssh ... 'git pull origin master'
    - npm ci
    - npx turbo run build --concurrency=1
    - pm2 restart dejban_frontend_new_turborepo || pm2 start npm --name ... -- start
    - pm2 save
  only: [master]
```

Git pull → npm ci → turbo build → PM2 restart. Simple, na blue-green.

### Backend CI/CD

Backend `.gitlab-ci.yml` **nist** to repo. Deploy manual ya joda.

---

## Security

| layer | chi |
|---|---|
| TLS | HTTPS ta Gateway, HTTP internal |
| JWT | Access token 15min, refresh 7 days |
| Cookie | HttpOnly, Secure, SameSite=None |
| Token revoke | Redis blacklist, check per request |
| CORS | Dev: allow-all, Prod: whitelist |
| Rate limit | Auth 6/30s, Global 500/1min per IP |
| Multi-tenancy | X-Site-Id header + claim check |
| Permission | Claim-based, per-endpoint filter |

---

## Chi **nadari** (ta resume dorough nashe)

- Kubernetes / container orchestration
- CDN baraye static assets
- Service mesh (Istio)
- Read replicas (Postgres standby)
- Database sharding
- Elasticsearch / full-text search engine
- Saga pattern formal (choreography via events hast, vali formal saga nist)
- Blue-green / canary deployment
- Auto-scaling (CPU/memory based)
- Centralized config service (Consul, etcd)
- API versioning via header (faghat URL)
- GraphQL
- gRPC-Web baraye browser
- Backend CI/CD pipeline
- Load testing (k6, JMeter)

---

## Smell-ha

1. **Single instance per service** — no redundancy. Service down = feature down
2. **Inbox FOR UPDATE bedune SKIP LOCKED** — scale-out = serialize
3. **Channel SSE singleton** — multi-instance = lost events
4. **SignalR in-memory** — multi-instance = Redis backplane lazem
5. **Quartz in-memory job store** — multi-instance = double execution
6. **Na active YARP health check** — service down → 502 ta restart
7. **Backend CI/CD nist** — manual deploy risk
8. **Seq/Jaeger disabled by default** — production observability gap
9. **Na CDN** — static asset-ha az server serve mishan
10. **Na read replica** — heavy report query = API slow
11. **CORS Dev allow-all** — production misconfigure risk
12. **7 Postgres container** — ops overhead. Managed Postgres (RDS) behtar baraye production
13. **Na distributed lock** (Redis Redlock) — faghat DB advisory lock

---

## 20 soal-e mosahabe

1. **System-et ra describe kon** — 14 service, YARP gateway, MassTransit async, Postgres per-service, Redis cache, MinIO files
2. **Chera microservice?** — independent deploy, team autonomy, technology choice
3. **Chera modular monolith baraye Dejban?** — module boundary bedune network overhead. Split later age lazem she
4. **Database per service chera?** — loose coupling. Schema change-e service A, B ra nemishkane
5. **Chejori beyn-e service-ha sohbat mikonan?** — sync HTTP (YARP), sync gRPC (device), async MassTransit/RabbitMQ
6. **Event-driven chie?** — publish event, subscriber react. Loose coupling
7. **Eventual consistency?** — read-model copy eventually updated. Trade-off: stale data vs coupling
8. **CAP?** — CP: Postgres consistent, network partition → unavailable (503)
9. **Chejori cache mikoni?** — HybridCache L1+L2, token blacklist Redis, 5min report ticket
10. **Rate limit chejori?** — Gateway sliding window per IP. Auth 6/30s, global 500/1min
11. **Auth chejori?** — JWT access 15min + refresh 7d cookie. Redis revoke. Gateway validate
12. **Chejori scale mikoni?** — stateless JWT → horizontal. Bottleneck: inbox lock, SignalR state
13. **Single point of failure?** — Gateway (1 instance), Redis (1 instance), each DB (1 instance)
14. **Monitoring?** — Serilog structured → Seq. OpenTelemetry traces → Jaeger
15. **Chejori deploy mikoni?** — Docker Compose. Frontend GitLab CI + PM2
16. **Health check?** — Postgres + Redis. Na YARP active health
17. **Failure handling?** — Polly retry (HTTP), MassTransit retry + circuit breaker (message), EF ExecutionStrategy (DB)
18. **Outbox chie?** — event + entity same transaction. Background job publish. Reliable messaging
19. **gRPC chera?** — binary fast, streaming, strict contract. Device SDK communication
20. **Age 10x traffic biad?** — horizontal scale services, Redis cluster, Postgres read replica, SKIP LOCKED inbox, CDN, connection pooling tune

---

## Resume

**short:**

> Architected a microservices platform (7+ services, YARP gateway) with async event-driven integration via MassTransit/RabbitMQ, PostgreSQL database-per-service, Redis HybridCache, MinIO object storage, and Serilog/OpenTelemetry observability — deployed with Docker Compose.

**bullets:**

- Designed database-per-service isolation (7 PostgreSQL) with schema-per-module inside a modular monolith, synchronized via transactional outbox/inbox
- Implemented dual communication: HTTP REST via YARP gateway for browser clients, gRPC for real-time device SDK integration
- Built resilience with Polly exponential retry, MassTransit circuit breaker, and EF serializable transaction retry strategies
- Configured HybridCache (memory+Redis) for token revocation, report tickets, and general caching with stampede protection

**skills:** `System Design, Microservices, Modular Monolith, API Gateway, Event-Driven Architecture, MassTransit, RabbitMQ, PostgreSQL, Redis, MinIO, gRPC, Docker Compose, Serilog, OpenTelemetry`

---

## File-haye mohem

| chi | koja |
|---|---|
| Docker infra | `docker-compose.yml` |
| Docker apps | `docker-compose.docker-development.yml` |
| Gateway pipeline | `ApiGateway/Program.cs` |
| YARP routes | `ApiGateway/appsettings.json` |
| MassTransit + consumers | `ACLServer/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| RabbitMQ queues | `Common/EventBus/eventbus_init/definitions.json` |
| HybridCache + Redis | `Common/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Token blacklist | `Common/Caching/TokenBlackListService.cs` |
| Token revoke middleware | `Common/Caching/TokenRevokeMiddleware.cs` |
| OpenTelemetry | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| Serilog + Seq config | `GlobalAppsettings/globalAppsettings.json` |
| gRPC proto | `Common/Protos/SSM/ssm_service.proto` |
| gRPC client | `ACLServer/Infrastructure/Services/ZKGrpcClientWrapper.cs` |
| S3 storage | `DCC/Infrastructure/Services/S3FileStorage.cs` |
| MinIO Docker | `docker-compose.yml` (minio + minio-init) |
| Polly retry | `ACLServer/Abstractions/Resilience/RetryPolicies.cs` |
| Quartz outbox | `Visitors.Infrastructure/Outbox/ProcessOutboxJob.cs` |
| Hangfire | `RequestTracker/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Health check | `Dejban.Api/Program.cs` |
| Frontend CI/CD | `dejban_frontend_new/.gitlab-ci.yml` |
| Axios client | `dejban_frontend_new/packages/api-client/src/axiosInstance.ts` |

---

*Day 06 tamum. Ba'd: Day 07 — Algorithms + Big-O. Fehrest: [README.md](./README.md).*
