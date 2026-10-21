# Design Patterns — fehrest

Har file yek pattern. ACL nist.

## Chetor bekhan

Har ketabche do bakhsh darad. Tartib ra avaz nakon.

1. **Aval khode pattern.** Ba ye mesal-e sade shoru mishavad. Esm-e file-e Dejban inja nist. Agar in bakhsh ra ba zaban-e khodet nagoi, bakhsh-e dovom ra nakhan.
2. **Bad Dejban ya front.** Haman ide ra ru ye code-e vaghe'i neshan midahad.

Akhar-e har file dah so'al-e mosahebe ast, ba javab-e kutah.

In chahar jomle ra baraye har pattern balad bash:

1. Che moshkeli ra hal mikonad.
2. Ki ki ra nemishnasad.
3. Ba kodam pattern-e nazdik ghalt mishavad.
4. Koja estefade kardane-ash zarar darad.

Jomle-ye panjom, bad az in-ha: "to Dejban inja neshaste."

Strategy-e device sync faghat to ACL ast va inja nist.

## Backend

| | File | Pattern |
|---|---|---|
| 01 | [repository](./01-repository.md) | Repository |
| 02 | [unit-of-work](./02-unit-of-work.md) | Unit of Work |
| 03 | [mediator](./03-mediator.md) | Mediator |
| 04 | [cqrs](./04-cqrs.md) | CQRS |
| 05 | [chain-of-responsibility](./05-chain-of-responsibility.md) | Chain of Responsibility |
| 06 | [decorator](./06-decorator.md) | Decorator |
| 07 | [factory](./07-factory.md) | Factory |
| 08 | [observer](./08-observer.md) | Observer |
| 09 | [options](./09-options.md) | Options |
| 10 | [template-method](./10-template-method.md) | Template Method |
| 11 | [result](./11-result.md) | Result |
| 12 | [outbox](./12-outbox.md) | Outbox |
| 13 | [inbox](./13-inbox.md) | Inbox |

## Front

| | File | Pattern |
|---|---|---|
| 14 | [provider-context](./14-provider-context.md) | Context |
| 15 | [guard](./15-guard.md) | Guard |
| 16 | [interceptor](./16-interceptor.md) | Interceptor |
| 17 | [query-key-factory](./17-query-key-factory.md) | Kelid-e cache |
| 18 | [facade](./18-facade.md) | Facade |
| 19 | [adapter](./19-adapter.md) | Adapter |
| 20 | [zustand-observer](./20-zustand-observer.md) | Store |

## In-ha ra be esm-e pattern-e hamin proje nagou

- Strategy faghat to ACL ast.
- Abstract Factory va Visitor va Flyweight va Bridge inja nistan.
- Specification be shekl-e library inja nist.
- State be shekl-e class-e joda inja nist. Vaziat aksaran ye field ast.
- Singleton-e dasti neminevisim. Khode DI ba `AddSingleton` in kar ra mikonad.
