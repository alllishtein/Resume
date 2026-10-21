# 03 — Mediator

Vaghti chand object bayad ba ham kar konand, be-jaye inke har kodam baghiye ra beshnasad, hame faghat ye vasete ra mishenasand. Vasete tasmim migirad in payam be ki beresad.

## Moshkel

Dah class ke mostaghim ham ra seda mizanand, ye tar-e ankabut misazand. Avaz kardan-e yeki, baghiye ra mikeshad. Test-e yeki, sakhtan-e noh tay-e digar ra mikhahad.

## Ide

Do shekl az in harf vojud darad. Har do ra "Mediator" seda mizanand. To mosahebe begou kodam ra miguyi.

**Shekl-e ghadimi, mesl-e ye form.** Dokme nabayad text-box ra beshnasad. Har do ba object-e form harf mizanand. Ghanun-e "agar matn khali ast dokme khamush bashad" mal-e form ast, na mal-e dokme. Dokme baghiye-ye ghet'e-ha ra field nadarad.

**Shekl-e emruzi to backend, ke be an command bus ham miguyand.** Ye payam misazi, masalan `PlaceOrder`, va be `Send` midahi. Vasete daghighan ye handler baraye an noe peyda mikonad va natije ra barmigardanad. Ferestande esm-e handler ra nemidanad. Handler ferestande ra nemishnasad.

Shekl-e dovom sade-tar az form ast: ye payam, ye javab. Ketab-e ma'ruf-e GoF bishtar shekl-e avval ra gofte. MediatR shekl-e dovom ast.

Chand ghanun:

**Ferestande, class-e handler ra field nadarad.** Agar dashte bashad, vasete alaki ast. Faghat ye paresh-e ezafe shode.

**Ye Send, ye handler.** Agar chand nafar bayad khabar shavand va ferestande montazer-e javab-e yeki az an-ha nist, an Observer ast. `Send` va `Publish` ra yeki nakon.

**In vasete dakhel-e haman process ast va montazer-e javab mimanad.** Saf-e Rabbit nist. Retry va timeout-e saf inja nist.

**Ghanun-e dakhel-e mowjudiat ra to vasete nariz.** "Gheymat-e sefaresh mosbat bashad" mal-e `Order` ast. "In darkhast ra be in handler bedeh" mal-e vasete ast. Agar vasete por az if-e domain shavad, ye class-e ghul shode.

**Payam dade-ye sade ast.** Agar command ye `DbContext` ya ye mowjudiat-e dar hal-e ta'ghib ra bebarad, joda'i tamoom shode.

## Mesal-e koochik

```csharp
Result<Guid> id = await bus.Send(new PlaceOrder(customerId, lines), ct);

sealed class PlaceOrderHandler : IHandler<PlaceOrder, Guid>
{
    public Task<Result<Guid>> Handle(PlaceOrder cmd, CancellationToken ct) { ... }
}
```

Ferestande esm-e `PlaceOrderHandler` ra nadarad. Agar handler ra avaz koni, ferestande hamchenan compile mishavad.

## Ba chi ghalt mishavad

**Observer** chand shenavande darad va ferestande montazer-e natije-ye yeki az an-ha nist. Mediator to shekl-e bus ye handler va ye javab darad.

**Facade** ye zirsystem ra sade mikonad. Dakhel-e zirsystem hanuz momken ast class-ha ham ra beshenasand. Mediator daghighan haman shenakht-e mostaghim ra barmidarad.

**Saf-e payam** beyn-e process-ha ast. `Send` dakhel-e ye process ast.

## Koja estefade nakon

Do class dakhel-e ye mowjudiat ra ba vasete seda nazan. Seda zadan-e mostaghim roshan-tar ast.

Har method-e koochak ra command nakon ta "me'mari" be nazar beresad. Debug sakht mishavad va joda'i-ye vaghe'i nadari.

Handler-e A ke `Send` be B mizanad va B dobare A, halghe ast. Marz-e kar gom mishavad.

## Hala dar Dejban

Shekl-e ma command bus ast, ba MediatR. Dialog-e UI nist.

- `ICommand<TResponse>` va `IQuery<TResponse>` ru `IRequest<ErrorOr<TResponse>>` neshaste-and.
- `ICommand` alave bar an `IBaseCommand` ast ta validation faghat ru neveshtan bashad.
- Handler-ha `ICommandHandler` va `IQueryHandler` hastand.

Endpoint `ISender.Send(command)` mikonad. Noe-e handler ra field nadarad.

Peyda kardan-e handler ba scan-e assembly-e module-ha ast, to `ApplicationConfiguration` ba `AddMediatR`. Ye darkhast, ye handler. Do handler baraye ye command khatay-e zaman-e ejra ast, na chand shenavande.

Dor-e `Send` se raftar neshaste: exception, log, validation. In-ha khode vasete nistan. Zanjire-i hastand ke dor-e vasete pichide. Joz'iat-eshan daftarche-ye Chain ast. Inja faghat in ra negah dar: bus payam ra be ye handler miresanad. Zanjire mitavanad ghabl az handler payam ra bargardanad, masalan vaghti validation rad shavad.

In `Send` az process birun nemiravad. Khabar-e beyn-e module-ha event-e yekparche-sazi va MassTransit ast. Agar begouyi "module-ha ba MediatR harf mizanand" ghalat ast.

Handler-ha Scoped hastand chon context-e EF baraye har darkhast ast.

## Agar beporsand, in tor begou

> Do shekl daram. Form: ghet'e-ha faghat vasete ra mishenasand. Bus: ye payam, ye handler, ye javab. Dejban dovomi ast, ba MediatR. Endpoint `Send` mikonad va handler ra be esm nemishnasad. Ye command do handler nadarad. Log va validation dor-e bus hastand, khode bus nistan. Beyn-e module-ha `Send` nist. Event-e saf ast.

## Dah so'al

**1. Mediator che shenakhti ra barmidarad?**
Shenakht-e mostaghim-e hamkar be hamkar. Har kodam faghat vasete ra mishnasad.

**2. Ghanun-e "agar matn khali ast dokme khamush bashad" mal-e kist?**
Mal-e form, ke vasete ast. Mal-e khode dokme nist.

**3. Chera in pattern rahat ghul mishavad?**
Chon har hamahangi vasvase mishavad inja jam' shavad. Hamahangi inja bemanad. Ghanun-e dakhel-e mowjudiat sar-e jayesh.

**4. Farq-e Send va Publish chi ast?**
Send ye handler va ye javab. Publish chand shenavande, va ferestande montazer-e ye natije-ye moshakhas nist.

**5. Command bus cheghadr az Mediator-e form sade-tar ast?**
Raft-o-bargasht-e ghet'e-haye form ra nadarad. Faghat ye payam be ye handler, ba javab.

**6. Chera payam nabayad mowjudiat-e zende haml konad?**
Chon ferestande va handler dobare ba ye object-e moshtarak-e dakheli be ham michasband.

**7. To Dejban ferestande kist?**
Endpoint. Noe-e handler ra nemishnasad. Faghat command va `ISender` ra mishnasad.

**8. Chera `ICommand` joda az `IRequest` sakhte shode?**
Ta javab hatman `ErrorOr` bashad va validation-e pipeline faghat ru neveshtan beneshinad.

**9. Agar handler-e A, handler-e B ra Send konad che mishavad?**
Ejra mishavad, vali marz-e kar mishkanad va halghe momken ast. A bayad khodesh kar ra jelo bebarad ya event bezanad.

**10. In bus ba Rabbit yeki ast?**
Na. Dakhel-e process ast, montazer-e javab mimanad, ye handler darad, saf nadarad.
