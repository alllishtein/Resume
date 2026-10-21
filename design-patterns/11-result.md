# 11 — Result

Function do rah darad: movaffagh, ya shekast-e ghabel-e pishbini. Har do ra to type-e bargashti migozarim ta caller majbur bashad har do ra bebinad. `throw` baraye shekast-e adi nist.

## Moshkel

`PlaceOrder` mitavanad be dalil-e adi beshkand: sabad khali ast, mojudi nist, code-e takhfif morde. In-ha bug nistan. Bakhshi az gharardad-e function-and.

Agar an-ha ra `throw` koni:

- emzay-e method miguyad "Order midaham" va gahi Order nemidahad
- caller mitavanad catch nakonad va 500-e bi-ma'ni be karbar bedahad
- `catch (Exception)` bug-e vaghe'i va khatay-e business ra yekja ghaz mikonad

Agar `null` bargardani, dalil-e shekast gom ast. Agar `(bool ok, T value)` bargardani, mishe `ok == false` va `value` ham por bashad.

## Ide

Result type-i ast ke ya value darad ya khata. Na har do. Na hich-kodam.

```csharp
Result<Order> Place(Cart cart)
{
    if (cart.IsEmpty) return Error.Validation("cart", "empty");
    return Order.From(cart);
}
```

Caller:

```csharp
result.Match(
    order => Save(order),
    error => Show(error));
```

`Match` do rah ra ejbari mikonad. `try/catch` in ejbar ra nadarad.

Tasvir-e railway hamin ast. Do riil. Movaffagh ru riil-e sabz miravad. Avvalin khata mipare ru riil-e ghermez, va ghadam-haye ba'd ejra nemishavand.

```csharp
Result<Receipt> Flow(Cart cart) =>
    Validate(cart)
        .Then(ReserveStock)
        .Then(Charge)
        .Then(BuildReceipt);
```

Agar `ReserveStock` khata dahad, `Charge` seda nemishavad.

Chand ghanun:

**Do halat-e joda.** Dast zadan-e `Value` bedune check bug ast. `Match` an dast zadan ra kam mikonad.

**Khatay-e ghabel-e pishbini inja ast. Bug exception mimanad.** "Code-e melli tekrar ast" → `Conflict`. "NullReference to mapper" → exception. Agar bug ra ham `Error` koni va ghaz koni, stack-e log ra az dast midi.

**Chand khata gahi ye javab-and.** Form mitavanad ham email bad bashad ham nam khali. Result bayad list-e khata ra ham balad bashad, na faghat ye string.

**Domain code-e HTTP nemisazad.** Domain `NotFound` misazad. Marz-e web an ra be 404 tabdil mikonad.

Dalil-e asli-ye "exception baraye business na" geran budan nist. Dalil-e asli in ast ke rah-e shekast to emzay-e method penhan mimanad.

| Noe | Ma'ni | Status-e ma'mul |
|---|---|---|
| Validation | vorudi bad | 400 |
| NotFound | shenase nist | 404 |
| Conflict | halat-e alan in kar ra nemipazirad | 409 |
| Unauthorized / Forbidden | ki hasti / haq nadari | 401 / 403 |

In jadval gharardad-e marz ast. Domain faghat noe ra mizanad.

Result pattern-e GoF nist. Az jahan-e functional amade.

Result ru marz-e senario va ghanun-e domain mizendegi, na ru har jam'-e do adad. `int Add(int, int)` Result nemikhahad.

## Hala dar Dejban

Library ErrorOr ast.

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

Har use-case `ErrorOr<T>` barmigardanad. Handler `return id` ya `return Errors.Personnel.NotFound`. Conversion-e implicit jabe ra misazad.

Validation-e pipeline agar FluentValidation fail shavad, ghabl az handler `Error.Validation` misazad. Chand failure ye list. Handler seda nemishavad. Sakhtan-e `ErrorOr<T>` az type-e baz ba `ErrorOr.From` anjam mishavad. Agar an nashavad, `ValidationException` partab mishavad. Masir-e adi `ErrorOr` ast, na exception.

Endpoint `Match` mikonad: success → `Results.Ok`, khata → `ApiResults.Problem`. `ProblemDetails` inja sakhte mishavad, na dakhel-e entity.

`ExceptionHandlingPipelineBehavior` exception-e handle-nashode ra log mikonad va `DejbanException` mipichand. An rah-e bug ast. Khatay-e `ErrorOr` inja nemiad chon throw nashode.

Query ham `ErrorOr` ast. NotFound-e khandan side-effect nist.

## Agar beporsand, in tor begou

> Result yani shekast-e ghabel-e pishbini joz'-e type-e bargashti ast. Ya value ya khata. Match caller ra mojbur mikonad. Exception baraye bug mimanad. GoF nist. Dejban ErrorOr ra ru har command va query gozashte. Validation agar fail shavad haman ErrorOr ra misazad va handler seda nemishavad. Endpoint Match mikonad be Ok ya ProblemDetails. Entity HTTP nemishnasad.

## Dah so'al

**1. Chera emzay-e `Order Place(...)` dorugh ast agar throw konad?**
Chon caller az ru type fekr mikonad hamishe `Order` migirad. Rah-e shekast-e adi to emza nist.

**2. Railway chi ra short-circuit mikonad?**
Ghadam-e bad az avvalin khata. `Charge` bad az `Reserve`-e shekaste seda nemishavad.

**3. `null` che kam darad?**
Dalil nadarad va "khata" va "nist" ra yeki mikonad.

**4. Chand khatay-e form kojast?**
To ye Result ba list-e Error. Avvalin-khata-va-bargard baraye form-e chand field bad ast.

**5. Bug ra Error mikoni?**
Na. Exception mimanad ta stack va log bemanad.

**6. Domain 404 midahad?**
Na. `NotFound` midahad. Marz-e HTTP status misazad.

**7. `Then` va `Match` farq?**
`Then` riil ra edame midahad. `Match` riil ra mibandad va asar-e naha'i mikonad, mesl-e save ya response.

**8. To Dejban handler chetor khata bar migardanad?**
`return` kardan-e `Error` ya value. `ErrorOr<T>` implicit sakhte mishavad.

**9. Validation-e fail handler ra seda mizanad?**
Na. Pipeline `ErrorOr` misazad va `next` ra seda nemizanad.

**10. `DejbanException` ru NotFound mipichad?**
Na. NotFound throw nist. `DejbanException` baraye exception-e handle-nashode ast.
