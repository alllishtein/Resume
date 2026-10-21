# 03 — Mediator

---

## Ye khat

Vaghti chand object bayad ba ham kar konand, bejaye inke har kodam baghi ra beshnasad, hame faghat **yek vasete** ra mishenasand. Vasete tasmim migirad in payam be ki beravad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Dah object ke har kodam mostaghim baghi ra seda mizanad, `10 × 9` felesh-e "man to ra mishnasam" misazad. Avaz kardan-e yeki, baghi ra mikeshad. Test-e yeki, sakhtan-e noh-taye digar ra mikhahad.

In web-e object-ha ast. Mediator an ra setare mikonad: hame faghat vasete ra mishenasand. Tedad-e felesh-e vaghe'i az moraba' be khati miravad.

## Ta'rif-e GoF

Intent-e ketab: interaction-e yek grup object ra dakhel-e yek object-e mediator jam' kon. Object-ha lazem nist yekdigar ra refer konand. An-ha mostaghel mishavand, va interaction-eshan joda avaz mishavad.

Kalame-ye mohem: **interaction**. Mediator faghat "yeksan konande-ye function call" nist. Ja-i ast ke **ghava'ed-e hamkari** zendegi mikonad. "Agar dialog-e login submit shod, button-e OK fa'al shavad va text-box-e khata pak shavad" — in ghanun-e dialog ast, na ghanun-e button. Button mediator ra seda mizanad. Button text-box ra nemishnasad.

## Sherkat-konande-ha

| Naghsh-e GoF | Mani |
|---|---|
| Mediator | interface-e vasete. Colleague-ha in ra mishenasand |
| ConcreteMediator | ghanun-e hamkari-e in senario |
| Colleague | object-i ke baghi-e colleague-ha ra nemishnasad. Faghat mediator ra |

Colleague mitavanad **khabar** bedahad ("man avaz shodam") va mitavanad **dastur** begirad ("khodet ra disable kon"). Har do az rah-e mediator. Felesh-e mostaghim-e colleague be colleague nist.

## Sakhtar

```
Button ---\
TextBox ---+--> Mediator --> ghanun-e dialog --> Button / TextBox
CheckBox --/
```

Button `TextBox` ra field nadarad. Agar farda `CheckBox` hazf shavad, `Button` compile mishavad. Faghat mediator avaz mishavad.

## Do shekl ke bayad joda koni

**Mediator-e GoF-e ghadimi (dialog, form, air-traffic).**
Concrete mediator colleague-ha ra be esm mishnasad va method-e an-ha ra seda mizanad. Colleague-ha mediator ra mishenasand. Interaction **chand-ta'e va do-tarafe** ast. Mesal-e kitab: dialog-e UI, borj-e moraghebe-ye parvaz. Hame-ye havapeyma ba borj harf mizanand, ba ham na.

**Mediator be shekl-e command bus (MediatR va shabihesh).**
Yek payam-e dakhel-e yek object (`Command`) miravad tu `Send`. Bus **yek** handler baraye an type peyda mikonad va natije ra bar migardanad. Sender handler ra be esm nemishnasad. Handler sender ra nemishnasad. Interaction inja sade-tar az dialog-e GoF ast: yek payam, yek pasokh, na web-e widget-ha.

Har do ra "mediator" seda mizanand. To mosahebe **begou kodam**. Agar begoyi MediatR va masal-e borj-e parvaz ra ghalt tarif koni, shekaf maloom mishavad. Jomle-ye dorost:

> "GoF mediator interaction-e chand colleague ra markazi mikonad. Command bus yek halat-e khasi ast: sender faghat payam ra midahad, bus yek handler ra peyda mikonad, va pipeline-e vasete mitavanad ghabl az handler kar-e ezafe konad."

## Ghanun-ha

**1. Sender concrete-e receiver ra field nadarad.**
Agar dashte bashad, mediator-e dorough ast. Faghat yek hop-e ezafe dari.

**2. Yek `Send` yek handler.**
Agar chand nafar bayad khabar shavand va sender montazer-e natije-ye yeki nabashad, an **observer** ast, na mediator. Ghalt-e bozorg-e mosahebe hamin yeki kardan-e `Send` va `Publish` ast.

**3. Mediator-e in-process montazer-e javab mimimand.**
Caller `await` mikonad. Natije bargasht mikhorad. An bus-e shabake nist. Timeout va retry-e Rabbit inja nist.

**4. Ghanun-e business-e colleague ra be mediator naspar.**
Mediator ghanun-e **hamkari** ra darad, na ghanun-e dakheli-e yek object. "Gheymat-e sefaresh mosbat bashad" mal-e `Order` ast. "In form submit shod, in se service ra be in tartib seda bezan" mal-e mediator ya use-case ast. Agar mediator khodesh hame-ye if-haye domain ra jam' konad, shode God Object. Pattern shekaste.

**5. Payam bayad dade-ye kham bashad, na object-e zende-ye kasi digar.**
Command field-haye sade darad. Agar command yek `DbContext` ya yek entity-e track-shode haml konad, joda'i tamoom shode.

## Anva'

**Mediator-e UI.** Haman GoF. Widget-ha.

**Command bus / Mediator-e application.** `Send(command) → result`. Yek handler. Pipeline-e log va validation mitavanad **dor-e** an bashad. Pipeline khodesh chain of responsibility ast ke rooye mediator neshast. Do pattern. Yeki nagir.

**Query bus.** Haman shekl, payam-e bi-khatar-e neveshtan. CQRS rooye hamin savar mishavad.

**Event aggregator.** Chandin publisher, chandin subscriber, vasete-ye markazi. In nazdiktar be observer-e markazi ast. Ba `Send`-e yek-handler eshtebah nagir.

## Mesal-e donya-ye bus

```csharp
// sender faghat in ra midanad:
Result<Guid> id = await bus.Send(new PlaceOrder(customerId, lines), ct);

// yek class-e digar, to assembly-e digar:
sealed class PlaceOrderHandler : IHandler<PlaceOrder, Guid>
{
    public Task<Result<Guid>> Handle(PlaceOrder cmd, CancellationToken ct) { ... }
}
```

Sender esm-e `PlaceOrderHandler` ra nadarad. Agar handler ra avaz koni, sender compile mimanad. Bus ba type-e `PlaceOrder` handler ra peyda mikonad.

## Farq-ha

| | Mediator | Observer | Facade |
|---|---|---|---|
| Chand girande | dar bus: yek. dar GoF: chand colleague vali az rah-e yek vasete | chand, va sender montazer-e javab-e yeki nist | yek vorudi-e sade be subsystem |
| Ki ki ra mishnasad | colleague-ha hamdigar ra na | subject list-e observer darad ya baraks | client facade ra, facade dakhel ra |
| Natije | pasokh-e senario | elam-e "shod" | sade-sazi |

Facade subsystem ra **sade** mikonad. Mediator colleague-ha ra **az ham bi-khabar** mikonad. Facade dakhel mitavanad hamchenan be ham vast bashad. Mediator daghighan an vast-e dakheli ra hazf mikonad.

## Koja bezan, koja nazan

Bezan vaghti tedad-e sender va receiver ziyad ast va nemikhahi har sender har receiver ra compile-time beshnasad, ya mikhahi yek pipeline-e sabet dor-e har payam dashte bashi.

Nazan vaghti:

- do class-e haman aggregate. Call-e mostaghim sade-tar va roshan-tar ast
- mediator ra ja-ye domain gozashti va class-e mediator 2000 khat `if` shode
- `Send` ra baraye "hame-ye kas-ha bekhahand" estefade mikoni. An publish ast

## Eshtebah-haye rayej

- Har method-e koochak ra command kardan ta "mimari" be nazar beravad. Hop-e ezafe, debug-e sakht, hich joda'i-e vaghe'i
- Handler-e A ke `Send`-e B mizanad va B dobare A. Cycle, va transaction-e namoshakhas
- Farz kardan bus-e in-process haman gharanti-e Rabbit ra darad
- Do handler baraye yek command va ta'ajob az exception-e runtime. Gharardad-e `Send` yek handler ast. Compile an ra nemibinad

## Mafhoom ra injoori begou

> "Mediator felesh-e mostaghim-e colleague-ha ra hazf mikonad. To shekl-e GoF, vasete ghanun-e hamkari-e chand widget ra darad. To shekl-e command bus, sender yek payam midahad va bus daghighan yek handler bar migardanad va natije ra pas midahad. Chand shenavande-ye bi-entezar-e javab observer ast. Mediator-e khoob God Object nemishavad. Ghanun-e dakhel-e entity sar-e jash mimimand."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

In proje shekl-e **command bus** ra darad, na dialog-e GoF. Library MediatR ast.

Gharardad-e ma rooye gharardad-e library neshast:

- `ICommand<TResponse>` va `IQuery<TResponse>` az `IRequest<ErrorOr<TResponse>>` ers mibarand
- `ICommand` alave bar an `IBaseCommand` ast ta pipeline-e validation faghat roye write benshinad
- handler-ha `ICommandHandler` / `IQueryHandler` hastand ke khodeshan `IRequestHandler`-e MediatR-and

Endpoint `ISender.Send(command)` mikonad. Type-e handler ra field nadarad. An haman ghanun-e "sender concrete ra nemishnasad" ast.

Peyda kardan-e handler ba scan-e assembly-e module-ha ast (`AddMediatR` + `RegisterServicesFromAssemblies` to `ApplicationConfiguration`). Yek request, yek handler. Do handler baraye yek command khataye runtime-e MediatR ast, na chand observer.

Dor-e `Send` se behavior neshast (exception, log, validation). An-ha **mediator nistand**. Chain-e rooye mediator-and. Tartib-e `AddOpenBehavior` avalin-sabt ra biruni-tarin mikonad. Joz'iat-e zanjir ketabche-ye chain ast. Inja faghat in ra negah dar: bus payam ra be yek handler mirasanad. Zanjir mitavanad ghabl az an handler payam ra rad konad (validation-e namotabar).

In `Send` az process birun nemiravad. Khabar-e beyn-e module integration event va MassTransit ast. Agar to mosahebe begoyi "module-ha ba MediatR harf mizanand", ghalat ast. Module-ha ba event-e bus harf mizanand. Dakhel-e yek process, endpoint ba handler az rah-e MediatR.

Handler-ha scoped-and chon context-e EF scoped ast. Mediator-e singleton ke handler-e scoped ra ghalat negah darad, haman bug-e lifetime ast. MediatR in ra per request dorost mikonad. Tozih-e mosahebe: "bus in-process ast, handler ba request zende mishavad, chon UoW-e haman request ra mikhahad."

---

## Script-e 90 sanie

> "Do mediator darim to zehn. GoF: chand colleague faghat vasete ra mishenasand va ghanun-e hamkari anja ast. Command bus: yek payam, yek handler, yek javab. Dejban dovomi ast, ba MediatR. Endpoint `ISender.Send` mikonad va handler ra be esm nemishnasad. `ICommand` va `IQuery` rooye `IRequest` neshastand va `ErrorOr` bar migardanand. Yek command do handler nadarad. Behavior-haye log va validation dor-e bus-and, khod-e bus nistand. Beyn-e module-ha `Send` nist. Event-e bus ast."

---

## 10 soal

**1. Mediator-e GoF che felesh-i ra hazf mikonad?**
Felesh-e mostaghim-e colleague be colleague. Har colleague faghat mediator ra mishnasad.

**2. Ghanun-e "button ra disable kon agar text khali ast" mal-e kist?**
Mal-e mediator-e dialog. Mal-e button nist, chon button nabayad text-box ra beshnasad.

**3. Chera God Object shodan asan ast?**
Chon har interaction vasvase darad inja jam' shavad. Marz: hamkari inja, invariant-e object sar-e jaye khod.

**4. `Send` va `Publish` farq?**
`Send` yek handler va yek javab. `Publish` chand shenavande va sender montazer-e yek natije-ye business nist. Dovomi observer ast.

**5. Command bus che-ghadr az GoF kamtar ast?**
Interaction-e do-tarafe-ye widget-ha ra nadarad. Faghat payam-e yek-tarafe be yek handler, ba bargasht-e natije.

**6. Chera payam nabayad entity-e zende haml konad?**
Chon joda'i tamoom mishavad. Sender va handler dobare ba object-e moshtarak-e dakheli be ham vast mishavand.

**7. To Dejban sender kist va chi ra nemishnasad?**
Endpoint. Type-e concrete-e handler ra nemishnasad. Faghat command va `ISender` ra mishnasad.

**8. Chera `ICommand` joda az `IRequest` sakhtid?**
Ta javab hatman `ErrorOr` bashad va validation-e pipeline faghat roye write (`IBaseCommand`) benshinad.

**9. Agar handler-e A, `Send`-e B konad chi mishavad?**
Teknikally ejra mishavad. Az nazar-e tarahi, marz-e senario shekaste va cycle momken ast. A bayad khodesh orchestrate konad ya event bezanad.

**10. In bus ba Rabbit yeki ast?**
Na. In-process, hamzaman az nazar-e caller, yek handler, bedune queue. Rabbit integration event ast.
