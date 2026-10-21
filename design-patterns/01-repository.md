# 01 — Repository

---

## Ye khat

Repository ja-neshin-e yek **majmue** ast. Client fekr mikonad object-ha to yek list-e hafeze neshaste-and: yeki ra ba shenase peyda kon, yeki ra ezafe kon, yeki ra hazf kon. Inke an list vaghe'an jadval-e SQL ast, file ast, ya API-e kasi digar, posht-e hamin ja-neshin mimanad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkeli ke hal mikonad

Code-e business yek kar darad: ghanun. "Agar personnel hazf shode, dobare hazf nashavad." "Agar code-e melli tekrar ast, nasaz."

Code-e data yek kar-e digar darad: kojast, che shekli roye disk darad, che join-i mikhahad, che lock-i.

Agar in do ta to yek method bashand, har taghir-e jadval ghanun ra mikeshad, va har taghir-e ghanun SQL ra. Test-e ghanun ham bedune database mojaz nist.

Repository in do jahan ra ba yek **gharardad-e majmu'e** joda mikonad. Samt-e business migoyad "personnel-e ba in id ra behem bedeh". Samt-e data tasmim migirad an jomle yani kodam `SELECT`.

## Ta'rif-e daghigh

Az ketab-e Evans (DDD): repository baraye har aggregate-e root yek majmu'e-ye mafhumi ast. Az an aggregate ra **misazi**, **peyda mikoni**, va **hazf mikoni**, ba zaban-e domain, na ba zaban-e query.

Az Fowler (Patterns of Enterprise Application Architecture): repository vasete-ye beyn-e domain va data-mapping ast ta shabihe collection bashad.

Do ta'rif yek chiz ra migoyand, ba yek stress-e mokhtalef:

- Evans stress mizad **marz-e aggregate**. Repository baraye har jadval nist. Baraye root ast. Bach-e-ha (document-e personnel, item-e sefaresh) az rah-e root load mishavand, na az repository-e jodagane-ye khod.
- Fowler stress mizad **shabihe collection**. `Add` va `Get` bayad mesl-e list bashand. Client transaction va SQL ra nabinad.

Agar har do ra dashte bashi, repository-e dorost dari. Agar faghat `GetAll` roye har jadval dashte bashi, esm-e repository ra roye DAO gozashte-i.

## Sherkat-konande-ha

| Naghsh | Mani | Chi ra midanad | Chi ra nemidanad |
|---|---|---|---|
| Client | use-case, handler, service | "personnel ra mikhaham" | SQL, schema, ORM |
| Repository (gharardad) | interface-e majmu'e | amal-haye zaban-e domain | joziat-e zakhire |
| Implementation | class-e posht-e interface | ORM, query, mapping | ghanun-e business |
| Aggregate | object-e domain | ghanun-e khod | inke chetor load shode |

Client implementation ra seda nemizanad. Implementation aggregate ra "por" mikonad va pas midahad. Ba'd az an, ghanun dakhel-e aggregate ejra mishavad, na dakhel-e repository.

## Sakhtar

```
Client
  |  Get(id) / Add(entity) / Remove(entity)
  v
IRepository          <-- gharardad, zaban-e domain
  |
  v
RepositoryImpl       <-- tanha ja-i ke data ra midanad
  |
  v
Jadval / file / API
```

Client felesh-e payin ra nemibinad. Faghat felesh-e aval ra mibinad.

## Ghanun-hayi ke pattern ra pattern mikonand

**1. Zaban-e method esm-e domain ast.**
`GetById`, `Add`, `FindUnpaidByCustomer`. Na `ExecuteSql`, na `Query("select ...")`. Agar method-e repository jomle-ye SQL-e parameter-dar mipazirad, digar ja-neshin-e majmu'e nist. Shode query-runner.

**2. Yek repository baraye yek aggregate root.**
Sefaresh repository darad. Khat-e sefaresh repository-e joda nadarad. Khat ra az dakhel-e sefaresh migiri. Dalil: invariant-e "jam'e khat-ha ba gheymat yeki bashad" faghat vaghti yek object-e kamel dast-e to ast ghabel-e hefz ast. Agar khat ra joda load koni, invariant ra dor zade-i.

**3. Add zakhire-ye nahayi nist.**
To yek list-e hafeze, `list.Add(x)` yani "alan to majmu'e ast", na "alan roye disk raft". Commit kar-e repository nist. Kar-e Unit of Work ast (ketabche-ye ba'd). Repository-i ke vasat-e `Add` khodesh `COMMIT` mizanad, client ra az jam' kardan-e chand taghir-e atomik mahrum mikonad.

**4. Implementation ghabel-e avaz ast, gharardad na.**
Emruz Postgres, farda test-e fake. Client taghir nakonad. In faghat vaghti arzeshesh darad ke gharardad **kuchak va sabet** bashad. Agar interface hame-ye tavanayi-haye ORM ra birun bedahad (`Include`, `AsNoTracking`, raw SQL), avaz kardan-e implementation dorough ast: client aslan be haman ORM vast shode.

**5. Repository ghanun-e business ejra nemikonad.**
"Hazf yani event ham besaz" kar-e entity ast. "Hazf-shode-ha ra to list nayavar" mitavanad kar-e repository bashad, chon an **tarif-e majmu'e** ast: majmu'e-ye personnel-haye zende. Farq-e in do ra yad begir. Avvali invariant-e yek object. Dovomi tarif-e chizi ke to majmu'e hast.

## Anva'

**Collection-oriented.**
`Add`, `Remove`, `Get`. Mesl-e `HashSet`. ORM taghir ra track mikonad. In haman shekli ast ke Evans goft.

**Persistence-oriented.**
`Save`, `Update`, `Insert` joda. Kamtar shabihe collection, bishtar shabihe DAO. Vaghti ORM-e change-tracker nadari (Dapper-e khali) in shekl-e rast ast, chon kasi joz to nemidanad INSERT ast ya UPDATE.

**Generic `IRepository<T>`.**
Yek interface baraye hame-ye entity-ha: `Get`, `Add`, `Delete`, `List`. Vasvas-e konande ast chon kam code dari. Shekast-e ma'mool:

- method-haye vaghe'i yek shape nistand (`GetWithDocuments` mal-e personnel ast, mal-e `T` nist)
- `IQueryable<T>` az generic birun mirizad va client query-e ORM minevisad
- aggregate-haye mokhtalef yek gharardad-e dorough-e yeksan migirand

Generic baraye CRUD-e bi-ghanun kar mikonad. Baraye domain-e por-ghanun, interface-e **dasti-e har aggregate** dorost-tar ast.

**Read repository joda az write.**
Write: `Get` kamel-e aggregate, `Add`. Read: list-e flat, projection, pagination. In digar CQRS ast ke ba repository tarkib shode. Repository-e write nabayad DTO-ye grid bar gardanad. Repository-e read nabayad aggregate-e ghabel-e `Save` bar gardanad.

**Specification.**
Bejaye `FindOverdue(date)` va `FindUnpaid(customer)` va tarkib-e an-ha, yek object-e shart (`OverdueSpec`) miferesti. Repository an shart ra be query tabdil mikonad. Ghavi ast, vali yek pattern-e **digar** ast. Repository-e sade bedune specification ham repository ast. An-ha ra yek chiz seda nakon.

## Mesal-e donya, ghabl az har proje

```csharp
public interface IOrderRepository
{
    Task<Order?> GetAsync(Guid id, CancellationToken ct);
    void Add(Order order);
}

public sealed class CreateOrderHandler(IOrderRepository orders, IUnitOfWork uow)
{
    public async Task Handle(NewOrder request, CancellationToken ct)
    {
        var order = Order.Place(request.CustomerId, request.Lines);
        orders.Add(order);
        await uow.CommitAsync(ct);
    }
}
```

Handler nemidanad `Orders` jadval ast ya document. `Order.Place` ghanun ra darad. `Add` faghat elam mikonad "in yeki azin be ba'd ozv-e majmu'e ast". `Commit` jaye digar ast.

Test-e hamin handler yek class-e koochak-e fake ast ke `Order` ra to `List` negah midarad. Database nist. Arzesh-e pattern hamin joda'i ast.

## Farq ba chiz-hayi ke eshtebah gerefte mishavand

**DAO (Data Access Object).**
DAO row va query ra mipooshand: `FindById` baraye yek jadval, `UpdateColumns`. Zaban-ash zaban-e jadval ast. Repository zaban-e aggregate ast. Yek DAO mitavanad chand jadval ra join konad va DTO bedahad. Repository gharardad mikonad object-e domain-e kamel bedahad, na yek row-e denormal.

**Table Gateway / Active Record.**
Table Gateway yek class baraye yek jadval, ba method-haye SQL. Active Record object-e domain khodesh `Save()` darad va az database khabar darad. Repository amdan in khabar ra **az** object migirad. Entity repository ra inject nemikonad. Agar entity `this.Save()` dashte bashad, repository nist.

**Unit of Work.**
Repository migoyad che objecti. UoW migoyad key hame-ye taghir-ha paydar shavand. Yek object mitavanad har do naghsh ra bazi konad (mesl-e DbContext), vali do naghsh-and. Client-e khoob har do ra be esm-e naghsh mibinad, na be esm-e class-e database.

**Service.**
Service kar-e chand aggregate ra hamahang mikonad. Repository yek majmu'e ast. "Sefaresh besaz va email befran" service ast. "Sefaresh ra bargardan" repository ast.

## Koja bezan, koja nazan

Bezan vaghti:

- ghanun-e domain dari va mikhahi bedune database test shavad
- mikhahi joziat-e load (join, filter-e "hazf-nashode", tenant) yek ja bashad
- chand implementation-e vaghe'i ya hadaghal yek fake mikhahi

Nazan, ya nazok negah dar, vaghti:

- faghat CRUD-e form ast va ORM khodesh hamin abstraction ra dade
- interface-at hame-ye ORM ra pass-through mikonad. Pas fake-at ham bayad ORM bashad va chizi joda nashode
- report-e 20 filter. An query ast, na majmu'e-ye aggregate. Yek class-e read joda besaz, be repository-e write nakob.

## Eshtebah-haye rayej

- Repository-e "khoda": 40 method, ham aggregate, ham report, ham email.
- `IQueryable` ra ta controller rad kardan. Client query misazad, pas implementation dige avaz nemishavad.
- Ghanun-e "mitavan hazf kard" dakhel-e `Delete` repository, va entity faghat kisse-ye data.
- Yek repository-e generic + cast-e daemi be type-e ORM.
- Farz kardan repository transaction ham hast. Nist.

## Chetor to mosahebe mafhoom ra begou, ghabl az esm-e proje

> "Repository collection-e aggregate ast, na wrapper-e jadval. Client Add va Get mibinad. SQL va commit ra nemibinad. Yek repository baraye root, na baraye har jadval-e bache. Generic repository ra vaghti method-ha yek shape nadarand estefade nemikonam, chon IQueryable leak mishavad va gharardad dorough yeksan mishavad. Farq-ash ba DAO in ast ke DAO row midahad va repository object-e domain-e ba invariant."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

Gharardad-e personnel hamin collection ast, ba chand method-e zaban-e domain:

`Microservices/Dejban/Modules/Personnels/Dejban.Modules.Personnels.Domain/Personnels/IPersonnelRepository.cs`

- `GetAsync` / `GetWithDocumentsAsync` — peyda kardan-e root, va yek bar load-e bache-ha vaghti lazem ast
- `Insert` / `InsertDocument` / `RemoveDocument` — ezafe va hazf. Save nist
- `SoftDeleteByUnitIdAsync` / `SoftDeleteBySiteIdAsync` — amal-e jam'i-e haman majmu'e, na SQL-e azad

Interface to **Domain** ast. Implementation to Infrastructure, va `PersonnelsDbContext` ra mibinad. Handler faghat interface ra mibinad. In haman joda'i-e bakhsh-e avval ast.

`Insert` commit nemikonad. Commit `IUnitOfWork.SaveChangesAsync` ast, va khod-e `PersonnelsDbContext` haman UoW ast. Pas do naghsh roye yek class-e EF neshastand, vali handler an-ha ra az do interface mibinad.

`GetQueryable` roye hamin interface hast. Az nazar-e kitab, in leak-e `IQueryable` ast ke bala goftam nabayad ta UI beravad. To in proje baraye pagination-e application baz shode. Agar to mosahebe gofti "repository-e ma hichvaght query birun nemidahad", ba hamin method dorogh shode-i. Jomle-ye dorost: write az method-e aggregate miravad. Read gahi `IQueryable` ra to application negah midarad, na to controller.

Repository generic-e `IRepository<T>` inja gharardad nist. Method-hayi mesl-e `GetWithDocumentsAsync` dalil-e haman bakhsh-e "chera generic na" hastand.

Report-e sangin va read-model-e joda (reporting) ra to hamin repository nakubide-and. An sath-e CQRS ast, na method-e panjahom-e `IPersonnelRepository`.

---

## Script-e 90 sanie

Avval mafhoom, ba'd proje:

> "Repository ra collection-e aggregate midanam. Client Get va Add mibinad, SQL va commit ra na. Root repository darad, bache-ha az rah-e root load mishavand. Add zakhire-ye nahayi nist. To Dejban `IPersonnelRepository` to domain-e Personnels hast: Get, GetWithDocuments, Insert. Insert save nemikonad. Save `IUnitOfWork` ast va `PersonnelsDbContext` an interface ra implement karde. Generic nasakhtim chon method-ha yek shape nistand. `GetQueryable` ra darim va an ra mahdud be application negah midarim, na inke begoyam ketab 100% ra'ayat shode."

---

## 10 soal

**1. Repository daghighan ja-ye chi ra migirad?**
Ja-ye majmu'e-ye aggregate. Client fekr mikonad list-e object darad. Zakhir-e vaghe'i posht-e interface ast.

**2. Chera baraye har jadval repository nemisazi?**
Chon invariant-e aggregate faghat ba root-e kamel hefz mishavad. Repository-e joda baraye bache, object ra shekaf mikonad.

**3. Farq-e `Add` va `Commit` chist?**
`Add` ozviat-e majmu'e ra elam mikonad. `Commit` an ra paydar mikonad va kar-e repository nist.

**4. DAO che farqi darad?**
DAO zaban-e row va jadval ast. Repository zaban-e object-e domain ast va gharardad mikonad aggregate-e kamel bedahad.

**5. Generic repository che-vaght shekast mikhorad?**
Vaghti method-haye domain yek emza nadarand, ya `IQueryable` birun mirizad va client be ORM vast mishavad.

**6. `IQueryable` roye interface yani chi?**
Yaani implementation dige kamelan avaz-pazir nist, chon client query-e haman ORM ra sakhte. Mitavanad amdan baraye read-e dakheli-e application baz shavad, be shart-e inke az an laye birun naravad.

**7. Ghanun-e "nabayad dobare hazf shavad" koja beneshinad?**
To entity. Repository faqat mitavanad majmu'e ra "faghat zende-ha" tarif konad.

**8. To Dejban in gharardad koja neshaste?**
`IPersonnelRepository` to domain. `Insert` save nist. Context-e EF posht-e implementation ast va joda `IUnitOfWork` ham hast.

**9. `GetWithDocumentsAsync` kodam ghanun-e kitab ra barmiavarad?**
Bache (document) repository-e joda nadarad. Az rah-e root, vaghti senario document mikhahad, load mishavad.

**10. Chetor test mikoni bedune database?**
Fake-e interface ke `List<Personnel>` ast. Handler ra ba an seda mizani. Test-e khod-e SQL test-e implementation ast, na test-e ghanun-e handler.
