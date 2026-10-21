# 10 — Template Method

---

## Ye khat

Pedar **tartib** ra ghofl mikonad. Bache faghat ghadam-hayi ra por mikonad ke pedar esm-eshan ra az ghabl gozashte. Bache tartib ra avaz nemikonad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Chand class kar-e yeksan darand, ba yek ya do ekhtelaf:

- hame: file ra baz kon, parse kon, zakhire kon, file ra beband
- ekhtelaf: parser-e CSV ya parser-e XML

Agar har class hame-ye tartib ra copy konad, taghir-e "ghabl az zakhire lock begir" ra bayad hame-ja tekrari anjam bedahi. Yeki ja mimimand.

Agar tartib ra ham be bache bespari, digar tartib-e vahed nadari. Har bache `Save` ra ghabl az `Parse` seda mizanad.

Template Method vasat-e in do ta ast: tartib yek bar to pedar, ekhtelaf to method-haye baz.

## Ta'rif-e GoF

Intent: skeleton-e algorithm ra to yek method tarif kon, va bazi ghadam-ha ra be subclass-ha bespar. Subclass mitavanad ghadam ra avaz konad, **bedune** avaz kardan-e sakhtar-e algorithm.

Hollywood principle haminja sakhte shod: "don't call us, we'll call you." Bache pedar ra baraye tartib seda nemizanad. Pedar, bache ra seda mizanad.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| AbstractClass | method-e template (sabet) + hook-haye abstract ya virtual |
| ConcreteClass | faqat hook-ha ra por mikonad |

Method-e template aksaran **nabayad** virtual bashad. Agar bashad, bache kol-e skeleton ra override mikonad va pattern ra dor mizanad. Hook-ha virtual ya abstract-and.

## Sakhtar

```csharp
abstract class Importer
{
    public void Run(Stream input)          // template: sabet
    {
        Open(input);
        var rows = Parse(input);           // hook
        Validate(rows);                    // hook-e ba default
        Save(rows);                        // hook
        Close();
    }

    protected abstract IReadOnlyList<Row> Parse(Stream input);
    protected abstract void Save(IReadOnlyList<Row> rows);
    protected virtual void Validate(IReadOnlyList<Row> rows) { }
    private void Open(Stream input) { }
    private void Close() { }
}
```

`Run` public va gheyr-e virtual. `Parse` abstract chon default-e ma'ni nadarad. `Validate` virtual chon "hichi nakon" default-e ghabool ast. `Open` private chon joz'-e skeleton ast va bache nabayad an ra bebine.

## Ghanun-ha

**1. Skeleton yek method ast, na "hamin class abstract ast".**
Har class-e `abstract` template method nist. Pattern vaghti ast ke yek method tartib ra seda mizanad va hook-ha daghighan ja-haye baz-e **haman** tartib-and. Abstract-e bi-tartib faghat inheritance ast.

**2. Bache tartib ra nemidanad va nabayad bedanad.**
Agar bache `Parse` ra seda bezanad va khodesh `Save` ra ham seda bezanad, do tartib dari. Hook faghat ghadam-e khod ra anjam midahad va barmigardad.

**3. `abstract` ya `virtual` amdan entekhab mishavad.**
`abstract`: ghadam ejbari, default-e dorost vojud nadarad. `virtual` ba badan-e khali: ghadam ekhtiari (hook-e vaghe'i-e GoF). Ghalt: hame ra abstract kardan ta bache-ye bi-niyaz ham method-e khali benevisad. Ya hame ra virtual kardan ta bache-ye faramoosh ghadam-e ejbari ra skip konad.

**4. Skeleton kutah mimanad.**
Taghir-e pedar hame-ye bache-ha ra mikeshad. Esm-e in dard: fragile base class. Agar skeleton har hafte avaz mishavad, pattern-e ghalat ra entekhab kard-e-i. Strategy (composition) behtar tahammol mikonad.

**5. Hook be vaziat-e pedar-e protected-e kheili ziad dast nazanad.**
Agar bache bayad panj field-e protected ra bedanad ta `Parse` ra benevisad, joda'i dorough ast. Vorudi-e hook bayad parameter bashad.

## Farq ba Strategy — so'al-e hatmi

Har do "bakhsh-e motaghayer" ra joda mikonand.

| | Template Method | Strategy |
|---|---|---|
| Vasl | inheritance | composition (interface) |
| Zaman-e entekhab | compile-time, ba class-e bache | runtime, ba dadan-e object |
| Ki tartib ra darad | pedar | context, ya khod-e strategy agar kol-e algorithm avaz shavad |
| Tarkib-e do ekhtelaf | subclass-e jadid, ya hook-e dovom | do object-e joda ke mishe avaz-eshan kard |
| Test-e bache | aksaran ba pedar | strategy ra tanha test mikoni |

Agar ekhtelaf **chand** ta ast va mikhahi tarkib-e azad (parser-e CSV + zakhire-ye SQL, ya CSV + file), strategy ya decorator behtar ast. Template vaghti **yek** skeleton-e sakht dari va ekhtelaf-ha ghadam-haye ma'loom-e haman skeleton-and.

Template ra "strategy-e inheritance-i" ham seda mizanand. Mafhoom nazdik ast. Sakhtar na. To mosahebe sakhtar ra begou.

## Farq ba Factory Method

Factory Method yek halat-e khasi-e haman fekr ast: skeleton yek method-e `Create` ra seda mizanad va bache mahsul ra misazad. Agar **faghat** sakhtan-e object avaz mishavad, esm-e daghigh factory method ast. Agar chand ghadam-e algorithm avaz mishavad, template method-e am-tar ast. Factory method zir-majmoe-ye fekri-e template ast, na zed-e an.

## Koja bezan, koja nazan

Bezan vaghti chand class yek tartib-e hatmi darand va do ghadam-eshan farq mikonad, va an tartib nabayad ghabel-e override bashad.

Nazan vaghti:

- skeleton har bar avaz mishavad (fragile base)
- tarkib-e runtime mikhahi
- faghat yek bache dari. Method-e sade kafi ast. Pedar-e abstract baraye yek class parsa-bazi ast

## Eshtebah-haye rayej

- Template-e virtual ke bache kol-e `Run` ra override mikonad
- Pedar-e 40 method-e protected ke bache bayad zendegi-e dakheli-e pedar ra balad bashad
- Seda kardan-e "har inheritance template ast"
- Copy-e skeleton to 8 class va goftan-e "ba'dan pedar misazim". Alan pattern ra **nadari**. Fursat-e pedar dari

## Mafhoom ra injoori begou

> "Template method skeleton-e sabet-e pedar ast va hook-e bache. Pedar bache ra seda mizanad, na baraks. Method-e skeleton ra virtual nemikonam ta tartib shekaste nashavad. Abstract yani ejbari, virtual-e khali yani ekhtiari. Farq-ash ba strategy inheritance dar barabar-e composition ast. Agar faghat sakhtan-e object hook bashad, factory method ast. Pedar-e bozorg fragile base class mishavad."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

`Dejban.Common.Application/Messaging/DomainEventHandler.cs`

```csharp
public abstract class DomainEventHandler<TDomainEvent> : IDomainEventHandler<TDomainEvent>
    where TDomainEvent : IDomainEvent
{
    public abstract Task Handle(TDomainEvent domainEvent, CancellationToken cancellationToken = default);

    public Task Handle(IDomainEvent domainEvent, CancellationToken cancellationToken = default) =>
        Handle((TDomainEvent)domainEvent, cancellationToken);
}
```

Skeleton: `Handle(IDomainEvent)`.
Hook: `Handle(TDomainEvent)`.

Tartib-e ghofl-shode kootah vali vaghe'i ast:

1. vorudi-e gheyr-generic ra begir — factory va list-e event type-e baz darand
2. an ra be `T` cast kon
3. hook-e bache ra seda bezan

Bache (`Personnel...Handler` ya decorator-e idempotent) faghat hook ra minevisad. Cast ra copy nemikonad. Agar farda "ghabl az hook, null ra rad kon" be method-e gheyr-generic ezafe shavad, hame-ye bache-ha an ra ers mibarand. Haman dalil-e pattern.

Hollywood inja: factory `Handle(IDomainEvent)` ra seda mizanad. An method, hook-e bache ra seda mizanad. Bache tasmim nemigirad cast kei bashad.

`abstract` budan-e hook dorost ast: handler-i ke `Handle(T)` nadarad handler nist. Default-e khali ma'ni nadarad.

Hamin skeleton baraye `IntegrationEventHandler<T>` hast. Do pedar, yek mafhoom, do marz-e event.

**Chizi ke template nist, hatman inja begou:**
Job-e `ProcessOutboxJob` har module shekl-e yeksan darad (bekhan, batch, handler, mark) vali class-e concrete-e joda neveshte shode. Skeleton-e vahed **nist**. Fursat-e template ya strategy hast. Agar beporand "outbox template method ast?" javab: na. Tekrar-e sakhtar ast, pedar-e ghofl-konande nist.

Pipeline-e MediatR ham template method nist. Tartib-ash composition-e chain ast, na `base.Handle`.

Decorator-e idempotent az hamin pedar inherit mikonad va hook ra override mikonad, vali raftar-e "ghabl va ba'd" decorator ast (composition-e `decorated`). Do pattern rooye yek class. Pedar cast ra ghofl karde. Wrapper idempotency ra ezafe karde. An-ha ra yek esm nada.

---

## Script-e 90 sanie

> "Template method ya'ni pedar tartib ra ghofl mikonad va bache faghat hook ra por mikonad. Skeleton nabayad virtual bashad. Abstract hook ejbari ast, virtual-e khali ekhtiari. Strategy haman niyaz ra ba composition va runtime hal mikonad. Factory method halat-e khasi ast ke hook faghat sakhtan-e object ast. To Dejban `DomainEventHandler<T>` skeleton-e koochak darad: `Handle` gheyr-generic cast mikonad va `Handle` generic-e abstract ra seda mizanad. Job-haye outbox har module copy shode-and va pedar-e vahed nadarand. An ra template-e mojood seda nemizanam."

---

## 10 soal

**1. Kodam method template ast va kodam hook?**
Template tartib-e public-e sabet. Hook abstract ya virtual ke pedar an ra seda mizanad.

**2. Hollywood principle inja yani chi?**
Bache pedar ra orkestrate nemikonad. Pedar bache ra seda mizanad.

**3. Chera template virtual nist?**
Chon bache kol-e tartib ra avaz mikonad va skeleton dige ghofl nist.

**4. `abstract` ya `virtual`?**
Abstract ghadam-e bi-default-e ejbari. Virtual ba badan-e khali ghadam-e ekhtiari.

**5. Fragile base class chist?**
Taghir-e koochak-e pedar raftar-e hame-ye bache-ha ra mikanad, chon bache-ha be joz'iat-e pedar vast-and.

**6. Farq ba strategy?**
Inheritance va entekhab-e compile-time, dar barabar-e composition va entekhab-e runtime.

**7. Farq ba factory method?**
Factory method hook-e sakhtan-e object ast. Template method skeleton-e am-tar ba chand hook-e mojaz.

**8. Har `abstract class` template ast?**
Na. Bayad yek method tartib ra ghofl karde bashad va hook-ha ja-haye baz-e haman tartib bashand.

**9. To Dejban skeleton-e `DomainEventHandler` chi ra ghofl karde?**
Cast az `IDomainEvent` be `T` va seda zadan-e hook-e typed. Bache cast ra copy nemikonad.

**10. Chera job-e outbox ra template-e mojood hesab nemikoni?**
Tartib-e zehni yeki ast vali pedar-e moshtarak an tartib ra ghofl nakarde. Har module class-e khod ra dare. Pattern vaghti pedar vojud darad, na vaghti copy-ha shabihand.
