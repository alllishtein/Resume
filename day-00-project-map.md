# Day 00 — Naghshe-ye proje Dejban (Orientation)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Day Zero** code-e jadid yad nemide; hadafesh in-e ke **hang nakoni**. Ghabl az inke YARP, MassTransit, outbox, ya JWT ra pechide bekhooni, bayad beduni Dejban **chi kar** mikone (business), code **koja** zendegi mikone (repo map), ye request **chejori** az browser ta Postgres miravad, va in ketabche-ha ra **chejori** bekhooni ta tartib-e fehrest ma'ni dashte bashe.

Age mostaghim az gateway ya messaging shoru' koni bedune in naghshe, maghzat por mishe va hang. In ruz ye tasvir-e zehni mide: platform-e multi-site amniat/dastresi, modular monolith + microservice, va zincire-ye request → Gateway → MediatR → DB (± event). Ba'd az in, Day 01 be ba'd har tech ra ru hamin naghshe pin mikoni.

---

# BAKHSH-E AVAL: WORLD — orientation chera lazeme

## Chera ghabl az tech, map?

To donya-ye enterprise, «orientation» yani ghabl az deep-dive, boundary-ha, entry point-ha, va glossary ra beduni. Inja faghate tooling nist — ye system-e vaghe'i ba chand DB, chand process, va multi-tenant site-ha. Bedune map, har file-e DEJBAN mesle joz'i az puzzle-e bi-frame mimanad.

---

## 1) Business — Dejban chie?

**Dejban** platform-e amniat / dastresi / traffic baraye site-ha-st (karkhane, edare, padegan, …). Yani ye product nist ke faghat CRUD dashte bashe; domain-haye asli-ash inha-and:

| domain | chi |
|---|---|
| **Personnels** | personel, site, unit, document, blacklist |
| **Visitors** | bazdid, rezerv, check-in, card |
| **Vehicles** | pelak, ownership, assignment, dastresi |
| **ACL / Devices** | dastgah ZK/Tiam/Virdi, ACL user, door, access log |
| **Gates** | gate hardware / relay |
| **RequestTracker** | cartable / workflow approve |
| **Armory / Inventory / CashLogistics / SecurityPatrols / WeighBridge** | module-haye business digar |
| **Identity** | login, role, claim, session |
| **DCC** | file / document storage |
| **Reporting** | Stimulsoft report |

**Multi-site:** har user mitone chand site dashte bashe. Scope-e request az header `X-Site-Id` + JWT claims miad — Day 16 in ra deep mikone; inja faghat bedun ke «tenant» = site.

---

## 2) Repo map — 3 folder

Workspace-e ma se folder-e asli dare. Har kodam ye maghsad-e joda dare:

```
D:\Dezhban\
├── dejban_backend_new\     ← .NET microservices + modular monolith
├── dejban_frontend_new\    ← Turborepo (Next.js apps + packages)
└── learning\               ← hamin ketabche-ha (Resume git)
```

### Backend — chi kojast?

Backend ye solution-e bozorg-e: Gateway vorudi-ye yekta-st, Common shared library-ha ra negah midare, va Microservices process-haye joda (ya modular monolith) ra darad:

```
dejban_backend_new\
├── ApiGateway\              ← YARP — exclusive HTTP entry
├── Common\                  ← JWT, cache, EventBus contracts, Tenancy, Protos
├── GlobalAppsettings\       ← JwtSettings, Serilog, shared config
├── docker-compose*.yml      ← Postgres×7, Redis, RabbitMQ, MinIO, MediaMTX
└── Microservices\
    ├── Dejban\              ← MODULAR MONOLITH (8 module, 1 process)
    │   ├── API\Dejban.Api\
    │   ├── Common\          ← Entity, MediatR, Outbox infra
    │   └── Modules\
    │       ├── Visitors\
    │       ├── Personnels\
    │       ├── Vehicles\
    │       ├── Armory\
    │       ├── CashLogistics\
    │       ├── Inventory\
    │       ├── SecurityPatrols\
    │       └── WeighBridge\
    ├── IdentityServer\      ← auth
    ├── ACLServer\           ← devices + access
    ├── DCC\                 ← files → MinIO
    ├── RequestTracker\      ← workflow
    ├── Reporting\
    ├── GateServer\
    └── *GrpcServer\         ← ZK / Tiam / Virdi adapters
```

Har Dejban module hamin layering ra follow mikone:

```
Domain → Application → Infrastructure → Presentation (+ IntegrationEvents)
```

### Frontend — chi kojast?

Frontend Turborepo-st: app-ha Next.js-and, shared logic to packages miravad:

```
dejban_frontend_new\
├── apps\
│   ├── dejban\              ← asosli (Next)
│   └── access-control\      ← …
├── packages\
│   ├── api-client\          ← Axios + tokenStorage
│   ├── auth\
│   └── ui\
└── .gitlab-ci.yml           ← build + PM2
```

---

## 3) Request lifecycle — yek tasvir dar zehenet

In diagram zincire-ye **sync** ra neshan mide. Har bar ke debug mikoni, az hamin hop-ha so'al kon:

```
Browser (Next.js)
  │  Axios: Bearer accessToken + cookie refresh + X-Site-Id
  ▼
ApiGateway (YARP) :7036
  │  CORS → RateLimit → TokenRevoke → JWT Auth → route
  ▼
Microservice (masalan Dejban.Api)
  │  Exception → Serilog → Auth → TenantContext → Endpoint
  ▼
MediatR
  │  Validation → Handler
  ▼
Domain + Repository + EF SaveChanges
  │  (± outbox row)
  ▼
PostgreSQL (schema ya DB-e service)
  │
  └─ async: MassTransit → RabbitMQ → digar service-ha / inbox
```

**Hamishe az in zincire so'al kon:** Request kojast? Auth shode? Tenant chie? Command ya Query? SaveChanges? Event?

### Lifecycle — ghanj (har hop chi check mikone)

Jadval-e zir haman diagram ra ba masooliat va tip-e debug gostar midahad. Sync path = hop 1→9 to haman request; async path = hop 10 ba'd az commit (eventual consistency baraye read-model copy-ha).

| # | hop | masool | tip |
|---|---|---|---|
| 1 | Browser | Next.js + Axios | `Authorization`, cookie refresh, `X-Site-Id` |
| 2 | Gateway | YARP | CORS, rate limit, JWT validate, token revoke (Redis) |
| 3 | Route | `appsettings` cluster | `/api/dejban/*` → Dejban.Api, `/identity/*` → Identity, … |
| 4 | ASP.NET | middleware | Exception → Serilog → Auth → **TenantContext** |
| 5 | Endpoint | Minimal API | bind body → `ISender.Send(command)` |
| 6 | MediatR | pipeline | Validation (FluentValidation) → Handler |
| 7 | Handler | Application | repo + domain method → `IUnitOfWork.SaveChanges` |
| 8 | EF | interceptor | domain events → **outbox row** (same transaction) |
| 9 | DB | Postgres | schema module (masalan `personnels.*`) |
| 10 | Async | Quartz + MT | publish integration event → consumer/inbox digar module |

**Debug checklist:** Gateway 401? → JWT/blacklist. 403? → claim/permission. 404 list? → soft-delete filter ya tenant. Data ghabli to module digar? → inbox/outbox lag.

---

## 4) Do architecture — na inke hame microservice-e

In fargh ra zud yad begir — hang-e bozorg az inja miad. Dejban.Api **modular monolith**-e (chand module, yek process, yek Postgres ba chand schema). Identity / ACL / DCC / … **microservice**-an (process va DB joda).

| | Dejban.Api | Identity / ACL / DCC / … |
|---|---|---|
| style | **Modular monolith** | **Microservice** |
| deploy | 1 process, 8 module | process joda |
| DB | 1 Postgres, **8 schema** | DB joda |
| API | Minimal API (`IEndpoint`) | Controllers |
| events | custom outbox + Dapper jobs | MassTransit EF Outbox |

Cross-service = **event** (na FK cross-DB). Dakhele Dejban = schema joda + copy read-model. Detail to Day 09.

---

## 5) Glossary — 30 kalame ke bayad beduni

In jadval dictionary-e kootah-e — age yeki ra nafahmidi, fehrest README → ruz-e marbut. Hadaf: ba’dan to WORLD/DEJBAN aslan hang nakoni.

| kalame | ma'ni-ye kootah |
|---|---|
| Gateway | vorudi yekta (YARP) |
| JWT | token signed baraye identity |
| Blacklist | token revoke shode to Redis |
| Claim | permission/role to principal |
| Tenant / Site | izolasyon multi-site |
| CQRS | Command vs Query |
| MediatR | bus-e in-process baraye handler |
| Pipeline behavior | middleware-e MediatR |
| ErrorOr | result ba error, na exception |
| FluentValidation | rule-haye input |
| Entity | domain object ba Id |
| Domain event | chizi dakhel-e module etefagh oftad |
| Integration event | beyn-e module/service |
| Outbox | event + entity same transaction |
| Inbox | receive + process idempotent |
| Aggregate | consistency boundary |
| DbContext | EF session / UoW |
| Schema | namespace to Postgres |
| Soft delete | IsDeleted, na physical delete |
| MassTransit | messaging library |
| RabbitMQ | message broker |
| HybridCache | memory + Redis |
| SignalR | realtime WebSocket |
| gRPC | binary RPC (device) |
| Quartz | scheduled jobs (outbox) |
| Hangfire | background jobs (RT) |
| MinIO | S3-compatible files |
| Scrutor | DI decorator |
| ProblemDetails | HTTP error body standard |

### Glossary — 20 kalame-ye digar (part 2)

| kalame | ma'ni-ye kootah |
|---|---|
| Minimal API | endpoint ba `MapGet`/`MapPost`, na Controller |
| IEndpoint | interface baraye register endpoint per feature file |
| TenantContext | `ITenantContext` — SiteIds az header + claim |
| X-Site-Id | header baraye site-e entekhab-shode |
| ISiteEntity | entity ba `SiteId` — tenant filter |
| IUnitOfWork | abstraction roye `SaveChanges` |
| Repository | data access per aggregate — na DbSet to handler |
| Value object | immutable object bedune Id (Plate, Address) |
| IntegrationEventConsumer | MassTransit/inbox handler baraye event |
| Read model copy | Site/Personnel copy to schema digar (Visitors, Vehicles) |
| Stimulsoft | engine-e report to Reporting service |
| Cartable | RequestTracker workflow / approve |
| ZK / Tiam / Virdi | brand-e device ACL — gRPC adapter |
| Plate reader | camera pelak → ACL event |
| migrationesho | process-e server ke migration misaze/apply mikone |
| ModelSnapshot | fingerprint-e EF model — commit na kon baraye change jadid |
| Named query filter | `SoftDeleteFilter` vs `TenantFilter` joda |
| OpenAPI / Scalar | API doc UI |
| Turborepo | monorepo build orchestrator FE |
| TanStack Query | cache + refetch data to React |

**Jam:** ~50 kalame — in 30 + 20. Age yeki ra nafahmidi, fehrest README → ruz-e marbut.

---

## 6) Chejori ketabche bekhooni (ta hang nakoni)

Har file 2 bakhsh dare:

1. **WORLD** — concept-e general (mosahebe + asl)
2. **DEJBAN** — exact file path + pattern-e in proje

**Ghaede:**
- Aval WORLD ra ta «fahmidam» bekhoon — code ra skip kon age zud-e
- Ba'd DEJBAN — path-ha ra to IDE baz kon, **1 mesal** ra follow kon
- Resume + 20 soal = review shab
- **Yek ruz = yek file.** Do tech parallel = hang

**Agar hang kardi:**
1. bargard Day 00 (in file)
2. request lifecycle ra dobare bekesh
3. faghat 1 radif az fehrest-e README ra edame bede

---

## 7) Tartib-e fehrest

README az Day 00 ta 59 be tartib-e yadgiri-e proje-st:

paye → pipeline/JWT/YARP → architecture → domain/EF → (Repo/Tenancy/…) → messaging → infra → FE → test → Algorithms (akhar).

Har ruz ke `—` bashe = hanuz neveshte nashode; bego ta benevisam.

---

## 8) To koja hasti?

Amade: **00–49**, **59**.  
Avalin khali: **Day 50 — SignalR client**.

---

## 9) Checklist — «amade-am day badi?»

- [ ] mitunam ba 5 jomle beguim Dejban chi kar mikone
- [ ] mitunam 5 microservice + Dejban modular monolith ra name bebaram
- [ ] mitunam request az browser ta DB ra ba angosht neshun bedam
- [ ] fargh-e domain event vs integration event ra mifahmam (kholase)
- [ ] midunam learning folder kojast va chejori PDF/motale'e mikonam

Age 5 ta tik khord → boro Day 01 (ya avalin ruz-e khali ke mikhay).

---

## 10) Tamrin-e 30 daghighe (bedune code zadan)

Hadaf: **jahat**, na mastery. Faghat in 5 file ra baz kon va jahat ra hes kon:

1. `ApiGateway/Program.cs` ra baz kon — faghat `Use*` ha ra bebin
2. `Dejban.Api/Program.cs` — `AddVisitorsModule` va `MapEndpoints`
3. ye endpoint to Visitors Presentation — `ISender.Send`
4. ye command handler — `SaveChanges`
5. `docker-compose.yml` — esm-e service-ha (db, redis, eventbus, minio)

---

## 11) Service map — har service chi kar mikone?

In jadval **orientation**-e — detail to ruz-haye 06–20. Duplicate nakon; faghat «koja beram?» ra javab mide.

| service | vorudi | DB / storage | async | ruz-e asli |
|---|---|---|---|---|
| **ApiGateway (YARP)** | `:7036` HTTPS | — | — | [07](./day-07-yarp.md), [08](./day-08-system-design.md) |
| **Dejban.Api** | `/api/dejban/...` | `payamgostar_dejban` — 8 schema | custom outbox/inbox + Quartz | [09](./day-09-microservices-modular-monolith-ddd.md)–[19](./day-19-dapper-outbox-inbox.md) |
| **IdentityServer** | login, user, role, site claim | `payamgostar_identity` | MassTransit outbox | [06](./day-06-jwt-token-blacklist.md), [36–37 khali] |
| **ACLServer** | device, door, ACL user, access log | `payamgostar_aclserver` | MT consumers + gRPC client | [27](./day-27-grpc-zk-tiam-virdi.md), [20](./day-20-masstransit-rabbitmq.md) |
| **DCC** | upload/download file, presign | `payamgostar_dcc` + **MinIO** | MT | [28 khali], [41 khali] |
| **RequestTracker** | cartable, workflow, approve | `payamgostar_requesttracker` | MT + **Hangfire** | [29 khali] |
| **Reporting** | Stimulsoft report, ticket | `payamgostar_reporting` + read Dejban schemas | kam | [39 khali] |
| **GateServer** | kiosk / gate relay | `payamgostar_gateserver` | — | — |
| **ZK/Tiam/Virdi gRPC** | device SDK | — (state local) | stream log/event | [27](./day-27-grpc-zk-tiam-virdi.md) |

**Dejban modules (1 process):** Visitors, Personnels, Vehicles, Armory, CashLogistics, Inventory, SecurityPatrols, WeighBridge — har kodam schema + DbContext joda.

**Rule:** cross-service = **event** (na FK cross-DB). dakhele Dejban = schema joda, copy read-model.

---

## 12) Fehrest ruz 01–20 — che ruz chi?

Motale'e pishnahadi: hafte 1 → 00–07. hafte 2 → 08–14. hafte 3 → 15–20. ba'd 21+ (outbox/inbox deep).

| ruz | file | yad begir |
|---|---|---|
| 01 | [HTTP/REST](./day-01-http-rest-web.md) | status code, REST, cookie vs header |
| 02 | [C# async](./day-02-csharp-async-concurrency-gc.md) | async/await, thread pool |
| 03 | [OOP/SOLID](./day-03-oop-solid-patterns.md) | pattern-ha, encapsulation |
| 04 | [SQL](./day-04-sql-relational-db.md) | join, index, ACID |
| 05 | [ASP.NET pipeline](./day-05-aspnet-pipeline-di.md) | middleware, DI scope |
| 06 | [JWT + blacklist](./day-06-jwt-token-blacklist.md) | access/refresh, revoke |
| 07 | [YARP](./day-07-yarp.md) | route, cluster, transform |
| 08 | [System design](./day-08-system-design.md) | scale, CAP, Dejban diagram |
| 09 | [Micro vs modular](./day-09-microservices-modular-monolith-ddd.md) | layer, module boundary |
| 10 | [CQRS/MediatR](./day-10-cqrs-mediatr-pipeline-behaviors.md) | command/query, behaviors |
| 11 | [Validation](./day-11-fluentvalidation-erroror.md) | FluentValidation, ErrorOr |
| 12 | [DDD](./day-12-ddd-aggregate-domain-event-value-object.md) | aggregate, VO, domain event |
| 13 | [EF/Npgsql](./day-13-ef-core-npgsql.md) | schema, filter, interceptor |
| 14 | [Repository/UoW](./day-14-repository-unit-of-work.md) | repo pattern, tracking |
| 15 | [Soft delete](./day-15-soft-delete.md) | IsDeleted, partial unique |
| 16 | [Multi-tenancy](./day-16-multi-tenancy.md) | X-Site-Id, TenantFilter |
| 17 | [Minimal API](./day-17-minimal-apis-iendpoint.md) | IEndpoint, MapEndpoints |
| 18 | [Modular DI](./day-18-modular-di.md) | AddXxxModule |
| 19 | [Dapper outbox/inbox](./day-19-dapper-outbox-inbox.md) | hot path SQL jobs |
| 20 | [MassTransit](./day-20-masstransit-rabbitmq.md) | RabbitMQ, consumer |

---

## 13) File map — repo (faghat landmark)

Az Day 00 faghat **5 file** baz kon (tamrin-e bala) — ba'd har ruz 3–5 file jadid to DEJBAN section. Inha landmark-ha-ye bakhshe:

### Backend (`dejban_backend_new`)

| maqsad | path |
|---|---|
| Gateway pipeline | `ApiGateway/Program.cs`, `ApiGateway/appsettings.json` |
| Dejban boot | `Microservices/Dejban/API/Dejban.Api/Program.cs` |
| Module register | `Microservices/Dejban/Modules/*/Infrastructure/*Module.cs` |
| Shared tenancy | `Microservices/Dejban/Common/Dejban.Common.*` + `Common/Tenancy/` (solution root) |
| Event contracts | `Common/EventBus/Contracts/` |
| Docker infra | `docker-compose.yml`, `docker-compose.docker-development.yml` |
| Global config | `GlobalAppsettings/globalAppsettings.json` |
| Identity | `Microservices/IdentityServer/` |
| ACL | `Microservices/ACLServer/` |
| DCC | `Microservices/DCC/` |
| Reporting | `Microservices/Reporting/` |
| RequestTracker | `Microservices/RequestTracker/` |
| Gate | `Microservices/GateServer/` |

### Frontend (`dejban_frontend_new`)

| maqsad | path |
|---|---|
| Main app | `apps/dejban/src/` |
| API client | `packages/api-client/src/axiosInstance.ts` |
| Auth/guards | `packages/ui/src/auth/` |
| Feature sections | `apps/dejban/src/sections/<feature>/` |
| Services (HTTP) | `apps/dejban/src/services/<feature>/` |

---

## 14) Motale'e — 3 mode

Se mode-ye motale'e darim. Hang = signal: ziad parallel nakhoon. Yek ruz, yek file. PDF/export: Markdown viewer ya print — folder `learning` joda az git app repo-ha.

| mode | vaght | chi |
|---|---|---|
| **Skim** | 20 min | WORLD faghat — concept |
| **Deep** | 60–90 min | WORLD + DEJBAN + 1 trace to IDE |
| **Review** | 15 min | Resume + soal-ha payan-e file |

---

*Day 00 tamum. Ba'd: Day 01 — HTTP / REST / Web. Fehrest: [README.md](./README.md).*
