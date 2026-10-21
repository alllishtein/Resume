# 10 — Template Method

Pedar tartib-e kar ra ghofl mikonad. Bache faghat ghadam-hayi ra por mikonad ke pedar esm-eshan ra az ghabl gozashte. Bache tartib ra avaz nemikonad.

## Moshkel

Chand class kar-e yeksan darand, ba yeki do ekhtelaf.

Hame: file ra baz kon, bekhan, zakhire kon, beband.
Ekhtelaf: khandan-e CSV ya khandan-e XML.

Agar har class hame-ye tartib ra copy konad, taghir-e "ghabl az zakhire ghofl begir" ra bayad hame-ja tekrar koni. Yeki ja mimanad.

Agar tartib ra ham be bache bespari, digar tartib-e vahed nadari. Yeki `Save` ra ghabl az khandan seda mizanad.

## Ide

Pedar ye method darad ke tartib ra seda mizanad. Ja-haye motaghayer method-e joda hastand. Bache faghat haman-ha ra por mikonad.

Be in miguyand: ma to ra seda mizanim, to ma ra baraye tartib seda nazan. Bache pedar ra kargardani nemikonad. Pedar bache ra seda mizanad.

```csharp
abstract class Importer
{
    public void Run(Stream input)          // tartib, sabet
    {
        Open(input);
        var rows = Parse(input);           // bache por mikonad
        Validate(rows);                    // ekhtiari, default khali
        Save(rows);                        // bache por mikonad
        Close();
    }

    protected abstract IReadOnlyList<Row> Parse(Stream input);
    protected abstract void Save(IReadOnlyList<Row> rows);
    protected virtual void Validate(IReadOnlyList<Row> rows) { }
}
```

`Run` nabayad virtual bashad. Agar bashad, bache kol-e tartib ra avaz mikonad va ghofl shekaste.

`abstract` yani ghadam ejbari ast va default-e dorost vojud nadarad. `virtual` ba badan-e khali yani ghadam ekhtiari ast. Hame ra abstract kardan bache ra majbur mikonad method-e khali benevisad. Hame ra virtual kardan bache-ye faramushkar ghadam-e ejbari ra skip mikonad.

Har class-e `abstract` in pattern nist. Pattern vaghti ast ke ye method tartib ra seda mizanad va method-haye baz daghighan ja-haye haman tartib-and.

Pedar ra kuta negah dar. Taghir-e pedar hame-ye bache-ha ra mikeshad. Agar pedar har hafte avaz mishavad, pattern-e ghalat ra entekhab kard-e-i.

## Ba Strategy ghalt nashavad

Har do "bakhsh-e motaghayer" ra joda mikonand.

| | Template Method | Strategy |
|---|---|---|
| Vasl | inheritance | composition |
| Zaman-e entekhab | compile-time, ba class-e bache | runtime, ba dadan-e object |
| Ki tartib ra darad | pedar | context, ya khode strategy |

Agar ekhtelaf chand ta ast va mikhahi tarkib-e azad (CSV ba SQL, ya CSV ba file), Strategy behtar ast. Template vaghti ye tartib-e sakht dari va ekhtelaf-ha ghadam-haye malum-e haman tartib-and.

Agar faghat sakhtan-e object avaz mishavad, esm-e daghigh Factory Method ast. Factory Method halat-e khasi-ye hamin fekr ast.

## Koja estefade nakon

Faghat ye bache dari. Method-e sade kafi ast. Pedar-e abstract baraye ye class ezafe ast.

Tartib har bar avaz mishavad. Pedar-e bozorg shekanande mishavad. Strategy tahammol-e behtar darad.

## Hala dar Dejban

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

Tartib-e ghofl-shode: `Handle(IDomainEvent)`.
Ghadam-e bache: `Handle(TDomainEvent)`.

1. vorudi-ye gheyr-e generic ra begir, chon factory type-e baz darad
2. an ra be `T` cast kon
3. method-e bache ra seda bezan

Bache faghat method-e typed ra minevisad. Cast ra copy nemikonad. Agar farda "ghabl az hook, null ra rad kon" be method-e gheyr-e generic ezafe shavad, hame-ye bache-ha an ra ers mibarand.

`abstract` budan dorost ast: handler-i ke `Handle(T)` nadarad handler nist.

Hamin shekl baraye `IntegrationEventHandler<T>` hast. Do pedar, ye mafhum, do marz-e event.

Job-e `ProcessOutboxJob` har module shekl-e yeksan darad, vali class-e joda neveshte shode. Pedar-e moshtarak an tartib ra ghofl nakarde. Agar beporsand "outbox template method ast?" javab: na. Tekrar-e sakhtar ast, ghofl nist.

Pipeline-e MediatR ham in pattern nist. Tartib-ash chain ast, na `base.Handle`.

Pushesh-e idempotent az hamin pedar inherit mikonad, vali raftar-e "ghabl va bad" Decorator ast. Do pattern ru ye class. Pedar cast ra ghofl karde. Pushesh tekrar ra kam mikonad.

## Agar beporsand, in tor begou

> Template method yani pedar tartib ra ghofl mikonad va bache faghat ghadam-e baz ra por mikonad. Method-e tartib ra virtual nemikonam. Abstract yani ejbari, virtual-e khali yani ekhtiari. Strategy haman niaz ra ba composition va runtime hal mikonad. To Dejban `DomainEventHandler<T>` cast az `IDomainEvent` be `T` ra ghofl karde va method-e typed ra seda mizanad. Job-haye outbox har module copy shode-and va pedar-e vahed nadarand. An ra in pattern seda nemizanam.

## Dah so'al

**1. Kodam method tartib ast va kodam ghadam-e bache?**
Tartib method-e public-e sabet. Ghadam-e bache abstract ya virtual ke pedar an ra seda mizanad.

**2. "Ma to ra seda mizanim" yani chi?**
Bache pedar ra orkestre nemikonad. Pedar bache ra seda mizanad.

**3. Chera method-e tartib virtual nist?**
Chon bache kol-e tartib ra avaz mikonad va ghofl mimanad shekaste.

**4. `abstract` ya `virtual`?**
Abstract ghadam-e bi-default va ejbari. Virtual ba badan-e khali ghadam-e ekhtiari.

**5. Pedar-e bozorg che dardi darad?**
Taghir-e koochak-e pedar raftar-e hame-ye bache-ha ra mikanad.

**6. Farq ba Strategy?**
Inheritance va entekhab-e compile-time, dar barabar-e composition va entekhab-e runtime.

**7. Farq ba Factory Method?**
Factory Method ghadam-e sakhtan-e object ast. Template method tartib-e am-tar ba chand ghadam-e baz.

**8. Har `abstract class` in pattern ast?**
Na. Bayad ye method tartib ra ghofl karde bashad.

**9. To Dejban `DomainEventHandler` chi ra ghofl karde?**
Cast az `IDomainEvent` be `T` va seda zadan-e method-e typed. Bache cast ra copy nemikonad.

**10. Chera job-e outbox ra in pattern hesab nemikoni?**
Tartib-e zehni yeki ast vali pedar-e moshtarak an ra ghofl nakarde. Har module class-e khod ra darad.
