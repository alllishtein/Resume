# 03 — Mediator (MediatR)

*Sender nemidanad ki javab midahad. Yek vasete in ra mifahmad.*

---

## Ye khat

Mediator ertebat-e mostaghim-e chand object ra hazf mikonad. Hame be yek vasete sohbat mikonand. Inja vasete **MediatR** ast va payam `ICommand` / `IQuery` ast.

## Moshkel bedune mediator

Endpoint bayad handler ra beshnasad, handler bayad validator ra seda bezanad, va har endpoint log va exception-e khod ra copy konad. Ba 8 module, in web-e dependency ast: Presentation → hame-ye handler-ha.

Ba mediator:

```
Endpoint  --Send(command)-->  ISender  -->  yek handler
```

Endpoint type-e handler ra dar project-ash reference-e mostaghim baraye call nemikhad. MediatR ba assembly scan an ra peyda mikonad (`AddMediatR` + `RegisterServicesFromAssemblies`).

## Gharardad-e in codebase

```csharp
public interface ICommand<TResponse> : IRequest<ErrorOr<TResponse>>, IBaseCommand;
public interface IQuery<TResponse> : IRequest<ErrorOr<TResponse>>;

public interface ICommandHandler<in TCommand, TResponse>
    : IRequestHandler<TCommand, ErrorOr<TResponse>>;

public interface IQueryHandler<in TQuery, TResponse>
    : IRequestHandler<TQuery, ErrorOr<TResponse>>;
```

`IRequest<T>` mal-e MediatR ast. `ICommand` / `IQuery` mal-e ma ast ta kas command ra be jaye query register nakonad va ta behavior-e validation faghat roye command benshinad (`IBaseCommand`).

Yek request **yek** handler darad. In ra ba event eshtebah nagir: event mitavanad chand handler dashte bashad (ketabche-ye Observer).

## Flow

```
IEndpoint.MapEndpoint
  → ISender.Send(new CreateXCommand(...))
      → ExceptionHandlingPipelineBehavior
      → RequestLoggingPipelineBehavior
      → ValidationPipelineBehavior     // faghat agar TRequest : IBaseCommand
      → XCommandHandler.Handle
  → ErrorOr<T> bar migardad
  → endpoint Match mikonad: Ok ya ProblemDetails
```

Sabt-e zanjir inja ast:

`Microservices/Dejban/Common/Dejban.Common.Application/ApplicationConfiguration.cs`

Avalin `AddOpenBehavior` **biruni-tarin** halqe ast. Pas exception dor-e log, log dor-e validation, validation dor-e handler.

## Mediator che chizi nist

- Bus-e beyn-e process nist. `Send` haman process, haman request, await mishavad.
- Event-e RabbitMQ nist. An integration event ast va az outbox birun miravad.
- "Hame chi ra mediator kon" nist. Call-e dakheli-e do class-e yek aggregate mediator nemikhahad.

## Hazine

- Call stack deraz-tar va debug yek hop sakht-tar.
- Handler-ha ba reflection peyda mishavand. Age do handler baraye yek request sabt shavad, runtime mifahme, compile na.
- Baraye yek CRUD-e koochak, `controller` → `service` sade-tar ast. In stack an ra pazirofte chon pipeline (validation, log, exception) va yeksan budan-e 8 module arzeshesh ra darad.

## Farq ba Observer

| | Mediator `Send` | Domain event |
|---|---|---|
| Chand girande | yek | chand |
| Sender montazer-e natije | bale (`ErrorOr<T>`) | na (raise va boro) |
| Kei | yek use-case | "ye chiz etefagh oftad" |

## Script-e 60 sanie

> "Endpoint-ha `ISender.Send` mikonand va handler ra be esm nemishenasand. MediatR az assembly-e module-ha yek handler baraye har `IRequest` peyda mikonad. Ma `ICommand` va `IQuery` ra roye `IRequest` gozashtim ta write va read joda bashand va `ErrorOr` bargardad. Behavior-ha — exception, log, validation — dor-e handler micharkhand bedune inke handler an-ha ra seda bezanad. In in-process ast. Beyn-e service-ha MassTransit ast, na `Send`."

---

## 10 soal

**1. Mediator che coupling-i ra miborrad?**
Sender digar be concrete handler, va handler digar be sender, reference-e compile-time baraye seda zadan nadarad.

**2. Chand handler baraye yek command?**
Yek. Age do ta sabt koni MediatR exception midahad. Chand shenavande = event, na `Send`.

**3. `ICommand` chera mostaghim `IRequest` nist faqat?**
Ta constraint-e validation (`IBaseCommand`) va return-e `ErrorOr` ejbari bashad, va query eshtebahan az pipeline-e command rad nashavad.

**4. Tartib-e behavior-ha ra che kas moshakhas mikonad?**
Tartib-e `AddOpenBehavior`. Avali biruni-tarin ast: Exception → Logging → Validation → Handler.

**5. Handler scoped ast ya singleton?**
Handler-ha ba DbContext scoped hastand. MediatR an-ha ra per request misazad. Singleton handler ke context inject konad bug ast.

**6. Mitavanam az handler-e A, handler-e B ra `Send` konam?**
Teknikally bale. Shekastan-e boundary ast: transaction, validation-e dobare, va cycle. Use-case bayad khodesh orchestrate konad ya event bezanad.

**7. Performance-e reflection?**
Resolve-e handler yek bar to startup/cache ast, na har bar parse-e string. Hazine-ye asli I/O ast, na MediatR. An ra bottleneck seda nazan ta profile karde bashi.

**8. MediatR va MassTransit farq?**
`Send` in-process, synchronous az nazar-e caller, yek handler. MassTransit process-e digar, queue, retry, chand consumer.

**9. Age mediator nabashad chi mishe?**
Bayad khodet interface-e handler ra inject koni. Baraye yek service kafi ast. Arzesh-e inja pipeline-e yeknavakht va nabudan-e reference az endpoint be handler-e concrete ast.

**10. Chetor debug mikoni ke handler-e ghalat ejra shode?**
Log-e `RequestLoggingPipelineBehavior` esm-e `TRequest` ra darad. Stack, handler-e haman namespace ra neshan midahad. Test: `Send` ba yek command va assert-e `ErrorOr`.
