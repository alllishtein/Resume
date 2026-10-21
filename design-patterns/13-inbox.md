# 13 — Inbox

Payam shayad chand bar beresad. Inbox yadash-e masraf-konande ast: "in payam ra hanuz anjam dade-am ya na." Asar-e business ye bar etefagh mioftad, hatta agar tahvil chand bar bashad.

In pattern-e GoF nist. Jofte-ye outbox ast.

## Moshkel

Outbox va bus gharanti-ye hadaghal-yek-bar midahand. Haman payam mitavanad dobare beresad chon:

- tolid-konande publish kard va mark-e outbox fail shod
- masraf-konande kar ra commit kard va ack-e bus gom shod
- do instance-e haman masraf-konande haman payam ra bardashtand

Agar "unit sakhte shod" do bar ejra shavad, do row-e copy, do email, do kam shodan-e mojudi. Bug-e business, na bug-e shabake.

"Khode bus exactly-once" jomle-ye tabligh ast. Beyn-e bus va database-ye to, exactly-once bedune hamkari-ye har do taraf vojud-e amali nadarad.

## Ide

Effectively-once = tahvil-e hadaghal-yek-bar + asar-e ye bar.

Inbox an "asar-e ye bar" ra ba ye jadval-e haman database-ye masraf-konande misazad:

```
BEGIN
  INSERT inbox (message_id)     -- agar tekrar, inja fail ya return
  UPDATE business               -- asar-e vaghe'i
COMMIT
```

Agar hamin `message_id` ghablan bashad, kol-e kar skip mishavad.

Esm-e transactional inbox: sabt-e "didam" va asar-e business ye transaction-and. Vagarna dobare do neveshtan-e joda dari: asar raft, yadash-e didan na, ya baraks.

Shekl-e sade-tar, bedune transaction-e moshtarak:

```
if (seen(id)) return;
handle();
mark(id);
```

Agar `handle` throw konad, mark nist, retry dorost ast. Agar `handle` ok va `mark` fail, retry `handle` ra dobare mizanad. Pas handler hatman bayad tekrar ra tahammol konad. In shekl "behtarin talash" ast, na jadoo. Exactly-once seda nakon.

Kelid-e dedupe bayad hoviat-e payam bashad, na faghat hoviat-e row-e business.

- `messageId` khub ast
- `messageId + handlerName` vaghti do handler-e mostaghel haman payam ra mikhahand. Har kodam ye bar
- `orderId` tanha bad ast baraye update-e dovom: payam-e jadid-e dovom ru haman order ghalat "tekrar" dide mishavad va drop mishavad

Unique-e business (masalan `Unit.Id` baraye event-e Created) komak mikonad, vali event-e "sms befrest" unique-e tabi'i nadarad. Inbox id-e payam ra yad midarad.

Ghanun-ha:

**Inbox database-ye masraf-konande ast, na database-ye tolid-konande.** Tolid-konande nemidanad to anjam dadi ya na.

**Agar jadval-e inbox ra bad az 7 ruz pak koni,** bus-i ke payam-e 8 ruz ghabl ra dobare befrestad asar-e dovom misazad. Ya negahdari-ye inbox az retry-e bus bishtar ast, ya asar khodesh hamishe tekrar-pazir ast.

**Inbox tartib-e jahani ra dorost nemikonad.** `Updated` mitavanad ghabl az `Created` beresad. Handler bayad "row nist, bad retry" ya version ra balad bashad.

**Ack-e bus bad az commit-e inbox.** Agar ack ghabl az commit bashad va commit fail shavad, bus fekr mikonad tamoom shode va payam gom mishavad.

## Hala dar Dejban

Do jadval-e "didam", do marz.

**Dakhel-e module.**
`IdempotentDomainEventHandler<T>` ghabl az handler jadval-e `outbox_message_consumers` ra mibinad. Kelid: `domainEvent.Id` + esm-e handler-e dakheli. Shekl: check, bad `decorated.Handle`, bad insert. In haman "behtarin talash" ast, na transaction-e vahed-e hatmi. Handler-e business bayad tekrar-e joz'i ra tahammol konad.

**Beyn-e module.**
`IdempotentIntegrationEventHandler<T>` va `ProcessInboxJob`. Options-e joda: `InboxOptions` ba `IntervalInSeconds` va `BatchSize`, section mesl-e `Personnels:Inbox`. Sor'at-e khordan-e payam nabayad be batch-e outbox-e haman module ghofl bashad.

Vasl ba Scrutor to `AddIntegrationEventHandlers`. Handler-e business `if (seen) return` nadarad. Pushesh-e hamegani, ta ye handler faramush nakonad.

Mesal: `UnitCreatedIntegrationEventHandler` to Visitors, Vehicles, WeighBridge, SecurityPatrols. Har kodam copy-e mahali-ye khod ra update mikonad va `IUnitOfWork`-e haman module ra save mikonad. Inbox-eshan jadval-e module-ye khod-eshan ast, na jadval-e Personnel.

`Created` va `Updated`-e bi-tartib hanuz momken ast. Inbox tartib-e jahani-ye module-ha ra dorost nemikonad.

## Agar beporsand, in tor begou

> Bus hadaghal ye bar mifrestad. Effectively-once yani asar-e consumer ye bar. Inbox id-e payam ra to database-ye khode consumer yadash mikonad. Shekl-e check bad handle bad mark panjere darad, pas handler khodesh ham bayad tekrar ra tahammol konad. Kelid message id be-alave-ye esm-e handler ast. Dejban do pushesh darad: yeki ru outbox_message_consumers, yeki ru inbox-e module-ye maghsad. UnitCreated to Visitors copy-e khod ra save mikonad, na database-ye Personnel. Exactly-once nemiguyam.

## Dah so'al

**1. Effectively-once yani chi?**
Tahvil mitavanad chand bar bashad. Asar-e business ye bar mimanad.

**2. Chera exactly-once-e bus kafi nist?**
Chon asar-e to to database-ye digar ast. Ack-e bus va commit-e to do manba'-and.

**3. Transactional inbox kodam do neveshtan ra yeki mikonad?**
Insert-e id-e payam va taghir-e business. Har do commit ya hich.

**4. Shekl-e mark-e bad az handle che panjere-i darad?**
Handle ok, mark fail, retry handle ra dobare mizanad.

**5. Kelid chera faghat orderId nist?**
Payam-e jadid-e dovom ru haman order ghalat drop mishavad. Kelid hoviat-e payam ast.

**6. Do handler, ye payam, chand bar?**
Do bar-e mojaz, ye bar baraye har handler. Kelid `messageId + handlerName`.

**7. Ack ra key midahi?**
Bad az commit-e inbox va business. Ack-e zud = gom shodan-e payam.

**8. Inbox tartib ra dorost mikonad?**
Na. `Updated` ghabl az `Created` hanuz momken ast.

**9. To Dejban inbox-e Visitors koja neshaste?**
Consumer-e `UnitCreated` to Visitors `IUnitOfWork` khod ra save mikonad. Yadash-e dedupe ham mal-e schema-ye consumer ast.

**10. Outbox-e producer jay-e inbox ra migirad?**
Na. Outbox miguyad ferestadam. Inbox miguyad anjam dadam. Har kodam database-ye khod.
