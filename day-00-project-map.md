# Day 00 — Naghshe-ye proje Dejban (Orientation)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## In ruz chie?

In **Day Zero**-e. Code-e ghabl nist. Hadaf: **hang nakoni**.

Ghabl az tech-e jadid:
1. beduni proje **chi kar** mikone (business)
2. beduni code **koja** zendegi mikone (map)
3. beduni ye request **chejori** az browser ta DB miravad
4. beduni chejori in ketabche-ha ra bekhooni
5. beduni **tartib-e motale'e** chera injori-e

Age faghat az YARP ya MassTransit shoru' koni bedune in map → maghzat por mishe va hang.

---

## 1) Business — Dejban chie?

**Dejban** = platform-e amniat / dastresi / traffic baraye site-ha (karkhane, edare, padegan, …).

Domain-haye asli:

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

**Multi-site:** har user mitone chand site dashte bashe. Header `X-Site-Id` + JWT claims.

---

## 2) Repo map — 3 folder

```
D:\Dezhban\
├── dejban_backend_new\     ← .NET microservices + modular monolith
├── dejban_frontend_new\    ← Turborepo (Next.js apps + packages)
└── learning\               ← hamin ketabche-ha (Resume git)
```

### Backend — chi kojast?

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

Har Dejban module:

```
Domain → Application → Infrastructure → Presentation (+ IntegrationEvents)
```

### Frontend — chi kojast?

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

**Hamishe az in zincire so'al kon:**  
Request kojast? Auth shode? Tenant chie? Command ya Query? SaveChanges? Event?

---

## 4) Do architecture — na inke hame microservice-e

| | Dejban.Api | Identity / ACL / DCC / … |
|---|---|---|
| style | **Modular monolith** | **Microservice** |
| deploy | 1 process, 8 module | process joda |
| DB | 1 Postgres, **8 schema** | DB joda |
| API | Minimal API (`IEndpoint`) | Controllers |
| events | custom outbox + Dapper jobs | MassTransit EF Outbox |

In fargh ra zud yad begir — hang-e bozorg az inja miad.

---

## 5) Glossary — 30 kalame ke bayad beduni

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

Amade: **00–14**, **19–20**, **59**.  
Avalin khali: **Day 15 — Soft Delete**.

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

1. `ApiGateway/Program.cs` ra baz kon — faghat `Use*` ha ra bebin
2. `Dejban.Api/Program.cs` — `AddVisitorsModule` va `MapEndpoints`
3. ye endpoint to Visitors Presentation — `ISender.Send`
4. ye command handler — `SaveChanges`
5. `docker-compose.yml` — esm-e service-ha (db, redis, eventbus, minio)

Hadaf: **jahat**, na mastery.

---

*Day 00 tamum. Ba'd: Day 01 — HTTP / REST / Web. Fehrest: [README.md](./README.md).*
