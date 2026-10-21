# 11 — Result (ErrorOr)

*Khataye montazere return mishavad. Exception baraye chiz-e shekaste.*

---

## Ye khat

Result (railway-oriented): function ya **value** bar migardanad ya **khata**. Caller mojbur ast har do rah ra bebine. `throw` baraye "national code tekrar ast" nist.

Library: **ErrorOr**. Contract:

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
public interface ICommandHandler<in TCommand, TResponse>
    : IRequestHandler<TCommand, ErrorOr<TResponse>>;
```

Handler `return personnel.Id` ya `return Errors.Personnel.NotFound`. Compiler `ErrorOr<T>` ra az implicit conversion misazad.

## Do rah, yek return

```
vorudi
  → validation behavior → age bad: ErrorOr (rah-e khata) va handler seda nemishavad
  → handler
       → ErrorOr<T> success
       → ErrorOr<T> failure (NotFound, Conflict, Validation)
  → endpoint
       result.Match(
         value => Results.Ok(value),
         errors => ApiResults.Problem(errors));
```

`Match` haman "switch roye rah" ast. Age yek rah ra faramoosh koni, compile ya review an ra migirad. `try/catch` an ejbar ra nadarad: mitavani catch nakoni va 500-e bi-mani bedahi.

## Chand jore `Error`

| Noe | Kei | HTTP-e ma'mool |
|---|---|---|
| Validation | vorudi bad | 400 |
| NotFound | id nist | 404 |
| Conflict | tekrar, race-e business | 409 |
| Unauthorized / Forbidden | identity / permission | 401 / 403 |
| Unexpected | bug, network, null-e mohal | 500, exception |

Validation-e pipeline khodesh `Error.Validation` misazad (`property` + message) va `ErrorOr.From` ra ba reflection seda mizanad ta `TResponse` haman `ErrorOr<Guid>` bemanad.

## Exception hanuz hast

`ExceptionHandlingPipelineBehavior` exception-e **handle-nashode** ra log mikonad va `DejbanException` mipichand. An baraye bug ast: `NullReference`, timeout, constraint-e database-e gheyr-montazere.

Ghanun:

- "user in code ra ghablan sabt karde" → `Error.Conflict`
- "disk por ast / bug" → exception

Age hame ra `throw` koni: control-flow ba exception geran ast, va caller mitavanad faramoosh konad. Age hame ra `ErrorOr` koni: `OutOfMemory` ra dasti model mikoni ke bi-mani ast.

## Railway yani chi

Har ghadam do rail darad. Success mimanad roye rail-e sabz. Avalin khata mipare roye rail-e ghermez va ghadam-haye ba'd **ejra nemishavand**. `Match` / `Then` / `else` roye `ErrorOr` hamin ast. Validation behavior rail-e ghermez ra **ghabl** az handler mibandad.

## Farq ba tuple `(bool ok, T value, string error)`

Tuple gharardad nadarad: `ok == false` vali value ham por ast. `ErrorOr` yek halat darad. List-e `Error` ham dari, na yek string.

## Script-e 60 sanie

> "Har command va query `ErrorOr<T>` bar migardanad. Khata-ye business — not found, conflict, validation — return mishavad va endpoint `Match` mikonad be Ok ya ProblemDetails. Validation behavior age FluentValidation fail shavad haman `ErrorOr` ra misazad va handler ra seda nemizanad. Exception faghat baraye shekast-e gheyr-montazere ast va behavior-e exception an ra be `DejbanException` tabdil mikonad. Event sourcing ya Result-e dasti naneveshtim; ErrorOr gharardad-e stack ast."

---

## 10 soal

**1. Chera exception baraye business error na?**
Exception baraye chiz-e **na-montazere** ast. Duplicate montazere ast. `throw` baraye an, flow ra penhan va geran mikonad va caller ra mojbur be handle nemikonad.

**2. `ErrorOr` va `Result<T,E>` farq-e amali?**
Har do railway hastand. ErrorOr list-e error-e typed (code, description, type) darad va ba ASP.NET ProblemDetails khub mineshinad. Ma an library ra entekhab kardim.

**3. Handler chand khata bar migardanad?**
Yek `ErrorOr` mitavanad chand `Error` dashte bashad. Validation hamin kar ra mikonad: hame-ye `ValidationFailure` yek list.

**4. Age handler exception partab konad, `ErrorOr` chi mishavad?**
Rah-e success/failure-e `ErrorOr` nist. Exception behavior an ra migirad. 500. Pas bug ra be `Error.Failure` tabdil nakon ta log-e stack ra gom koni; bug bayad exception bemanad.

**5. Query-e NotFound `Error` ast ya `null`?**
Gharardad-e in stack `ErrorOr` / NotFound ast ta endpoint yek `Match` dashte bashad. `null` caller ra dobare vared-e if mikonad.

**6. Performance?**
`ErrorOr` allocation-e koochak darad. Moqabel-e database chizi nist. Argument-e "exception geran ast" faghat vaghti throw-e ziyad roye happy path dari.

**7. `Match` ra faramoosh konim?**
Pas `ErrorOr` ra be client-e HTTP pass dade-i va shekl-e response tasadofi mishavad. Endpoint **hatman** success va errors ra joda mikonad.

**8. Validation do bar?**
Behavior yek bar ghabl az handler. Handler nabayad haman FluentValidation ra dobare seda bezanad. Handler faqat ghanun-i ra check mikonad ke be database/aggregate niaz darad (unique budan).

**9. Farq ba ProblemDetails?**
`ErrorOr` model-e dakheli ast. ProblemDetails (RFC 7807) model-e HTTP ast. `ApiResults.Problem` tarjome mikonad. Domain `ProblemDetails` nemishnasad.

**10. Test?**
`result.IsError` va `result.FirstError.Type`. Baraye success `result.Value`. Exception-e joda: `Assert.Throws`. Har do ra yek test ghalt nakon.
