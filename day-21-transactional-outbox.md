# Day 21 — Transactional Outbox (custom Dejban)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Transactional Outbox** yani event ra **hamoon transaction**-e ke entity save mishe, to table `outbox_messages` minevisi; ba'd ye worker (Quartz) poll mikone va publish/handle mikone. Chera? Ta **dual-write** (DB OK + Rabbit fail, ya baraks) etefagh nayofte. Do system (Postgres + Rabbit) yek distributed transaction nistan — 2PC gerun o rare-e. Outbox = single DB transaction for business data + «intent to publish».

Dejban custom: EF `InsertOutboxMessagesInterceptor` → schema-local `outbox_messages` → `ProcessOutboxJob` (Dapper + `FOR UPDATE`) → `DomainEventHandlersFactory` → (Scrutor) idempotent handler → ziad `IEventBus.PublishAsync` → MassTransit/Rabbit. In fasl **pattern + pipeline-e custom**; Day 19 = Dapper SQL; Day 22 = MassTransit EF Outbox (style digar); Day 23 = Inbox side.

---

# BAKHSH-E AVAL: WORLD — Transactional Outbox to donya

## Dual-write problem

```
Handler:
  1) SaveChanges → Personnel inserted   ✅
  2) bus.Publish(PersonnelCreated)      ❌ broker down / timeout
→ DB has personnel, other modules NEVER sync
```

Ya:

```
  1) Publish first   ✅
  2) SaveChanges     ❌ constraint fail
→ Ghost event, no row
```

Yani chi? Do store bedune atomicity = inconsistency. Outbox in moshkel ro ba «message intent» to **hamun** DB resolve mikone.

---

## Pattern — steps

```
[Same DB transaction]
  INSERT/UPDATE business tables
  INSERT outbox_messages (event payload JSON)
COMMIT

[Later — separate process/job]
  SELECT unprocessed FROM outbox FOR UPDATE
  dispatch (in-process handlers and/or bus publish)
  UPDATE outbox SET processed_on_utc = now()
```

**Guarantee:** age business commit shod, outbox row **hast**. Delivery be handlers **at-least-once**-e (retries / multi workers → need **idempotency**). Exactly-once end-to-end practically = at-least-once + idempotent processing.

---

## Chera na 2PC / XA?

| | Outbox | 2PC |
|---|---|---|
| Complexity | medium | high |
| Broker support | any | needs XA |
| Latency | async lag | sync lock |
| Ops | poller + monitoring | coordinator failure modes |

Industry default for microservices: **Outbox** (ya Inbox, Change Data Capture / Debezium). Dejban ham outbox-e app-level — CDC estefade nemikone.

---

## CDC / Debezium alternative

Postgres WAL → Debezium → Kafka. Outbox table ya even business table CDC. Dejban **estefade nemikone** — app-level interceptor + Quartz. Simpler ops for their scale; more app code. Interview: «CDC push-based; ma poll-based custom.»

---

## Outbox table design (classic)

| column | ma'ni |
|---|---|
| `id` | event id (often = domain event id) |
| `type` | CLR / message type name |
| `content` | JSON payload |
| `occurred_on` | when raised |
| `processed_on` | null = pending |
| `error` | last failure (optional) |
| extras | tenant ids, correlation, headers |

Index: `(processed_on) WHERE processed_on IS NULL` + `occurred_on` for FIFO poll. Dejban `SiteIds` / `IsSuperAdmin` ham roye row snapshot mikone ta background tenant dashte bashe.

---

## Polling strategies

| strategy | note |
|---|---|
| `SELECT … FOR UPDATE` | lock rows in job transaction |
| `FOR UPDATE SKIP LOCKED` | multi-instance safe — workers don't block |
| `DELETE` after process | alternate to processed flag |
| LISTEN/NOTIFY | wake poller (optional) |
| CDC | push instead of poll |

**Dejban:** `FOR UPDATE` **bedune** `SKIP LOCKED` + Quartz `[DisallowConcurrentExecution]` per job type — single concurrent runner per scheduler; multi-node still risk without SKIP LOCKED / clustered Quartz care. In smell-e scalability-e.

---

## At-least-once + idempotency

Outbox → handler may run twice (crash after handle, before mark processed; or dual workers).

Fix:

1. Mark processed **after** success only (ideal)
2. Idempotent handlers (consumer table keyed by messageId + handler name)
3. Natural idempotency (upsert by business key)

Dejban uses (2) heavily — `outbox_message_consumers` (Day 23/24 deepen). **Also** marks processed even on error (see smells) — failed message won't auto-retry via poll! Yani poison az loop kharej mishe, vali ops bayad dasti requeue kone.

---

## Outbox vs Inbox

| | Outbox | Inbox |
|---|---|---|
| Side | producer | consumer |
| Problem | reliable publish | reliable/idempotent consume |
| Dejban | this day | Day 23 |

Flow Dejban modular:

```
Module A outbox → domain handler → Rabbit publish
Module B MassTransit consumer → INSERT inbox
Module B ProcessInboxJob → integration handlers
```

Symmetric design — intentional. Yek mental model baraye hardo taraf.

---

## Immediate domain dispatch vs outbox

| | In-process after SaveChanges | Outbox |
|---|---|---|
| Same request | sync side effects | eventual |
| Failure after commit | side effect lost | row remains |
| Request latency | higher if handlers heavy | low (just insert) |
| Transaction boundary | handlers after commit usually | write in same tx |

Dejban: Raise in domain → **deferred** to interceptor on SaveChanges → worker later. Handler HTTP returns before Rabbit fan-out completes (eventual consistency). Chera khube? Request zood barmigarde; reliability az outbox miad.

---

## Poison / failed messages

Options:

- Leave `processed_on` null + retry count
- Move to `outbox_poison` / dead letter
- Mark processed + `error` column (manual ops) ← **Dejban style**

Monitoring: alert on `error IS NOT NULL` or growing pending age. Bedune alert, poison silent mimune.

---

## Comparison matrix

| approach | Dejban modular | Identity/ACL (teaser Day 22) |
|---|---|---|
| Write outbox | EF interceptor | MassTransit EF Outbox middleware |
| Table | `*.outbox_messages` | MT `outbox_message` / state |
| Dispatch | Quartz + Dapper | MT bus outbox delivery |
| Domain events | first-class | often integration-focused |

Har do «transactional outbox» family — implementation farq. Modular = Raise + interceptor; microservice = Publish + Bus Outbox.

---

# BAKHSH-E DOVOM: DEJBAN — custom outbox end-to-end

## Pipeline — yek negah

```
Personnel.SoftDelete()
  → Raise(PersonnelDeletedDomainEvent)     // in-memory list on Entity

DeletePersonnelHandler
  → unitOfWork.SaveChangesAsync()
       → InsertOutboxMessagesInterceptor.SavingChangesAsync
            → read DomainEvents from ChangeTracker Entries<Entity>
            → ClearDomainEvents()
            → Add OutboxMessage { Id, Type, Content jsonb, SiteIds, IsSuperAdmin, OccurredOnUtc }
       → SQL: UPDATE personnel + INSERT outbox_messages   // ONE transaction
  → HTTP 204

… seconds later …

Quartz ProcessOutboxJob (Personnels)
  → BEGIN
  → SELECT … FROM personnels.outbox_messages
       WHERE processed_on_utc IS NULL
       ORDER BY occurred_on_utc LIMIT BatchSize
       FOR UPDATE
  → foreach message:
       deserialize IDomainEvent
       TenantContextAccessor.SetContext(SiteIds, IsSuperAdmin)
       DomainEventHandlersFactory.GetHandlers(...)
       foreach handler (idempotent decorator → real):
            PersonnelDeletedDomainEventHandler
              → eventBus.PublishAsync(PersonnelSoftDeleted)  // MassTransit
       UPDATE outbox SET processed_on_utc, error
  → COMMIT
```

In diagram ra **hafz kon** — mosahebe + debug. Har step ye failure mode dare (jadval zir).

---

## Domain side — Raise

```csharp
// Dejban.Common.Domain/Entity.cs
private readonly List<IDomainEvent> _domainEvents = [];

public IReadOnlyCollection<IDomainEvent> DomainEvents => [.. _domainEvents];

protected void Raise(IDomainEvent domainEvent) → _domainEvents.Add(domainEvent);

public void ClearDomainEvents() → _domainEvents.Clear();
```

```csharp
// Personnel.SoftDelete
Raise(new PersonnelDeletedDomainEvent(Id, deletedBy));
```

Event `Id` / `OccurredOnUtc` az `DomainEvent` base — **same Guid** later = outbox message id = idempotency key. Yani yek id az domain ta outbox ta (optional) integration event.

---

## Write path — `InsertOutboxMessagesInterceptor`

```csharp
// Common/.../Outbox/InsertOutboxMessagesInterceptor.cs
public sealed class InsertOutboxMessagesInterceptor : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(...)
    {
        if (eventData.Context is not null)
            InsertOutboxMessages(eventData.Context);
        return base.SavingChangesAsync(...);
    }

    private static void InsertOutboxMessages(DbContext context)
    {
        var tenantInfo = TenantContextAccessor.Current;

        var outboxMessages = context.ChangeTracker
            .Entries<Entity>()
            .Select(e => e.Entity)
            .SelectMany(entity =>
            {
                var events = entity.DomainEvents;
                entity.ClearDomainEvents();
                return events;
            })
            .Select(domainEvent => new OutboxMessage
            {
                Id = domainEvent.Id,
                Type = domainEvent.GetType().Name,
                Content = JsonConvert.SerializeObject(domainEvent, SerializerSettings.Instance),
                SiteIds = [.. tenantInfo?.SiteIds ?? []],
                IsSuperAdmin = tenantInfo?.IsSuperAdmin ?? false,
                OccurredOnUtc = domainEvent.OccurredOnUtc
            })
            .ToList();

        context.Set<OutboxMessage>().AddRange(outboxMessages);
    }
}
```

**Critical properties:**

1. Runs **before** SaveChanges SQL flush → same transaction
2. Clears domain events so double-save doesn't duplicate
3. Snapshots **tenant** for background (Day 16)
4. Registered singleton; each module DbContext `.AddInterceptors(...)`

```csharp
services.TryAddSingleton<InsertOutboxMessagesInterceptor>();
// PersonnelsModule:
.AddInterceptors(sp.GetRequiredService<InsertOutboxMessagesInterceptor>())
```

Age interceptor ro forget koni roye DbContext-e jadid: business save mishe, **hich** outbox row nist — silent sync bug.

---

## Table model

```csharp
public sealed class OutboxMessage
{
    public Guid Id { get; init; }
    public string Type { get; init; }
    public string Content { get; init; }      // jsonb
    public List<Guid> SiteIds { get; init; }
    public bool IsSuperAdmin { get; init; }
    public DateTime OccurredOnUtc { get; init; }
    public DateTime? ProcessedOnUtc { get; init; }
    public string? Error { get; init; }
}
```

```csharp
// OutboxMessageConfiguration
builder.ToTable("outbox_messages");
builder.HasKey(o => o.Id);
builder.Property(o => o.Content).HasMaxLength(2000).HasColumnType("jsonb");
```

Per module schema: `personnels.outbox_messages`, `visitors.outbox_messages`, …

**Smell:** `HasMaxLength(2000)` + `jsonb` — large domain events may truncate/fail; 2000 often too small for rich payloads.

Consumer dedup table:

```csharp
public sealed class OutboxMessageConsumer(Guid outboxMessageId, string name)
{
    public Guid OutboxMessageId { get; init; }
    public string Name { get; init; }  // handler type name
}
// PK (OutboxMessageId, Name)
```

In table ro Scrutor decorator minevise (Day 24) — ta double Handle skip she.

---

## Options + Quartz registration

```json
// modules.personnels.json
"Personnels": {
  "Outbox": { "IntervalInSeconds": 5, "BatchSize": 50 }
}
```

```csharp
services.Configure<OutboxOptions>(configuration.GetSection("Personnels:Outbox"));
services.ConfigureOptions<ConfigureProcessOutboxJob>();
```

```csharp
internal sealed class ConfigureProcessOutboxJob(IOptions<OutboxOptions> outboxOptions)
    : IConfigureOptions<QuartzOptions>
{
    public void Configure(QuartzOptions options)
    {
        string jobName = typeof(ProcessOutboxJob).FullName!;
        options
            .AddJob<ProcessOutboxJob>(c => c.WithIdentity(jobName))
            .AddTrigger(c => c.ForJob(jobName)
                .WithSimpleSchedule(s =>
                    s.WithIntervalInSeconds(_outboxOptions.IntervalInSeconds).RepeatForever()));
    }
}
```

Har module **own** `ProcessOutboxJob` type + own schema SQL → 8 jobs on shared Quartz host. Interval 5s → typical delay 0–5s (+ batch time). Tradeoff: kamtar interval = kamtar lag, bishtar poll load.

---

## `ProcessOutboxJob` — dispatch

```csharp
[DisallowConcurrentExecution]
internal sealed class ProcessOutboxJob(...) : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        await using var connection = await dbConnectionFactory.OpenConnectionAsync();
        await using var transaction = await connection.BeginTransactionAsync();

        var messages = await GetOutboxMessagesAsync(connection, transaction);

        foreach (var outboxMessage in messages)
        {
            Exception? exception = null;
            try
            {
                IDomainEvent domainEvent = JsonConvert.DeserializeObject<IDomainEvent>(
                    outboxMessage.Content, SerializerSettings.Instance)!;

                using var scope = serviceScopeFactory.CreateScope();
                TenantContextAccessor.SetContext(
                    [.. outboxMessage.SiteIds], outboxMessage.IsSuperAdmin);

                var handlers = DomainEventHandlersFactory.GetHandlers(
                    domainEvent.GetType(),
                    scope.ServiceProvider,
                    Application.AssemblyReference.Assembly);

                foreach (var handler in handlers)
                    await handler.Handle(domainEvent, context.CancellationToken);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "... {MessageId}", outboxMessage.Id);
                exception = ex;
            }
            finally
            {
                TenantContextAccessor.Clear();
            }

            await UpdateOutboxMessageAsync(connection, transaction, outboxMessage, exception);
        }

        await transaction.CommitAsync();
    }
}
```

### Poll SQL

```sql
SELECT id, content, site_ids, is_super_admin
FROM personnels.outbox_messages
WHERE processed_on_utc IS NULL
ORDER BY occurred_on_utc
LIMIT @BatchSize
FOR UPDATE
```

### Mark processed

```sql
UPDATE personnels.outbox_messages
SET processed_on_utc = @ProcessedOnUtc,
    error = @Error
WHERE id = @Id
```

**Even when `exception != null`**, `processed_on_utc` set mishe → **no automatic retry**. Ops must requeue manually or fix + reset null. In smell #1-e — interview gold.

---

## `DomainEventHandlersFactory`

```csharp
public static IEnumerable<IDomainEventHandler> GetHandlers(
    Type type, IServiceProvider sp, Assembly assembly)
{
    // cache: assembly+eventType → handler Types implementing IDomainEventHandler<TEvent>
    // resolve each via GetRequiredService (gets Decorate chain)
}
```

Handlers registered in `AddXxxModule` → `TryAddScoped` + `Decorate` idempotent (Day 18/24). Factory concrete type resolve mikone; Scrutor wrapper barmigardune.

---

## Idempotent decorator (outbox consumers)

```csharp
// Personnels.Infrastructure/Outbox/IdempotentDomainEventHandler.cs
if (await OutboxConsumerExistsAsync(...)) return;

await decorated.Handle(domainEvent, ct);

await InsertOutboxConsumerAsync(...); // personnels.outbox_message_consumers
```

Agar job crash **after** handler success **before** outbox UPDATE processed:

- next poll picks message again
- idempotent skip if consumer row exists
- then marks processed again

Agar crash **before** consumer insert → handler runs twice → handler itself must be safe (publish duplicate integration event → inbox idempotency Day 23).

**Gap:** consumer insert va outbox processed update **transactions joda** (Dapper connection in decorator vs job transaction) — classic at-least-once nuance. Yani atomic «handle + mark» nist.

---

## Domain handler → integration event

```csharp
internal sealed class PersonnelDeletedDomainEventHandler(IEventBus eventBus)
    : DomainEventHandler<PersonnelDeletedDomainEvent>
{
    public override async Task Handle(PersonnelDeletedDomainEvent domainEvent, CancellationToken ct)
    {
        await eventBus.PublishAsync(
            new PersonnelSoftDeleted(
                domainEvent.Id,
                domainEvent.OccurredOnUtc,
                domainEvent.PersonnelId,
                domainEvent.DeletedBy),
            ct);
    }
}
```

```csharp
// EventBus → MassTransit IBus
public async Task PublishAsync<T>(T integrationEvent, CancellationToken ct)
    => await bus.Publish(integrationEvent, ct);
```

Tenant headers: MT publish filter reads `TenantContextAccessor` (restored in job) → `X-Tenant-SiteIds` (Day 16/20). Publish **inside** FOR UPDATE transaction = lock across network I/O (smell #12).

---

## Serialization

Newtonsoft + custom `SerializerSettings` (type handling for `IDomainEvent` polymorph deserialize). `Type` column stores name; content must round-trip to concrete event type.

**Smell risk:** serializer settings mismatch → deserialize null/throw → message marked processed with error. Deploy coordination: SerializerSettings bayad across modules yeksan bemune.

---

## Multi-module isolation

| module | outbox table | job |
|---|---|---|
| Personnels | `personnels.outbox_messages` | `Personnels...ProcessOutboxJob` |
| Visitors | `visitors.outbox_messages` | … |
| … | 8 schemas | 8 jobs |

Domain event in Personnels **only** Personnels Application handlers. Cross-module = integration event on bus, not shared outbox table. Yani modular boundary to messaging ham hafz mishe.

---

## End-to-end example — SoftDelete Personnel

1. API Delete → SoftDelete → Raise domain event  
2. SaveChanges → row `is_deleted` + outbox insert  
3. Job → PersonnelDeletedDomainEventHandler → `PersonnelSoftDeleted` publish  
4. Vehicles/Visitors/… consumers → inbox (Day 23) → local SoftDelete copies  

Reliability: step 2 atomic. Steps 3–4 eventual. HTTP 204 ghabl az fan-out.

---

## Latency & ordering

- Interval 5s → typical delay 0–5s (+ batch time)
- `ORDER BY occurred_on_utc` ≈ FIFO per batch
- Multi-handler same event: sequential in foreach
- No global order across modules

Depend nakon on «handler A ghabl az B» across reflection order — handlers independent bashan.

---

## Observability

Log lines: `Beginning/Completed to process outbox messages`.

Useful queries:

```sql
-- backlog
SELECT COUNT(*) FROM personnels.outbox_messages WHERE processed_on_utc IS NULL;

-- failures (stuck as processed with error)
SELECT id, type, error, occurred_on_utc
FROM personnels.outbox_messages
WHERE error IS NOT NULL
ORDER BY processed_on_utc DESC
LIMIT 50;

-- oldest pending age
SELECT MIN(occurred_on_utc) FROM personnels.outbox_messages WHERE processed_on_utc IS NULL;
```

Alert: pending age > N minutes; error rate.

Serilog filters in Program **exclude** noisy Outbox SQL (optional) — don't blind yourself to errors. Filter noise, na exception.

---

## vs Day 19 / 20 / 22 / 23

| day | focus |
|---|---|
| **19** | Dapper APIs used inside jobs |
| **20** | MassTransit/Rabbit after publish |
| **21 (inja)** | transactional outbox **pattern** + Dejban custom write/dispatch |
| **22** | MassTransit EF Outbox (standalone services) |
| **23** | Inbox + idempotent integration handlers |
| **24** | Scrutor Decorate deep dive |

---

## Chera custom, na faghat MT Outbox?

Modular monolith:

- Domain events first-class in EF entities
- Per-schema outbox co-located with module DbContext
- Handlers decide publish / other side effects
- One interceptor shared

Standalone Identity/ACL: less domain-event ceremony → MT EF Outbox closer to bus.

Har do «transactional outbox» family — implementation farq. Interview 60s: «modular = custom; identity/acl = MT EF; contract = Rabbit.»

---

## Failure modes (whiteboard)

| failure | natije | mitigation |
|---|---|---|
| Broker down during Publish | handler throws; Dejban marks processed+error | **no auto retry** — ops/manual; better: retry before mark |
| Job crash after publish before UPDATE | re-deliver; idempotent + inbox | OK-ish |
| Interceptor skipped (Forgot AddInterceptors) | no outbox rows | silent missing sync |
| Tenant SiteIds empty in outbox | background wrong filter | middleware must set on request |
| JSON too big / 2000 limit | SaveChanges fail or truncate | raise limit; compact events |
| Dual app instances FOR UPDATE | lock wait / block | SKIP LOCKED + clustered scheduler |
| Handler non-idempotent | duplicate side effects | decorator + design |

---

## Smell-ha

1. **Processed even on error** — poison swallowed from poll loop  
2. **No SKIP LOCKED** — multi-instance locking  
3. **Content MaxLength(2000)** vs jsonb rich events  
4. **8× copied** ProcessOutboxJob / IdempotentHandler (schema string)  
5. **Idempotent insert ≠ job transaction** — dual connection  
6. **Type name only** — rename class breaks old rows  
7. **DisallowConcurrentExecution** local to scheduler node  
8. **No metric/alert** built-in for backlog  
9. **Newtonsoft polymorphic** fragility  
10. **ClearDomainEvents before successful commit** — if SaveChanges fails after interceptor add, events cleared in memory — know EF interceptor + failed transaction behavior; re-Raise may be needed on retry paths  
11. **Batch in one transaction** — long lock if handlers slow (Publish inside lock!)  
12. **Publish inside FOR UPDATE transaction** — holds row locks during network I/O — **scalability smell**

### Smell #12 deep

Ideal pattern often:

1. FOR UPDATE SKIP LOCKED fetch ids  
2. process outside / shorter transactions  
3. or: process then update without holding lock across HTTP to Rabbit  

Dejban holds transaction open across `PublishAsync` — under load, lock contention on outbox table. Interview: in smell ro boland sharh bede.

---

## Debug checklist

1. Domain event Raised? breakpoint SoftDelete  
2. After SaveChanges: row in `{schema}.outbox_messages`?  
3. `SiteIds` populated?  
4. Quartz job running? logs Beginning…  
5. `processed_on_utc` still null after minutes? job/options  
6. `error` column set? read exception  
7. Handler registered in Application assembly?  
8. Decorate/idempotent skipping unexpectedly?  
9. Rabbit get message? (Day 20)  
10. Requeue test: `UPDATE … SET processed_on_utc = NULL, error = NULL WHERE id = …`

---

## 25 soal-e mosahebe

1. Dual-write chie?  
2. Transactional outbox chie?  
3. Chera same transaction?  
4. At-least-once yani chi?  
5. Chera idempotent handler?  
6. CDC vs outbox?  
7. FOR UPDATE chie?  
8. SKIP LOCKED cherā?  
9. Dejban interceptor koja run mishe?  
10. SiteIds cherā roye outbox?  
11. ProcessOutboxJob chejori dispatch?  
12. Domain vs integration event in this pipeline?  
13. Processed + error — retry?  
14. Outbox vs Inbox?  
15. Chera na publish ghabl az SaveChanges?  
16. Quartz interval tradeoff?  
17. Multi-schema outbox?  
18. Lock across Publish smell?  
19. OutboxMessage.Id = domainEvent.Id?  
20. Factory pattern for handlers?  
21. Scrutor role?  
22. MT EF Outbox vs custom?  
23. Poison message strategy?  
24. Chejori monitor backlog?  
25. SaveChanges fail after ClearDomainEvents?

---

## Senario-ha

### A) Happy path SoftDelete  
Outbox row → job → SoftDeleted publish → other modules sync.

### B) Rabbit down  
Handler throws → row processed with error → **stuck** until manual reset + broker up.

### C) Crash after publish  
Re-run → idempotent may skip handler → mark processed; consumers may see dup publish → inbox dedup.

### D) Forgot interceptor on new DbContext  
Business saves; no events ever → sync bug.

### E) Huge batch + slow publish  
Outbox locks; other jobs wait — scale smell.

---

## Mini lab

1. SoftDelete one personnel; SQL select outbox row before 5s  
2. Watch `processed_on_utc` flip  
3. Breakpoint interceptor + ProcessOutboxJob  
4. Stop Rabbit; SoftDelete; inspect `error` column  
5. Reset processed null; start Rabbit; see recovery (or not if already marked)  
6. Compare Identity MT outbox tables (preview Day 22)

---

## Resume

**short:**

> Implemented a custom transactional outbox for a modular monolith: EF Core `SaveChanges` interceptor persists domain events to per-schema `outbox_messages` in the same transaction, Quartz/Dapper workers poll with `FOR UPDATE`, restore tenant context, and dispatch idempotent domain handlers that publish integration events via MassTransit.

**bullets:**

- Eliminated dual-write between PostgreSQL and RabbitMQ by co-committing business changes and outbox rows  
- Snapshotted multi-tenant `SiteIds`/`IsSuperAdmin` onto outbox messages for reliable background dispatch  
- Built per-module `ProcessOutboxJob` with batching, ordering by `occurred_on_utc`, and handler factory resolution  
- Layered Scrutor-decorated idempotent domain handlers using `outbox_message_consumers` keys  

**skills:** `Transactional Outbox, EF Core Interceptors, Domain Events, Quartz.NET, Dapper, Idempotency, MassTransit, PostgreSQL, Modular Monolith, Reliable Messaging`

---

## File-haye mohem

| chi | koja |
|---|---|
| Interceptor | `Common/.../Outbox/InsertOutboxMessagesInterceptor.cs` |
| OutboxMessage | `.../Outbox/OutboxMessage.cs` |
| EF config | `OutboxMessageConfiguration.cs` |
| Consumer row | `OutboxMessageConsumer.cs` + Configuration |
| Handler factory | `DomainEventHandlersFactory.cs` |
| Process job | e.g. `Personnels.Infrastructure/Outbox/ProcessOutboxJob.cs` |
| Quartz config | `ConfigureProcessOutboxJob.cs` |
| Options | `OutboxOptions.cs` + `modules.personnels.json` |
| Idempotent decorator | `.../Outbox/IdempotentDomainEventHandler.cs` |
| Sample handler | `.../DeletePersonnel/PersonnelDeletedDomainEventHandler.cs` |
| EventBus | `Common/.../EventBus/EventBus.cs` |
| Entity.Raise | `Dejban.Common.Domain/Entity.cs` |
| DbContext AddInterceptors | `PersonnelsModule` / each module |

---

## Chejori digest koni

1. Dual-write ra roye kaghaz bekesh (5 min)  
2. Interceptor line-by-line (15 min)  
3. ProcessOutboxJob + SQL (20 min)  
4. SoftDelete E2E ba SQL (20 min)  
5. List smells #1 #12 boland sharh bede (10 min)  
6. 25 soal (20 min)

---

## Deep dive — ClearDomainEvents + failed SaveChanges

Interceptor `ClearDomainEvents()` **ghabl az** successful commit seda mishe (during SavingChanges).

Agar SaveChanges ba'dan fail konad (constraint, timeout):

- DB rollback → outbox INSERT ham rollback ✅
- In-memory entity: domain events **khali** shodan ❌
- Retry haman tracked entity bedune re-Raise → **outbox tekrari nist**

Amali: bazi teams Clear ra post-success mikonan; Dejban clear-before. Age retry path dari, domain method ra dobare seda bezan ya events ra preserve kon. In nuance-e interview-e.

---

## Deep dive — chand handler baraye yek event

```csharp
foreach (IDomainEventHandler domainEventHandler in handlers)
    await domainEventHandler.Handle(...);
```

Yek `PersonnelCreatedDomainEvent` mitone:

- publish `PersonnelCreated` integration
- update read model
- kick ACL sync command

Har kodom idempotent key = `(eventId, handlerTypeName)` joda.

Order = reflection order (unstable) — **depend nakon** on order; handlers independent bashan.

---

## Deep dive — Type column vs assembly rename

`Type = domainEvent.GetType().Name` — short name, na AssemblyQualifiedName.

Rename class `PersonnelDeletedDomainEvent` → `PersonnelRemovedDomainEvent`:

- old outbox rows deserialize fail
- deploy coordination: drain outbox ghabl az rename, ya versioned type map

---

## Glossary outbox

| kalame | ma'ni |
|---|---|
| Dual-write | do store bedune atomicity |
| Outbox | table-e «publish intent» |
| Poller / dispatcher | job ke outbox ra khali mikone |
| At-least-once | momken tekrari |
| Idempotent consumer | tekrari safe |
| Poison message | payam-e fail-daemi |
| Backlog | pending count / age |
| FOR UPDATE | row lock in tx |
| SKIP LOCKED | skip locked rows (multi worker) |

---

## Interview 60s

> «We avoid dual-write by writing domain events into per-schema outbox tables in the same SaveChanges transaction via an EF interceptor. Quartz jobs poll with FOR UPDATE, restore tenant context, and run Scrutor-decorated handlers that publish to Rabbit. Failures are marked with an error column rather than auto-retried — that is an ops tradeoff we know.»

---

*Day 21 tamum. Ba'd: Day 22 — MassTransit EF Outbox (amade). Fehrest: [README.md](./README.md).*
