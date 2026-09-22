# Day 23 — Inbox + Idempotent Handler

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Inbox** yani payam-e vorudi az bus ra **aval** to DB (`inbox_messages`) zakhire kon, **ba'd** async process kon. Consumer MassTransit to Dejban modules **khodesh** business logic nemizane — faghat `INSERT … ON CONFLICT DO NOTHING`. Quartz `ProcessInboxJob` poll mikone (`FOR UPDATE`), tenant restore, handlers ra seda mizane.

**Idempotent handler** (Scrutor Decorate) ba table `inbox_message_consumers` (messageId + handler name) jeloye double-process ra migire. Outbox (Day 21) = producer reliability; Inbox (inja) = **consumer** reliability. MT `InboxState` (Day 22) = hamin idea, library-owned. Chera do-phase? Ta Rabbit az slow EF cascade block nashe, va replay az inbox table momken bashe.

---

# BAKHSH-E AVAL: WORLD — Inbox + Idempotency to donya

## Chera Inbox?

Consumer mostaghim:

```
Rabbit deliver → Consume() { heavy DB work } → Ack
```

Moshkel-ha:

- Slow consumer → prefetch backlog / timeout
- Crash mid-handler → redelivery → **duplicate side effects**
- Broker retry storms under partial failure
- Hard to pause processing without losing messages

**Inbox pattern:**

```
Rabbit deliver → INSERT inbox (fast) → Ack
… later …
Job → SELECT pending inbox → handle → mark processed
```

Maziat: durable buffer in **your** DB; process at your pace; natural place for idempotency keys. Yani Ack zood, business later — Rabbit nafas mikeshad.

---

## At-least-once everywhere

| hop | guarantee |
|---|---|
| Outbox → Rabbit | at-least-once (Day 21/22) |
| Rabbit → Consumer | at-least-once |
| Inbox job → Handler | at-least-once (crash/retry) |

**Exactly-once** end-to-end practically = at-least-once transport + **idempotent** processing. Broker «exact» nemide; to safe mikoni.

---

## Idempotency — se layer

| layer | mesal |
|---|---|
| **Transport inbox row** | `ON CONFLICT (id) DO NOTHING` — one row per event id |
| **Handler consumer table** | `(inbox_message_id, handler_name)` processed once |
| **Business check** | `if (site already exists) return` |

Hame se useful. Faghat yeki = gaps (crash between handle and mark). Dejban **1 + 4** (exist check / SoftDelete guard) heavily estefade mikone.

---

## Inbox vs Outbox (dobare)

| | Outbox | Inbox |
|---|---|---|
| Direction | leaving this service | entering this service |
| Problem | publish reliably | process reliably / once |
| Dejban write | EF interceptor | MT consumer INSERT |
| Dejban process | ProcessOutboxJob | ProcessInboxJob |
| Dedup table | `outbox_message_consumers` | `inbox_message_consumers` |

Symmetric design — intentional. Yek mental model baraye hardo taraf: persist → poll → handle → mark.

---

## Inbox vs MT InboxState

| | Custom Dejban inbox | MT InboxState (Day 22) |
|---|---|---|
| Who writes | `IntegrationEventConsumer` | MassTransit pipeline |
| Process | Quartz separate | often same consume transaction |
| Multi-schema | per module schema | per service DB |
| Handler style | `IIntegrationEventHandler` + Decorate | `IConsumer.Consume` |
| Ack timing | after INSERT inbox (fast) | after consume+SaveChanges |

Dejban modular: **ack early**, process async — isolates Rabbit from slow EF cascades. Identity: business inside Consume + InboxState.

---

## Idempotent handler patterns (WORLD)

```csharp
// 1) Dedup store
if (alreadyProcessed(messageId, handlerName)) return;
DoWork();
MarkProcessed(messageId, handlerName);

// 2) Natural key upsert
INSERT ... ON CONFLICT (business_key) DO UPDATE ...

// 3) Conditional update
UPDATE ... WHERE version = @expected

// 4) Exist check
if (await repo.Get(id) is not null) return;
```

Dejban uses **1 + 4** heavily. Pattern 2/3 kamtar, vali WORLD miduni.

---

## Ordering & concurrency

Inbox `ORDER BY occurred_on_utc` ≈ FIFO per batch. Cross-event order across producers **not** global.

`FOR UPDATE` locks batch rows. Multi-instance: prefer `SKIP LOCKED` (Dejban often missing — same smell as outbox). SoftDelete ghabl az SiteCreated = NotFound poison — ordering dependency smell.

---

## Poison inbox messages

Same as outbox Day 21: Dejban marks `processed_on_utc` **even on error** → no auto-retry. Ops: read `error`, fix, reset null, or replay. Fast Ack poison ro **delay** mikone ta job — monitor `error` column.

---

# BAKHSH-E DOVOM: DEJBAN — Inbox + Idempotent end-to-end

## Big picture

```
[Rabbit] SiteCreated / PersonnelSoftDeleted / …
    ↓
MassTransit IConsumer<T>
  TenantContextConsumeFilter → SetContext from headers
    ↓
IntegrationEventConsumer<T>   // FAST
  INSERT INTO {schema}.inbox_messages
  ON CONFLICT (id) DO NOTHING
  → Ack
    ↓
Quartz ProcessInboxJob every ~5s
  SELECT … WHERE processed_on_utc IS NULL
  FOR UPDATE LIMIT BatchSize
  foreach:
    deserialize IIntegrationEvent
    TenantContextAccessor.SetContext(SiteIds, IsSuperAdmin)
    IntegrationEventHandlersFactory.GetHandlers(...)
    foreach handler:
      IdempotentIntegrationEventHandler
        → if consumer row exists: skip
        → else real handler (Presentation)
        → INSERT inbox_message_consumers
    UPDATE inbox SET processed_on_utc, error
  COMMIT
```

In diagram ra hafz kon — mosahebe + debug. Do phase: persist, ba'd process.

---

## Phase 1 — `IntegrationEventConsumer` (persist only)

```csharp
// Visitors.Infrastructure/Inbox/IntegrationEventConsumer.cs
internal sealed class IntegrationEventConsumer<TIntegrationEvent>(IDbConnectionFactory dbConnectionFactory)
    : IConsumer<TIntegrationEvent>
    where TIntegrationEvent : IntegrationEvent
{
    public async Task Consume(ConsumeContext<TIntegrationEvent> context)
    {
        await using var connection = await dbConnectionFactory.OpenConnectionAsync();

        var tenantInfo = TenantContextAccessor.Current;
        var integrationEvent = context.Message;

        var inboxMessage = new InboxMessage
        {
            Id = integrationEvent.Id,
            Type = integrationEvent.GetType().Name,
            Content = JsonConvert.SerializeObject(integrationEvent, SerializerSettings.Instance),
            SiteIds = [.. tenantInfo?.SiteIds ?? []],
            IsSuperAdmin = tenantInfo?.IsSuperAdmin ?? false,
            OccurredOnUtc = integrationEvent.OccurredOnUtc
        };

        const string sql =
            """
            INSERT INTO visitors.inbox_messages(id, type, content, site_ids, is_super_admin, occurred_on_utc)
            VALUES (@Id, @Type, @Content::json, @SiteIds, @IsSuperAdmin, @OccurredOnUtc)
            ON CONFLICT (id) DO NOTHING
            """;

        await connection.ExecuteAsync(sql, inboxMessage);
    }
}
```

**Points:**

1. **No business logic** — only durable capture  
2. **Event Id** = inbox PK = dedup key across redeliveries  
3. **Tenant snapshot** from consume filter headers (Day 16)  
4. **ON CONFLICT DO NOTHING** — second delivery noop  
5. Registered per event: `configure.AddConsumer<IntegrationEventConsumer<SiteCreated>>()` (Day 18)

Har module schema khodesh: `visitors.inbox_messages`, `vehicles.inbox_messages`, …

---

## Model

```csharp
public sealed class InboxMessage
{
    public Guid Id { get; init; }
    public string Type { get; init; }
    public string Content { get; init; }      // jsonb, MaxLength 2000 smell
    public List<Guid> SiteIds { get; init; }
    public bool IsSuperAdmin { get; init; }
    public DateTime OccurredOnUtc { get; init; }
    public DateTime? ProcessedOnUtc { get; init; }
    public string? Error { get; init; }
}

public sealed class InboxMessageConsumer(Guid inboxMessageId, string name)
{
    public Guid InboxMessageId { get; init; }
    public string Name { get; init; } // decorated handler type name
}
// PK (InboxMessageId, Name)
```

EF configs: `ToTable("inbox_messages")` / `inbox_message_consumers` — applied on each module DbContext. Shape almost mirror-e outbox.

---

## Phase 2 — `ProcessInboxJob`

```csharp
[DisallowConcurrentExecution]
internal sealed class ProcessInboxJob(...) : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        await using var connection = await dbConnectionFactory.OpenConnectionAsync();
        await using var transaction = await connection.BeginTransactionAsync();

        var messages = await GetInboxMessagesAsync(connection, transaction);

        foreach (var inboxMessage in messages)
        {
            Exception? exception = null;
            try
            {
                var integrationEvent = JsonConvert.DeserializeObject<IIntegrationEvent>(
                    inboxMessage.Content, SerializerSettings.Instance)!;

                using var scope = serviceScopeFactory.CreateScope();
                TenantContextAccessor.SetContext(
                    [.. inboxMessage.SiteIds], inboxMessage.IsSuperAdmin);

                var handlers = IntegrationEventHandlersFactory.GetHandlers(
                    integrationEvent.GetType(),
                    scope.ServiceProvider,
                    Presentation.AssemblyReference.Assembly);

                foreach (var handler in handlers)
                    await handler.Handle(integrationEvent, context.CancellationToken);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "... {MessageId}", inboxMessage.Id);
                exception = ex;
            }

            await UpdateInboxMessageAsync(connection, transaction, inboxMessage, exception);
        }

        await transaction.CommitAsync();
    }
}
```

Poll:

```sql
SELECT id, content, site_ids, is_super_admin
FROM visitors.inbox_messages
WHERE processed_on_utc IS NULL
ORDER BY occurred_on_utc
LIMIT @BatchSize
FOR UPDATE
```

Mark:

```sql
UPDATE visitors.inbox_messages
SET processed_on_utc = @ProcessedOnUtc, error = @Error
WHERE id = @Id
```

**Smell vs Outbox job:** `ProcessOutboxJob` has `finally { TenantContextAccessor.Clear(); }` — **ProcessInboxJob (Visitors) Clear nadare** in the snippet — AsyncLocal leak risk across iterations / job end. Check your module copy; treat as bug if missing.

**Same smell:** error ⇒ still processed (no auto-retry).

---

## Options + Quartz

```json
// modules.visitors.json
"Visitors": {
  "Inbox": { "IntervalInSeconds": 5, "BatchSize": 50 }
}
```

```csharp
services.Configure<InboxOptions>(configuration.GetSection("Visitors:Inbox"));
services.ConfigureOptions<ConfigureProcessInboxJob>();
```

Same pattern as Outbox options (Day 18/21). Interval tradeoff: lag vs poll load.

---

## `IntegrationEventHandlersFactory`

```csharp
// scan Presentation assembly for IIntegrationEventHandler<TEvent>
// cache by assembly+type name
// GetRequiredService → resolves Decorate chain (idempotent outer)
```

Handlers live in **Presentation** (integration event handlers), registered in `AddIntegrationEventHandlers` with Scrutor Decorate (Day 18/24). Domain handlers Application; integration handlers Presentation — Clean Architecture split.

---

## IdempotentIntegrationEventHandler (Scrutor)

```csharp
internal sealed class IdempotentIntegrationEventHandler<TIntegrationEvent>(
    IIntegrationEventHandler<TIntegrationEvent> decorated,
    IDbConnectionFactory dbConnectionFactory)
    : IntegrationEventHandler<TIntegrationEvent>
    where TIntegrationEvent : IIntegrationEvent
{
    public override async Task Handle(TIntegrationEvent integrationEvent, CancellationToken ct)
    {
        await using var connection = await dbConnectionFactory.OpenConnectionAsync();

        var key = new InboxMessageConsumer(integrationEvent.Id, decorated.GetType().Name);

        if (await InboxConsumerExistsAsync(connection, key))
            return;

        await decorated.Handle(integrationEvent, ct);

        await InsertInboxConsumerAsync(connection, key);
    }
}
```

```sql
SELECT EXISTS(
  SELECT 1 FROM visitors.inbox_message_consumers
  WHERE inbox_message_id = @InboxMessageId AND name = @Name)

INSERT INTO visitors.inbox_message_consumers(inbox_message_id, name)
VALUES (@InboxMessageId, @Name)
```

**Mirror** of `IdempotentDomainEventHandler` on outbox side (Day 21) — same shape, inbox tables.

**Race window:** handle succeeds, crash before INSERT consumer → re-run handler. Business handler must tolerate (exist check / SoftDelete idempotent).

**Separate connection** from job's FOR UPDATE transaction — not one atomic unit with mark processed.

---

## Real handlers — business idempotency

### SiteCreated (Visitors)

```csharp
public sealed class SiteCreatedIntegrationEventHandler(ISiteRepository siteRepository, IUnitOfWork unitOfWork)
    : IntegrationEventHandler<SiteCreated>
{
    public override async Task Handle(SiteCreated e, CancellationToken ct)
    {
        if (await siteRepository.GetAsync(e.SiteId, ct) is not null)
            return; // already synced

        siteRepository.Insert(Site.Create(...));
        await unitOfWork.SaveChangesAsync(ct);
    }
}
```

### PersonnelSoftDeleted (Vehicles)

```csharp
// load local personnel copy — throw if missing (strict)
// cascade delete assignments / ownerships
// personnel.SoftDelete()
// SaveChanges
```

SoftDelete domain method idempotent (`if (IsDeleted) return`) — good. **Throw NotFound** if copy never arrived — poison until Site/Personnel created events catch up (ordering dependency smell). Design for tolerance better az strict throw.

---

## Full chain — SoftDelete Personnel (consumer view)

```
Personnels outbox → PersonnelSoftDeleted on Rabbit
  → Visitors IntegrationEventConsumer → visitors.inbox_messages
  → Vehicles IntegrationEventConsumer → vehicles.inbox_messages
  → Armory / CashLogistics / … same

Each module ProcessInboxJob independently:
  → Idempotent handler → SoftDelete local copy / cleanup
```

Fan-out = many inbox rows (one per module schema), same event Id. Yani yek Rabbit message, chand durable inbox.

---

## Outbox consumers vs Inbox consumers (don't mix up)

| table | when |
|---|---|
| `{schema}.outbox_message_consumers` | domain event handlers after outbox dispatch |
| `{schema}.inbox_message_consumers` | integration event handlers after inbox dispatch |

Both Scrutor Decorate. Both `(messageId, handlerTypeName)`. Smell: rename handler = new key; in-flight duplicate momken.

---

## Contrast Identity `IConsumer` (Day 22)

Identity `PersonnelCreatedConsumer` = **business inside Consume** + MT InboxState — no separate Quartz inbox table.

Dejban module = **two-phase** (persist → job → handler).

| | Dejban module | Identity |
|---|---|---|
| Ack | after inbox INSERT | after Consume+SaveChanges |
| Latency to effect | +inbox interval | immediate (in consume) |
| Isolation from Rabbit | high | consume holds message |
| Code | more moving parts | simpler MT style |

---

## Why two-phase in modular monolith?

1. **Many handlers / heavy cascades** (Vehicles SoftDelete cleans assignments)  
2. **Don't block** competing consumers on Rabbit  
3. **Uniform** with outbox Quartz ops model  
4. **Per-schema** DB ownership clear  
5. Can replay from inbox table without Rabbit  

Tradeoff: eventual lag (~seconds); more ops surfaces. Interview: in tradeoff ro boland bego.

---

## Failure modes

| failure | result | mitigation |
|---|---|---|
| Duplicate Rabbit delivery | ON CONFLICT skip | OK |
| Crash after INSERT before Ack | redelivery → CONFLICT noop | OK |
| Handler throws | processed+error | manual reset |
| Crash after handler before consumer INSERT | handler runs twice | business idempotent |
| Crash after consumer INSERT before inbox UPDATE | re-run; idempotent skip handler; mark processed | OK-ish |
| Missing Clear TenantContext | wrong tenant next message | add finally Clear |
| Handler NotFound (ordering) | error column | ensure create events first / tolerate missing |
| FOR UPDATE multi-node | blocking | SKIP LOCKED |

---

## Debug checklist

1. Message on Rabbit? (queue depth)  
2. Row in `{schema}.inbox_messages`?  
3. `ON CONFLICT` — duplicate id already there?  
4. `SiteIds` on inbox row empty? (tenant filter headers)  
5. Job logs Beginning process inbox?  
6. `processed_on_utc` / `error`?  
7. Row in `inbox_message_consumers`?  
8. Business table updated (Site/Personnel copy)?  
9. Handler registered in Presentation + Decorate?  
10. Requeue: `UPDATE … SET processed_on_utc = NULL, error = NULL` + delete consumer row if need re-run handler  

---

## Observability SQL

```sql
-- backlog
SELECT COUNT(*) FROM visitors.inbox_messages WHERE processed_on_utc IS NULL;

-- failures
SELECT id, type, LEFT(error, 200), occurred_on_utc
FROM visitors.inbox_messages
WHERE error IS NOT NULL
ORDER BY processed_on_utc DESC
LIMIT 30;

-- which handlers ran
SELECT * FROM visitors.inbox_message_consumers
WHERE inbox_message_id = @Id;
```

---

## Smell-ha

1. **Processed on error** — no auto-retry  
2. **No SKIP LOCKED**  
3. **TenantContext Clear missing** on some ProcessInboxJob copies  
4. **Content MaxLength(2000)**  
5. **8× copy-paste** ProcessInboxJob / IdempotentIntegration / Consumer SQL schema  
6. **Throw NotFound** in sync handlers — brittle ordering  
7. **Long FOR UPDATE** while handlers run SaveChanges + maybe more  
8. **Idempotent connection ≠ job transaction**  
9. **Handler type name** rename breaks dedup key semantics for in-flight  
10. **Fast Ack** hides poison until job — monitor error column  
11. **Multiple handlers** order undefined  
12. **Inventory** thin consumers — inconsistent maturity  

---

## 25 soal-e mosahebe

1. Inbox pattern chie?  
2. Chera na business dar IConsumer (Dejban)?  
3. ON CONFLICT DO NOTHING?  
4. At-least-once + idempotent?  
5. inbox_message_consumers chie?  
6. Se layer idempotency?  
7. ProcessInboxJob vs ProcessOutboxJob?  
8. Tenant snapshot cherā?  
9. Scrutor Decorate role?  
10. MT InboxState vs custom inbox?  
11. SiteCreated exist check?  
12. SoftDelete idempotent?  
13. Chera event Id = inbox Id?  
14. Duplicate fan-out across modules?  
15. Poison message strategy Dejban?  
16. SKIP LOCKED?  
17. Fast Ack maziat?  
18. Crash between handle and consumer insert?  
19. Factory scans which assembly?  
20. Outbox consumers vs inbox consumers?  
21. Ordering create vs soft-delete?  
22. Replay az inbox?  
23. Interval/BatchSize tradeoff?  
24. Identity consumer farq?  
25. Chejori test idempotency?

---

## Senario-ha

### A) Happy SiteCreated  
INSERT inbox → job → Site.Create local → consumers row → processed.

### B) Double delivery  
Second INSERT conflict → one inbox row → one process (or idempotent skip).

### C) Handler fail  
processed + error; Site missing; fix code; reset processed + delete consumer row; reprocess.

### D) SoftDelete before SiteCreated (wrong order)  
Personnel handler NotFound → error; later hard to recover — design for tolerance.

### E) Two handlers on one event  
Both get separate consumer keys; one can fail independently (but one Update processed for whole message — **smell**: one exception fails whole message mark with error even if first handler succeeded… actually foreach handlers in try — one throw aborts remaining; consumer rows may partial; processed+error). Important interview point!

**Partial handler success:** Handler A inserted consumer row; Handler B throws → message marked error; retry: A skipped (idempotent), B runs again. Good **if** A left consumer row. If A succeeded but crashed before consumer insert, A runs twice — need business idempotent.

---

## Mini lab

1. Publish/create Site from Identity; watch `visitors.inbox_messages`  
2. Wait job; see Site in visitors schema  
3. Inspect `inbox_message_consumers`  
4. Manually re-INSERT same event id via consumer path — CONFLICT  
5. Force handler exception; see error column  
6. Compare Identity PersonnelCreated (no inbox table)  

---

## Resume

**short:**

> Built a two-phase inbox for modular consumers: MassTransit handlers only persist integration events into per-schema `inbox_messages` (`ON CONFLICT DO NOTHING`), Quartz workers dispatch idempotent `IIntegrationEventHandler`s decorated with Scrutor against `inbox_message_consumers`, restoring tenant context for EF-filtered upserts and soft-deletes of local read models.

**bullets:**

- Separated broker ack (fast inbox insert) from heavy cross-aggregate sync work  
- Deduplicated bus redeliveries at row level and handler level  
- Combined transport idempotency with domain checks (`GetAsync` exists / `SoftDelete` guards)  
- Aligned inbox processing with outbox jobs for symmetric ops (backlog, error columns, batching)  

**skills:** `Inbox Pattern, Idempotent Consumers, MassTransit, Quartz.NET, Dapper, Scrutor, Integration Events, At-least-once Delivery, PostgreSQL, Modular Monolith`

---

## File-haye mohem

| chi | koja |
|---|---|
| InboxMessage | `Common/.../Inbox/InboxMessage.cs` |
| InboxMessageConsumer | `.../InboxMessageConsumer.cs` |
| EF configs | `InboxMessageConfiguration.cs` |
| Handlers factory | `IntegrationEventHandlersFactory.cs` |
| MT consumer | e.g. `Visitors.../Inbox/IntegrationEventConsumer.cs` |
| Process job | `Visitors.../Inbox/ProcessInboxJob.cs` |
| Idempotent decorate | `Visitors.../Inbox/IdempotentIntegrationEventHandler.cs` |
| Quartz config | `ConfigureProcessInboxJob.cs` |
| Options | `InboxOptions` + `modules.*.json` |
| Sample handler | `Visitors.../Sites/SiteCreatedIntegrationEventHandler.cs` |
| Cascade example | `Vehicles.../PersonnelDeletedIntegrationEventHandler.cs` |
| Module register | `AddIntegrationEventHandlers` + `AddConsumer<IntegrationEventConsumer<…>>` |

---

## Connection to other days

| day | rabt |
|---|---|
| 15 Soft delete | SoftDelete in integration handlers |
| 16 Tenancy | SiteIds on inbox + SetContext |
| 18 Modular DI | Decorate + ConfigureConsumers |
| 19 Dapper | SQL in consumer/job |
| 20 MassTransit | IConsumer bridge |
| 21 Outbox | producer twin |
| 22 MT InboxState | microservice twin |
| 24 Scrutor | Decorate deep dive |

---

## Chejori digest koni

1. Draw two-phase inbox (10 min)  
2. Read IntegrationEventConsumer + ProcessInboxJob (25 min)  
3. SoftDelete E2E SQL inbox (20 min)  
4. Explain partial multi-handler failure (10 min)  
5. 25 soal (20 min)

---

## Glossary

| kalame | ma'ni |
|---|---|
| Inbox | durable inbound message store |
| Two-phase consume | persist then process |
| Idempotent | safe to run twice |
| Dedup key | event id (+ handler name) |
| ON CONFLICT DO NOTHING | insert ignore duplicate PK |
| Consumer table | which handlers finished message |
| Fast ack | ack after persist, not after business |
| Poison inbox | failed processed row needing ops |
| Read model sync | local Site/Personnel copy update |

---

## Deep dive — multi-handler partial failure

```csharp
try {
  foreach (handler in handlers) // A, B, C
    await handler.Handle(...);
}
catch { exception = ... }
await UpdateInbox(..., exception); // always mark processed
```

Agar B throw:

- A maybe wrote `inbox_message_consumers`  
- C never ran  
- Message `error` set  

Retry after fix:

- A skipped (idempotent)  
- B runs  
- C runs  

Design handlers **independent** and **idempotent**. Don’t rely on «all or nothing» across handlers without a saga.

---

## Deep dive — replay playbook

```sql
-- 1) inspect
SELECT * FROM vehicles.inbox_messages WHERE id = @id;

-- 2) allow reprocess
DELETE FROM vehicles.inbox_message_consumers WHERE inbox_message_id = @id;
UPDATE vehicles.inbox_messages
SET processed_on_utc = NULL, error = NULL
WHERE id = @id;

-- 3) wait job OR run job once in eng environment
```

Production: feature flag / admin tool better than raw SQL — still know SQL.

---

## Decision: when inbox two-phase?

| use two-phase (Dejban) | use inline consume (Identity) |
|---|---|
| Heavy multi-aggregate sync | Light single aggregate |
| Many handlers per event | One consumer class |
| Want ack latency low | OK to hold message |
| Already Quartz outbox culture | MT EF outbox culture |

---

## Interview 60s

> «Modular consumers ack Rabbit after a fast inbox insert, then Quartz dispatches Scrutor-decorated integration handlers. We dedupe at the row with ON CONFLICT and at the handler with inbox_message_consumers, plus business exists checks. Same ops model as our custom outbox.»

---

*Day 23 tamum. Ba'd: Day 24 — Decorator (Scrutor) (amade). Fehrest: [README.md](./README.md).*
