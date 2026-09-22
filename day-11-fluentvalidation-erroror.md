# Day 11 — FluentValidation + ErrorOr

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Do layer baraye "input ghalat": **FluentValidation** (shape/format — empty, regex, length) va **ErrorOr** (natije-ye business — NotFound, Conflict). FluentValidation to MediatR pipeline run mishe → `Error.Validation` → handler aslan seda **nemishe**. Handler/domain ba ErrorOr NotFound/Conflict barmigardone. Endpoint `Match(Ok, Problem)` → HTTP. Exception = unexpected; ErrorOr = expected.

---

# BAKHSH-E AVAL: WORLD — Validation + Result to donya

## Chera exception baraye validation bad-e?

```csharp
// ❌ control flow ba exception
if (string.IsNullOrEmpty(name))
    throw new ValidationException("Name required");
```

- Exception = expensive + stack unwind
- Expected failure (user typo) ≠ bug
- Hard to return **multiple** field errors cleanly

**Better:** validate → list of errors → return as value.

---

## FluentValidation chie?

Library baraye rule-based validation. Separate class az handler.

```csharp
public class CreateUserValidator : AbstractValidator<CreateUserCommand>
{
    public CreateUserValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.Age).InclusiveBetween(18, 120);
        RuleFor(x => x.Password).MinimumLength(8)
            .Matches("[A-Z]").WithMessage("Need uppercase");
    }
}
```

### Common rules

| rule | mesal |
|---|---|
| `NotEmpty` / `NotNull` | required |
| `MaximumLength` / `Length` | string size |
| `GreaterThan` / `InclusiveBetween` | numbers |
| `EmailAddress` / `Matches(regex)` | format |
| `IsEnumName` / `IsInEnum` | enums |
| `Must` / `MustAsync` | custom predicate |
| `When` / `Unless` | conditional |
| `RuleForEach` + `ChildRules` | collections / nested |
| `DependentRules` | rules after parent succeeds |
| `Include` / `SetValidator` | compose validators |
| `WithMessage` / `WithName` | messaging |

### Cascade modes

```csharp
RuleFor(x => x.Email)
    .NotEmpty()
    .EmailAddress(); // default: continue collecting errors

// CascadeMode.Stop — stop after first failure on this property
```

### DI registration

```csharp
services.AddValidatorsFromAssembly(assembly);
// MediatR:
config.AddOpenBehavior(typeof(ValidationBehavior<,>));
```

---

## Result / ErrorOr pattern

```csharp
ErrorOr<User> result = await GetUser(id);

if (result.IsError)
    return result.Errors;

User user = result.Value;
```

Or:

```csharp
return result.Match(
    user => Results.Ok(user),
    errors => Results.Problem(...));
```

### ErrorOr factory methods

| factory | meaning | typical HTTP |
|---|---|---|
| `Error.Validation` | bad input | 400 |
| `Error.NotFound` | missing | 404 |
| `Error.Conflict` | duplicate / state | 409 |
| `Error.Unauthorized` | auth | 401 |
| `Error.Forbidden` | permission | 403 |
| `Error.Failure` | general business fail | 400/500 |
| `Result.Success` | void success | 200/204 |
| `Result.Updated` / `Deleted` | semantic success | 200/204 |

```csharp
public static class UserErrors
{
    public static Error NotFound(Guid id) =>
        Error.NotFound("User.NotFound", $"User {id} not found");

    public static Error EmailTaken(string email) =>
        Error.Conflict("User.EmailTaken", $"Email {email} already used");
}
```

**Implicit conversion:** `return user.Id;` → `ErrorOr<Guid>`.  
`return UserErrors.NotFound(id);` → `ErrorOr<T>` with error.

---

## Layers of validation (World)

```
1. FluentValidation     → format, required, shape     (pipeline)
2. Handler checks       → existence, uniqueness       (DB lookup)
3. Domain factory       → invariants                  (Entity.Create)
4. DB constraints       → unique index last line
```

Don't put uniqueness-only in FluentValidation `MustAsync` if you can do it in handler — clearer + race-aware with DB unique index.

---

## ProblemDetails (RFC 7807)

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "One or more validation errors occurred.",
  "status": 400,
  "errors": {
    "Email": ["Email is required"],
    "Age": ["Age must be between 18 and 120"]
  }
}
```

ASP.NET: `ValidationProblem` / `Problem` / custom mapper from ErrorOr.

---

## Alternatives

| approach | note |
|---|---|
| DataAnnotations | attributes on DTO — couples model |
| FluentValidation | external rules — preferred |
| Manual ifs | fine for tiny apps |
| Result&lt;T&gt; (custom) | like ErrorOr |
| LanguageExt / OneOf | functional styles |
| Zod (frontend) | FE twin of FluentValidation (Day 27) |

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **`MustAsync` live DB checks in validators** — Dejban commented / prefers handlers
- **`CascadeMode` explicit** — defaults
- **`WithName` for display names** — rare/absent
- **`IValidatorInterceptor`** — absent
- **`Unless`** — absent (use `When`)
- **Query validation in Dejban pipeline** — only `IBaseCommand`
- **Shared ValidationBehavior package** — 5 microservice copies

---

# BAKHSH-E DOVOM: DEJBAN — FluentValidation + ErrorOr

## Versions

```xml
FluentValidation.DependencyInjectionExtensions  12.1.0
ErrorOr                                          2.0.1
```

---

## Registration

### Dejban

```csharp
// ApplicationConfiguration.cs
services.AddMediatR(config =>
{
    config.RegisterServicesFromAssemblies(moduleAssemblies);
    config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
    config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
    config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
});

services.AddValidatorsFromAssemblies(moduleAssemblies, includeInternalTypes: true);
```

### Microservices (ACL, Identity, …)

```csharp
services.AddMediatR(config =>
{
    config.RegisterServicesFromAssemblyContaining<ApplicationAssemblyReference>();
    config.AddOpenBehavior(typeof(ValidationBehavior<,>));
});
services.AddValidatorsFromAssembly(ApplicationAssemblyReference.Assembly);
```

---

## Pipeline: FluentValidation → ErrorOr

### Dejban ValidationPipelineBehavior

```csharp
// Dejban.Common.Application/Behaviors/ValidationPipelineBehavior.cs

internal sealed class ValidationPipelineBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IBaseCommand   // ← commands only
    where TResponse : IErrorOr
{
    public async Task<TResponse> Handle(...)
    {
        if (!validators.Any()) return await next();

        var results = await Task.WhenAll(
            validators.Select(v => v.ValidateAsync(context, ct)));

        var failures = results.Where(r => !r.IsValid)
            .SelectMany(r => r.Errors).ToList();

        if (failures.Count == 0) return await next();

        // ValidationFailure → Error.Validation → ErrorOr.From via reflection
        return TryCreateResponseFromErrors(failures, out var response)
            ? response
            : throw new ValidationException(failures);
    }
}
```

**Bridge:**

```csharp
Error.Validation(
    code: string.IsNullOrWhiteSpace(x.PropertyName) ? x.ErrorCode : x.PropertyName,
    description: x.ErrorMessage);
```

→ `ErrorOr<T>.From(List<Error>)` (reflection because `TResponse` open generic).

**Short-circuit:** handler **never runs** if validation fails.

### Microservice ValidationBehavior

Same conversion; constraint = `IRequest<TResponse>` → **commands + queries** validate.

---

## Command contracts (ErrorOr)

```csharp
public interface ICommand : IRequest<ErrorOr<Success>>, IBaseCommand;
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

`IBaseCommand` = marker for Dejban validation behavior.

---

## Validator examples

### CreatePersonnel — basics + When + RuleForEach

```csharp
// Personnels.Application/.../CreatePersonnelCommandValidator.cs

RuleFor(c => c.PersonnelCode).NotEmpty();
RuleFor(c => c.FirstName).NotEmpty();
RuleFor(c => c.NationalCode).NotEmpty()
    .WithMessage("'{PropertyName}' الزامی است");
RuleFor(c => c.Gender).NotEmpty().IsEnumName(typeof(Gender));
RuleForEach(c => c.ContractIds).NotEmpty();
RuleFor(c => c.AccessCode)
    .GreaterThan(0)
    .When(c => c.AccessCode.HasValue);
```

### Login — localization + conditional formats

```csharp
// IdentityServer/.../LoginCommandValidator.cs

RuleFor(x => x.UserName).NotEmpty()
    .WithMessage(x => localizer["'{PropertyName}' الزامی است"]);

RuleFor(x => x.UserName).EmailAddress()
    .When(x => x.UserName.Contains('@'));

RuleFor(x => x.UserName).Matches(@"^09[0-9]{2}-?[0-9]{3}-?[0-9]{4}$")
    .When(/* mobile path */);

RuleFor(x => x.UserName).Matches(@"^[A-Za-z0-9.]+$")
    .When(/* username path */);
```

### CreateVisitor — When by visitor type

```csharp
RuleFor(c => c.NationalCode).NotEmpty()
    .When(x => !x.VisitorTypeName.Equals(nameof(VisitorTypesEnum.Foreigner), ...));

RuleFor(c => c.PassportNumber).NotEmpty()
    .When(x => x.VisitorTypeName.Equals(nameof(VisitorTypesEnum.Foreigner), ...));
```

### CreateVehicle — nested When + Must + RuleForEach

```csharp
When(c => c.OwnerInfo != null, () =>
{
    When(c => c.OwnerInfo.OwnershipType == OwnershipType.Personnel, () =>
    {
        RuleFor(c => c.OwnerInfo.NationalCode)
            .Matches("^[0-9]{10}$");
    });

    When(c => c.OwnerInfo.OwnershipType is OwnershipType.Organization
              or OwnershipType.Contractor, () =>
    {
        RuleFor(c => c.Assignment)
            .Must(HasAtLeastOneDriver)
            .WithMessage("...");
    });
});

When(c => c.Assignment != null, () =>
{
    RuleForEach(c => c.Assignment!.DriverIds).NotEmpty();
});
```

### CreateVisitReservation — ChildRules + XOR Must

```csharp
RuleForEach(x => x.Visitors).ChildRules(visitor =>
{
    visitor.RuleFor(x => x)
        .Must(x => x.VisitorId.HasValue ^ x.CreateVisitor is not null)
        .WithMessage("Either VisitorId or CreateVisitor required");

    visitor.RuleForEach(x => x.Items).ChildRules(/* ... */);
    visitor.RuleForEach(x => x.Vehicles).ChildRules(v =>
        v.RuleFor(x => x.PlateNumber).NotEmpty().MaximumLength(64));
});
```

### DependentRules (ACL)

```csharp
RuleFor(x => x.Brand).IsEnumName(...)
    .DependentRules(() =>
    {
        RuleFor(x => x.TerminalId).NotEmpty().When(...Virdi...);
        RuleFor(x => x.SerialNumber).NotEmpty().When(...Tiam|ZK...);
    });
```

### Include (compose)

```csharp
// UpdateVisitReservationCommandValidator
Include(new CreateVisitReservationCommandValidatorAdapter());
```

---

## Error factories (Domain)

```csharp
// PersonnelErrors.cs
public static Error NotFound(Guid personnelId) =>
    Error.NotFound("Personnel.NotFound", $"پرسنل با شناسه {personnelId} یافت نشد");

public static Error NationalCodeExists(string nationalCode) =>
    Error.Conflict("Personnel.NationalCodeExists", $"...");
```

```csharp
// Errors.Auth.cs (IdentityServer)
public static Error InvalidCredentials =>
    Error.Unauthorized(code: "Auth.InvalidCredentials", ...);

public static List<Error> IdentityErrors(IEnumerable<IdentityError> errors) =>
    errors.Select(err => Error.Validation(
        code: $"Auth.{err.Code}",
        description: err.Description)).ToList();
```

**Convention:** `{Entity}.{Reason}` stable codes → FE/i18n friendly.

---

## Handler patterns

```csharp
// 1) Early return factories
if (site == null) return SiteErrors.NotFound(request.SiteId);
if (nationalCodeExists) return PersonnelErrors.NationalCodeExists(...);

// 2) Domain ErrorOr forward
var assetResult = Asset.Create(...);
if (assetResult.IsError) return assetResult.Errors;

// 3) Success with value (implicit ErrorOr)
return asset.Id;

// 4) Void success
return Result.Success;
```

**Uniqueness:** FluentValidation shape; handler `AnyAsync` for exists → Conflict. Unique index = final safety.

---

## Domain ErrorOr (always-valid)

```csharp
// VehiclePlate.CreatePlate → ErrorOr<VehiclePlate>
// Asset.Create → ErrorOr<Asset>

var plate = VehiclePlate.CreatePlate(number, type);
if (plate.IsError) return plate.Errors;
```

Presentation sometimes validates plate **before** `Send` (CreateVehicle endpoint) — double gate ok.

---

## HTTP Match

### Minimal API (Dejban)

```csharp
var result = await sender.Send(request);
return result.Match(Results.Ok, ApiResults.Problem);
// or
return result.Match(_ => Results.NoContent(), ApiResults.Problem);
```

### Controllers (ACL)

```csharp
return (await mediator.Send(request)).Match(Ok, Problem);
```

### ApiResults / ApiController mapping

| ErrorType | Status |
|---|---|
| Validation | 400 (`ValidationProblem` if all validation) |
| Unauthorized | 401 |
| Forbidden | 403 |
| NotFound | 404 |
| Conflict | 409 |
| Failure | 400 (Dejban) / 500 (some ApiControllers) |
| other | 500 |

```csharp
// ApiResults.Problem(List<Error>)
// Validation errors → dictionary by error.Code (often property name)
```

---

## Full request flow

```
POST /api/v1/Personnels/Create
  → MediatR
  → ExceptionHandling
  → Logging
  → ValidationPipelineBehavior
       validators.ValidateAsync
       fail? → ErrorOr.From(Validation errors) → STOP
  → CreatePersonnelCommandHandler
       Site missing? → SiteErrors.NotFound
       NationalCode exists? → PersonnelErrors.NationalCodeExists
       Personnel.CreateAsync → Raise domain event
       SaveChanges → return Id
  → Match(Results.Ok, ApiResults.Problem)
  → 200 Guid | 400/404/409 ProblemDetails
```

---

## FE note (kootah)

Backend Day 15 = FluentValidation + ErrorOr.  
Frontend Day 27 = React Hook Form + **Zod** — haman idea (schema validation) on client. Axios shows ProblemDetails messages (Day 09).

---

## Smell-ha

1. **5 copy-paste ValidationBehavior** — should be shared Common
2. **Reflection for ErrorOr.From** — fragile/slow vs generic helper
3. **Dejban queries skip FluentValidation** — intentional but inconsistent with microservices
4. **Failure → 400 vs 500** — Dejban ApiResults ≠ some ApiControllers
5. **PropertyName as error code** — works for ValidationProblem; weird for custom ErrorCode
6. **MustAsync commented** — unfinished patterns
7. **Include rare** — duplication across Create/Update validators
8. **Plate validated in endpoint AND domain** — ok but easy to drift
9. **Persian messages mixed** — some localizer, some hardcoded
10. **No CascadeMode.Stop** where useful (stop after NotEmpty)
11. **Handler does format checks sometimes** — belongs in validator
12. **No centralized Error → ProblemDetails tests**

---

## 20 soal-e mosahebe

1. **FluentValidation chie?** — External rule classes for request DTOs/commands
2. **Chera na DataAnnotations?** — Keeps Domain/DTO clean; richer rules
3. **ErrorOr chie?** — Result type: value OR list of errors (no throw)
4. **Chera na exception for NotFound?** — Expected; cheaper; composable
5. **Pipeline validation short-circuit?** — Fail → return ErrorOr; handler skipped
6. **Error.Validation vs NotFound?** — Input shape vs missing resource
7. **Match?** — Branch success vs errors at API edge
8. **When / RuleForEach?** — Conditional + collection rules
9. **DependentRules?** — Child rules after parent valid
10. **Include?** — Reuse another validator
11. **Must vs MustAsync?** — Sync vs async custom; DB often in handler
12. **IBaseCommand?** — Marker so only commands hit Dejban validation behavior
13. **Error factory class?** — Stable codes + messages (`Personnel.NotFound`)
14. **ProblemDetails?** — Standard error HTTP body
15. **Conflict 409?** — Duplicate national code / invalid state
16. **Domain ErrorOr?** — Invariants at factory (`VehiclePlate.Create`)
17. **Implicit conversion?** — `return id` → `ErrorOr<Guid>`
18. **Result.Success?** — Void command success
19. **Validation + unique index?** — App check + DB final guard
20. **Zod vs FluentValidation?** — FE schema vs BE rules; same idea

---

## Deep dive — `ValidationPipelineBehavior` + reflection bridge

Constraint Dejban:

```csharp
where TRequest : IBaseCommand
where TResponse : IErrorOr
```

Flow:
1. `IEnumerable<IValidator<TRequest>>` — 0 validator → pass through
2. `Task.WhenAll(ValidateAsync)` — parallel validators
3. `ValidationFailure` → `Error.Validation(code: PropertyName, description: Message)`
4. `typeof(TResponse).GetMethod(nameof(ErrorOr<object>.From))` invoke static **From(List<Error>)**
5. Age reflection fail → `throw new ValidationException` (fallback)

**Microservice `ValidationBehavior`:** `IRequest<TResponse>` — **queries ham** validate mishan.

| | Dejban | ACL/Identity |
|---|---|---|
| constraint | `IBaseCommand` | any `IRequest` |
| queries validated | na (by default) | bale |

---

## Deep dive — ErrorOr `Match` patterns

```csharp
// Minimal API — value
return result.Match(Results.Ok, ApiResults.Problem);

// NoContent
return result.Match(_ => Results.NoContent(), ApiResults.Problem);

// Created with route
return result.Match(
    id => Results.Created($"/api/v1/Personnels/{id}", id),
    ApiResults.Problem);

// Controller ACL
return (await mediator.Send(request)).Match(Ok, Problem);
```

**Chain errors:**

```csharp
ErrorOr<Asset> created = Asset.Create(...);
if (created.IsError) return created.Errors;

ErrorOr<Success> saved = await Persist(created.Value);
return saved.IsError ? saved.Errors : Result.Success;
```

**First error vs all errors:** `ApiResults.Problem` — age **hame** Validation → dictionary; else **first** error only (mixed types).

---

## Deep dive — `ApiResults.Problem` line-by-line

```csharp
if (errors.All(e => e.Type == ErrorType.Validation))
    return ValidationProblem(errors); // ASP.NET ValidationProblemDetails

return Problem(errors[0]); // single RFC 7807 ProblemDetails
```

Mapping:
- Validation → 400 grouped by `error.Code`
- Unauthorized → 401
- Forbidden → 403
- NotFound → 404
- Conflict → 409
- Failure → **400** (Dejban) — na 500
- default → 500

**Identity `ApiController`:** `title` = Description, Failure sometimes 500 — **cross-service inconsistency** for shared FE client.

---

## Deep dive — Advanced FluentValidation (WORLD + Dejban)

### `Must` / custom logic

```csharp
RuleFor(x => x.EndDate)
    .Must((cmd, end) => end >= cmd.StartDate)
    .WithMessage("End must be after start");
```

### `RuleForEach` + `SetValidator`

```csharp
RuleForEach(x => x.Lines).SetValidator(new OrderLineValidator());
```

### Async rule (rare Dejban)

```csharp
RuleFor(x => x.Code)
    .MustAsync(async (code, ct) => !await repo.Exists(code, ct))
    .WithMessage("Taken");
```

**Dejban preference:** uniqueness to **handler** `AnyAsync` → `Error.Conflict` — race + unique index.

### Excel import validators

Personnels import: row-level validator + `StaffImportRowEditDialog` — same FluentValidation ideas on **DTO rows**, na faghat commands.

---

## Deep dive — Domain ErrorOr factories (more examples)

```csharp
// VehiclePlate — value object
public static ErrorOr<VehiclePlate> CreatePlate(string number, PlateType type)
{
    if (string.IsNullOrWhiteSpace(number))
        return Error.Validation("VehiclePlate.Empty", "...");
    // ...
    return new VehiclePlate(number, type);
}

// SiteErrors, VisitorErrors, AssetErrors — same {Entity}.{Reason} code
```

**Handler:**

```csharp
var plate = VehiclePlate.CreatePlate(request.PlateNumber, request.PlateType);
if (plate.IsError) return plate.Errors;
```

Presentation **double validation:** endpoint sometimes pre-check plate format — **drift risk** if yek ja update shod yek ja na.

---

## Deep dive — Pipeline order (Dejban)

```
ExceptionHandlingPipelineBehavior  (outer — catch unexpected)
RequestLoggingPipelineBehavior
ValidationPipelineBehavior         (FluentValidation → ErrorOr)
Handler                              (business ErrorOr)
```

Validation **qabl** handler — handler **aslan** run nemishe age format fail. Logger hanooz request ra did (depends log level).

**ExceptionHandling:** unexpected throw → Problem 500 — na ErrorOr.

---

## Deep dive — ValidationProblem shape vs single Problem

Multi-field login fail (Identity):

```json
{
  "status": 400,
  "errors": {
    "UserName": ["الزامی است"],
    "Password": ["الزامی است"]
  }
}
```

Single NotFound:

```json
{
  "status": 404,
  "title": "Personnel.NotFound",
  "detail": "پرسنل با شناسه ... یافت نشد"
}
```

FE: detect `errors` object vs `title`/`detail`.

---

## Anti-patterns (smell detail)

| smell | fix direction |
|---|---|
| DB check in MustAsync everywhere | handler + unique index |
| throw ValidationException in handler | return Error.Validation |
| string match on `Description` | use stable `Code` |
| 5 copy ValidationBehavior | extract Common package |
| query without validation | add validator or document why |

---

## Chejori in fasl ra «digested» koni (lab — ~45 min)

1. Breakpoint `ValidationPipelineBehavior` — POST personnel bedune NationalCode (10 min)
2. Inspect response JSON — `errors` dict keys = property names (5 min)
3. Trigger `Personnel.NotFound` — 404 `title` code (5 min)
4. Open `CreateVehicleCommandValidator` — trace nested `When` (10 min)
5. Compare Dejban vs ACL `ValidationBehavior` constraint in IDE (5 min)
6. Write **1 rule** test: validator + `TestValidate` (FluentValidation test helper) (10 min)

**FluentValidation test (WORLD):**

```csharp
var result = validator.TestValidate(new CreatePersonnelCommand { FirstName = "" });
result.ShouldHaveValidationErrorFor(x => x.FirstName);
```

---

## 5 soal-e ezafe (bonus)

21. **`IErrorOr` marker chi?** — constraint for open generic behavior / ErrorOr.From
22. **Chera `ErrorOr.From` reflection?** — `TResponse` compile-time unknown; alternative: source generator
23. **`Result.Updated` vs `Success`?** — semantic void outcomes (if used in codebase)
24. **ChildRules vs SetValidator?** — inline nested rules vs reusable child validator class
25. **ValidationException fallback ke?** — TResponse not ErrorOr-compatible — dev misconfig

---

## Resume

**short:**

> Implemented command validation with FluentValidation 12 in MediatR pipeline behaviors that convert failures to ErrorOr validation errors without throwing, and used ErrorOr across handlers/domain factories with ProblemDetails mapping for HTTP 400/401/403/404/409.

**bullets:**

- Registered assembly-scanned validators and open generic `ValidationPipelineBehavior` constrained to commands (`IBaseCommand`)
- Authored rich validators: conditional `When`, `RuleForEach`/`ChildRules`, `Must`, `DependentRules`, localized Login rules
- Standardized domain/application errors via static factories (`PersonnelErrors`, `Errors.Auth`) and `Match(..., ApiResults.Problem)`
- Kept format checks in FluentValidation and uniqueness/existence in handlers + domain `ErrorOr` factories (`VehiclePlate`, `Asset`)

**skills:** `FluentValidation, ErrorOr, Result Pattern, MediatR Pipeline Behaviors, ProblemDetails, Input Validation, Domain Invariants`

---

## File-haye mohem

| chi | koja |
|---|---|
| Packages | `Directory.Packages.props` |
| Dejban registration | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| ValidationPipelineBehavior | `Dejban.Common.Application/Behaviors/ValidationPipelineBehavior.cs` |
| ValidationBehavior (ACL) | `ACLServer/Abstractions/Behaviors/ValidationBehavior.cs` |
| ICommand / IBaseCommand | `Dejban.Common.Application/Messaging/ICommand.cs` |
| CreatePersonnel validator | `Personnels.Application/.../CreatePersonnelCommandValidator.cs` |
| Login validator | `IdentityServer/.../LoginCommandValidator.cs` |
| CreateVisitor validator | `Visitors.Application/.../CreateVisitorCommandValidator.cs` |
| CreateVehicle validator | `Vehicles.Application/.../CreateVehicleCommandValidator.cs` |
| VisitReservation nested | `Visitors.Application/.../CreateVisitReservationCommandValidator.cs` |
| DependentRules | `ACLServer/.../GetTerminalFirmwareVersionQueryValidator.cs` |
| Include | `Visitors.Application/.../UpdateVisitReservationCommandValidator.cs` |
| PersonnelErrors | `Personnels.Domain/Personnels/PersonnelErrors.cs` |
| Errors.Auth | `IdentityServer/Application/Auth/Errors/Errors.Auth.cs` |
| VehiclePlate ErrorOr | `Vehicles.Domain/Vehicles/VehiclePlate.cs` |
| ApiResults | `Dejban.Common.Presentation/Results/ApiResults.cs` |
| ApiController.Problem | `ACLServer/Controllers/ApiController.cs` |

---

Day 11 tamum. Ba'd: Day 12 — DDD (aggregate, domain event, value object). Fehrest: [README.md](./README.md).
