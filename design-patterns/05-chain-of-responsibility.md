# 05 — Chain of Responsibility

*Har halqe ya kar mikonad, ya be ba'di pass midahad. Handler-e asli az zanjir khabar nadarad.*

---

## Ye khat

Request az yek zanjire rad mishavad. Har halqe mitavanad javab ra tamoom konad ya `next()` bezanad. Cross-cutting (log, validation, exception) birun-e handler mimanad.

## Moshkel

Age har `CreatePersonnelCommandHandler` avval validator, ba'd log, ba'd try/catch dashte bashad, yek taghir-e policy = dast zadan be dah-ha handler. Yeki faramoosh mikonad. Chain an ra yek bar, dor-e hame, migozarad.

## In codebase

`IPipelineBehavior<TRequest, TResponse>` mal-e MediatR ast. Sabt:

```csharp
config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
```

File: `Dejban.Common.Application/ApplicationConfiguration.cs`

Tartib-e sabt = tartib-e birun be dakhel:

```
Send
  → ExceptionHandling     try { next } catch → DejbanException + log
    → RequestLogging      log, next, log-e modat
      → Validation        faghat command; age khata, next() nashavad
        → Handler
```

`next` haman `RequestHandlerDelegate` ast. Seda zadaneash halqe-ye ba'di ast, na "handler" hatman. Handler akharin halqe ast.

## Validation daghighan chi mikonad

`ValidationPipelineBehavior` do constraint darad:

```csharp
where TRequest : IBaseCommand
where TResponse : IErrorOr
```

Pas **query** az in halqe rad nemishavad (constraint-e generic). Command-ha bale.

Agar validator nabashad, `next()`.
Agar hame valid bashand, `next()`.
Agar khata bashad, `ErrorOr` az `Error.Validation` sakhte mishavad va **handler seda nemishavad**. Reflection inja faghat baraye `ErrorOr<T>.From(List<Error>)` ast, chon `TResponse` to compile-time `ErrorOr<Guid>` ast va behavior an type-e baz ra nami-shenasad.

Agar sakhtan-e `ErrorOr` nashavad, `ValidationException` partab mishavad. Masir-e adi haman `ErrorOr` ast.

## Exception behavior

Exception-e handle-nashode ra log mikonad va dar `DejbanException` mipichand, ba esm-e request. An ra **ghaz** mikonad ke stack-e asli bemanad (`innerException`). Business error-e `ErrorOr` inja nemiad, chon exception nist.

## Farq ba Decorator

| | Chain | Decorator |
|---|---|---|
| Chand halqe | list, tartib-e sabt | aksaran yek wrapper dor-e yek object |
| Tasmim | mitavanad zanjir ra beborad (`next` nazanad) | aksaran ghabl/ba'd, ba'd original ra seda mizanad |
| Inja | pipeline-e MediatR | `IdempotentDomainEventHandler` |

Har do "wrap" hastand. Farq-e mosahebe: chain **chand** handler-e ham-noghsh darad va mitavanad motevaghef shavad. Decorator yek object ra ba haman interface ghat'e mikonad.

## ASP.NET middleware hamin pattern ast

`app.Use(...)` ham chain ast: authentication, tenant, endpoint. Pipeline-e MediatR **dakhel** use-case ast. Middleware **gabl** az an, roye HTTP. Begou har do ra ta kas fekr nakonad yeki-and.

```
HTTP middleware (auth, tenant, route)
  → IEndpoint
    → MediatR chain (exception, log, validation)
      → handler
```

## Script-e 60 sanie

> "Cross-cutting ra ba `IPipelineBehavior` anjam midahim, na dakhel-e handler. Se behavior sabt shode: exception birun, ba'd log, ba'd validation. Validation faghat `IBaseCommand` ra migirad va age FluentValidation khata dashte bashad `ErrorOr` bar migardanad va handler ejra nemishavad. `next()` halqe-ye ba'di ast. HTTP middleware zanjir-e joda-ye gabl az endpoint ast."

---

## 10 soal

**1. Chain che moshkeli ra hal mikonad?**
Ezafe kardan-e yek ghadam-e jadid (log, auth, validation) bedune taghir-e handler-haye mojood. Open/Closed.

**2. Ki tartib ra moshakhas mikonad?**
Tartib-e `AddOpenBehavior`. Avalin sabt, avalin wrapper, yani biruni-tarin.

**3. Age validation `next` ra seda nazanad chi?**
Handler, SQL, va domain ejra nemishavand. Pas khataye vorudi arzan ast va side-effect nadarad.

**4. Chera query validate nemishavad ba hamin behavior?**
Constraint `TRequest : IBaseCommand`. Query an ra implement nemikonad. Age query validation mikhahad, ya behavior-e digar ya validator-e khod-e query.

**5. Exception-e business koja miravad?**
`ErrorOr`. Behavior-e exception faghat exception-e gheyr-montazere ra mipichand. Duplicate national code nabayad `throw` shavad.

**6. Mitavanam behavior-e jadid ezafe konam?**
Bale: class-e `IPipelineBehavior` va yek khat `AddOpenBehavior`. Handler-ha avaz nemishavand. Hamin OCP ast.

**7. Behavior mitavanad scoped service begirad?**
Bale. Validator-ha inject mishavand. Behavior har request sakhte mishavad. Service-e singleton-e sangin ra inja cache nakon age be request bastagi darad.

**8. Farq ba middleware-e ASP.NET?**
Middleware HTTP ast (header, status, path) va gabl az endpoint. Behavior object-e command ast va gabl az handler. Auth inja middleware ast, na behavior.

**9. Zanjir-e deraz che moshkeli darad?**
Debug sakht, tartib-e eshtebah (log gabl az exception = log-e naghes), va behavior-i ke `next` ra faramoosh konad request ra bi-seda mikoshad.

**10. Chetor test mikoni?**
Behavior ra ba `next` fake test kon: validator-e namotabar → `next` **sefr** bar. Validator-e khali → `next` yek bar. Exception-e `next` → `DejbanException`.
