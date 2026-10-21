# 12 — Outbox

Do manba' (database va bus) ye transaction-e moshtarak-e arzan nadarand. Pas niyat-e khabar ra hamrah-e taghir-e asli, to haman database minevisim. Ferestadan-e vaghe'i badan, az ru haman radif, anjam mishavad.

In pattern-e GoF nist. Pattern-e entegration ast.

## Moshkel

```
database.Commit(order);   // shod
bus.Publish(OrderPlaced); // inja process mimirad
```

Sefaresh hast. Kasi khabar nashod.

Baraks ham bad ast: avval publish, bad crash ghabl az commit. Anbar chizi ra reserve karde ke sefaresh-ash vojud nadarad.

Retry-e sade-ye `Publish` bad az commit ham kafi nist. Agar process beyne do khat bemirad, kasi yadash nist ke publish nashode. Retry faghat vaghti stack hanuz zende ast kar mikonad.

Transaction-e tozi'-shode (2PC) har do manba' ra ye commit mikonad. Gheymat-ash lock-e toolani va bus-hayi ast ke aslan in ra nemidahand. Baraye aksar-e system-ha avvalin entekhab nist.

## Ide

Jadval-e outbox haman database-ye aggregate ast. Dakhel-e haman transaction-i ke sefaresh insert mishavad, ye radif-e "lotfan in payam ferestade shavad" ham insert mishavad.

Ya har do ru disk hastand, ya hich. Bad ye process-e joda radif-haye ferestade-nashode ra mikhanad, ru bus publish mikonad, va radif ra mark mikonad.

Atomicity inja faghat baraye neveshtan-e niyat ast. Khode `Publish` dakhel-e transaction-e sefaresh nist.

```
1. aggregate ra to hafeze avaz kon, event ra yadash kon
2. BEGIN
     neveshtan-e aggregate
     INSERT outbox
   COMMIT
3. relay: SELECT radif-haye mark-nashode, be andaze-ye batch
4. bus.Publish
5. UPDATE outbox SET published = true
```

Agar beyne 4 va 5 bemiri, radif mark nashode. Relay dobare publish mikonad. Pas tahvil hadaghal ye bar ast. Daghighan ye bar nist.

Jomle-ye dorost: outbox dual write ra az beyn mibarad. Tahvil-e bus ra exactly-once nemikonad. Consumer bayad tekrar ra tahammol konad.

Ghanun-ha:

**Jadval-e outbox haman database-ye aggregate ast.** Jadval-e database-ye digar haman dual write ra barmigardanad.

**Payload bayad baraye ferestadan-e ba'di kafi bashad.** Relay aggregate-e zende ra dobare hesab nakonad. Aggregate shayad badan avaz shode bashad. Radif bayad type, id, va body-ye haman lahze ra dashte bashad.

**Payam-e sammi zanjire ra nayestad.** Radif-i ke publish-ash hamishe throw mikonad, agar baghi-ye batch ra ghofl konad, hame-ye outbox aghab mioftad. Retry-e mahdud va kenar gozashtan-e an radif joz'-e tarh ast.

**Tartib-e jahani jadoo nist.** Chand relay-e movazi, tartib-e do aggregate-ye bi-rabt ra gharanti nemikonand. Tartib-e ye aggregate ra mishavad ba ye saf-e tak-kari ya version hefz kard.

Do shekl-e relay:

**Polling.** Job har N sanie `SELECT ... WHERE published nashode LIMIT batch`. Sade. Latency barabar-e interval ast.

**Log-e database (CDC).** Khandan-e WAL, mesl-e Debezium. Latency kamtar, infra sangin-tar. Atomicity-e radif farq nemikonad. Faghat "ki radif ra bar midarad" farq mikonad.

Use-case nabayad bad az save, `Publish` ham bezanad. An dual write-e dasti ast va outbox ra dor mizanad.

Outbox mal-e tolid-konande ast. Inbox mal-e masraf-konande. Outbox gom shodan-e payam ra hal mikonad. Tekrar-e payam ra consumer hal mikonad.

Khabar-e haman lahze ru bus sade-tar ast va shekaste-ye dual write. Faghat vaghti gom shodan-e khabar mohem nist ghabul ast.

## Hala dar Dejban

`Entity.Raise` event ra faghat to memory mirizad. `SaveChanges` aggregate va radif-e outbox ra ye transaction mikonad. Use-case `bus.Publish` nemizanad.

Relay shekl-e polling ast, na CDC. `ProcessOutboxJob` har module. Adad-ha az `OutboxOptions`: `IntervalInSeconds` va `BatchSize`. Section mesl-e `Personnels:Outbox`. Job `IOptions<OutboxOptions>` migirad.

Schema-ye har module joda ast. Outbox-e Personnel to schema-e `personnels` ast, na ye jadval-e jahani.

Bad az khandan-e radif, `DomainEventHandlersFactory` handler-haye haman module ra peyda mikonad. Pushesh-e idempotent ghabl az handler jadval-e `outbox_message_consumers` ra mibinad. Kelid: id-e event + esm-e handler. In kam kardan-e tekrar-e dakhel-e producer ast. Tekrar-e module-ye birun kar-e inbox-e an-ha ast.

Handler-e domain mitavanad integration event besazad. Aggregate khodesh bus ra nemishnasad.

Latency-e khabar = interval-e job. Module-ye digar haman millisecond be-rooz nist.

Jomle-i ke nabayad begouyi: "ma exactly-once-e outbox darim." Jomle-i ke bayad begouyi: neveshtan-e state va niyat atomic ast. Tahvil hadaghal ye bar ast. Handler-e dakheli jadval-e consumer darad. Module-ye maghsad inbox-e khod ra darad.

## Agar beporsand, in tor begou

> Dual write yani commit-e database va publish-e bus do manba'-and va crash-e beyne-shan payam ra gom mikonad. Outbox niyat ra to haman transaction minevisad. Relay badan mifrestad. Exactly-once nist. Dejban Raise ra to memory negah midarad va SaveChanges radif-e outbox ra ham minevisad. Relay poll-e ProcessOutboxJob ast. CDC nist. Handler-haye haman module az factory miayand. Khabar-e module-ye digar integration event ast va anja inbox lazem darim.

## Dah so'al

**1. Dual write daghighan kodam crash ast?**
Commit-e manba'-e avval anjam shode, manba'-e dovom na, va process digar zende nist ta retry konad.

**2. Outbox kodam bakhsh ra atomic mikonad?**
Taghir-e aggregate va neveshtan-e niyat-e publish. Khode ersal be bus dakhel-e an transaction nist.

**3. Chera jadval bayad haman database bashad?**
Vagarna neveshtan-e outbox khodesh dual write-e dovom ast.

**4. Hadaghal-yek-bar az koja miayad?**
Publish shode, mark fail shode, relay dobare mifrestad.

**5. Polling va CDC farq?**
Har do relay-and. Polling job va SELECT. CDC log-e database. Atomicity-e radif farq nemikonad.

**6. Payam-e sammi chi mikonad?**
Agar sar-e batch bemanad, baghi-ye payam-ha aghab mioftand. Bayad az masir-e zende joda shavad.

**7. Tartib-e hame-ye payam-ha ra darim?**
Na. Faghat ba gharardad-e ezafe, tartib-e ye aggregate. Outbox-e parallel tartib-e jahani nist.

**8. To Dejban relay kodam shekl ast?**
Polling-e `ProcessOutboxJob`. Interval va batch az `OutboxOptions` har module. CDC nist.

**9. Use-case Publish ham mizanad?**
Nabayad. Save kafi ast. Publish-e ezafe dual write-e kenar-e outbox ast.

**10. Jadval-e `outbox_message_consumers` jay-e inbox-e module-ye digar ra migirad?**
Na. An baraye handler-e haman module ast. Module-ye maghsad jadval-e khod ra mikhahad.
