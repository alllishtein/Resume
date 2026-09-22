# Day 11 — CQRS + MediatR + Pipeline Behaviors

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

CQRS mige read va write ra joda kon. MediatR in joda kardan ra implement mikone: command/query → pipeline behavior-ha → handler. Pipeline behavior mesle middleware-e vali baraye use case-ha (na HTTP). Dejban 3 behavior dare: Exception → Logging → Validation. Microservice-ha faghat Validation daran. In fasl kole flow ra trace mikone: az HTTP request ta response.

---

# BAKHSH-E AVAL: WORLD — CQRS + MediatR to donya

## CQRS chie?

**Command Query Responsibility Segregation.** Do ta model joda:

| | Command (Write) | Query (Read) |
|---|---|---|
| **chi mikone** | state avaz mikone | data barmigardone |
| **return** | success/error | data |
| **side effect** | bale (DB change, event) | na |
| **validation** | bale (business rules) | minimal |
| **cache** | na | bale |
| **example** | CreatePersonnel, DeleteVisitor | GetPersonnels, GetVisitorById |

### Chera CQRS?

1. **Responsibility separation** — write logic complex, read logic optimized. Mix nakonid
2. **Independent optimization** — write model: rich domain, validations. Read model: flat DTO, denormalized
3. **Scalability** — read traffic >> write traffic. Read ra joda scale kon (cache, read replica)
4. **Testability** — command test: state change. Query test: data shape

### Levels of CQRS

| level | chi | complexity |
|---|---|---|
| **Level 1** | Separate interfaces (ICommand vs IQuery) | low ← **Dejban inja** |
| **Level 2** | Separate models (write entity vs read DTO) | medium |
| **Level 3** | Separate databases (write DB vs read DB) | high |
| **Level 4** | Event sourcing (write = events, read = projections) | very high |

Dejban Level 1 — same DB, same entities, vali command/query type system enforce mishe.

---

## MediatR chie?

Mediator design pattern. **Request** miad, MediatR **handler** ra peida mikone va seda mizane. Caller handler ra nemishine — loose coupling.

```
Endpoint → ISender.Send(command) → MediatR → Handler → Result
```

**Bedune MediatR:**
```csharp
// ❌ Controller direct dependency
public class VisitorController(
    IVisitorRepository repo,
    IUnitOfWork uow,
    IEventBus bus,
    IDccClient dcc) { ... }  // 10+ dependencies
```

**Ba MediatR:**
```csharp
// ✅ Controller only knows ISender
public class VisitorController(ISender sender)
{
    [HttpPost]
    public async Task<IResult> Create(CreateVisitorCommand cmd)
        => (await sender.Send(cmd)).Match(Results.Ok, Problem);
}
```

**Maziat:**
- Endpoint az handler details bikhabar-e
- Handler testable (mock dependencies)
- Cross-cutting concern (validation, logging) to pipeline behavior
- Swap handler implementation bedune endpoint change

---

## Pipeline Behavior chie?

Mesle **middleware** vali baraye MediatR request-ha. Har request az chain-e behavior-ha rad mishe ghabl (va ba'd) az handler.

```
Request → Behavior1 → Behavior2 → Behavior3 → Handler → Response
           (outer)      (mid)       (inner)
```

```csharp
public class MyBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,  // next behavior ya handler
        CancellationToken cancellationToken)
    {
        // BEFORE handler
        var response = await next();
        // AFTER handler
        return response;
    }
}
```

**Register order = execution order:** aval register = outermost ring.

```csharp
config.AddOpenBehavior(typeof(ExceptionBehavior<,>));   // 1st: outermost
config.AddOpenBehavior(typeof(LoggingBehavior<,>));      // 2nd
config.AddOpenBehavior(typeof(ValidationBehavior<,>));   // 3rd: closest to handler
```

**Flow:**
```
Exception wraps → Logging wraps → Validation wraps → Handler
                                                        ↓
                                                     result
                                                        ↓
                                   Validation passes ←──┘
                              Logging logs result ←──────┘
                         Exception catches if thrown ←────┘
```

---

## Open Generic Registration

`AddOpenBehavior(typeof(ValidationBehavior<,>))` — **open generic**. MediatR automatically closes the generic baraye har request type:

```
ValidationBehavior<CreatePersonnelCommand, ErrorOr<Guid>>
ValidationBehavior<DeleteVisitorCommand, ErrorOr<Success>>
ValidationBehavior<GetVisitorsQuery, ErrorOr<PagedList<object>>>
```

Yek class, hame request-ha.

---

## ISender vs IMediator vs IPublisher

| interface | chi | use case |
|---|---|---|
| `ISender` | `Send(IRequest<T>)` — yek handler | command/query dispatch |
| `IPublisher` | `Publish(INotification)` — chand handler | domain event broadcast |
| `IMediator` | har do | legacy, prefer `ISender` |

**Best practice:** `ISender` baraye command/query. `IPublisher` baraye notification. `IMediator` na lazem (too broad).

---

## INotification (MediatR Notification)

```csharp
public record OrderPlaced(Guid OrderId) : INotification;

public class SendEmailHandler : INotificationHandler<OrderPlaced>
{
    public Task Handle(OrderPlaced notification, CancellationToken ct) { ... }
}

public class UpdateStockHandler : INotificationHandler<OrderPlaced>
{
    public Task Handle(OrderPlaced notification, CancellationToken ct) { ... }
}

// Publish → BOTH handlers run
await publisher.Publish(new OrderPlaced(orderId));
```

**Send vs Publish:**
- `Send` → **exactly one** handler. Return value. Command/Query.
- `Publish` → **zero to many** handlers. No return. Notification/Event.

---

## ErrorOr + MediatR

`ErrorOr<T>` = ye type ke ya **result** dare ya **error list**. Alternative to exceptions baraye expected errors.

```csharp
public interface ICommand : IRequest<ErrorOr<Success>>;
public interface ICommand<T> : IRequest<ErrorOr<T>>;
public interface IQuery<T> : IRequest<ErrorOr<T>>;
```

```csharp
// Handler:
if (user == null) return UserErrors.NotFound(id);  // error path
return user.Id;                                      // success path (implicit conversion)

// Endpoint:
result.Match(
    value => Results.Ok(value),      // success
    errors => ApiResults.Problem(errors)  // error → ProblemDetails
);
```

**Chera ErrorOr (na exception)?**
- Exception = unexpected (bug, network fail). Stack trace, heavy.
- ErrorOr = expected (not found, validation fail). Lightweight, type-safe.
- Pipeline behavior mitone error check kone bedune try/catch.

---

## Unit of Work — koja SaveChanges seda mishe?

**Do approach:**

| approach | chi | Dejban? |
|---|---|---|
| **Handler-level** | Handler khodesh `SaveChangesAsync()` seda mizane | ✅ bale |
| **Behavior-level** | `UnitOfWorkBehavior` automatic save ba'd az handler | ❌ na |

**Dejban handler-level:**
```csharp
public async Task<ErrorOr<Guid>> Handle(CreateCommand cmd, CancellationToken ct)
{
    repo.Insert(entity);
    await unitOfWork.SaveChangesAsync(ct);  // explicit
    return entity.Id;
}
```

**Handler-level behtar chon:** control dare. Chand SaveChanges to yek handler (multi-step). Error handling ghabl az save.

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **Separate read database** (CQRS Level 3) — Dejban same DB baraye read/write
- **Event sourcing** (CQRS Level 4) — state az event rebuild. Dejban CRUD
- **`UnitOfWorkBehavior`** — automatic save. Dejban explicit
- **`IStreamRequest<T>`** — MediatR streaming. Dejban estefade nakarde
- **`RequestPreProcessor` / `RequestPostProcessor`** — MediatR hooks. Dejban behavior estefade karde
- **Custom `MediatR.Pipeline` behaviors** — caching behavior, transaction behavior
- **Wolverine / Brighter** — alternatives to MediatR. Dejban MediatR
- **Decorrelation ID behavior** — trace ID propagation via behavior
- **Idempotency behavior** — duplicate command check. Dejban idempotent to outbox/inbox, na behavior
- **Authorization behavior** — permission check to behavior. Dejban endpoint filter estefade karde

---

# BAKHSH-E DOVOM: DEJBAN — CQRS + MediatR to in proje

## MediatR registration — Dejban vs Microservices

### Dejban — 3 behavior, multi-assembly

```csharp
// File: Dejban.Common.Application/ApplicationConfiguration.cs

services.AddMediatR(config =>
{
    config.RegisterServicesFromAssemblies(moduleAssemblies);  // 8 module assemblies

    config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
    config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
    config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
});

services.AddValidatorsFromAssemblies(moduleAssemblies, includeInternalTypes: true);
```

### Microservices — 1 behavior, single assembly

```csharp
// File: ACLServer/Abstractions/Extensions/ServiceCollectionExtensions.cs
// (Same pattern: DCC, IdentityServer, RequestTracker, Reporting)

services.AddMediatR(config =>
{
    config.RegisterServicesFromAssemblyContaining<ApplicationAssemblyReference>();
    config.AddOpenBehavior(typeof(ValidationBehavior<,>));
});
```

### GateServer — na behavior

```csharp
services.AddMediatR(config =>
{
    config.RegisterServicesFromAssemblyContaining<ApplicationAssemblyReference>();
    // na behavior!
});
```

| | Dejban | Microservices | GateServer |
|---|---|---|---|
| Behaviors | 3 (Exception→Log→Validation) | 1 (Validation) | 0 |
| ICommand/IQuery | ✅ custom interfaces | ❌ direct IRequestHandler | ✅ custom (no ErrorOr) |
| ErrorOr | ✅ | ✅ | ❌ |
| Assembly scan | multi (8 modules) | single | single |

---

## Command/Query interfaces

### ICommand — write

```csharp
// File: Dejban.Common.Application/Messaging/ICommand.cs

public interface ICommand : IRequest<ErrorOr<Success>>, IBaseCommand;
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IBaseCommand;  // marker for pipeline behavior constraint
```

```csharp
// File: Dejban.Common.Application/Messaging/ICommandHandler.cs

public interface ICommandHandler<in TCommand>
    : IRequestHandler<TCommand, ErrorOr<Success>>
    where TCommand : ICommand;

public interface ICommandHandler<in TCommand, TResponse>
    : IRequestHandler<TCommand, ErrorOr<TResponse>>
    where TCommand : ICommand<TResponse>;
```

### IQuery — read

```csharp
// File: Dejban.Common.Application/Messaging/IQuery.cs

public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

```csharp
// File: Dejban.Common.Application/Messaging/IQueryHandler.cs

public interface IQueryHandler<in TQuery, TResponse>
    : IRequestHandler<TQuery, ErrorOr<TResponse>>
    where TQuery : IQuery<TResponse>;
```

**Key:** `IBaseCommand` marker → `ValidationPipelineBehavior` constraint: `where TRequest : IBaseCommand`. Validation faghat roye **command** run mishe, na query.

---

## Pipeline Behaviors — 3 implementation

### 1. ExceptionHandlingPipelineBehavior (outermost)

```csharp
// File: Dejban.Common.Application/Behaviors/ExceptionHandlingPipelineBehavior.cs

internal sealed class ExceptionHandlingPipelineBehavior<TRequest, TResponse>(
    ILogger<ExceptionHandlingPipelineBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : class
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        try
        {
            return await next();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Unhandled exception for {RequestName}",
                typeof(TRequest).Name);

            throw new DejbanException(typeof(TRequest).Name, innerException: exception);
        }
    }
}
```

**Chi mikone:** Hame-ye unhandled exception-ha ra catch mikone, log mikone, va `DejbanException` wrap mikone. Global exception handler (Day 08) in ra catch mikone va ProblemDetails barmigardone.

**Constraint:** `TRequest : class` — hame-ye request-ha (command + query).

### 2. RequestLoggingPipelineBehavior

```csharp
// File: Dejban.Common.Application/Behaviors/RequestLoggingPipelineBehavior.cs

internal sealed class RequestLoggingPipelineBehavior<TRequest, TResponse>(
    ILogger<RequestLoggingPipelineBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : class
    where TResponse : IErrorOr
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        var requestName = typeof(TRequest).Name;
        logger.LogInformation("Processing request {RequestName}", requestName);

        var result = await next();

        if (result.IsError)
        {
            using (LogContext.PushProperty("Error", result.Errors, true))
            {
                logger.LogError("Completed request {RequestName} with error", requestName);
            }

            // OpenTelemetry tags
            Activity.Current?.SetTag("request.error", true);
            Activity.Current?.SetTag("request.error_type",
                result.Errors?.FirstOrDefault().Type.ToString());
        }
        else
        {
            logger.LogInformation("Completed request {RequestName}", requestName);
        }

        return result;
    }
}
```

**Chi mikone:** Log ghabl va ba'd az handler. Age `ErrorOr.IsError` → error log + OpenTelemetry tag. Trace correlation.

**Constraint:** `TResponse : IErrorOr` — faghat request-haei ke ErrorOr return mikonan.

### 3. ValidationPipelineBehavior (closest to handler)

```csharp
// File: Dejban.Common.Application/Behaviors/ValidationPipelineBehavior.cs

internal sealed class ValidationPipelineBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IBaseCommand      // ← FAGHAT command!
    where TResponse : IErrorOr
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        if (!validators.Any()) return await next();

        var context = new ValidationContext<TRequest>(request);
        var validationResults = await Task.WhenAll(
            validators.Select(v => v.ValidateAsync(context, cancellationToken)));

        var errors = validationResults
            .Where(r => !r.IsValid)
            .SelectMany(r => r.Errors)
            .ToList();

        if (errors.Count == 0) return await next();

        // Convert FluentValidation errors → ErrorOr errors
        return TryCreateResponseFromErrors(errors, out var response)
            ? response
            : throw new ValidationException(errors);
    }

    private static bool TryCreateResponseFromErrors(
        List<ValidationFailure> failures, out TResponse response)
    {
        List<Error> errors = failures.ConvertAll(x => Error.Validation(
            code: string.IsNullOrWhiteSpace(x.PropertyName) ? x.ErrorCode : x.PropertyName,
            description: x.ErrorMessage));

        response = (TResponse?)typeof(TResponse)
            .GetMethod(nameof(ErrorOr<object>.From),
                BindingFlags.Static | BindingFlags.Public,
                types: [typeof(List<Error>)])?
            .Invoke(null, [errors])!;

        return response is not null;
    }
}
```

**Chi mikone:**
1. Hame-ye `IValidator<TRequest>` ra resolve mikone (DI → FluentValidation)
2. Hamaro run mikone (`Task.WhenAll` — parallel)
3. Error hast → convert to `ErrorOr<T>` error via reflection → **short-circuit** (handler run nemishe)
4. Error nist → `next()` → handler run mishe

**Constraint:** `TRequest : IBaseCommand` — **faghat command validate mishe**. Query skip mishe. Chon query side-effect nadare, validation kam lazem-e.

**Reflection trick:** `ErrorOr<T>.From(List<Error>)` ra ba reflection seda mizane chon `TResponse` generic-e va compile-time type-esh maloom nist.

### Microservice ValidationBehavior — fargh

```csharp
// File: ACLServer/Abstractions/Behaviors/ValidationBehavior.cs

// Constraint: TRequest : IRequest<TResponse> (na IBaseCommand)
// → validation roye HAME request-ha run mishe (command + query)
```

5 ta microservice (ACL, DCC, Identity, RequestTracker, Reporting) hame **copy-paste** haman code hastan ba in fargh.

---

## Command handler examples

### Simple create — Asset

```csharp
// File: Armory.Application/Assets/CreateAssets/CreateAssetCommandHandler.cs

// Command:
public sealed record CreateAssetCommand(
    Guid SiteId, Guid AssetDefinitionId,
    string Serial, string Status, int Quantity) : ICommand<Guid>;

// Handler:
public sealed class CreateAssetCommandHandler(
    IAssetRepository assetRepository,
    ISiteRepository siteRepository,
    IAssetsDefinationsRepository defRepo,
    IUnitOfWork unitOfWork) : ICommandHandler<CreateAssetCommand, Guid>
{
    public async Task<ErrorOr<Guid>> Handle(CreateAssetCommand request, CancellationToken ct)
    {
        // 1. Validate references exist
        var site = await siteRepository.GetAsync(request.SiteId);
        if (site == null) return SiteErrors.NotFound(request.SiteId);

        var def = await defRepo.GetAsync(request.AssetDefinitionId);
        if (def == null) return AssetDefinitionError.NotFound(request.AssetDefinitionId);

        // 2. Domain factory (validation inside)
        var result = Asset.Create(request.SiteId, request.AssetDefinitionId,
            request.Serial, request.Status, request.Quantity);
        if (result.IsError) return result.Errors;

        // 3. Persist + outbox
        assetRepository.Insert(result.Value);
        await unitOfWork.SaveChangesAsync(ct);

        // 4. Return ID
        return result.Value.Id;
    }
}
```

**Pattern:** Validate refs → Domain factory → Persist → Return.

### Domain event publish — Personnel

```csharp
// Handler:
Personnel.CreateAsync(...) internally calls:
    personnel.Raise(new PersonnelCreatedDomainEvent(personnel.Id));

personnelRepository.Insert(personnel);
await unitOfWork.SaveChangesAsync(ct);
// ↑ InsertOutboxMessagesInterceptor captures event → outbox table (same tx)

// Later (Quartz job):
PersonnelCreatedDomainEventHandler:
    → sender.Send(GetPersonnelQuery)     // re-query full data
    → eventBus.PublishAsync(PersonnelCreated)  // integration event → RabbitMQ
```

### Complex validation — CheckInVisit

```csharp
// 313 lines! Key checks:
// - Reservation exists?
// - Status == approved?
// - Visitor not blacklisted?
// - Door assigned?
// - Card valid and not expired?
// - All visitors have required documents?
// - Time window valid?
// Each check → return specific Error (na exception)
```

### External service — DCC file upload

```csharp
// Upload visitor document:
var uploadResult = await dccHttpClient.UploadFileAsync(file, ct);
if (uploadResult.IsError) return uploadResult.Errors;

visitor.AddDocument(uploadResult.Value.FileId, ...);
await unitOfWork.SaveChangesAsync(ct);
return new VisitorDocumentResponse(uploadResult.Value);
```

---

## Query handler examples

### Simple get-by-id

```csharp
// File: Personnels.Application/Personnels/GetPersonnel/GetPersonnelQueryHandler.cs

// Query:
public sealed record GetPersonnelQuery(Guid PersonnelId) : IQuery<object>;

// Handler:
public sealed class GetPersonnelQueryHandler(
    IPersonnelRepository repo) : IQueryHandler<GetPersonnelQuery, object>
{
    public async Task<ErrorOr<object>> Handle(GetPersonnelQuery query, CancellationToken ct)
    {
        var personnel = await repo.GetDetailedAsync(query.PersonnelId, ct);
        if (personnel == null) return PersonnelErrors.NotFound(query.PersonnelId);

        return new { personnel.Id, personnel.FirstName, /* ... */ };
    }
}
```

### Paginated list with filter/sort

```csharp
// File: Personnels.Application/Personnels/GetPersonnels/GetPersonnelsQueryHandler.cs

// Filter map: string → Expression
private readonly Dictionary<string, Expression<Func<Personnel, object>>> _filterMap = new()
{
    ["personnelcode"] = p => p.PersonnelCode,
    ["firstname"] = p => p.FirstName,
    ["lastname"] = p => p.LastName,
    ["nationalcode"] = p => p.NationalCode,
};

// Sort map: string → Expression
private readonly Dictionary<string, Expression<Func<Personnel, object>>> _sortMap = new()
{
    ["personnelcode"] = p => p.PersonnelCode,
    // ...
};

// Handler:
var query = repo.GetAllQueryable()
    .ApplyFilters(request.Filters, _filterMap)
    .ApplySorting(request.SortBy, request.SortOrder, _sortMap);

return await PagedList<object>.CreateAsync(query.Select(p => new { ... }), request.Page, request.PageSize);
```

**Pattern:** Dictionary-based filter/sort dispatch (O(1) lookup, Day 07) → IQueryable composition → PagedList.

### Projection (Select) — dropdown

```csharp
// File: Personnels.Application/GetSelectPersonnels/GetSelectPersonnelsQueryHandler.cs

// Slim projection for dropdowns (na full entity):
return await repo.GetAllQueryable()
    .Where(p => !p.IsDeleted)
    .Select(p => new {
        p.Id,
        FullName = p.FirstName + " " + p.LastName,
        p.Position.Name
    })
    .ToListAsync(ct);
```

**Pattern:** `Select` ghabl az `ToListAsync` → SQL faghat column-haye lazem ra fetch mikone (na `SELECT *`).

---

## Notification pattern — do approach

### Approach 1: Dejban — custom (na MediatR INotification)

```
Entity.Raise(DomainEvent)
    → SaveChanges → outbox table
    → Quartz → DomainEventHandlersFactory → IDomainEventHandler<T>
```

`IDomainEventHandler<T>` → custom interface. MediatR `INotificationHandler` **nist**.

**Chera custom?** Outbox pattern lazem dare event dakhel-e transaction save beshe. MediatR `Publish` synchronous-e — age fail beshe, entity ham rollback mishe.

### Approach 2: RequestTracker / ACLServer — MediatR INotification

```csharp
// File: RequestTracker/Application/.../RequestCreatedDomainEvent.cs

public record RequestCreatedDomainEvent(Guid RequestId) : INotification;

// Handler:
public class RequestCreatedDomainEventHandler(...)
    : INotificationHandler<RequestCreatedDomainEvent>
{
    public async Task Handle(RequestCreatedDomainEvent notification, CancellationToken ct)
    {
        // Create tasks for first workflow step
    }
}

// Publisher (in command handler):
await publisher.Publish(new RequestCreatedDomainEvent(request.Id));
await context.SaveChangesAsync(ct);
```

**Mohem:** `Publish` **ghabl az** `SaveChanges` → age handler fail kone, SaveChanges aslan run **nemishe** → consistent. Vali in **in-process**-e — service down = event lost. (Dejban outbox in ra solve mikone.)

---

## ISender vs IMediator — usage

| | ISender | IMediator | IPublisher |
|---|---|---|---|
| method | `Send(IRequest<T>)` | `Send` + `Publish` | `Publish(INotification)` |
| Dejban endpoints | ✅ | ❌ | ❌ |
| Dejban domain event handlers | ✅ (re-query) | ❌ | ❌ |
| Microservice controllers | ✅ | ❌ | ❌ |
| RequestTracker commands | ✅ | ❌ | ✅ (domain events) |
| GateServer (legacy) | ❌ | ✅ | ❌ |

**Convention:** `ISender` baraye command/query. `IPublisher` baraye notification. `IMediator` = legacy.

---

## ErrorOr — kole flow

### Return values

```csharp
// Success with data:
return entity.Id;                    // implicit ErrorOr<Guid>
return new { Name = "Ali" };         // implicit ErrorOr<object>

// Success without data:
return Result.Success;               // ErrorOr<Success>
return Result.Updated;               // IdentityServer pattern
return Result.Deleted;               // RequestTracker pattern

// Error:
return PersonnelErrors.NotFound(id); // ErrorOr<T> with error
return result.Errors;                // forward errors from inner call
```

### Error definition

```csharp
public static class PersonnelErrors
{
    public static Error NotFound(Guid id) =>
        Error.NotFound("Personnel.NotFound", $"Personnel {id} not found");

    public static Error DuplicateCode(string code) =>
        Error.Conflict("Personnel.DuplicateCode", $"Code {code} already exists");
}
```

### HTTP mapping

```csharp
// File: Dejban.Common.Presentation/Results/ApiResults.cs

// ErrorType → HTTP status:
// Validation  → 400
// NotFound    → 404
// Conflict    → 409
// Unauthorized → 401
// Forbidden   → 403
// Failure     → 500

// Endpoint:
result.Match(
    value => Results.Ok(value),
    errors => ApiResults.Problem(errors)
);
```

### Pipeline behavior ErrorOr handling

```
ValidationBehavior:
    errors → ErrorOr.From(List<Error>) → return (no handler call)
    no errors → next() → handler

LoggingBehavior:
    result = next()
    result.IsError? → log error + OTel tag
    return result (unchanged)

ExceptionBehavior:
    try { next() } catch → DejbanException → ExceptionHandler → 500
```

---

## Request/Response flow — full trace

### POST `/api/v1/Personnels/Create`

```
HTTP Request (JSON body)
    ↓
1. YARP Gateway → route to Dejban.Api
    ↓
2. Middleware pipeline (CORS → Auth → Tenant → ...)
    ↓
3. CreatePersonnel endpoint (Presentation)
   ┌──────────────────────────────────────────────┐
   │ app.MapPost("/api/v1/Personnels/Create",     │
   │   async (CreatePersonnelCommand cmd,         │
   │          ISender sender) =>                   │
   │   {                                           │
   │     var result = await sender.Send(cmd);     │
   │     return result.Match(                      │
   │       Results.Ok,                             │
   │       ApiResults.Problem);                    │
   │   })                                          │
   └──────────────────────┬───────────────────────┘
                          ↓
4. MediatR pipeline:
   ┌──────────────────────────────────────────────┐
   │ ExceptionHandlingBehavior                     │
   │   try {                                       │
   │     ┌────────────────────────────────────┐   │
   │     │ RequestLoggingBehavior              │   │
   │     │   log "Processing CreatePersonnel" │   │
   │     │   ┌────────────────────────────┐   │   │
   │     │   │ ValidationBehavior          │   │   │
   │     │   │   validators.ValidateAsync()│   │   │
   │     │   │   errors? → return ErrorOr  │   │   │
   │     │   │   no errors ↓               │   │   │
   │     │   │   ┌────────────────────┐   │   │   │
   │     │   │   │ Handler             │   │   │   │
   │     │   │   │ - validate refs     │   │   │   │
   │     │   │   │ - Personnel.Create()│   │   │   │
   │     │   │   │ - repo.Insert()     │   │   │   │
   │     │   │   │ - UoW.SaveChanges() │   │   │   │
   │     │   │   │   ↳ outbox write    │   │   │   │
   │     │   │   │ - return id         │   │   │   │
   │     │   │   └────────────────────┘   │   │   │
   │     │   │   result ok? pass through  │   │   │
   │     │   └────────────────────────────┘   │   │
   │     │   log "Completed CreatePersonnel"  │   │
   │     └────────────────────────────────────┘   │
   │   } catch → DejbanException                   │
   └──────────────────────┬───────────────────────┘
                          ↓
5. result.Match(Results.Ok, ApiResults.Problem)
    ↓
HTTP 200 { "id": "..." }   ya   HTTP 400/404/409 ProblemDetails
    ↓
6. (Async, later) Quartz ProcessOutboxJob:
   outbox_messages → PersonnelCreatedDomainEventHandler
     → ISender.Send(GetPersonnelQuery) → full data
     → IEventBus.PublishAsync(PersonnelCreated) → RabbitMQ
```

---

## SaveChanges — handler-level (na behavior)

```csharp
// Pattern to HAME-ye Dejban handlers:

public async Task<ErrorOr<Guid>> Handle(CreateCommand cmd, CancellationToken ct)
{
    // 1. Business logic
    var entity = Entity.Create(...);
    if (entity.IsError) return entity.Errors;

    // 2. Persist
    repo.Insert(entity.Value);
    await unitOfWork.SaveChangesAsync(ct);
    // ↑ InsertOutboxMessagesInterceptor:
    //   - Extract DomainEvents from ChangeTracker
    //   - Serialize to outbox_messages table
    //   - Same transaction as entity insert

    // 3. Return
    return entity.Value.Id;
}
```

**Na UnitOfWorkBehavior:** Transaction boundary explicit-e. Handler decide mikone **kei** save kone. Chand SaveChanges to yek handler momken-e (masalan: create entity → save → upload file → update entity → save).

---

## GateServer — legacy pattern (bedune ErrorOr)

```csharp
// File: GateServer/Application/Shared/CqrsPattern/ICommand.cs

public interface ICommand<out TResult> : IRequest<TResult> { }

// Handler returns plain object (na ErrorOr):
public class GetGateLabelsHandler : IQueryHandler<GetGateLabelsQuery, List<GateLabelDto>>
{
    public async Task<List<GateLabelDto>> Handle(...) { ... }
}
```

**Na ErrorOr, na pipeline behavior, IMediator inject mishe.** Legacy code ke refactor nashode.

---

## Smell-ha

1. **Validation faghat roye command (Dejban)** — query skip mishe. Vali microservice-ha hame validate mikonan
2. **5 copy-paste ValidationBehavior** — ACL, DCC, Identity, RT, Reporting hame copy hastan. Bayad shared bashe
3. **GateServer na ErrorOr, na behavior** — inconsistent ba baghie
4. **Reflection to ValidationBehavior** — `ErrorOr<T>.From` via reflection. Fragile, slow
5. **Na UnitOfWorkBehavior** — explicit save ok, vali developer forget risk
6. **Na caching behavior** — query result cache to behavior. Dejban nadare
7. **Na authorization behavior** — permission check to endpoint filter, na behavior
8. **Na idempotency behavior** — duplicate command detection to behavior. Dejban to outbox dare
9. **Domain event handler exception → DejbanException** — swallow ya retry?
10. **`object` return type to query handler** — `ErrorOr<object>` anonymous type = na type-safe
11. **IPublisher ghabl az SaveChanges (RequestTracker)** — handler fail → event already dispatched → inconsistent
12. **Na streaming (IStreamRequest)** — large list query-ha kole result load mikonan

---

## 20 soal-e mosahebe

1. **CQRS chie?** — Command Query separation. Write ≠ Read model
2. **MediatR chie?** — Mediator pattern. Send request → find handler → execute. Loose coupling
3. **Pipeline behavior chie?** — Middleware baraye MediatR. Before/after handler. Validation, logging, exception
4. **AddOpenBehavior order?** — Aval register = outermost. Akhar = closest to handler
5. **ISender vs IMediator?** — ISender slim (Send only). IMediator broad (Send + Publish). Prefer ISender
6. **INotification chie?** — Multi-handler event. Publish → all handlers run. Na return value
7. **ErrorOr chie? Chera na exception?** — Expected errors as values. Lightweight, type-safe. Exception = unexpected
8. **ValidationBehavior chejori kar mikone?** — FluentValidation → errors → ErrorOr.From → short-circuit
9. **Chera validation faghat roye command?** — Query side-effect nadare. Command state avaz mikone → validate lazem
10. **UnitOfWork to behavior ya handler?** — Handler (Dejban). Control over when to save. Multi-step support
11. **Domain event dispatch kei mishe?** — Dejban: outbox (async, reliable). RT: IPublisher (sync, in-process)
12. **Chera outbox na IPublisher?** — Outbox same transaction = reliable. IPublisher = fail possible
13. **Factory method + ErrorOr?** — `Entity.Create()` → `ErrorOr<Entity>`. Validation inside domain
14. **Query handler caching?** — Dejban behavior nadare. Manually ya HybridCache
15. **Chejori test mikoni?** — Handler: mock repos + unit test. Behavior: mock next() delegate
16. **Request/Response flow?** — Endpoint → ISender → Behaviors chain → Handler → ErrorOr → Match → HTTP
17. **Open generic chie?** — `Behavior<,>` → MediatR closes per request type. Yek class, hame requests
18. **ErrorOr vs Result pattern?** — ErrorOr: multiple errors, typed. Result: single, simple. Both avoid exceptions
19. **Chera MediatR na direct injection?** — Loose coupling. Cross-cutting via behaviors. Swap handler easy
20. **Streaming?** — `IStreamRequest<T>` → `IAsyncEnumerable`. Dejban estefade nakarde

---

## Resume

**short:**

> Implemented CQRS pattern via MediatR across a modular monolith (8 modules) and 7 microservices, with 3 pipeline behaviors (exception handling, structured logging with OpenTelemetry, FluentValidation) and ErrorOr-based error handling — eliminating exception-driven control flow for expected business errors.

**bullets:**

- Designed ICommand/IQuery type system with ErrorOr<T> return types, enforcing command-query separation at compile time via marker interfaces
- Built 3-stage MediatR pipeline: ExceptionHandling (catch + wrap) → RequestLogging (Serilog + OTel tags) → Validation (FluentValidation → ErrorOr short-circuit without exceptions)
- Implemented outbox-based domain event dispatch: entity raises event → outbox table (same transaction) → Quartz job → domain event handler → integration event publish
- Created dictionary-based filter/sort dispatch for paginated query handlers with IQueryable composition and PagedList

**skills:** `CQRS, MediatR, Pipeline Behaviors, FluentValidation, ErrorOr, Domain Events, Outbox Pattern, Command/Query Separation, Clean Architecture`

---

## File-haye mohem

| chi | koja |
|---|---|
| MediatR registration (Dejban) | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| MediatR registration (ACL) | `ACLServer/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| ICommand / ICommandHandler | `Dejban.Common.Application/Messaging/ICommand.cs` |
| IQuery / IQueryHandler | `Dejban.Common.Application/Messaging/IQuery.cs` |
| ExceptionHandlingBehavior | `Dejban.Common.Application/Behaviors/ExceptionHandlingPipelineBehavior.cs` |
| RequestLoggingBehavior | `Dejban.Common.Application/Behaviors/RequestLoggingPipelineBehavior.cs` |
| ValidationPipelineBehavior | `Dejban.Common.Application/Behaviors/ValidationPipelineBehavior.cs` |
| ValidationBehavior (micro) | `ACLServer/Abstractions/Behaviors/ValidationBehavior.cs` |
| Simple create handler | `Armory.Application/Assets/CreateAssets/CreateAssetCommandHandler.cs` |
| Domain event handler | `Personnels.Application/CreatePersonnel/PersonnelCreatedDomainEventHandler.cs` |
| Complex command | `Visitors.Application/Visitors/CheckInVisit/CheckInVisitCommandHandler.cs` |
| Paginated query | `Personnels.Application/Personnels/GetPersonnels/GetPersonnelsQueryHandler.cs` |
| Projection query | `Personnels.Application/GetSelectPersonnels/GetSelectPersonnelsQueryHandler.cs` |
| FluentValidation | `Personnels.Application/CreatePersonnel/CreatePersonnelCommandValidator.cs` |
| ErrorOr mapping | `Dejban.Common.Presentation/Results/ApiResults.cs` |
| INotification (RT) | `RequestTracker/Application/.../RequestCreatedDomainEvent.cs` |
| INotification (ACL) | `ACLServer/Application/*SDKEventHandlers/` |
| DomainEvent base | `Dejban.Common.Domain/DomainEvent.cs` |
| DomainEventHandler | `Dejban.Common.Application/Messaging/DomainEventHandler.cs` |
| Outbox interceptor | `Dejban.Common.Infrastructure/Outbox/InsertOutboxMessagesInterceptor.cs` |
| GateServer legacy CQRS | `GateServer/Application/Shared/CqrsPattern/` |

---

*Day 11 tamum. Ba'd: Day 12 — DDD (aggregate, domain event, value object). Fehrest: [README.md](./README.md).*
