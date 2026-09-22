# Day 57 — Testcontainers + Bogus

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** unit (Day 56 InMemory) kafist? Postgres/Redis vaghe'i to test?

**Javab Dejban (honesty):**

| tool | naqsh |
|---|---|
| **Testcontainers** (`PostgreSql` + `Redis`) | Docker container sari baraye integration |
| **WebApplicationFactory\<Program\>** | boot API Dejban ba connection string override |
| **Bogus** (`Faker`) | data fake (esm, code, tarikh) |
| **xUnit CollectionFixture** | yek bar start container baraye suite |
| **MediatR `ISender`** | call command/query bedune HTTP (bishtar) |

Zincir:

```
dotnet test *.IntegrationTests
  → IAsyncLifetime: Start Postgres + Redis containers
  → ConfigureWebHost: ConnectionStrings:Postgres/Redis = container CS
  → WebApplicationFactory boots Program
  → BaseIntegrationTest: scope + Sender (+ DbContext/HttpClient)
  → Fact/Theory: Send(command) + FluentAssertions
  → Dispose: stop containers
```

Olgu factory:

```csharp
new PostgreSqlBuilder().WithImage("postgres:latest").WithDatabase("dejban")...Build();
new RedisBuilder().WithImage("redis:latest").Build();
Environment.SetEnvironmentVariable("ConnectionStrings:Postgres", _dbContainer.GetConnectionString());
```

**Band-e gharardad-e jadid:** farz kon / yani chi / chera + **honesty:** happy-path create/get often **commented** (TODO VisitorType); validation/NotFound zende.

Day 56 = xUnit unit/arch. Day 25 = Redis HybridCache. Day 13 = EF/Npgsql. **In ruz = integration harness.**

---

# BAKHSH-E AVAL: WORLD — Testcontainers + Bogus

## Farz kon — lab vs maket cardboard

**InMemory EF (Day 56 RT):** maket cardboard — sari, ama Postgres quirks (schema, constraint, SQL raw) kam.  
**Testcontainers:** lab kuchek Docker — Postgres/Redis real process, throw away ba'd az test.

**Yani chi:** integration test = app + real infra deps, na mock hame chiz.

---

## Testcontainers chie?

.NET library (Testcontainers for .NET): start Docker images from tests.

```csharp
var pg = new PostgreSqlBuilder().WithImage("postgres:16").Build();
await pg.StartAsync();
var cs = pg.GetConnectionString();
```

| mafhum | ma'ni |
|---|---|
| Builder | image, ports, creds |
| StartAsync | pull+run container |
| GetConnectionString | ready CS |
| IAsyncLifetime | xUnit lifecycle |
| Docker required | daemon must run |

Modules Dejban: `Testcontainers.PostgreSql`, `Testcontainers.Redis` (v4.9).

---

## Bogus chie?

Fake data generator (C# port of faker):

```csharp
var faker = new Faker();
faker.Name.FirstName();
faker.Random.Replace("##########"); // national-like
faker.Date.Past(40, DateTime.Today.AddYears(-18));
faker.PickRandom<Gender>();
```

**Chera?** Unique-ish inputs; kam collision; khundani-tar az `"test1"`.

---

## WebApplicationFactory

ASP.NET Core testing host: boots real `Program` / DI pipeline in-process.

Override config → point to Testcontainers.  
`CreateClient()` → HttpClient optional; Dejban often uses `ISender` directly.

---

## Pyramid reminder

```
E2E Playwright (FE)
Integration Testcontainers  ← emruz
Unit xUnit / NetArchTest
```

---

# BAKHSH-E DOVOM: DEJBAN — harness

## Qesmat 1 — koja

| project | packages |
|---|---|
| `Dejban.Modules.Visitors.IntegrationTests` | Testcontainers PG+Redis, Bogus, Mvc.Testing, xUnit |
| `Dejban.IntegrationTests` | same (solution-level / cross-module intent) |
| `Visitors.UnitTests` | Bogus only (no containers) |

Versions (`Directory.Packages.props`): Bogus 35.6.5; Testcontainers.* 4.9.0.

Presentation csproj-ha: `InternalsVisibleTo` → `*.IntegrationTests`.

---

## Qesmat 2 — IntegrationTestWebAppFactory

```csharp
public class IntegrationTestWebAppFactory : WebApplicationFactory<Program>, IAsyncLifetime
{
    private readonly PostgreSqlContainer _dbContainer = new PostgreSqlBuilder()
        .WithImage("postgres:latest")
        .WithDatabase("dejban")
        .WithUsername("postgres")
        .WithPassword("postgres")
        .Build();

    private readonly RedisContainer _redisContainer = new RedisBuilder()
        .WithImage("redis:latest")
        .Build();

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        Environment.SetEnvironmentVariable("ConnectionStrings:Postgres", _dbContainer.GetConnectionString());
        Environment.SetEnvironmentVariable("ConnectionStrings:Redis", _redisContainer.GetConnectionString());
    }

    public async Task InitializeAsync()
    {
        await _dbContainer.StartAsync();
        await _redisContainer.StartAsync();
    }
    // DisposeAsync → StopAsync both
}
```

**Chera env vars?** App Options/CS bind az configuration — override ghabl az host build.  
**Chera Redis ham?** HybridCache/Redis infra (Day 25) — app boot momken niaz dashte bashe.  
**Chera na RabbitMQ container?** Emruz package nist — messaging integration incomplete / external or mocked path. Honesty.

**Docker:** bedune Docker daemon → StartAsync fail.

---

## Qesmat 3 — CollectionFixture (yek container baraye suite)

```csharp
[CollectionDefinition(nameof(IntegrationTestCollection))]
public sealed class IntegrationTestCollection : ICollectionFixture<IntegrationTestWebAppFactory>;

[Collection(nameof(IntegrationTestCollection))]
public abstract class BaseIntegrationTest { ... }
```

**Yani chi:** hame test class-ha **share** yek factory → Postgres/Redis **yek bar** start (sari-tar az per-class).  
Tradeoff: shared DB state → need cleanup / isolation discipline.

---

## Qesmat 4 — BaseIntegrationTest (Visitors)

```csharp
_scope = factory.Services.CreateScope();
HttpClient = factory.CreateClient();
Sender = GetRequiredService<ISender>();
DbContext = GetRequiredService<VisitorsDbContext>();
Faker = new Faker(); // static on Visitors base
```

`CleanDatabaseAsync`: raw SQL DELETE inbox/outbox/visitors schema tables — reset between tests when called.

**Chera Sender na faqat HttpClient?** Faster, skip auth HTTP sometimes; tests application pipeline + EF + validators.  
HttpClient available for endpoint-level later.

---

## Qesmat 5 — Bogus to commands

`CreateVisitorTests` / `UpdateVisitorTests`:

```csharp
NationalCode = nationalCode ?? Faker.Random.Replace("##########"),
Gender = gender ?? Faker.PickRandom<Gender>().ToString(),
DateOfBirth = dateOfBirth ?? Faker.Date.Past(40, DateTime.Today.AddYears(-18)),
```

`TheoryData` InvalidCommands: empty first/last name → expect `ErrorType.Validation`.

Valid create Theory **commented** — TODO seed VisitorType first.

---

## Qesmat 6 — zende vs khab tests (honesty)

| test | status |
|---|---|
| Create/Update invalid → Validation | **live** |
| Get/Update NotFound | **live** |
| Create/Get/Update success path | **commented** (VisitorType prerequisite) |
| Cross-module propagate (Dejban.IntegrationTests) | **commented** + Poller |

**Resume:** «Integration harness with Testcontainers Postgres/Redis and Bogus; validation and not-found paths green; full create flows blocked on fixture seed work.»

---

## Qesmat 7 — Poller (eventual consistency)

```csharp
Poller.WaitAsync(TimeSpan.FromSeconds(15), async () => await Sender.Send(query));
```

PeriodicTimer 1s — wait until ErrorOr success or timeout.  
Designed for outbox/inbox / other module catch-up (commented CreateVisitor_Should_Propagate...).

**Chera?** Messaging async — assert immediate often flake.

---

## Qesmat 8 — CleanDatabaseAsync

Deletes:

- `visitors.inbox_message_consumers` / `inbox_messages`  
- `outbox_*`  
- `visitors.visitors`

Schema-aware (Day 13 multi-schema). Call when tests mutate and share container.

Smell: not auto-called in every Fact — discipline manual.

---

## Qesmat 9 — contrast Unit InMemory vs Integration PG

| | RT Unit Day 56 | Visitors Integration |
|---|---|---|
| DB | EF InMemory | Postgres container |
| Cache | n/a | Redis container |
| Host | new Handler(db) | full WebApplicationFactory |
| Speed | ms | seconds (Docker) |
| Fidelity | medium | high |

---

## Qesmat 10 — prerequisites run

1. Docker Desktop / engine running  
2. First run pulls `postgres:latest`, `redis:latest` (slow)  
3. `dotnet test ...IntegrationTests`  
4. CI needs Docker-in-Docker or privileged runner (Day 58)

---

# BAKHSH-E SEVOM: WORLD extras

## Reuse containers

CollectionFixture = reuse. Alternative: Ryuk cleanup, `.WithReuse(true)` experimental — know concept.

## Fixed ports vs random

Builders assign random host ports — CS includes them — parallel-safe-ish.

## Migrations

App must migrate/ensure schema on startup (ApplyMigrations / migrate path Day 31). If boot skips migrate → tables missing → fail. Know your Program startup.

## Bogus locales

`new Faker("fa")` possible — Dejban often default en names even for FA product (OK for IDs).

## Replace patterns

`##########` = 10 digits — national code shape; not checksum-valid Iranian code — enough for many validators.

---

# BAKHSH-E CHAHAROM: jadval mosahebe

| Q | A |
|---|---|
| Why Testcontainers? | real Postgres/Redis |
| Images? | postgres:latest, redis:latest |
| How wire CS? | env ConnectionStrings:* |
| Share containers? | ICollectionFixture |
| Fake data? | Bogus Faker |
| Call app? | ISender (+ HttpClient) |
| Happy path create? | often commented |
| RabbitMQ TC? | not in packages |
| Docker need? | yes |
| Poller? | wait async success |

---

# BAKHSH-E PANJOM: farz kon / senario

## Se dastan

**1) First `dotnet test` Integration**  
Pull images → start PG/Redis → factory boot → NotFound Fact green.

**2) Enable ValidCommands**  
Seed VisitorType in Arrange → uncomment Theory → assert `IsError` false + row in DbContext.

**3) Cross-module**  
Uncomment Poller test when ticketing/customer module contract exists — wait outbox.

---

## Smell-ha

1. Happy paths commented — suite under-exercises write path  
2. `postgres:latest` non-pinned — CI drift  
3. No RabbitMQ testcontainer — messaging IT weak  
4. Env SetEnvironmentVariable process-wide — careful parallel assemblies  
5. CleanDatabase not always invoked  
6. Duplicate factory code Visitors vs Dejban.IntegrationTests  
7. CommandHelpers empty stub  
8. Gender from Bogus.DataSets.Name static import — odd coupling  

---

## Debug checklist

| symptom | check |
|---|---|
| Cannot connect Docker | daemon / permissions |
| Image pull timeout | network / mirror |
| Relation does not exist | migrations on boot |
| Redis connection fail | CS env name mismatch |
| Flaky shared state | CleanDatabase / unique Faker |
| Validation always fail | FluentValidation rules vs Bogus shape |
| Slow suite | fixture reuse vs per-test containers |

---

## 25 soal-e mosahebe

1. Testcontainers chie?  
2. Chera na faqat InMemory?  
3. Kodom images?  
4. WebApplicationFactory?  
5. ICollectionFixture chera?  
6. Bogus chie?  
7. Chejori CS override?  
8. ISender vs HttpClient?  
9. CleanDatabase?  
10. Poller chera?  
11. Happy path status?  
12. Docker required?  
13. Redis chera to IT?  
14. RabbitMQ?  
15. InternalsVisibleTo?  
16. TheoryData invalid?  
17. Day 56 contrast?  
18. latest tag smell?  
19. Version packages?  
20. Multi-schema DELETE?  
21. Faker.Random.Replace?  
22. IAsyncLifetime?  
23. Day 25 link?  
24. CI need?  
25. One-liner Day 57?

---

## Senario-ha

**S1:** Pin `postgres:16-alpine` — reproducible CI.  
**S2:** Add `Testcontainers.RabbitMq` — full bus IT.  
**S3:** Auto-clean in BaseIntegrationTest ctor/Dispose.  
**S4:** Shared helper library for factories (DRY).  
**S5:** Bogus fa locale for display-name tests.

---

## Mini lab

1. Read Visitors `IntegrationTestWebAppFactory`  
2. Read `BaseIntegrationTest` + CleanDatabase SQL  
3. Trace CreateVisitorTests Invalid Theory  
4. Find commented ValidCommands TODO  
5. Open Poller.cs  
6. Confirm Docker running → `dotnet test` one IT project  

---

## Resume (1 paragraph)

> Dejban integration tests boot the real API with **WebApplicationFactory**, backed by **Testcontainers** for **PostgreSQL** and **Redis**, share containers via an xUnit **CollectionFixture**, and build inputs with **Bogus**. Tests typically exercise MediatR commands/queries (validation and not-found paths are live; full create flows still need VisitorType seeding). **Docker** is required; RabbitMQ is not yet containerized in this harness.

Keywords: `Testcontainers` · `PostgreSqlContainer` · `RedisContainer` · `WebApplicationFactory` · `Bogus` · `ICollectionFixture` · `ISender` · `Poller`

---

## File-haye mohem

| path | chera |
|---|---|
| `...Visitors.IntegrationTests/Abstractions/IntegrationTestWebAppFactory.cs` | containers |
| `.../BaseIntegrationTest.cs` | scope + clean |
| `.../Visitors/*VisitorTests.cs` | Bogus + Facts |
| `Dejban.IntegrationTests/Abstractions/*` | solution-level + Poller |
| `Directory.Packages.props` | versions |
| Day 56 | unit contrast |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 13 | EF Npgsql schemas |
| 25 | Redis |
| 31 | Docker / migrations |
| 56 | xUnit unit vs this |
| **57** | this |
| 58 | CI + Docker runners |

---

## Chejori digest koni

1. Docker containers from tests  
2. Factory + env CS  
3. Shared fixture  
4. Bogus data  
5. Honesty commented happy paths  

---

## Glossary

| term | ma'ni |
|---|---|
| Testcontainers | Docker-from-tests |
| WebApplicationFactory | in-process ASP.NET host |
| CollectionFixture | shared xUnit fixture |
| Bogus / Faker | fake data |
| IAsyncLifetime | async setup/teardown |
| Poller | retry until success |
| Connection string override | point app at container |
| Ryuk | TC cleanup sidecar (internal) |

---

## Deep dive — why both PG and Redis

App infrastructure registers both; boot may touch Redis for cache. Missing Redis → startup exception even if test only hits DB.

---

## Deep dive — MediatR integration style

Pros: stable, no JWT dance.  
Cons: skips HTTP/auth middleware — complement with a few HttpClient tests later.

---

## Deep dive — ErrorOr asserts

`result.IsError`, `FirstError.Type == Validation`, `Should().Be(VisitorErrors.NotFound(...))` — matches app Result style (Day 11 family).

---

## Anti-pattern

| bad | better |
|---|---|
| Shared DB no cleanup | CleanDatabase / transactions |
| latest tags forever | pin versions |
| Only InMemory for PG SQL | Testcontainers |
| Uncomment create without seed | seed VisitorType |
| Claim full IT coverage | honesty partial |

---

## Interview 60s

«Integration tests use Testcontainers to run Postgres and Redis, wire connection strings into WebApplicationFactory, and share that host with a collection fixture. Bogus generates visitor fields. We assert validation and not-found through MediatR; success-path creates are scaffolded but still need type seeding. Docker is mandatory.»

---

## Quick self-test

1. Containers? → Postgres + Redis  
2. Host? → WebApplicationFactory  
3. Share? → CollectionFixture  
4. Data? → Bogus  
5. Call? → ISender  
6. Happy create? → commented  
7. Docker? → yes  

---

## Final checklist

- [ ] Testcontainers idea  
- [ ] factory + env  
- [ ] fixture lifecycle  
- [ ] Bogus  
- [ ] live vs commented  
- [ ] Poller  
- [ ] resume  

---

## Extra — Farz kon lab Docker

Har `dotnet test` Integration = lab pop-up: Postgres + Redis.  
Bogus = generator esm fake baraye moz.  
Sender = dastor mostaghim be maghz app.  
Comment-ha = «asansor hanuz nasb nashode» (VisitorType).

---

## Extra — time cost

Cold: image pull minutes.  
Warm: container start ~few seconds + migrate.  
Unit ACL: ms — use right layer.

---

## Extra — parallel collections

Different CollectionDefinition names → parallel possible.  
Same collection → serialized for that fixture — intentional.

---

## Extra — DisposeAsync new keyword

`public new async Task DisposeAsync` hides WebApplicationFactory dispose — ensure containers stop; know pattern quirk.

---

## Extra — HttpClient future

`factory.CreateClient()` ready for `/api/visitors` auth e2e-ish without Playwright.

---

## Extra — seed strategy for VisitorType

Options:  
1. Sender.Send(CreateVisitorTypeCommand) in Arrange  
2. DbContext.Add + SaveChanges  
3. SQL script in InitializeAsync  

Unblock ValidCommands.

---

## Extra — Respawn WORLD

Library wipe DB between tests — alternative to manual DELETE. Not in Dejban props — optional improve.

---

## Band-e gharardad-e jadid

Testcontainers = lab portable.  
Postgres/Redis = dastgah lab.  
WebApplicationFactory = roshan kardan app.  
CollectionFixture = yek lab baraye hame.  
Bogus = generator data.  
Sender = telephon mostaghim.  
Poller = sabr baraye payam.  
Comment = kar-e nime-tamam seed.

---

## 10 jomle fluency

1. Integration tests need Docker.  
2. Testcontainers starts Postgres and Redis.  
3. Connection strings are overridden via environment variables.  
4. WebApplicationFactory boots Program.  
5. A collection fixture shares one factory.  
6. Bogus builds fake visitor fields.  
7. Tests send MediatR commands.  
8. Validation and not-found cases run today.  
9. Success creates wait on VisitorType seeding.  
10. Poller helps async cross-module asserts.

---

## Extra — version pins

| pkg | ver |
|---|---|
| Bogus | 35.6.5 |
| Testcontainers.PostgreSql | 4.9.0 |
| Testcontainers.Redis | 4.9.0 |
| Microsoft.AspNetCore.Mvc.Testing | (central) |

---

## Extra — security note

Factory uses postgres/postgres local only in containers — never production secrets.

---

## Extra — CI shapes

| runner | note |
|---|---|
| GitLab Docker executor | dind / socket |
| shell + Docker | simpler |
| no Docker | skip IT category |

Day 58 expands.

---

## Extra — category traits WORLD

`[Trait("Category","Integration")]` — filter `dotnet test --filter`. Optional.

---

## Extra — compare TestServer only

WebApplicationFactory without TC still uses whatever CS in appsettings — risk hitting shared/dev DB. TC isolates.

---

## Extra — 10 soalat sari

1. Docker? yes  
2. PG+Redis? yes  
3. RabbitMQ TC? no  
4. Bogus? yes  
5. Fixture share? yes  
6. Sender? yes  
7. Valid create live? no  
8. NotFound live? yes  
9. Poller? yes  
10. Clean SQL schema? visitors.*  

---

## Extra — Diagram 30s

Begu: «Tests start Postgres and Redis with Testcontainers, point the API host at them, share one factory, fake data with Bogus, and send commands through MediatR.»

---

## Extra — Common bugs

| symptom | likely |
|---|---|
| Docker.DotNet errors | daemon down |
| Auth failure Redis | wrong CS key |
| Timeout Poller | outbox not running |
| Unique violation | no clean + same national code |
| Host build fail | Program deps unmet |

---

## Extra — Layer checklist

| layer | tech |
|---|---|
| Containers | Testcontainers |
| Host | WebApplicationFactory |
| Lifecycle | IAsyncLifetime + CollectionFixture |
| Data | Bogus |
| Assert | FluentAssertions + ErrorOr |
| Reset | CleanDatabase SQL |
| Async wait | Poller |

---

## Extra — Farz kon add RabbitMQ

1. Package Testcontainers.RabbitMq  
2. Start in factory  
3. Set RabbitMqTransport env  
4. Poller asserts consumer side  

---

## Extra — UnitTests Bogus overlap

Same Faker patterns in domain unit (commented) — one vocabulary across layers.

---

## Extra — DateTime UTC

Commented create sets `DateOfBirth = DateTime.UtcNow` / `ToUniversalTime` — Npgsql UTC sensitivity (Day 13).

---

## Extra — Multi-module InternalsVisibleTo

Personnels/WeighBridge/SecurityPatrols Presentation also grant IntegrationTests — pattern ready even if IT project missing.

---

## Extra — empty CommandHelpers

Placeholder for shared create helpers — fill when un-commenting flows.

---

## Extra — Final fluency drill

«We run Dejban integration tests on real Postgres and Redis via Testcontainers, host the API with WebApplicationFactory, share it through a collection fixture, and generate inputs with Bogus. Live tests cover validation and not-found; full creates still need seeding.»

---

## Extra — Capacity planning

Don't run full IT on every save — pre-commit unit+arch; CI IT nightly/PR. Balance.

---

## Extra — image caching

CI cache Docker layers — huge win after first pull.

---

## Extra — health wait

TC waits for container ready; still app migrate race — if flake, explicit wait/migrate call.

---

## Khoruj-e zehni

> Midunam integration Dejban ba Testcontainers Postgres+Redis + WebApplicationFactory + CollectionFixture + Bogus kar mikone; Sender MediatR; validation/NotFound zende; happy-path create commented; Docker lazeme; RabbitMQ TC hanuz nist.

Age in paragraph mal-e to shod — Day 57 done.

---

*Day 57 tamum. Ba'd: Day 58 — GitLab CI + PM2 (amade). Fehrest: [README.md](./README.md).*