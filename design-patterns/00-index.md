# Design Patterns — fehrest

*Ketabche-haye joda. Har file yek pattern. ACL nist.*

---

## Chetor bekhan

Har ketabche khodesh kafi-e. Tartib-e pa'in az zireen (data) be bala (UI) mire.

Baraye har pattern in chahar jomle ra boland begou:

1. **Intent** — in pattern che moshkeli ra hal mikonad.
2. **Structure** — ki ki ra seda mizanad, va ki ra **nemi**shenasad.
3. **Dejban** — yek file-e vaghe'i.
4. **Tradeoff** — koja nazanash, chon interview-er hamin ra miporsad.

Strategy-e device sync (`IDeviceSyncStrategy`) faghat to ACL ast. In series an ra nadarad.

## Backend (Dejban, bedune ACL)

| # | File | Pattern | Yek jomle |
|---|---|---|---|
| 01 | [repository](./01-repository.md) | Repository | Domain `DbContext` ra nemibinad |
| 02 | [unit-of-work](./02-unit-of-work.md) | Unit of Work | Chand taghir, yek commit |
| 03 | [mediator](./03-mediator.md) | Mediator | Endpoint handler ra nemishnasad |
| 04 | [cqrs](./04-cqrs.md) | CQRS | Write va read do contract |
| 05 | [chain-of-responsibility](./05-chain-of-responsibility.md) | Chain of Responsibility | Validation/log birun-e handler |
| 06 | [decorator](./06-decorator.md) | Decorator | Idempotency bedune dast zadan be handler |
| 07 | [factory](./07-factory.md) | Factory | Sakhtan-e object yek ja, ba ghanun |
| 08 | [observer](./08-observer.md) | Observer | Entity event raise mikonad, handler-ha loosely coupled |
| 09 | [options](./09-options.md) | Options | Config type-safe, na string-e part |
| 10 | [template-method](./10-template-method.md) | Template Method | Skeleton to base, ghadam-e akhar to subclass |
| 11 | [result](./11-result.md) | Result | Khataye business exception nist |
| 12 | [outbox](./12-outbox.md) | Transactional Outbox | Save va publish yek transaction |
| 13 | [inbox](./13-inbox.md) | Inbox | Event-e tekrar-shode yek bar process mishavad |

## Frontend

| # | File | Pattern | Yek jomle |
|---|---|---|---|
| 14 | [provider-context](./14-provider-context.md) | Provider / Context | Dependency-e moshtarak bedune prop drilling |
| 15 | [guard](./15-guard.md) | Guard / Protection Proxy | Login joda az permission-e safhe |
| 16 | [interceptor](./16-interceptor.md) | Chain + Single Flight | Har request token/site/refresh ra khodesh midanad |
| 17 | [query-key-factory](./17-query-key-factory.md) | Factory (cache key) | Hoviat-e cache yek tabe' |
| 18 | [facade](./18-facade.md) | Facade | UI axios ra nemibinad |
| 19 | [adapter](./19-adapter.md) | Adapter | Shekl-e bigane ra be shekl-e khodi tabdil kon |
| 20 | [zustand-observer](./20-zustand-observer.md) | Observer (store) | Subscriber-ha az taghir-e site khabar mishavand |

## In-ha ra to resume nagou (to in codebase nistan)

- **Strategy** — faghat ACL (device brand). In series amdan nadarad.
- **Abstract Factory, Visitor, Flyweight, Bridge** — nist.
- **Specification** (Ardalis) — query-ha LINQ-e mostaghim-and.
- **State** be shekl-e class-e joda — status bishtar field ast, na state object.
- **Singleton dasti** — DI `AddSingleton` an ra mikonad. Class-e `lock` + `Instance` nanevis.
