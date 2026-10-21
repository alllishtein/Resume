# 13 — Inbox

---

## Ye khat

Payam shayad **chand bar** beresad. Inbox yadash-e masraf-konande ast: "in payam ra hanuz anjam dade-am ya na." Asar-e business yek bar etefagh mioftad, hatta agar tahvil chand bar bashad.

Pattern-e GoF nist. Jok-e idempotent consumer / transactional inbox ast, jofte-ye outbox.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Outbox va bus gharanti-e at-least-once midahand. Haman payam mitavanad dobare beresad chon:

- tolid-konande publish kard va mark-e outbox fail shod
- masraf-konande kar ra commit kard va ack-e bus gom shod
- do instance-e haman masraf-konande haman payam ra bardashtand

Agar "Unit sakhte shod" do bar ejra shavad, do row-e replica, do email, do kam-shodan-e mojudi. Bug-e business, na bug-e shabake.

"Khod-e bus exactly-once" jomle-ye marketing ast. Bein-e do system-e joda (bus va database-e to) exactly-once-e vaghe'i bedune hamkari-e har do taraf vojud-e amali nadarad.

## Ta'rif

**Effectively-once** = tahvil-e at-least-once + asar-e yek bar.

Inbox an "asar-e yek bar" ra ba yek jadval-e **haman database-e masraf-konande** misazad:

```
BEGIN
  INSERT inbox (message_id)          -- agar tekrar, inja fail ya return
  UPDATE business ...                -- asar-e vaghe'i
COMMIT
```

Agar hamin `message_id` ghablan bashad, kol-e kar skip mishavad. Bus mitavanad dobare beferestad. Database avaz-e dovom nemibinad.

Esm-e "transactional inbox": sabt-e "didam" va asar-e business **yek** transaction-and. Vagarna dobare dual write dari: asar raft, yadash-e didan na, ya baraks.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Bus | payam ra, shayad chand bar, mifrestad |
| Inbox store | id-e dide-shode ra yadash midarad |
| Handler | asar-e business. Bayad betavanad dobare-ye bi-khatar ham bashad |
| Deduper | ghabl az handler, ya dakhel-e haman transaction, mifahmad in id taze ast ya na |

Handler-e khoob **do** defa' darad: jadval-e inbox, va khod-e asar-e idempotent (unique key, `UPDATE` i ke dobare-ash haman natije ast). Jadval tanha panjere-ye crash-e beyne "kar tamoom shod" va "insert-e inbox fail shod" ra nemibandad, magar har do yek transaction bashand.

## Do jay-e dedupe

**Dakhel-e haman transaction-e business.** Ghavi-tarin shekl. Ya har do commit, ya hich. Tekrar-e ba'di id ra mibinad va khoruj mikonad.

**Ghabl va ba'd, bedune transaction-e moshtarak.** Shekl-e rayej-e sade:

```
if (seen(id)) return;
handle();          // asar
mark(id);          // yadash
```

Agar `handle` throw konad, mark nist, retry dorost ast. Agar `handle` ok va `mark` fail, retry `handle` ra dobare mizanad. Pas handler **hatman** bayad dobare-kari ra tahammol konad. In shekl "behtarin talash" ast, na jadoo. To mosahebe an ra exactly-once seda nakon.

## Kilid-e dedupe

Kilid bayad **hoviat-e tahvil** bashad, na faghat hoviat-e row-e business.

- `messageId` khub ast
- `messageId + handlerName` vaghti **do** handler-e mostaghel haman payam ra mikhahand. Har kodam yek bar. Yek handler dobar na
- `orderId` tanha bad ast baraye "update-e dovom": payam-e dovom-e jadid haman order ra ghalt "tekrar" mibinad va drop mikonad

Unique-e business (masalan `Unit.Id` baraye event-e Created) komak mikonad, vali event-e "sms befrest" unique-e tabi'i nadarad. Inbox id-e **payam** ra yad midarad, na faghat shekl-e data.

## Ghanun-ha

**1. Inbox database-e masraf-konande ast, na database-e tolid-konande.**
Tolid-konande nemidanad to anjam dadi ya na. Outbox-e u yadash-e ferestadn ast. Inbox-e to yadash-e anjam dadan.

**2. Payam-e ghadimi-tar az dedupe-window bayad gharardad dashte bashad.**
Agar jadval-e inbox ra ba'd az 7 ruz pak koni, bus-i ke payam-e 8 ruz-e ghabl ra dobare befrestad asar-e dovom misazad. Ya retention-e inbox az retention-e retry-e bus bishtar ast, ya asar khodesh idempotent-e hameshgi ast.

**3. Tartib-e jahani ra inbox dorost nemikonad.**
`Updated` mitavanad ghabl az `Created` beresad. Handler bayad "row nist, ba'd retry" ya version ra balad bashad. Drop-e koor-koor-e payam-e "zed" bug ast.

**4. Poison joda mishavad.**
Payam-i ke hamishe throw mikonad nabayad sar-e saf-e inbox-e baqi ra ghofl konad. Tedad-e talash, ba'd kenar.

**5. Ack-e bus ba'd az commit-e inbox.**
Agar ack ghabl az commit bashad va commit fail shavad, bus fekr mikonad tamoom shode va payam gom mishavad. At-least-once az samt-e masraf-konande ya'ni: avval commit, ba'd ack. Tekrar-e ehtemali ghabool, gom shodan na.

## Farq-ha

**Outbox.** Tolid. "Befrest". Inbox. Masraf. "Anjam dadam". Pipeline-e salem har do ra darad.

**Idempotency-Key-e HTTP.** Haman fekr baraye POST-e dobare-ye client. Jadval-e "in key ra didam". Inbox haman fekr baraye payam-e bus.

**Unique constraint tanha.** Hal-e `INSERT` dobare. Hal-e hame-ye anva'-e asar na. Inbox am-tar ast.

**Exactly-once-e bus.** Be onvan-e gharardad-e tanha-ye samte bus ghabool nakon. Effectively-once ra to tarh-e khodet besaz.

## Koja bezan, koja nazan

Bezan baraye har consumer-e bus ke asar-e dovom-ash geran ast (pool, email, reserve).

Nazan baraye log-e metric ke dobare-ash bi-azar ast va hazine-ye jadval nemiarzad. Hanuz bayad **agahane** an ra bi-inbox koni, na faramoosh.

## Mafhoom ra injoori begou

> "Inbox yadash-e id-e payam to database-e consumer ast. Tahvil at-least-once mimanad. Asar yek bar mishavad agar yadash va business yek transaction bashand. Shekl-e check-ba'd-handle-ba'd-mark panjere-ye tekrar darad, pas khod-e handler ham bayad idempotent bashad. Kilid message id ast, na faghat id-e row-e business, vaghti do payam-e jadid rooye yek row mojaz ast. Ack ra ba'd az commit midaham. Exactly-once-e marketing ra gharar nemigozaram. Effectively-once migoyam."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

Do jadval-e "didam", do marz. Har do haman mafhoom-and.

**Marz-e dakhel-e module (domain).**
`IdempotentDomainEventHandler<T>` ghabl az handler-e domain `outbox_message_consumers` ra mibinad. Kilid: `domainEvent.Id` + esm-e handler-e dakheli. Shekl-e code: check, ba'd `decorated.Handle`, ba'd insert. In haman shekl-e "behtarin talash" ast, na transaction-e vahed-e hatmi-e "handle + mark". Pas handler-e business bayad dobare-ye joz'i ra tahammol konad. Decorator an ra az dast-e handler-e faramooshkar dar miavarad, vali exactly-once nemisazad.

**Marz-e beyn-e module (integration).**
`IdempotentIntegrationEventHandler<T>` va `ProcessInboxJob`. Options-e joda: `InboxOptions` (`IntervalInSeconds`, `BatchSize`) section-e mesl-e `Personnels:Inbox`. Sor'at-e khordan-e payam nabayad be batch-e outbox-e haman module ghofl bashad, pas options joda ast.

Vasl-e decorator ba Scrutor to `AddIntegrationEventHandlers`. Handler-e business `if (seen) return` nadarad. Haman dalil-e decorator: faramooshi-e yek handler hame-ye dedupe ra shekaste mikonad, pas wrap-e hamegani.

Mesal-e shenavande-ye vaghe'i: `UnitCreatedIntegrationEventHandler` to Visitors, Vehicles, WeighBridge, SecurityPatrols. Har kodam replica-e mahali-e khod ra update mikonad va `IUnitOfWork`-e **haman** module ra save mikonad. Inbox-eshan jadval-e module-e khod-eshan ast, na jadval-e Personnels. Haman ghanun-e "inbox database-e consumer ast".

Shekl-e check-then-handle-then-insert ra to domain handler didim. Integration ham wrapper-e idempotent darad. Vaghti to mosahebe miri, shekl ra az rooye hamin code begou va ede'a-ye "hamishe yek transaction-e vahed-e mark+business" nakon agar an transaction ra to haman method nadidi. Sedaghat: dedupe-e jadval hast, decorator hast, handler bayad dobare-kari ra ham tahammol konad.

`Created` va `Updated`-e bi-tartib hanuz momken ast. Inbox tartib-e jahani-e module-ha ra dorost nemikonad. Replica bayad "row nist" ra balad bashad.

---

## Script-e 90 sanie

> "Bus at-least-once mifrestad. Effectively-once ya'ni asar-e consumer yek bar. Inbox id-e payam ra to database-e khod-e consumer yadash mikonad. Ghavi-tarin shekl: yadash va business yek transaction. Shekl-e check ba'd handle ba'd mark panjere darad, pas handler khodesh ham idempotent mimanad. Kilid message id be alave-ye esm-e handler ast vaghti do shenavande-ye mojaz darim. Dejban do wrapper darad: IdempotentDomainEventHandler rooye outbox_message_consumers, va IdempotentIntegrationEventHandler rooye inbox-e module-e maghsad. Scrutor har do ra Decorate mikonad. UnitCreated to Visitors va Vehicles replica-e khod-eshan ra save mikonad, na database-e Personnels. Exactly-once nemigoyam."

---

## 10 soal

**1. Effectively-once ya'ni chi?**
Tahvil mitavanad chand bar bashad. Asar-e business yek bar mimanad.

**2. Chera exactly-once-e bus kafi nist?**
Chon asar-e to to database-e digar ast. Ack-e bus va commit-e to do manba'-and. Hamkari-e inbox lazem ast.

**3. Transactional inbox kodam do write ra yeki mikonad?**
`INSERT` id-e payam va taghir-e business. Har do commit ya hich.

**4. Shekl-e mark-e ba'd-az-handle che panjere-i darad?**
Handle ok, mark fail, retry handle ra dobare mizanad. Handler bayad an ra tahammol konad.

**5. Kilid chera faghat `orderId` nist?**
Payam-e jadid-e dovom rooye haman order ghalt drop mishavad. Kilid hoviat-e payam ast.

**6. Do handler, yek payam, chand bar?**
Do bar-e mojaz, yek bar baraye har handler. Kilid `messageId + handlerName`.

**7. Ack ra key midahi?**
Ba'd az commit-e inbox va business. Ack-e zud = gom shodan-e payam.

**8. Inbox tartib ra dorost mikonad?**
Na. `Updated` ghabl az `Created` hanuz momken ast. Handler bayad an halat ra bepazirad.

**9. To Dejban inbox-e Visitors koja neshast, na to Personnels?**
Consumer-e `UnitCreated` to Visitors `IUnitOfWork` khod ra save mikonad. Yadash-e dedupe ham mal-e schema-e consumer ast.

**10. Outbox-e producer jay-e inbox ra migirad?**
Na. Outbox migoyad ferestadam. Inbox migoyad anjam dadam. Har kodam database-e khod.
