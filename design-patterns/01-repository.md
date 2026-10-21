# 01 — Repository

Ye anbar ra tasavor kon. Kasi ke sefaresh sabt mikonad nabayad bedanad kala dar ghafase-ye chand ast. Faghat miguyad: "sefaresh ba in shomare ra biavar" va "in sefaresh ra bezar dakhel-e anbar". Inke posht-e anbar jadval-e SQL ast ya file, be u marbut nist.

Repository hamin gharardad ast. Code-e business ba ye list az object-ha harf mizanad. Zakhire-ye vaghe'i posht-e haman list mimanad.

## Moshkel

Sabt-e personnel do jur kar darad.

Yeki ghanun ast: agar hazf shode, dobare hazf nashavad. Agar code-e melli tekrar ast, nasaz.

Yeki zakhire ast: kodam jadval, kodam join, kodam filter-e site.

Agar har do to ye method bashand, har taghir-e jadval ghanun ra ham mikeshad. Test-e ghanun ham bedune database emkan nadarad.

Repository in do ra joda mikonad. Handler miguyad "personnel ba in shenase ra bede". Class-e posht-e interface tasmim migirad in jomle kodam `SELECT` ast.

## Ide

Code-e business se kar ba ye mowjudiat mikonad: peydash konad, ezafe konad, hazf konad. Mesl-e ye list to hafeze.

Chand ghanun-e sade in pattern ra pattern mikonad.

**Zaban-e method, zaban-e domain ast.** `GetById` va `Add` dorost ast. `ExecuteSql` yani digar list nisti, shode-i ejrakonande-ye query.

**Baraye rishe-ye mowjudiat ye makhzan dari, na baraye har jadval.** Sanad-e personnel makhzan-e joda nadarad. Az khode personnel bargozari mishavad. Agar bache ra joda begiri, ghanun-e "personnel va sanad-ha-yash ba ham motabar-and" mishkanad.

**Ezafe kardan yani ozv-e list shod, na inke ru disk raft.** Zakhire-ye naha'i kar-e Repository nist. Kar-e Unit of Work ast. Agar `Add` haman lahze commit konad, digar nemitavani do taghir ra ba ham yekja benevisi.

**Makhzan ghanun-e business ejra nemikonad.** "Hazf yani event ham sakhte shavad" kar-e khode mowjudiat ast. "Hazf-shode-ha ra to list niavar" mitavanad kar-e makhzan bashad, chon ta'rif-e khode list ast: list-e personnel-haye zende.

Ye makhzan-e omumi `IRepository<T>` baraye hame-ye mowjudiat-ha vasvase-konande ast, chon code kam mishavad. Zud mishkanad. Method-haye vaghe'i ye shekl nistan. `GetWithDocuments` mal-e personnel ast, mal-e har `T` nist. Aksaran ham `IQueryable` az in interface nashat mikonad va masraf-konande dobare be ORM michasbad.

## Mesal-e koochik

```csharp
public interface IOrderRepository
{
    Task<Order?> GetAsync(Guid id, CancellationToken ct);
    void Add(Order order);
}

var order = Order.Place(customerId, lines); // ghanun inja
orders.Add(order);                           // faghat ozv-e list
await uow.CommitAsync(ct);                   // zakhire inja
```

Test-e in handler ye class-e ja'li ast ke `Order` ra to ye `List` negah midarad. Database lazem nist.

## Ba chi ghalt mishavad

**DAO** ba zaban-e radif va jadval harf mizanad: in sotun ra update kon. Repository ba zaban-e object-e domain harf mizanad va mowjudiat-e kamel barmigardanad.

**Active Record** yani khode mowjudiat `Save()` darad va az database khabar darad. Dar Repository mowjudiat az zakhire khabar nadarad.

**Unit of Work** miguyad key hame-ye taghir-ha neveshte shavand. Repository miguyad kodam object. Ye class-e EF mitavanad har do naghsh ra bazi konad, vali do naghsh-and.

**Service** chand kar ra hamahang mikonad, masalan sefaresh besaz va email befrest. Repository faghat haman list ast.

## Koja estefade nakon

Form-e sade-ye chahar fieldi ke hich ghanuni nadarad, gahi ba khode EF kafi ast. EF az ghabl ye jur Repository va Unit of Work ast. Laye-ye ezafe faghat vaghti miarzad ke ghanun-e domain dari va mikhahi bedune database test shavad, ya mikhahi tarz-e bargozari (join, hazf-nashode-ha, site) ye ja bemanad.

Gozaresh-e bist-filteri ra dakhel-e makhzan-e mowjudiat nariz. An query-e khandan ast, na list-e mowjudiat.

## Hala dar Dejban

Gharardad-e personnel injast:

`Microservices/Dejban/Modules/Personnels/Dejban.Modules.Personnels.Domain/Personnels/IPersonnelRepository.cs`

- `GetAsync` va `GetWithDocumentsAsync` yani rishe ra peyda kon, va sanad-ha ra faghat vaghti lazem ast ba ham biavar.
- `Insert` va `InsertDocument` va `RemoveDocument` yani ezafe va hazf. Zakhire nistan.
- `SoftDeleteByUnitIdAsync` kar-e daste-jam'i ru haman list ast, na ye SQL-e azad.

Interface to Domain ast. Piyadesazi to Infrastructure va `PersonnelsDbContext` ra mibinad. Handler faghat interface ra mibinad.

`Insert` zakhire nemikonad. Zakhire `IUnitOfWork.SaveChangesAsync` ast. Khode `PersonnelsDbContext` haman Unit of Work ast.

`GetQueryable` ru hamin interface hast. Yani query-e EF ta laye-ye application bala amade. Agar to mosahebe begouyi "makhzan-e ma hichvaght query birun nemidahad" ba hamin method dorugh gofte-i. Jomle-ye dorost: neveshtan az method-e mowjudiat miravad. Khandan gahi `IQueryable` ra dakhel-e application negah midarad, na ta controller.

Makhzan-e omumi `IRepository<T>` inja gharardad nist. `GetWithDocumentsAsync` dalil-ash hamin ast ke method-ha ye shekl nistan.

## Agar beporsand, in tor begou

> Makhzan ra list-e mowjudiat midanam. Handler Get va Add mibinad, SQL va commit ra na. Rishe makhzan darad, bache-ha az rah-e rishe miayand. Insert zakhire nist. To Dejban `IPersonnelRepository` to domain-e Personnel ast. Zakhire ba `IUnitOfWork` ast va khode context-e EF an ra piyade karde. Makhzan-e generic nasakhtim. `GetQueryable` ra darim va ta UI nemiravad.

## Dah so'al

**1. Repository jay-e che chizi ra migirad?**
Jay-e list-e mowjudiat. Code-e business fekr mikonad ba object-ha kar mikonad. Zakhire posht-e interface ast.

**2. Chera baraye har jadval ye makhzan nemisazi?**
Chon ghanun-e mowjudiat faghat vaghti hefz mishavad ke rishe va bache-hash ba ham bashand.

**3. Farq-e Add va Commit chi ast?**
Add miguyad ozv-e list shod. Commit ru disk minevisad va kar-e makhzan nist.

**4. DAO che farqi darad?**
DAO radif va sotun midahad. Repository object-e domain-e kamel midahad.

**5. Makhzan-e generic koja mishkanad?**
Vaghti method-haye vaghe'i ye emza nadarand, ya `IQueryable` birun mizanad va masraf-konande be ORM michasbad.

**6. Ghanun-e "dobare hazf nashavad" koja mineshinad?**
Dakhel-e mowjudiat. Makhzan faghat mitavanad list ra "faghat zende-ha" ta'rif konad.

**7. To Dejban in gharardad kojast?**
`IPersonnelRepository` to domain. `Insert` zakhire nist. Context-e EF posht-e piyadesazi ast.

**8. `GetWithDocumentsAsync` kodam ghanun ra neshan midahad?**
Sanad makhzan-e joda nadarad. Az rah-e personnel, vaghti lazem bashad, bargozari mishavad.

**9. Chetor bedune database test mikoni?**
Ye class-e ja'li ke personnel ra to `List` negah midarad. Test-e khod-e SQL test-e piyadesazi ast, na test-e ghanun-e handler.

**10. Gozaresh-e sangin ra koja migozari?**
Kharej az makhzan-e mowjudiat. Query-e khandan ya model-e khandan-e joda.
