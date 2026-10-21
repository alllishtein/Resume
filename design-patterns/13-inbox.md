# 13 — Inbox

*Payam-e tekrar-shode ra yek bar process kon. Do bar process kardan az gom kardan badtar ast, pas dedupe darim.*

---

## Ye khat

Inbox jadval-e "in message ra hanuz kar karde-am ya na" ast, to database-e **consumer**. Publish at-least-once ast. Inbox an ra baraye business yek bar mikonad.

## Moshkel

Outbox va Rabbit gharanti nemidahand ke consumer yek bar bebine:

- mark-e "published" fail shod → dobare publish
- consumer commit kard vali ack-e bus gom shod → dobare deliver
- do instance-e haman consumer

Bedune inbox, `UnitCreated` mitavanad do bar row-e replica besazad, ya do bar soft-delete konad.

## Do decorator, do jadval

| | Domain (haman module) | Integration (module-e digar) |
|---|---|---|
| Wrapper | `IdempotentDomainEventHandler<T>` | `IdempotentIntegrationEventHandler<T>` |
| Vasl | `services.Decorate` to `AddDomainEventHandlers` | hamin, `AddIntegrationEventHandlers` |
| Jadval | `outbox_message_consumers` | inbox consumers (schema-e haman module) |
| Kilid | `domainEvent.Id` + esm-e handler | id-e integration event + esm-e handler |

Handler-e business `if (already) return` nadarad. Scrutor an ra birun push karde. Mesal-e consumer-e vaghe'i:

`UnitCreatedIntegrationEventHandler` to Visitors, Vehicles, WeighBridge, SecurityPatrols — har kodam replica-e khod ra update mikonad va `IUnitOfWork` ra save mikonad.

## Flow

```
bus deliver (shayad dobare)
  → satr-e inbox (haman DB-e consumer)     // niyat-e "didam"
  → ProcessInboxJob
       IOptions<InboxOptions>
  → IdempotentIntegrationEventHandler
       EXISTS ?
         bale → return
         na → decorated.Handle
              INSERT consumer
              handler khodesh SaveChanges-e business mizanad
```

`InboxOptions` mesl-e outbox: interval va batch, section-e `Personnels:Inbox` va hamta-ye har module.

## Gharardad-e handler

Handler bayad **idempotent-e khodesh** ham bashad, hatman dar panjere-ye beyn-e "kar tamoom shod" va "insert-e consumer fail shod". Mesal-e khoob: `INSERT` i ke unique constraint darad, ya `UPDATE` i ke dobare-ash bi-khatar ast (set-e haman value).

Decorator dedupe-e **behtarin talash** ast, na jadoo-ye exactly-once. Jomle-ye mosahebe:

> "Effectively-once: at-least-once delivery plus idempotent handler plus a consumer table."

## Farq-e inbox va "unique index tanha"

Unique index roye data-e business (masalan `Unit.Id`) khub ast vali hame-ye event update nistand. Event-e "increment" ya "send sms" unique-e tabi'i nadarad. Jadval-e inbox **id-e message** ra yadash midarad, na faghat shekl-e data.

## Order va poison

Inbox tartib-e global-e hame-ye module-ha ra dorost nemikonad. Poison: message-i ke hamishe throw mikonad bayad az batch-e zende joda shavad (retry count, dead letter) ta baghi-e inbox va-istad.

## Script-e 60 sanie

> "Consumer-ha at-least-once migirand, pas har integration handler ba `IdempotentIntegrationEventHandler` wrap shode. Ghabl az kar, id-e message va esm-e handler ra to jadval-e inbox check mikonad. Handler-haye mesl-e `UnitCreatedIntegrationEventHandler` replica-e mahali ra update mikonand va UoW-e haman module ra save mikonand. Domain va integration do decorator-e joda darand chon do jadval va do boundary hastand. Effectively-once migooyim, na exactly-once."

---

## 10 soal

**1. Inbox va outbox farq?**
Outbox producer: "in kar ra kardam, lotfan bebus". Inbox consumer: "in message ra hanuz anjam dade-am". Har kodam database-e khod-e haman service.

**2. Chera har do lazem-and?**
Outbox gom shodan-e payam ba'd az commit-e producer ra hal mikonad. Inbox tekrar-e payam dar consumer ra. Yeki jaye digari nist.

**3. Kilid-e dedupe?**
Id-e event + esm-e **handler-e dakheli**. Do handler baraye yek event har kodam yek bar. Yek handler dobar na.

**4. `Decorate` inja che rabti darad?**
Idempotency decorator ast (ketabche-ye 06). Inbox **mahali** ast ke an decorator satr minevisad. Pattern-e enterprise inbox ast, pattern-e GoF decorator.

**5. Handler `SaveChanges` mizanad va ba'd crash ghabl az insert-e inbox?**
Retry handler ra dobare seda mizanad. Pas handler bayad dobare-kari ra tahammol konad (unique key, update-e yeksan).

**6. Mitavan inbox ra faghat ba Redis `SETNX` sakht?**
Baraye "yek bar" shabih. Problem: Redis va database-e business dobare dual write mishavand. Jadval-e inbox haman DB-e consumer in race ra kutah mikonad.

**7. Message-e ba tartib-e avaz?**
Inbox khodkar sort-e global nemikonad. Age `Updated` ghabl az `Created` beresad, handler bayad version ya "row nist, ba'd retry" dashte bashad. An ra be onvan-e ghanun-e consumer begou.

**8. `InboxOptions` chera joda az outbox ast?**
Sor'at-e consume va produce yeki nist. Yek module mitavanad batch-e vorudi-e bozorg-tar bekhad bedune inke outbox-e khod ra avaz konad.

**9. Test-e retry?**
Yek bar handle-e movaffagh, ba'd haman id: repository-e business **sefr** bar-e ezafe. Va yek test: handle throw mikonad, satr-e consumer nist, bar-e dovom handle dobare seda mishavad.

**10. Exactly-once-e vaghe'i vojud darad?**
Dar do system-e joda (bus + db) amalan na, bedune gharardad-e moshakhs. Chizi ke misazi effectively-once ast: deliver-e tekrar + effect-e yek bar.
