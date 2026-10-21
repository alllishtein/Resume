# 04 — CQRS

Kari ke system ra avaz mikonad va kari ke faghat chizi ra mikhanad ye shekl nistan. Joda-shan mikoni ta har kodam shekl-e khodesh ra dashte bashad.

## Moshkel

Ye class-e `Order` nemitavanad hamzaman hame-ye in-ha bashad:

- ghanun-e "ta pardakht nashode khat ezafe kon"
- form-e sabt
- jadval-e bist filter ba jam'-e forush-e mah
- esm-e moshtari, ke aslan field-e khode sefaresh nist

Neveshtan object-e koochak va motabar mikhahad. Khandan object-e takht va sari' va por az field-e namayeshi mikhahad. Ye class har do ra bad anjam midahad.

## Ide

Aval ye ghanun-e sade-tar hast be esm-e CQS: methodi ke mikhanad, system ra avaz nakonad. Methodi ke avaz mikonad, baraye so'al-e ba'di dade-ye gonde bargardanad.

CQRS hamin harf ra az method bala mibarad ta model. Model-e neveshtan joda az model-e khandan. Shayad handler joda, DTO joda, hatta database joda.

Se sath darad. Sath-e balatar yani behtar nist. Yani geran-tar.

**Sath-e 1.** Do class va do handler. `CreateOrder` va `GetOrderList`. Har do haman jadval ra mibinand. Neveshtan ba mowjudiat ast. Khandan ba ye DTO-ye takht. Database yeki ast. Hamin ke commit shod, khandan-e ba'di haman dade ra mibinad.

**Sath-e 2.** Hanuz ye database, vali shekl-e khandan jodast. Masalan ye view ya ye select ba join. Mowjudiat-e neveshtan an join ra nadarad.

**Sath-e 3.** Database-ye neveshtan joda, ye copy baraye khandan. Jadval az copy mikhanad. Inja takhir hast: bad az sabt, ta copy beresad, list momken ast kohne bashad.

Hich-kodam "CQRS-e kamel-tar" be ma'ni-ye behtar nist. Sath-e 3 ra vaghti barmidari ke sath-e 1 kam biavarad: gozaresh-e sangin, ya khandan kheyli sholugh-tar az neveshtan.

Chand chiz in pattern nist.

**Event sourcing nist.** Event sourcing yani tarikh-e event-ha ra zakhire koni, na vaziat-e alan. Kheyli-ha in do ra ba ham miguyand. Ma event-e domain darim. Tarikh-e kamel-e event be-jaye radif-e jadval nadarim. Agar beporsand "CQRS dari?" va to event sourcing nadari, begou nadari.

**Do class-e khali ham kafi nist.** Agar command faghat field-ha ra copy konad va query haman mowjudiat ra bargardanad, esm-e CQRS ra dari va joda'i-ye model ra na.

**Do microservice-e ejbari nist.** Joda'i-ye code dakhel-e ye process ham CQRS ast.

Ghanun-ha:

Khandan vaziat-e business ra avaz nemikonad. "In bazdid ra beshmar" farman ast, na kar-e makhfi dakhel-e `GetById`. Log-e zir-sakht eshkali nadarad.

Farman mitavanad shenase bargardanad. Nabayad kol-e shekl-e safhe ra bargardanad. Vagarna model-e neveshtan dobare shekl-e UI mishavad.

Field-e jadid yani do ja taghir: farman va model-e khandan. In hazine-ye sabet-e pattern ast. Agar nagu'i, pattern ra balad nisti.

To sath-e 3, safhe bayad takhir-e copy ra tahammol konad. Ya az javab-e khode farman UI ra taze kon, ya sath-e 3 ra baraye an safhe entekhab nakon.

## Mesal-e koochik

```csharp
public readonly record struct PlaceOrder(Guid CustomerId, IReadOnlyList<Line> Lines);

public readonly record struct OrderListItem(Guid Id, string CustomerName, decimal Total, string Status);
```

Handler-e avval `Order.Place` ra seda mizanad va commit mikonad. Handler-e dovom ye select mizanad va `OrderListItem` por mikonad. Class-e `Order` field-e `CustomerName` nadarad. Esm-e moshtari mal-e jadval-e digari ast va faghat to khandan join mishavad.

## Koja estefade nakon

Agar form va jadval haman shekl-and, do poshte hazine-ye khali ast. Sath-e 3 ra baraye har mowjudiat nasaz. Takhir-e copy bug-hayi misazad ke sath-e 1 aslan nadasht.

## Hala dar Dejban

Sath-e ghaleb-e module-ha sath-e 1 ast.

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

Do gharardad. Har do az MediatR miravand va har do `ErrorOr` barmigardanand. Joda'i in ast ke:

- validation-e pipeline faghat ru command ast, chon `IBaseCommand` darad. Query in gheyd ra nadarad.
- handler-e command mowjudiat ra bar mikonad, method-e mowjudiat, `SaveChanges`.
- handler-e query ye DTO-ye takht barmigardanad, na mowjudiat-e ghabel-e neveshtan.

Database-ye khandan va neveshtan baraye bishtar-e module-ha yeki ast. In ra "CQRS ba do database" seda nakon.

Sath-e 3 jayi ast ke gozaresh-giri model-e khandan-e joda darad. Dade-ye neveshte-shode ye bar-e digar be shekl-e gozaresh zakhire mishavad. An yeki ba takhir taze mishavad. Joz'iat-ash to `day-64` ast.

Mapster abzar-e copy-e field ast, khode in pattern nist. Agar naghshe-ye yek-be-yek va bi-taghir bashad, joda'i-ye model hanuz ru kaghaz ast.

## Agar beporsand, in tor begou

> CQS miguyad method-e khandan avaz nakonad. CQRS miguyad model-e khandan va neveshtan yeki nabashand. Se sath darad: do handler, do shekl dakhel-e ye database, ya do zakhire ba takhir. Event sourcing nist. Dejban sath-e avval ra hame-ja darad: command mowjudiat ra minevisad, query ye DTO-ye takht. Validation faghat ru command ast. Gozaresh-giri jayi ast ke model-e khandan-e joda darim.

## Dah so'al

**1. Farq-e CQS va CQRS chi ast?**
CQS joda'i-ye method ast. CQRS joda'i-ye model ast, va shayad joda'i-ye zakhire. Dovomi avvali ra farz mikonad.

**2. Chera ye class-e Order ham baraye ghanun ham baraye jadval bad ast?**
Shekl-e ghanun va shekl-e namayesh yeki nist.

**3. Sath-e 1 va sath-e 3 az nazar-e tazegi-ye dade che farqi darand?**
Sath-e 1 ba commit, khandan-e ba'di dorost ast. Sath-e 3 ta copy beresad momken ast aghab bashad.

**4. Event sourcing kojay-e in ta'rif ast?**
Hich-ja. Manba'-e haghighat mitavanad haman radif-e alan bashad.

**5. Query mojaz ast che bargardanad?**
DTO va list va "peyda nashod". Nabayad radif ra update konad.

**6. Command mojaz ast shenase bargardanad?**
Bale. Vaghti kol-e graph-e safhe ra barmigardani, joda'i mishkanad.

**7. Hazine-ye sabet chi ast?**
Har field-e jadid do ja ra avaz mikonad. To sath-e 3 bayad takhir ra ham tarahi koni.

**8. Sath-e ghaleb-e Dejban kodam ast?**
Sath-e 1. Do interface, ye database-ye module. Validation faghat command ast.

**9. Sath-e 3 koja dide mishavad?**
Model-e khandan-e gozaresh-giri. Mowjudiat nist. Bad az neveshtan, dirtar az commit-e asli taze mishavad.

**10. Che chizi ra to review rad mikoni?**
Query ke `SaveChanges` bezanad, ya command ke baraye ye jadval mowjudiat ra ba hame-ye rabete-ha bar konad.
