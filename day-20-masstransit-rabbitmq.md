# Day 20 — MassTransit + RabbitMQ

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**MassTransit** abstraction-e messaging toye .NET-e: tu type-haye C#, consumer, retry, outbox, va request/response fekr mikoni, va khodesh ba broker (inja **RabbitMQ**) harf mizane. Dejban ba ina **integration event** publish mikone — yani chizi ke beyn-e service-ha / module-ha bayad sync beshe, na faghat domain event-e dakheli.

Masir-e kolli injuri-e: domain event → outbox → `IEventBus.PublishAsync` → RabbitMQ → consumer-ha. Do style consumer darim: (1) module-haye Dejban.Api = inbox table + Quartz, (2) ACL / Identity / RequestTracker = `IConsumer` + MassTransit EF Outbox. Plus request/response ba `GetResponse`. Retry va circuit breaker built-in hastan.

---

# BAKHSH-E AVAL: WORLD — Messaging to donya

## Chera message bus?

| sync HTTP | async messaging |
|---|---|
| caller wait mikone | fire-and-forget / eventually consistent |
| tight coupling | loose coupling |
| hardo taraf bayad up bashan | producer mitone edame bede age consumer down bashe (age durable) |
| request/response tabi'i-e | pub/sub tabi'i-e |

**Vaghti messaging be dard mikhore:** side-effect-haye cross-service, fan-out (chand consumer yek event), load leveling, va reliability vaghti nemikhay request HTTP ro be hame dependency-ha vasl koni.

Yani chi? Age CreatePersonnel anjam shod, Visitors, Vehicles, ACL, va Identity bayad khabar dar she — agar hame ro sync HTTP seda koni, latency o failure-ha ziad mishe. Bus = ye event midam, har ki gush mikone.

---

## RabbitMQ concepts

| concept | chi |
|---|---|
| **Exchange** | router — publish miad inja, ba rule be queue miravad |
| **Queue** | buffer-e message-ha |
| **Binding** | ghaede-ye exchange → queue (routing key) |
| **Routing key** | label baraye routing |
| **Ack / Nack** | consumer confirm / reject mikone |
| **Durable** | ba restart-e broker mire |
| **Prefetch** | chand message unacked dar ye consumer |

Exchange type-ha: direct, topic, fanout, headers.

```
Publisher → Exchange → (bindings) → Queue(s) → Consumer(s)
```

To practice, MassTransit bishtar-e in topology ro barat misaze — to type publish mikoni, endpoint name formatter queue name midahad.

---

## MassTransit chie?

Library-i ke:

- Type-haye C# ro be exchange/queue map mikone
- Message ro serialize mikone (ma'mulan JSON)
- Retry, circuit breaker, outbox midahad
- Consumer ha ro be shekl-e `IConsumer<T>` minevisi
- Request/response, saga, scheduling dare

```csharp
services.AddMassTransit(x =>
{
    x.AddConsumer<OrderCreatedConsumer>();
    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.Host("localhost", "/", h => { h.Username("guest"); h.Password("guest"); });
        cfg.ConfigureEndpoints(context);
    });
});

// publish
await bus.Publish(new OrderCreated(orderId));
```

**Endpoint name formatter:** kebab-case — yani `OrderCreated` → queue `order-created`.

Chera abstraction? Ta Application layer mostaghim be Rabbit API vasl nashe; test o swap-e transport asoon-tar bashe; va pattern-haye enterprise (outbox, retry) yekja bemunan.

---

## Publish vs Send

| | Publish | Send |
|---|---|---|
| pattern | pub/sub | point-to-point |
| topology | exchange → chand queue | endpoint-e khas |
| use | event («chizi etefagh oftad») | command («in kar ro bokon») |

Dejban baraye integration event-ha **Publish** estefade mikone — chand service bayad copy begiran. Send bishtar vase command-haye mokhatab-e yek endpoint-e.

---

## Consumer patterns

```csharp
public class OrderCreatedConsumer : IConsumer<OrderCreated>
{
    public async Task Consume(ConsumeContext<OrderCreated> context)
    {
        await DoWork(context.Message);
    }
}
```

**Competing consumers:** chand instance roye **hamun** queue → load balance. Yani scale-out-e worker.

**InstanceId:** queue joda baraye har service (`order-created-aclserver`) → **har** service ye copy migire (fan-out). In to Dejban kheili moheme — ACL va Identity hardo bayad `PersonnelCreated` ro bebinan, na inke yeki az do ta.

---

## Delivery guarantees

| guarantee | meaning |
|---|---|
| At-most-once | momken-e lose she |
| At-least-once | momken-e duplicate she ← **ma'mul** |
| Exactly-once | sakht; ba inbox + idempotency approx mishi |

**Idempotent consumer** baraye at-least-once lazeme. Broker guarantee nemide «faghat yek bar side-effect»; to bayad safe bash i age dobare Consume seda zade shod.

---

## Retry + Circuit breaker

```csharp
cfg.UseMessageRetry(r => r.Exponential(
    retryLimit: 5,
    minInterval: TimeSpan.FromSeconds(1),
    maxInterval: TimeSpan.FromMinutes(5),
    intervalDelta: TimeSpan.FromSeconds(2)));

cfg.UseCircuitBreaker(cb =>
{
    cb.TrackingPeriod = TimeSpan.FromMinutes(1);
    cb.TripThreshold = 15;
    cb.ActiveThreshold = 10;
    cb.ResetInterval = TimeSpan.FromMinutes(5);
});
```

Flow: fail → retry → hanuz fail → error queue / skip. Age fail-haye ziad ba ham bioftan → circuit open → consume pause mishe ta dependency nafas bekeshad.

Yani chi? Transient DB blip = retry. Dependency-e murde = circuit ta storm nasazi.

---

## Transactional Outbox (MassTransit EF)

```csharp
x.AddEntityFrameworkOutbox<AppDbContext>(o =>
{
    o.UsePostgres();
    o.UseBusOutbox();
});
// endpoint:
cfg.UseEntityFrameworkOutbox<AppDbContext>(context);
```

Publish ba `SaveChanges` to **hamun** DB transaction miravad — dual-write problem (DB OK + broker fail) kam mishe. Day 22 in ro deep mikone.

**Alternative:** custom outbox table + background job (module-haye Dejban — Day 14/21).

---

## Request / Response

```csharp
// client
var response = await client.GetResponse<StockLevelResponse>(
    new CheckStock(productId), ct);

// consumer
public async Task Consume(ConsumeContext<CheckStock> context)
{
    await context.RespondAsync(new StockLevelResponse { Qty = 10 });
}
```

Sync-style RPC roye bus — timeout momkene. Kam estefade kon: coupling + latency. Ja-yi ke query cross-service lazem-e va HTTP internal nadari, Dejban in olgu ro dare.

---

## RabbitMQ vs Kafka (kholase)

| | RabbitMQ | Kafka |
|---|---|---|
| model | smart broker / queues | log / partitions |
| replay | sakht | asoon (offset) |
| use | task dispatch, RPC, classic events | analytics, CDC, high throughput stream |

Dejban = **RabbitMQ**. Kafka inja transport-e asli nist.

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **Sagas / state machines** — MassTransit Automatonymous (Dejban choreography mikone, na orchestration-e rasmi)
- **Message scheduling** — delayed publish
- **Kafka / Azure Service Bus** transports
- **MassTransit.Redis** as bus — package version shode, vali bus wired nist
- **Courier routing slips** — multi-step activities
- **Dead letter management UI** beyond RabbitMQ management

In lists yani «nadari» = smell / future option, na bug.

---

# BAKHSH-E DOVOM: DEJBAN — MassTransit + RabbitMQ

## Versions

```xml
MassTransit                      8.5.7
MassTransit.RabbitMQ             8.5.7
MassTransit.EntityFrameworkCore  8.5.7
MassTransit.Redis                8.5.7  <!-- versioned, bus NOT using it -->
```

Yadet bashe version-ha ba `Directory.Packages.props` sync bemunan across service-ha — schema-e serialization o outbox table ba upgrade avaz mishe.

---

## Infrastructure

```yaml
# docker-compose.yml
eventbus:
  image: rabbitmq:management
  volumes:
    - ./Common/EventBus/eventbus_init/definitions.json:/etc/rabbitmq/definitions.json
```

`definitions.json`:

- Queue-haye **kebab-case** ro pre-declare mikone
- Exchange/binding-ha khali — MassTransit dar runtime misaze
- Mesal: `personnel-created`, `personnel-created-aclserver`, `get-user-site-claims`

Config bind: `RabbitMqTransport` / `RabbitMqTransportOptions`.

**Drift risk:** age MassTransit queue name avaz she vali definitions ghadimi bemune, startup warning / missing bind.

---

## IEventBus abstraction

```csharp
// Dejban.Common.Application/EventBus/IEventBus.cs
public interface IEventBus
{
    Task PublishAsync<T>(T integrationEvent, CancellationToken ct = default)
        where T : IIntegrationEvent;
    Task PublishBatchAsync<T>(...);
}

// Implementation
internal sealed class EventBus(IBus bus) : IEventBus
{
    public Task PublishAsync<T>(T e, CancellationToken ct)
        where T : IIntegrationEvent
        => bus.Publish(e, ct);
}
```

Application be `IEventBus` depend mikone, **na** type-haye MassTransit — Clean Architecture. Test double asoon; Infrastructure detail to Common.Infrastructure mimune.

---

## Contracts

```csharp
// Common/EventBus/Contracts/Events/PersonnelCreated.cs
public sealed class PersonnelCreated : IntegrationEvent
{
    public Guid PersonnelId { get; init; }
    public long ACLUserId { get; init; }
    public string FirstName { get; init; }
    public Guid SiteId { get; init; }
    // ... full projection for ACL / RT / other modules
}
```

```csharp
public sealed class SiteCreated : IntegrationEvent { /* SiteId, Name, ... */ }
```

Folder: `Common/EventBus/Contracts/Events/` + `Requests/`.

**Fat event:** projection kamel — consumer ACL user misaze bedune DB call digar; versioning sakht — field hazf = break. Dejban baraye speed-e ACL/RT **fat** entekhab karde.

---

## Publish path (Dejban)

```
Personnel.Create → Raise(PersonnelCreatedDomainEvent)
  → EF SaveChanges → custom outbox insert (Day 14/21)
  → ProcessOutboxJob → PersonnelCreatedDomainEventHandler
       → GetPersonnelQuery
       → eventBus.PublishAsync(new PersonnelCreated(...))
            → IBus.Publish → RabbitMQ
```

```csharp
// PersonnelCreatedDomainEventHandler.cs
await eventBus.PublishAsync(
    new PersonnelCreated(domainEvent.Id, domainEvent.OccurredOnUtc, /* mapped fields */),
    cancellationToken);
```

Yani HTTP response ghabl az fan-out-e kamel barmigarde — eventual consistency. Reliability roye **outbox** hast, na mid-request Publish.

---

## Two consumer styles

### A) Dejban modules — inbox bridge

```csharp
// IntegrationEventConsumer<T> : IConsumer<T>
public async Task Consume(ConsumeContext<T> context)
{
    // Dapper INSERT {schema}.inbox_messages ON CONFLICT DO NOTHING
}
```

Registered per module:

```csharp
configure.AddConsumer<IntegrationEventConsumer<SiteCreated>>();
configure.AddConsumer<IntegrationEventConsumer<PersonnelCreated>>();
// ...
```

Ba'd: Quartz `ProcessInboxJob` → `IntegrationEventHandler<T>` (read-model upsert). Day 23 deep.

**Queue names:** plain kebab (`personnel-created`) — module-ha compete; idempotent by event id. Chera compete OK-e? Chun har module schema-e khodesh inbox dare va ON CONFLICT / handler dedup dare — vali mental model confusing-e (smell).

### B) ACLServer / RequestTracker / Identity — real consumers

```csharp
// ACLServer PersonnelCreatedConsumer
public async Task Consume(ConsumeContext<PersonnelCreated> context)
{
    // create ACLUser, SaveChanges (EF outbox on endpoint)
}
```

```csharp
x.AddConsumer<PersonnelCreatedConsumer>()
    .Endpoint(e => e.InstanceId = "ACLServer");
// → queue personnel-created-aclserver (own copy of every event)
```

Hamin pattern baraye RequestTracker (`InstanceId = "RequestTracker"`) va IdentityServer.

**Chera InstanceId?** Har service bayad **hame** event-ha ra bebine (fan-out). Bedune InstanceId, competing consumers → yek service faghat message migire.

---

## AddMassTransit — ACLServer (template)

```csharp
services.AddMassTransit(x =>
{
    x.DisableUsageTelemetry();
    x.AddEntityFrameworkOutbox<ApplicationDbContext>(o =>
    {
        o.UsePostgres();
        o.UseBusOutbox();
    });
    x.SetKebabCaseEndpointNameFormatter();

    x.AddConsumer<PersonnelCreatedConsumer>()
        .Endpoint(e => e.InstanceId = "ACLServer");
    // 20+ consumers...

    x.AddRabbitMqConfigureEndpointsCallback((context, name, cfg) =>
    {
        if (name.EndsWith("get-aclservice-endpoints", ...)) return;
        cfg.UseEntityFrameworkOutbox<ApplicationDbContext>(context);
    });

    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.UseTenantContextFilters(context);
        cfg.UseMessageRetry(r => r.Exponential(
            5, TimeSpan.FromSeconds(1),
            TimeSpan.FromMinutes(5), TimeSpan.FromSeconds(2)));
        cfg.UseCircuitBreaker(cb =>
        {
            cb.TrackingPeriod = TimeSpan.FromMinutes(1);
            cb.TripThreshold = 15;
            cb.ActiveThreshold = 10;
            cb.ResetInterval = TimeSpan.FromMinutes(5);
        });
        cfg.ConfigureEndpoints(context);
    });
});
```

DbContext: `AddInboxStateEntity` / `AddOutboxMessageEntity` / `AddOutboxStateEntity`.

### Dejban InfrastructureConfiguration

- Hamin retry + CB + tenant filters + `ConfigureEndpoints`
- Module-ha `ConfigureConsumers` / `ConfigureReceiveEndpoints` inject mikonan
- **No** MassTransit EF Outbox — custom Quartz outbox/inbox

### Services using MassTransit EF Outbox

ACLServer, IdentityServer, RequestTracker, DCC, GateServer, Reporting.

---

## Tenant context on bus

```csharp
// Common/Tenancy/TenantContextMassTransitExtensions.cs
cfg.UseTenantContextFilters(context);
```

Publish/consume filter-ha `site_ids` / super-admin ro carry mikonan — inbox worker-ha `TenantContextAccessor` ro restore mikonan. Bedune in, read-model sync ba tenant khali eshtebah filter mishe (Day 16).

---

## Request / Response examples

### HasApprovedRequestStep (Visitors ↔ RequestTracker)

```csharp
// Client (Visitors)
var response = await client.GetResponse<HasApprovedRequestStepResponse>(
    new HasApprovedRequestStep(sourceId), cancellationToken);

// Consumer (RequestTracker)
public async Task Consume(ConsumeContext<HasApprovedRequestStep> context)
{
    var has = await dbContext.Requests.AnyAsync(/* approved step */);
    await context.RespondAsync(new HasApprovedRequestStepResponse
    {
        HasApprovedStep = has
    });
}
```

Registration: `AddRequestClient<HasApprovedRequestStep>()` in VisitorsModule.  
Outbox often **skipped** on RPC endpoints (callback `get-*` names ro exclude mikone) — latency kamtar.

### Other RPC

- `GetUserSiteClaims` (Identity) — claims enrichment (Day 25 cache mikone)
- `IsContractorRegistrationNumberUnique` (Dejban ↔ Identity)
- ACL service endpoints discovery

**Tradeoff:** Visitors **depends** RequestTracker up — fallback? Hang = UX block. Interview: sometimes HTTP + Polly clearer.

---

## End-to-end flow

```
[Personnels module]
  CreatePersonnel → domain event → custom outbox → Publish PersonnelCreated
                         │
                         ▼ RabbitMQ exchange/queues
         ┌───────────────┼────────────────┬──────────────────┐
         ▼               ▼                ▼                  ▼
  Dejban Visitors   Dejban Vehicles   ACLServer          RequestTracker
  IntegrationEvent  IntegrationEvent  PersonnelCreated   PersonnelCreated
  Consumer→inbox    Consumer→inbox    Consumer (ACLUser) Consumer (copy)
         ▼               ▼
  Quartz inbox     Quartz inbox
  upsert Site/     upsert ...
  Personnel copy
```

In diagram ra **hafz kon** — mosahebe + debug. Yek contract, do consume style.

---

## Compare outbox strategies

| | Dejban modules | ACL / Identity / RT |
|---|---|---|
| Write | EF interceptor → `outbox_messages` | MassTransit EF Outbox |
| Process | Quartz + Dapper | MassTransit bus outbox |
| Inbox | custom `inbox_messages` | MassTransit InboxState |
| Consumer | bridge → handler | direct `IConsumer` |

Har do transactional — implementation fargh. Goal yeksan: dual-write nabashe.

---

## Smell-ha

1. **Dejban ConfigureReceiveEndpoints empty stubs** — dead API surface; extension point hast vali alan empty
2. **Competing consumers across Dejban modules** on same queue name — ba idempotent inbox kar mikone, vali confusing
3. **definitions.json queues vs MassTransit auto topology** — drift risk
4. **MassTransit.Redis unused** for bus
5. **No saga** — multi-step workflows = choreography only
6. **RPC over bus** — timeout/coupling; sometimes HTTP clearer
7. **Circuit breaker + retry numbers undocumented** — tribal knowledge
8. **Large PersonnelCreated payload** — fat events; schema change breaks all consumers
9. **Json serialization settings** must stay compatible across services
10. **No formal contract tests** (Pact) for events
11. **Error queue / poison** handling not customized in snippets
12. **Duplicate consumer code** across services for same event shape

Har smell ye tradeoff dare — interview age «chera inja?» porsidan, in list komak mikone.

---

## 20 soal-e mosahebe

1. **MassTransit chie?** — .NET messaging framework over brokers
2. **RabbitMQ exchange vs queue?** — route vs store
3. **Publish vs Send?** — pub/sub vs point-to-point
4. **At-least-once?** — may duplicate → need idempotency
5. **Outbox chera?** — atomic business + message intent
6. **InstanceId chera?** — dedicated queue per service (fan-out)
7. **Competing consumers?** — scale workers on same queue
8. **IConsumer vs inbox bridge?** — process now vs persist then process
9. **Message retry?** — transient failure recovery
10. **Circuit breaker?** — stop hammering failing dependency
11. **Request/response on bus?** — RPC with timeout
12. **KebabCaseEndpointNameFormatter?** — `PersonnelCreated` → `personnel-created`
13. **Integration vs domain event?** — cross-boundary vs internal
14. **IEventBus abstraction?** — keep Application free of MassTransit
15. **EF Outbox vs custom?** — MassTransit built-in vs Quartz+Dapper
16. **Tenant filters on bus?** — multi-tenancy across async boundary
17. **Kafka vs Rabbit?** — log/stream vs classic messaging
18. **Saga?** — orchestrated long-running process — Dejban hasn't
19. **Poison message?** — repeated fail → error queue / manual
20. **Fat event smell?** — large payloads couple producers/consumers

---

## Deep dive — `ConfigureConsumers` per module (Dejban)

Har module yek static delegate be `InfrastructureConfiguration` midahad:

```csharp
// VisitorsModule.cs (pattern repeated × 8)
public static Action<IRegistrationConfigurator> ConfigureConsumers =>
    configure =>
    {
        configure.AddRequestClient<HasApprovedRequestStep>();

        configure.AddConsumer<IntegrationEventConsumer<SiteCreated>>();
        configure.AddConsumer<IntegrationEventConsumer<PersonnelCreated>>();
        // ... Site, Unit, Contractor, Door, Request*, AccessLog, ...
    };
```

**InfrastructureConfiguration:**

```csharp
foreach (Action<IRegistrationConfigurator> configureConsumers in moduleConfigureConsumers)
    configureConsumers(configure);

configure.SetKebabCaseEndpointNameFormatter();
configure.UsingRabbitMq((context, cfg) =>
{
    cfg.UseTenantContextFilters(context);
    cfg.UseMessageRetry(...);
    cfg.UseCircuitBreaker(...);
    foreach (var moduleReceive in moduleConfigureReceiveEndpoints)
        moduleReceive(cfg, context);
    cfg.ConfigureEndpoints(context);
});
```

| piece | role |
|---|---|
| `ConfigureConsumers` | **register** consumer types + request clients |
| `ConfigureReceiveEndpoints` | optional manual receive endpoint tweak (often **empty stub**) |
| `ConfigureEndpoints` | MassTransit auto-bind consumer → queue name |

**Smell:** `// configure.AddConsumers(Assembly)` commented — har event **dasti** `AddConsumer<IntegrationEventConsumer<T>>` → compile-time list, vali boilerplate ziad. Maziat: intentional surface; gheymat: har event jadid = edit-e module.

---

## Deep dive — Tenant filters roye bus

```csharp
// TenantContextMassTransitExtensions.cs
cfg.UseConsumeFilter(typeof(TenantContextConsumeFilter<>), context);
cfg.UsePublishFilter(typeof(TenantContextPublishFilter<>), context);
cfg.UseSendFilter(typeof(TenantContextSendFilter<>), context);
```

**Publish:** vaghti domain handler `eventBus.PublishAsync(PersonnelCreated)` — filter site context ra to message headers/metadata carry mikone.

**Consume:** `IntegrationEventConsumer` `TenantContextAccessor.Current` → snapshot to inbox `site_ids`.

**Send (RPC):** request client ham bayad tenant dashte bashe ta downstream query dorost filter she.

Bedune in: integration handler to Visitors module ba tenant khali — read-model sync eshtebah. Day 16 tenancy + Day 20 bus = yek dastan.

---

## Deep dive — Endpoint naming + queues

| C# type | default queue (KebabCase) |
|---|---|
| `PersonnelCreated` consumer | `personnel-created` |
| `PersonnelCreatedConsumer` + `InstanceId = "ACLServer"` | `personnel-created-aclserver` |

MassTransit RabbitMQ:

- publish → **exchange** (type name based)
- consumer endpoint → **queue** bind shode

`definitions.json` queues **pre-declare** — MassTransit runtime ham topology misaze. **Drift:** queue name avaz shod, definitions ghadimi → startup warning / missing bind.

Lab tip: management UI `:15672` — depth-e `personnel-created` vs `personnel-created-aclserver` ro moghayese kon.

---

## Deep dive — Retry vs circuit breaker (interaction)

```
Message fail (transient DB)
  → Retry 1..5 exponential (1s → … → 5min cap)
  → Still fail → move toward error/dead-letter (MT default behavior)
Many messages fail together
  → Circuit opens (15 failures / 1 min tracking)
  → Pause consume 5 min (ResetInterval)
  → Half-open retry
```

**Na haman outbox job retry:** Dejban module inbox/outbox **Quartz** retry nadare (Day 19). MassTransit retry **faghat roye IConsumer.Consume** — baraye `IntegrationEventConsumer` insert inbox, insert fail → retry; insert success → OK.

**ACL consumer** ba EF outbox: consume + SaveChanges + bus outbox flush — retry mitone duplicate side-effect bede age consumer idempotent nist. Logical check (`existingUser != null`) + InboxState = safety net.

---

## Deep dive — Request/response registration

```csharp
// Visitors module
configure.AddRequestClient<HasApprovedRequestStep>();

// Handler (conceptual)
IRequestClient<HasApprovedRequestStep> client;
var response = await client.GetResponse<HasApprovedRequestStepResponse>(
    new HasApprovedRequestStep(sourceId), ct);
```

| topic | note |
|---|---|
| Timeout | default MT timeout — RPC hang = UX block |
| Outbox skip | ACL callback `get-*` endpoints bedune EF outbox — latency kamtar |
| Coupling | Visitors **depends** RequestTracker up — fallback? |

**Alternative WORLD:** HTTP internal API + Polly — Dejban bus-first baraye cross-microservice.

---

## Deep dive — PublishBatch

```csharp
Task PublishBatchAsync<T>(IEnumerable<T> events, CancellationToken ct);
```

Agar handler chand integration event yekja — kamtar round-trip. Hanooz **har event** masir Rabbit joda (na transaction across messages). Atomicity faghat dar outbox-e producer-e.

---

## Event catalog (sample contracts)

| Event | producer (typical) | consumers (typical) |
|---|---|---|
| `PersonnelCreated` | Personnels outbox handler | Visitors/Vehicles inbox, ACL, RT |
| `SiteCreated` | Sites module / Identity | read-models across modules |
| `RequestStepApproved` | RequestTracker | Visitors reservation lock |
| `AccessLogCreated` | ACL / devices | reporting paths |

**Fat event:** `PersonnelCreated` projection kamel — consumer ACL user misaze bedune DB call digar; **versioning** sakht — field hazf = break.

**Thin event:** faghat `PersonnelId` — consumer query bezane — coupling kamtar, traffic bishtar.

Dejban = **fat** baraye ACL/RT speed. Interview: tradeoff ro boland bego.

---

## Custom outbox vs MassTransit EF Outbox — timeline

```
[Dejban module]
  T0: SaveChanges + outbox row (EF)
  T1: Quartz poll (Dapper FOR UPDATE)
  T2: Domain handler → Publish
  T3: IntegrationEventConsumer → inbox INSERT
  T4: Quartz inbox → upsert read model

[ACLServer]
  T0: Consumer message OR local command SaveChanges
  T1: EF OutboxMessage + BusOutbox flush
  T2: Rabbit publish atomic with DB (same pattern intent)
```

Har do **at-least-once** — idempotency layer joda (Day 21–23).

---

## Monitoring / ops (WORLD checklist)

- RabbitMQ management: queue depth, unacked, publish rate
- Error queue (`*_error`) — poison inspect
- Consumer lag: inbox `processed_on_utc IS NULL` count per schema
- Circuit breaker open logs — spike correlation

Dejban: centralized dashboard **limited** — SQL + Rabbit UI manual. Lab: in checklist ro roye kaghaz dashte bash.

---

## Chejori in fasl ra «digested» koni (lab — ~50 min)

1. Docker `eventbus` up — management UI `:15672` (5 min)
2. Create personnel → trace log «Publish» / queue `personnel-created` depth (10 min)
3. Compare queue `personnel-created` vs `personnel-created-aclserver` (InstanceId) (10 min)
4. Kill RequestTracker → `GetResponse` timeout behavior (optional, 10 min)
5. Read `VisitorsModule.ConfigureConsumers` — count consumer types (5 min)
6. Draw fan-out diagram roye kaghaz (5 min)
7. 20 soal + bonus zir (5 min)

---

## 5 soal-e ezafe (bonus)

21. **`DisableUsageTelemetry` chi?** — MassTransit telemetry off (privacy/ops choice)
22. **Chera `IEventBus` na `IBus` to Application?** — test double + Clean Architecture
23. **IntegrationEventConsumer exception = ?** — MT retry; inbox row maybe never inserted if always fail
24. **`ConfigureReceiveEndpoints` empty — chera register?** — extension point baraye manual bind; alan unused
25. **Redis package versioned vali bus na — risk?** — dead dependency / future option

---

## Resume

**short:**

> Integrated services with MassTransit 8.5 / RabbitMQ: publish integration events via `IEventBus`, consume with InstanceId fan-out and inbox bridges, MassTransit EF outbox on standalone services, exponential retry + circuit breaker, and request/response for cross-service queries.

**bullets:**

- Published domain outcomes as integration contracts (`PersonnelCreated`, `SiteCreated`) through `IBus.Publish`
- Implemented dual consume paths: Dejban `IntegrationEventConsumer` → inbox/Quartz vs ACL/RT/Identity `IConsumer` with `InstanceId` queues
- Configured MassTransit EF Outbox (`UsePostgres` + `UseBusOutbox`) on Identity, ACL, RequestTracker, DCC, Gate, Reporting
- Added resilience (`UseMessageRetry` exponential, `UseCircuitBreaker`) and tenant propagation filters on the bus
- Used `IRequestClient.GetResponse` for approval checks and uniqueness RPCs across services

**skills:** `MassTransit, RabbitMQ, Event-Driven Architecture, Integration Events, Transactional Outbox, Message Retry, Circuit Breaker, Request/Response Messaging, Pub/Sub`

---

## File-haye mohem

| chi | koja |
|---|---|
| Packages | `Directory.Packages.props` |
| Docker eventbus | `docker-compose.yml` |
| Queue definitions | `Common/EventBus/eventbus_init/definitions.json` |
| IEventBus | `Dejban.Common.Application/EventBus/IEventBus.cs` |
| EventBus impl | `Dejban.Common.Infrastructure/EventBus/EventBus.cs` |
| Dejban MT setup | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| ACL MassTransit | `ACLServer/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Identity MT | `IdentityServer/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| RequestTracker MT | `RequestTracker/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Contracts | `Common/EventBus/Contracts/Events/` |
| Domain→Publish | `Personnels.Application/.../PersonnelCreatedDomainEventHandler.cs` |
| Inbox consumer | `*/Infrastructure/Inbox/IntegrationEventConsumer.cs` |
| ACL consumer | `ACLServer/Application/Consumers/PersonnelCreatedConsumer.cs` |
| RPC consumer | `RequestTracker/.../HasApprovedRequestStepConsumer.cs` |
| RPC client | `Visitors.Application/.../VisitReservationApprovalLock.cs` |
| Tenant bus filters | `Common/Tenancy/TenantContextMassTransitExtensions.cs` |

---

## Interview 60s

> «We publish integration events over MassTransit and RabbitMQ. Modular Dejban modules write to an inbox then process with Quartz; Identity and ACL use real IConsumers with InstanceId queues so every service gets a copy. Retry and circuit breaker sit on the bus; IEventBus keeps Application free of MassTransit types.»

---

## Glossary

| kalame | ma'ni |
|---|---|
| Integration event | cross-boundary «happened» message |
| Domain event | internal aggregate notification |
| Fan-out | har service ye copy |
| Competing consumers | chand worker yek queue |
| InstanceId | suffix baraye queue-e service |
| At-least-once | momken tekrari |
| Outbox | publish intent to DB |
| Inbox | inbound durable buffer |
| Poison | payam-e fail-daemi |
| Fat event | payload-e por projection |

---

*Day 20 tamum. Ba'd: Day 21 — Transactional Outbox (custom Dejban) (amade). Fehrest: [README.md](./README.md).*
