# 05 — Chain of Responsibility

Ye darkhast az chand halghe rad mishavad. Har halghe ya khodesh kar ra tamoom mikonad, ya midahad be ba'di. Kasi ke darkhast ra ferestade nemidanad kodam halghe javab dade.

## Moshkel

Log, validation-e shekl-e vorudi, va gereftan-e exception be hame-ye senario-ha marbut ast, na be ghanun-e ye senario.

Agar dakhel-e har handler copy-shan koni, yeki ja mimanad. Taghir-e siyasat yani dast zadan be dah-ha class. Handler por az kodi mishavad ke mal-e business nist.

## Ide

In kar-ha ra birun-e handler, ba ye tartib-e sabet, migozari. Handler faghat kar-e khodesh ra balad ast.

Shekl-e ghadimi-ash mesl-e poshtibani ast: sath-e 1 agar natavanest midahad sath-e 2, u agar natavanest midahad sath-e 3. Har kodam faghat ba'di ra mishnasad. Ferestande nemidanad tah-e kar ki javab dad.

Shekl-e emruzi-ash middleware ast. Har halghe ye `next` darad. Mitavanad ghabl az `next` kar konad va bad az bargashtan ham kar konad. Masalan log-e "shoru'", bad `next`, bad log-e "cheghadr tool keshid".

Shekl-e poshtibani aksaran ya khodesh tamoom mikonad ya midahad ba'di. Middleware har do taraf-e `next` ra darad.

Chand ghanun:

**Tartib bakhshi az gharardad ast.** Validation ghabl az handler. Log dor-e hame-chiz, pas biruni-tar. Gereftan-e exception az hame biruni-tar, ta khatay-e khode log ra ham begirad. Avaz kardan-e tartib, ma'ni-ye zanjire ra avaz mikonad.

**Halghe mitavanad zanjire ra beborad.** Agar validation rad shod va `next` seda nashod, handler nabayad ejra shavad. Fayede-ye asli-ye pattern hamin ghat' kardan ast.

**Halghe-ye hamegani ghanun-e ye mowjudiat ra balad nist.** "In field khali nabashad" kar-e halghe ast. "In code-e melli to in site tekrar ast" kar-e handler ast, chon database va ghanun-e haman mowjudiat ra mikhahad.

**Har senario zanjire ra khodesh new nakonad.** Chidan-e halghe-ha ye ja ast, moghe'-e bala amadan-e barname. Vagarna dobare copy dari.

## Mesal-e koochik

```csharp
async Task<Result<T>> Validate<T>(Command cmd, Func<Task<Result<T>>> next)
{
    var errors = validator.Check(cmd);
    if (errors.Count > 0) return Result<T>.Fail(errors);
    return await next();
}
```

Agar khata bargardani, `next` seda nashode. Handler khab ast.

## Ba chi ghalt mishavad

**Decorator** ye object-e moshakhas ra mipushanad va aksaran kar-e asli ra anjam midahad, ba ye kar-e ezafe ghabl ya bad. Chain chand halghe-ye ham-naghsh darad va mitavanad begoyad "hamin-ja bas ast" ya "mal-e man nist, boro ba'di".

**Mediator** ye vasete-ye markazi ast ke miguyad ki ba ki. Chain ye saf-e khati ast va har halghe faghat ba'di ra midanad.

**Strategy** ye algorithm ra jaygozin mikonad. Chain chand filter ra posht-e sar-e ham emtehan mikonad.

Middleware-e khode ASP.NET ham hamin zanjire ast, ru HTTP: authentication, routing, endpoint. Zanjire-ye dakhel-e use-case chiz-e digari ast. Har do chain hastand, to do laye.

## Koja estefade nakon

Ye `if`-e tanha zanjire nemikhahad. Zanjire-ye panzdah-ta'i ke kasi tartib-ash ra balad nist, debug ra az seday-e mostaghim sakht-tar mikonad.

## Hala dar Dejban

Do zanjire darim.

**Zanjire-ye HTTP** ghabl az endpoint ast. Authentication, tenant, masir.

**Zanjire-ye use-case** bad az endpoint va ghabl az handler ast. MediatR esm-ash `IPipelineBehavior` ast.

Sabt to `Dejban.Common.Application/ApplicationConfiguration.cs`:

```csharp
config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
```

Avalin sabt, biruni-tarin halghe ast:

```
Send
  → exception
      → log
          → validation
              → handler
```

Log bad az handler ham moddat ra minevisad. Exception dor-e hame-chiz ast.

Validation zanjire ra miborad. Faghat command az an rad mishavad, chon gheyd-ash `TRequest : IBaseCommand` ast. Query in gheyd ra nadarad. Agar FluentValidation khata bedahad, `Error.Validation` barmigardad va handler seda nemishavad. Agar hich validator sabt nashode bashad, `next` seda mishavad.

Khatay-e business inja throw nemishavad. `ErrorOr` ast. Raftar-e exception faghat kharabi-ye gheyr-montazere ra log mikonad va to `DejbanException` mipichad, ba haman exception-e asli dakhel-ash.

Endpoint raftar-ha ra new nemikonad. Moghe'-e shoru'-e barname chide mishavand.

## Agar beporsand, in tor begou

> Darkhast az halghe-ha rad mishavad va ferestande nemidanad ki tamoom-ash kard. Shekl-e middleware ghabl va bad az next har do kar mikonad va mitavanad zanjire ra beborad. Dejban do zanjire darad: HTTP ghabl az endpoint, va MediatR ghabl az handler. Tartib-e dovomi: exception birun, log vasat, validation dakhel. Validation faghat command ast va agar rad shavad handler ejra nemishavad.

## Dah so'al

**1. Ferestande che chizi ra nemidanad?**
Inke tah-e kar kodam halghe darkhast ra tamoom kard.

**2. Boridan-e zanjire yani che?**
Halghe `next` ra seda nemizanad. Handler ejra nemishavad.

**3. Farq-e saf-e poshtibani ba middleware chi ast?**
Poshtibani aksaran ya khodesh tamoom mikonad ya midahad ba'di. Middleware ghabl va bad az `next` har do kar mikonad.

**4. Chera tartib gharardad ast?**
Chon "log dor-e exception" ba "exception dor-e log" raftar-e digari ast.

**5. Che chizi nabayad to halghe-ye hamegani bashad?**
Ghanun-e khas-e ye mowjudiat ke database-ye haman senario ra mikhahad.

**6. Farq-ash ba Decorator chi ast?**
Decorator kar-e asli ra anjam midahad va chizi ezafe mikonad. Chain mitavanad begoyad hamin-ja tamoom.

**7. Farq-ash ba Strategy chi ast?**
Strategy ye algorithm-e entekhab-shode ast. Chain chand filter-e posht-e sar-e ham ast.

**8. Tartib-e behavior-ha to Dejban chi ast?**
Exception, bad log, bad validation, bad handler. Avalin `AddOpenBehavior` biruni ast.

**9. Chera Query az validation-e in behavior rad nemishavad?**
Gheyd-e `IBaseCommand` ra nadarad.

**10. Test-e zanjire ra chetor minevisi?**
Validation-e namotabar: `next` sefr bar. Bedune validator: `next` ye bar. Agar `next` throw konad: push-e exception, na `ErrorOr`.
