# 02 — Unit of Work

*Chand taghir ra yek transaction kon. Ya hame commit, ya hich.*

---

## Ye khat

Unit of Work list-e kar-haye anjam-shode ra negah midarad va **yek bar** an-ha ra mianavardad. To EF, khod-e `DbContext` hamin ast: change tracker + `SaveChanges`.

## Moshkel

```
personnelRepository.Insert(personnel);   // age inja save shavad
documentRepository.Insert(document);     // va inja exception
```

Personnel neveshte shode, document na. Domain shekaste. UoW har do ra track mikonad va yek `SaveChanges` an-ha ra to yek transaction-e database minevisad.

## Sherkat-konande-ha

`IUnitOfWork` to application-e har module. Mesal-e Personnels:

```csharp
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    EntityEntry<TEntity> Entry<TEntity>(TEntity entity) where TEntity : class;
}
```

Implementation class-e joda nist. Khod-e context an ra implement mikonad:

```csharp
public sealed class PersonnelsDbContext(...)
    : DbContext(options), IUnitOfWork, ITenantDbContext
```

Va DI an ra be interface vasl mikonad (`PersonnelsModule`):

```csharp
services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<PersonnelsDbContext>());
```

Handler `PersonnelsDbContext` ra nemibinad. `IUnitOfWork` ra mibinad.

## Chera `Entry` roye interface ast?

Handler-ha gavahi mikhahand graph-e tracked ra taghir bedahand (masalan relation ke EF khodesh kashf nemikonad) bedune inke type-e context leak shavad. In yek sakhesh-e amali ast. To mosahebe begou: "UoW-e khales faghat `SaveChanges` ast; `Entry` ra gozashtim ta application be `DbContext` cast nazanad."

## Lifetime

`DbContext` **scoped** ast: yek request, yek context, yek tracker. Do request tracker-e moshtarak nadarand. Singleton kardan-e context khatar-e race va memory leak ast — in ra joda yad begir, chon so'al-e tekrar-shode-ye .NET ast.

## Flow-e dorost

```
1. repository.GetAsync     → entity tracked mishavad
2. entity.SoftDelete(...)  → state-e memory + domain event to list
3. repository.Insert(...)  → faghat agar jadid ast
4. unitOfWork.SaveChangesAsync
     → SQL-e hame-ye entity-haye tracked
     → yek transaction
     → bad az commit, event-ha baraye outbox jam mishavand
```

Age qabl az 4 exception biayad, database taghir nakarde. Memory-e in request ham ba tamom shodan-e scope dor mirizad.

## Domain event va UoW

`Entity.Raise` event ra **faqat to memory** mirizad (`_domainEvents`). Ta `SaveChanges` call nashavad, kasi an event ra paydar nakarde. In gharardad-e in codebase ast: event-e domain ba commit-e aggregate mimiravad, na zudtar. Joz'iat-e outbox to ketabche-ye 12 ast.

## Key UoW-e dasti nanevis

Age yek `DbContext` dari, neveshtan-e class-e `UnitOfWork` ke faghat `SaveChanges` ra forward konad arzesh-e kami darad. In stack haman context ra `IUnitOfWork` karde ta handler be EF type vaghe'i nashavad. An yek interface-e nazok ast, na yek UoW-e dovom.

UoW-e vaghe'an joda vaghti lazem ast ke **chand** persistence (do context, ya SQL + file) ra yek transaction koni. Inja har module yek context darad. Transaction-e beyn-e module-ha ba outbox hal shode, na ba yek UoW-e bozorg.

## Farq ba Repository

Repository migooyad **che** objecti ra mikhahi. UoW migooyad **key** hame paydar shavad. Handler har do ra mikhahi. Yeki jaye digari nist.

## Script-e 60 sanie

> "`PersonnelsDbContext` ham `DbContext` ast ham `IUnitOfWork`. Handler faghat interface ra mibinad va dar enteha yek `SaveChangesAsync` mizanad. Change tracker hame-ye aggregate-haye in request ra yek transaction mikonad. Event-e domain ta hamin commit to memory mimanad. Context scoped ast, pas request-ha tracker ra share nemikonand. Beyn-e module-ha UoW-e moshtarak nasakhtim; anja outbox darim."

---

## 10 soal

**1. UoW daghighan chi negah midarad?**
Majmoo'e-ye entity-haye tracked va vaziat-e an-ha (Added/Modified/Deleted) ta yek commit.

**2. Chera `SaveChanges` dakhel-e repository nist?**
Chon yek use-case mitavanad chand repository ra taghir dahad. Save-e zud, transaction ra tekke mikonad.

**3. `DbContext` khodesh UoW nist?**
Hast. Ma class-e dovom nasakhtim. Faqat an ra az interface export kardim ta application be type-e EF vast nashavad.

**4. Age `SaveChanges` exception bedahad chi?**
Transaction rollback mishavad. Event-e domain ham age ba hamin save paydar shavad, publish nemishavad. In haman dalil-e outbox ast.

**5. Chera scoped, na singleton?**
Context thread-safe nist va tracker roshd mikonad. Yek request yek tracker. Singleton = race + data-e request-e ghabli.

**6. Do module, do context. Yek transaction?**
Na, bedune distributed transaction. Har module UoW-e khod ra commit mikonad. Hamahangi-e beyn-e an-ha integration event + outbox/inbox ast.

**7. `Entry<T>` inja che mikonad?**
Dastresi-e kontorol-shode be change tracker bedune cast be `DbContext`. Joz'-e pattern-e klasik nist; joz'-e API-e in proje ast.

**8. Chand `SaveChanges` to yek handler?**
Gahi baraye gereftan-e id ghabl az ghadam-e ba'd lazem mishavad. Har call yek transaction-e joda ast. Age har do bayad atomik bashand, bayad yek save bashand ya transaction-e explicit.

**9. UoW va `TransactionScope`?**
`SaveChanges` khodesh transaction baz mikonad. `TransactionScope` / distributed transaction inja gharardad nist. Scale va Postgres an ra zesht mikonand.

**10. Chetor test mikoni ke commit yek bar ast?**
Fake-e `IUnitOfWork` beshmar `SaveChangesAsync` chand bar seda shode, va repository-e fake ta qabl az an chizi naneveshte bashad. Test-e transaction-e vaghe'i integration ast: exception-e amdi va ba'd assert ke row nist.
