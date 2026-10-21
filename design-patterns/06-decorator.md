# 06 — Decorator

*Haman interface, yek wrapper, behavior-e ezafe. Class-e asli ra baz nakon.*

---

## Ye khat

Decorator dor-e yek object mianad, haman contract ra implement mikonad, va ghabl ya ba'd az original kar-e ezafe mikonad. Client fargh ra nemibinad.

## Moshkel

Har domain-event handler bayad idempotent bashad: Rabbit ya job shayad haman event ra do bar bedehad. Copy kardan-e `SELECT EXISTS` to 40 handler hatman yeki ra ja mindazad. Decorator yek bar an ra dor-e **hame** mizanad.

## Code-e vaghe'i

`Personnels/.../Outbox/IdempotentDomainEventHandler.cs`

```csharp
internal sealed class IdempotentDomainEventHandler<TDomainEvent>(
    IDomainEventHandler<TDomainEvent> decorated,
    IDbConnectionFactory dbConnectionFactory)
    : DomainEventHandler<TDomainEvent>
    where TDomainEvent : IDomainEvent
{
    public override async Task Handle(TDomainEvent domainEvent, CancellationToken cancellationToken = default)
    {
        await using DbConnection connection = await dbConnectionFactory.OpenConnectionAsync();

        var outboxMessageConsumer = new OutboxMessageConsumer(domainEvent.Id, decorated.GetType().Name);

        if (await OutboxConsumerExistsAsync(connection, outboxMessageConsumer))
            return;

        await decorated.Handle(domainEvent, cancellationToken);

        await InsertOutboxConsumerAsync(connection, outboxMessageConsumer);
    }
}
```

Jadval: `personnels.outbox_message_consumers` ba `(outbox_message_id, name)`.

`name` esm-e **handler-e dakheli** ast, na esm-e decorator. Pas do handler baraye yek event joda hesab mishavand. Yek handler dobar ejra nemishavad.

## Scrutor chetor wrap mikonad

`PersonnelsModule.AddDomainEventHandlers`:

```csharp
services.TryAddScoped(domainEventHandler);

Type closedIdempotentHandler =
    typeof(IdempotentDomainEventHandler<>).MakeGenericType(domainEvent);

services.Decorate(domainEventHandler, closedIdempotentHandler);
```

`Decorate` yani: har ki `PersonnelCreatedDomainEventHandler` ra bekhad, **decorator** ra migirad, va decorator khod-e handler ra be onvan-e `decorated` migirad.

Hamin kar baraye integration event ham hast: `IdempotentIntegrationEventHandler<>` va `Decorate` roye an.

Client (`DomainEventHandlersFactory`) `GetRequiredService(handlerType)` mizanad. DI decorator ra midahad. Factory az wrapper khabar-e joda nadarad.

## Ghadam-ha ra boland begou

1. Event-id + esm-e handler ra jost-o-ju kon.
2. Age hast, bargard. Original seda **nemishavad**.
3. Age nist, `decorated.Handle`.
4. Ba'd satr-e consumer ra insert kon.

Noghte-ye tiz: insert **ba'd** az handle ast. Age handle exception bedahad, satr neveshte nemishavad, pas retry mojaz ast. Age handle movaffagh bashad va insert fail shavad, retry momken ast handler ra **dobare** ejra konad. Idempotency-e kamel nist ta handler khodesh dobare-kari ra tahammol konad, ya insert va handle yek transaction bashand. In ra to mosahebe **khodet** begou. Kas-i ke "decorator = 100% exactly-once" begouyad ghalat ast. In **at-least-once + dedupe-e behtar** ast.

## Farq

| | Decorator | Inheritance | Chain |
|---|---|---|---|
| Composition | object-e dakheli | `base.Handle` | `next()` |
| Chand wrapper | mitavani decorator-e dovom ham bezani | selasele-ye class | list-e behavior |
| Inja | idempotency | `DomainEventHandler<T>` skeleton | MediatR behaviors |

Inheritance class ra taghir-e daste-bandi mikonad. Decorator runtime, ba DI, vasl mishavad. Handler-e business az idempotency inherit nemikonad.

## Key decorator nazar

- Yek class, yek ja, hich reuse: method-e khosoosi kafi ast.
- Decorator-i ke 5 mas'uliat darad (log + retry + auth + cache + metric) khodash god object mishavad. Har mas'uliat yek wrapper.

## Script-e 60 sanie

> "Idempotency ra ba decorator-e Scrutor mizanim, na dakhel-e handler. `IdempotentDomainEventHandler<T>` haman `DomainEventHandler<T>` ast, `decorated` ra inject mikonad, va ghabl az call to `outbox_message_consumers` negah mikonad. Kilid event id be alave-ye esm-e handler ast. Module ba `services.Decorate` an ra vasl mikonad. Insert ba'd az handle ast, pas in exactly-once-e database nist; at-least-once ba dedupe ast va handler bayad dobare-kari-e joz'i ra tahammol konad."

---

## 10 soal

**1. Decorator che OCP-i midahad?**
Behavior-e jadid (idempotency, cache, log) bedune edit-e class-e asli va bedune inke client type-e jadid beshnasad.

**2. Chera `decorated.GetType().Name` na `this.GetType()`?**
`this` decorator ast va baraye hame yek esm darad. Dedup bayad **handler-e business** ra joda konad.

**3. Do handler baraye yek event?**
Do satr, do `name`. Har kodam yek bar. Decorator-e har handler joda wrap shode.

**4. Age `Handle` throw konad?**
Insert anjam nemishavad. Job/retry mitavanad dobare beayad. In khordegi-e matloob ast.

**5. Exactly-once hast?**
Na. Messaging at-least-once ast. In jadval consumer-e movaffagh ra yadash midarad. Panjere-ye beyn-e success va insert hanuz dobare-kari-e momken ast.

**6. Scrutor inja che mikonad?**
Implementation-e DI ra avaz mikonad: type-e sabt-shode mimanad, instance-e dade-shode wrapper ast, original be constructor-e wrapper dade mishavad.

**7. Farq ba middleware?**
Middleware zanjir-e HTTP/request ast. In decorator-e yek handler-e event ast. Har do wrap hastand, sat-e mokhtalef.

**8. Mitavani decorator ra faghat baraye yek event bezani?**
Bale, ba shart-e `Decorate` entekhabi. In stack **hame** ra wrap mikonad chon faramooshi-e idempotency geran-tar az yek query-e EXISTS ast.

**9. Test?**
Connection-e fake: bar-e aval `decorated` yek bar seda. Bar-e dovom ba haman id sefr bar. Exception-e `decorated`: insert seda nashavad.

**10. Inheritance sade-tar nabod?**
Age base class idempotency dashte bashad, har handler mojbur be an base ast va test-e handler be database vasl mishavad. Composition ejaze midahad handler-e khali ra bedune SQL test koni va wrapper ra joda.
