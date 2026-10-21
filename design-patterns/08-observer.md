# 08 — Observer

---

## Ye khat

Yek object vaziat-ash avaz mishavad. Kasan-i ke **ghablan** gofte-and "be man ham begoo", khabar mishavand. Object-e avval esm-e an-ha ra be soorat-e list-e sabet-e compile nemishnasad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

`Order` vaghti pardakht mishavad bayad anbar, email, va amarnama-ye forush khabar shavand. Agar `Order.Pay()` mostaghim `warehouse.Reserve()` va `mail.Send()` ra seda bezanad:

- `Order` be hame-ye an system-ha vast shode
- ezafe kardan-e "sms ham befrest" yani virayesh-e `Pay`
- test-e `Pay` bedune email va anbar nist
- `Order` nemidanad chand nafar vaghe'an mohem-and. Faghat list-e emrooz ra balad ast

Observer list ra **baz** mikonad. `Order` faghat migoyad "pardakht shod". Anbar va email khod-eshan gush midadand.

## Ta'rif-e GoF

Intent: dependency-e yek-be-chand tarif kon ta vaghti object-e avval vaziat avaz kard, hame-ye vast-shode-ha khodkar khabar va be-rooz shavand.

Esm-e digar-e ghadimi: Publish / Subscribe. (Bus-e shabake ba'dan hamin esm ra bardasht. Pa'in farq-eshan ra begir.)

## Sherkat-konande-ha

| Naghsh-e GoF | Esm-e rayej | Kar |
|---|---|---|
| Subject | Publisher | list-e observer ra darad. `Attach`, `Detach`, `Notify` |
| Observer | Subscriber | interface-e `Update` |
| ConcreteSubject | — | vaziat-e vaghe'i. Vaghti avaz shod `Notify` |
| ConcreteObserver | — | be `Update` padokh midahad |

Subject concrete-e observer ra nemishnasad. Faghat interface. Observer aksaran subject ra mishnasad ta betavanad vaziat-e jadid ra **bekeshad** (pull). Dar shekl-e push, `Update(data)` hame-ye chiz ra haml mikonad va observer subject ra kamtar mishnasad.

## Sakhtar

```
order.Pay()
  -> vaziat = Paid
  -> Notify()
       -> for each observer in list: observer.Update(order)
            warehouse.Reserve(...)
            mail.Send(...)
```

Ezafe kardan-e sms = yek class-e jadid + yek `Attach`. `Pay` avaz nemishavad. In haman Open/Closed ast.

## Ghanun-ha

**1. Subject list ra darad, observer-ha yekdigar ra na.**
Sms nabayad email ra seda bezanad. Agar seda bezanad, web-e mostaghim bargashte va observer faghat yek hop-e ezafe bude.

**2. `Notify` gharardad-e "khabar", na "dastur-e ba-javab".**
Subject montazer-e return-e business-e yek observer-e khas nemimimand. Agar bemanad, dobare be an yek nafar vast shode. (Mitavanad montazer-e tamoom shodan-e hame bemanad ta exception ra bebine. An hamchenan "be hame begoo" ast, na "javab-e anbar ra be man bargardan ta sefaresh ra betanam bebandam".)

**3. Attach va Detach motenazer-and.**
Observer-e UI ke subject-e toolani-omr ra `Attach` mikonad va `Detach` nemikonad, subject an ra zende negah midarad. Memory leak-e klassik-e hamin pattern ast. Har subscribe bayad tarighe-ye unsubscribe dashte bashad, ya lifetime-e subject anqadr kutah bashad ke leak ma'ni nadahad.

**4. Tartib-e `Notify` ra gharanti farz nakon**, magar sanad karde bashi.
List-e `foreach` tartib-e attach ra darad. Business nabayad be "avval anbar, ba'd email" az tariq-e tasadof-e list tekye konad. Agar tartib gharardad ast, an dige observer-e azad nist. Yek orchestrator-e sarih mikhahi.

**5. Exception-e yek observer gharardad mikhahad.**
Agar dovomin `Update` throw konad, sevom aslan seda nemishavad. Ya hame ra try kon va jam' kon, ya avvalin shekast kol-e `Notify` ra beborad. Har do ghabel-e defa'. Bi-gharardad bug ast.

## Push va pull

**Push.** `Update(OrderPaid data)`. Subject midanad observer che mikhahad. Agar har observer field-e motefavet bekhad, emzaye `Update` varam mikonad.

**Pull.** `Update(Subject subject)`. Observer khodesh `subject.Status` ra mikhanad. Subject nemidanad ke che fieldi mohem ast. Observer be subject vast-tar mishavad.

Domain event-e modern aksaran push-e **daded** ast: khod-e event hame-ye field-e lazem ra darad (`OrderPaid { OrderId, Total }`) va observer be aggregate-e zende vast nemishavad. In behtar az har do shekl-e ghadimi baraye system-e chand-laye ast, chon event yek value-e sabet ast, na pointer be object-e motaghayer.

## Deferred notification — joz'-e mohem ke GoF-e UI nadarad

GoF-e ketab `Notify` ra **haman lahze**-ye taghir seda mizanad. To business-e database in aksaran khatar ast:

- observer email mifrestad
- ba'd transaction rollback mishavad
- email-e dorough rafte

Pas shekl-e jadid: subject event ra **yadash midarad** va hanooz kasi ra seda nemizanad. Ba'd az commit-e movaffagh, kasi digar list ra mikhanad va observer-ha ra seda mizanad. Esm-e rayej: domain event-e deferred.

Hanooz observer ast: chand shenavande, subject an-ha ra be esm-e class-e anbar va email nemishnasad. Farq faghat **zaman-e Notify** ast. In ra ba "event-e haman lahze" ghalt yeki nakon. Mosahebe hamin ra miporsad.

## Farq ba chiz-haye nazdik

**Mediator.** Subject dar observer list-e observer-ha ra (ya yek registry) darad va "be hame" migooyad. Mediator-e GoF ghanun-e hamkari-e do-tarafe ra markazi mikonad: widget-ha hamdigar ra nemishenasand **va** vasete tasmim migirad ki ra seda bezanad, na hatman hame ra. Command bus yek handler darad. Observer chand ta.

**Pub/Sub-e bus (Rabbit).** Haman mafhoom-e "khabar bedune esm-e shenavande", vali beyne process, ba queue, retry, va at-least-once. Observer-e GoF dakhel-e yek process va aksaran haman call stack ast. Bus copy-e hafeze nist.

**Event-e zaban (C# `event`).** Abzar-e zaban baraye hamin pattern: `+=` ham Attach, `Invoke` ham Notify. Abzar pattern nist. Mishe observer dasht bedune keyword-e `event` (list-e dasti, ya scan-e handler-ha).

## Koja bezan, koja nazan

Bezan vaghti "ye chiz etefagh oftad" chand asar-e mostaghel darad va nemikhahi asar-e jadid class-e asli ra edit konad.

Nazan vaghti yek asar-e hatmi-e haman senario dari ke bayad javab-ash ra haman lahze bedani ("agar anbar kam bud, sefaresh sabt nashavad"). An call-e mostaghim ya natije-ye `Result` ast. Observer an ra penhan mikonad va khata ra be "kasi yek ja throw kard" tabdil mikonad.

## Eshtebah-haye rayej

- Notify ghabl az commit
- Observer-i ke subject ra dobare avaz mikonad va Notify-e too-daro misazad (re-entrancy)
- Tekye be tartib
- Subscribe bedune unsubscribe rooye subject-e singleton
- Goftan-e "har event observer-e bus ast" bedune tafkik-e in-process va queue

## Mafhoom ra injoori begou

> "Observer dependency-e yek-be-chand ast. Subject Notify mikonad, concrete-e shenavande ra nemishnasad. Shenavande-ha hamdigar ra seda nemizanand. Push dade mifrestad, pull subject ra mikhanad. Domain event-e khoob push-e sabet ast va Notify-ash ra ta ba'd az commit aghab mindazad, vagarna asar-e khareji ghabl az rollback anjam mishavad. Tartib-e shenavande gharanti nist magar sarih neveshte bashad. Chand shenavande farq-e in pattern ba Send-e yek-handler ast."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

Subject-e domain `Entity` ast. `Dejban.Common.Domain/Entity.cs`.

- List **private** ast. Birun `Attach`-e dasti-e event-e ja'li nemikonad
- `Raise` **protected** ast. Faghat method-e khod-e entity. In be jaye `Notify`-e haman lahze neshast, vali **seda nemizanad**. Faghat be list ezafe mikonad
- `DomainEvents` read-only ast ta birun bekhanad
- `ClearDomainEvents` public ast ta infrastructure ba'd az bardashtan-e list, an ra khali konad va dobare khabar nadeh

Pas shekl-e ma **deferred** ast, na GoF-e haman-lahze. `personnel.SoftDelete()` event ra to memory mirizad. Handler-e anbar va module-ye digar hanooz khab-and. Ta `SaveChanges` commit nashavad, kasi haq-e asar-e khareji nadarad.

Shenavande-ha `IDomainEventHandler<T>` hastand. Attach-e `+=` nist. "Man subscribe-am" ya'ni class-at in interface ra implement karde va to assembly-e haman module hast. `DomainEventHandlersFactory` an-ha ra payda mikonad. Chand handler baraye yek event ghanuni ast. Inja farq ba `ISender.Send` roshan mishavad: Send yek handler, event chand ta.

Push ast: khod-e `IDomainEvent` dade ra haml mikonad. Handler be instance-e zende-ye entity-e nime-kar vast nist.

Do sath-e khabar, do marz:

| | Domain event | Integration event |
|---|---|---|
| Mahdude | haman module | beyn-e module |
| Zaman | ba commit, to outbox | ba'd, rooye bus |
| Shenavande | `IDomainEventHandler<T>` | `IIntegrationEventHandler<T>` |

Aggregate integration event ra `Raise` nemikonad. Aggregate faghat domain event mishenasad. Yek domain-handler mitavanad ba'dan integration event besazad. In joda'i jeloye vast shodan-e entity be Rabbit ra migirad. Haman ghanun-e "subject concrete-e hame-ye shenavande-haye jahan ra nemishnasad".

`UnitCreated` ke Visitors, Vehicles, WeighBridge va SecurityPatrols mishanavand integration ast, na `Raise`-e dakhel-e entity-e Personnels.

Decorator-e idempotent dor-e handler neshast. An joz'-e observer nist. Joz'-e tahvil-e at-least-once ast. Observer-e kitab farz mikonad `Notify` yek bar-e daroni seda mishavad. Bus in farz ra nadarad.

---

## Script-e 90 sanie

> "Observer ya'ni yek subject, chand shenavande, bedune esm-e concrete-e shenavande dakhel-e subject. Notify-e ketab haman lahze ast. To business-e database an ra aghab mindazim ta commit, vagarna email-e rollback-shode miferestim. Dejban hamin kar ra mikonad: `Raise` faghat list-e private ra por mikonad va protected ast ta faghat method-e entity event besazad. Factory ba'd az outbox hame-ye `IDomainEventHandler` haye an type ra seda mizanad. Chand handler mojaz ast. In Send-e MediatR nist. Domain event az module birun nemiravad. Khabar-e beyn-e module integration event-e joda ast."

---

## 10 soal

**1. Subject che chizi ra nabayad beshnasad?**
Class-e concrete-e observer. Faghat interface, ya faghat "list-e shenavande-ye in type".

**2. Push va pull?**
Push dade ra ba khabar mifrestad. Pull faghat migooyad "avaz shodam" va observer khodesh mikhanad. Event-e sabet-e push baraye joda'i-e laye behtar ast.

**3. Chera Notify-e haman lahze ba database khatar ast?**
Asar-e observer mitavanad qabl az rollback-e transaction anjam shavad.

**4. Deferred event hanuz observer ast?**
Bale. Chand shenavande, subject an-ha ra be esm nemishnasad. Faghat zaman-e Notify avaz shode.

**5. Memory leak-e in pattern kojast?**
Attach bedune Detach rooye subject-i ke az observer bishtar zende mimanad.

**6. Tartib-e observer-ha gharanti ast?**
Na, magar sanad karde bashi. Shenavande-ha bayad mostaghel bashand.

**7. Farq ba `Send`?**
Send yek handler va yek javab-e lazem. Observer chand shenavande va subject montazer-e javab-e yek-i az an-ha nist.

**8. `Raise` to Dejban chand nafar ra haman lahze seda mizanad?**
Hich-kas ra. Faghat be list-e dakheli-e entity ezafe mikonad.

**9. Chera list private va `Raise` protected ast?**
Ta application event-e ja'li ezafe nakonad va event faghat az taghir-e ghanuni-e entity sakhte shavad.

**10. Domain event va integration event?**
Avvali shenavande-ye haman module, hamrah-e commit. Dovomi gharardad-e beyn-e module rooye bus. Entity dovomi ra nemishnasad.
