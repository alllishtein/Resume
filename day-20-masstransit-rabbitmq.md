# Day 20 — MassTransit + RabbitMQ

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

MassTransit = .NET abstraction roye message broker. RabbitMQ = broker. Dejban ba ina **integration event** publish mikone: domain event → outbox → `IEventBus.PublishAsync` → RabbitMQ → consumers. Do style consumer: (1) Dejban modules = inbox table + Quartz, (2) ACL/Identity/RequestTracker = `IConsumer` + MassTransit EF Outbox. Plus request/response (`GetResponse`). Retry + circuit breaker built-in.

---

# BAKHSH-E AVAL: WORLD — Messaging to donya

## Chera message bus?

| sync HTTP | async messaging |
|---|---|
| caller wait | fire-and-forget / eventually |
| tight coupling | loose coupling |
| both up required | producer continues if consumer down (if durable) |
| request/response natural | pub/sub natural |

**Use messaging when:** cross-service side effects, fan-out, load leveling, reliability.

---

## RabbitMQ concepts

| concept | chi |
|---|---|
| **Exchange** | router — receive publish, route to queues |
| **Queue** | buffer of messages |
| **Binding** | exchange → queue rule (routing key) |
| **Routing key** | label for routing |
| **Ack / Nack** | consumer confirm / reject |
| **Durable** | survive broker restart |
| **Prefetch** | how many unacked messages per consumer |

Exchange types: direct, topic, fanout, headers.

```
Publisher → Exchange → (bindings) → Queue(s) → Consumer(s)
```

---

## MassTransit chie?

Library that:
- Maps C# types → exchanges/queues
- Serializes messages (JSON)
- Retries, circuit breaker, outbox
- Consumers as `IConsumer<T>`
- Request/response, sagas, scheduling

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

**Endpoint name formatter:** kebab-case → queue `order-created`.

---

## Publish vs Send

| | Publish | Send |
|---|---|---|
| pattern | pub/sub | point-to-point |
| topology | exchange → multiple queues | specific endpoint |
| use | events (“something happened”) | commands (“do this”) |

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

**Competing consumers:** multiple instances same queue → load balance.  
**InstanceId:** separate queue per service (`order-created-aclserver`) → each service gets a copy (fan-out).

---

## Delivery guarantees

| guarantee | meaning |
|---|---|
| At-most-once | may lose |
| At-least-once | may duplicate ← **usual** |
| Exactly-once | hard; approximate with inbox idempotency |

**Idempotent consumers** required for at-least-once.

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

Fail → retry → still fail → error queue / skip. Too many fails → circuit open → pause.

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

Publish joins same DB transaction as `SaveChanges` — no dual-write problem.

**Alternative:** custom outbox table + background job (Dejban modules — Day 14).

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

Sync-style RPC over bus — timeout possible. Use sparingly (coupling + latency).

---

## RabbitMQ vs Kafka (kholase)

| | RabbitMQ | Kafka |
|---|---|---|
| model | smart broker / queues | log / partitions |
| replay | hard | easy (offset) |
| use | task dispatch, RPC, classic events | analytics, CDC, high throughput stream |

Dejban = RabbitMQ.

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **Sagas / state machines** — MassTransit Automatonymous
- **Message scheduling** — delayed publish
- **Kafka / Azure Service Bus** transports
- **MassTransit.Redis** as bus — package present, not wired
- **Courier routing slips** — multi-step activities
- **Dead letter management UI** beyond RabbitMQ management

---

# BAKHSH-E DOVOM: DEJBAN — MassTransit + RabbitMQ

## Versions

```xml
MassTransit                      8.5.7
MassTransit.RabbitMQ             8.5.7
MassTransit.EntityFrameworkCore  8.5.7
MassTransit.Redis                8.5.7  <!-- versioned, bus NOT using it -->
```

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
- Pre-declares **queues** (kebab-case)
- Exchanges/bindings empty — MassTransit creates at runtime
- Examples: `personnel-created`, `personnel-created-aclserver`, `get-user-site-claims`

Config bind: `RabbitMqTransport` / `RabbitMqTransportOptions`.

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

Application depends on `IEventBus`, na MassTransit types — Clean Architecture.

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

---

## Publish path (Dejban)

```
Personnel.Create → Raise(PersonnelCreatedDomainEvent)
  → EF SaveChanges → custom outbox insert (Day 14)
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

Later: Quartz `ProcessInboxJob` → `IntegrationEventHandler<T>` (read-model upsert).

**Queue names:** plain kebab (`personnel-created`) — modules compete; idempotent by event id.

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

Same for RequestTracker (`InstanceId = "RequestTracker"`), IdentityServer.

**Chera InstanceId?** Har service bayad **hame** event-ha ra bebine (fan-out). Bedune InstanceId, competing consumers → yek service faghat.

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

- Same retry + CB + tenant filters + `ConfigureEndpoints`
- Modules inject `ConfigureConsumers` / `ConfigureReceiveEndpoints`
- **No** MassTransit EF Outbox — custom Quartz outbox/inbox

### Services using MassTransit EF Outbox

ACLServer, IdentityServer, RequestTracker, DCC, GateServer, Reporting.

---

## Tenant context on bus

```csharp
// Common/Tenancy/TenantContextMassTransitExtensions.cs
cfg.UseTenantContextFilters(context);
```

Publish/consume filters carry `site_ids` / super-admin — inbox workers restore `TenantContextAccessor`.

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
Outbox often **skipped** on RPC endpoints (callback excludes `get-*` names).

### Other RPC

- `GetUserSiteClaims` (Identity)
- `IsContractorRegistrationNumberUnique` (Dejban ↔ Identity)
- ACL service endpoints discovery

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

---

## Compare outbox strategies

| | Dejban modules | ACL / Identity / RT |
|---|---|---|
| Write | EF interceptor → `outbox_messages` | MassTransit EF Outbox |
| Process | Quartz + Dapper | MassTransit bus outbox |
| Inbox | custom `inbox_messages` | MassTransit InboxState |
| Consumer | bridge → handler | direct `IConsumer` |

Har do transactional — implementation fargh.

---

## Smell-ha

1. **Dejban ConfigureReceiveEndpoints empty stubs** — dead API surface
2. **Competing consumers across Dejban modules** on same queue name — works via idempotent inbox, vali confusing
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

Day 20 tamum. Ba'd: Day 21 — Transactional Outbox deep dive (khali). Fehrest: [README.md](./README.md).
