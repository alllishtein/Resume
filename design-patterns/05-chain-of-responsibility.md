# 05 — Chain of Responsibility

---

## Ye khat

Yek darkhast az yek zanjire-ye halqe rad mishavad. Har halqe ya khodesh an ra tamoom mikonad, ya be halqe-ye ba'di midahad. Darkhast-dehande nemidanad kodam halqe javab dade.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Yek kar-e "mohiti" hast ke be **hame-ye** senario-ha ta'allogh darad, na be ghanun-e yek senario: log, validation-e shekl, authentication, metric, tarjome-ye exception.

Agar an ra dakhel-e har senario copy koni:

- yeki faramoosh mishavad
- taghir-e policy yani dast zadan be dah-ha class
- senario-e business por az code-i mishavad ke mal-e an nist

Chain in kar-e mohiti ra **birun** az senario, be tartib-e sabet, mizananad. Senario faqat kar-e khod ra midanad.

## Ta'rif-e GoF

Intent: jeloye vast shodan-e sender be receiver ra begir, ba dadan-e shans be chand object ke an darkhast ra handle konand. Halqe-ha zanjir mishavand va darkhast ta ja-i ke yek halqe an ra bardarad jolo miravad.

Do nokte-ye ketab:

- sender receiver-e daghigh ra nemishnasad
- **bishtar az yek** object mitavanad baraye handle shodan candidate bashad. Kodam-esh, runtime moshakhas mishavad

Mesal-e klassik: support-e sath-e 1, agar natavanest sath-e 2, agar natavanest sath-e 3. Ya filter-haye ruydad-e UI: yek widget event ra mikhorad ya be parent pas midahad.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Handler | gharardad-e `Handle(request)` va danestan-e "ba'di kist" |
| ConcreteHandler | ya kar mikonad, ya `next` ra seda mizanad, ya har do (kari kon **va** be-de boro) |
| Client | faghat avval-e zanjir ra mishanad. Baghi ra na |

"Ba'di kist" mitavanad reference-e classic (`Successor`) bashad, ya yek delegate be nam-e `next` ke kas-e digar zanjir ra sakhte. Har do chain-and. Dovomi shekl-e modern-e middleware ast.

## Sakhtar

Shekl-e klassik:

```
Client -> H1.next = H2
          H2.next = H3
          H3.next = null

H1: agar mal-e man nist, Successor.Handle
```

Shekl-e pipeline (middleware):

```
Client -> H1(request, next = H2)
            H2(request, next = H3)
              H3(request, next = senario)
```

Farq-e amali-e dovom: har halqe **ham ghabl az next, ham ba'd az next** kar mikonad. Mesal: log-e "shoru'", `next()`, log-e "payan va modat". Shekl-e klassik-e GoF aksaran faghat ya-man-ya-ba'di ast va ba'd az successor kari nemikonad.

To mosahebe begou: "GoF successor-e yek-tarafe ast. Middleware haman chain ast vali dor-e `next` baz va baste mishavad, pas mitavanad ba'd az handler ham kar konad."

## Ghanun-ha

**1. Tartib joz'-e gharardad ast.**
Validation ghabl az senario. Log dor-e hame chiz, pas birun-tar. Exception-handler birun-tarin, ta khataye log ra ham begirad. Avaz kardan-e tartib, ma'ni-e zanjir ra avaz mikonad. "Har ki zood-tar register shod" bayad sanad dashte bashad, na shans.

**2. Halqe mitavanad zanjir ra beborad.**
Agar validation fail shod va `next` seda nashod, senario **nabayad** ejra shavad. An short-circuit ast va kol-e arzesh-e pattern baraye hamin ghat' kardan-ha ast. Halqe-i ke hamishe `next` ra seda mizanad va hich sharti nadarad, faghat decorator-e barname-nevisi ast.

**3. Halqe ghanun-e senario ra balad nist.**
Validation-e "in field khali nabashad" halqe ast. Validation-e "in code-e melli to in tenant tekrar nabashad" aksaran senario ast, chon database va ghanun-e haman aggregate ra mikhahad. Agar hame-ye if-haye business ra be halqe-ye aval borti, zanjir God Object shode.

**4. Halqe-ha bayad mostaghel-e yekdigar bashand.**
Agar H2 farz konad H1 yek field-e khasi ra por karde va an sanad nashode bashad, zanjir-e penhan dari. Gharardad-e beyne halqe-ha bayad haman `request` va `response` bashad, na side-channel-e namoshakhas.

**5. Client zanjir ra jam' nemikonad.**
Agar har use-case khodesh `new Log(new Validation(new Handler()))` benevisad, dobare copy dari. Jam' kardan-e zanjir yek ja (startup, factory) ast.

## Anva'

**Klassik-e GoF.** Har concrete tasmim migirad successor ra seda bezanad ya na. Zanjir mitavanad to runtime toolani ya kutah shavad.

**Middleware / pipeline.** `next` delegate. Ghabl va ba'd. ASP.NET Core hamin ast: authentication, routing, endpoint. Har `Use` yek halqe.

**Chain-e filter-e UI.** Event-e click az bache be pedar miravad ta yeki an ra "bekhorad".

**Chain-e tasvib.** Mablagh-e koochak ra modir-e tim, bozorg-tar ra modir-e vahed. Avvalin kasi ke **hagh** darad, zanjir ra mibandad. In nazdik-tarin mesal be motan-e GoF ast.

## Mesal-e donya-ye pipeline

```csharp
async Task<Result<T>> Validate<T>(Command cmd, Func<Task<Result<T>>> next)
{
    var errors = validator.Check(cmd);
    if (errors.Count > 0) return Result<T>.Fail(errors);
    return await next();
}
```

Agar `Fail` bargardi, `next` seda nashode. Handler-e business khab nist. In kol-e pattern dar 6 khat ast.

## Farq-ha

**Decorator.** Decorator haman interface ra wrap mikonad va **hamishe** (ya taghriban hamishe) original ra seda mizanad, ba kar-e ghabl ya ba'd. Chain chand halqe-ye **ham-noghsh** darad ke har kodam mitavanad beguyad "mal-e man nist" ya "hamin-ja bas ast". Decorator-e chand-ta'e rooye ham shabihe chain mishavad. Farq-e mosahebe: chain baraye **entekhab ya ghat'**, decorator baraye **ezafe kardan-e behavior bedune taghir-e masir**.

**Mediator.** Mediator yek vasete-ye markazi ast ke migoyad ki ba ki. Chain list-e khati ast va har halqe faghat ba'di ra midanad, na hame ra.

**Strategy.** Strategy yek algorithm ra **jaigozin** mikonad. Chain chand algorithm-e ehtemali ra **posht-e sar-e ham** emtehan mikonad ta yeki bepazirad.

## Koja bezan, koja nazan

Bezan baraye concern-e tekrari-e hame-ye darkhast-ha, va baraye tasvib/filter-i ke receiver-e nahayi az ghabl maloom nist.

Nazan vaghti zanjir-e 15 halqe dari va hich-kas tartib ra balad nist. Debug az call-e mostaghim sakht-tar mishavad. Va nazan vaghti faghat yek `if` dari. `if` zanjir nist.

## Eshtebah-haye rayej

- Faramoosh kardan-e `next` va tamoom shodan-e bi-sedaye request
- Halqe-ye business-e khasi (faghat yek command) dakhel-e zanjir-e hamegani
- Tartib-e eshtebah: log-e "success" ghabl az validation
- E'temad be tartib-e reflection bedune test

## Mafhoom ra injoori begou

> "Chain ya'ni sender nemidanad ki darkhast ra tamoom mikonad. Har halqe ya an ra bar midarad ya be ba'di midahad. Shekl-e middleware alave bar an, dor-e `next` baz va baste mishavad pas ghabl va ba'd har do mojaz ast. Short-circuit bakhsh-e pattern ast: validation-e bad nabayad be senario beresad. Tartib gharardad ast. Farq-ash ba decorator in ast ke decorator masir ra nemiborad. Farq-ash ba strategy in ast ke strategy yek algorithm ra jaygozin mikonad, na chand filter-e posht-e sar-e ham."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

Do zanjir-e joda darim. An-ha ra yeki nakon.

**Zanjir-e HTTP** (middleware-e ASP.NET): ghabl az endpoint. Authentication, tenant, route. In haman shekl-e `next` ast. Ketabche-ye joda-ye pipeline-e ASP.NET hast. Inja faghat marz-ash ra mishenasim.

**Zanjir-e use-case** (MediatR `IPipelineBehavior`): ba'd az endpoint, ghabl az handler.

Sabt to `Dejban.Common.Application/ApplicationConfiguration.cs`:

```csharp
config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
```

Avvalin `AddOpenBehavior` biruni-tarin halqe ast. Pas:

```
Send
  -> ExceptionHandling     try { next } catch -> log + DejbanException
       -> RequestLogging   ghabl va ba'd az next
            -> Validation  agar khata: next() nashavad
                 -> Handler
```

In daghighan shekl-e pipeline-e bakhsh-e avval ast, na shekl-e successor-e yek-tarafe-ye sade. Log **ba'd** az handler ham kar darad. Exception **dor-e** hame chiz ast.

Validation short-circuit mikonad. Constraint-ash:

```csharp
where TRequest : IBaseCommand
where TResponse : IErrorOr
```

Pas query aslan vared-e in halqe nemishavad. Command-e bi-validator `next()` mishavad. Command-e namotabar `Error.Validation` bar migardanad va handler seda **nemishavad**. Sakhtan-e `ErrorOr<T>` az type-e baz ba `ErrorOr.From` anjam mishavad. Agar an nashavad, `ValidationException` partab mishavad. Masir-e adi `ErrorOr` ast, na exception. In vasl-e chain be Result ast.

Exception behavior khataye business ra ghaz nemikonad, chon business `ErrorOr` ast va throw nist. Faghat shekast-e gheyr-montazere ra mipichand ta stack-e asli `innerException` bemanad.

Client-e zanjir (`IEndpoint`) behavior-ha ra `new` nemikonad. Startup an-ha ra jam' mikonad. Haman ghanun-e "client zanjir ra nasazad".

---

## Script-e 90 sanie

> "Chain ya'ni darkhast az halqe-ha rad mishavad va sender nemidanad ki an ra tamoom kard. GoF successor-e yek-tarafe darad. Middleware `next` darad pas ghabl va ba'd har do mishe, va mitavanad zanjir ra beborad. Dejban do zanjir darad: HTTP ghabl az endpoint, va MediatR ghabl az handler. Dakhel-e dovomi tartib in ast: exception birun, log vasat, validation dakhel. Validation faghat command ast va agar fail shavad handler ejra nemishavad. Log ba'd az handler ham modat ra mizanad. In decorator nist chon decorator baraye ghat'-e masir nist."

---

## 10 soal

**1. Sender to chain che chizi ra nemidanad?**
Inke kodam concrete dar nahayat darkhast ra handle mikonad.

**2. Short-circuit chist?**
Halqe `next` ra seda nemizanad. Baghi-e zanjir, az jomle senario, ejra nemishavad.

**3. Farq-e successor-e GoF va `next`-e middleware?**
GoF aksaran ya-man-ya-ba'di ast. Middleware mitavanad ghabl **va** ba'd az `next` kar konad, mesl-e log-e zaman.

**4. Tartib chera gharardad ast?**
Chon ma'ni-e "log dor-e exception" ya "exception dor-e log" avaz mishavad. Taghir-e tartib = taghir-e raftar.

**5. Che chizi nabayad to halqe-ye hamegani bashad?**
Ghanun-e khas-e yek aggregate ke database-e haman senario ra mikhahad. An mal-e handler ast.

**6. Farq ba decorator?**
Decorator behavior ezafe mikonad va masir ra negah midarad. Chain mitavanad beguyad "hamin-ja tamoom" ya "mal-e man nist, boro ba'di".

**7. Farq ba strategy?**
Strategy yek algorithm-e entekhab-shode ast. Chain chand candidate-e posht-e sar-e ham ast.

**8. To Dejban tartib-e behavior-ha chi migoyad?**
Exception biruni-tarin, ba'd log, ba'd validation, ba'd handler. Avvalin `AddOpenBehavior` birun ast.

**9. Chera query validate-e in behavior nemishavad?**
Constraint-e `TRequest : IBaseCommand`. Query an ra nadarad. Short-circuit-e validation mal-e command ast.

**10. Test-e zanjir ra chetor mishkani?**
Validation-e namotabar: `next` sefr bar. Validation-e khali: `next` yek bar. `next` ke throw konad: wrapper-e exception, na `ErrorOr`.
