# 02 — Unit of Work

Ye senario ra ta akhar anjam bedeh, bad yek bar benevis. Ya hame-ye taghir-ha zakhire mishavand, ya hich-kodam.

## Moshkel

Sabt-e sefaresh se kar ast: khode sefaresh, kam shodan-e mojudi, ye radif-e hesab.

Agar har kodam haman lahze commit konad va dovomi khata bedahad, sefaresh mande va mojudi na. Database nime-kare ast.

Transaction-e database hamin ra hal mikonad, be sharti ke ye ja baz va baste shavad. Agar har class ettesal va commit-e khodesh ra dashte bashad, kasi nemidanad "in kar tamoom shod" kojast.

## Ide

Unit of Work daftar-e taghir-haye ye kar ast. Chahar jur object ra yadash mimanad:

- **jadid:** bayad insert shavad
- **kasif:** az database amade va avaz shode
- **hazf-shode:** bayad delete shavad
- **tamiz:** amade va avaz nashode, kari ba an nist

Vaghti `Commit` seda zade shavad, hamin daftar ye transaction mishavad va bad khali mishavad.

Ta ghabl az commit, database az in kar khabar nadarad. Agar khata biayad va commit nashavad, disk dast nakhord-e.

Chand ghanun:

**Ye senario, ye daftar, ye commit.** Do bar zakhire yani do transaction. Agar kar bayad yekparche bashad, zakhire-ye vasat mamnoo' ast. Estesna vaghti ast ke amdan do kar-e joda mikhahi: masalan sefaresh bemanad hatta agar email naravad. An vaght do kar-and, na ye Unit of Work.

**Ye shenase, ye object to hafeze.** Agar do bar haman id ra begiri va do copy besazi, yeki ra avaz mikoni va digari ghadimi mimanad. Moghe'-e zakhire malum nist kodam dorost ast. Be in miguyand Identity Map. Change tracker to EF hamin kar ra mikonad.

**Marz-e daftar, marz-e haman kar ast, na marz-e ye jadval.** Chand makhzan mitavanand ye daftar ra sharik bashand, agar haman ettesal va haman tracker bashand. Do database-ye joda ye Unit of Work-e sade nistan. An transaction-e tozi'-shode ast va geran. Baraye khabar dadan be service-e digar, Outbox hast, na kesh dadan-e hamin daftar ru do server.

**Omr-e daftar be andaze-ye haman kar ast.** Ye Unit of Work baraye kol-e omr-e process ghalat ast. List-e kasif bozorg mishavad va do darkhast-e bi-rabt ghati mishavand. To web, aksaran ye darkhast.

**Mowjudiat Commit nadarad.** Agar dashte bashad, har method-e koochak mitavanad zud zakhire konad va marz-e kar beshkanad. Faghat use-case midanad kar tamoom shode.

Agar ORM dari, `DbContext` to EF khodesh hamin daftar ast. `SaveChanges` haman Commit ast. Sakhtan-e class-e taze ke faghat `SaveChanges` ra seda bezanad pattern-e jadid nist. Fayede-ash faghat in ast ke handler esm-e class-e database ra nabinad.

## Mesal-e koochik

```csharp
var order = await orders.GetAsync(id, ct);    // tamiz
order.Pay(amount);                             // kasif shod
payments.Add(new Payment(order.Id, amount));  // jadid
await uow.CommitAsync(ct);                     // ye transaction
```

Agar `Pay` khata bedahad, `Commit` seda nemishavad. Pardakht-e jadid ham neveshte nashode.

## Ba chi ghalt mishavad

**Repository** miguyad kodam object. Unit of Work miguyad key neveshte shavad.

**Outbox** vaghti lazem ast ke hamrah-e zakhire, ye khabar ham hatman be saf beravad. Unit of Work be-tanha-yi saf ra commit nemikonad.

**Transaction-e SQL** zaban-e database ast. Unit of Work zaban-e object ast: nemidani kodam SQL, midani kodam object avaz shode. Tah-e kar, ye transaction baz mikonad.

## Koja estefade nakon

Ye insert-e bi-ghanun, transaction-e khod-e EF kafi ast. Esm-e jadid vasat-ash chizi hal nemikonad.

Unit of Work ra singleton nakon "ta ettesal kamtar masraf shavad". Estakhr-e ettesal kar-e digari ast. Daftar-e toolani yani bug.

## Hala dar Dejban

Interface-e module-e Personnel:

```csharp
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    EntityEntry<TEntity> Entry<TEntity>(TEntity entity) where TEntity : class;
}
```

`SaveChangesAsync` haman Commit ast. Adad-e bargashti tedade radif-haye dast-khorde ast.

`Entry` to ta'rif-e klasik-e in pattern nist. Inja hast ta handler bedune didan-e noe-e context be change tracker beresad. To mosahebe begou in sazesh-e proje ast.

Class-e joda baraye Unit of Work naneveshte-im. `PersonnelsDbContext` ham `DbContext` ast, ham `IUnitOfWork`. Handler context ra be esm-e class-e EF nemibinad.

Sabt in tor ast:

```csharp
services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<PersonnelsDbContext>());
```

`Scoped` yani ye darkhast, ye daftar. Singleton nist.

Handler mowjudiat ra avaz mikonad, event hanuz faghat to hafeze ast, ye `SaveChangesAsync` ham mowjudiat ra minevisad ham niyat-e event ra baraye Outbox.

Har module context-e khodesh ra darad. Daftar-e Personnel taghir-e bazdidkonande ra nemibinad. Yekparchegi dakhel-e module ast. Beyn-e module-ha ye Unit of Work-e moshtarak nasakhte-im. Anja Outbox ast, yani khabar ba kami takhir miresad, na ye commit-e sarasari.

## Agar beporsand, in tor begou

> Unit of Work daftar-e jadid va kasif va hazf-shode-ye ye kar ast va an ra ye transaction mikonad. Repository zakhire nemikonad. Omr-ash be andaze-ye haman darkhast ast. To Dejban khode `PersonnelsDbContext` in daftar ast va `IUnitOfWork` ra piyade karde. Handler ye `SaveChangesAsync` mizanad. Beyn-e module-ha ye daftar-e moshtarak nadarim.

## Dah so'al

**1. Unit of Work che chiz-hayi ra yadash mimanad?**
Object-e jadid, avaz-shode, hazf-shode, va tamiz. Zakhire faghat se tay-e avval ra minevisad.

**2. Farq-ash ba transaction-e SQL chi ast?**
Transaction zaban-e database ast. Unit of Work zaban-e object ast va tah-e kar ye transaction baz mikonad.

**3. Identity Map che mikonad?**
Jeloy-e do copy az ye shenase ra migirad ta taghir ru ye nemune bemanad.

**4. Chera mowjudiat Commit nadarad?**
Chon nemidanad kar tamoom shode ya hanuz ye object-e digar ham bayad avaz shavad.

**5. Do bar Save to ye senario yani che?**
Do transaction. Yekparche nistan.

**6. Chera daftar-e kol-e process ghalat ast?**
List-e taghir bi-andaze bozorg mishavad va do darkhast ghati mishavand.

**7. EF ke khodesh in kar ra mikonad. Class-e jadid che fayede-i darad?**
Agar faghat `SaveChanges` ra jelo befrestad, fayede-ash makhfi kardan-e noe-e EF az handler ast.

**8. To Dejban Unit of Work kodam class ast?**
`PersonnelsDbContext` va mo'adel-ash to har module, ke `IUnitOfWork` ra piyade karde.

**9. Chera Scoped?**
Ta marz-e daftar barabar-e marz-e darkhast bashad.

**10. Do module ra chetor ye commit mikoni?**
Ba in daftar nemikoni. Har kodam tracker-e khodesh ra darad. Hamahangi-shan Outbox ast.
