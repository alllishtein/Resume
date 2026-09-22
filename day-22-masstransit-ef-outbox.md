# Day 22 — MassTransit EF Outbox

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**MassTransit Entity Framework Outbox** = transactional outbox/inbox **built into MassTransit**, backed by EF Core tables (`OutboxMessage`, `OutboxState`, `InboxState`). Standalone services (Identity, ACL, RequestTracker, DCC, Gate, Reporting) in: `AddEntityFrameworkOutbox` + `UsePostgres` + `UseBusOutbox`, va roye consumer endpoints `UseEntityFrameworkOutbox`.

Pattern-e developer: `IPublishEndpoint.Publish(...)` **ba'd** (ya ghabl az) business changes, **`SaveChangesAsync` yekja** — message ba DB commit atomic. Delivery be Rabbit = MassTransit **Bus Outbox** worker (na Quartz custom Day 21). Dejban modular monolith **in style ra estefade nemikone** — custom interceptor + Quartz. In fasl = style-e microservice-ha + comparison. Goal yeksan ba Day 21: dual-write nabashe; implementation digar.

---

# BAKHSH-E AVAL: WORLD — MassTransit EF Outbox to donya

## Yadbari — transactional outbox (Day 21)

Goal yeksan: **dual-write** DB + broker ra hazf kon. Farq = **che kasi** outbox table ra minevise/mikhoone:

| | Custom (Day 21) | MT EF Outbox (Day 22) |
|---|---|---|
| Write API | Domain `Raise` + EF interceptor | `IPublishEndpoint.Publish` |
| Tables | app `outbox_messages` | MT `OutboxMessage` / `OutboxState` |
| Delivery | Quartz + Dapper | Bus Outbox hosted service |
| Inbox | app `inbox_messages` | MT `InboxState` |
| Consumer glue | bridge + ProcessInboxJob | `UseEntityFrameworkOutbox` on endpoint |

Yani chi? Modular = domain-event-first + multi-schema. Microservice = MT-first + yek DbContext.

---

## MassTransit Outbox — do mode

### 1) Bus Outbox (producer)

```
handler:
  db.Add(entity)
  await publishEndpoint.Publish(new SomethingHappened(...))
  await db.SaveChangesAsync()
```

Ba `UseBusOutbox()`:

- `Publish` **mostaghim** be Rabbit **nemire**
- Message to EF `OutboxMessage` (linked to outbox transaction / `OutboxState`)
- `SaveChanges` = business + outbox **yek transaction**
- Background **Bus Outbox** delivery → RabbitMQ

### 2) Consumer Outbox / Inbox (consumer)

```
cfg.UseEntityFrameworkOutbox<ApplicationDbContext>(context);
```

Consume:

- Message receive → inbox lock (`InboxState`)
- Consumer logic + optional further `Publish` → same DbContext transaction
- Ack after successful SaveChanges
- Duplicate delivery → inbox sees already consumed → skip

In = MassTransit’s transactional consume + outbox for cascading publishes. Chera khube? Consume + SaveChanges + cascade Publish atomic mimunan.

---

## Tables (MassTransit EF integration)

| table | role |
|---|---|
| **OutboxMessage** | serialized bus messages waiting to send |
| **OutboxState** | delivery lock / sequence for bus outbox |
| **InboxState** | consumer idempotency / in-progress consume |

Names default PascalCase tables (Identity/ACL migrations show `OutboxMessage`, `InboxState`, `OutboxState`) — often **public** schema of that service DB, na per-module schema.

Relationships: OutboxMessage can link to OutboxState or InboxState (consume-time publishes). Version upgrade-e MT = migration drift risk — yadet bashe.

---

## Chera `UseBusOutbox`?

Bedune Bus Outbox, `Publish` synchronous to broker **mid-request** — dual-write risk if you SaveChanges separately.

Ba Bus Outbox:

```
Publish → staged in DbContext
SaveChanges → commit staged messages
Delivery service → broker
```

Developer experience: **looks like** normal `Publish`, **behaves like** outbox. Interview: «Publish is intercepted/staged.»

---

## Publish order — ghabl ya ba'd az Add?

Common MassTransit sample:

```csharp
await _publishEndpoint.Publish(new OrderSubmitted(order.Id));
await _db.SaveChangesAsync();
```

Ya:

```csharp
_db.Orders.Add(order);
await _publishEndpoint.Publish(...);
await _db.SaveChangesAsync();
```

Mohem: **yek** `SaveChanges` ke outbox + entities ra commit konad. Publish ghabl az SaveChanges OK chon staging; Publish **ba'd az** SaveChanges bedune active outbox transaction = often **immediate** broker send (dual-write again!) — follow MT docs for your version: keep Publish inside same unit of work **before** final SaveChanges when using Bus Outbox.

Dejban Identity `CreateSite`: Publish **before** SaveChanges ✅.

---

## Inbox / exactly-once consume (approx)

At-least-once from Rabbit + InboxState:

1. First delivery: insert inbox, run consumer, save, mark complete
2. Redelivery: inbox hit → MassTransit short-circuits

Consumer still should be **logically idempotent** (Identity PersonnelCreated checks `existingUser != null`). Transport idempotency ≠ business idempotency — hardo lazem-an.

---

## Query endpoints exception

RPC / request-response endpoints (`get-user-site-claims`, `get-aclservice-endpoints`) often **skip** `UseEntityFrameworkOutbox`:

```csharp
x.AddRabbitMqConfigureEndpointsCallback((context, name, cfg) =>
{
    if (name.Equals("get-user-site-claims", ...)) return;
    cfg.UseEntityFrameworkOutbox<ApplicationDbContext>(context);
});
```

Chera? Request/response latency + transactional outbox overhead; often read-only, no cascading publish. Blindly outbox zadan roye RPC = slow path bedune maziat.

---

## Pros / cons vs custom Quartz outbox

| | MT EF Outbox | Custom Day 21 |
|---|---|---|
| Code volume | kam (library) | bishtar (interceptor, jobs, SQL) |
| Domain events first-class | optional | baked in Raise→interceptor |
| Multi-schema modular | awkward (one DbContext outbox) | natural per schema |
| Delivery tuning | MT options | Quartz Interval/BatchSize |
| Learning curve | MT-specific | your code, your bugs |
| Inbox unified | yes with consumer outbox | separate inbox jobs |
| Lock across publish | MT manages delivery | Dejban held FOR UPDATE during Publish (smell) |

**Dejban.Api modular:** custom fit. **Identity/ACL microservices:** MT EF Outbox fit.

---

## Bus Outbox delivery internals (conceptual)

1. After commit, `OutboxState` row represents a delivery lock
2. Hosted service queries pending `OutboxMessage`
3. Sends to Rabbit via MassTransit transport
4. Removes/marks delivered
5. Competing app instances coordinated via DB locks on OutboxState

Shabih-e Quartz poll, vali **MassTransit-owned**. Contrast Day 21: failed handler often **marks processed + error** → no auto retry. MT delivery/retry generally **better defaults** for broker publish.

---

## Failure modes

| failure | behavior |
|---|---|
| SaveChanges fails | outbox + business rollback — no ghost message |
| Broker down after commit | messages stay in OutboxMessage — delivery retries |
| Consumer crashes mid-handler | inbox incomplete → redelivery |
| Consumer succeeds, ack lost | inbox prevents double side-effect (usually) |
| Poison consumer | MT retry → error queue (`_error`) |

Yani broker down ba'd az commit = **nadari lose**; faghat delay. In farq-e bozorg ba Day 21 poison style-e.

---

## CDC still alternative

Debezium on `OutboxMessage` table possible — rare when MT Bus Outbox already polls. Don’t stack both casually.

---

# BAKHSH-E DOVOM: DEJBAN — MT EF Outbox to standalone services

## Koja active-e?

| service | MT EF Outbox |
|---|---|
| **IdentityServer** | yes |
| **ACLServer** | yes |
| **RequestTracker** | yes |
| **DCC** | yes |
| **GateServer** | yes |
| **Reporting** | yes |
| **Dejban.Api modules** | **no** — custom Day 21 |

Program.cs logging filters often **exclude** `OutboxState` / `InboxState` / `OutboxMessage` SQL noise (GateServer, Dejban.Api similarly for custom names). Delivery polls chatty — filtered in prod logs. Don’t filter **errors**.

---

## Registration template (Identity)

```csharp
// IdentityServer/.../ServiceCollectionExtensions.cs → AddMassTransit
services.AddMassTransit(x =>
{
    x.DisableUsageTelemetry();

    x.AddEntityFrameworkOutbox<ApplicationDbContext>(o =>
    {
        o.UsePostgres();
        o.UseBusOutbox();
    });

    x.SetKebabCaseEndpointNameFormatter();

    x.AddConsumer<GetUserSiteClaimsConsumer>(); // RPC — no InstanceId special
    x.AddConsumer<PersonnelCreatedConsumer>()
        .Endpoint(e => e.InstanceId = "IdentityServer");
    // PersonnelUpdated / Deleted similarly

    x.AddRabbitMqConfigureEndpointsCallback((context, name, cfg) =>
    {
        if (name.Equals("get-user-site-claims", StringComparison.OrdinalIgnoreCase))
            return; // skip EF outbox on RPC endpoint

        cfg.UseEntityFrameworkOutbox<ApplicationDbContext>(context);
    });

    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.UseTenantContextFilters(context);
        cfg.UseMessageRetry(r => r.Exponential(...));
        cfg.UseCircuitBreaker(cb => { ... });
        cfg.ConfigureEndpoints(context);
    });
});
```

**ACL** hamin template + bishtar consumers (Site/Unit/Visitor/Vehicle/Door/VisitSchedule/Relay/…) + skip `get-aclservice-endpoints`.

---

## DbContext — MT entities

```csharp
// IdentityServer ApplicationDbContext.OnModelCreating
modelBuilder.AddInboxStateEntity();
modelBuilder.AddOutboxStateEntity();
modelBuilder.AddOutboxMessageEntity();

modelBuilder.ApplyTenantQueryFilters(this);
modelBuilder.ApplySoftDeleteQueryFilters();
```

Migrations include these three MassTransit entity types (Designer files show full schema). **Commit migrations on server process** for Identity still follows team rules for that service — different from Dejban module «no migration in repo» emphasis, but know tables exist.

---

## Producer example — CreateSite

```csharp
// IdentityServer CreateSiteCommandHandler
_context.Sites.Add(site);

await _publishEndpoint.Publish(new SiteCreated(
    site.Id,
    site.IsMainSite,
    site.IsContractor,
    site.Name,
    site.Description,
    site.ParentSiteId));

// maybe more DB work (super admin grant)...

await _context.SaveChangesAsync();
```

**Flow:**

1. `Publish` → MassTransit Bus Outbox stages `OutboxMessage` on `ApplicationDbContext`
2. `SaveChanges` → `INSERT sites` + outbox rows **one commit**
3. Bus Outbox service → Rabbit `SiteCreated`
4. Dejban modules / ACL consumers receive (their own inbox/outbox style)

No `Raise(domainEvent)`, no custom interceptor, no Quartz for this publish path. Developer API almost identical to «just Publish» — **behavior** changes.

---

## Consumer example — PersonnelCreated → Identity user

```csharp
class PersonnelCreatedConsumer(
    IOptions<IdentitySettings> identityOptions,
    ApplicationDbContext dbContext,
    IPasswordHasher<ApplicationUser> passwordHasher)
    : IConsumer<PersonnelCreated>
{
    public async Task Consume(ConsumeContext<PersonnelCreated> context)
    {
        var site = await dbContext.Sites.SingleOrDefaultAsync(x => x.Id == context.Message.SiteId);
        if (site == null) return;

        var existingUser = await dbContext.Users
            .SingleOrDefaultAsync(x => x.Id == context.Message.PersonnelId.ToString());
        if (existingUser != null) return; // logical idempotency

        // create ApplicationUser + UserRole...
        await dbContext.SaveChangesAsync();
    }
}
```

Endpoint has `UseEntityFrameworkOutbox` → consume transactional with `InboxState`. Duplicate `PersonnelCreated` → inbox / early return.

**Producer of PersonnelCreated:** usually Dejban Personnels custom outbox → `IEventBus.Publish` — cross-style bridge! Message on Rabbit is the **contract**; outbox implementation per service can differ. Interview gold: «modular = custom; identity/acl = MT EF; contract = Rabbit message.»

---

## InstanceId = dedicated queue (fan-out)

```csharp
.Endpoint(x => x.InstanceId = "IdentityServer")
.Endpoint(x => x.InstanceId = "ACLServer")
```

Har service **khodesh** copy of `PersonnelCreated` migire (queue per instance id). Competing consumers **within** Identity scale horizontally on same InstanceId queue; Identity vs ACL = **two queues**, both get the event.

Day 20 covered; critical for EF Outbox chapter because **each** service’s consume path uses **that** service’s InboxState DB — not shared.

---

## Tenant filters still apply

```csharp
cfg.UseTenantContextFilters(context);
```

Publish/consume headers `X-Tenant-SiteIds` / `X-IsSuperAdmin` (Day 16). Consumer DbContext queries respect tenant when context restored.

CreateSite publish runs in HTTP request with TenantContext — Bus Outbox stores message; delivery later still sends headers captured at publish time (MT message headers).

---

## ACL consumer surface (scale of wiring)

ACL registers many `IConsumer`s with InstanceId ACLServer + EF outbox on almost all (except get-endpoints RPC). Har consume that writes DB + maybe republishes benefits from transactional outbox.

GateServer / DCC / Reporting / RequestTracker: same `AddEntityFrameworkOutbox` + `UseBusOutbox` pattern — copy-paste platform style across microservices (Day 18 contrast: Dejban modules share custom; microservices share MT template).

---

## Cross-ecosystem sequence (full story)

```
[FE] Create Personnel on Dejban.Api
  → Personnels SaveChanges
  → custom outbox_messages (Day 21)
  → Quartz → PersonnelCreatedDomainEventHandler
  → IEventBus.Publish(PersonnelCreated)  // may be immediate publish from worker
       NOTE: worker publish is after outbox processed — reliability was on custom outbox

[Rabbit] PersonnelCreated

[IdentityServer] PersonnelCreatedConsumer (InboxState)
  → create ApplicationUser
  → SaveChanges (+ optional further outbox publishes)

[ACLServer] PersonnelCreatedConsumer (InboxState)
  → sync device users / ACL entities
```

**Do outbox technologies** in one business flow — interview gold. Same reliability goal, different hosting model.

---

## Serilog noise filter

```csharp
// GateServer / similar
.Filter.ByExcluding(logEvent =>
    commandText contains OutboxState | InboxState | OutboxMessage)
```

Delivery polls chatty — filtered in prod logs. Don’t filter **errors**. Over-filter = delivery failures blind.

---

## Comparison table — memorize

| topic | Dejban.Api module | Identity / ACL |
|---|---|---|
| Outbox write | `InsertOutboxMessagesInterceptor` | `IPublishEndpoint` + Bus Outbox |
| Trigger | `Entity.Raise` | explicit `Publish` in handler |
| Poller | `ProcessOutboxJob` Quartz | MT Bus Outbox hosted |
| SQL lock | Dapper `FOR UPDATE` | MT OutboxState locking |
| Inbox | `inbox_messages` + Quartz | `InboxState` + endpoint filter |
| Idempotent handler | Scrutor `outbox_message_consumers` | InboxState + manual checks |
| DbContext count | 8 module contexts | 1 ApplicationDbContext |
| Schema | `personnels.outbox_messages` | public `OutboxMessage` |

In jadval ra az bar kon — mosahebe «chera do outbox?» inja javab mide.

---

## Smell-ha / pitfalls

1. **Publish after SaveChanges** by mistake → bypass bus outbox (immediate send)  
2. **Forgot AddOutbox*Entity** on model → runtime EF errors  
3. **Forgot UseBusOutbox** → Publish hits broker immediately  
4. **RPC endpoint with heavy outbox** — skipped intentionally; don’t add blindly  
5. **Logical idempotency missing** in consumer — inbox helps transport-level, not always business  
6. **Dual styles** in one company — onboarding cost (document!)  
7. **Fat events** + MT serialize size  
8. **Tenant empty** on background publish if context not set  
9. **Migration drift** of MT table shapes across MT version upgrades  
10. **Filtering Outbox SQL** hides delivery failures if over-filtered  
11. **Multiple DbContexts** + wrong context type in `AddEntityFrameworkOutbox<T>`  
12. **Long consumer transaction** holding inbox lock — keep Consume thin  

---

## Debug checklist

1. After CreateSite: row in Identity `OutboxMessage`?  
2. Message appears in Rabbit? (delivery working)  
3. Consumer queue `personnel-created-identity-server` depth?  
4. `InboxState` row for message id?  
5. User created in AspNetUsers?  
6. Compare Dejban `personnels.outbox_messages` for PersonnelCreated path  
7. MT version docs for Bus Outbox quirks  
8. Exception in Consume → retry / `_error` queue  

---

## 25 soal-e mosahebe

1. MassTransit EF Outbox chie?  
2. UseBusOutbox chie mikone?  
3. OutboxMessage vs OutboxState vs InboxState?  
4. Chera Publish ghabl az SaveChanges?  
5. Dual-write chejori solve mishe?  
6. Consumer UseEntityFrameworkOutbox?  
7. Chera RPC endpoints skip outbox?  
8. Custom Day 21 vs MT — tradeoffs?  
9. Chera Dejban.Api MT outbox nadare?  
10. InstanceId + inbox?  
11. At-least-once ba InboxState?  
12. Logical vs transport idempotency?  
13. CreateSite flow step-by-step?  
14. PersonnelCreated Identity consumer?  
15. Cross-style bridge (custom → MT)?  
16. UsePostgres in AddEntityFrameworkOutbox?  
17. Bus Outbox delivery failure?  
18. Poison / error queue?  
19. Tenant headers with outbox?  
20. AddInboxStateEntity kojast?  
21. Competing consumers vs fan-out queues?  
22. Mapster/MediatR + Publish order?  
23. Upgrade MassTransit migration risk?  
24. Chejori test outbox locally?  
25. Saga vs outbox?

---

## Senario whiteboard

### A) CreateSite Identity  
Publish SiteCreated → SaveChanges → OutboxMessage → Rabbit → Dejban Visitors/Personnels copies via their consumers/inbox.

### B) Broker down after Identity commit  
OutboxMessage pending → when broker up, Bus Outbox drains → no lost SiteCreated.

### C) Publish after SaveChanges bug  
Site committed; Publish throws → no message, no outbox row → **dual-write regression**.

### D) Duplicate PersonnelCreated  
InboxState / existingUser check → no duplicate AspNetUsers.

### E) Explain to interviewer why two outbox systems  
Modular domain-event density + multi-schema vs microservice single DbContext + MT-first.

---

## Mini lab

1. Open Identity `AddMassTransit` + `ApplicationDbContext` MT entities  
2. Breakpoint CreateSite Publish + SaveChanges  
3. SQL: `SELECT * FROM "OutboxMessage" ORDER BY 1 DESC LIMIT 5`  
4. Soft-create personnel on Dejban; watch Identity consumer + AspNetUsers  
5. Stop Rabbit briefly; CreateSite; see OutboxMessage accumulate; start Rabbit; drain  
6. Diff mentally with `personnels.outbox_messages` columns  

---

## Resume

**short:**

> Integrated MassTransit Entity Framework Outbox (`UsePostgres` + `UseBusOutbox`) on Identity, ACL, and related microservices so `IPublishEndpoint.Publish` and EF `SaveChanges` share one transaction, with `UseEntityFrameworkOutbox` on consume endpoints for inbox-backed idempotent processing — complementing the modular monolith’s custom Quartz outbox.

**bullets:**

- Registered `AddEntityFrameworkOutbox<ApplicationDbContext>` and mapped `InboxState` / `OutboxState` / `OutboxMessage` entities  
- Staged integration events via `IPublishEndpoint` in command handlers (e.g. `SiteCreated`) before `SaveChangesAsync`  
- Applied consumer EF outbox on Rabbit endpoints while exempting RPC request clients  
- Documented dual-stack messaging: Dejban custom outbox vs microservice MT EF Outbox over shared Rabbit contracts  

**skills:** `MassTransit, EF Core Outbox, Bus Outbox, Inbox Pattern, RabbitMQ, Transactional Messaging, Microservices, Idempotent Consumers, PostgreSQL`

---

## File-haye mohem

| chi | koja |
|---|---|
| Identity MT + outbox | `IdentityServer/.../ServiceCollectionExtensions.cs` `AddMassTransit` |
| Identity DbContext MT entities | `IdentityServer/.../ApplicationDbContext.cs` |
| CreateSite publish | `.../CreateSite/CreateSiteCommandHandler.cs` |
| PersonnelCreated consumer | `IdentityServer/.../PersonnelCreatedConsumer.cs` |
| ACL MT + outbox | `ACLServer/.../ServiceCollectionExtensions.cs` |
| ACL DbContext | `ACLServer/.../ApplicationDbContext.cs` |
| RequestTracker / DCC / Gate / Reporting | same `AddEntityFrameworkOutbox` pattern |
| Contrast custom | Day 21 files under `Dejban.Common.Infrastructure/Outbox/` |

---

## Connection to other days

| day | rabt |
|---|---|
| 19 Dapper | custom job SQL (not used here) |
| 20 MassTransit | bus, retry, InstanceId |
| 21 Custom outbox | sibling pattern |
| 23 Inbox deep | custom inbox; here InboxState |
| 09 Architecture | modular vs microservice messaging |
| 16 Tenancy | tenant filters on bus |

---

## Chejori digest koni

1. Jadval custom vs MT ra az bar kon (10 min)  
2. Identity AddMassTransit + CreateSite (20 min)  
3. SQL OutboxMessage after CreateSite (10 min)  
4. PersonnelCreated consumer + Inbox idea (15 min)  
5. 25 soal (20 min)

---

## Deep dive — Bus Outbox vs «just Publish»

```csharp
// WITHOUT Bus Outbox:
await publishEndpoint.Publish(evt); // network I/O now
await db.SaveChangesAsync();        // if this fails → ghost event on bus

// WITH UseBusOutbox:
await publishEndpoint.Publish(evt); // stages in EF change tracker / outbox
await db.SaveChangesAsync();        // atomic
// later: delivery hosted service → Rabbit
```

Developer API almost identical — **behavior** changes. Interview: «Publish is intercepted/staged.»

---

## Deep dive — InboxState lifecycle (conceptual)

1. Message delivered to consumer endpoint  
2. MT begins DB transaction; ensures InboxState for messageId  
3. If already completed → skip consumer body  
4. Else run `Consume`  
5. Any `Publish` inside Consume also staged to OutboxMessage (linked to inbox)  
6. SaveChanges + complete inbox  
7. Ack to Rabbit  

Cascade: Identity consume might publish further events transactionally — rare in Dejban Identity personnel consumer (mostly DB only), more relevant when ACL republishes.

---

## Deep dive — RequestTracker / DCC / Gate / Reporting

Hame:

```csharp
x.AddEntityFrameworkOutbox<ApplicationDbContext>(o =>
{
    o.UsePostgres();
    o.UseBusOutbox();
});
```

+ `AddInboxStateEntity` / `AddOutboxStateEntity` / `AddOutboxMessageEntity` on their DbContext.

**Reporting / DCC** may publish less; pattern still registered for consistency and any future consume/publish. GateServer device-facing — outbox for reliable device-related events.

Copy-paste = intentional platform standard for microservices (opposite of Dejban’s custom multi-schema).

---

## Deep dive — CreateSite + SuperAdmin grant

```csharp
_context.Sites.Add(site);
await _publishEndpoint.Publish(new SiteCreated(...));
var superAdminGrant = await SuperAdminSiteAccessHelper.AddSiteToSuperAdminAsync(...);
await _context.SaveChangesAsync();
// then cache invalidate (after commit) — NOT in outbox
```

**Cache invalidate after SaveChanges** = best-effort. Age process dies after commit before invalidate → stale cache until TTL. Outbox does **not** cover Redis cache. Pattern: outbox for **messages**; cache = separate concern (Day 25).

---

## Deep dive — Batch consumers

```csharp
IConsumer<Batch<PersonnelDeleted>>
```

MT can batch deletes. EF Outbox still wraps the consume unit — understand batch ack semantics when debugging deletes.

---

## Testing strategies

| test | chejori |
|---|---|
| Unit handler | mock `IPublishEndpoint` — verify Publish called; don’t assert Rabbit |
| Integration | Testcontainers Postgres + Rabbit; assert OutboxMessage then bus |
| Consumer | WebApplicationFactory / MT test harness; publish message; assert user row |
| Dual-write regression | force SaveChanges throw after Publish staging — expect no OutboxMessage |

MassTransit test harness simplifies in-memory bus — still use real EF outbox for confidence.

---

## Ops queries (Identity DB)

```sql
-- pending delivery
SELECT COUNT(*) FROM "OutboxMessage";

-- inbox activity
SELECT * FROM "InboxState" ORDER BY "Received" DESC LIMIT 20;

-- stuck delivery locks (conceptual — column names per MT version)
SELECT * FROM "OutboxState";
```

Compare Dejban:

```sql
SELECT COUNT(*) FROM personnels.outbox_messages WHERE processed_on_utc IS NULL;
```

---

## Decision guide — which outbox when?

| context | choose |
|---|---|
| Rich domain events on many EF entities | Custom interceptor (Day 21) |
| Single DbContext microservice, MT-first | MT EF Outbox (Day 22) |
| Need multi-schema isolation | Custom per schema |
| Want least custom code | MT EF Outbox |
| Already invested Quartz inbox/outbox | Stay consistent in that host |

Mixing **inside one process** (custom + MT outbox same DbContext) = confusion — Dejban avoids by splitting hosts.

---

## Interview story (60 second)

> «We use two transactional outbox implementations. In the modular monolith, domain events are collected on aggregates and written to per-schema outbox tables via an EF SaveChanges interceptor, then Quartz workers dispatch handlers that publish to Rabbit. In Identity and ACL microservices we use MassTransit’s EF Core outbox: handlers call IPublishEndpoint.Publish and SaveChanges once; Bus Outbox delivers to Rabbit, and consumers use UseEntityFrameworkOutbox with InboxState. Same reliability goal, different hosting model.»

---

## Extra whiteboard — failure injection

1. Kill Rabbit before CreateSite SaveChanges → commit succeeds with OutboxMessage; restart Rabbit → SiteCreated appears  
2. Kill Identity after SaveChanges before delivery completes → same  
3. Throw in PersonnelCreatedConsumer → retry / error queue; InboxState not completed  
4. Re-deliver → existingUser return or inbox skip  

---

## Cheatsheet — registration checklist (new microservice)

1. `modelBuilder.AddInboxStateEntity/OutboxState/OutboxMessage`  
2. `AddEntityFrameworkOutbox<TDbContext>(o => { o.UsePostgres(); o.UseBusOutbox(); })`  
3. Consumers + `InstanceId` if fan-out  
4. `AddRabbitMqConfigureEndpointsCallback` → `UseEntityFrameworkOutbox` (skip RPC)  
5. Handlers: `Publish` then `SaveChanges`  
6. Migration / migrationesho for MT tables  
7. Log filter optional for poll noise  

---

## Glossary

| kalame | ma'ni |
|---|---|
| Bus Outbox | stage publish until SaveChanges; deliver later |
| Consumer outbox | transactional consume + cascade publish |
| InboxState | MT consumer idempotency/lock |
| OutboxState | delivery coordination |
| IPublishEndpoint | MT publish API (outbox-aware with Bus Outbox) |
| InstanceId | per-service queue suffix for fan-out |
| Dual-stack | custom + MT outbox in one product |
| Staged message | written to OutboxMessage, not yet on Rabbit |
| Delivery service | MT hosted poller that flushes Bus Outbox |
| RPC exempt | request client endpoints skip EF outbox |

---

## Related reading order

```
Day 20 MassTransit basics
  → Day 21 Custom transactional outbox (Dejban.Api)
  → Day 22 MT EF Outbox (Identity/ACL)   ← you are here
  → Day 23 Inbox + Idempotent (Dejban custom inbox deep)
  → Day 24 Scrutor Decorate
```

Age Day 21 nakhoondi, aval dual-write + custom pipeline; ba'd in fasl «library version» mishe.

---

*Day 22 tamum. Ba'd: Day 23 — Inbox + Idempotent Handler (amade). Fehrest: [README.md](./README.md).*
