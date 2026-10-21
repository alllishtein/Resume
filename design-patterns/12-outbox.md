# 12 — Transactional Outbox

---

## Ye khat

Do manba' (database va bus) yek transaction-e moshtarak-e arzan nadarand. Pas **niyat-e khabar** ra hamrah-e taghir-e asli, to **haman** database minevisim. Ferestadn-e vaghe'i ba'dan, az rooye haman satr, anjam mishavad.

Pattern-e GoF nist. Pattern-e enterprise integration ast (Hohpe, "Transactional Outbox").

---

# BAKHSH-E AVAL — khode pattern

## Moshkel-e dual write

```
database.Commit(order);   // shod
bus.Publish(OrderPlaced); // inja process mimirad
```

Sefaresh hast. Kasi khabar nashod. Anbar reserve nemikonad.

Baraks:

```
bus.Publish(OrderPlaced); // anbar reserve kard
database.Commit(order);   // fail
```

Anbar chizi ra reserve karde ke sefaresh-ash vojud nadarad.

Retry-e sade-ye `Publish` bad az commit ham kafi nist. Agar process **beyne** do khat bemirad, retry-i vojud nadarad chon hich-kas yadash nist ke publish nashode. Retry faghat vaghti stack hanuz zende ast kar mikonad.

Distributed transaction (2PC) har do manba' ra yek commit mikonad. Gheymat: lock-e toolani, coordinator, shekast-e shabake, va bus-hayi ke aslan 2PC nemidahand. Baraye aksar-e system-haye emruz avvalin entekhab nist.

## Ta'rif

Jadval-e outbox **haman database**-e aggregate ast. Dakhel-e haman transaction-i ke sefaresh INSERT mishavad, yek satr-e "lotfan in payam ferestade shavad" ham INSERT mishavad.

Ya har do roye disk hastand, ya hich. Ba'd yek process-e joda satr-haye ferestade-nashode ra mikhanad, rooye bus publish mikonad, va satr ra mark mikonad.

Atomicity inja faghat baraye **neveshtan-e niyat** ast. Khod-e `Publish` dakhel-e transaction-e sefaresh nist.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Use-case | aggregate ra avaz mikonad. Bus ra mostaghim seda nemizanad |
| Database | aggregate + satr-e outbox, yek commit |
| Relay / dispatcher | satr-haye baqi-mande ra mikhanad va publish mikonad |
| Bus | payam ra be consumer mibarad |
| Consumer | bayad tekrar ra tahammol konad (inbox) |

Use-case **nabayad** ba'd az save, `Publish` ham bezanad. An dual write-e dasti ast va outbox ra dor mizanad.

## Sakhtar-e zaman

```
1. aggregate ra to hafeze avaz kon, event ra yadash kon
2. BEGIN
     INSERT/UPDATE aggregate
     INSERT outbox (event id, type, payload, created_at)
   COMMIT
3. relay: SELECT satr-haye mark-nashode LIMIT batch
4. bus.Publish(payload)
5. UPDATE outbox SET published = true
```

Agar beyn-e 4 va 5 bemiri, satr mark nashode. Relay dobare publish mikonad. Pas tahvil **at-least-once** ast. Exactly-once nist.

Jomle-ye dorost-e mosahebe:

> "Outbox dual write ra az beyn mibarad. Tahvil-e bus ra exactly-once nemikonad. Consumer bayad tekrar ra tahammol konad."

## Ghanun-ha

**1. Jadval-e outbox haman database-e aggregate ast.**
Jadval-e database-e digar haman dual write ra barmigardanad. "Outbox-e markazi-e yek server-e digar" pattern ra shekaste mikonad.

**2. Payload bayad baraye ferestadn-e ba'di kafi bashad.**
Relay aggregate-e zende ra "dobare hesab" nakonad. Aggregate shayad ba'dan avaz shode bashad. Satr-e outbox bayad type, id, va body-e haman lahze ra dashte bashad.

**3. Relay mitavanad tekrari befrestad. Gharardad hamin ast.**
Mark-e ba'd-az-publish panjere-ye tekrar darad. Tarahi-e consumer bedune in panjere na-tamam ast.

**4. Poison message zanjir ra mistanad.**
Satr-i ke publish-ash hamishe throw mikonad, agar baqi-e batch ra ghofl konad, hame-ye outbox aghab mioftad. Retry-e mahdud va kenar gozashtan-e satr-e sammi (dead letter) joz'-e tarh ast, na ezafe-ye ba'di.

**5. Tartib-e jahani jadoo nist.**
Chand relay-e movazi, tartib-e do aggregate-e bi-rabt ra gharanti nemikonand. Tartib-e **yek aggregate** ra mitavan ba yek saf-e tak-kari ya barchasb-e version hefz kard. Agar beporand "outbox FIFO-e jahani midahad?" javab na.

## Do shekl-e relay

**Polling.** Job har N sanie `SELECT ... WHERE published_at IS NULL LIMIT batch`. Sade. Latency = interval. Bar-e database = tedad-e poll. In shekl-e rayej-e app-e ma'mooli ast.

**Log-based (CDC).** Khandan-e WAL-e database (Debezium va shabihesh). Latency kamtar, app poll nemikonad. Hazine: infra-e sangin-tar. Pattern-e outbox har do relay ra ghabool darad. Atomicity-e satr ba aggregate farq nemikonad. Faghat "ki satr ra bar midarad" farq mikonad.

## Farq-ha

**Dual write + retry.** Retry crash-e beyne do khat ra nemipooshand. Outbox niyat ra ghabl az commit sabt karde, pas crash-e ba'd az commit hanuz satr darad.

**UoW.** UoW yek database ra atomik mikonad. Outbox **niyat-e ferestadn** ra vared-e haman UoW mikonad. UoW-e tanha bus ra commit nemikonad.

**Inbox.** Outbox mal-e **tolid-konande** ast. Inbox mal-e **masraf-konande**. Outbox gom-shodan-e payam ra hal mikonad. Tekrar-e payam ra consumer hal mikonad. Yeki jaye digari nist.

**Event-e haman lahze rooye bus.** Sade-tar, va shekaste-ye dual write. Faghat vaghti gom shodan-e khabar aslan mohem nist (metric-e bi-arzesh) ghabool ast.

## Koja bezan, koja nazan

Bezan vaghti ba'd az taghir-e database, system-e digar **hatman** bayad khabar shavad va gom shodan-e an khabar bug-e business ast.

Nazan vaghti khabar haman process va haman transaction ast. Outbox delay va tekrar midahad. Call-e dakheli arzan-tar va sade-tar ast.

## Eshtebah-haye rayej

- "Outbox = exactly-once"
- Publish-e mostaghim kenar-e outbox "baraye sor'at"
- Payload-e khali va load-e dobare-ye aggregate to relay
- Yek worker-e parallel bedune ghofl-e satr (`SKIP LOCKED` ya shabihesh) va do publish-e hamzaman
- Bi-tavajoh be lag: sen-e ghadimi-tarin satr-e mark-nashode

## Mafhoom ra injoori begou

> "Dual write crash-e beyne database va bus ra gom mikonad. Outbox niyat-e publish ra to haman transaction-e aggregate minevisad. Relay ba'dan an satr ra mifrestad. Polling ya CDC faghat shekl-e relay ast. Tahvil at-least-once ast. Exactly-once ra aggregate-e producer jadoo nemikonad. Consumer dedupe mikhahad. Tartib-e jahani nadarim. Poison message bayad az batch-e zende joda shavad."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

`Entity.Raise` event ra faghat to memory mirizad. `SaveChanges` aggregate va satr-e outbox ra yek transaction mikonad. Use-case `bus.Publish` nemizanad. Haman ghanun-e "dual write-e dasti mamnoo'".

Relay shekl-e **polling** ast, na CDC. `ProcessOutboxJob` har module. Adad-ha az `OutboxOptions`: `IntervalInSeconds` (har chand sanie poll) va `BatchSize` (chand satr dar har bar). Section-e config mesl-e `Personnels:Outbox`. Job `IOptions<OutboxOptions>` migirad.

Schema-ye har module joda ast. Outbox-e Personnels to schema-e `personnels` ast, na yek jadval-e global-e hame-ye Dejban. Haman "outbox haman database-e aggregate".

Ba'd az khandan-e satr, `DomainEventHandlersFactory` handler-haye **haman module** ra peyda mikonad. Decorator-e idempotent ghabl az handler jadval-e `outbox_message_consumers` ra mibinad. Kilid: id-e event + esm-e handler. In dedupe-e **dakhel-e** producer ast, baraye handler-hayi ke relay shayad dobare seda bezanad. Dedupe-e module-e birun kar-e inbox-e an-ha ast.

Handler-e domain mitavanad integration event besazad. An payam-e beyn-e module ast. Aggregate khodesh bus ra nemishnasad. Do ghadam: domain event (haman module, az outbox) va integration event (bus, be samte inbox-e digar).

Latency-e khabar = interval-e job. Module-e digar haman millisecond be-rooz nist. Eventual consistency. UI nabayad farz-e baraks konad.

Jomle-i ke nabayad begoyi: "ma exactly-once-e outbox darim." Jomle-i ke bayad begoyi: "neveshtan-e state va niyat atomic ast. Tahvil at-least-once ast. Handler-e dakheli consumer-table darad. Module-e maghsad inbox-e khod ra darad."

---

## Script-e 90 sanie

> "Dual write ya'ni commit-e database va publish-e bus do manba'-and va crash-e beyne-shan payam ra gom mikonad. Outbox niyat ra to haman transaction minevisad. Relay ba'dan mifrestad. Exactly-once nist, at-least-once ast. Dejban Raise ra to memory negah midarad va SaveChanges satr-e outbox ra ham minevisad. Relay poll-e ProcessOutboxJob ast, ba BatchSize va Interval az OutboxOptions-e har module. CDC nist. Handler-haye haman module az factory miayand va decorator-e consumer-table tekrar-e dakheli ra kam mikonad. Khabar-e module-e digar integration event ast va anja inbox lazem darim. Lag-e job yani eventual, na haman-lahze."

---

## 10 soal

**1. Dual write daghighan kodam crash ast?**
Commit-e manba'-e avval anjam shode, manba'-e dovom na, va process digar zende nist ta retry konad.

**2. Outbox kodam bakhsh ra atomic mikonad?**
Taghir-e aggregate va **neveshtan-e niyat-e** publish. Khod-e ersal be bus dakhel-e an transaction nist.

**3. Chera jadval bayad haman database bashad?**
Vagarna neveshtan-e outbox khodesh dual write-e dovom ast.

**4. At-least-once az koja miayad?**
Publish shode, mark fail shode, relay dobare mifrestad. Ya consumer ack ra gom karde.

**5. Polling va CDC farq?**
Har do relay-and. Polling job va `SELECT`. CDC log-e database. Atomicity-e satr farq nemikonad. Latency va infra farq mikonad.

**6. Poison message chi mikonad?**
Agar to sar-e batch bemanad, baghi-e payam-ha aghab mioftand. Bayad az masir-e zende joda shavad.

**7. Tartib-e hame-ye payam-ha ra darim?**
Na. Faghat ba gharardad-e ezafe, tartib-e yek aggregate ya yek partition. Outbox-e parallel FIFO-e jahani nist.

**8. To Dejban relay kodam shekl ast?**
Polling-e `ProcessOutboxJob`. Interval va batch az `OutboxOptions` har module. CDC nist.

**9. Use-case `Publish` ham mizanad?**
Nabayad. Save kafi ast. Publish-e ezafe dual write-e kenar-e outbox ast.

**10. Dedupe-ye `outbox_message_consumers` jay-e inbox-e module-e digar ra migirad?**
Na. An baraye handler-e **haman** module ast. Module-e maghsad jadval-e khod ra mikhahad.
