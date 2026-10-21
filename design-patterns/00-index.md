# Design Patterns — fehrest

*Har file yek pattern. ACL nist.*

---

## Gharardad-e khundan

Har ketabche **do bakhsh** darad. Tartib ra be-ham nazan.

1. **Bakhsh-e avval — khode pattern.** Moshkel, ta'rif, sherkat-konande-ha, sakhtar, ghanun, anva', mesal-e sade-ye donya, farq ba pattern-haye nazdik, koja bezan va koja nazan. Inja **hich file-e Dejban** nist. Ta in bakhsh ra boland natavan goft, bakhsh-e dovom ra nakhan.
2. **Bakhsh-e dovom — neshoon-e code.** Haman mafhoom roye code-e Dejban ya front pin mishavad: ki naghsh-e Subject ast, ki Decorator, chi az ketab kamel nist.

Akhar-e har file: script-e mosahebe, ba'd 10 soal. So'al-haye aval mafhoom-and. So'al-haye akhar "in ra to code kojast".

Chahar jomle-i ke bayad **bad az bakhsh-e avval** balad bashi, ghabl az inke esm-e file biayad:

1. In pattern che moshkeli ra hal mikonad.
2. Ki ki ra seda mizanad, va ki ra nemishnasad.
3. Ba kodam pattern eshtebah gerefte mishavad va farq-e daghigh chist.
4. Koja estefade-ash zian ast.

Ba'd, jomle-ye panjom: "to Dejban hamin neshaste inja."

Strategy-e device sync faghat to ACL ast. In series an ra nadarad.

## Backend

| # | File | Pattern |
|---|---|---|
| 01 | [repository](./01-repository.md) | Repository |
| 02 | [unit-of-work](./02-unit-of-work.md) | Unit of Work |
| 03 | [mediator](./03-mediator.md) | Mediator |
| 04 | [cqrs](./04-cqrs.md) | CQRS |
| 05 | [chain-of-responsibility](./05-chain-of-responsibility.md) | Chain of Responsibility |
| 06 | [decorator](./06-decorator.md) | Decorator |
| 07 | [factory](./07-factory.md) | Factory Method / Simple Factory |
| 08 | [observer](./08-observer.md) | Observer |
| 09 | [options](./09-options.md) | Options (ASP.NET, na GoF) |
| 10 | [template-method](./10-template-method.md) | Template Method |
| 11 | [result](./11-result.md) | Result / Railway |
| 12 | [outbox](./12-outbox.md) | Transactional Outbox |
| 13 | [inbox](./13-inbox.md) | Inbox / Idempotent Consumer |

## Frontend

| # | File | Pattern |
|---|---|---|
| 14 | [provider-context](./14-provider-context.md) | Provider / Context |
| 15 | [guard](./15-guard.md) | Protection Proxy / Guard |
| 16 | [interceptor](./16-interceptor.md) | Interceptor + Single Flight |
| 17 | [query-key-factory](./17-query-key-factory.md) | Cache identity / Key factory |
| 18 | [facade](./18-facade.md) | Facade |
| 19 | [adapter](./19-adapter.md) | Adapter |
| 20 | [zustand-observer](./20-zustand-observer.md) | Observer-e store |

## In-ha ra be onvan-e pattern-e in codebase nagou

- **Strategy** — faghat ACL.
- **Abstract Factory, Visitor, Flyweight, Bridge** — nist.
- **Specification** be shekl-e kitab — query-ha LINQ-e mostaghim-and.
- **State** be shekl-e class-e joda — status bishtar field ast.
- **Singleton dasti** — container ba `AddSingleton` an ra midahad.
