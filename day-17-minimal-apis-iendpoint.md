# Day 17 — Minimal APIs + `IEndpoint`

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Dejban API = **Minimal APIs**, na MVC Controllers. Har HTTP route ye class-e koochik `internal sealed class X : IEndpoint` ba method `MapEndpoint` — dakhelesh `app.MapGet/Post/...` + MediatR `ISender.Send` + `ErrorOr.Match(Results.Ok, ApiResults.Problem)`. Discovery automatic: har module `services.AddEndpoints(Presentation.Assembly)` → reflection hame `IEndpoint` ha ra `Transient` register mikone; `Program` faghat `app.MapEndpoints()` seda mizane. In **OCP**: endpoint jadid = class jadid, **Program avaz nemishe**. Versioning URL (`/api/v{version}`), tags, auth, form upload, endpoint filters (`RequirePermissions`, `RequireSiteAccess`) — hame roye `RouteHandlerBuilder` chain. Standalone services (Identity/ACL/…) ziad **Controllers** daran — do style dar org.

---

# BAKHSH-E AVAL: WORLD — Minimal APIs to donya

## Tarikhche-ye kootah

| doran | style |
|---|---|
| ASP.NET classic | WebForms / ASHX |
| ASP.NET MVC | Controllers + Actions |
| Web API 2 / Core MVC | `[ApiController]` + `ControllerBase` |
| .NET 6+ | **Minimal APIs** — functional route mapping |
| Community | Carter, FastEndpoints, vertical slices |

Minimal API = kam boilerplate, az code-behin route, DI parameter injection, `IResult` return.

**Controller nemorde** — hanooz ghavi baraye complex model binding, filters attribute-based, team-haye MVC-first. Vali greenfield microservice / modular often Minimal.

---

## Minimal API chie? (hello world)

```csharp
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/hello", () => "world");
app.MapGet("/hello/{name}", (string name) => $"hello {name}");
app.MapPost("/orders", (CreateOrderDto dto) => Results.Created($"/orders/{dto.Id}", dto));

app.Run();
```

Bedune Controller class. Route + handler lambda (ya method group).

### Verb helpers

```csharp
app.MapGet(...)
app.MapPost(...)
app.MapPut(...)
app.MapPatch(...)
app.MapDelete(...)
app.MapMethods("/x", ["GET", "HEAD"], handler)
app.Map("/", ...) // all methods — rare
```

---

## Parameter binding — az koja miad?

| source | chejori |
|---|---|
| Route | `{id:guid}` → `Guid id` |
| Query | `?page=1` → `int page` or complex |
| Header | `[FromHeader] string x` |
| Body JSON | complex type (POST/PUT) automatic |
| Form | `[FromForm] T` + `IFormFile` |
| Services | `ISender sender` — DI |
| HttpContext | `HttpContext httpContext` |
| Cancellation | `CancellationToken ct` → RequestAborted |
| AsParameters | flatten record/query object |

```csharp
app.MapGet("/items", async (
    [AsParameters] GetItemsQuery query,  // bind all props from query/route
    ISender sender,
    CancellationToken ct) =>
{
    return await sender.Send(query, ct);
});
```

**Route constraints:** `{id:guid}`, `{version:apiVersion}`, `{name:maxlength(50)}`.

---

## `IResult` va Results

```csharp
Results.Ok(value)           // 200
Results.Created(uri, value) // 201
Results.NoContent()         // 204
Results.BadRequest()        // 400
Results.ValidationProblem(dict)
Results.Unauthorized()      // 401
Results.Forbid()            // 403
Results.NotFound()          // 404
Results.Conflict()          // 409
Results.Problem(...)        // RFC 7807 ProblemDetails
Results.File(...) / Bytes / Stream
Results.Redirect(...)
```

`TypedResults.*` — generic compile-time metadata better for OpenAPI.

Minimal handler return types:
- `IResult`
- `Task<IResult>`
- raw object → framework wraps as Ok (sometimes) — prefer explicit `Results.*`

---

## Route groups

```csharp
var api = app.MapGroup("/api/v1/orders")
    .RequireAuthorization()
    .WithTags("Orders");

api.MapGet("/", ListOrders);
api.MapGet("/{id:guid}", GetOrder);
api.MapPost("/", CreateOrder);
```

Shared prefix + shared filters. Dejban **kam** az MapGroup estefade mikone — har endpoint full path minevise (duplication smell, vali clear).

---

## Middleware vs Endpoint Filter vs MediatR Behavior

```
HTTP request
  → Middleware pipeline (CORS, AuthN, AuthZ, Tenant, ExceptionHandler)
  → Endpoint selected
  → Endpoint Filters (per-route IEndpointFilter chain)
  → Route handler lambda
       → MediatR Send
            → Pipeline Behaviors (Validation, Logging, …)
            → Command/Query Handler
```

| layer | scope | mesal Dejban |
|---|---|---|
| Middleware | all requests | `UseTenantContext`, JWT |
| Endpoint filter | one/few routes | `RequirePermissions`, `RequireSiteAccess` |
| MediatR behavior | all Send() | FluentValidation |
| Handler | one use case | CreatePersonnelHandler |

**Ghalat:** business rule to endpoint filter. Filter = HTTP/auth cross-cutting. Business = handler/domain.

---

## `IEndpointFilter`

```csharp
public class PermissionRequirementFilter(HashSet<string> permissions) : IEndpointFilter
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        if (!context.HttpContext.User.Identity?.IsAuthenticated ?? true)
            return TypedResults.Unauthorized();

        if (!HasPermission(...))
            return TypedResults.Forbid();

        return await next(context); // continue chain → handler
    }
}

app.MapPost("/x", Handler)
    .AddEndpointFilter(new PermissionRequirementFilter(perms));
```

Extension sugar:

```csharp
.RequirePermissions("users/write")
.RequireSiteAccess()
.RequireRoles("Admin")
```

---

## Authorization on Minimal APIs

```csharp
.RequireAuthorization()                    // any authenticated
.RequireAuthorization("MyPolicy")          // named policy
.AllowAnonymous()                          // override
```

Attribute-style policies still work via metadata; filters common for site-scoped permission (need HttpContext header).

---

## API versioning

Strategies: URL segment, header, query.

```csharp
// URL segment — Dejban
options.ApiVersionReader = new UrlSegmentApiVersionReader();
// /api/v1/Personnels/...

app.NewApiVersionSet()
    .HasApiVersion(new ApiVersion(1, 0))
    .ReportApiVersions()
    .Build();

.MapToApiVersion(new ApiVersion(1, 0))
.WithApiVersionSet(versionSet)
```

Asp.Versioning package (ex Microsoft.AspNetCore.Mvc.Versioning evolution).

---

## OpenAPI / Scalar / Swagger

Minimal APIs + `AddOpenApi()` (.NET 9/10) + Scalar UI.

Metadata:
```csharp
.WithName("GetPersonnels")           // operationId / link generation
.WithTags("Personnels")              // group in docs
.WithDescription("...")
.WithMetadata(new EndpointDescriptionAttribute("FA title"))
.Accepts<T>("multipart/form-data")
.Produces<T>(200)
.ProducesProblem(404)
```

---

## Controllers vs Minimal — comparison

| | Controllers | Minimal APIs |
|---|---|---|
| Structure | class + many actions | 1 file ≈ 1 route (often) |
| Boilerplate | more | less |
| Test | controller unit test | filter/handler test; endpoint = integration |
| Filters | IActionFilter / attributes | IEndpointFilter |
| Model binding | mature | good + AsParameters |
| Familiarity | huge ecosystem | growing |
| Modular monolith | OK | **excellent** with IEndpoint scan |
| File upload | `[FromForm]` | same + DisableAntiforgery |

**Dejban choice:** Minimal + IEndpoint plugin for modular Presentation assemblies.

**Identity/ACL/RequestTracker/Reporting:** often Controllers — historical / team habit / MVC features.

---

## Vertical slice + endpoint-per-feature

```
Features/
  CreatePersonnel/
    CreatePersonnelCommand.cs
    CreatePersonnelHandler.cs
    CreatePersonnelValidator.cs
    CreatePersonnelEndpoint.cs   // IEndpoint
```

Dejban nazdik: Application folder per use case + Presentation `CreatePersonnel.cs` joda (layer folders, na pure vertical folder). Idea yeksan: **yek feature = yek endpoint class**.

Libraries:
- **Carter** — modules implement `ICarterModule` AddRoutes
- **FastEndpoints** — class per endpoint with HandleAsync
- **Dejban IEndpoint** — homemade Carter-like, simple

---

## Antiforgery + APIs

Browser form POST + cookies → CSRF risk → antiforgery tokens.

SPA Bearer token APIs usually CSRF-less for JSON. **Multipart form** from SPA still may hit antiforgery middleware.

```csharp
.DisableAntiforgery(); // Dejban on Create/Update personnel form endpoints
```

Understand why — without it, form upload 400 antiforgery.

---

## ProblemDetails (RFC 7807)

Standard error body:

```json
{
  "type": "...",
  "title": "Personnel.NotFound",
  "status": 404,
  "detail": "...",
  "instance": "DELETE /api/v1/Personnels/...",
  "requestId": "0H..."
}
```

`AddProblemDetails` + exception handler + `Results.Problem` / `ValidationProblem`.

FE axios `getErrorMessage` az in mikhone (Day 01/40).

---

## Testing endpoints

| level | chejori |
|---|---|
| Handler unit | mock repo — **prefer** (thin endpoint) |
| WebApplicationFactory | full HTTP integration |
| Filter unit | invoke filter with fake HttpContext |

Thin endpoint = test value to Application. Fat endpoint (logic in lambda) = hard / smell.

---

## Anti-patterns

1. **Fat lambda** — business logic to MapPost body
2. **DbContext inject to endpoint** — skip Application layer
3. **Copy-paste versionSet** 20 lines every file
4. **Inconsistent routes** — `/GetPersonnels` RPC-ish vs REST `/personnels`
5. **Forgot RequireAuthorization** — anonymous leak
6. **Sync over async** — `.Result` in lambda
7. **Ignoring CancellationToken**
8. **Returning domain entities** — leak; use DTO/response
9. **MapGroup never used** → path duplication / typo risk
10. **Controller + Minimal mixed** bedune convention doc

---

## Chizaei ke donya dare, Dejban kam/nist

- Shared `MapGroup("/api/v{version}/Personnels")` per module
- FastEndpoints / Carter library
- Endpoint generator source-gen
- Consistent REST resource naming (mix RPC `GetPersonnels` + REST `{id}`)
- `.Produces<T>()` everywhere for OpenAPI perfection
- Active `.RequirePermissions` on all mutating routes (many only `.RequireAuthorization()`; permission filters commented)

---

# BAKHSH-E DOVOM: DEJBAN — Minimal APIs + IEndpoint to in proje

## Contract

```csharp
// File: Dejban.Common.Presentation/Endpoints/IEndpoint.cs
namespace Dejban.Common.Presentation.Endpoints;

public interface IEndpoint
{
    void MapEndpoint(IEndpointRouteBuilder app);
}
```

Har Presentation class ke route tarif mikone in interface ra implement mikone.

---

## Discovery — `AddEndpoints` / `MapEndpoints`

```csharp
// File: Dejban.Common.Presentation/Endpoints/EndpointExtensions.cs

public static IServiceCollection AddEndpoints(
    this IServiceCollection services,
    params Assembly[] assemblies)
{
    ServiceDescriptor[] serviceDescriptors = [.. assemblies
        .SelectMany(a => a.GetTypes())
        .Where(type => type is { IsAbstract: false, IsInterface: false } &&
                       type.IsAssignableTo(typeof(IEndpoint)))
        .Select(type => ServiceDescriptor.Transient(typeof(IEndpoint), type))];

    services.TryAddEnumerable(serviceDescriptors);
    return services;
}

public static IApplicationBuilder MapEndpoints(
    this WebApplication app,
    RouteGroupBuilder? routeGroupBuilder = null)
{
    IEnumerable<IEndpoint> endpoints =
        app.Services.GetRequiredService<IEnumerable<IEndpoint>>();

    IEndpointRouteBuilder builder = routeGroupBuilder is null ? app : routeGroupBuilder;

    foreach (IEndpoint endpoint in endpoints)
        endpoint.MapEndpoint(builder);

    return app;
}
```

**Chejori kar mikone:**
1. Reflection: non-abstract classes assignable to `IEndpoint`
2. `TryAddEnumerable` — multiple registrations of same service type `IEndpoint`
3. Resolve `IEnumerable<IEndpoint>` → hame instances
4. Har kodom `MapEndpoint` → routes registered on app

**Lifetime** lifetime: endpoint mapper object short-lived at startup map time; handlers themselves are lambdas capturing DI per-request.

**OCP:** class `CreateFoo : IEndpoint` ezafe kon → assembly scan migire. `Program.cs` / `EndpointExtensions` **dast nemizani**.

~**380** `IEndpoint` implementations across Dejban modules.

---

## Module registration

```csharp
// PersonnelsModule.cs
services.AddEndpoints(Presentation.AssemblyReference.Assembly);
```

Har module Presentation assembly:

```csharp
// Presentation/AssemblyReference.cs
public static class AssemblyReference
{
    public static readonly Assembly Assembly = typeof(AssemblyReference).Assembly;
}
```

`Program.cs`:

```csharp
builder.Services.AddPersonnelsModule(...);
builder.Services.AddVisitorsModule(...);
// ... 8 modules — each AddEndpoints own assembly

// pipeline:
app.UseAuthentication();
app.UseAuthorization();
app.UseTenantContext();
app.MapEndpoints();  // ALL modules' endpoints
```

Optional `routeGroupBuilder` param — agar bekhay hame zir `/api` group; currently null = map on app root.

---

## Canonical endpoint template

```csharp
internal sealed class CreatePersonnel : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var versionSet = app.NewApiVersionSet()
            .HasApiVersion(new ApiVersion(1, 0))
            .ReportApiVersions()
            .Build();

        app.MapPost("/api/v{version:apiVersion}/Personnels/Create",
            async ([FromForm] CreatePersonnelCommand request, ISender sender) =>
            {
                var result = await sender.Send(request);
                return result.Match(Results.Ok, ApiResults.Problem);
            })
            .RequireAuthorization()
            .WithApiVersionSet(versionSet)
            .WithTags(Tags.Personnels)
            .WithMetadata(new EndpointDescriptionAttribute("پرسنل | ایجاد پرسنل"))
            .MapToApiVersion(new ApiVersion(1, 0))
            .DisableAntiforgery();
    }
}
```

**Anatomy:**
1. `internal sealed` — encapsulation; only DI via interface
2. Version set (repeated boilerplate)
3. `MapPost` + path with `apiVersion` constraint
4. Thin lambda: bind → `Send` → `Match`
5. Auth + OpenAPI metadata + antiforgery off for form

---

## Query list — `[AsParameters]`

```csharp
internal sealed class GetPersonnels : IEndpoint
{
    public void MapEndpoint(IEndpointRouteBuilder app)
    {
        var versionSet = /* ... */;

        app.MapGet("/api/v{version:apiVersion}/Personnels/GetPersonnels",
            async ([AsParameters] GetPersonnelsQuery request, ISender sender) =>
            {
                var result = await sender.Send(request);
                return result.Match(Results.Ok, ApiResults.Problem);
            })
            .RequireAuthorization()
            .WithApiVersionSet(versionSet)
            .WithTags(Tags.Personnels)
            .WithName("GetPersonnels")
            .WithMetadata(new EndpointDescriptionAttribute("پرسنل | لیست پرسنل"))
            .MapToApiVersion(new ApiVersion(1, 0));
    }
}
```

Query object properties ← query string (paging, filters). `WithName` for link generation / OpenAPI operationId.

---

## Delete — route id + audit from user

```csharp
app.MapDelete("/api/v{version:apiVersion}/Personnels/{personnelId:guid}",
    async (Guid personnelId, HttpContext httpContext, ISender sender) =>
    {
        var deletedBy = httpContext.User.Identity?.Name ?? "System";
        var command = new DeletePersonnelCommand(personnelId, deletedBy);
        var result = await sender.Send(command);
        return result.Match(_ => Results.NoContent(), ApiResults.Problem);
    })
```

- Success → **204 NoContent**
- Error → ProblemDetails
- Soft delete under the hood (Day 15)

---

## Update — form + files + route id merge

```csharp
app.MapPut("/api/v{version:apiVersion}/Personnels/{id}",
    async (
        Guid id,
        [FromForm] UpdatePersonnelCommand request,
        IFormFile? AvatarImage,
        IFormFile? SignatureImage,
        ISender sender) =>
    {
        request.PersonnelId = id;
        if (AvatarImage is not null) request.AvatarImage = AvatarImage;
        if (SignatureImage is not null) request.SignatureImage = SignatureImage;

        var result = await sender.Send(request);
        return result.Match(_ => Results.Ok(), ApiResults.Problem);
    })
    .Accepts<UpdatePersonnelCommand>("multipart/form-data")
    .DisableAntiforgery();
```

Endpoint allowed to **map HTTP shape → command** (id from route into command). Still no business rules.

---

## `ApiResults.Problem` — ErrorOr → HTTP

```csharp
// Dejban.Common.Presentation/Results/ApiResults.cs
public static IResult Problem(List<Error> errors)
{
    if (errors.Count is 0)
        return Results.Problem();

    if (errors.All(e => e.Type == ErrorType.Validation))
        return ValidationProblem(errors); // 400 + errors dictionary

    return Problem(errors[0]); // first error wins for non-validation
}

// Mapping:
// Validation → 400
// Unauthorized → 401
// Forbidden → 403
// NotFound → 404
// Conflict → 409
// Failure → 400
// else → 500
```

```csharp
result.Match(Results.Ok, ApiResults.Problem);
result.Match(_ => Results.NoContent(), ApiResults.Problem);
```

Identity Controllers: parallel `ApiController.Problem(List<Error>)` → `IActionResult`. Haman idea, do host styles.

Global:

```csharp
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddProblemDetails(options =>
{
    options.CustomizeProblemDetails = context =>
    {
        context.ProblemDetails.Instance =
            $"{context.HttpContext.Request.Method} {context.HttpContext.Request.Path}";
        context.ProblemDetails.Extensions.Add("requestId", context.HttpContext.TraceIdentifier);
    };
});
```

Unexpected exception → exception handler. Expected domain errors → ErrorOr + ApiResults (no exception).

---

## Versioning config (shared)

```csharp
// Common/.../AddApiVersioningAndExplorer
services.AddApiVersioning(options =>
{
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.ReportApiVersions = true;
    options.ApiVersionReader = new UrlSegmentApiVersionReader();
})
.AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";
    options.SubstituteApiVersionInUrl = true;
});
```

Called from `Dejban.Common.Infrastructure` (+ Identity, ACL, …).

Response headers may report supported versions. YARP path `{apiVersion}` segment match (Day 07) — versioning semantics = ASP.NET, na YARP.

---

## Tags (OpenAPI grouping)

```csharp
// Personnels.Presentation/Tags.cs
internal static class Tags
{
    internal const string Personnels = "Personnels";
    internal const string Doors = "Doors";
    internal const string Cameras = "Cameras";
    // ...
}
```

`.WithTags(Tags.Personnels)` → Scalar/OpenAPI group. Har module Tags class khodesh.

---

## Authorization filters (Common.Authorization)

```csharp
// Extension methods on RouteHandlerBuilder
.RequireSiteAccess()
.RequireEndpointAccess()
.RequireRoles("Admin")
.RequirePositions("Guard")
.RequirePermissions("users/write", "users/Delete")
```

Implementations = `IEndpointFilter`:
- `SiteAccessRequirementFilter` — header sites ⊆ JWT sites; empty header → Forbid
- `PermissionRequirementFilter` — site-scoped permission evaluator + header sites
- `EndpointAccessRequirementFilter` — claim endpoint access key vs request
- Role / Position filters

**Waqeiyat-e codebase:** ziad endpoints faghat `.RequireAuthorization()` (authenticated). Specifik permission lines sometimes **commented**:

```csharp
// .RequireSiteAccess()
// .AddEndpointFilter(new SiteAccessRequirementFilter())
// .RequirePermissions("users/read, users/write")
```

Tenant EF filter (Day 16) still isolates **data**. Permission filters = finer action control — partially adopted.

AuthN/AuthZ middleware order:

```
UseAuthentication → UseAuthorization → UseTenantContext → MapEndpoints
```

Endpoint filters run **after** endpoint match, inside auth'd pipeline.

---

## JSON options (Minimal binding)

```csharp
services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.Converters.Add(new StrictNullableGuidJsonConverter());
    // Strict DateTime, Guid, enum as string, IgnoreCycles...
});
```

Strict converters → bad GUID string = bind error, na silent Empty. Important for API hardness.

---

## SignalR / health / OpenAPI side-by-side

`MapEndpoints` only IEndpoint routes. Also:

```csharp
app.MapHealthChecks("health", ...);
app.MapOpenApi(); // dev
// SignalR hubs mapped elsewhere in infra
```

Health usually anonymous. Don't put business on health.

---

## Controllers dar org (contrast)

```csharp
// IdentityServer
[ApiController]
[Authorize]
public class ApiController : ControllerBase
{
    protected IActionResult Problem(List<Error> errors) { ... }
}

// derived controllers: MediatR Send + Match(Ok, Problem)
```

| service | style |
|---|---|
| **Dejban.Api** | Minimal + IEndpoint |
| IdentityServer | Controllers |
| ACLServer | Controllers (+ some) |
| RequestTracker | Controllers |
| Reporting | Controllers |
| GateServer | mix / device oriented |
| DCC | Controllers / minimal mix |

Resume: «modular monolith Minimal API endpoints; identity/ACL MVC controllers» — accurate.

---

## Full request walkthrough

```
FE: POST /api/v1/Personnels/Create
    Authorization: Bearer …
    X-Site-Id: {site}
    Content-Type: multipart/form-data

YARP → Dejban.Api

CORS → ExceptionHandler → Serilog → AuthN → AuthZ
→ TenantContextMiddleware (AsyncLocal sites)
→ Endpoint: CreatePersonnel MapPost matched
→ (optional endpoint filters)
→ lambda:
     bind CreatePersonnelCommand from form
     sender.Send(command)
       → ExceptionHandlingBehavior
       → LoggingBehavior
       → ValidationBehavior (FluentValidation)
       → CreatePersonnelCommandHandler
            repos + UoW Soft tenant filters apply
            return ErrorOr<Guid>
→ Match(Results.Ok, ApiResults.Problem)
→ 200 + id  |  400/404/409 ProblemDetails
```

---

## Presentation layer responsibilities (boundary)

**OK in IEndpoint:**
- HTTP method + path
- Bind route/query/form/header → command/query
- Map user identity → audit fields (`deletedBy`)
- `Send` + `Match` to status codes
- Auth metadata, OpenAPI metadata
- Antiforgery / accepts content-type

**NOT OK (push down):**
- EF queries
- Business invariants
- Direct `SaveChanges`
- Multi-step workflows without Application service/handler

Integration event handlers also live in Presentation assemblies (consume bus) — separate from IEndpoint but same project.

---

## Route naming style (honest)

Dejban mix:
- RPC-ish: `/Personnels/GetPersonnels`, `/Personnels/Create`
- REST-ish: `/Personnels/{personnelId:guid}` DELETE, `/Personnels/{id}` PUT

FE axios paths mirror these. Consistency secondary to stability. New endpoints: follow nearest module convention.

---

## MapGroup opportunity (refactor mental model)

Emruz:

```csharp
app.MapGet("/api/v{version:apiVersion}/Personnels/GetPersonnels", ...)
app.MapPost("/api/v{version:apiVersion}/Personnels/Create", ...)
```

Behtar (hypothetical):

```csharp
var group = app.MapGroup("/api/v{version:apiVersion}/Personnels")
    .WithApiVersionSet(versionSet)
    .RequireAuthorization()
    .WithTags(Tags.Personnels);

group.MapGet("/GetPersonnels", ...);
group.MapPost("/Create", ...);
```

Dejban hanuz per-endpoint full path — miduni tradeoff.

---

## Connection to other days

| day | rabt |
|---|---|
| 01 HTTP/REST | verbs, status, ProblemDetails |
| 03 OOP | IEndpoint = OCP plugin |
| 05 Pipeline | middleware vs filters vs behaviors |
| 06 JWT | RequireAuthorization |
| 07 YARP | `/api/v{version}/...` forward |
| 09 Architecture | Presentation layer |
| 10 CQRS/MediatR | ISender.Send |
| 11 ErrorOr | Match + ApiResults |
| 16 Tenancy | header before endpoint; filters SiteAccess |
| 18 Modular DI | AddXxxModule includes AddEndpoints |
| 33 OpenAPI+Scalar | metadata tags |
| 37 Permissions | RequirePermissions filters |
| 40 Auth E2E | FE calls these routes |

---

## Smell-ha

1. **VersionSet boilerplate** copied every endpoint file
2. **No MapGroup** — long duplicated prefixes
3. **RPC + REST mix** in paths
4. **Permission filters commented** — authz incomplete vs design
5. **DisableAntiforgery** broad on forms — OK for Bearer SPA; document threat model
6. **`ApiResults` first-error-only** for non-validation — multiple domain errors rare
7. **Failure → 400** (not 500) — intentional soft; ops may want distinguish
8. **Internal sealed endpoints** — good; but hard to find without knowing scan
9. **~380 endpoints** — discoverability needs Scalar tags + naming discipline
10. **UpdatePersonnel mutates request** (`PersonnelId = id`) — fine; avoid heavier logic
11. **WithName missing** on many routes — OpenAPI/links weaker
12. **Controllers vs Minimal** dual stack in org — onboarding cost
13. **Test.cs / commented endpoints** leftover noise
14. **RouteGroupBuilder param unused** in Program
15. **Transient IEndpoint** resolved once at MapEndpoints — OK; don't inject scoped state into IEndpoint class fields (use lambda DI)

---

## Debug checklist («endpoint 404 / 401»)

1. Path typo vs FE (`GetPersonnels` exact)?
2. Version `v1` vs `v{version}` registered?
3. Module `AddEndpoints` called?
4. Class `IEndpoint` + non-abstract?
5. `RequireAuthorization` + missing Bearer → 401
6. Permission filter → 403
7. Tenant empty intersect → 200 empty list (not 404)
8. Antiforgery on form without Disable → 400
9. Scalar/OpenAPI — endpoint listed?
10. YARP cluster path strip wrong?

---

## 25 soal-e mosahebe

1. Minimal API chie?
2. Controllers vs Minimal — tradeoffs?
3. `IResult` / `Results.Ok`?
4. Parameter binding sources?
5. `[AsParameters]` chie?
6. `IEndpointFilter` vs middleware?
7. MediatR behavior vs endpoint filter?
8. Chera thin endpoint?
9. `IEndpoint` + assembly scan — OCP?
10. `TryAddEnumerable` chera?
11. `MapEndpoints` chejori hame ra peyda mikone?
12. ErrorOr → HTTP chejori?
13. ProblemDetails chie?
14. API versioning URL segment?
15. `DisableAntiforgery` chera?
16. `RequireAuthorization` vs `RequirePermissions`?
17. Form file upload Minimal?
18. `WithTags` / `WithName`?
19. MapGroup maziat?
20. CancellationToken automatic?
21. Strict JSON converters cherā?
22. Identity Controllers — fargh?
23. Chejori endpoint test?
24. Fat lambda smell?
25. YARP + version segment?

---

## Senario whiteboard

### A) Add new endpoint

```
1. Application: Command + Handler + Validator
2. Presentation: class CreateX : IEndpoint { MapPost ... Send Match }
3. NOTHING in Program.cs
4. Run → Scalar shows under Tags
```

### B) Forgot AddEndpoints on new module

```
Module DI registers handlers but no routes
→ 404 forever
→ fix: services.AddEndpoints(Presentation.Assembly)
```

### C) Permission filter on

```
Authenticated but no permission claim for site
→ Endpoint filter Forbid 403
→ Handler never runs
```

### D) Spoof without tenant middleware

```
Still Need UseTenantContext before MapEndpoints
Endpoint thin — data leak prevented by EF filters not by endpoint
```

---

## Mini lab (1 session)

1. IDE: `IEndpoint.cs` + `EndpointExtensions.cs` bekhoon
2. `CreatePersonnel.cs` / `GetPersonnels.cs` / `DeletePersonnel.cs` side-by-side
3. Breakpoint `MapEndpoints` foreach — count endpoints
4. Scalar UI — find Personnels tag
5. DevTools: POST create → status + ProblemDetails on validation fail
6. Temporarily comment `RequireAuthorization` locally — see 200 anonymous (then revert!)
7. Compare Identity `ApiController` Problem mapping ba `ApiResults`

---

## Resume

**short:**

> Built a modular Minimal API surface with an `IEndpoint` plugin model: assembly-scanned endpoint classes per feature, MediatR dispatch, ErrorOr-to-ProblemDetails mapping, URL API versioning, and composable endpoint filters for site/permission checks — keeping `Program` free of per-route registration.

**bullets:**

- Implemented `IEndpoint` + `AddEndpoints`/`MapEndpoints` discovery (`TryAddEnumerable`) across ~8 module Presentation assemblies (~380 routes)
- Kept endpoints thin: bind HTTP → `ISender.Send` → `Match(Results.*, ApiResults.Problem)`
- Applied Asp.Versioning URL segments, OpenAPI tags/metadata, multipart uploads with `DisableAntiforgery`
- Provided `RequirePermissions` / `RequireSiteAccess` / role/position `IEndpointFilter` extensions alongside JWT `RequireAuthorization`

**skills:** `ASP.NET Core Minimal APIs, IEndpoint, Endpoint Filters, MediatR, ErrorOr, ProblemDetails, API Versioning, OpenAPI/Scalar, Modular Monolith, OCP, Multipart Forms`

---

## File-haye mohem

| chi | koja |
|---|---|
| IEndpoint | `Dejban.Common.Presentation/Endpoints/IEndpoint.cs` |
| Discovery | `.../Endpoints/EndpointExtensions.cs` |
| ApiResults | `Dejban.Common.Presentation/Results/ApiResults.cs` |
| Program map | `Dejban.Api/Program.cs` → `MapEndpoints()` |
| Module register | e.g. `PersonnelsModule.AddEndpoints(Presentation.Assembly)` |
| AssemblyReference | `*.Presentation/AssemblyReference.cs` |
| Create/Get/Delete/Update | `Personnels.Presentation/Personnels/*.cs` |
| Tags | `Personnels.Presentation/Tags.cs` |
| Versioning DI | `Common/.../AddApiVersioningAndExplorer` |
| Auth filter extensions | `Common/Authorization/AuthorizationExtensions.cs` |
| Permission filter | `PermissionRequirementFilter.cs` |
| SiteAccess filter | `SiteAccessRequirementFilter.cs` |
| JSON options | `Dejban.Api/Extensions/ServiceCollectionExtension.cs` |
| Scalar | `ScalarExtensions.cs` |
| Identity contrast | `IdentityServer/Controllers/ApiController.cs` |

---

## Chejori digest koni

1. World: Controllers vs Minimal jadval (10 min)
2. Read EndpointExtensions line-by-line (10 min)
3. Copy one endpoint as mental template (5 min)
4. Trace one FE call → Network → endpoint class (15 min)
5. 25 soal boland (20 min)
6. Sketch «add endpoint» without touching Program (5 min)

---

*Day 17 tamum. Ba'd: Day 18 — Modular DI (`AddXxxModule`) (amade). Fehrest: [README.md](./README.md).*
