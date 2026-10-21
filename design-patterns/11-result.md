# 11 — Result

---

## Ye khat

Function do rah darad: **movaffagh** ya **shekast-e ghaabel-e pishbini**. Har do ra to type-e bargashti mizarim ta caller majbur bashad har do ra bebine. `throw` baraye shekast-e ghaabel-e pishbini nist.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

`PlaceOrder` mitavanad be chand dalil-e **addi** shekast bokhorad: sabad khali ast, mojudi nist, code-e takhfif morde. In-ha bug nistan. Bakhshe-i az gharardad-e function-and.

Agar an-ha ra `throw` koni:

- emzaye method (`Order`) dorugh migoyad. Migooyad "Order midaham". Gahi Order nemidahad va control az stack birun miparad
- caller mitavanad catch nakonad va 500-e bi-ma'ni be karbar bedahad
- `catch (Exception)` bug-e vaghe'i va khataye business ra yekja ghaz mikonad
- jaryan-e adi-e "in code eshtebah bud" hazine va shakl-e exception migirad, va khanande-ye code rah-e shekast ra nemibinad

Agar `null` bar gardani: dalil-e shekast gom ast. Agar `(bool ok, T value)` bar gardani: mishe `ok == false` va `value` ham por bashad. Gharardad-e narm shekaste mishavad.

## Ta'rif

Result (va esm-e nazdik-e railway-oriented programming, Scott Wlaschin): type-i ke **ya** value darad **ya** khata. Na har do. Na hich-kodam.

```csharp
Result<Order> Place(Cart cart)
{
    if (cart.IsEmpty) return Error.Validation("cart", "empty");
    return Order.From(cart);   // implicit: Result success
}
```

Caller:

```csharp
result.Match(
    order => Save(order),
    error => Show(error));
```

`Match` do rah ra **ejbari** mikonad. `try/catch` in ejbar ra nadarad.

"Railway" tasvir-e hamin ast. Do riil. Movaffagh rooye riil-e sabz miravad. Avvalin khata mipare rooye riil-e ghermez, va ghadam-haye ba'd **ejra nemishavand**. `Bind` / `Then` / `Map` hamin avaz kardan-e riil-and, bedune `if` tooye har khat.

```csharp
Result<Receipt> Flow(Cart cart) =>
    Validate(cart)
        .Then(ReserveStock)
        .Then(Charge)
        .Then(BuildReceipt);
```

Agar `ReserveStock` khata dahad, `Charge` seda nemishavad. In hamun short-circuit-e zanjir ast, vali rooye **type**, na rooye exception.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| `Result<T>` / `ErrorOr<T>` | jabe-ye do halat |
| `Error` | dalil-e typed: code, matn, noe (validation, not found, conflict) |
| Function-e domain | `Result` bar migardanad, throw-e business nemikonad |
| `Match` / `Then` | caller ra rooye do rah mikeshanad |
| Marz-e birun (HTTP, UI) | `Error` ra be status va matn-e karbar tabdil mikonad |

Domain **nabayad** HTTP 404 beshnasad. Domain `NotFound` misazad. Marz-e web an ra be 404 tabdil mikonad. An tabdil adapter-e marz ast, na joz'-e Result.

## Ghanun-ha

**1. Do halat-e motenafi.**
API-e khoob `Value` ra vaghti khata dari partab mikonad ya aslan nemidahad. Dast-zadan-e `Value` bedune check, bug ast. `Match` an dast-zadan ra kamrar mikonad.

**2. Khata-ye ghaabel-e pishbini inja ast. Bug exception mimanad.**
"Code-e melli tekrar ast" → `Conflict`. "NullReference to mapper" → exception. Agar bug ra ham `Error.Unexpected` koni va ghaz koni, stack-e log ra az dast midi. Agar har do ra throw koni, caller farq ra nemibinad.

**3. Chand khata gahi yek javab-and.**
Form mitavanad ham email bad bashad ham nam khali. `Result` bayad **list**-e khata ra ham balad bashad, na faghat yek string. Validation-e zud-bazgasht (avvalin khata va boro) baraye in senario bad ast.

**4. `Then` khata ra chang nemizanad.**
Function-e `Then` faghat rooye success seda mishavad. Agar dakhel-e `Then` dobare `try/catch` koni va khata ra null koni, railway ra shekasti.

**5. Exception baraye control-flow-e adi na.**
`throw` baraye "mojudi nist" stack ra mikand, catch-e dur ra majbur mikonad, va to ba'zi runtime-ha geran-tar az return ast. Dalil-e asli **geran budan** nist. Dalil-e asli **namar'i** ast. Gerani far'e ast va faghat vaghti throw rooye rah-e por-tekrar dari mohem mishavad.

## Anva'-e khata ke be dard-e web mikhorad

| Noe | Ma'ni | Status-e ma'mool |
|---|---|---|
| Validation | vorudi bad, kar shoru nashod | 400 |
| NotFound | shenase nist | 404 |
| Conflict | halat-e alan in kar ra nemipazirad, ya tekrar | 409 |
| Unauthorized / Forbidden | ki hasti / haq nadari | 401 / 403 |
| Failure | shekast-e ma'lum-e gheyr-e bug, masalan service-e kharej javab-e ma'lum dad | 502 ya 400, amdan entekhab kon |

In jadval **gharardad-e marz** ast. Domain faghat noe ra mizanad. HTTP ra na.

## Farq-ha

**Exception.** Baraye shekast-e gheyr-e gharardad. Result baraye shekast-e dakhel-e gharardad. Har do to yek system-e salem hastand. Yeki jay-e digari ra nemigirad.

**`null`.** Faghat "nist". Dalil nadarad. Baraye NotFound-e bi-dalil kafi ast. Baraye validation na.

**Tuple-e `(bool, T, string)`.** Compiler to ra mojbur nemikonad. Result mojbur mikonad.

**Exception-e business-e typed (`NotFoundException`).** Behtar az `Exception` khali ast, vali hamchenan emza dorugh ast va `Match` nadarad. Result haman etela'at ra to type-e bargashti mizarad.

**GoF.** Result pattern-e GoF nist. Az jahan-e functional va az "functional core, imperative shell" amade. To mosahebe an ra GoF seda nakon.

## Koja bezan, koja nazan

Bezan baraye har shekasti ke caller-e doros bayad an ra be karbar ya be senario-ye ba'd neshan dahad.

Nazan baraye:

- bug va shekast-e mohit (disk, bug-e null). Exception.
- har method-e koochak-e private. Agar hame-ye `int Add(int,int)` `Result` bar gardanad, sholugh-e bi-dalil dari. Result rooye **marz-e senario** va **ghanun-e domain** mizendegi, na rooye har jam'e do adad

## Eshtebah-haye rayej

- `Result` ra throw kardan-e dobare to caller ("agar error, throw NotFoundException"). Pas hame-ye hazine-ye exception bargasht va type bi-karbord shod
- `Match` nakardan va `.Value` gereftan
- Qati kardan-e 400 va 500
- Domain ke `ProblemDetails` misazad. Domain be HTTP vast shode

## Mafhoom ra injoori begou

> "Result ya value ast ya khata, na har do. Shekast-e ghaabel-e pishbini return mishavad ta emzaye method dorugh nagoyad va caller har do rah ra Match konad. Then riil-e sabz ra edame midahad va riil-e ghermez ra short-circuit. Exception baraye bug mimanad. Chand khataye validation yek list ast. Domain code-e HTTP nemisazad. Marz an ra tarjome mikonad. GoF nist."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

Library **ErrorOr** ast. Gharardad:

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

Har use-case `ErrorOr<T>` bar migardanad. Handler `return id` ya `return Errors.Personnel.NotFound`. Conversion-e implicit jabe ra misazad. Handler `new ErrorOr<Guid>(...)` neminevisad.

Validation-e pipeline (chain) agar FluentValidation fail shavad, **ghabl** az handler `Error.Validation` misazad: code az esm-e property, description az message. Chand failure yek list. `ErrorOr.From(List<Error>)` ba reflection seda mishavad chon behavior type-e baz-e `ErrorOr<Guid>` ra to compile-time be soorat-e concrete nemishnasad. Railway-e ghermez inja handler ra ejra nemikonad.

Agar sakhtan-e `ErrorOr` az list nashavad, `ValidationException` partab mishavad. An rah-e ezterari ast, na rah-e adi.

Endpoint `Match` mikonad: success → `Results.Ok`, khata → `ApiResults.Problem`. In haman marz-e bakhsh-e avval ast. `ProblemDetails` (RFC 7807) inja sakhte mishavad, na dakhel-e entity.

`ExceptionHandlingPipelineBehavior` exception-e handle-nashode ra log mikonad va `DejbanException` mipichand, ba `innerException`. An rah-e bug ast. Khataye `ErrorOr` inja nemiad chon throw nashode. Do riil-e mokhtalef: type-e bargashti, va exception-e birun az gharardad.

Query ham `ErrorOr` ast. NotFound-e khandan side-effect nist. CQS shekaste nemishavad.

---

## Script-e 90 sanie

> "Result ya'ni shekast-e ghaabel-e pishbini joz'-e type-e bargashti ast. Ya value ya khata. Match caller ra mojbur mikonad. Then khata ra short-circuit mikonad. Exception baraye bug mimanad. GoF nist. Dejban ErrorOr ra rooye har command va query gozashte. Handler NotFound ya id bar migardanad. Validation-e pipeline agar fail shavad haman ErrorOr ra misazad va handler seda nemishavad. Endpoint Match mikonad be Ok ya ProblemDetails. Entity HTTP nemishnasad. Exception-e vaghe'i ra behavior-e joda log mikonad va mipichand, ghaz-e business error nist."

---

## 10 soal

**1. Chera emzaye `Order Place(...)` dorugh ast agar throw konad?**
Chon caller az rooye type fekr mikonad hamishe `Order` migirad. Rah-e shekast-e adi to emza nist.

**2. Railway chi ra short-circuit mikonad?**
Ghadam-e ba'd az avvalin khata. `Charge` ba'd az `Reserve` shekaste seda nemishavad.

**3. `null` che kam darad?**
Dalil nadarad va "khata" va "nist" ra yeki mikonad.

**4. Chand khataye form kojast?**
To yek `Result` ba list-e `Error`. Avvalin-khata-va-bargard baraye form-e chand field bad ast.

**5. Bug ra `Error` mikoni?**
Na. Exception mimanad ta stack va log bemanad. `Error` baraye chizi ast ke gharardad an ra pishbini karde.

**6. Domain 404 midahad?**
Na. `NotFound` midahad. Marz-e HTTP status misazad.

**7. `Then` va `Match` farq?**
`Then` riil ra edame midahad va `Result` jadid misazad. `Match` riil ra mibandad va asar-e nahayi (save, response) mikonad.

**8. To Dejban handler chetor khata bar migardanad?**
`return` kardan-e `Error` (masalan `Errors.Personnel.NotFound`) ya value. `ErrorOr<T>` implicit sakhte mishavad.

**9. Validation-e fail handler ra seda mizanad?**
Na. Pipeline `ErrorOr` validation misazad va `next` ra seda nemizanad.

**10. `DejbanException` rooye NotFound mipichad?**
Na. NotFound throw nist. `DejbanException` baraye exception-e handle-nashode-ye pipeline ast.
