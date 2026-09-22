# Day 56 — xUnit + NetArchTest

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** backend Dejban chejori test / architecture enforce mikone?

**Javab (honesty):**

| layer | tool | koja |
|---|---|---|
| **Unit** | **xUnit** + **FluentAssertions** | ACLServer, RequestTracker (ghavi); Visitors UnitTests (thin / commented) |
| **Architecture** | **NetArchTest.Rules** + xUnit | `Visitors.ArchitectureTests` (layers + conventions); `Dejban.ArchitectureTests` (module isolation — **gap**) |
| **Integration** | xUnit (+ Testcontainers Day 57) | `*.IntegrationTests` — in ruz deep nist |

Zincir-ezehni:

```
dotnet test
  → xUnit discovery [Fact] / [Theory]
  → Unit: handler/evaluator logic + InMemory EF (RT)
  → Arch: Types.InAssembly(...).Should().NotHaveDependencyOn(...)
  → FluentAssertions: result.Should().Be(...)
```

Olgu NetArchTest:

```csharp
Types.InAssembly(DomainAssembly)
    .Should()
    .NotHaveDependencyOn(ApplicationAssembly.GetName().Name)
    .GetResult()
    .ShouldBeSuccessful();
```

Olgu unit (ACL):

```csharp
[Fact]
public void Authorized_vehicle_is_allowed()
{
    Evaluate(Fixture()).Decision.Should().Be(VehicleAccessDecisions.Allow);
}
```

**Band-e gharardad-e jadid:** farz kon / yani chi / chera + **honesty gap** ModuleTests empty + Visitors domain unit commented.

Day 09 = Clean Architecture map. Day 55 = FE Playwright. Day 57 = Testcontainers+Bogus. **In ruz = xUnit + NetArchTest.**

---

# BAKHSH-E AVAL: WORLD — xUnit + architecture tests

## Farz kon — baresi karkhane vs nagshe sakhteman

**xUnit unit:** yek charkh / yek gheiych — Evaluate, Handle command.  
**NetArchTest:** nagshe-ye sakhteman — «Domain nabayad Application ra reference kone» — compile-time-ish via reflection on assemblies.

Har do xUnit runner mishe; tafavot: **behavior** vs **structure**.

---

## xUnit chie?

.NET test framework (ba NUnit/MSTest). Style attribute-based:

| API | ma'ni |
|---|---|
| `[Fact]` | yek test bedune params |
| `[Theory]` + `[InlineData]` | parameterized |
| `IDisposable` ctor | setup/teardown per class instance |
| `IAsyncLifetime` | async dispose |
| `IClassFixture<T>` | shared fixture per class |
| `ICollectionFixture<T>` | shared across classes |

Assert: often **FluentAssertions** (`Should().Be`) — khundani-tar az `Assert.Equal`.

Runner: `dotnet test`, VS Test Explorer, CI.

---

## NetArchTest chie?

Library: write unit tests that scan assemblies with fluent rules.

```csharp
Types.InAssembly(asm)
  .That().ImplementInterface(typeof(ICommand))
  .Should().BeSealed()
  .GetResult();
```

**Chera?** Clean Architecture / naming conventions **enforce**, na faqat docs. PR ke Domain→Infrastructure add kone → test red.

Alternatives WORLD: ArchUnitNET, custom analyzers — Dejban = NetArchTest.Rules.

---

## Test pyramid backend

```
        /\     E2E / Playwright (FE Day 55)
       /  \    Integration (DB, bus) Day 57
      /____\   Unit xUnit  ← emruz ghavi dar ACL/RT
     / arch \  NetArchTest ← Visitors template
```

---

# BAKHSH-E DOVOM: DEJBAN — koja chi hast

## Qesmat 1 — map proje-ha

| project | noe |
|---|---|
| `ACLServer.UnitTests` | unit — evaluators, contracts |
| `RequestTracker.UnitTests` | unit — commands, services, InMemory DB |
| `Dejban.Modules.Visitors.UnitTests` | unit scaffold — **Facts commented** |
| `Dejban.Modules.Visitors.ArchitectureTests` | **NetArchTest** layers + domain/app/presentation rules |
| `Dejban.ArchitectureTests` | cross-module — **currently weak** |
| `*.IntegrationTests` | Day 57 territory |

Central versions (`Directory.Packages.props`):

| package | version (approx) |
|---|---|
| xunit | 2.9.3 |
| xunit.runner.visualstudio | 3.1.5 |
| FluentAssertions | 8.8.0 |
| NetArchTest.Rules | 1.3.2 |
| Microsoft.NET.Test.Sdk | (central) |

`<Using Include="Xunit" />` — global usings in test csproj.

---

## Qesmat 2 — NetArchTest Visitors: LayerTests

```csharp
Domain → not Application
Domain → not Infrastructure
Application → not Infrastructure
Application → not Presentation
Presentation → not Infrastructure
```

**Yani chi:** dependency rule Clean Architecture (Day 09) — **automated**.

**Chera Presentation↛Infrastructure?** Ideal: Presentation→Application only. (Day 09 also notes real-world smell ba IntegrationEventHandler base — rules still encode intent.)

---

## Qesmat 3 — DomainTests conventions

| rule | ma'ni |
|---|---|
| DomainEvents sealed | no unintended inheritance |
| name ends `DomainEvent` | discoverability |
| Entity private parameterless ctor | EF + encapsulation |
| Entity no public ctors | force factories (`Create`) |

Mixed: NetArchTest for sealed/naming; reflection loop + FluentAssertions for constructors.

---

## Qesmat 4 — ApplicationTests conventions

Commands/Queries/Handlers/Validators/DomainEventHandlers:

- sealed  
- naming suffix (`Command`, `CommandHandler`, `Query`, …)  
- handlers + validators **NotBePublic** (internal)

**Chera NotBePublic?** Hide from other modules; DI still registers via assembly scan.

---

## Qesmat 5 — PresentationTests

`IConsumer<>` (MassTransit) in Presentation:

- not public, sealed  
- name ends `IntegrationEventHandler`

**Yani chi:** integration event handlers live presentation/consumers layer — naming contract.

---

## Qesmat 6 — Dejban.ArchitectureTests ModuleTests (gap)

```csharp
string[] otherModules = [];
// ...
.Should().NotHaveDependencyOnAny(otherModules)
```

**Honesty:** empty array → test **almost always green** — does not yet enforce Visitors↛OtherModules. Day 09 smell documented.

**Ideal:** fill `otherModules` with other module namespaces when more modules grow.

---

## Qesmat 7 — ACLServer unit (ghavi behavior)

`VehicleAccessDecisionEvaluatorTests` — pure decision table:

- authorized → Allow  
- unknown plate → ManualRequired (agent) / Deny (operator)  
- blacklist → denied  
- outside schedule → denied  
- … many Facts  

Also: `VehiclePolicyEvaluator`, `ParkingQuota`, `ParkingOccupancyStore`, agent/relay contract tests.

**Style:** Fixture() record + with-expressions — readable scenarios. **No DB.**

**Resume gold:** «unit-tested vehicle access decision matrix.»

---

## Qesmat 8 — RequestTracker unit

Command handler tests ba **EF InMemory** (`TestDbContextFactory.Create`):

```csharp
public class UpdateRequestTypeStepCommandHandlerTests : IDisposable
{
    private readonly ApplicationDbContext _dbContext = TestDbContextFactory.Create(...);
    // seed RequestType + Personnel
    [Fact]
    public async Task Handle_ReplacesAssigneesAndUpdatesScalars() { ... }
}
```

Also services: workflow, assignee selection, PersianDateFormatter, consumers details.

**Yani chi:** «unit» dar RT = handler + lightweight DB — na full Testcontainers (Day 57).

---

## Qesmat 9 — Visitors UnitTests (thin)

`VisitorTests` Facts **commented out**; `BaseTest` has Bogus `Faker` + `AssertDomainEventWasPublished`.

**Honesty:** architecture rules ghavi; domain unit examples prepared but not active. Expand = uncomment + fix API + Day 57 Bogus patterns.

---

## Qesmat 10 — FluentAssertions role

Everywhere: `result.Should().Be(...)`, `failingTypes.Should().BeEmpty()`.  
Readable failure messages for mosahebe demos.

---

## Qesmat 11 — chejori run

```bash
dotnet test Microservices/ACLServer/tests/ACLServer.UnitTests
dotnet test .../Dejban.Modules.Visitors.ArchitectureTests
dotnet test  # solution filter
```

CI (Day 58) typically `dotnet test` on test projects.

---

# BAKHSH-E SEVOM: WORLD extras xUnit

## Arrange-Act-Assert

ACL/RT tests follow AAA — name methods `Handle_...` / behavior sentence.

## Theory

Parameterized edge cases (many reason codes) — ACL mostly Fact-per-scenario (clearer failures).

## Isolation

No shared static mutable state; RT uses unique InMemory DB name per class (`Guid`).

## What not to unit-test

Full HTTP pipeline → Integration.  
UI → Playwright Day 55.

---

# BAKHSH-E CHAHAROM: jadval mosahebe

| Q | A |
|---|---|
| Test framework? | xUnit |
| Assert lib? | FluentAssertions |
| Arch lib? | NetArchTest.Rules |
| Strongest unit? | ACLServer evaluators, RT handlers |
| Strongest arch? | Visitors ArchitectureTests |
| Module isolation enforced? | **not really yet** |
| Visitors domain unit live? | mostly commented |
| Layers forbidden? | Domain↛App/Infra; App↛Infra/Pres; Pres↛Infra |

---

# BAKHSH-E PANJOM: farz kon / senario

## Se dastan

**1) Junior adds `using Infrastructure` in Domain**  
LayerTests red → PR blocked. NetArchTest payed off.

**2) Change vehicle blacklist rule**  
Update evaluator + Fact in ACLServer.UnitTests — fast feedback.

**3) Add new module HR**  
Extend ModuleTests `otherModules` — else false confidence.

---

## Smell-ha

1. ModuleTests empty otherModules  
2. Visitors unit Facts commented  
3. ShouldBeSuccessful helper — pattern used; ensure extension exists in solution  
4. Presentation↛Infra rule vs real IntegrationEventHandler dependency tension (Day 09)  
5. InMemory EF ≠ Postgres behavior (RT)  
6. No NetArchTest on ACLServer/RequestTracker (folder CA different)  
7. coverlet referenced — coverage not necessarily gated  

---

## Debug checklist

| symptom | check |
|---|---|
| Arch fail FailingTypes | which type broke rule |
| Unit green InMemory fail prod | SQL feature / constraint |
| Fact not discovered | IsTestProject + runner package |
| Internal handler test | InternalsVisibleTo |
| ModuleTests always green | empty arrays |

---

## 25 soal-e mosahebe

1. xUnit Fact vs Theory?  
2. FluentAssertions chera?  
3. NetArchTest chie?  
4. Domain nabayad depend on?  
5. Handler NotBePublic chera?  
6. DomainEvent naming?  
7. Entity private ctor chera?  
8. ACL unit mesal?  
9. RT InMemory?  
10. Visitors unit status?  
11. ModuleTests gap?  
12. IConsumer naming?  
13. Day 09 link?  
14. Day 57 next?  
15. coverlet?  
16. global Using Xunit?  
17. Directory.Packages?  
18. Architecture vs unit?  
19. How run?  
20. Clean Architecture enforce?  
21. sealed Command chera?  
22. Validator suffix?  
23. Integration vs unit RT?  
24. FE counterpart Day?  
25. One-liner Day 56?

---

## Senario-ha

**S1:** New `CreateFooCommand` public handler — ApplicationTests fail NotBePublic.  
**S2:** Entity public ctor — DomainTests fail.  
**S3:** Add parking quota edge — new Fact ACL.  
**S4:** Fill otherModules — ModuleTests becomes real.  
**S5:** Uncomment Visitor.Create test — domain unit live.

---

## Mini lab

1. Open `LayerTests.cs` — list 5 rules  
2. Open `ApplicationTests.cs` — count conventions  
3. Run mental ACL Authorized_vehicle Fact  
4. Read ModuleTests empty arrays  
5. Peek VisitorTests comments + Bogus BaseTest  
6. `dotnet test` one UnitTests project locally  

---

## Resume (1 paragraph)

> Backend tests use **xUnit** and **FluentAssertions**, with rich **unit** coverage on **ACLServer** decision evaluators and **RequestTracker** command handlers (EF InMemory). **NetArchTest** enforces **Visitors** Clean Architecture layering and CQRS naming/visibility conventions; solution-level module isolation tests exist but still need real cross-module dependency lists.

Keywords: `xUnit` · `FluentAssertions` · `NetArchTest` · `Types.InAssembly` · `LayerTests` · `[Fact]` · Clean Architecture

---

## File-haye mohem

| path | chera |
|---|---|
| `...Visitors.ArchitectureTests/Layers/LayerTests.cs` | dependency rules |
| `.../Application/ApplicationTests.cs` | CQRS conventions |
| `.../Domain/DomainTests.cs` | entity/event rules |
| `Dejban.ArchitectureTests/Layers/ModuleTests.cs` | module gap |
| `ACLServer.UnitTests/*Evaluator*` | behavior unit |
| `RequestTracker.UnitTests/Commands/*` | handler + InMemory |
| `Directory.Packages.props` | versions |
| Day 09 | architecture narrative |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 09 | CA + module smells |
| 10 | CQRS — arch naming |
| 11 | FluentValidation — Validator rules |
| 12 | Domain events — DomainTests |
| 55 | FE Playwright counterpart |
| **56** | this |
| 57 | Testcontainers + Bogus |
| 58 | CI runs dotnet test |

---

## Chejori digest koni

1. xUnit = runner  
2. FluentAssertions = assert style  
3. NetArchTest = structure guard Visitors  
4. ACL/RT = real unit meat  
5. Gaps honesty  

---

## Glossary

| term | ma'ni |
|---|---|
| Fact | single test |
| Theory | parameterized test |
| FluentAssertions | Should() API |
| NetArchTest | assembly rule tests |
| FailingTypes | types that broke rule |
| InMemory EF | lightweight DB for tests |
| Clean Architecture | dependency direction |
| sealed | no subclass |
| InternalsVisibleTo | test internal types |
| coverlet | coverage collector |

---

## Deep dive — NetArchTest fluent chain

`Types.InAssembly` → filter `That()` → `Should()` constraints → `GetResult()` → success assert.

Failed result lists offending types — fix code or relax rule consciously.

---

## Deep dive — why architecture tests are unit tests

No browser, no DB — milliseconds. Run on every PR. Cheapest architecture review.

---

## Deep dive — NotBePublic handlers

Still testable: same assembly tests OR InternalsVisibleTo UnitTests.  
Visitors unit currently thin — internals pattern ready when expanded.

---

## Anti-pattern

| bad | better |
|---|---|
| Only docs for CA | NetArchTest |
| Empty ModuleTests pride | fill namespaces |
| Comment all Facts | delete or fix |
| Test via HTTP for pure function | unit evaluator |
| Ignore FailingTypes message | read type list |

---

## Interview 60s

«We use xUnit with FluentAssertions. ACLServer and RequestTracker have solid unit tests for access decisions and command handlers. Visitors has NetArchTest suites that lock Clean Architecture dependencies and CQRS naming. Cross-module isolation tests are scaffolded but still need real module lists.»

---

## Quick self-test

1. Runner? → xUnit  
2. Arch lib? → NetArchTest  
3. Layer Domain↛? → Application & Infrastructure  
4. Strong unit apps? → ACL + RT  
5. ModuleTests strong? → no  
6. Visitors domain Facts? → commented  
7. Assert style? → FluentAssertions  

---

## Final checklist

- [ ] xUnit basics  
- [ ] FluentAssertions  
- [ ] NetArchTest layers  
- [ ] CQRS conventions  
- [ ] ACL/RT unit  
- [ ] gaps  
- [ ] resume  

---

## Extra — Farz kon police-e sakhteman

NetArchTest = shahrdari.  
LayerTests = «in tabaghe nabayad be an tabaghe nardeban bezane».  
ApplicationTests = «in dar bayad in etiket ro dashte bashe».  
Unit ACL = «in ghanun-e vorud khodro dorost kar mikone».  
ModuleTests empty = police bedune list — hame green.

---

## Extra — AAA example RT

Arrange: seed step + assignees.  
Act: `Handle(UpdateRequestTypeStepCommand)`.  
Assert: scalars + assignees replaced (`Should()`).

---

## Extra — record with-expressions ACL

`Fixture() with { Vehicle = null }` — immutable scenario variants. Modern C# test style.

---

## Extra — IDisposable test class

RT disposes DbContext — no connection leak in long runs.

---

## Extra — naming Fact methods

`Authorized_vehicle_is_allowed` — behavior English; good for report readability.

---

## Extra — Bogus peek (Day 57)

Visitors BaseTest `Faker` ready — fake names/codes. Full story next day.

---

## Extra — IntegrationTests mention

`Dejban.IntegrationTests` / Visitors Integration — some Facts commented; Testcontainers Day 57.

---

## Band-e gharardad-e jadid

xUnit = motor test.  
Fact = yek case.  
FluentAssertions = zaban assert.  
NetArchTest = gheide sakhteman.  
LayerTests = nardeban mamnu.  
ApplicationTests = naming police.  
ACL unit = maghz decision.  
RT unit = handler + InMemory.  
Gap = ModuleTests empty + Visitors Facts sleep.

---

## 10 jomle fluency

1. Backend tests run on xUnit.  
2. Assertions use FluentAssertions.  
3. NetArchTest guards Visitors layers.  
4. Domain must not reference Application.  
5. Handlers should be sealed and internal.  
6. ACLServer unit-tests vehicle access decisions.  
7. RequestTracker tests handlers with EF InMemory.  
8. Module isolation test is still a stub.  
9. Visitors domain unit tests are mostly commented.  
10. Architecture tests are the cheapest CA review.

---

## Extra — version centralization

Central Package Management — bump xunit once in Directory.Packages.props.

---

## Extra — IsTestProject

csproj flag helps SDK / tooling recognize test assemblies.

---

## Extra — ProjectReference shape

ArchitectureTests → Infrastructure (pulls module graph).  
UnitTests → main csproj / Application as needed.

---

## Extra — MassTransit consumer rule

PresentationTests couples messaging shape to naming — rename carefully.

---

## Extra — when arch test fails in CI

1. Read FailingTypes  
2. Wrong reference? move code to correct layer  
3. Or update rule if architecture decision changed (ADR)

---

## Extra — compare ArchUnitNET

Similar idea; team chose NetArchTest — know name for interview.

---

## Extra — mutation testing WORLD

Stryker.NET — optional advanced; not in repo claim.

---

## Extra — 10 soalat sari

1. Framework? xUnit  
2. Arch? NetArchTest  
3. Assert? FluentAssertions  
4. Domain↛App? yes  
5. ACL unit? yes  
6. ModuleTests filled? no  
7. Visitors Facts live? no  
8. RT DB? InMemory  
9. Handler public? should not  
10. Next day? Testcontainers  

---

## Extra — Diagram 30s

Begu: «xUnit runs two kinds of tests: behavior units for ACL and RequestTracker, and NetArchTest structure rules for Visitors. Layers cannot point inward the wrong way. Module isolation is the remaining gap.»

---

## Extra — Common bugs

| symptom | likely |
|---|---|
| Arch red after move | wrong project reference |
| Internal inaccessible | InternalsVisibleTo |
| InMemory false green | provider differences |
| No tests discovered | missing runner package |
| Always green ModuleTests | empty deps list |

---

## Extra — Layer checklist backend test

| concern | tool |
|---|---|
| Pure logic | xUnit unit |
| Handler+EF light | xUnit + InMemory |
| CA dependencies | NetArchTest |
| Naming/visibility | NetArchTest |
| Real Postgres/bus | Integration Day 57 |
| HTTP UI | Playwright Day 55 |

---

## Extra — Farz kon fill ModuleTests

```csharp
string[] otherModules = [
  "Dejban.Modules.Users", // example when exists
];
```

Then Visitors assemblies must not reference those — real modular monolith guard.

---

## Extra — CQRS link Day 10

ICommand/IQuery interfaces used in ApplicationTests filters — arch tests document CQRS shapes.

---

## Extra — Domain event link Day 12

IDomainEvent / DomainEvent base — DomainTests sealed + suffix.

---

## Extra — Validator link Day 11

AbstractValidator<> — sealed, internal, `*Validator` name.

---

## Extra — coverlet

Package on ArchitectureTests — `dotnet test --collect:"XPlat Code Coverage"` possible; gating policy = team/CI.

---

## Extra — Final fluency drill

«We enforce Visitors Clean Architecture with NetArchTest and write xUnit behavior tests for ACL access decisions and RequestTracker handlers. FluentAssertions keeps asserts readable. Cross-module NetArch rules are still incomplete.»

---


## Extra — Capacity / speed

Arch + ACL unit = seconds.  
Prefer before Integration/Playwright in local loop.

---

## Extra — Test project naming

`*.UnitTests` / `*.ArchitectureTests` / `*.IntegrationTests` — discoverability in solution folder.

---

## Extra — Why Visitors got ArchitectureTests first

Modular monolith template (Milan-style) land kard roye Visitors; digar module-ha hanooz copy-paste nashode — expand opportunity.

---

## Extra — RequestTracker vs Dejban module style

RT: classic Application/Infrastructure in one service — unit hits handlers directly.  
Dejban Visitors: stricter layer assemblies — NetArchTest fits better.

---

## Extra — AgentDeviceContractTests

ACL also tests DTO/contract shapes for agent devices — serialization/compat unit style beside evaluators.

---

## Extra — Persian messages in asserts

ACL asserts Persian `Reason` strings — FE/agent UX contract; change copy = update test.

---

## Extra — parallel dotnet test

`dotnet test -m:1` if shared resources; default parallel per assembly usually OK for these units.

---

## Extra — solution filter tip

Open only `*Tests*.csproj` in IDE for focus.

---
## Khoruj-e zehni

> Midunam backend ba xUnit+FluentAssertions test mishe; NetArchTest layer/CQRS Visitors ro lock mikone; ACL/RT unit ghavi-an; ModuleTests va Visitors domain Facts hanuz gap daran; Integration miravad Day 57.

Age in paragraph mal-e to shod — Day 56 done.

---

*Day 56 tamum. Ba'd: Day 57 — Testcontainers + Bogus (amade). Fehrest: [README.md](./README.md).*