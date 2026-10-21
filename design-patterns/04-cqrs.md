# 04 — CQRS

*Write model va read model yek shape nistand. Majbur nistand yek database ham bashand.*

---

## Ye khat

Command Query Responsibility Segregation: method ya path-i ke **system ra avaz mikonad** az path-i ke **faghat mikhanad** joda ast. Sath-e kam: do interface. Sath-e boland: do model, do store.

## Sath-ha — in ra ghalt jam nakon

| Sath | Mani | Dejban |
|---|---|---|
| Method (CQS, Meyer) | command `void`/natije, query side-effect nadarad | `ICommand` vs `IQuery` |
| Model | write = aggregate, read = DTO | handler-e command entity ra load mikonad; query DTO bar migardanad |
| Store | write DB joda az read DB | hame-ye module-ha in nistand. Reporting read-model darad |

Interview-er "CQRS dari?" — javab-e daghigh:

> "Command va query joda register mishavand va query aggregate ra bar nemigardanad. Read replica-ye joda baraye har module nasakhtim. Ja'i ke list sangin ast, read model / reporting darim."

Na "bale, CQRS-e kamel ba event sourcing". Event sourcing inja **nist**.

## Code

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;
```

Fargh-e amali:

- Command: `ValidationPipelineBehavior` roye `IBaseCommand` fa'al ast. Query az an constraint rad nemishavad, pas validator-e FluentValidation-e command roye query nist.
- Command aggregate load mikonad, method-e entity, `SaveChanges`.
- Query `IQueryable` / projection / Dapper. Entity-e kamel ba hame-ye navigation lazem nist.

Har do `ErrorOr<T>` bar migardanand. "Query side-effect nadarad" yani data ra avaz nemikonad. Log va metric side-effect-e infra hastand, na shekastan-e CQRS.

## Chera joda

- Write bayad invariant-e aggregate ra hefz konad. Read bayad sari' va flat bashad (grid, filter, pagination). Yek model har do ra bad anjam midahad.
- Mitavani read ra scale koni bedune inke write model ra denormalize koni.
- Permission mitavanad farq dashte bashad: kasi list mibine, kasi create mikonad.

## Hazine ke bayad begouyi

- Do model = do jaye taghir. Field-e jadid shayad ham command, ham DTO, ham query ra begirad.
- Age read az write aghab biyaftad (read model-e joda), UI bayad eventual consistency ra tahammol konad.
- Baraye form-e 3 field, do stack ezafe ast. Arzesh vaghti list va ghanun-e write har do jadidi hastand.

## Reporting

Read-model-e reporting projection ast: data-e neveshte-shode yek bar digar be shekl-e gozaresh zakhire mishavad. An CQRS-e sath-e store ast, na "har query CQRS-e kamel". Ketabche-ye stack: `day-64`.

## Script-e 60 sanie

> "CQRS-e ma avval contract ast: `ICommand` va `IQuery`, har do `ErrorOr`, vali validation-e pipeline faghat roye command. Command aggregate va invariant ra mibinad. Query DTO-e flat baraye grid. Event sourcing nadarim. Ja'i mesl-e reporting ke read sangin ast model-e joda darim va an eventual consistent ast. Baghi-e module-ha haman database ra mikhanand, faghat path-e code joda ast."

---

## 10 soal

**1. CQRS va CQS farq?**
CQS ghanun-e method ast: query side-effect nadarad. CQRS haman ra ta model va shayad ta store joda mikonad.

**2. Hame-ye query bayad database-e digar bashad?**
Na. Joda'i-e code bedune joda'i-e database ham CQRS ast. Store-e joda vaghti scale ya shekl-e read fargh-e jadidi darad.

**3. Chera query `ErrorOr` bar migardanad age side-effect nadarad?**
Not found va validation-e vorudi khataye business-and, exception nistand. Side-effect-e data nist.

**4. Command mitavanad data bar gardanad?**
Inja bale: `ErrorOr<Guid>` baraye id-e sakht-shode. Purist-ha command ra void mikhahand. Bargasht-e id amali va ghanuni ast; bargasht-e graph-e kamel-e UI shoru'-e shekastan-e joda'i ast.

**5. Event sourcing lazem-e CQRS ast?**
Na. CQRS bedune event sourcing rayej ast. Event sourcing bedune CQRS ham momken ast vali kam. Ma event-e domain darim, event sourcing na.

**6. Eventual consistency ra chetor to UI migi?**
Bad az command, ya haman response dade-ye kafi midahad, ya client query ra invalidate mikonad. Age read model aghab bashad, bayad an ra be onvan-e delay-e ma'lum bepaziri, na bug-e random.

**7. Update-e hamzaman?**
Do command roye yek aggregate bayad ba concurrency token ya version-e row hal shavand. CQRS an ra hal nemikonad. UoW va database an ra hal mikonand.

**8. Query mitavanad `SaveChanges` bezanad?**
Nabayad. Age audit-e "did" mikhahi, an yek command-e joda ast, na ghalat-e `GetById`.

**9. Mapster in vasat chi mikonad?**
Projection-e entity/DTO. Pattern-e joda nist; abzar-e joda kardan-e shape-e read az shape-e write ast. `day-60`.

**10. Kaj shode CQRS ra chetor mifahmi?**
Query i ke status ra update mikonad, ya command i ke 15 include baraye ye form-e grid load mikonad. Avali side-effect-e makhfi, dovomi model-e ghalat.
