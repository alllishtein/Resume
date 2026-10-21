# 04 — CQRS

---

## Ye khat

Kari ke **system ra avaz mikonad** va kari ke **faghat chizi ra mikhanad** yek model nistand. Joda-shaan mikoni ta har kodam shekl-e khod ra dashte bashad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Yek model-e `Order` hame-chiz ra mikhahad bashad:

- ghanun-e "mitavan khat ezafe kard ta vaghti pardakht nashode"
- form-e sabt
- grid-e 20 filter ba jam'e forush-e mah
- namayesh-e esm-e moshtari ke aslan field-e aggregate nist

Write mikhahad object-e koochak, invariant, va kam field. Read mikhahad flat, sari', va por az field-haye namayeshi. Yek class har do ra bad anjam midahad: ya ghanun-e write shekaste mishavad ta grid rahat shavad, ya grid `Include`-e sangin mikeshad ta aggregate "kam" bemanad.

## Ta'rif

**CQS** (Command Query Separation, Bertrand Meyer) ghanun-e **method** ast:

- command system ra avaz mikonad va chizi bar nemigardanad ke az an baraye so'al-e ba'd estefade koni (ya faghat yek id)
- query javab midahad va system ra avaz nemikonad

**CQRS** (Command Query Responsibility Segregation, Greg Young, va ba'd Fowler an ra moarefi kard) haman ghanun ra az method **bala** mibarad ta model:

- model-e neveshtan joda az model-e khandan
- shayad handler joda, DTO joda, hatta database joda

CQS hamishe mitavanad bedune CQRS bashad (method-ha joda, model yeki). CQRS bedune CQS shekaste ast: agar "query" ham update mikonad, joda kardan-e model dorough ast.

## Se sath — in-ha ra roye ham nari

**Sath-e 1. Joda'i-e code.**
`CreateOrderCommand` va `GetOrderListQuery` do class, do handler. Har do haman jadval ra mikhanand. Model-e write aggregate ast. Model-e read yek DTO-ye flat. Database yeki ast. Consistency ghavi ast: hamun ke commit shod, query-e ba'd haman data ra mibinad.

**Sath-e 2. Joda'i-e model-e dakheli.**
Write aggregate-e normalize. Read view ya query-e denormal ke haman database ast (`SELECT` ba join, ya yek view). Hanuz yek store.

**Sath-e 3. Joda'i-e store.**
Write database-e khod ra darad. Yek projection an ra be store-e read copy mikonad. Grid az store-e dovom mikhanad. Inja **eventual consistency** pish miayad: ba'd az command, ta projection beresad, read mitavanad ghadimi bashad.

Hich sathi "CQRS-e kamel-tar" be ma'naye behtar nist. Sath-e 3 gheymat darad. An ra vaghti bar midari ke sath-e 1 khafash konad (scale-e read, shekl-e gozaresh, tim-e joda).

## Chizi ke CQRS nist

**Event sourcing.**
Zakhire kardan-e **tarikh-e event** bejaye zakhire-ye vaziat-e alan. CQRS aksaran ba an harf zade mishavad chon Young har do ra ba ham zad. Vali CQRS bedune event sourcing tamam-e donya-ye amali ast. Event sourcing bedune joda'i-e read ham momken ast, faghat dardnak. Agar porsidand "CQRS dari?" va to event sourcing nadari, begou nadari. Dorogh-e "bale ma event source mikonim" rizume ra mishkanad.

**CRUD-e do class-e khali.**
`CreateXCommand` ke faghat field-ha ra copy mikonad roye entity, va `GetXQuery` ke haman entity ra bar migardanad. Esm-e CQRS ra dari, joda'i-e model ra na. Model hanuz yeki ast.

**Do microservice-e ejbari.**
CQRS dakhel-e yek process ham ma'ni darad. Joda'i-e deploy joz'-e ta'rif nist.

## Ghanun-ha

**1. Query side-effect-e business nadarad.**
Nabayad vaziat ra avaz konad. Log va metric side-effect-e infra hastand. "Didan-e safhe ra be onvan-e visit hesab kon" side-effect-e business ast va bayad command bashad, na ghalat-e `GetById`.

**2. Command model-e read ra bar nagardan.**
Javab-e command mitavanad id ya vaziat-e natije bashad. Javab-e command **nabayad** graph-e kamel-e UI bashad. Vagarna model-e write dobare shekl-e safhe ra barmidarad va joda'i tamoom mishavad.

**3. Write invariant ra hefz mikonad. Read sari' budan ra.**
Index-e grid, denormal, hatta dade-ye tekrar, to read mojaz ast. Haman tekrar to aggregate-e write kasif ast. Do ghanun-e shekl dari. An ra yek class nakon.

**4. Sath-e 3 ra bedune zaban-e consistency be UI nadeh.**
Agar projection 2 sanie aghab bashad, client ke haman lahze list ra mikhanad bayad bedanad chera radif-e jadid nist. Ya az javab-e khod-e command UI ra be-rooz kon, ya query ra ba'd az lag bezan, ya sath-e 3 ra baraye an safhe entekhab nakon.

**5. Do model ya'ni do jaye taghir.**
Field-e jadid shayad command, aggregate, event, projection, va DTO ra begirad. In hazine-ye sabet-e pattern ast. Agar an ra nagoyi, pattern ra balad nisti.

## Mesal-e donya

```csharp
// write: ghanun
public readonly record struct PlaceOrder(Guid CustomerId, IReadOnlyList<Line> Lines);

// read: shekl-e grid, na aggregate
public readonly record struct OrderListItem(Guid Id, string CustomerName, decimal Total, string Status);
```

Handler-e avval `Order.Place` seda mizanad va commit mikonad. Handler-e dovom `SELECT` mizanad va `OrderListItem` por mikonad. `Order` class field-e `CustomerName` nadarad. An mal-e jadval-e digar ast va faghat to read join mishavad.

## Farq-ha

**Repository.** Repository aggregate-e write ra collection mikonad. CQRS migoyad model-e read aslan an aggregate nist. Repository-e write va query-e read kenar-e ham mimanand.

**Event sourcing.** Tarikh-e taghirat manba'-e haghighat ast. CQRS faghat joda'i-e masir-e khandan va neveshtan ast. Manba'-e haghighat mitavanad hamchenan radif-e jadval bashad.

**CRUD.** Yek model, chahar amal. CQRS vaghti chahar amal digar yek shekl nistand.

## Koja bezan, koja nazan

Bezan vaghti ghanun-e write va shekl-e read har do jaddi hastand, ya read chand bar sangin-tar az write ast.

Nazan vaghti form va jadval haman shekl-and. Do stack hazine-ye khali ast. Sath-e 3 ra baraye "har entity" nasaz. Lag-e projection bug-hayi misazad ke sath-e 1 aslan nadasht.

## Eshtebah-haye rayej

- Goftan-e CQRS va ma'ni kardan-e event sourcing
- Query-i ke `Save` mizanad
- Command-i ke 15 include baraye por kardan-e yek grid mikeshad
- Do database bedune tarh-e lag
- Sync negah dashtan-e do store ba dual write. An shekast-e consistency ast. Projection bayad az vaghe'iat-e commit-shode (event ya outbox) besazad, na az do `Save` mostaghel

## Mafhoom ra injoori begou

> "CQS ghanun-e method ast: query avaz nemikonad. CQRS haman ra ta model joda mikonad. Sath-e avval faghat do handler va do DTO ast va haman database. Sath-e store-e joda eventual consistent ast va hazine darad. Event sourcing lazem-e CQRS nist. Command graph-e UI bar nemigardanad. Query status ra update nemikonad."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

Sath-e ghalib-e module-ha **sath-e 1** ast.

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

Do contract. Har do az MediatR miravand va har do `ErrorOr` bar migardanand. Joda'i in nist ke query exception-e joda dashte bashad. Joda'i in ast ke:

- command `IBaseCommand` ast va validation-e pipeline **faghat** roye an neshast. Query az an constraint rad nemishavad
- handler-e command aggregate load mikonad, method-e entity, `SaveChanges`
- handler-e query projection / `IQueryable` / DTO. Aggregate-e ghabel-e neveshtan bar nemigardanad

Database-e write va read baraye aksar-e module-ha yeki ast. Consistency ghavi ast. In ra "CQRS-e kamel ba do store" seda nakon.

Sath-e 3 ja'i ast ke reporting read-model darad: dade-ye neveshte-shode yek bar-e digar be shekl-e gozaresh zakhire mishavad. An eventual ast. Safhe-hayi ke az an mikhanand nabayad farz konand haman millisecond-e command be-rooz-and. Joz'iat-e an pipeline to `day-64` ast. In ketabche faghat naghsh-ash ra moshakhas mikonad: projection-e read, na aggregate-e write.

Mapster (abzar-e map) pattern nist. Vasat-e sath-e 1 neshaste ta shekl-e entity be shekl-e DTO tabdil shavad. Agar map-e 1:1-e bi-taghir dashte bashi, joda'i-e model-et hanuz kaghazi ast.

`ErrorOr` roye query yani "not found" javab-e khandan ast, na side-effect. An CQS ra nemishkanad.

---

## Script-e 90 sanie

> "CQS migoyad method-e khandan avaz nakonad. CQRS migoyad model-e khandan va neveshtan aslan yeki nabashand. Se sath darad: do handler, do shekl dakhel-e yek database, ya do store ba lag. Event sourcing nist. Dejban sath-e avval ra hameja darad: `ICommand` va `IQuery`, command aggregate ra minevisad, query DTO-ye flat. Validation-e pipeline faghat command ast. Do database-ye ejbari nadarim. Reporting ja'i ast ke read-model-e joda darim va an eventual ast. Command-e man list-e grid bar nemigardanad."

---

## 10 soal

**1. CQS va CQRS farq?**
CQS joda'i-e method ast. CQRS joda'i-e model (va shayad store) ast. Dovomi avvali ra farz mikonad.

**2. Chera yek `Order` baraye ham ghanun ham grid bad ast?**
Shekl-e invariant va shekl-e namayesh yeki nist. Yek class ya ghanun ra nasaz mikonad ya query ra sangin.

**3. Sath-e 1 va sath-e 3 farq-e consistency?**
Sath-e 1 ba commit, khandan-e ba'd rast ast. Sath-e 3 ta projection beresad mitavanad aghab bashad.

**4. Event sourcing kojaye ta'rif ast?**
Hich ja. Manba'-e haghighat mitavanad radif-e alan bashad. Event sourcing tarikh-e event ra manba' mikonad. Pattern-e jodast.

**5. Query mitavanad chi bar gardanad ke hanuz query bemanad?**
DTO, list, flag-e vojud. Nabayad row ra update konad. "Visit ra beshmar" command ast.

**6. Command mitavanad id bar gardanad?**
Bale. Shekastan-e joda'i nist. Shekastan vaghti graph-e kamel-e safhe ra bar migardani va model-e write shekl-e UI mishavad.

**7. Hazine-ye sabet chist?**
Do ja baraye har field-e jadid, va to sath-e 3 tarh-e lag.

**8. To Dejban sath-e ghalib kodam ast?**
Sath-e 1. Do interface, yek database-e module. `ICommand` pipeline-e validation darad. `IQuery` na.

**9. Koja sath-e 3 dide mishavad?**
Read-model-e reporting. An aggregate nist. Ba'd az neveshtan, projection aghab-tar az commit-e asli mibine.

**10. Che shekasti ra to code-e review rad mikoni?**
Query-i ke `SaveChanges` mizanad, ya command-i ke baraye yek grid aggregate ra ba hame-ye relation load mikonad.
