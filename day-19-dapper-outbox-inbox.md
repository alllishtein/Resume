# Day 19 — Dapper (outbox / inbox)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Dapper** = micro-ORM: SQL ra khodet minevisi, result map mishe be object. EF Core change-tracker va LINQ dare; Dapper **control + speed** midahad baraye raw SQL — bedune tracking overhead. Chera important-e? Outbox/inbox worker-ha SQL-e hot + row lock mikhan, na graph-e domain.

To Dejban, Dapper qalb-e **outbox/inbox workers**-e: poll ba `FOR UPDATE`, update `processed_on_utc`, idempotent consumer check. Write-e outbox hanooz **EF interceptor**-e (hamoon transaction ba business data). Hybrid: EF baraye domain write, Dapper baraye messaging plumbing. Day 21 pattern ra deep mikone; inja tool + SQL.

---

# BAKHSH-E AVAL: WORLD — Dapper + Outbox/Inbox to donya

## Dapper chie?

```csharp
await using var conn = await dataSource.OpenConnectionAsync();

var users = await conn.QueryAsync<User>(
    "SELECT id, full_name AS FullName FROM users WHERE is_active = @active",
    new { active = true });

await conn.ExecuteAsync(
    "UPDATE users SET last_login = @now WHERE id = @id",
    new { id, now = DateTime.UtcNow });
```

| | EF Core | Dapper |
|---|---|---|
| SQL | LINQ → generated | **to minevisi** |
| Tracking | bale | na |
| Migrations | bale | na |
| Performance | good | usually faster (less overhead) |
| Multi-mapping | Include | splitOn / multi-map |
| Best for | domain write, complex graph | reports, jobs, hot SQL, locks |

**Micro-ORM** = map rows ↔ objects, bedune full unit-of-work stack. Vaghti miduni SQL chi bayad bashe (FOR UPDATE, EXISTS, …), Dapper natural-e.

---

## Core APIs

| API | chi |
|---|---|
| `QueryAsync<T>` / `Query<T>` | SELECT → `IEnumerable<T>` |
| `QueryFirstOrDefaultAsync` | 0–1 row |
| `QuerySingleAsync` | exactly 1 |
| `ExecuteAsync` | INSERT/UPDATE/DELETE → rows affected |
| `ExecuteScalarAsync<T>` | single value (`EXISTS`, `COUNT`) |
| `QueryMultiple` | multi-result sets (one round-trip) |
| `QueryAsync<(A,B)>` / multi-map | join → multiple types |

```csharp
bool exists = await conn.ExecuteScalarAsync<bool>(
    "SELECT EXISTS(SELECT 1 FROM outbox_consumers WHERE id = @Id)",
    new { Id = messageId });
```

---

## Parameterization (SQL injection)

Hamishe parameterized — string concat = hole:

```csharp
// ✅ parameterized
await conn.QueryAsync("SELECT * FROM t WHERE id = @Id", new { Id = id });

// ❌ string concat
await conn.QueryAsync($"SELECT * FROM t WHERE id = '{id}'");
```

Dapper anonymous object / DTO → named params. Postgres: `@Id` style via Npgsql.

---

## Mapping tricks

```csharp
// snake_case columns → PascalCase props
DefaultTypeMap.MatchNamesWithUnderscores = true;

// alias in SQL
"SELECT full_name AS FullName FROM ..."

// custom type handler (uuid[], arrays)
SqlMapper.AddTypeHandler(new GuidListHandler());
```

Dejban `MatchNamesWithUnderscores` ra to `AddApplication` set mikone — vase hamin snake_case Postgres ba PascalCase C# match mishe.

---

## Transaction + row locking

Worker-ha bayad row ra lock konan ta do instance yek message ra do-bar process nakonan:

```csharp
await using var tx = await conn.BeginTransactionAsync();

var rows = await conn.QueryAsync<Msg>(
    """
    SELECT id, content FROM outbox_messages
    WHERE processed_on_utc IS NULL
    ORDER BY occurred_on_utc
    LIMIT 50
    FOR UPDATE
    """,
    transaction: tx);

// process...
await conn.ExecuteAsync("UPDATE ... SET processed_on_utc = @now WHERE id = @Id",
    param, transaction: tx);

await tx.CommitAsync();
```

| lock | behavior |
|---|---|
| `FOR UPDATE` | lock rows; other tx **wait** |
| `FOR UPDATE SKIP LOCKED` | skip locked → parallel workers ✅ scale |
| `FOR UPDATE NOWAIT` | fail immediately if locked |

**World best practice for multi-instance workers:** `SKIP LOCKED`. Dejban alan faghat `FOR UPDATE` (+ Quartz single execution) — scale smell.

---

## Transactional Outbox (pattern)

```
Same DB transaction:
  1. Save business entity
  2. Insert outbox row (event payload)

Later worker:
  3. Poll unprocessed outbox
  4. Publish / handle
  5. Mark processed
```

**Chera?** Age publish ghabl az commit bashe va crash kone → event lost ya phantom. Outbox = at-least-once + durable. Dual-write problem ra Day 21 deep mikone.

## Inbox (pattern)

```
Bus delivers message
  → INSERT inbox (idempotent ON CONFLICT)
  → Worker processes inbox
  → Mark processed + record consumer (idempotent per handler)
```

**Chera?** At-least-once delivery → duplicate. Inbox + consumer table = process-once per handler.

---

## Idempotency

```
Handler name + message id → consumer table
EXISTS? → skip
ELSE → handle → INSERT consumer
```

Decorator pattern (Scrutor) around real handler — Day 23/24.

---

## Dapper vs alternatives

| tool | note |
|---|---|
| Dapper | king of micro-ORM in .NET |
| Dapper.Contrib | CRUD attributes |
| SqlKata | query builder → SQL |
| EF `FromSql` / `SqlQuery` | raw SQL inside EF |
| ADO.NET | zero abstraction |

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **`SKIP LOCKED`** — Dejban faghat `FOR UPDATE` (+ Quartz single execution)
- **Dapper.Contrib / QueryMultiple** — nist
- **Stored procedures** via Dapper — nist
- **Retry failed outbox** (`processed_on_utc` set even on error) — failed = stuck unless manual
- **Outbox write via Dapper** — Dejban write = EF interceptor
- **MassTransit EF Outbox** (standalone services) — pattern digar (Day 39)

---

# BAKHSH-E DOVOM: DEJBAN — Dapper to outbox/inbox

Hybrid architecture-e Dejban: EF baraye domain + interceptor write to outbox; Dapper baraye poll/process/idempotency. 8 module hamin pattern — faghat schema name fargh mikone. Avval version/setup, ba'd flow.

## Version & setup

```xml
<!-- Directory.Packages.props -->
Dapper 2.1.66
```

```csharp
// ApplicationConfiguration.cs
Dapper.DefaultTypeMap.MatchNamesWithUnderscores = true;

// InfrastructureConfiguration.cs
NpgsqlDataSource npgsqlDataSource = new NpgsqlDataSourceBuilder(cs).Build();
services.TryAddSingleton(npgsqlDataSource);
services.TryAddScoped<IDbConnectionFactory, DbConnectionFactory>();

SqlMapper.AddTypeHandler(new GenericArrayHandler<string>());
SqlMapper.AddTypeHandler(new GuidListHandler()); // List<Guid> ↔ uuid[]
```

```csharp
// IDbConnectionFactory + DbConnectionFactory
public interface IDbConnectionFactory
{
    ValueTask<DbConnection> OpenConnectionAsync();
}

internal sealed class DbConnectionFactory(NpgsqlDataSource dataSource) : IDbConnectionFactory
{
    public async ValueTask<DbConnection> OpenConnectionAsync()
        => await dataSource.OpenConnectionAsync();
}
```

---

## Hybrid architecture

```
Command handler
  → entity.Raise(domainEvent)
  → EF SaveChanges
      → InsertOutboxMessagesInterceptor  ← EF write to outbox_messages
  → Quartz ProcessOutboxJob             ← Dapper poll + FOR UPDATE
      → DomainEventHandler (may publish integration event)
          → IdempotentDomainEventHandler ← Dapper EXISTS/INSERT consumers

MassTransit consumer
  → IntegrationEventConsumer            ← Dapper INSERT inbox ON CONFLICT DO NOTHING
  → Quartz ProcessInboxJob              ← Dapper poll + FOR UPDATE
      → IntegrationEventHandler
          → IdempotentIntegrationEventHandler ← Dapper consumers
```

**8 modules** hamin pattern: Visitors, Personnels, Vehicles, Armory, Inventory, CashLogistics, WeighBridge, SecurityPatrols — faghat schema name fargh mikone (`visitors.*`, `personnels.*`, …).

---

## Table shape

| table | role |
|---|---|
| `{schema}.outbox_messages` | domain events waiting to process |
| `{schema}.outbox_message_consumers` | (message_id, handler_name) idempotency |
| `{schema}.inbox_messages` | integration events waiting |
| `{schema}.inbox_message_consumers` | same for inbox handlers |

Columns (messages):

```
id uuid PK
type text
content jsonb
site_ids uuid[]
is_super_admin boolean
occurred_on_utc timestamptz
processed_on_utc timestamptz NULL
error text NULL
```

Config example: BatchSize **50**, Interval **5 seconds** (`modules.visitors.json` Outbox/Inbox options).

---

## ProcessOutboxJob (Visitors)

```csharp
// File: Visitors.Infrastructure/Outbox/ProcessOutboxJob.cs

[DisallowConcurrentExecution]
internal sealed class ProcessOutboxJob(...) : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        await using DbConnection connection = await dbConnectionFactory.OpenConnectionAsync();
        await using DbTransaction transaction = await connection.BeginTransactionAsync();

        var messages = await GetOutboxMessagesAsync(connection, transaction);

        foreach (var outboxMessage in messages)
        {
            Exception? exception = null;
            try
            {
                var domainEvent = JsonConvert.DeserializeObject<IDomainEvent>(
                    outboxMessage.Content, SerializerSettings.Instance)!;

                using var scope = serviceScopeFactory.CreateScope();
                TenantContextAccessor.SetContext(
                    [.. outboxMessage.SiteIds], outboxMessage.IsSuperAdmin);

                var handlers = DomainEventHandlersFactory.GetHandlers(
                    domainEvent.GetType(), scope.ServiceProvider,
                    Application.AssemblyReference.Assembly);

                foreach (var handler in handlers)
                    await handler.Handle(domainEvent, context.CancellationToken);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "... {MessageId}", outboxMessage.Id);
                exception = ex;
            }

            await UpdateOutboxMessageAsync(connection, transaction, outboxMessage, exception);
        }

        await transaction.CommitAsync();
    }

    private async Task<IReadOnlyList<OutboxMessageResponse>> GetOutboxMessagesAsync(...)
    {
        string sql =
            $"""
             SELECT id AS Id, content AS Content,
                    site_ids AS SiteIds, is_super_admin AS IsSuperAdmin
             FROM visitors.outbox_messages
             WHERE processed_on_utc IS NULL
             ORDER BY occurred_on_utc
             LIMIT {outboxOptions.Value.BatchSize}
             FOR UPDATE
             """;

        return (await connection.QueryAsync<OutboxMessageResponse>(sql, transaction: transaction))
            .ToList();
    }

    private async Task UpdateOutboxMessageAsync(..., Exception? exception)
    {
        const string sql =
            """
            UPDATE visitors.outbox_messages
            SET processed_on_utc = @ProcessedOnUtc, error = @Error
            WHERE id = @Id
            """;

        await connection.ExecuteAsync(sql, new
        {
            outboxMessage.Id,
            ProcessedOnUtc = dateTimeProvider.UtcNow,
            Error = exception?.ToString()
        }, transaction);
    }
}
```

### Points

1. **Dapper `QueryAsync` + `ExecuteAsync`** — na EF
2. **`FOR UPDATE`** — lock rows for this transaction
3. **`[DisallowConcurrentExecution]`** — yek instance job to yek scheduler
4. **Tenant restored** from message `site_ids` / `is_super_admin`
5. **Error path:** `processed_on_utc` **set** + `error` filled → **auto-retry nist**

---

## ProcessInboxJob

Hamoon structure; table = `visitors.inbox_messages`; deserialize `IIntegrationEvent`; handlers from **Presentation** assembly.

```sql
FROM visitors.inbox_messages
WHERE processed_on_utc IS NULL
ORDER BY occurred_on_utc
LIMIT {BatchSize}
FOR UPDATE
```

---

## IntegrationEventConsumer — Dapper insert

```csharp
// File: Visitors.Infrastructure/Inbox/IntegrationEventConsumer.cs

const string sql =
    """
    INSERT INTO visitors.inbox_messages(id, type, content, site_ids, is_super_admin, occurred_on_utc)
    VALUES (@Id, @Type, @Content::json, @SiteIds, @IsSuperAdmin, @OccurredOnUtc)
    ON CONFLICT (id) DO NOTHING
    """;

await connection.ExecuteAsync(sql, inboxMessage);
```

- MassTransit deliver → **persist only**
- Process async by Quartz
- `ON CONFLICT DO NOTHING` → duplicate bus delivery safe
- `@Content::json` / jsonb + `GuidListHandler` for `site_ids`

---

## Idempotent handlers (Dapper EXISTS)

```csharp
// IdempotentDomainEventHandler

if (await OutboxConsumerExistsAsync(connection, consumer))
    return;  // already handled by this handler type

await decorated.Handle(domainEvent, ct);
await InsertOutboxConsumerAsync(connection, consumer);

// SQL:
SELECT EXISTS(
  SELECT 1 FROM visitors.outbox_message_consumers
  WHERE outbox_message_id = @OutboxMessageId AND name = @Name);

INSERT INTO visitors.outbox_message_consumers(outbox_message_id, name)
VALUES (@OutboxMessageId, @Name);
```

Inbox twin: `inbox_message_consumers` + `IdempotentIntegrationEventHandler`.

Wired ba Scrutor `Decorate` (Day 41).

---

## Chera Dapper inja (na EF)?

| need | Dapper fit |
|---|---|
| `FOR UPDATE` in explicit tx | natural ADO/Dapper |
| No change tracker overhead | poll every 5s |
| Schema-qualified SQL | clear `visitors.outbox_messages` |
| Map to tiny records | `OutboxMessageResponse` |
| `EXISTS` scalar | `ExecuteScalarAsync<bool>` |

EF still owns:
- Domain SaveChanges
- Outbox **insert** (interceptor)
- Card number / ACL user id sequences (Serializable EF tx)

---

## Other Dapper usage

**PatrolReportService** (SecurityPatrols): cross-schema blacklist queries

```sql
-- visitors.black_list_history / personnels.black_list_history
connection.QueryAsync<VisitorBlackListDto>(...)
```

Rare escape hatch when module DbContext shouldn't join foreign schema.

---

## Error / retry reality

| case | behavior |
|---|---|
| Handler throws | log + `error` column + **mark processed** |
| Next poll | row **skipped** (`processed_on_utc IS NOT NULL`) |
| Manual fix | clear `processed_on_utc` / re-insert / admin tool |
| Bus duplicate | inbox `ON CONFLICT DO NOTHING` |
| Handler re-run same message | consumer EXISTS → skip |

**Smell:** poison message silent after one failure. World often: retry count, dead-letter, exponential backoff.

---

## Concurrency smell (scale)

```
Instance A: FOR UPDATE rows 1..50
Instance B: waits on same rows  (na SKIP LOCKED)
+ Quartz DisallowConcurrentExecution → usually 1 runner per process
```

Multi-node Dejban.Api bedune `SKIP LOCKED` → serialize / block. Day 06/07 ham goftim.

**Fix World:**  

```sql
FOR UPDATE SKIP LOCKED
```

---

## Contrast: MassTransit EF Outbox (standalone)

Identity / ACL / RequestTracker: MassTransit `AddEntityFrameworkOutbox` — tables `OutboxMessage` / `InboxState` managed by MassTransit. **Dapper jobs nist.** Dejban modules = custom Dapper workers.

---

## Smell-ha

1. **No SKIP LOCKED** — multi-instance blocking
2. **Failed = processed** — no automatic retry
3. **Hardcoded schema in SQL strings** — 8 copy-paste jobs (`visitors.` vs `personnels.`)
4. **Json.NET deserialize** — polymorphism settings critical
5. **Long transaction** — lock held while handlers run (HTTP/DB inside handlers!)
6. **Dual connection stacks** — EF pool + NpgsqlDataSource
7. **No QueryMultiple / Contrib** — fine, but limited toolkit
8. **error column unbounded text** — exception.ToString() can be huge
9. **BatchSize in SQL string interpolation** — ok as int from options, not user input; still style smell vs parameter
10. **Inbox consumer insert after handle** — crash between handle & insert → re-run (idempotent handler must be truly safe)

---

## 20 soal-e mosahebe

1. **Dapper chie?** — Micro-ORM; you write SQL; maps results
2. **EF vs Dapper?** — EF tracking/LINQ/migrations; Dapper raw/fast/control
3. **Outbox pattern?** — Persist event with business data same tx; publish later
4. **Inbox pattern?** — Persist incoming message; process async; idempotent
5. **FOR UPDATE?** — Lock selected rows until tx ends
6. **SKIP LOCKED?** — Parallel workers skip locked rows
7. **Chera Dejban Dapper for jobs?** — Locks + lightweight poll
8. **Outbox write kejast?** — EF SaveChanges interceptor
9. **ON CONFLICT DO NOTHING?** — Idempotent inbox insert
10. **Idempotent consumer table?** — (messageId, handlerName) processed once
11. **MatchNamesWithUnderscores?** — snake_case → PascalCase
12. **TypeHandler?** — Custom map (uuid[] ↔ List&lt;Guid&gt;)
13. **DisallowConcurrentExecution?** — One Quartz job run at a time
14. **Failed message retry?** — Dejban marks processed — usually no auto-retry
15. **At-least-once vs exactly-once?** — Bus at-least-once; exactly-once via inbox+consumers
16. **SQL injection?** — Always parameterized `@Id`
17. **QueryAsync vs ExecuteAsync?** — Query returns rows; Execute mutates
18. **ExecuteScalarAsync?** — Single value (EXISTS, COUNT)
19. **Long lock smell?** — Don't call slow external I/O while holding FOR UPDATE
20. **Hybrid persistence?** — EF domain + Dapper infrastructure messaging

---

## Deep dive — Dapper multi-mapping (WORLD)

Gahi yek SELECT chand table join mikone va mikhai **object graph** besazi bedune EF Include:

```csharp
// splitOn = first column that belongs to type B (usually PK of second table)
var sql = """
    SELECT o.id, o.content, c.id, c.name
    FROM orders o
    JOIN customers c ON c.id = o.customer_id
    WHERE o.id = @OrderId
    """;

await conn.QueryAsync<Order, Customer, Order>(
    sql,
    (order, customer) =>
    {
        order.Customer = customer;
        return order;
    },
    new { OrderId = id },
    splitOn: "id"); // second "id" column starts Customer
```

| pattern | when |
|---|---|
| `(A,B)` tuple | flat join, 2 types, no nesting |
| `QueryAsync<A,B,C,...>` + splitOn | 1-to-1 or many-to-1 join |
| `QueryMultiple` | 2+ result sets, e.g. header + lines |
| manual map | weird shapes, aggregates |

**Dejban outbox/inbox:** faghat **yek table** → `QueryAsync<OutboxMessageResponse>` kafi. Multi-map to `PatrolReportService` ya report-ha momken — na to job-ha.

**Smell:** splitOn ghalat → silent wrong mapping (Customer null). Test ba known row.

---

## Deep dive — `Query` sync vs async + connection lifetime

```csharp
// ✅ job/worker pattern (Dejban)
await using DbConnection connection = await dbConnectionFactory.OpenConnectionAsync();
await using DbTransaction transaction = await connection.BeginTransactionAsync();
// ... QueryAsync / ExecuteAsync with transaction: transaction
await transaction.CommitAsync();
// connection disposed → back to NpgsqlDataSource pool
```

| rule | chi |
|---|---|
| `OpenConnectionAsync` per job run | connection short-lived |
| `NpgsqlDataSource` singleton | pool shared across app |
| pass `transaction:` to Dapper | same tx as FOR UPDATE |
| `await using` | return connection to pool |

**Anti-pattern:** static `IDbConnection` singleton — thread-safety + stale state.

**EF vs Dapper same DB:** do pool path (EF internal + DataSource) — monitor `Max Pool Size` age traffic spike.

---

## Deep dive — Outbox write (EF) vs read/process (Dapper)

```csharp
// InsertOutboxMessagesInterceptor — EF ChangeTracker, na Dapper
var tenantInfo = TenantContextAccessor.Current;

var outboxMessages = context.ChangeTracker.Entries<Entity>()
    .SelectMany(e => { e.Entity.ClearDomainEvents(); return domainEvents; })
    .Select(domainEvent => new OutboxMessage
    {
        Id = domainEvent.Id,
        Content = JsonConvert.SerializeObject(domainEvent, SerializerSettings.Instance),
        SiteIds = [.. tenantInfo?.SiteIds ?? []],
        IsSuperAdmin = tenantInfo?.IsSuperAdmin ?? false,
        ...
    });

context.Set<OutboxMessage>().AddRange(outboxMessages);
```

**Chera inja EF?**
- Domain event-ha **haman SaveChanges** ke aggregate update shode insert mishan → **same transaction** automatic
- Dapper INSERT joda = risk dual-write / partial commit

**Worker side:** EF change tracker overhead bi-fayde — faghat read JSON + dispatch handler.

---

## Deep dive — Tenant restore to background (Day 16 link)

```
HTTP request → TenantContextMiddleware → AsyncLocal
  → SaveChanges → outbox row stores site_ids + is_super_admin snapshot

ProcessOutboxJob:
  TenantContextAccessor.SetContext(outboxMessage.SiteIds, outboxMessage.IsSuperAdmin)
  → handler EF queries get TenantFilter again
```

**IntegrationEventConsumer** ham snapshot az `TenantContextAccessor.Current` (MassTransit consume filter publish kard) → inbox row.

**Leak scenario:** consumer bedune filter + empty SiteIds → handler ba tenant khali → filter hame chiz ra filter mikone ya SuperAdmin false → **0 row updated**. Test: inbox row SiteIds non-empty ba'd az cross-module event.

---

## Deep dive — Idempotent decorator + connection per handler

Idempotent handlers (`IdempotentDomainEventHandler`) typically:
1. `OpenConnectionAsync` (ya connection az outer scope)
2. `ExecuteScalarAsync<bool>` EXISTS on `{schema}.outbox_message_consumers`
3. age true → return (skip)
4. `await decorated.Handle(...)`
5. `INSERT` consumer row

**Race:** do worker parallel (bedune SKIP LOCKED ya do handler instance) — unique index roye `(outbox_message_id, name)` **last line** (age migration/server dare).

**Crash between 4 and 5:** at-least-once → handler dobare run → business side bayad idempotent ya EXISTS save.

---

## Deep dive — Json.NET polymorphism to outbox

`SerializerSettings.Instance` + `IDomainEvent` deserialize:
- `$type` ya custom resolver lazem — agar settings avaz she, worker **fail** → `error` column + processed (no retry)

**Interview:** «chejori version event payload?» — backward-compatible fields, new event types, na rename-e breaking bedune migration data.

---

## Deep dive — Quartz wiring (ConfigureProcessOutboxJob)

Har module:
- `services.ConfigureOptions<ConfigureProcessOutboxJob>()`
- Quartz job identity = `typeof(ProcessOutboxJob).FullName`
- Trigger interval az `OutboxOptions` (modules JSON)

`[DisallowConcurrentExecution]` = **yek thread** in job type per scheduler — vali **chand Dejban.Api instance** = chand scheduler = hanooz FOR UPDATE block (unless SKIP LOCKED).

---

## EF raw SQL escape hatch (contrast)

```csharp
// EF Core 8+
await db.Database.SqlQuery<OutboxMessageResponse>(sql).ToListAsync();
```

Dejban **nemire** in masir baraye jobs — Dapper explicit, module-agnostic factory. EF `FromSqlRaw` ba entity tracked = mix smell.

---

## Decision tree — Dapper ya EF?

```
Need change tracker / domain graph?
  YES → EF
Need FOR UPDATE batch job?
  YES → Dapper (or EF + raw SQL — heavier)
Cross-schema report, read-only, hot path?
  → Dapper OK (PatrolReportService)
Outbox insert same tx as aggregate?
  → EF interceptor (Dejban)
```

---

## Chejori in fasl ra «digested» koni (lab — ~45 min)

1. **SQL log:** yek create personnel → `personnels.outbox_messages` row ba `processed_on_utc NULL` (5 min)
2. **Wait 5s** → row processed; `content` JSON ra baz kon — type name domain event (5 min)
3. Breakpoint `ProcessOutboxJob.Execute` — SiteIds restore (10 min)
4. RabbitMQ management UI — queue `personnel-created` message count ba publish (5 min)
5. Duplicate delivery simulate — inbox `ON CONFLICT` → still 1 row (5 min)
6. **Thought experiment:** SQL `FOR UPDATE SKIP LOCKED` — 2 worker che row migirin? (5 min)
7. 20 soal bala + 5 zir ra boland javab bede (10 min)

**Optional SQL playground (local DB):**

```sql
BEGIN;
SELECT id FROM visitors.outbox_messages
WHERE processed_on_utc IS NULL
ORDER BY occurred_on_utc LIMIT 5
FOR UPDATE;
-- session 2: same query → blocks (no SKIP LOCKED)
ROLLBACK;
```

---

## 5 soal-e ezafe (bonus)

21. **Chera LIMIT to SQL string interpolate shode?** — int from options, na user input; parameter ham behtar baraye plan cache
22. **NpgsqlDataSource vs `new NpgsqlConnection`?** — pooling + central config
23. **Inbox vs outbox consumer table?** — same idempotency idea, joda schema/table baraye domain vs integration handlers
24. **Handler publish integration event toinside outbox job?** — chain: domain handler → `IEventBus` → Rabbit → inbox; outbox row still marks processed even if bus down? (depends handler — bus publish failure → exception → error column)
25. **GuidListHandler chi kar mikone?** — map Postgres `uuid[]` ↔ `List<Guid>` for Dapper params/results

---

## Resume

**short:**

> Implemented transactional outbox/inbox processing with Dapper 2.1 on PostgreSQL: schema-qualified SQL, `FOR UPDATE` batch polling, Quartz workers, and idempotent consumer tables — while EF Core remains responsible for domain persistence and outbox inserts via SaveChanges interceptor.

**bullets:**

- Built `ProcessOutboxJob` / `ProcessInboxJob` using Dapper `QueryAsync`/`ExecuteAsync` with transactional `FOR UPDATE` batching (size 50, interval 5s)
- Inserted inbox rows from MassTransit consumers via Dapper `INSERT ... ON CONFLICT DO NOTHING`
- Enforced handler idempotency with Dapper `EXISTS` + consumer table inserts, wrapped by Scrutor decorators
- Configured `NpgsqlDataSource`, underscore name matching, and `uuid[]` type handlers for `site_ids`

**skills:** `Dapper, Micro-ORM, Transactional Outbox, Inbox Pattern, PostgreSQL FOR UPDATE, Idempotency, Quartz, Raw SQL, Npgsql`

---

## File-haye mohem

| chi | koja |
|---|---|
| Dapper version | `Directory.Packages.props` |
| Underscore mapping | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| IDbConnectionFactory | `Dejban.Common.Application/Data/IDbConnectionFactory.cs` |
| DbConnectionFactory | `Dejban.Common.Infrastructure/Data/DbConnectionFactory.cs` |
| GuidListHandler | `Dejban.Common.Infrastructure/Data/GuidListHandler.cs` |
| ProcessOutboxJob | `Visitors.Infrastructure/Outbox/ProcessOutboxJob.cs` |
| ProcessInboxJob | `Visitors.Infrastructure/Inbox/ProcessInboxJob.cs` |
| IntegrationEventConsumer | `Visitors.Infrastructure/Inbox/IntegrationEventConsumer.cs` |
| Idempotent domain | `Visitors.Infrastructure/Outbox/IdempotentDomainEventHandler.cs` |
| Idempotent integration | `Visitors.Infrastructure/Inbox/IdempotentIntegrationEventHandler.cs` |
| Outbox EF write | `Dejban.Common.Infrastructure/Outbox/InsertOutboxMessagesInterceptor.cs` |
| OutboxMessage config | `Visitors.Infrastructure/Outbox/OutboxMessageConfiguration.cs` |
| Other Dapper | `SecurityPatrols.../PatrolReportService.cs` |

---

*Day 19 tamum. Ba'd: Day 20 — MassTransit + RabbitMQ (amade). Fehrest: [README.md](./README.md).*

