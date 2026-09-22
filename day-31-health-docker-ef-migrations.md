# Day 31 — Health Checks + Docker + EF migration workflow

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

In ruz se chiz-e «ops»-e ke beham vasl-an:

**1) Health Checks** — yani ye endpoint ke az app miporse: «zende-i? Postgreso mibini? Rediso mibini?» Load balancer / Docker / monitoring ba in midunan traffic behet bedan ya na. To Dejban.Api: `AddHealthChecks().AddNpgSql(...).AddRedis(...)` va `GET /health` ba JSON-e khub. Postgres container-ha khodeshun `pg_isready` healthcheck daran. Reporting ye health-e ekstra baraye font/js dare.

**2) Docker** — yani app va DB va Redis va Rabbit va MinIO dar container, ba `docker-compose` chand-layer. Base: `docker-compose.yml` (network + volume + service bedune port publish). Development: port-ha (18001 Identity DB, …). Docker-dev/prod: build Dockerfile-e har microservice. Multi-stage Dockerfile: restore → build → publish → runtime kuchik.

**3) EF migration workflow** — yani schema-e DB chejori ba code sync mishe. **Local/dev:** startup `Database.Migrate()` (Dejban 8 context ba `ApplyMigrations`, digar service-ha `DbInitializer`). **Team policy (mohem):** baraye taghir-e schema, entity/config commit mishe; class-e `Migration` to repo **commit nemishe** — server ba **migrationesho** ba'd az deploy misaze/apply mikone. Local temporary migration OK, ghabl commit pak.

In fasl ravoontar az ghabl tozih mide: chera har kodum, chejori bekhuni, che smell-i dare.

**Band-e jadid-e gharardad (az in ruz):** tozihat bayad **ravoontar va sade-tar** bashan — bishtar «farz kon / yani chi / chera», kamtar telegram. Hamin olgu baraye Day 32+ ham.

---

# BAKHSH-E AVAL: WORLD — se mafhum ba zaban-e sade

## Health Check — be zaban-e adam

Farz kon restaurant-i. Ghabl az inke mosafer biad, ye nafar check mikone: ashpazkhune baz-e? gaz dare? yakhchal sard-e?

Health check hamun-e baraye software:

- **Liveness:** process zende-st? (crash nakarde)
- **Readiness:** amade-ye traffic? (DB up-e, migrate tamum shode, …)

Agar readiness fail bashe, load balancer request nemifreste — user 502 kamtar mibine, system time dare recover she.

---

## Chera faghat «ping HTTP 200» kaf nist?

App mitune HTTP bdeh vali Postgres down bashe → har API 500. Health check-e **dependency-aware** (NpgSql, Redis) in ro migire.

| check | ma'ni-ye sade |
|---|---|
| self | process up |
| PostgreSQL | mitunam connect/query konam |
| Redis | PING ok |
| custom | masalan font file hast? (Reporting) |

---

## Docker — be zaban-e adam

Docker = «app + dependency-hash to ye jabe-ye standard».

- **Image** = noskhe-ye pokhte (mesal `postgres`, ya image-e Dejban.Api ke khodet sakhti)
- **Container** = ye instance-e running az image
- **Volume** = disk-e paydar (DB data ba `docker compose down` pak nashe)
- **Network** = LAN-e virtual beyn container-ha (`identitydb` hostname)

`docker compose` chand service ro ba yek farman up mikone. Bedune in, developer 7 Postgres + Redis + Rabbit dasti nasb mikone — dard.

---

## Compose overlay — chera chand file?

Yek file-e bozorg hame chiz = conflict. Olgu:

| file | naqsh |
|---|---|
| `docker-compose.yml` | tarife service + volume + network (asli) |
| `docker-compose.development.yml` | faghat **ports** baraye laptop |
| `docker-compose.docker-development.yml` | build app containers + depends |
| `docker-compose.docker-production.yml` | prod-ish |

```bash
docker compose -f docker-compose.yml -f docker-compose.development.yml up -d
```

Yani: base + overlay. Port 18004 = dejbandb az host.

---

## Multi-stage Dockerfile — chera?

Build .NET niaz be **SDK** dare (bozorg). Run faghat **aspnet runtime** mikhad (kuchiktar, amniattar).

```
stage base   → runtime image
stage build  → sdk, restore, build
stage publish→ publish output
stage final  → copy publish into runtime → ENTRYPOINT dotnet App.dll
```

Fayde: image final SDK nadare; attack surface kamtar; size kamtar.

---

## EF Migration — be zaban-e adam

Code mige: «table Personnel in column-ha ro mikhad.»  
DB shayad ghadimi bashe. Migration = script-e taghir-e schema (ADD COLUMN, …) + history table `__EFMigrationsHistory`.

`Database.Migrate()` = «hame migration-e apply-nashode ro ejra kon.»

**Moshkel-e team-ha:** age har developer migration file commit kone, merge conflict + tartib kharab. Dejban policy: **schema owner = server migrationesho**; developer entity avaz mikone, Migration class to PR nist (magar local temp).

---

## Startup Migrate — khub ya bad?

**Khub baraye local:** `docker up` → app start → Migrate → seed → kari.  
**Bad baraye multi-replica prod:** do pod hamzaman Migrate → race.  
**Behtar prod:** job/migrator joda (migrationesho) ghabl az scale-out API.

Dejban code alan startup Migrate dare (dev convenience) + policy server-side baraye schema evolve.

---

# BAKHSH-E DOVOM: DEJBAN — daqiq to proje

## Qesmat 1 — Health Checks

### Dejban.Api

```csharp
builder.Services.AddHealthChecks()
    .AddNpgSql(databaseConnectionString)
    .AddRedis(redisConnectionString);

app.MapHealthChecks("health", new HealthCheckOptions
{
    ResponseWriter = UIResponseWriter.WriteHealthCheckUIResponse
});
```

**Yani chi?**

1. Package-haye health check Postgres va Redis register mishan.  
2. Endpoint `/health` (relative to app — posht-e YARP masir-e gateway check kon).  
3. `UIResponseWriter` JSON-e khanatar mide (status per check), na faghat plain text.

Age Postgres down → overall Unhealthy → orchestrator mitune restart/stop traffic.

### Docker healthcheck ru-ye Postgres

```yaml
healthcheck:
  test: pg_isready -U postgres -d payamgostar_identity
  interval: 10s
  timeout: 5s
  retries: 10
  start_period: 10s
```

**Yani chi?** Docker midune container «ready»-e ya na. `depends_on` ba `condition: service_healthy` (to overlay-haye app) montazer mimune DB ghabl az start-e API — kamtar Migrate fail «connection refused».

`Task.Delay(10000)` ghabl Migrate = wait-e ezafi «DB ya amade shode» — smell/hack, na jaygozin-e health depends_on.

### Reporting — health custom

`GET /health/reporting-assets` check mikone wwwroot/js/css/lib va font-ha (DejaVu/Tahoma…). Age Stimulsoft font nadashte bashe, report shekast mikhore — pas health-e **business asset**, na faghat DB.

---

## Qesmat 2 — Docker to Dejban

### Chi to compose base hast?

| service | naqsh-e sade |
|---|---|
| `identitydb` … `gateserverdb` | Postgres joda per bounded context |
| `dejbandb` | DB modular monolith |
| `eventbus` | RabbitMQ |
| `redis` | cache / blacklist |
| `minio` + `minio-init` | object storage + bucket/CORS |
| network `backend` | DNS beyn container-ha |
| volumes `*-data` | persist |

**Chera 7 Postgres?** Database-per-service (Day 09) — failure/isolation. Compose in architecture ro **dasti** mirror mikone.

### Port map (development overlay)

| host port | service |
|---|---|
| 18001 | Identity DB |
| 18002 | RequestTracker DB |
| 18003 | ACL DB |
| 18004 | Dejban DB |
| 18005 | DCC DB |
| 18006 | Reporting DB |
| 18007 | Gate DB |
| 5672 / 15672 | Rabbit / management |
| 6379 | Redis |
| 19000 / 19001 | MinIO API / console |

Connection string local: `Host=localhost;Port=18004;...`  
Connection string dakhel Docker network: `Host=dejbandb;Port=5432;...`

**Confusion-e mamool:** app to container `localhost` mige → khodesh, na DB. Bayad hostname service.

### App containers (docker-development)

Build az Dockerfile har service (Identity, DCC, Reporting, RequestTracker, ACL, Dejban.Api, Gate, ApiGateway). `depends_on` → DB/redis/rabbit/minio.

### Multi-stage Dejban.Api Dockerfile (kholase)

1. Copy csproj-ha → `dotnet restore` (layer cache)  
2. Copy source → build/publish  
3. Final: aspnet 10.0, `ENTRYPOINT dotnet Dejban.Api.dll`, EXPOSE 80  

**Yani chi baraye mosahebe?** «We use multi-stage builds so production images only contain the runtime and published bits.»

---

## Qesmat 3 — EF migration workflow (Dejban + policy)

### A) Anchi code alan mikone (local/docker)

**Dejban.Api** hangam start:

```csharp
await app.ApplyMigrations();
await app.ApplySeedData();
```

```csharp
public static async Task ApplyMigrations(this IApplicationBuilder app)
{
    using var scope = app.ApplicationServices.CreateScope();
    await Task.Delay(10000); // wait DB

    ApplyMigration<VisitorsDbContext>(scope);
    ApplyMigration<PersonnelsDbContext>(scope);
    // … 8 module DbContext
}

private static void ApplyMigration<TDbContext>(IServiceScope scope) where TDbContext : DbContext
{
    using var context = scope.ServiceProvider.GetRequiredService<TDbContext>();
    context.Database.Migrate();
}
```

**Yani chi?** Har schema-e module (Visitors, Personnels, …) joda Migrate mishe. Modular monolith = chand DbContext, yek process.

**Identity / ACL / DCC / …:** `DbInitializer` → `MigrateAsync` (+ seed Identity).

### B) Team policy — migrationesho (in bakhsh ra khub bekhun)

Fekr-e eshtebah: «pas migration file bayad hamishe to git bashe.»

Policy-e proje (Day 13 + `.cursor` rules):

1. Developer **entity / Fluent config / validator** avaz mikone → commit.  
2. Class-e `Migration` / update ModelSnapshot baraye schema **jadid** to PR **nemiyad**.  
3. Ba'd az deploy code, process-e **migrationesho** ru-ye server migration misaze/apply mikone.  
4. **Local testing:** mituni temporary migration besazi ta DB local update she; ghabl **commit/push** an file-ha + Script-ha ro pak kon / snapshot ro bargardun.

**Chera?** Yek manba-e haghighat baraye apply-e prod; kamtar merge hell; control-e DBA/ops.

**World vs Dejban:** to aksar team-ha migration to repo-st. To mosahebe begu: «in team server-side migrator dare; local ApplyMigrations convenience-e.»

### C) Zincir-e taghir schema (zehni)

```
1) Domain property ezafe (DateOfBirth?)
2) EF configuration IsRequired(false)
3) Commit code (bedune Migration class — policy)
4) Deploy
5) migrationesho → ALTER TABLE …
6) App instances ba schema jadid
```

Local:

```
1-2 same
3) dotnet ef migrations add … (temporary)
4) run app / Migrate()
5) test
6) delete migration files ghabl push
```

### D) Smell-haye Migrate on startup

| smell | tozih-e sade |
|---|---|
| Race | 2 replica hamzaman Migrate |
| Slow start | Delay 10s + migrate + seed = boot tool |
| Permission | app identity niaz DDL dare — amniat |
| Hidden apply | ops nemidune key schema avaz shod |

Ideal prod: migrator job joda; API faghat DML.

---

## Se layer ba ham — ye dastan

```
docker compose up
  → Postgres healthy (pg_isready)
  → Dejban.Api container start
  → Delay + Migrate 8 schemas
  → Seed
  → /health → Healthy (Npgsql+Redis)
  → YARP traffic
```

Age DB slow: healthcheck fail → app depends wait → ya Delay 10s najat mide (na ziba, amma amali).

---

## Smell-ha (kamel)

1. `Task.Delay(10000)` — magic sleep  
2. Migrate on every boot multi-instance  
3. App user ba DDL rights  
4. Health endpoint public bedune auth (ma'mulan OK, ama abuse)  
5. `/health` detailed JSON → info leak (version/deps) — prod sometimes minimal  
6. Connection string localhost dakhel container  
7. Volume forget → data loss compose down -v  
8. Migration conflict age kasi Migration commit kone bar khalaf policy  
9. Seed Identity tool (30s delay digar) — boot slow  
10. Reporting health font path Linux vs Windows  
11. No separate liveness vs readiness to Dejban (hardcore k8s)  
12. Dockerfile COPY bozorg — build cache sensitivity  

---

## Debug checklist (sade)

1. `docker compose ps` — unhealthy?  
2. `pg_isready` / log Postgres  
3. App log: Migrate exception?  
4. Host port eshtebah? 18004 vs 5432  
5. `/health` Unhealthy — kodom check?  
6. Redis down → health fail even if API «half works»  
7. Migration pending — `__EFMigrationsHistory`  
8. Policy: accidental Migration file to git status?  

---

## 25 soal-e mosahebe

1. Liveness vs readiness?  
2. Chera health dependency?  
3. AddNpgSql / AddRedis?  
4. UIResponseWriter?  
5. Docker image vs container?  
6. Volume chera?  
7. Compose overlay?  
8. Multi-stage Dockerfile?  
9. Chera chand Postgres?  
10. Hostname vs localhost?  
11. `Database.Migrate` chie?  
12. `__EFMigrationsHistory`?  
13. Chera Delay ghabl Migrate?  
14. migrationesho chie (team)?  
15. Chera Migration class commit nemishe?  
16. Local temp migration?  
17. Race Migrate multi-pod?  
18. depends_on healthy?  
19. Reporting health assets?  
20. Seed vs Migrate?  
21. DDL permission smell?  
22. Health public risk?  
23. Build cache restore csproj?  
24. Port map development?  
25. Ideal prod migration pipeline?

---

## Senario-ha (ba tozih)

### A) Laptop subh
Compose up → DB healthy → API Migrate → /health green → FE kar mikone.  
**Yani:** dependency order + auto schema.

### B) Redis off
/health Unhealthy. API shayad ba'dan fail-open blacklist (Day 25) — ama health mige «amadegi kamel nist».

### C) Do instance Dejban bedune lock
Har do Migrate → rare EF race.  
**Yani:** startup migrate for prod scale out nist.

### D) Schema change ba policy
Entity commit → deploy → migrationesho → OK.  
Kasi Migration commit mikone → review reject / conflict ba policy.

### E) Wrong host in container
Connection localhost → fail Migrate. Fix: `dejbandb`.

---

## Mini lab

1. `curl` / browser `/health` — JSON checks  
2. Stop redis container — health again  
3. Read `MigrationExtensions` + Delay  
4. `docker compose` file-ha — kodom port overlay  
5. Read Dejban Dockerfile stages  
6. Git status: Migration file unwanted?  
7. Reporting `/health/reporting-assets`  

---

## Resume

**kutah:**

> Operated Dejban’s ops baseline: ASP.NET health checks for PostgreSQL and Redis, layered Docker Compose for multi-database local/cloud stacks with multi-stage .NET 10 images, and an EF migration approach that uses startup `Migrate()` for local convenience while production schema evolves via server-side migrationesho without committing migration classes in app PRs.

**bullet-ha:**

- Exposed `/health` with NpgSql + Redis checks and detailed UI response writer  
- Documented Compose base/overlay ports and multi-stage Dockerfiles for microservices  
- Applied per-module `Database.Migrate()` on Dejban startup (8 DbContexts) with initializer delays  
- Followed team policy: entity changes in git; schema apply via migrationesho; local-only migrations cleaned before push  

**skill-ha:** `ASP.NET Health Checks, Docker, Docker Compose, Multi-stage Builds, EF Core Migrations, PostgreSQL, DevOps, Readiness Probes, .NET 10`

---

## File-haye mohem

| chi | koja |
|---|---|
| Health registration | `Dejban.Api/Program.cs` |
| ApplyMigrations | `Dejban.Api/Extensions/MigrationExtensions.cs` |
| Identity Migrate+seed | `IdentityServer/.../DbExtensions.cs` |
| Reporting assets health | `Reporting/Controllers/HealthController.cs` |
| Compose base | `docker-compose.yml` |
| Ports overlay | `docker-compose.development.yml` |
| App build overlay | `docker-compose.docker-*.yml` |
| Dockerfile mesal | `Dejban.Api/Dockerfile` |
| Policy note | Day 13 + `.cursor/rules/no-ef-migrations-in-repo.mdc` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 09 Microservices | DB per service → chand Postgres |
| 13 EF | migrationesho policy omigh |
| 18 DI | modules + connection strings |
| 28 MinIO | compose minio service |
| 30 Observability | health ≠ traces; complementary |
| 07 YARP | route to /health? |

---

## Chejori digest koni (ravesh-e sade)

1. Health = «halet khub-e?» (10 min)  
2. Compose = «jaebe-ha» (20 min)  
3. Dockerfile stages (15 min)  
4. Migrate local vs migrationesho (25 min) — **in ghesmat-e mohem-e mosahebe**  
5. Lab compose + /health (20 min)  
6. 25 soal (20 min)

---

## Glossary (sade)

| kalame | ma'ni-ye yek khati |
|---|---|
| Health check | test-e zende/amade budan |
| Readiness | amade-ye traffic |
| Compose | multi-container recipe |
| Volume | disk paydar container |
| Overlay | file compose ezafi |
| Multi-stage | chand FROM to Dockerfile |
| Migrate() | apply pending EF migrations |
| migrationesho | server process schema |
| Seed | data avaliye ba'd migrate |
| pg_isready | Postgres ready probe |

---

## Deep dive — chera 10 saniye Delay?

Docker Postgres «started» ≠ «accept connections». Healthcheck in ro behtar handle mikone. Delay = belt-and-suspenders. Behtar: `depends_on: condition: service_healthy` + retry Migrate (Polly Day 32).

---

## Deep dive — liveness vs readiness (k8s mindset)

Alan yek `/health` har do dependency ro check mikone. To Kubernetes:

- **liveness** fail → kill pod (restart)  
- **readiness** fail → az Service kharej (restart lazem nist)

Age Redis temporarily down, readiness fail OK; liveness fail → restart storm. Ideal: split endpoints. Dejban gap-e possible.

---

## Deep dive — seed ba'd migrate

Identity: Migrate → Delay 30s → Upsert SuperAdmin/sites/claims.  
**Yani:** schema avval, data ba'd. Event `SiteCreated` publish. Fail seed → throw (claims empty = bug getMe).

---

## Anti-pattern (ba tozih)

```csharp
// BAD: Migrate to har request
// GOOD: startup ya migrator job

// BAD: commit 5 Migration az 5 branch
// GOOD (Dejban): entity only; migrationesho

// BAD: health detailed ba connection string
// GOOD: status + check names bedune secret
```

---

## Interview 60s (ravoon)

> «We run Postgres, Redis, Rabbit and MinIO in Compose with healthchecks, and our APIs expose ASP.NET health endpoints for NpgSql and Redis. Images are multi-stage .NET 10 builds. For schema, local startup calls EF Migrate across module DbContexts for developer speed, but our team policy is that migration classes aren’t committed in feature PRs—the server migrationesho process owns generating and applying migrations after deploy.»

---

## Quick self-test

1. Dejban health deps? → NpgSql + Redis  
2. Endpoint? → `health`  
3. Dejbandb host port? → 18004  
4. Migrate chand context? → 8  
5. Delay? → 10s  
6. migrationesho? → server schema apply  
7. Migration to PR? → no (policy)  
8. Multi-stage final base? → aspnet runtime  
9. pg_isready? → DB container health  
10. Reporting health? → fonts/js/css  

---

## Final checklist

- [ ] Health chera + Dejban wiring  
- [ ] Compose layers + ports  
- [ ] Dockerfile stages  
- [ ] ApplyMigrations  
- [ ] migrationesho vs local  
- [ ] smells Delay/race  
- [ ] resume  

---

## Extra — «migrationesho» ra chejori to mosahebe tozih bedi (ravoon)

Begu:

«Ma nemikhaym har feature branch ye Migration file tolid kone chon merge conflict va tartib-e apply kharab mishe. Developer model ro avaz mikone. Ba'd az inke code ru-ye server raft, ye process be esm-e migrationesho migration ro misaze va ru-ye DB apply mikone. Local baraye test mitunim temporary migration dashte bashim ama commit nemikonim.»

In jomle = clear + honest + fargh ba world default.

---

## Extra — Compose networks sade

Hame service `networks: backend`. Pas `dejban-api` mitune `Host=dejbandb` resolve kone. Az laptop, port publish lazem. Do jahan: host vs network.

---

## Extra — Volume vs bind mount

Volume named (`dejbandb-data`) = Docker manage. Bind mount = folder host. DB data → volume. Source code hot reload → bind (dev tools).

---

## Extra — Health az YARP

Age monitoring az biroon miad, gateway bayad `/health` ro route kone ya sidecare. Check kon ApiGateway routes — shayad mostaghim be service. Ops detail.

---

## Extra — EF Migrate idempotent?

Bale: bar dovom pending nadare → no-op. Inke har start seda mishe «hamishe schema avaz» nemikone — faghat check history. Hazine: connection + query history.

---

## Map — boot Dejban.Api

```
Build DI (modules, health, MT, …)
Build app
UseCors
ApplyMigrations (delay 10s → 8× Migrate)
ApplySeedData
ApplyMediaMTX
MapHealthChecks /health
ExceptionHandler → LogContext → Serilog → Auth → Tenant → Endpoints
Run
```

---

## Map — developer schema change (policy)

```
Change entity
  → PR without Migration*.cs
  → Review/merge/deploy
  → migrationesho on server
  → apps roll forward
```

---

## Lab aha (sade)

1. /health green → stop postgres → red  
2. Delete Delay mentally — race ba slow disk  
3. `docker compose down -v` → data raft (volume wipe) — tarsnak  
4. Find Migration file local → yadat bashe commit nakoni  

---

## What Day 31 is *not*

- Kubernetes manifests full  
- Helm  
- Flyway/Liquibase compare deep  
- CI GitLab (Day 58)  

Focus: **health + compose/docker + migration reality Dejban**.

---

## Resume keywords (ATS)

`Health Checks` · `Docker` · `Docker Compose` · `multi-stage Dockerfile` · `EF Core Migrate` · `PostgreSQL` · `readiness` · `DevOps` · `database migrations` · `.NET`

---

## Band-e gharardad-e jadid — chejori in fasl (va azin be ba'd) neveshte mishe

Az Day 31 be ba'd, gharardad ye band-e ezafe dare:

> **Tozihat ravoontar va sade-tar bashan.** Yani: ghabl az code, ye dastan-e kuchik; ba'd «yani chi»; ba'd «chera»; ba'd smell. Kamtar telegram-line; bishtar jomle-ye kamel ke adam betune seda konad.

In fasl ghasdan hamin sabk ro peiyade karde:

- jomle-haye «yani chi / chera / farz kon» bishtar  
- jadval ba tozih-e ghabl, na faghat esm  
- policy migrationesho ba zaban-e mosahebe (honest)  
- deep dive-haye kuchik ke «chera in hack hast» ro migiran  

---

## Farz kon — ye ruz-e normal-e developer (dastan-e kamel)

Sobh laptop baz mikoni. Mikhay Dejban.Api + Identity + Redis + Rabbit + MinIO.

**Bedune Docker:** bayad 7 Postgres nasb koni, port set koni, Redis, Rabbit… sa'at-ha.

**Ba Docker Compose (development overlay):**

1. `docker compose -f docker-compose.yml -f docker-compose.development.yml up -d`  
2. Docker Postgres-ha ro miyare bala. Har kodum `pg_isready` midavad — yani «man amade-am connection begiram».  
3. To Visual Studio / `dotnet run` Dejban.Api. Connection string mige `Host=localhost;Port=18004` — yani az **host** miri be port-e publish-shode.  
4. App start mishe → `ApplyMigrations` → 10 saniye wait (shayad DB hanuz soft-e) → 8 ta `Migrate()` baraye 8 schema.  
5. Seed (age bashe) → ba'd `MapHealthChecks`.  
6. Browser: `https://localhost:..../health` → JSON: Healthy, PostgreSQL Healthy, Redis Healthy.

**Yani chi be zaban-e adam?**  
Stack-e local mesl-e ye factory-e kuchik: jabe-ha (container) + check-e dar (health) + sync-e naqshe-ye sakhteman (migrate) + ba'd dar-e vorud-e moshtari (API).

Age Redis down bashe: health Unhealthy. API shayad hanuz ye endpoint bedahad, ama «amadegi-ye kamel» nist — monitoring in ro mibine.

---

## Farz kon — taghir-e schema ba policy (dastan)

Mikhay `DateOfBirth` ro optional koni.

1. Entity: `DateOnly? DateOfBirth`  
2. Fluent config: `.IsRequired(false)`  
3. Commit + PR — **bedune** `*Migration*.cs`  
4. Reviewer midune: schema ba migrationesho miad  
5. Deploy code  
6. migrationesho ru-ye server migration misaze / apply mikone  
7. App instances schema jadid ro mibinan  

**Local ghabl deploy:** mituni `dotnet ef migrations add …` bezani ta laptopet test she. Ba'd az test, un file-ha ro **pak** mikoni ghabl push — chon policy mige manba'-e schema apply = server, na 5 branch-e parallel.

**Chera in qadr sakht be nazar miad?**  
Chon team yek bar dard-e merge-e Migration + tartib-e eshtebah-e `__EFMigrationsHistory` ro khorde. Cost-e discipline < cost-e hell-e prod.

**World default:** aksar company-ha Migration to git commit mikonan. To mosahebe **har do** ro bedun; begu «in team server-side migrator dare». Honesty = skor.

---

## Chera 8 ta DbContext, ye Migrate-e zigzagi?

Dejban modular monolith-e: Visitors, Personnels, SecurityPatrols, Vehicles, Armory, CashLogistics, Inventory, WeighBridge — har kodum DbContext + schema-ye khodesh (Day 09/13/18).

`ApplyMigrations` ye list-e sade-st:

```
Visitors → Personnels → SecurityPatrols → Vehicles
→ Armory → CashLogistics → Inventory → WeighBridge
```

**Yani chi?** Yek process, chand schema. Migrate per context = har schema history-e joda dare. Age yeki fail she, ba'di-ha shayad ejra nashan (tartib sequential) — boot log ro bekhun.

**Chera Delay ghabl hame?**  
Yek wait baraye «DB shayad amade nist». Behtar bood: retry per Migrate (Polly Day 32) ya `depends_on: service_healthy` vaghti app ham to Compose-e.

---

## Health JSON — chejori bekhuni (sade)

Ba `UIResponseWriter`, response roughly:

- `status`: Healthy / Degraded / Unhealthy  
- `entries.PostgreSQL.status`  
- `entries.Redis.status`  
- duration-ha  

**Farz kon:** PostgreSQL Healthy, Redis Unhealthy → overall Unhealthy (mamulan).

**Pas chi kar koni?**

1. `docker compose ps` — redis Up-e?  
2. Port 6379 conflict ba Redis local digar?  
3. Connection string typo?  
4. Network: app to container `Host=redis` vs host `localhost`

Health = map-e diagnostik, na magic.

---

## Docker — layer caching ba zaban-e adam

Dockerfile avval **faghat csproj** copy mikone → `dotnet restore`.  
Ba'd source copy → build.

**Chera?**  
Age faghat ye `.cs` avaz she, layer-e restore az cache miad — build sari'tar. Age `csproj` avaz she, restore dobare.

**Yani chi baraye resume?**  
«Optimized Docker builds with restore-layer caching and multi-stage publish.»

Final stage = aspnet runtime, na sdk. Image kuchiktar + kamtar tool baraye attacker.

---

## Compose: base vs overlay — ye mesal-e zehnii

`docker-compose.yml`:

- service `dejbandb` tarif shode  
- volume `dejbandb-data`  
- **port publish nist** (ya kam) — baraye inke to Docker network khali hostname bashe  

`docker-compose.development.yml`:

- `ports: "18004:5432"` — az laptop `localhost:18004`  

`docker-compose.docker-development.yml`:

- service `dejban-api` build mikone  
- `depends_on: dejbandb: condition: service_healthy`  
- env connection `Host=dejbandb`  

**Yani:** yek haqiqat-e service; chand «chejori run». Merge-e file-ha ba `-f` `-f`.

---

## Seed vs Migrate — farq-e sade (yek bar digar ba dastan)

| | Migrate | Seed |
|---|---|---|
| chie? | sakhteman (table/column) | mohtava (SuperAdmin, site, claim) |
| key ejra? | schema jadid / pending | data avaliye / idempotent upsert |
| fail = | app schema nadare | login/getMe khali |

**Farz kon:** Migrate OK, Seed fail → table hast, user admin nist → FE login shekast. Pas seed ham «health-e business»-e soft-e — ama alan to `/health` nist; to log-e startup-e.

Identity: ba'd Migrate ye Delay digar (~30s) ghabl upsert — hamun smell-e wait.

---

## Prod-ish fikr — 4 gozine baraye schema

| ravesh | khub? |
|---|---|
| Startup `Migrate()` multi-replica | bad — race |
| Startup Migrate + leader election | ok-ish, pichide |
| Job/Init container migrator | khub — k8s pattern |
| **migrationesho ba'd deploy** | Dejban team policy |

To mosahebe: ideal = migrator joda; Dejban = hybrid (code Migrate local + policy server).

---

## Ertebat Health ba Day 30 (Observability) — ye jomle-ye ravoon

Day 30 mige: «chi shod to request? chera kond?» (log/trace/metric).  
Day 31 mige: «aslan zende-am va dependency-am up-e?» (boolean-ish).

Har do lazem-an. Health green + trace por az error = momken (business bug). Health red + trace nadaari = infra.

---

## Ertebat ba Day 07 YARP

Client / k8s probe shayad be **gateway** bezane, na mostaghim Dejban.Api. Pas:

- ya YARP `/health` ro forward mikone  
- ya ApiGateway khodesh health-e joda dare (`/health/reporting-routes` mesal)  
- ya probe mostaghim be service port dakheli  

Ops bayad bedune kodom URL «source of truth»-e readiness-e.

---

## 10 jomle ke bayad betuni seda koni (fluency drill)

1. Health check yani dependency-aware readiness, na faghat process up.  
2. Dejban `/health` = NpgSql + Redis + UI JSON writer.  
3. Compose overlay = base tarife + development ports.  
4. Host `localhost:18004` ≠ container `Host=dejbandb`.  
5. Multi-stage = sdk build, runtime run.  
6. `Database.Migrate()` pending-ha ro apply mikone; dobare no-op.  
7. Dejban 8 context joda Migrate mishe.  
8. `Task.Delay(10000)` wait-e DB-e — smell; better healthy depends + retry.  
9. Team: entity to git; Migration class to feature PR na; migrationesho server.  
10. Local temp migration OK; ghabl commit pak.

Age in 10 ta ravoon nisti — fasl tamum nashode.

---

## Soalat-e «chera» (javab-e yek khati + nim khat)

**Chera Redis to health-e Dejban hast?**  
Chon HybridCache / blacklist / infra-ye asosi; bedunesh raftar avaz mishe.

**Chera chand Postgres?**  
Bounded context isolation — Day 09.

**Chera volume?**  
Ta `compose down` (bedune `-v`) data bemune.

**Chera migrationesho?**  
Yek owner baraye schema apply; kamtar conflict.

**Chera health detailed JSON?**  
Debug asun; prod sometimes summarize (info leak).

---

## Checklist-e ghabl-e mosahebe (Day 31)

- [ ] Liveness vs readiness ba mesal  
- [ ] AddNpgSql + AddRedis koja  
- [ ] Port 18004 = dejbandb  
- [ ] 8 context name (hadeaqal 4 tasho)  
- [ ] Delay 10s chera  
- [ ] migrationesho vs world default  
- [ ] Local temp migration rule  
- [ ] Multi-stage one-liner  
- [ ] depends_on healthy vs Delay  
- [ ] Resume paragraph seda kon  

---

## Khoruj-e zehni (ye paragraph baraye khodet)

> Man midunam chejori stack-e local ba Compose miad bala, chejori health mige DB/Redis ok-an, chejori image multi-stage sakhte mishe, va chejori schema to Dejban: local ba `Migrate()` sari'e, ama policy-e team ine ke Migration class to PR-e feature nist va server ba migrationesho schema ro pish mibare. In fargh ro to mosahebe honest tozih midam.

Age in paragraph mal-e to shod — Day 31 done.

---

*Day 31 tamum. Ba'd: Day 32 — Polly (amade). Fehrest: [README.md](./README.md).*
