# 07 — Factory

*Sakhtan-e object yek ja jam mishavad, chon "new" ghanun darad.*

---

## Ye khat

Factory tasmim-e **che concrete-i sakhte shavad** ra az client mighirad. Client `new Personnel { ... }` ya `new Handler()` nemizanad.

In stack **se jore** factory darad. Abstract Factory nadarad. Strategy-e device (ACL) ra inja nayavar.

## 1. Static factory method — aggregate

`Personnel.CreateAsync(...)` va `CreateSuperAdminAsync(...)` to domain.

Path: `Dejban.Modules.Personnels.Domain/Personnels/Personnel.cs`

Client `new Personnel()` nemizanad. Factory:

- field-haye ejbari va ACL user id ra yek ja set mikonad
- domain event-e "created" ra `Raise` mikonad
- do rah-e sakht (personnel-e adi va super admin) do method-e ba esm-e ma'ni darand, na do constructor-e mobham

**Farq ba constructor:** constructor zamani ast ke sakhtan sade va sync ast. Factory method zamani ast ke esm mikhahi (`Create` vs `CreateSuperAdmin`), ya kar async dari (`IACLUserIdGenerator`), ya nemikhahi har field-e public set shavad.

## 2. Factory + reflection — handler-haye event

`Dejban.Common.Infrastructure/Outbox/DomainEventHandlersFactory.cs`

```csharp
public static IEnumerable<IDomainEventHandler> GetHandlers(
    Type type, IServiceProvider serviceProvider, Assembly assembly)
{
    Type[] domainEventHandlerTypes = HandlersDictionary.GetOrAdd(
        $"{assembly.GetName().Name}{type.Name}",
        _ => assembly.GetTypes()
            .Where(t => t.IsAssignableTo(typeof(IDomainEventHandler<>).MakeGenericType(type)))
            .ToArray());

    // GetRequiredService baraye har type
}
```

In **Simple Factory** ast, na Abstract Factory: yek method, yek khanevade-ye handler baraye yek event type.

`ConcurrentDictionary` natije-ye reflection ra cache mikonad. Reflection har message tekrar nemishavad. Kilid = esm-e assembly + esm-e type.

`GetRequiredService` mohem ast: DI decorator-e idempotent ra midahad (ketabche-ye 06). Factory khodesh `new` nemizanad, vagarna Scrutor skip mishavad.

Hamin olgu baraye integration event: `IntegrationEventHandlersFactory`.

## 3. Factory-e connection

`DbConnectionFactory` dor-e `NpgsqlDataSource`. Client `new NpgsqlConnection` nemizanad. Lifetime va pooling yek ja ast.

`IDesignTimeDbContextFactory<PersonnelsDbContext>` factory-e **abzar** ast (EF migrations design-time). An ra ba factory-e runtime ghalt nagir. Migration-e schema in repo dast-sakht-e server ast; in class baraye design-time-e EF ast.

## Abstract Factory inja nist

Abstract Factory khanevade misazad: `IUiFactory.CreateButton()` + `CreateDialog()` ke ham-sabk bashand (Win ya Mac). Ma yek handler-type ya yek aggregate misazim. Age to mosahebe esm ra bozorg kardi va "abstract factory" gofti, interview-er miporsad khanevade kojast. Javab-e rast: "simple factory va static factory method".

## DI khodesh factory ast

`IServiceProvider.GetRequiredService` factory-e general-e container ast. Class-e factory-e khodeman vaghti lazem ast ke **entekhab** (kodam type, kodam method) ghanun-e ma bashad, na faghat `new`.

## Script-e 60 sanie

> "Se factory darim. `Personnel.CreateAsync` invariant va domain event ra yek ja ejra mikonad. `DomainEventHandlersFactory` ba reflection handler-haye yek event ra peyda mikonad, type-ha ra to `ConcurrentDictionary` cache mikonad, va instance ra az DI migirad ta decorator-e idempotent az dast naravad. `DbConnectionFactory` sakhtan-e connection ra markazi mikonad. Abstract factory nadarim."

---

## 10 soal

**1. Factory method va constructor?**
Constructor vaghti sakhtan sade ast. Factory vaghti esm, shart, ya async mikhahi va nemikhahi object-e nim-sakhte birun biyayad.

**2. Chera `CreateAsync` static ast?**
Aggregate hanuz vojud nadarad. Instance method nemitavanad khodash ra besazad. Static factory avvalin instance-e **valid** ra midahad.

**3. Simple factory va abstract factory?**
Simple: yek method, yek mahsul, shart-e entekhab dakhel. Abstract: interface-i ke **chand** mahsul-e ham-khanevade misazad. Dovomi inja nist.

**4. Chera factory-e handler `new` nemizanad?**
`new` DI ra dor mizanad: scoped service, decorator-e Scrutor, va test-e double az dast miravand.

**5. Cache-e `ConcurrentDictionary` chera?**
`GetTypes()` geran ast. Har outbox message nabayad assembly ra scan konad. Kilid assembly+type ast ta do module esm-e event-e yeksan ra ghalt share nakonand.

**6. Age handler-e jadid ezafe shavad?**
Factory khodkar an ra ba scan mibinad, be shart-e inke class `IDomainEventHandler<T>` bashad va to assembly-e dade-shode bashad. Factory ra edit nemikoni. OCP.

**7. Factory va Strategy?**
Strategy algorithm-e jaygozin ast va client interface ra mibinad. Factory tasmim migirad **kodam** concrete sakhte shavad. Aksaran factory, strategy ra bar migardanad. Strategy-e device in repo faghat ACL ast va in series nist.

**8. `IDesignTimeDbContextFactory` ra to runtime seda mizani?**
Na. EF tools vaght-e design-time an ra mikhanad. Runtime az DI va `AddDbContext` miravad.

**9. Factory-e khoda-sakht ke faghat `new X()` ast?**
Ezafe ast. Factory vaghti shart, cache, ya joda kardan az `new` arzeshesh ra midehad.

**10. Test?**
`CreateAsync` ra ba generator-e fake seda bezan va assert kon event-e created to `DomainEvents` hast va field-e namotabar aslan object nemisazad. Factory-e handler ra ba assembly-e test va `ServiceCollection` assert kon ke type-e decorator bar migardad.
