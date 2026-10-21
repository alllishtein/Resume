# 12 — Transactional Outbox

*Taghir-e database va "khabar dadan" ya har do commit mishavand, ya hich kodam.*

---

## Ye khat

Outbox yek jadval-e haman database-e aggregate ast. Event dakhel-e **haman transaction**-e `SaveChanges` neveshte mishavad. Yek job ba'dan satr-ha ra mikhanad va roye bus publish mikonad.

## Moshkel-e do resource

```
await unitOfWork.SaveChangesAsync();   // commit shod
await bus.Publish(integrationEvent);   // inja process mire
```

Row hast, payam nist. Masir-e baraks ham bad ast: avval publish, ba'd crash ghabl az commit → consumer chizi mibine ke database nadarad.

Do resource (Postgres va Rabbit) transaction-e moshtarak-e arzan nadarand. Outbox har do niyat ra to **yek** resource minevisad.

## Flow-e Dejban

```
1. entity.Raise(domainEvent)                 memory
2. SaveChanges
     aggregate rows
     + satr-e outbox (haman DB, haman transaction)
3. ProcessOutboxJob (Quartz)
     IOptions<OutboxOptions>.BatchSize
     IOptions<OutboxOptions>.IntervalInSeconds
     satr-haye chap-nashode ra bar midarad
4. DomainEventHandlersFactory handler-ha ra miavarad
5. IdempotentDomainEventHandler
     age (eventId, handlerName) hast → skip
     vagarna handler, ba'd insert to outbox_message_consumers
6. handler mitavanad integration event publish konad
```

Options: `Personnels:Outbox` → `IntervalInSeconds`, `BatchSize`. Har module schema-e khod ra darad, masalan `personnels.outbox_message_consumers`.

## In exactly-once nist

| Marhale | Tedad-e ejra |
|---|---|
| Neveshtan-e outbox ba aggregate | atomic ba save |
| Khandan-e job va publish | **at-least-once** |
| Handler-e domain | at-least-once, ba dedupe-e jadval-e consumer |

Publish mitavanad anjam shavad va mark-e "chap shod" fail shavad. Job dobare publish mikonad. Consumer bayad inbox dashte bashad (ketabche-ye 13). Kas-i ke begouyad "outbox = exactly-once" ghalat ast. Jomle-ye dorost:

> "Atomic write of state and intent. Delivery is at-least-once. Consumers dedupe."

## Chera event haman lahze roye bus nist

`Raise` faqat list-e memory ast. Ta save, chizi baraye dastan kardan nist. Outbox processor **ba'd** az commit khabar midahad. Delay = interval-e job. UI nabayad farz konad module-e digar haman millisecond be-rooz shode.

## Farq ba dual write-e "ba retry"

Retry-e `Publish` bad az commit, satr-e gom-shode ra bar nemigardanad age process bein-e do khat bemirad. Outbox niyat ra **ghabl** az commit sabt karde, pas crash ba'd az commit hanuz satr ra darad va job an ra bar midarad.

## Script-e 60 sanie

> "Aggregate va outbox message to yek `SaveChanges` neveshte mishavand. Job-e har module, ba `OutboxOptions` (batch va interval), satr-ha ra publish mikonad. Handler-ha az factory miayand va decorator-e idempotent an-ha ra ba jadval-e consumer dedupe mikonad. Rabbit va Postgres transaction-e vahed nadarand, pas dual write nemizanim. Tahvil at-least-once ast; exactly-once ra ba inbox-e maghsad tamam mikonim. Delay-e job yani eventual consistency beyn-e module."

---

## 10 soal

**1. Outbox che atomicity-i midahad?**
State va niyat-e publish ya har do roye disk hastand ya hich. Khod-e ersal be bus dakhel-e an transaction nist.

**2. Chera jadval haman database ast?**
Ta ba aggregate yek commit dashte bashad. Jadval-e database-e digar haman moshkel-e dual write ra bar migardanad.

**3. Job crash vasat-e batch?**
Satr-haye mark-nashode dobare khande mishavand. At-least-once. Dedupe ejbari ast.

**4. `BatchSize` va `IntervalInSeconds` koja?**
`OutboxOptions`, section-e `Personnels:Outbox` va hamta-ye har module. `IOptions<OutboxOptions>` dakhel-e `ProcessOutboxJob`.

**5. Domain event va integration event inja?**
Outbox-e domain handler-haye haman module ra run mikonad. An handler mitavanad integration event besazad. Aggregate mostaghim be bus vasl nist.

**6. Order-e message?**
Yek partition/yek aggregate ra bayad be tartib fekr kard. Batch-e movazi tartib-e global ra gharanti nemikonad. Age tartib mohem ast, concurrency-e job va key-e ordering ra begou, na "outbox tartib ra jadoo mikonad".

**7. Poison message?**
Handler hamishe throw mikonad. Bayad retry-e mahdud va dead-letter dashte bashi, vagarna job haman satr ra ta abad migirad va batch ja mimanad.

**8. Outbox va CDC (Debezium)?**
Har do niyat ra az log-e database mifrestand. Ma polling-e jadval darim, na khandan-e WAL. Sade-tar baraye in stack. Latency = interval-e poll.

**9. Mitavan job ra 10 bar parallel kard?**
Baraye module-haye joda bale, chon schema joda ast. Dakhel-e yek jadval, do worker bayad satr ra `FOR UPDATE SKIP LOCKED` begirand vagarna yek message do bar hamzaman publish mishavad. Dedupe hanuz lazem ast.

**10. Chetor mifahmi outbox gir karde?**
Satr-haye ba `processed` khali ke sen-eshan az interval bishtar ast, roshd-e jadval, va log-e job. Metric: lag = `now - oldest unprocessed`. In ra be onvan-e alamat-e operasyon begou.
