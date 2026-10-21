# 08 — Observer

Ye object vaz'-ash avaz mishavad. Kasan-i ke ghablan gofte-and "be man ham begou", khabar mishavand. Object-e avval esm-e class-e an-ha ra dakhel-e khodesh nadarad.

## Moshkel

Vaghti sefaresh pardakht mishavad, anbar va email va amar bayad bakhabar shavand. Agar `Pay()` mostaghim har se ra seda bezanad:

- sefaresh be hame-ye an system-ha chasbide
- ezafe kardan-e payamak yani virayesh-e `Pay`
- test-e pardakht bedune email va anbar nist

## Ide

Sefaresh faghat miguyad "pardakht shod". Anbar va email khodeshan gush dade budand.

Be objecti ke khabar midahad Subject miguyand. Be gush-dahande Observer. Subject list-e gush-dahande-ha ra darad. Gush-dahande-ha ham ra seda nemizanand.

```
order.Pay()
  → vaziat = pardakht-shode
  → be har gush-dahande: khabar bedeh
       anbar reserve mikonad
       email miravad
```

Payamak-e taze yani ye class-e taze va ye sabt-nam. `Pay` avaz nemishavad.

Ghanun-ha:

**Subject list ra darad, gush-dahande-ha yekdigar ra na.** Payamak nabayad email ra seda bezanad. Agar seda bezanad, tar-e ankabut bargashte.

**Khabar, dastur-e ba-javab nist.** Subject montazer-e return-e business-e ye gush-dahande-ye khas nemimanad. Agar bemanad, dobare be an yek nafar chasbide.

**Sabt-nam va laghv bayad juft bashand.** Gush-dahande-i ke subscribe mikonad va unsubscribe nemikonad, subject an ra zende negah midarad. Memory leak-e ma'ruf-e hamin pattern ast.

**Tartib-e khabar ra gharanti farz nakon**, magar neveshte bashi. Gush-dahande-ha bayad mostaghel bashand. Agar tartib gharardad ast, digar observer-e azad nisti. Ye hamahang-konande-ye roshan mikhahi.

**Exception-e ye gush-dahande gharardad mikhahad.** Agar dovomin throw konad, sevom aslan seda nemishavad. Ya hame ra try kon, ya avvalin shekast kol ra beborad. Bi-gharardad bug ast.

Do jur khabar:

**Push.** Khod-e khabar dade ra haml mikonad: `OrderPaid { OrderId, Total }`. Gush-dahande be object-e zende vasl nist.

**Pull.** Faghat miguyad "avaz shodam" va gush-dahande khodesh vaziat ra mikhanad. Subject nemidanad che fieldi mohem ast, vali gush-dahande be subject vast-tar mishavad.

Event-e domain-e emruz aksaran push-e sabet ast. Event ye value ast, na pointer be object-e motaghayer.

## Khabar-e haman lahze va khabar-e ba'd az commit

Ketab aksaran haman lahze-ye taghir hame ra seda mizanad. To business-e database in khatar ast: email miravad, bad transaction rollback mishavad, email-e dorugh rafte.

Shekl-e dorost: object event ra yadash midarad va hanuz kasi ra seda nemizanad. Bad az commit-e movaffagh, kasi digar list ra mikhanad va gush-dahande-ha ra seda mizanad. Hanuz observer ast. Faghat zaman-e khabar aghab oftade.

## Ba chi ghalt mishavad

**Send-e MediatR** ye handler va ye javab darad. Observer chand shenavande darad.

**Saf-e Rabbit** haman "khabar bedune esm-e shenavande" ast, vali beyn-e process, ba retry va tekrar. Observer-e ketab dakhel-e ye process va haman call stack ast.

**`event` to C#** abzar-e zaban baraye hamin pattern ast. Abzar pattern nist. Mishavad observer dasht bedune keyword-e `event`.

Observer ra vaghti nazan ke ye asar hatmi dari va javab-ash ra haman lahze mikhahi: "agar anbar kam bud, sefaresh sabt nashavad". An seda-ye mostaghim ya `Result` ast. Observer an ra penhan mikonad.

## Hala dar Dejban

Subject-e domain `Entity` ast. `Dejban.Common.Domain/Entity.cs`.

- List private ast. Birun event-e ja'li ezafe nemikonad
- `Raise` protected ast. Faghat method-e khode mowjudiat. Kasi ra seda nemizanad. Faghat be list ezafe mikonad
- `DomainEvents` read-only ast
- `ClearDomainEvents` public ast ta infrastructure bad az bardashtan-e list, an ra khali konad va dobare khabar nadahad

Pas khabar-e ma ba'd az commit ast, na haman lahze. `SoftDelete` event ra to memory mirizad. Ta `SaveChanges` commit nashavad, kasi haq-e asar-e khareji nadarad.

Shenavande-ha `IDomainEventHandler<T>` hastand. `+=` nist. "Man subscribe-am" yani class-at in interface ra piyade karde va to assembly-e haman module hast. `DomainEventHandlersFactory` an-ha ra peyda mikonad. Chand handler baraye ye event ghanuni ast. Farq ba `Send`: Send ye handler, event chand ta.

Push ast: khode event dade ra haml mikonad.

Do sath-e khabar:

| | Domain event | Integration event |
|---|---|---|
| Mahdude | haman module | beyn-e module |
| Zaman | ba commit, to outbox | bad, ru bus |
| Shenavande | `IDomainEventHandler<T>` | `IIntegrationEventHandler<T>` |

Aggregate integration event ra `Raise` nemikonad. Ye domain-handler mitavanad badan integration event besazad. `UnitCreated` ke Visitors va Vehicles mishnavand integration ast, na `Raise`-e dakhel-e entity.

Pushesh-e idempotent dor-e handler neshaste. An joz'-e observer nist. Joz'-e tahvil-e hadaghal-yek-bar ast. Ketab farz mikonad khabar ye bar-e dakheli seda mishavad. Bus in farz ra nadarad.

## Agar beporsand, in tor begou

> Observer yani ye subject, chand shenavande, bedune esm-e class-e shenavande dakhel-e subject. Khabar-e ketab haman lahze ast. To database an ra ta bad az commit aghab mindazim, vagarna email-e rollback-shode miferestim. Dejban hamin kar ra mikonad: `Raise` faghat list-e private ra por mikonad. Factory bad az outbox hame-ye handler-haye an type ra seda mizanad. Chand handler mojaz ast. In Send nist. Domain event az module birun nemiravad. Khabar-e beyn-e module integration event-e joda ast.

## Dah so'al

**1. Subject che chizi ra nabayad beshnasad?**
Class-e moshakhas-e gush-dahande. Faghat list ya interface.

**2. Push va pull?**
Push dade ra ba khabar mifrestad. Pull faghat miguyad avaz shodam va gush-dahande khodesh mikhanad.

**3. Chera khabar-e haman lahze ba database khatar ast?**
Asar-e gush-dahande mitavanad ghabl az rollback anjam shavad.

**4. Khabar-e ba'd az commit hanuz observer ast?**
Bale. Chand shenavande, subject an-ha ra be esm nemishnasad. Faghat zaman-e khabar avaz shode.

**5. Memory leak-e in pattern kojast?**
Subscribe bedune unsubscribe ru subject-i ke az gush-dahande bishtar zende mimanad.

**6. Tartib-e gush-dahande-ha gharanti ast?**
Na, magar neveshte bashi. Bayad mostaghel bashand.

**7. Farq ba Send?**
Send ye handler va ye javab-e lazem. Observer chand shenavande va subject montazer-e javab-e yeki az an-ha nist.

**8. `Raise` to Dejban chand nafar ra haman lahze seda mizanad?**
Hich-kas ra. Faghat be list-e dakheli ezafe mikonad.

**9. Chera list private va `Raise` protected ast?**
Ta application event-e ja'li ezafe nakonad va event faghat az taghir-e ghanuni-ye mowjudiat sakhte shavad.

**10. Domain event va integration event?**
Avvali shenavande-ye haman module, hamrah-e commit. Dovomi gharardad-e beyn-e module ru bus. Entity dovomi ra nemishnasad.
