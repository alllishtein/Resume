# 01 — Repository

*Domain nemidanad data kojast. Faghat ye contract miporsad.*

---

## Ye khat

Repository ye collection-e in-memory ra **taghlid** mikonad. Handler `GetAsync` / `Insert` seda mizanad. EF, SQL, schema, `DbSet` posht-e interface mimanan.

## Moshkel

Age `CreatePersonnelCommandHandler` mostaghim `PersonnelsDbContext.Personnels` ra bebine:

- domain be EF vasl mishavad (test bedune database sakht mishavad)
- query-e `Include` va soft-delete to dah handler copy mishavad
- avaz kardan-e storage hame-ye application ra mikeshad

## Sherkat-konande-ha

| Naghsh | Inja |
|---|---|
| Contract | `IPersonnelRepository` to Domain |
| Implementation | class-e infrastructure ke `PersonnelsDbContext` ra migirad |
| Client | command/query handler |
| Chizi ke repository **nist** | transaction. An `IUnitOfWork` ast |

Path:

`Microservices/Dejban/Modules/Personnels/Dejban.Modules.Personnels.Domain/Personnels/IPersonnelRepository.cs`

```csharp
public interface IPersonnelRepository
{
    Task<Personnel?> GetAsync(Guid id, CancellationToken cancellationToken = default);
    Task<Personnel?> GetWithDocumentsAsync(Guid id, CancellationToken cancellationToken = default);
    void Insert(Personnel personnel);
    void InsertDocument(PersonnelDocument document);
    void RemoveDocument(PersonnelDocument document);
}
```

Noghte-haye mosahebe:

- Interface to **Domain** ast, implementation to **Infrastructure**. Application faghat interface ra inject mikonad. In haman Dependency Inversion ast.
- Method-ha zaban-e business-and: `GetWithDocumentsAsync`, `SoftDeleteByUnitIdAsync`. Na `ExecuteSql`.
- `Insert` track mikonad. Save nemikonad. Commit kar-e Unit of Work ast.
- Repository **module-specific** ast. Yek `IRepository<T>` generic to in stack gharardad nist. Interview-er age beporsad "chera generic nist?": chunk-e method-ha (`GetWithDocuments`, soft-delete bar asas unit) to generic ja nemigirand, va generic repository zood be `IQueryable` leak tabdil mishavad.

## `IQueryable` roye interface

`GetQueryable()` roye hamin interface hast. In ye bazgasht-e amdan-i ast: list-ha filter/sort/page mikhahand va projection to application mimimand.

In ra to mosahebe **khodet** begou, montazer-e surprise nabash:

> "Read side sometimes exposes IQueryable so paging stays in one place. The write side still goes through aggregate methods. I would not let a controller compose that IQueryable."

Kasi ke begouyad "repository hichvaght IQueryable nemidahad" dar in codebase dorost nist. Kasi ke begouyad "pas repository bi-mani ast" ham tond rafte: write path hanuz az EF joda ast.

## Flow

```
Handler
  → IPersonnelRepository.GetAsync(id)
      → Infrastructure: DbSet + filter (tenant, soft delete, include)
  → personnel.SoftDelete(...)     // ghanun to entity
  → repository.Insert(...)        // faghat track, age jadid bashad
  → IUnitOfWork.SaveChangesAsync  // inja commit
```

## Key estefade nakon

- CRUD-e 4 khati ke hich ghanun-e aggregate nadarad va faghat EF mikhahi: repository-e nazok faghat ye layer-e ezafe ast. EF khodesh repository + UoW ast. In stack **balad** entekhab karde chon test va boundary-e module mohem ast. Begou entekhab ra, na inke "hamishe lazem ast".
- Repository-e "god" ke 40 method-e report darad. Report miravad query handler / Dapper / read model, na to repository-e aggregate.

## Farq

| | Repository | Unit of Work | DAO |
|---|---|---|---|
| Mas'uliat | peyda kardan va track-e aggregate | commit-e hame-ye taghir-e in context | row/SQL |
| Zaban | `GetWithDocuments` | `SaveChangesAsync` | `SELECT ...` |
| Transaction | na | bale | shayad |

## Script-e 60 sanie

> "Har module ye repository-e khodesh darad, masalan `IPersonnelRepository` to domain-e Personnels. Handler aggregate ra migirad, method-e entity ghanun ra ejra mikonad, va `Insert` faghat object ra track mikonad. `PersonnelsDbContext` posht-e interface ast va hamzaman `IUnitOfWork` ast, pas save yek ja etefagh mioftad. Repository generic nist chon method-ha domain-specific-and. Roye read, `GetQueryable` ra baz gozashtim ta pagination to application bemanad; controller an ra compose nemikonad."

---

## 10 soal

**1. Repository che moshkeli ra hal mikonad?**
Joda kardan-e zaban-e domain az joziat-e persistence. Client collection mibine, na SQL.

**2. Chera inja generic `IRepository<T>` nist?**
Method-ha yek shape nadarand: `GetWithDocumentsAsync`, soft-delete bar asas site/unit. Generic ya leak-e `IQueryable` mishavad ya method-e bi-mani tolid mikonad.

**3. `Insert` chera `Save` nist?**
Chand aggregate shayad to yek request avaz shavand. Commit bayad yek transaction bashad. An kar-e `IUnitOfWork.SaveChangesAsync` ast.

**4. Interface ra koja migozari va chera?**
To Domain. Infrastructure be Domain reference midahad, baraks na. Handler be interface vaghe'i (DIP) vast mishavad.

**5. EF ke khodesh repository ast. Pas in layer ezafe nist?**
Baraye CRUD-e sade mitavanad ezafe bashad. Inja arzeshesh boundary-e test va in ast ke ghanun-e load (`Include`, tenant, soft delete) yek ja bashad. An ra "hamishe" seda nazan.

**6. `GetQueryable` naghz-e pattern nist?**
Sath-e write ra nashkaste. Sath-e read ra baz karde. Risk: agar UI ya controller an `IQueryable` ra begirad, persistence leak mishavad. Bayad to application bimand.

**7. Repository transaction mishavad?**
Na. Age do repository to yek `DbContext` bashand, UoW an do ra yekja commit mikonad. Repository-e joda transaction-e joda nist.

**8. Soft delete koja bashad: repository ya entity?**
Ghanun (event, `DeletedAt`, idempotent budan) to entity. Query-e "hazf-shode-ha naya" mitavanad to repository bashad ta hame-ye read-ha yek filter dashte bashand.

**9. Chetor test mikoni?**
Handler ra ba fake-e `IPersonnelRepository` test kon. Test-e khod-e repository ba database-e vaghe'i (integration) ast, chon arzeshesh haman SQL/Include ast.

**10. Repository va cache?**
Cache posht-e haman interface mishe (decorator). Client nabayad bedanad ke natije az Redis amade ya az Postgres. In stack cache ra aksaran jaye digar (HybridCache) mizanad, na dakhel-e har repository.
