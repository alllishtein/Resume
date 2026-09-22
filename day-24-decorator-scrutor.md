# Day 24 — Decorator (Scrutor)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Decorator** yani ye object ra ba wrapper wrap kon ta behavior ezafe she, bedune avaz-e class-e asli (OCP). **Scrutor** = library roye MS.DI ke `services.Decorate(...)` midahad. Dejban **faghat** Decorate estefade mikone (na `Scan()`): har domain/integration event handler ra ba `Idempotent*EventHandler<T>` wrap mikone ta double-process (outbox/inbox at-least-once) skip she.

Handler-e business **nadune** az idempotency — cross-cutting to decorator. In fasl = pattern + Scrutor DI mechanics + Dejban wiring; Days 21/23 = outbox/inbox tables ke decorator mikhoone/minevise. Chera in tool? Chun event handlers MediatR `IRequest` nistan — pipeline behavior unha ro wrap nemikone.

---

# BAKHSH-E AVAL: WORLD — Decorator pattern to donya

## GoF Decorator — idea

```
Client → IComponent.Operation()
              ↑
         ConcreteComponent
              ↑
         DecoratorA (adds logging) → calls inner.Operation()
              ↑
         DecoratorB (adds caching) → calls inner.Operation()
```

```csharp
public interface INotifier
{
    Task NotifyAsync(string message);
}

public sealed class EmailNotifier : INotifier
{
    public Task NotifyAsync(string message) => SendEmail(message);
}

public sealed class LoggingNotifier(INotifier inner) : INotifier
{
    public async Task NotifyAsync(string message)
    {
        Log.Information("notify {Message}", message);
        await inner.NotifyAsync(message);
    }
}

public sealed class RetryNotifier(INotifier inner) : INotifier
{
    public async Task NotifyAsync(string message)
    {
        for (var i = 0; i < 3; i++)
        {
            try { await inner.NotifyAsync(message); return; }
            catch when (i < 2) { await Task.Delay(100); }
        }
    }
}

// compose: Retry → Logging → Email
INotifier n = new RetryNotifier(new LoggingNotifier(new EmailNotifier()));
```

**Maziat:**

- Open for extension, closed for modification (OCP)
- Compose at runtime / DI
- Single Responsibility: Email sends; Logging logs

**Vs inheritance:** `LoggingEmailNotifier : EmailNotifier` explode combinations (logging+retry+metrics × N). Decorator stacks freely. Yani inheritance tree explode mishe; decorator stack flexible-e.

---

## Decorator vs digar wrap-ha

| pattern | fargh |
|---|---|
| **Decorator** | same interface; add behavior; often multiple |
| **Proxy** | same interface; control access (lazy, remote, security) |
| **Adapter** | **different** interface → make compatible |
| **Facade** | simplify subsystem; often new API |
| **Middleware / Pipeline** | chain for cross-cutting (HTTP, MediatR) — cousin of decorator |

Interview: Proxy ≈ decorator ba intent-e control; Adapter changes shape. Middleware = decorator-like baraye HTTP/MediatR.

---

## Cross-cutting placement options (.NET)

| approach | mesal | Dejban |
|---|---|---|
| Decorator (DI) | Scrutor Idempotent* | **yes** handlers |
| MediatR pipeline | ValidationBehavior | **yes** commands |
| ASP.NET middleware | TenantContext | **yes** HTTP |
| Endpoint filter | RequirePermissions | **yes** routes |
| EF interceptor | InsertOutboxMessages | **yes** SaveChanges |
| AOP (Castle, etc.) | rare | no |

**Rule of thumb:**

- Per-handler type concern tied to that service → **Decorate**
- All MediatR requests → **pipeline behavior**
- All HTTP → **middleware**

Idempotency for event handlers = perfect Decorate (not every MediatR command). Har layer ye job — hamposhi nakon.

---

## Manual DI decorator (bedune Scrutor)

```csharp
services.AddScoped<EmailNotifier>();
services.AddScoped<INotifier>(sp =>
{
    var email = sp.GetRequiredService<EmailNotifier>();
    return new LoggingNotifier(email);
});
```

Ya:

```csharp
services.AddScoped<INotifier, EmailNotifier>();
// replace — painful with many services
```

Scrutor automates replace + wire inner instance. Bedune an, N ta handler = N ta factory boilerplate.

---

## Scrutor chie?

NuGet package: extends `IServiceCollection`.

Famous APIs:

- `Scan(...)` — convention registration (Dejban **uses rarely/not** for handlers)
- `Decorate<TService, TDecorator>()` / `Decorate(Type, Type)` — **Dejban uses this**

```csharp
services.AddScoped<IPaint, Paint>();
services.Decorate<IPaint, PaintDecorator>();
// resolve IPaint → PaintDecorator(inner: Paint)
```

Multiple:

```csharp
services.Decorate<IPaint, LoggingPaintDecorator>();
services.Decorate<IPaint, CachingPaintDecorator>();
// resolve → Caching(Logging(Paint))  — order = decorate order (last = outermost often)
```

Confirm order in tests — Scrutor stacks; last Decorate typically wraps previous. Document intended stack.

---

## Open generics

```csharp
services.AddScoped(typeof(ICommandHandler<>), typeof(CommandHandler<>));
services.Decorate(typeof(ICommandHandler<>), typeof(LoggingHandler<>));
```

Dejban closes generic per event:

```csharp
typeof(IdempotentDomainEventHandler<>).MakeGenericType(domainEvent);
services.Decorate(concreteHandlerType, closedIdempotent);
```

Yani per-event closed decorator — bishtar descriptor, vali explicit.

---

## Lifetime

Decorator usually **same lifetime** as decorated (Scoped with Scoped). Captive dependency: Singleton decorator holding Scoped inner = bug.

Dejban: both Scoped (`TryAddScoped` + Decorate). Lifetime mismatch = subtle leak / disposed DbContext.

---

## Testing decorated services

```csharp
// Unit-test inner handler alone — new RealHandler(...) without decorator
// Unit-test decorator — mock IDomainEventHandler<T> decorated
// Integration — full DI; force double Handle; assert consumer table / skip
```

Decorator should be thin — easy to test with mocked inner. Fat decorator = smell.

---

## Anti-patterns

1. Fat decorator (business rules) — keep cross-cutting only  
2. Decorator order undocumented  
3. Decorate before registering inner → Scrutor throw  
4. Resolving concrete type expecting concrete instance after Decorate (may get wrapper)  
5. Using Scan() blindly registering decorators as services twice  
6. Inheritance instead of decorator for cross-cutting  

---

# BAKHSH-E DOVOM: DEJBAN — Scrutor Decorate to in proje

## Package

```xml
<!-- Dejban.Common.Infrastructure.csproj -->
<PackageReference Include="Scrutor" />
```

Modules reference Infrastructure → get Decorate extension.

**Scan()** for auto-register handlers: **not** the main path — manual reflection loop + TryAddScoped + Decorate.

---

## Registration loop (PersonnelsModule)

```csharp
private static void AddDomainEventHandlers(this IServiceCollection services)
{
    Type[] domainEventHandlers = Application.AssemblyReference.Assembly
        .GetTypes()
        .Where(t => t.IsAssignableTo(typeof(IDomainEventHandler)))
        .ToArray();

    foreach (Type domainEventHandler in domainEventHandlers)
    {
        services.TryAddScoped(domainEventHandler); // concrete handler type

        Type domainEvent = domainEventHandler
            .GetInterfaces()
            .Single(i => i.IsGenericType)
            .GetGenericArguments()
            .Single();

        Type closedIdempotentHandler =
            typeof(IdempotentDomainEventHandler<>).MakeGenericType(domainEvent);

        services.Decorate(domainEventHandler, closedIdempotentHandler);
    }
}
```

Integration side — same shape, Presentation assembly + `IdempotentIntegrationEventHandler<>`:

```csharp
services.TryAddScoped(integrationEventHandler);
services.Decorate(integrationEventHandler, closedIdempotentHandler);
```

**× 8 modules** copy this (Day 18 smell) — schema-specific idempotent class per module. DRY fix mental: shared helper ba schema param.

---

## Chejori resolve mishe?

```
DomainEventHandlersFactory.GetHandlers(eventType, sp, assembly)
  → finds concrete PersonnelDeletedDomainEventHandler type
  → sp.GetRequiredService(concreteType)
  → Scrutor factory returns IdempotentDomainEventHandler<PersonnelDeletedDomainEvent>
       ctor(IDomainEventHandler<T> decorated = ORIGINAL PersonnelDeleted...,
            IDbConnectionFactory db)
  → cast to IDomainEventHandler → Handle()
```

Outer `Handle` = idempotent check; inner = publish integration event / business.

**Key for consumer table:**

```csharp
var outboxMessageConsumer = new OutboxMessageConsumer(
    domainEvent.Id,
    decorated.GetType().Name); // ORIGINAL handler name, na Idempotent*
```

`decorated.GetType().Name` → `PersonnelDeletedDomainEventHandler` — stable business key. Chera na Idempotent*? Chun rename-e decorator nabayad key avaz kone; business handler name = identity.

---

## IdempotentDomainEventHandler (decorator body)

```csharp
internal sealed class IdempotentDomainEventHandler<TDomainEvent>(
    IDomainEventHandler<TDomainEvent> decorated,
    IDbConnectionFactory dbConnectionFactory)
    : DomainEventHandler<TDomainEvent>
    where TDomainEvent : IDomainEvent
{
    public override async Task Handle(TDomainEvent domainEvent, CancellationToken ct = default)
    {
        await using var connection = await dbConnectionFactory.OpenConnectionAsync();

        var key = new OutboxMessageConsumer(domainEvent.Id, decorated.GetType().Name);

        if (await OutboxConsumerExistsAsync(connection, key))
            return;

        await decorated.Handle(domainEvent, ct);

        await InsertOutboxConsumerAsync(connection, key);
    }
}
```

SQL against **`personnels.outbox_message_consumers`** (module-specific string).

Inbox twin: `IdempotentIntegrationEventHandler` → `inbox_message_consumers` (Day 23). Same pattern — learn once.

---

## Chera decorator, na code inside every handler?

Bedune decorator:

```csharp
public async Task Handle(...)
{
    if (await AlreadyProcessed(...)) return;
    await eventBus.PublishAsync(...);
    await MarkProcessed(...);
}
```

× N handlers → copy-paste, forget risk, OCP fail.

Ba decorator: handlers stay pure «map domain → integration» / «upsert read model». Resume soundbite: idempotency ezafe shod bedune edit-e N handler.

---

## Chera na MediatR pipeline?

Domain/integration event handlers **MediatR IRequest nistan** — custom `IDomainEventHandler` / `IIntegrationEventHandler` invoked from Quartz factories.

Pipeline behaviors won't wrap them. Decorate = right tool.

Commands still use ValidationBehavior etc. (Day 10/11) — parallel world. Dejban **both** estefade mikone — don't replace one with the other blindly.

---

## Order of Decorate calls

Dejban: **one** decorator per handler (idempotent only).

Agar later LoggingDecorator ezafe koni:

```csharp
services.Decorate(handler, typeof(Idempotent...));
services.Decorate(handler, typeof(Logging...)); // careful which is outer
```

Test double-invoke and log order. Document intended stack: e.g. Logging(Idempotent(Handler)) vs Idempotent(Logging(Handler)) — idempotent outer usually better (skip = no log spam) or inner (log attempts) — product choice.

---

## Factory + decorator interaction

```csharp
// DomainEventHandlersFactory
object domainEventHandler = serviceProvider.GetRequiredService(domainEventHandlerType);
handlers.Add((domainEventHandler as IDomainEventHandler)!);
```

Resolves **concrete service type** that Scrutor replaced with decorator factory. Result typed as `IDomainEventHandler` for `Handle`.

Don't `as PersonnelDeletedDomainEventHandler` — may be null after decorate. Cast to interface, na concrete.

---

## TryAddScoped + Decorate order

1. **Must** register inner first (`TryAddScoped`)  
2. Then `Decorate`  
3. Decorate before register → Scrutor: no matching descriptor → exception at startup  

`TryAdd` = skip if already added (safe for shared). Decorate mutates existing descriptor. Startup fail on Decorate → first check: inner registered?

---

## Comparison — outbox vs inbox decorator

| | Domain (outbox path) | Integration (inbox path) |
|---|---|---|
| Class | `IdempotentDomainEventHandler<T>` | `IdempotentIntegrationEventHandler<T>` |
| Inner | `IDomainEventHandler<T>` | `IIntegrationEventHandler<T>` |
| Table | `outbox_message_consumers` | `inbox_message_consumers` |
| Assembly of inners | Application | Presentation |
| Invoked from | ProcessOutboxJob | ProcessInboxJob |

Same pattern — learn once. Days 21/23 tables, Day 24 mechanics.

---

## OCP story for resume / interview

> Adding idempotency did not require editing dozens of handlers. We registered a generic decorator with Scrutor so each handler gained at-least-once safety transparently.

Classic SOLID soundbite + real code path.

---

## Standalone services?

Identity/ACL: **no** Scrutor idempotent event handlers — use MT InboxState / manual `if (exists) return` in `IConsumer` (Day 22/23). Decorate is a **Dejban.Api modular** trademark.

---

## Could you Decorate repositories?

```csharp
services.AddScoped<IPersonnelRepository, PersonnelRepository>();
services.Decorate<IPersonnelRepository, CachingPersonnelRepository>();
```

Possible — Dejban **doesn't** today. Caching often HybridCache in handlers (Day 25). Pattern available.

---

## Smell-ha

1. **8 copies** of Idempotent*Handler differing only by schema name in SQL  
2. **8 copies** of Decorate registration loops  
3. **No Scan()** — fine, but reflection loop duplicated  
4. **Concrete type Decorate** — resolving concrete after decorate returns wrapper; confusing if someone expects concrete  
5. **Handler rename** changes `decorated.GetType().Name` dedup key — in-flight duplicates possible  
6. **Decorator DB connection ≠ job transaction** (Days 21/23)  
7. **Only one cross-cut** — no metrics/logging decorator yet (opportunity)  
8. **Scrutor only in Common.Infrastructure** — modules must reference that package graph  
9. **Open generic Decorate once** not used — closed per event via MakeGenericType (more descriptors)  
10. **Tests** often skip asserting decorator registration  

### DRY fix (mental refactor)

```csharp
// shared
services.AddIdempotentHandlers<IdempotentDomainEventHandler<>>(
    Application.Assembly, schema: "personnels");
```

Pass schema into decorator via `IOptions` / constructed type — today hardcoded SQL schema strings.

---

## Debug checklist

1. Startup fail on Decorate → inner not registered / wrong types  
2. Handler runs twice → consumer table miss / wrong Name / schema typo  
3. Handler never runs → EXISTS true stale row; delete consumer row  
4. `GetRequiredService(concrete)` unexpected type → remember decorator wrapper  
5. Missing Scrutor package reference → Decorate extension missing  

---

## 25 soal-e mosahebe

1. Decorator pattern chie?  
2. Vs inheritance?  
3. Vs Proxy / Adapter?  
4. OCP chejori?  
5. Scrutor chie?  
6. Decorate vs Scan?  
7. Dejban cherā Decorate?  
8. IdempotentDomainEventHandler flow?  
9. `decorated.GetType().Name` cherā?  
10. Chera na copy-paste into handlers?  
11. Chera na MediatR behavior?  
12. Lifetime Scoped?  
13. Decorate order?  
14. TryAdd then Decorate order?  
15. Outbox vs Inbox decorator?  
16. Factory chejori resolve mikone?  
17. Multiple decorators stack?  
18. Captive dependency risk?  
19. Identity Scrutor dare?  
20. Test decorator?  
21. Open generic Decorate?  
22. SOLID which principles?  
23. Middleware vs decorator?  
24. EF interceptor vs decorator?  
25. DRY smell across modules?

---

## Senario whiteboard

### A) First process  
EXISTS false → Publish → INSERT consumers  

### B) Redelivery  
EXISTS true → return immediately — no second Publish  

### C) Crash after Publish before INSERT consumers  
Redelivery → Publish again → inbox/consumer downstream must be idempotent (Day 23)  

### D) Add LoggingDecorator  
Discuss outer vs inner; show DI registration  

### E) Forget Decorate on new module  
Handlers work; duplicates under at-least-once — silent prod bug  

---

## Mini lab

1. Read `PersonnelsModule.AddDomainEventHandlers`  
2. F12 `IdempotentDomainEventHandler`  
3. Breakpoint EXISTS / decorated.Handle / INSERT  
4. SoftDelete twice quickly / replay outbox — second skip  
5. Temporarily comment Decorate — observe duplicate risk in eng only  

---

## Resume

**short:**

> Applied the Decorator pattern via Scrutor `Decorate` to wrap all domain and integration event handlers with generic idempotent handlers, keeping business handlers free of deduplication logic while enforcing at-least-once safety against outbox/inbox consumer tables.

**bullets:**

- Registered concrete handlers then decorated them with `IdempotentDomainEventHandler<>` / `IdempotentIntegrationEventHandler<>` per module  
- Keyed idempotency by `(messageId, innerHandlerTypeName)` using Dapper EXISTS/INSERT  
- Separated cross-cutting reliability from application/presentation handler code (OCP)  
- Documented stack alternatives (MediatR behaviors, middleware) and why Decorate fits event handlers  

**skills:** `Decorator Pattern, Scrutor, Dependency Injection, SOLID/OCP, Idempotency, Domain Events, Integration Events, Clean Architecture`

---

## File-haye mohem

| chi | koja |
|---|---|
| Scrutor package | `Dejban.Common.Infrastructure.csproj` |
| Decorate registration | e.g. `PersonnelsModule.AddDomainEventHandlers` |
| Domain decorator | `Personnels.Infrastructure/Outbox/IdempotentDomainEventHandler.cs` |
| Integration decorator | `Visitors.Infrastructure/Inbox/IdempotentIntegrationEventHandler.cs` |
| Factory resolve | `DomainEventHandlersFactory` / `IntegrationEventHandlersFactory` |
| Consumer rows | `OutboxMessageConsumer` / `InboxMessageConsumer` |
| Sample inner handler | `PersonnelDeletedDomainEventHandler` |

---

## Connection to other days

| day | rabt |
|---|---|
| 03 OOP/SOLID | Decorator intro |
| 05 Pipeline/DI | Scrutor section |
| 10 MediatR | behaviors ≠ event Decorate |
| 18 Modular DI | registration loops |
| 21 Outbox | domain decorator tables |
| 23 Inbox | integration decorator tables |
| 25 Cache | optional future Caching decorator |

---

## Chejori digest koni

1. Draw Email/Logging/Retry compose (5 min)  
2. Read Module Decorate loop (15 min)  
3. Trace SoftDelete through IdempotentDomainEventHandler (20 min)  
4. Explain OCP soundbite (5 min)  
5. 25 soal (20 min)

---

## Glossary

| kalame | ma'ni |
|---|---|
| Decorator | wrapper same interface + extra behavior |
| Scrutor | DI helpers: Scan + Decorate |
| Decorate | replace registration with wrapper factory |
| Inner / decorated | original service instance |
| Outer | wrapper client calls first |
| Cross-cutting | logging, retry, idempotency, cache |
| Open generic | `Handler<>` without closed T |
| Dedup key | messageId + handler type name |

---

## Deep dive — decorator vs interceptor vs behavior (one diagram)

```
HTTP request
  → Middleware (tenant, auth)          // all requests
  → Endpoint filter (permission)       // some routes
  → MediatR behaviors (validation)     // all IRequest
  → Command handler
       → entity.Raise
       → SaveChanges
            → EF Interceptor (outbox write)

Later Quartz:
  → DomainEventHandlersFactory
  → Scrutor Decorator (idempotent)     // each IDomainEventHandler
  → Real domain event handler
       → IEventBus.Publish

Later inbox Quartz:
  → Scrutor Decorator (idempotent)     // each IIntegrationEventHandler
  → Real integration handler
```

Har layer ye job — hamposhi nakon.

---

## Deep dive — implementing a second decorator (exercise)

```csharp
internal sealed class LoggingDomainEventHandler<T>(
    IDomainEventHandler<T> decorated,
    ILogger<LoggingDomainEventHandler<T>> logger)
    : DomainEventHandler<T> where T : IDomainEvent
{
    public override async Task Handle(T e, CancellationToken ct)
    {
        logger.LogInformation("Handling {Event}", typeof(T).Name);
        await decorated.Handle(e, ct);
    }
}

// after idempotent decorate:
services.Decorate(handlerType, typeof(LoggingDomainEventHandler<>).MakeGenericType(domainEvent));
```

Decide: Logging outer (logs even skips?) — if Idempotent outer, skips silent; if Logging outer + Idempotent inner, logs every attempt including skips.

---

## Interview 60s

> «We use Scrutor to decorate event handlers. Each handler is registered, then wrapped with a generic idempotent decorator that checks a consumer table before invoking the real handler. That keeps idempotency out of business code and matches our outbox/inbox at-least-once processing.»

---

## Deep dive — Scrutor Decorate under the hood (conceptual)

1. Find `ServiceDescriptor` where `ServiceType == domainEventHandler` (concrete)  
2. Save reference to create **original** instance  
3. Replace descriptor with `ImplementationFactory`:  
   - create original  
   - `ActivatorUtilities.CreateInstance(decoratorType, …, original as dependency)`  
4. Future `GetRequiredService(serviceType)` → factory → decorator instance  

Agar hich descriptor match nashe → exception: «No service for type X found to decorate».

---

## Deep dive — `decorated` parameter matching

```csharp
IdempotentDomainEventHandler(
    IDomainEventHandler<TDomainEvent> decorated,  // Scrutor fills with original
    IDbConnectionFactory dbConnectionFactory)     // normal DI
```

Scrutor matches constructor arg assignable from the decorated service. Digar dependencies az container.

Agar do parameter hamoon type dashte bashi → ambiguous — avoid.

---

## Deep dive — naming keys & refactor safety

| change | asar |
|---|---|
| Rename handler class | new Name → old consumer rows orphan; duplicates until TTL/manual clean |
| Move handler namespace | `GetType().Name` unchanged (Name not FullName) — OK |
| Two handlers same short Name different namespaces | **collision risk** — rare; FullName safer |

Dejban uses `.Name` — miduni risk.

---

## Deep dive — unit test decorator

```csharp
var inner = Substitute.For<IDomainEventHandler<PersonnelDeletedDomainEvent>>();
var db = /* fake connection factory returning EXISTS false then true */;
var sut = new IdempotentDomainEventHandler<PersonnelDeletedDomainEvent>(inner, db);

await sut.Handle(evt, ct);
await sut.Handle(evt, ct);

await inner.Received(1).Handle(evt, ct);
```

Integration: real Postgres Testcontainer; assert row count in `outbox_message_consumers`.

---

## Deep dive — MediatR `IPipelineBehavior` is «decorator-like»

```csharp
public class LoggingBehavior<TReq, TRes>(ILogger ...) : IPipelineBehavior<TReq, TRes>
{
    public async Task<TRes> Handle(TReq request, RequestHandlerDelegate<TRes> next, CancellationToken ct)
    {
        // before
        var response = await next(); // «inner»
        // after
        return response;
    }
}
```

Same structure (before/after/inner). Difference: MediatR wires open behaviors for all requests; Scrutor Decorate targets specific service registrations.

Dejban uses **both** — don't replace one with the other blindly.

---

## Cheat sheet — add idempotent decorator to new module

1. Copy `IdempotentDomainEventHandler` / Integration twin; fix schema SQL  
2. `AddDomainEventHandlers` / `AddIntegrationEventHandlers` with Decorate loop  
3. Ensure factory resolves via DI (not `new Handler()`)  
4. Smoke: process same outbox/inbox message twice — second no side effect  

---

## Related reading order

```
Day 03 Decorator intro (SOLID)
  → Day 05 Scrutor snippet
  → Day 18 Modular DI registration
  → Day 21/23 Outbox/Inbox tables
  → Day 24 (inja) full Decorate mechanics
```

---

*Day 24 tamum. Ba'd: Day 25 — HybridCache + Redis (amade). Fehrest: [README.md](./README.md).*
