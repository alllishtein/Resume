# 07 — Factory

---

## Ye khat

Client `new` ra khodesh nemizanad. Sakhtan-e object ghanun darad: kodam class, che field-hayi, che tartibi. An ghanun yek ja jam' mishavad. An ja factory ast.

---

# BAKHSH-E AVAL — khode pattern

In esm se chiz-e mokhtalef ra mipooshand. Agar an-ha ra yeki koni, mosahebe ra mibazi. Avval joda-shaan kon.

## 1. Simple Factory — esm-e rayej, pattern-e GoF nist

Yek method ya yek class, ba `if` / `switch` / map, yek interface bar migardanad va concrete ra ghof mikonad.

```csharp
INotifier Create(string channel) => channel switch
{
    "email" => new EmailNotifier(),
    "sms"   => new SmsNotifier(),
    _       => throw new ArgumentOutOfRangeException(nameof(channel))
};
```

Client `EmailNotifier` ra nemishnasad. Faghat `INotifier` ra migirad.

Mahdudiat: har concrete-e jadid, hamin `switch` ra edit mikonad. Bast-e baraye taghir (Open/Closed) kamel nist. Baraye tedad-e kam va maloom, sade-tarin chiz-e dorost ast. An ra "abstract factory" seda nakon ta bozorg-ash nakarde bashi.

## 2. Factory Method — in yeki to ketab-e GoF ast

Intent: interface-e sakhtan-e object ra tarif kon, vali bezar **subclass** tasmim begirad kodam class sakhte shavad. Class-e pedar yek algorithm darad va vasat-e an "yek object besaz" ra be method-e abstract mikahad.

```csharp
abstract class Importer
{
    public void Run(Stream input)
    {
        var parser = CreateParser();   // hook
        parser.Parse(input);
        Save();
    }

    protected abstract IParser CreateParser();
}

sealed class CsvImporter : Importer
{
    protected override IParser CreateParser() => new CsvParser();
}
```

Nokte: `Run` tartib ra darad. `CreateParser` faghat mahsul ra avaz mikonad. Pedar concrete-e parser ra nemishnasad.

Farq ba simple factory: entekhab ba **subclass** ast, na ba `switch`-e markazi. Concrete-e jadid = class-e jadid, na virayesh-e `switch`. Hazine: selasele-ye class.

Factory Method hamchenan mitavanad **static** bashad va subclass nakhahad. An ra "static factory method" seda mizanand (Joshua Bloch, na GoF). Hadaf-ash avaz kardan-e constructor ast, na pedar-farzand.

## 3. Static factory method — jaygozin-e constructor

```csharp
public static Order Place(Guid customerId, IReadOnlyList<Line> lines)
{
    if (lines.Count == 0) throw new ArgumentException("empty");
    var order = new Order(customerId, lines);
    order.Record(new OrderPlaced(order.Id));
    return order;
}
```

Chera be jaye `new Order(...)`:

- **esm** dari. `Place` va `Rehydrate` do rah-e sakht-and. Do constructor-e ham-emza esm nadarand
- **ghanun** yek ja ejra mishavad: list-e khali, event, field-haye hasel
- mitavanad **subtype** bar gardanad bedune inke caller type-e nahayi ra bedanad
- mitavanad **async** bashad. Constructor async nist
- mitavanad object-e **az ghabl sakhte** ra pas bedahad (cache). Constructor hamishe instance-e jadid ast

Constructor hanuz vojud darad, vali `private` ya `internal` ta rah-e bi-ghanun-e `new` baste bashad. Agar constructor-e public ham baz bemanad, factory dorough-e ekhtiari ast.

In pattern "object-e nimbandi birun nayad" ra gharanti mikonad. Ya `Place` yek `Order` valid bar migardanad, ya exception / result. Hichvaght `Order` bedune line-e ejbari dast-e caller nemiravad.

## 4. Abstract Factory — GoF, va aksaran ezafe ast

Intent: interface-i besaz ke **khanevade** az object-haye ham-sabk besazad, bedune nam bordan-e concrete.

```csharp
interface IWidgetFactory
{
    IButton CreateButton();
    IDialog CreateDialog();
}

sealed class MacFactory : IWidgetFactory { ... }
sealed class WinFactory : IWidgetFactory { ... }
```

Arzesh vaghti ast ke mahsul-ha bayad **ba ham jor** bashand: button-e Mac ba dialog-e Win ghalat ast. Factory-e khanevade in tarkib-e ghalat ra sakht mikonad.

Agar faghat yek mahsul dari (`INotifier`), abstract factory nemikhahi. Simple factory kafi ast. Eshtebah-e mosahebe: har `Create` ra abstract factory khandan.

## 5. DI container factory ast, vali jaye hame-ye factory-ha nist

`GetRequiredService<INotifier>()` sakhtan ra az client migirad. An factory-e general ast. Class-e factory-e dasti vaghti lazem ast ke **ghanun-e entekhab** mal-e to bashad: "in brand", "in aggregate faqat az `Place` sakhte shavad", "in type-ha ra scan kon va cache kon". Container an ghanun ra balad nist magar khodet an ra be an yad bedahi.

Agar factory-at faghat `return new EmailNotifier()` ast va hich sharti nadarad, factory-e ezafe ast. Container hamin kar ra mikonad.

## Ghanun-e moshtarak-e hame-ye anva'

- Client concrete ra `new` nemizanad
- Ghanun-e sakht (validation, event, entekhab-e class) yek ja ast
- Mahsul ba interface ya ba type-e domain-e valid barmigardad, na ba object-e nimkar
- Factory-e khoob **kari joz sakhtan** nemikonad. Agar `Create` ham save konad ham email bezanad, shode service. Esm-ash factory mimanad, naghsh-ash na

## Farq ba Builder

Builder object-e **chand-ghadami** va aksaran ekhtiari-ye ziad misazad (`builder.SetA().SetB().Build()`). Factory yek ghadam, yek mahsul-e kamel. Agar `Build` khodash ghanun-e sakht darad, daroon-ash factory-method ast. Builder baraye tartib-e por kardan ast. Factory baraye "kodam class / kodam rah-e sakht".

## Farq ba Strategy

Strategy algorithm-e jaygozin ast va client interface-e algorithm ra darad. Factory tasmim migirad **kodam concrete be vojud biyayad**. Aksaran factory yek strategy bar migardanad va ba'd client strategy ra seda mizanad. Do pattern-e posht-e sar-e ham. Yeki nistand.

## Koja bezan, koja nazan

Bezan vaghti `new` ghanun ra rad mishavad, ya esm-e rah-e sakht mohem ast, ya concrete bayad az client ghof shavad.

Nazan vaghti `new` yek DTO-e bi-ghanun ast. Factory-e an faqat parsa-bazi ast.

## Mafhoom ra injoori begou

> "Simple factory yek switch-e markazi ast va GoF nist. Factory Method-e GoF algorithm-e pedar ra sabet negah midarad va sakhtan-e mahsul ra be subclass midahad. Static factory method jaygozin-e constructor ast: esm, ghanun, async, va bastan-e `new`-e bi-ghanun. Abstract factory khanevade-ye ham-sabk misazad. Man har `Create` ra abstract factory seda nemizanam. Container ham factory ast, vali ghanun-e domain ra khodash balad nist."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

**Static factory method rooye aggregate.**
`Personnel.CreateAsync(...)` va `Personnel.CreateSuperAdminAsync(...)` to `Dejban.Modules.Personnels.Domain/Personnels/Personnel.cs`.

Do esm, do rah. Constructor-e `new Personnel { FirstName = ... }` rah-e rasmi nist, chon ACL user id, field-haye ejbari, va `Raise`-e event-e created bayad yek ja etefagh bioftand. `CreateAsync` async ast chon `IACLUserIdGenerator` async ast. Constructor in kar ra nemitavanad. In daghighan dalil-e static factory method-e bakhsh-e avval ast, na abstract factory.

**Simple factory + reflection baraye handler-e event.**
`Dejban.Common.Infrastructure/Outbox/DomainEventHandlersFactory`.

Vorudi: type-e event + assembly. Khoruji: hame-ye `IDomainEventHandler` haye an type. `switch` nist. Scan ast. Cache-e `ConcurrentDictionary` ta `GetTypes()` har payam tekrar nashavad. Kilid = esm-e assembly + esm-e type, ta do module esm-e yeksan ra ghalt share nakonand.

In factory `new Handler()` nemizanad. `GetRequiredService` mizanad. Dalil az bakhsh-e avval: container decorator ra balad ast, factory-e dasti-e `new` na. Agar inja `new` bezani, idempotency-e Scrutor mipard.

Hamin shekl: `IntegrationEventHandlersFactory`.

In abstract factory nist. Khanevade-ye ham-sabk (button+dialog) nist. Yek noe mahsul: handler-e haman event.

**Factory-e connection.**
`DbConnectionFactory` dor-e `NpgsqlDataSource`. Client `new NpgsqlConnection` nemizanad. Ghanun-e pooling yek ja ast. Simple factory / wrapper-e sakht. Pattern-e bozorg-tar az in nist.

**`IDesignTimeDbContextFactory<PersonnelsDbContext>`.**
Factory-e **abzar-e EF** ast, na factory-e runtime-e business. EF vaght-e design-time an ra mikhanad ta context besazad. An ra to runtime-e request seda nazan va an ra ba `CreateAsync`-e personnel ghalt nakon.

Abstract factory va strategy-e brand-e dastgah (ZK/Tiam/Virdi) in ketabche nist. Dovomi to ACL ast.

---

## Script-e 90 sanie

> "Se chiz ra joda midanam. Simple factory switch-e markazi ast. Factory Method-e GoF sakhtan ra be subclass mikahad ta algorithm-e pedar concrete ra neshanad. Static factory method jaygozin-e constructor ast. Abstract factory khanevade misazad va ma an ra nadarim. To Dejban `Personnel.CreateAsync` static factory ast: async, event, va do rah-e sakht ba do esm. `DomainEventHandlersFactory` simple factory-e scan-i ast, natije ra cache mikonad, va instance ra az DI migirad ta decorator-e idempotent `new` nashavad va az dast naravad. Design-time factory-e EF runtime nist."

---

## 10 soal

**1. Simple factory chera GoF nist?**
Ketab an ra be in esm nadarad. Yek method-e markazi ba shart ast. Mofid ast, vali OCP-e kamel nadarad.

**2. Factory Method-e GoF kodam bakhsh ra be subclass midahad?**
Faghat sakhtan-e mahsul. Tartib-e algorithm to pedar mimimand.

**3. Static factory che chizi az constructor bishtar darad?**
Esm, shart-e valid budan, bargardandan-e subtype, async, va emkan-e bargardandan-e instance-e ghabli.

**4. Chera constructor-e public kenar-e factory dorough ast?**
Chon rah-e dovom-e bi-ghanun baz mimanad. Factory ikhtiari mishavad.

**5. Abstract factory key vaghe'an lazem ast?**
Vaghti chand mahsul bayad az yek khanevade-ye ham-sabk bashand va tarkib-e qati mamnoo' ast.

**6. Factory va Builder?**
Builder por kardan-e chand-ghadami. Factory yek ghadam ta mahsul-e kamel, ya entekhab-e class.

**7. Factory va container?**
Container `new` va lifetime ra midahad. Factory-e dasti ghanun-e entekhab ya ghanun-e domain ra midahad. `new` khali factory-e dasti nemikhahad.

**8. `CreateAsync` che ra yek ja jam' karde?**
Rah-e sakht-e valid-e personnel: generator-e ACL, field-ha, va domain event. Do esm (`Create` va `CreateSuperAdmin`) do gharardad-e joda-and.

**9. Chera factory-e handler `new` nemizanad?**
`new` DI va decorator ra dor mizanad. `GetRequiredService` wrapper-e idempotent ra hamin type bar migardanad.

**10. Cache-e reflection baraye chi ast?**
`GetTypes` geran ast. Har message nabayad assembly ra scan konad. Kilid-e assembly+type jeloye barkhord-e esm-e yeksan-e do module ra migirad.
