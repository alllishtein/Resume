# 08 — Observer (domain event)

*Vaghti chizi etefagh oftad, shenavande-ha khabar mishavand. Sazande-ye event an-ha ra be esm nemishnasad.*

---

## Ye khat

Observer: subject taghir ra elam mikonad, observer-ha subscribe hastand. To DDD-e in proje, subject aggregate ast, elam `IDomainEvent` ast, subscribe handler-ha hastand ke ba reflection peyda mishavand.

## Do sath — in ra ghalt nagou

| | Domain event | Integration event |
|---|---|---|
| Mahdude | haman module | beyn-e module-ha |
| Kei paydar mishavad | ba `SaveChanges` (outbox) | ba'd az publish roye bus |
| Handler | `IDomainEventHandler<T>` to Application | `IIntegrationEventHandler<T>` to Presentation |
| Mesal | `PersonnelUpdatedDomainEvent` | `UnitCreated` ke Visitors/Vehicles/WeighBridge consume mikonand |

Aggregate **integration event** publish nemikonad. Aggregate faghat domain event `Raise` mikonad. Yek domain-handler mitavanad ba'dan integration event besazad. In joda'i mohem ast: domain be Rabbit vaghe'i nist.

## Subject

`Dejban.Common.Domain/Entity.cs`

```csharp
public abstract class Entity
{
    private readonly List<IDomainEvent> _domainEvents = [];

    public IReadOnlyCollection<IDomainEvent> DomainEvents => [.. _domainEvents];

    public void ClearDomainEvents() => _domainEvents.Clear();

    protected void Raise(IDomainEvent domainEvent) => _domainEvents.Add(domainEvent);
}
```

- List **private** ast. Birun `Add` nemikonad.
- `Raise` **protected** ast. Faghat method-e khod-e entity.
- `DomainEvents` read-only ast.
- `ClearDomainEvents` public ast ta infrastructure ba'd az jam' kardan, list ra khali konad va dobare publish nashavad.

In observer-e **pull + deferred** ast: event-ha ja-be-ja shode va ba'dan khande mishavand. `Raise` haman lahze handler ra seda nemizanad. Dalil: handler nabayad ghabl az commit-e movaffagh kar-e khareji konad.

## Shenavande

`DomainEventHandlersFactory` hame-ye `IDomainEventHandler<T>`-haye assembly ra baraye haman `T` bar migardanad. **Chand** handler baraye yek event ghanuni ast. In farq-e asli ba MediatR `Send` ast (yek handler).

Har handler ba decorator-e idempotent wrap shode. Pas "khabar" had-aghall yek bar-e mofid ast, na dobar-e kamel (ketabche-ye 06).

## Flow

```
personnel.SoftDelete(...)
  → Raise(new PersonnelDeleted...)     // faghat list-e memory
unitOfWork.SaveChangesAsync
  → aggregate + outbox message         // yek transaction
ProcessOutboxJob
  → factory handler-ha ra peyda mikonad
  → decorator, ba'd handler
  → handler shayad integration event publish konad
module-e digar
  → inbox + IdempotentIntegrationEventHandler
```

## Chera na call-e mostaghim

`Personnel` nabayad `VisitorRepository` ra beshnasad. Module-ha be ham reference-e domain nemidahand. Event in rah ra miposhkanad. Gheymat: trace sakht-tar, va tartib-e handler-ha ra gharardad-e sakht farz nakon magar an ra neveshte bashi.

## Farq ba pub/sub-e bus

Observer-e in ketabche in-process ast (handler-haye haman module). Bus (MassTransit) beyn-e process ast. Har do "khabar bedune esm-e shenavande" hastand. Avali ba commit-e database jor shode, dovomi ba queue.

## Script-e 60 sanie

> "Aggregate ba `Raise` event ra to list-e private mirizad va kasi ra seda nemizanad. `Raise` protected ast ta faghat method-e entity event besazad. Ba'd az `SaveChanges`, outbox an-ha ra bar midarad va `DomainEventHandlersFactory` hame-ye handler-haye an type ra peyda mikonad. Chand handler mojaz ast; in `Send`-e MediatR nist. Domain event az module birun nemiravad. Age module-e digar bayad bedanad, handler yek integration event misazad va an az inbox-e maghsad rad mishavad."

---

## 10 soal

**1. Chera `Raise` haman lahze handler ra seda nemizanad?**
Chon transaction shayad rollback shavad. Khabar-e zud = kar-e khareji baraye chizi ke commit nashode.

**2. Chera list private ast?**
Ta application event-e ja'li `Add` nakonad va invariant-e "event faghat az method-e entity" bemanad.

**3. `ClearDomainEvents` chera public ast age list private ast?**
Infrastructure bayad ba'd az copy be outbox list ra pak konad. Pak kardan ba publish kardan farq darad. Ezafe kardan hanuz mamnoo' ast.

**4. Chand observer?**
Chand `IDomainEventHandler<T>`. Factory hame ra bar migardanad. `Send` yek handler darad.

**5. Domain event va integration event?**
Domain: haman module, ghabl/hamrah-e commit. Integration: gharardad-e beyn-e module, bus, inbox. Aggregate dovomi ra nemishnasad.

**6. Age handler khodesh aggregate ra avaz konad va `SaveChanges` bezanad?**
Momken ast vali event-e jadid bayad dobare jam' shavad. Loop va transaction-e deraz risk ast. Handler bayad kutah bashad.

**7. Tartib-e handler-ha?**
`GetTypes` tartib-e gharardad-e business nadarad. Handler-ha bayad mostaghel bashand. Age tartib mohem ast, yek handler-e vaghed an-ha ra be tartib seda bezanad.

**8. Observer-e klasik `Subscribe` darad. Inja kojast?**
Subscribe = "class-e to in assembly `IDomainEventHandler<T>` ra implement kon". Scan jaye list-e dasti-e `+=` neshast. Kamtar faramoosh mishavad.

**9. Chetor test mikoni?**
Method-e entity ra seda bezan va `DomainEvents` ra assert kon. Handler ra joda, ba event-e dasti, test kon. Test-e "aya factory an ra did" integration-e sabok ast.

**10. Memory leak-e observer-e klasik inja hast?**
Na be shekl-e `+=` ke unsubscribe nashavad. Risk-e digar: event-e bozorg to list ta save bemanad. Request-e kutah an ra mahdud mikonad. Context-e scoped ra singleton nakon.
