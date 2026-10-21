# 02 — Unit of Work

---

## Ye khat

Unit of Work yek **vahed-e kar** ra negah midarad: hame-ye chiz-hayi ke in senario avaz karde, ta yek lahze ba ham paydar shavand. Ya hame minevisand, ya hich-kodam.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Yek senario kam-tar az "yek jadval" kar mikonad. Sefaresh sakhte mishavad, mojudi kam mishavad, yek satr-e hesab ham neveshte mishavad. Agar har kodam haman lahze `COMMIT` khod ra bezanad:

- avvali commit shode, dovomi exception dade → sefaresh-e bi-mojudi
- dobare run kardan-e senario moshkel ra badtar mikonad, chon bakhsh-i az kar hanuz hast

Transaction-e database hamin moshkel ra hal mikonad, vali faghat agar **yek** ja transaction baz va baste shavad. Agar har class khodesh connection va commit dashte bashad, kasi nemidanad marz-e "in kar tamoom shod" kojast.

## Ta'rif

Fowler: Unit of Work list-e object-hayi ra negah midarad ke az database load shode ya sakhte shode-and, taghir-ha ra hesab mikonad, va **yek bar** an-ha ra minevisad. Hamchenan concurrency ra (ki in object ra dast zade) mitavanad modiriat konad.

Chahar list-e zehn-i, hatman be hamin esm-ha to code nistan:

- **new** — object-hayi ke bayad INSERT shavand
- **dirty** — object-hayi ke load shode-and va avaz shode-and
- **removed** — object-hayi ke bayad DELETE shavand
- **clean** — load shode, avaz nashode, kari nist

Vaghti `Commit` seda mikhorad, UoW in list-ha ra be yek transaction tabdil mikonad va khali mikonad.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Client (use-case) | object-ha ra avaz mikonad va **yek bar** commit mikhahad |
| Unit of Work | taghir ra sabt mikonad va atomik minevisad |
| Repository | object ra az majmu'e migirad ya be an ezafe mikonad. Khodash commit nemikonad |
| Database | transaction-e vaghe'i |

Repository va UoW do naghsh-and. Client har do ra mikhahad. Repository bedune UoW ya zud commit mikonad ya aslan commit nemikonad. UoW bedune repository ham momken ast (client mostaghim object ra register konad), vali ma'moolan repository `Add` ra be UoW-e jari elam mikonad.

## Sakhtar-e zehni

```
use-case
  |-- repo.Get(order)      --> object-e clean, dakhel-e UoW track shod
  |-- order.AddLine(...)   --> haman object dirty shod
  |-- repo.Add(payment)    --> object-e new
  |-- uow.Commit()         --> BEGIN; INSERT; UPDATE; COMMIT;
```

Ta ghabl az `Commit` database az in kar khabar nadarad. Rollback ya exception = list-e hafeze dor mirizad, disk dast nakhode.

## Ghanun-ha

**1. Yek use-case, yek UoW, yek commit.**
Do `Commit` yani do transaction. Agar senario bayad atomik bashad, commit-e vasat mamnoo' ast. Istisna-ye agahane: vaghti **amdan** mikhahi bakhsh-e avval paydar shavad hatta agar bakhsh-e dovom fail shavad (masalan "sefaresh sabt shod" joda az "email raft"). An dige yek unit of work nist. Do unit ast va bayad be esm-e do senario joda shavad.

**2. UoW identity ra ham negah midarad.**
Agar do bar haman id ra load koni, bayad **haman object-e hafeze** ra begiri, na do copy. Vagarna yeki ra avaz mikoni, copy-e digar ghadimi mimanad, va commit nemidanad kodam rast ast. In ra Identity Map migoyand. UoW-e khoob ya khodesh an ra darad, ya roye chizi saresh mishavad ke darad (change tracker-e ORM).

**3. Marz-e UoW marz-e transaction-e business ast, na marz-e jadval.**
Chand repository mitavanand yek UoW ra share konand, **agar** haman connection va haman tracker bashand. Do database-e joda yek UoW-e sade nistand. An distributed transaction ast va gheymat-ash balast. Pattern-e outbox baraye haman ja amade, na baraye inke UoW ra kesh bedahi roye do server.

**4. Lifetime-e UoW = lifetime-e senario.**
Yek UoW baraye hame-ye omr-e process ghalat ast: list-e dirty roshd mikonad, do kar-e bi-rabt yek tracker ra share mikonand, va thread-ha roye yek object-e gheyr-e amn race mikonand. UoW-e durust ba shoru'-e kar sakhte mishavad va ba commit ya fail dor mirizad. To web, in aksaran "yek request" ast.

**5. Object-e domain UoW ra nemishnasad.**
Entity `Commit()` nadarad. Agar dashte bashad, har method-e koochak mitavanad zud commit konad va marz-e senario shekaste mishavad. Use-case tanha kasi ast ke midanad kar tamoom shode.

## Anva'

**UoW-e dasti.**
Khodet list-e new/dirty/removed ra negah midari va SQL minevisi. Mofid vaghti ORM nadari. Khatarnak vaghti identity map ra faramoosh koni.

**UoW-e ORM.**
`DbContext` dar EF, `Session` dar NHibernate, `DataContext` dar LINQ to SQL. Change tracker haman chahar list ast. `SaveChanges` haman `Commit` ast. Sakhtan-e class-e `UnitOfWork` ke faghat `SaveChanges` ra seda bezanad pattern-e jadid nist. Yek esm-e ezafe ast. Arzesh-e esm-e ezafe faghat in ast ke client type-e ORM ra nabinad.

**UoW be ezaye request.**
Middleware ya scope-e DI avval-e request UoW misazad, akhar-e request commit mikonad. Use-case `Commit` ra faramoosh nemikonad. Gheymat: har request hatta read-e khali ham tracker darad, va commit-e zood-hanjam (avval-e method, bad exception) hanuz yek transaction-e nimekash ast agar akhar-e request koor-koor commit konad. Commit-e **explicit** to use-case shaffaf-tar ast.

**UoW-e chand resource.**
Do connection, yek `TransactionScope`. Az nazar-e mafhoom haman "ya hame ya hich" ast. Az nazar-e amal, lock va failure-e shabake an ra akharin charre mikonad, na avvalin.

## Mesal-e donya

```csharp
await using var uow = factory.Begin();
var order = await orders.GetAsync(id, ct);   // clean
order.Pay(amount);                            // dirty
payments.Add(new Payment(order.Id, amount)); // new
await uow.CommitAsync(ct);                   // yek transaction
```

Agar `Pay` exception bedahad, `Commit` seda nemishavad. Payment-e new ham disk nashode. In kol-e pattern ast.

## Farq-ha

**Transaction Script.**
Yek method, yek SQL-e boland, yek transaction. UoW nist chon object-e track-shode nist. Baraye kar-e sade kafi ast. UoW vaghti chand object-e zende dari va nemikhahi har method SQL-e khod ra commit konad.

**Repository.**
Majmu'e. UoW dafatar-e taghirat. `Get` kar-e avvali, `Commit` kar-e dovomi.

**Outbox.**
UoW yek database ra atomik mikonad. Outbox vaghti bayad **khabar** ham ba haman commit gharanti shavad, bedune commit-e dovom roye bus. UoW ja-ye outbox ra nemigirad.

**Identity Map tanha.**
Identity map faghat "do load = yek object" ast. UoW an ra **be alave-ye** list-e taghir va commit darad. Mishe identity map bedune UoW dasht. UoW-e khoob bedune identity map shekaste ast.

## Koja bezan, koja nazan

Bezan vaghti chand taghir bayad atomik bashand va nemikhahi har repository commit-e makhfi dashte bashad.

Nazan vaghti:

- yek insert-e bi-ghanun dari va transaction-e ORM kafi ast. Esme jadid vasat-e an chizi hal nemikonad
- do service-e shabake ra mikhahi yek UoW koni. An distributed transaction ast. Avval tarahi ra avaz kon
- UoW ra singleton mikoni "ta connection kam masraf shavad". Connection pool kar-e digar ast. UoW-e long-lived bug ast

## Eshtebah-haye rayej

- `Save` dakhel-e har `Add`
- do context-e joda va farz-e yek transaction
- `Commit` to constructor ya to getter
- entity-i ke repository ya UoW inject mikonad
- farz kardan `SaveChanges` hamishe yek round-trip-e koochak ast. Tracker-e bozorg (hezaran object) commit-e geran va gheyr-e ghabil-e pishbini misazad

## Mafhoom ra injoori begou

> "Unit of Work dafatar-e taghir-e yek senario ast: chi jadid ast, chi kasif ast, chi bayad hazf shavad. Yek commit an dafatar ra yek transaction mikonad. Repository object ra midad, UoW zaman-e neveshtan ra moshakhas mikonad. UoW ba senario be donya miayad va ba commit mimirad. Do database ra ba yek UoW ja nemizanam."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

Gharardad-e module-e Personnels:

```csharp
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    EntityEntry<TEntity> Entry<TEntity>(TEntity entity) where TEntity : class;
}
```

`SaveChangesAsync` haman `Commit` ast. Bargardandan-e `int` tedad-e row-e dast-khorde ast. Chiz-e ezafe-ye kitab nist. Mofid ast baraye fahmidan-e "aya aslan chizi nevesht".

`Entry<T>` ra kitab-e Fowler nadasht. Inja hast ta handler, bedune didan-e type-e context, be change tracker dastresi dashte bashad. Naghsh-e UoW ra kam kamar bozorg-tar az "faghat commit" karde. To mosahebe begou in sazesh ast, na inke UoW-e klasik `Entry` dashte bashad.

Implementation class-e joda nist. `PersonnelsDbContext` ham `DbContext` ast ham `IUnitOfWork` ham `ITenantDbContext`. Ya'ni change tracker-e EF haman chahar list-e Fowler ast, va ma faghat esm-e `Commit` ra `SaveChangesAsync` seda mizanim va an ra az interface-e khodeman export mikonim ta handler `DbContext` ra type-e vaghe'i nabinad.

Sabt:

```csharp
services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<PersonnelsDbContext>());
```

`Scoped` haman ghanun-e lifetime ast: yek request, yek tracker. Singleton nist.

Handler model-e bakhsh-e avval ra anjam midahad: repository load ya `Insert` mikonad, entity method-e ghanun ra mizanad (`Raise` hanooz faghat memory ast), yek `SaveChangesAsync` ham aggregate ra minevisad ham — ba outbox — niyat-e event ra. Do commit-e makhfi nist.

Har module context-e khod ra darad. Pas UoW-e Personnels taghir-e Visitors ra nemibinad. Atomik budan **dakhel-e module** ast. Beyn-e module-ha UoW-e moshtarak nasakhte-and. Anja outbox va inbox marz-e consistency ra avaz mikonand (eventual). In ra be onvan-e "UoW-e bozorg-e hame-ye Dejban" nagou. Ghalat ast.

---

## Script-e 90 sanie

> "Unit of Work dafatar-e new va dirty va removed-e yek senario ast va an ra yek transaction commit mikonad. Repository commit nemikonad. Lifetime-ash haman senario ast, na hame-ye process. To Dejban khod-e `PersonnelsDbContext` hamin dafatar ast va `IUnitOfWork` ra implement karde. Handler yek `SaveChangesAsync` mizanad. Scoped ast ta request-ha tracker ra share nakonand. `Entry` roye interface yek sazesh-e amali ast. Beyn-e module-ha yek UoW nadarim, chon do database-e manteghi ra amdan yek transaction nakardim."

---

## 10 soal

**1. UoW che chahar chizi ra yadash midarad?**
Object-e jadid, kasif (avaz-shode), hazf-shode, va tamiz (load-shode-ye bi-taghir). Commit faghat se dafe-ye avval ra minevisad.

**2. Farq-ash ba khod-e transaction-e SQL chist?**
Transaction zaban-e database ast. UoW zaban-e object ast: nemidani kodam SQL, midani kodam object avaz shode. UoW dar nahayat yek transaction baz mikonad.

**3. Identity map inja che mikonad?**
Jeloye do copy az yek id ra migirad ta taghir roye yek instance bemanad.

**4. Chera entity `Commit` nadarad?**
Chon entity nemidanad senario tamoom shode ya hanuz yek object-e digar ham bayad avaz shavad.

**5. Do `Save` to yek senario yani chi?**
Do transaction. Atomik nistand. Faghat age amdan do kar-e joda mikhahi in kar dorost ast.

**6. Chera UoW-e process-wide shekaste ast?**
Tracker bi-nahayat roshd mikonad, do senario ghat mishavand, va concurrency-e object-e gheyr-e amn pish miayad.

**7. ORM ke khodesh UoW ast. Class-e jadid che arzeshi darad?**
Hich, agar faghat forward-e `SaveChanges` bashad. Arzesh faghat makhfi kardan-e type-e ORM az client ast.

**8. To Dejban UoW kodam class ast?**
`PersonnelsDbContext` (va hamta-ye har module) ke `IUnitOfWork` ra implement karde. Handler interface ra mibinad.

**9. Chera scoped?**
Ta marz-e UoW barabar-e marz-e request bashad. Singleton haman shekast-e "omr-e process" ast.

**10. Do module ra chetor yek commit mikoni?**
Ba in UoW nemikoni. Har kodam tracker-e khod ra darad. Hamahangi-e beyn-eshan outbox ast, ya'ni eventual, na atomic-e distributed.
