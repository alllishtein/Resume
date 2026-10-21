# 07 — Factory

Kasi ke object ra mikhahad, khodesh `new` nemizanad. Sakhtan ghanun darad: kodam class, kodam field-ha, che tartibi. An ghanun ye ja jam' mishavad. An ja factory ast.

Esm-e factory se chiz-e mokhtalef ra ghati mikonad. Agar yeki-shan koni, so'al-e mosahebe ra mibazi.

## Noe'-e avval: ye method ke entekhab mikonad

Ye method ba `if` ya `switch`, ye gharardad barmigardanad va class-e moshakhas ra ghayem mikonad.

```csharp
INotifier Create(string channel) => channel switch
{
    "email" => new EmailNotifier(),
    "sms"   => new SmsNotifier(),
    _       => throw new ArgumentOutOfRangeException(nameof(channel))
};
```

Kasi ke `Create` ra seda mizanad `EmailNotifier` ra nemishnasad. Faghat `INotifier` ra migirad.

Har class-e taze hamin `switch` ra edit mikonad. Baraye tedad-e kam va malum, sade-tarin chiz-e dorost ast. In ra Abstract Factory seda nakon.

## Noe'-e dovom: pedar tartib ra darad, bache object ra misazad

In yeki to ketab-e GoF ast va esm-ash Factory Method ast.

Pedar ye algorithm darad va vasat-ash "ye object besaz" ra be method-e abstract midahad. Bache tasmim migirad kodam class sakhte shavad.

```csharp
abstract class Importer
{
    public void Run(Stream input)
    {
        var parser = CreateParser();
        parser.Parse(input);
        Save();
    }

    protected abstract IParser CreateParser();
}
```

`Run` tartib ra darad. `CsvImporter` faghat `new CsvParser()` ra barmigardanad. Pedar esm-e `CsvParser` ra nemishnasad.

Farq ba switch-e bala: entekhab ba subclass ast, na ba ye `if` markazi. Class-e taze yani class-e jadid, na virayesh-e `switch`. Hazine-ash selsele-ye class ast.

## Noe'-e sevom: method-e sabet be-jaye constructor

```csharp
public static Order Place(Guid customerId, IReadOnlyList<Line> lines)
{
    if (lines.Count == 0) throw new ArgumentException("empty");
    var order = new Order(customerId, lines);
    order.Record(new OrderPlaced(order.Id));
    return order;
}
```

Chera be-jaye `new Order(...)`:

- esm dari. `Place` va `Rehydrate` do rah-e sakht-and. Do constructor-e ham-emza esm nadarand
- ghanun ye ja ejra mishavad: list-e khali, event, field-haye hasel
- mitavanad async bashad. Constructor async nist
- mitavanad object-e az ghabl sakhte ra pas bedahad. Constructor hamishe instance-e jadid ast

Constructor hanuz hast, vali `private` ta rah-e bi-ghanun-e `new` baste bashad. Agar constructor-e public ham baz bemanad, factory ekhtiari-e dorugh ast. Ya `Place` ye `Order` motabar midahad, ya khata. Hichvaght `Order` bedune line-e ejbari dast-e caller nemiravad.

## Abstract Factory chi ast va chera aksaran ezafe ast

Ye interface ke **chand** object-e ham-sabk misazad: button-e Mac ba dialog-e Mac, na button-e Mac ba dialog-e Windows. Arzesh-ash vaghti ast ke tarkib-e ghalat bayad sakht bashad.

Agar faghat ye mahsul dari, haman switch-e avval kafi ast. Har `Create` ra Abstract Factory seda nakon.

## DI ham object misazad

`GetRequiredService<INotifier>()` sakhtan ra az caller migirad. Class-e factory-e dasti vaghti lazem ast ke ghanun-e entekhab mal-e to bashad: "in brand", "in mowjudiat faghat az `Place` sakhte shavad". Container an ghanun ra balad nist magar khodet be an yad bedahi.

Agar factory-at faghat `return new EmailNotifier()` ast va hich sharti nadarad, factory-e ezafe ast. Container hamin kar ra mikonad.

Factory-e khub kari joz sakhtan nemikonad. Agar `Create` ham save konad ham email bezanad, shode service.

## Ba Builder ghalt nashavad

Builder object-e chand-ghadami misazad: `SetA().SetB().Build()`. Factory ye ghadam ta mahsul-e kamel, ya entekhab-e class. Agar `Build` khodesh ghanun-e sakht darad, dakhel-ash haman method-e sabet ast.

Strategy algorithm ra avaz mikonad. Factory tasmim migirad kodam class be vojud biayad. Aksaran factory ye strategy bar migardanad va bad caller an ra seda mizanad. Do pattern-e posht-e sar-e ham.

## Koja estefade nakon

`new` ye DTO-ye bi-ghanun factory nemikhahad. Factory vaghti `new` ghanun ra rad mishavad, ya esm-e rah-e sakht mohem ast.

## Hala dar Dejban

**Method-e sabet ru aggregate.**
`Personnel.CreateAsync(...)` va `Personnel.CreateSuperAdminAsync(...)` to `Dejban.Modules.Personnels.Domain/Personnels/Personnel.cs`.

Do esm, do rah. `new Personnel { FirstName = ... }` rah-e rasmi nist, chon ACL user id, field-haye ejbari, va `Raise`-e event-e created bayad ye ja etefagh bioftand. `CreateAsync` async ast chon generator-e ACL user id async ast. Constructor in kar ra nemitavanad.

**Factory-e scan baraye handler-e event.**
`Dejban.Common.Infrastructure/Outbox/DomainEventHandlersFactory`.

Vorudi: noe-e event va assembly. Khoruji: hame-ye handler-haye an noe. `switch` nist. Scan ast. Natije ra to `ConcurrentDictionary` cache mikonad ta `GetTypes()` har payam tekrar nashavad. Kelid esm-e assembly be-alave-ye esm-e type ast, ta do module esm-e yeksan ra eshtebah share nakonand.

In factory `new Handler()` nemizanad. `GetRequiredService` mizanad. Dalil: container pushesh-e idempotent ra balad ast, `new` dasti na. Agar inja `new` bezani, Scrutor mipard.

Hamin shekl: `IntegrationEventHandlersFactory`.

In Abstract Factory nist. Khanevade-ye ham-sabk nist. Ye noe mahsul: handler-e haman event.

**Factory-e connection.**
`DbConnectionFactory` dor-e `NpgsqlDataSource`. Caller `new NpgsqlConnection` nemizanad. Ghanun-e pool ye ja ast.

**`IDesignTimeDbContextFactory`.**
Factory-e abzar-e EF ast, na factory-e runtime-e business. EF vaght-e design-time an ra mikhanad. An ra to darkhast-e runtime seda nazan.

Abstract Factory va strategy-e brand-e dastgah in ketabche nist. Dovomi to ACL ast.

## Agar beporsand, in tor begou

> Se chiz ra joda midanam. Switch-e markazi. Factory Method ke pedar tartib darad va bache object misazad. Method-e sabet be-jaye constructor. Abstract Factory khanevade misazad va ma an ra nadarim. To Dejban `Personnel.CreateAsync` method-e sabet ast: async, event, va do rah ba do esm. `DomainEventHandlersFactory` scan mikonad, cache mikonad, va instance ra az DI migirad ta pushesh-e idempotent az dast naravad.

## Dah so'al

**1. Switch-e markazi chera Factory Method-e GoF nist?**
Entekhab to ye method-e markazi ast, na to subclass. Har class-e jadid haman switch ra edit mikonad.

**2. Factory Method-e GoF kodam bakhsh ra be bache midahad?**
Faghat sakhtan-e mahsul. Tartib-e algorithm to pedar mimanad.

**3. Method-e sabet che chizi az constructor bishtar darad?**
Esm, shart-e motabar budan, async, va emkan-e bargardandan-e instance-e ghabli.

**4. Chera constructor-e public kenar-e factory dorugh ast?**
Chon rah-e dovom-e bi-ghanun baz mimanad.

**5. Abstract Factory key vaghe'an lazem ast?**
Vaghti chand mahsul bayad az ye khanevade-ye ham-sabk bashand va tarkib-e ghat'i mamnoo' ast.

**6. Factory va Builder?**
Builder por kardan-e chand-ghadami. Factory ye ghadam ta mahsul-e kamel, ya entekhab-e class.

**7. `CreateAsync` che ra ye ja jam' karde?**
Rah-e sakht-e motabar-e personnel: generator-e ACL, field-ha, va domain event.

**8. Chera factory-e handler `new` nemizanad?**
`new` DI va pushesh ra dor mizanad. `GetRequiredService` pushesh-e idempotent ra hamin type bar migardanad.

**9. Cache-e reflection baraye chi ast?**
`GetTypes` geran ast. Har payam nabayad assembly ra scan konad. Kelid-e assembly va type jeloy-e barkhord-e esm-e yeksan-e do module ra migirad.

**10. `IDesignTimeDbContextFactory` ra to runtime seda mizani?**
Na. Abzar-e EF to design-time an ra mikhanad. Runtime az DI miravad.
