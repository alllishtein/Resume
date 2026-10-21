# 06 — Decorator

---

## Ye khat

Yek object ra dakhel-e object-e digar mizarim ke **haman interface** ra darad. Client fargh ra nemibinad. Wrapper ghabl ya ba'd az original, kar-e ezafe mikonad. Original ra edit nemikoni.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Class-e `OrderSender` kar-ash ferestadan ast. Ba'd mikhahi:

- log
- retry
- cache
- "agar hamin kar ra dobare ferestadim, dobare nafrest"

Agar har kodam ra ba `if` dakhel-e `OrderSender` bezani, class chand dalil baraye taghir peida mikonad. Agar ba inheritance `LoggingOrderSender : OrderSender` besazi, tarkib-e "log + retry + cache" ya selasele-ye enfejari mishavad (`LoggingRetryCacheSender`) ya aslan ghabel-e tarkib nist.

Decorator tarkib ra az rah-e **composition** midahad: har kar-e ezafe yek wrapper, va wrapper-ha rooye ham michinand. Mesl-e lebas: badan yeki ast, kot va kafsh joda pushidani-and.

## Ta'rif-e GoF

Intent: be yek object, **dynamic**, mas'uliat-e ezafe bedeh. Decorator jaygozin-e amali-e subclass ast baraye expand kardan-e raftar.

Kalame-ye `dynamic` mohem ast. Subclass ra compile-time entekhab mikoni. Decorator ra runtime vasl mikoni: emruz ba log, farda bi log, bedune taghir-e class-e asli.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Component | interface-e moshtarak (`Send`, `Handle`, `Read`) |
| ConcreteComponent | kar-e asli, bi-khabar az wrapper |
| Decorator | haman interface ra implement mikonad va yek `Component` dakheli darad |
| ConcreteDecorator | kar-e ezafe + seda zadan-e dakheli |

Client type-e `Component` ra mibinad. Nemidanad concrete ast ya do laye wrapper.

## Sakhtar

```
Client
  -> LoggingDecorator      (Component)
       -> RetryDecorator   (Component)
            -> OrderSender (ConcreteComponent)
```

Har laye faghat laye-ye dakheli ra mishnasad, an ham faghat ba interface. `OrderSender` hich-kodam decorator ra nemishnasad. In hamon "original ra edit nakon" ast.

Shekl-e call:

```
client.Send()
  log("before")
    retry
      orderSender.Send()
    (agar fail, retry)
  log("after")
```

## Ghanun-ha

**1. Interface-e birun va dakhel yeki ast.**
Agar wrapper method-e jadid-e `SendWithLog` bar gardanad va client ra majbur konad an ra seda bezanad, decorator nist. Facade ya adapter-e shekaste ast. Arzesh-e decorator in ast ke client **avaz nashavad**.

**2. Decorator owner-e kar-e asli nist.**
Kar-e asli ra forward mikonad. Agar forward nakonad va khodesh hame chiz ra dobare benevisad, wrapper-e dorough ast.

**3. Tarkib-pazir ast.**
Do decorator-e ham-interface bayad betavanand rooye ham beneshinand. Pas decorator nabayad farz konad dakheli-ash hatman concrete-e asli ast. Dakheli mitavanad khodesh decorator bashad.

**4. Shaffaf budan hazine darad.**
Client nemidanad cache ya retry hast. In khoob ast ta vaghti raftar-e ezafe **gheyr-e montazere** nashavad. Retry-e penhan mitavanad side-effect-e "email" ra do bar ejra konad. Decorator-e ba side-effect bayad gharardad-e idempotent budan-e dakheli ra boland begoyad.

**5. Tartib-e wrap ma'ni darad.**
Log-e birun-e retry: yek log, chand talash-e dakheli. Log-e dakhel-e retry: har talash yek log. Haman do class, do tartib, do raftar. Tartib ra sanad kon.

## Anva'

**Decorator-e amalkard.** Log, metric, cache, retry, lock. Original ra avaz nemikonad. Faghat dorash chiz mizanad.

**Decorator-e filter.** Ghabl az original tasmim migirad aslan seda bezanad ya na. "Agar hamin payam ra dide-am, original ra seda nazan." Hanuz decorator ast agar interface yeki bashad. Nazdik-e marz-e chain mishavad. Farq: yek wrapper dor-e yek object-e moshakhas, na zanjir-e candidate-haye ham-arz.

**Decorator-e tarjome-ye natije.** Original `int` midahad, wrapper haman interface ra negah midarad vali natije ra ghabl az bargasht fix mikonad. Agar interface avaz shavad, digar decorator nist. Adapter ast.

## Mesal-e donya

```csharp
interface INotifier { Task SendAsync(string message, CancellationToken ct); }

sealed class EmailNotifier : INotifier
{
    public Task SendAsync(string message, CancellationToken ct) => /* smtp */;
}

sealed class IdempotentNotifier(INotifier inner, ISeenStore seen) : INotifier
{
    public async Task SendAsync(string message, CancellationToken ct)
    {
        if (await seen.AlreadyAsync(message, ct)) return;
        await inner.SendAsync(message, ct);
        await seen.MarkAsync(message, ct);
    }
}
```

`EmailNotifier` az `seen` khabar nadarad. Client `INotifier` mikhahad va `IdempotentNotifier` migirad. Test-e email bedune `seen` anjam mishavad. Test-e idempotency ba `inner`-e fake anjam mishavad.

Nokte-ye hamin mesal, chon ba'd to proje tekrari ast: `Mark` **ba'd** az `Send` ast. Agar `Send` throw konad, mark nemishavad va retry mojaz ast. Agar `Send` movaffagh bashad va `Mark` fail shavad, retry dobare `Send` mikonad. Pas decorator "daghighan yek bar" ra jadoo nemikonad. "Talash-e dobare ra kam mikonad" va dakheli bayad dobare-kari ra tahammol konad. In joz'-e mafhoom ast, na joz'-e yek bug-e proje.

## Farq-ha

| | Decorator | Inheritance | Proxy | Chain |
|---|---|---|---|---|
| Vasl | composition, haman interface | subclass | composition, haman interface | list-e handler |
| Hadaf | behavior-e ezafe, tarkib-pazir | taghir-e daste | kontrol-e dastresi, often yek laye (lazy, remote, security) | entekhab ya ghat'-e masir |
| Dakheli khabar darad? | na | `base` ra midanad | na | faghat next |

Proxy-e GoF va Decorator sakhtar-e yekshan darand. Farq **hadaf** ast. Proxy ja-neshin ast: dastresi, mahal, ya hazine-ye sakhtan ra kontrol mikonad va mas'uliat-e jadid-e business ezafe nemikonad. Decorator mas'uliat-e jadid ezafe mikonad. Agar to mosahebe har wrap ra decorator seda koni, miporsand farq-e proxy chist. Javab hamin paraghraf ast.

Strategy algorithm ra **avaz** mikonad (dakheli-e motefavet). Decorator algorithm ra **mipooshand** (dakheli haman mimanad, dorash chiz-e jadid).

## Koja bezan, koja nazan

Bezan vaghti chand tarkib-e raftar-e ezafe mikhahi va nemikhahi subclass-e `A+B+C` besazi, va client nabayad taghir konad.

Nazan vaghti:

- faghat yek `if` to yek class. Wrapper-e tak-estefade hazine-ye zehni ast
- wrapper-e panj-kar (log+retry+auth+cache+metric) to yek class. An dobare chand-dalil shode. Har kar yek laye
- interface anqadr bozorg ast ke wrapper bayad dah method-e bi-rabt ra pass konad. Avval interface ra koochak kon

## Eshtebah-haye rayej

- Farz-e exactly-once bedune transaction-e moshtarak-e "kar + mark"
- Tartib-e wrap-e tasadofi
- Decorator-i ke be concrete-e dakheli cast mikonad. Tarkib-paziri mire
- Inheritance-e `LoggingEmail : Email` va seda kardan-e an "decorator". Sakhtar inheritance ast

## Mafhoom ra injoori begou

> "Decorator haman interface ra wrap mikonad ta raftar-e ezafe, bedune edit-e asli va bedune taghir-e client, ezafe shavad. Tarkib-ash composition ast, pas chand wrapper rooye ham michinand va tartib-eshan ma'ni darad. Az inheritance kamtar shekanande ast chon asli wrapper ra nemishnasad. Az proxy ba hadaf joda mishavad: proxy dastresi ra kontrol mikonad, decorator mas'uliat ezafe mikonad. Agar mark-e 'anjam shod' ba'd az kar-e asli bashad, exactly-once nist."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

`IdempotentDomainEventHandler<TDomainEvent>` haman `IdempotentNotifier` ast.

Path: `Personnels/.../Outbox/IdempotentDomainEventHandler.cs` (va hamta-ye har module).

- Component: `DomainEventHandler<T>` / `IDomainEventHandler<T>`
- Concrete: handler-e business, masalan handler-e `PersonnelCreated`
- Decorator: `IdempotentDomainEventHandler`
- Dakheli: parameter-e `decorated`

Raftar-e ezafe: ghabl az `decorated.Handle` to jadval-e `personnels.outbox_message_consumers` migardad. Kilid `domainEvent.Id` be alave-ye **esm-e type-e dakheli** (`decorated.GetType().Name`). Esm-e khod-e decorator na, chon baraye hame yek esm ast va do handler-e yek event ra ghalt yeki mikonad.

Agar satr hast, `decorated` seda **nemishavad**. In haman decorator-e filter ast. Agar nist, avval dakheli, ba'd insert.

Insert ba'd az handle ast. Pas haman nokte-ye bakhsh-e avval inja zende ast: exception-e handle → mark nist → retry mojaz. Handle-e movaffagh va insert-e fail → retry momken ast handle ra dobare seda bezanad. Jomle-ye dorost "at-least-once ba dedupe", na "exactly-once".

Vasl shodan-e wrapper dasti-e `new` nist. `PersonnelsModule.AddDomainEventHandlers` ba Scrutor:

```csharp
services.TryAddScoped(domainEventHandler);
services.Decorate(domainEventHandler, closedIdempotentHandler);
```

`Decorate` yani har ki an handler ra bekhad, wrapper ra migirad, va wrapper original ra be onvan-e `decorated` migirad. Client (`DomainEventHandlersFactory` ke `GetRequiredService` mikonad) type-e business ra mikhahad va decorator migirad. Original az idempotency khabar nadarad. Test-e ghanun-e business bedune jadval-e consumer mojaz mimanad.

Hamin sakhtar, joda, baraye integration event: `IdempotentIntegrationEventHandler` va `AddIntegrationEventHandlers`. Do decorator, do jadval, yek mafhoom.

Pipeline-e MediatR (log, validation) az nazar-e sakhtar wrap ast, vali **chain** ast chon chand halqe-ye ham-noghsh va short-circuit-e validation darad. An ra inja decorator-e idempotency seda nakon.

---

## Script-e 90 sanie

> "Decorator ya'ni wrapper-e haman interface, composition na inheritance, client avaz nemishavad, va chand laye rooye ham tartib-e ma'ni-dar darand. Proxy dastresi ra kontrol mikonad. Decorator mas'uliat ezafe mikonad. Mark-e ba'd-az-kar exactly-once nist. To Dejban `IdempotentDomainEventHandler` dor-e handler-e domain neshast. Kilid-ash id-e event va esm-e handler-e dakheli ast. Scrutor ba `Decorate` an ra vasl mikonad ta factory haman type ra bekhad va wrapper begirad. Handle-e throw mark nemizanad. Integration event decorator-e joda-ye hamin olgu ra darad."

---

## 10 soal

**1. Chera inheritance baraye "log + retry + cache" bad ast?**
Tarkib-ha enfejar mikonand: har zirmajmue yek subclass. Composition har laye ra yek bar minevisi va rooye ham migozari.

**2. Client che chizi ra nabayad bebine?**
Type-e concrete-e wrapper. Agar mojbur shavad method-e jadid seda bezanad, interface shekaste va decorator nist.

**3. Tartib-e do decorator che ra avaz mikonad?**
Mahdude-ye "ghabl va ba'd". Log-e birun-e retry yek record baraye chand talash ast. Baraks, har talash ra log mikonad.

**4. Farq ba proxy?**
Sakhtar nazdik ast. Proxy kontrol-e dastresi ya hazine-ye sakhtan ast. Decorator mas'uliat-e jadid-e raftari ast.

**5. Farq ba chain?**
Chain chand candidate darad va masir ra miborad. Decorator yek original-e moshakhas ra mipooshand.

**6. Chera mark-e ba'd az kar exactly-once nist?**
Beyne movaffaghiat-e kar va movaffaghiat-e mark, crash mitavanad kar ra dobare pish biyavarad.

**7. To Dejban original chetor az wrapper joda test mishavad?**
Handler-e business `decorated` nist. Decorator ba DI push shode. Test-e ghanun wrapper va SQL-e consumer ra nemibinad.

**8. Chera `GetType()` roye `decorated` ast na `this`?**
`this` hame-ye event-ha ra yek esm mikonad. Dedup bayad handler-e business ra joda konad.

**9. Do handler baraye yek event chand bar ejra mishavand?**
Har kodam yek bar. Do esm, do satr. Decorator-e har handler joda wrap shode.

**10. `services.Decorate` az nazar-e pattern chi mikonad?**
Assembly-e runtime-e zanjir-e wrapper. Client `GetRequiredService(handlerType)` mizanad va biruni-tarin decorator ra migirad, bedune `new` dasti.
