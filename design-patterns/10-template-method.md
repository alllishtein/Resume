# 10 — Template Method

*Skeleton-e algorithm to base class ast. Subclass faghat ghadam-e moteghayer ra por mikonad.*

---

## Ye khat

Template Method: method-e public-e base tartib-e kar ra qof mikonad va yek ya chand method-e abstract ra seda mizanad. Subclass nemitavanad tartib ra be-zanad, faghat joz'-e khod ra.

## Code-e in proje

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

Skeleton inja koochak vali vaghe'i ast:

1. Vorudi-e **gheyr-generic** (`IDomainEvent`) ra begir — chon factory va list-e event type-e baz darand.
2. Cast be `TDomainEvent`.
3. Method-e abstract-e subclass ra seda bezan.

Subclass (`IdempotentDomainEventHandler` ya handler-e business) faghat `Handle(TDomainEvent)` ra minevisad. Cast-e eshtebah va signature-e interface yek ja ast.

Hamin shekl baraye `IntegrationEventHandler<T>` hast.

## Chera in template ast na "faghat inheritance"

Inheritance har reuse-i nist. Template Method vaghti **tartib** qof shode bashad va noghte-haye baz (`abstract` / `virtual`) ma'loom bashand. Inja noghte-ye baz yek dane ast: `Handle(T)`. Noghte-ye sabet: cast + ertebat ba `IDomainEventHandler`.

Agar farda log-e "ghabl va ba'd" ra be method-e gheyr-generic ezafe koni, hame-ye handler-ha an ra miras mibarand bedune copy. An haman elat-e pattern ast.

## Ja-haye digar ke skeleton dari

- Pipeline-e MediatR skeleton-e **composition** ast (chain), na template method. Tartib to base class nist.
- `Entity.Raise` template nist. Faqat yek ghadam ast.
- Job-e outbox: "bekhan, batch, handler, mark" mitavanest template method bashad. To code bishtar class-e concrete-e tekrari-e har module ast. An ra template-e kamel seda **nazan**. Begou: "template-e vaghe'i-e ma `DomainEventHandler<T>` ast; job-ha copy shode-and va mitavanestand skeleton-e moshtarak dashte bashand."

In sedaghat to mosahebe ghavidar-tar az an ast ke har class-e `abstract` ra template seda koni.

## Farq

| | Template Method | Strategy | Decorator |
|---|---|---|---|
| Vasl | inheritance, compile-time | interface, runtime | wrap, runtime |
| Ki tartib ra darad | base class | client ya context | wrapper |
| Avaz kardan-e algorithm | subclass-e jadid | object-e jadid | wrapper-e jadid |
| Inja | cast + `Handle(T)` | ACL, in series na | idempotency |

Strategy ra inheritance-e template ghalt napazir: strategy composition ast va runtime avaz mishavad. Template avaz-e algorithm = class-e jadid.

## Hollywood principle

"Don't call us, we'll call you." Subclass base ra baraye tartib seda nemizanad. Base, subclass ra seda mizanad. `Handle(IDomainEvent)` to base, `Handle(T)` to bache ra seda mizanad. Bache tasmim nemigirad ke cast kei bashad.

## Script-e 60 sanie

> "`DomainEventHandler<T>` template method-e koochak-e ma ast. Method-e gheyr-generic ke factory mibinad, event ra be T cast mikonad va method-e abstract ra seda mizanad. Handler-e business faghat haman method ra por mikonad. Idempotency ra inja nazashtim; an decorator ast, chon composition ast va test-e handler ra be SQL vasl nemikonad. Har abstract class template nist."

---

## 10 soal

**1. Template method ra to yek jomle?**
Base tartib ra darad, subclass ghadam-haye abstract ra por mikonad.

**2. Kodam method skeleton ast va kodam hook?**
Skeleton: `Handle(IDomainEvent)`. Hook: `Handle(TDomainEvent)`.

**3. Chera do `Handle`?**
Interface-e gheyr-generic baraye factory va list. Method-e generic baraye handler-e type-safe. Cast yek ja, na to har subclass.

**4. Farq ba strategy?**
Template inheritance ast va tartib sabet. Strategy interface ast va kol-e algorithm ra runtime avaz mikoni.

**5. Farq ba decorator-e idempotent?**
Decorator ghabl/ba'd ra **birun** ezafe mikonad va original ra composition mikonad. Template dakhel-e selasele-ye class ast. Ma har do ra darim, baraye do kar-e mokhtalef.

**6. `virtual` ya `abstract`?**
`abstract` vaghti ghadam ejbari ast va default-e ma'ni nadarad. `virtual` vaghti default-e ghaabel-e override dari. Inja handler **hatman** bayad `Handle(T)` dashte bashad, pas abstract.

**7. Risk-e template?**
Base shekastane (fragile base): taghir-e skeleton hame-ye subclass-ha ra mikeshad. Skeleton ra kutah negah dar.

**8. Mitavan in ra bedune inheritance nevesht?**
Bale, yek function `(event, next) => next((T)event)`. An dige template method-e klasik nist. Ma an ra ba abstract class kardim ta handler-ha signature-e yeksan dashte bashand.

**9. Job-haye outbox template hastand?**
Shekl-e kar yeki ast vali class-e `ProcessOutboxJob` har module joda neveshte shode. Pattern-e amade nist. Fursat-e refactor hast, na chizi ke alan be onvan-e skeleton-e vahed darim.

**10. Test-e subclass chetor cast ra test mikonad?**
Test-e cast mal-e base ast: `Handle((IDomainEvent)typed)` va assert ke hook-e subclass haman instance ra dide. Test-e subclass faghat ghanun-e business ra mizanad.
