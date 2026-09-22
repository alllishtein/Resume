# Day 12 — DDD: Aggregate + Domain Event + Value Object

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

DDD (Domain-Driven Design) mige: **business logic bayad to Domain bashe**, na to Controller / Handler / Database. Entity-ha rich bashe (factory, invariant, event). Value Object identity nadare. Aggregate consistency boundary-e. Domain Event mige "chizi etefagh oftad." Dejban in tactical pattern-ha ra **partially** piade karde: `Entity` + `DomainEvent` + outbox hast; `AggregateRoot` / `ValueObject` base / Domain Service **nist**.

---

# BAKHSH-E AVAL: WORLD — DDD tactical to donya

## Chera DDD?

Bedune DDD, model-e anemic peida mishe:

```csharp
// ❌ Anemic model:
public class Order {
    public Guid Id { get; set; }           // public setter
    public OrderStatus Status { get; set; } // hamechi az birun set mishe
}

// Logic to handler:
order.Status = OrderStatus.Shipped;  // invariant? check nashode!
```

Ba DDD:

```csharp
// ✅ Rich model:
public class Order : Entity {
    public OrderStatus Status { get; private set; }

    public ErrorOr<Success> Ship() {
        if (Status != OrderStatus.Paid)
            return OrderErrors.CannotShipUnpaid;
        Status = OrderStatus.Shipped;
        Raise(new OrderShippedDomainEvent(Id));
        return Result.Success;
    }
}
```

**Maziat:** Business rule yek ja zendegi mikone. Handler thin mishe. Test-e domain bedune DB.

---

## Entity vs Value Object vs Aggregate

| | Entity | Value Object | Aggregate |
|---|---|---|---|
| **identity** | dare (Id) | nadare | cluster of entities |
| **equality** | by Id | by value (content) | by root Id |
| **mutable?** | bale (controlled) | ideally immutable | via root only |
| **mesal** | Personnel, Vehicle, Asset | VehiclePlate, Money, Address | Vehicle + Ownerships |

### Entity

```csharp
public abstract class Entity {
    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyCollection<IDomainEvent> DomainEvents => [.. _domainEvents];
    protected void Raise(IDomainEvent e) => _domainEvents.Add(e);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

**Gha'ede-ha:**
1. Private constructor (+ EF parameterless)
2. Private setters
3. Factory method (`Create` / `CreateAsync`)
4. Mutation via methods (`Update`, `Ship`, `Assign`)
5. Raise domain event ba'd az successful change

### Value Object

Identity nadare. Do ta `VehiclePlate` ba haman Value + Type → **equal**-an.

```csharp
public record Money(decimal Amount, string Currency)
{
    public static ErrorOr<Money> Create(decimal amount, string currency)
    {
        if (amount < 0) return MoneyErrors.Negative;
        if (string.IsNullOrWhiteSpace(currency)) return MoneyErrors.CurrencyRequired;
        return new Money(amount, currency.ToUpperInvariant());
    }

    public Money Add(Money other)
    {
        if (Currency != other.Currency) throw new InvalidOperationException("Currency mismatch");
        return this with { Amount = Amount + other.Amount };
    }
}
```

**Gha'ede-ha:**
1. Immutable (`init` / `record`)
2. Equality by value (record automatic)
3. Validation to factory
4. Behavior methods return **new** instance (na mutate)

**Common VOs:** Money, Address, Email, PhoneNumber, DateRange, Percentage, VehiclePlate.

### Aggregate + Aggregate Root

Aggregate = cluster of objects ke **ba ham** consistent hastand.

```
Vehicle (ROOT)
├── VehiclePlate (VO)
├── Ownerships[] (child entities)
└── Assignments[] (child entities)
```

**Rules of Aggregates (Evans / Vernon):**

1. **Reference by Id** — aggregate digar ra ba navigation nest, ba Id reference kon
2. **One transaction = one aggregate** — cross-aggregate → domain/integration event
3. **Small aggregates** — 1–3 entity, na 50
4. **Only root is public entry** — child-ha az birun `new` / modify **nashan**
5. **Invariants protected by root** — root check mikone ghabl az change

```csharp
public class Order : AggregateRoot  // entry point
{
    private readonly List<OrderLine> _lines = [];
    public IReadOnlyCollection<OrderLine> Lines => _lines.AsReadOnly();

    public ErrorOr<Success> AddLine(ProductId productId, int qty)
    {
        if (Status != OrderStatus.Draft)
            return OrderErrors.CannotModify;
        if (_lines.Count >= 100)
            return OrderErrors.TooManyLines;
        _lines.Add(OrderLine.Create(productId, qty));
        return Result.Success;
    }
}
```

---

## Domain Event

**Domain Event** = "chizi ke to domain etefagh oftade va digaran bayad bedunan."

```csharp
public sealed class OrderShippedDomainEvent(Guid orderId) : DomainEvent
{
    public Guid OrderId { get; } = orderId;
}
```

**Chera?**
- Decouple: Order nadone Inventory / Shipping / Email
- Audit trail
- Eventual consistency beyn-e aggregates / modules

**Domain Event vs Integration Event:**

| | Domain Event | Integration Event |
|---|---|---|
| scope | dakhel-e yek bounded context | beyn-e contexts / services |
| transport | in-process / outbox | message bus (RabbitMQ) |
| audience | same module handlers | other modules / services |
| Dejban | `PersonnelCreatedDomainEvent` | `PersonnelCreated` (Common.EventBus) |

**Flow-e standard:**

```
Entity.Raise(domainEvent)
  → SaveChanges (same transaction)
  → Outbox table
  → Background job
  → DomainEventHandler
  → (optional) Publish IntegrationEvent
```

---

## Domain Service

Logic ke be **yek** entity belong **nakone**:

```csharp
public class TransferService  // domain service
{
    public ErrorOr<Success> Transfer(Account from, Account to, Money amount)
    {
        var debit = from.Debit(amount);
        if (debit.IsError) return debit.Errors;
        return to.Credit(amount);
    }
}
```

Age logic faghat roye yek entity-e → method-e entity. Age cross-entity + domain rule → Domain Service.

---

## Specification Pattern

Query logic ra encapsulate kon:

```csharp
public class ActivePersonnelSpec : Specification<Personnel>
{
    public override Expression<Func<Personnel, bool>> ToExpression()
        => p => !p.IsDeleted && p.EmploymentStatus == EmploymentStatus.Active;
}
```

Reusable, composable, testable. Alternative: repository method per query.

---

## Anemic vs Rich Domain Model

| Anemic | Rich |
|---|---|
| Public setters | Private setters |
| Logic to service/handler | Logic to entity |
| `order.Status = Shipped` | `order.Ship()` |
| Easy CRUD | Protects invariants |
| IdentityServer / RequestTracker style | Vehicle / Asset style |

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **`AggregateRoot` base class** — Dejban faghat `Entity` dare
- **`ValueObject` base class** — Dejban ad-hoc `record`
- **Domain Service** — formal type nist
- **Specification pattern** — nist (Armory `Specification` = key/value data, na pattern)
- **Money / Address / Email VOs** — nist; national code string-e
- **Event sourcing** — state = events. Dejban CRUD + events
- **Always-valid model** (Vernon) — har mutation ErrorOr, hich invalid state
- **Ubiquitous Language enforcement** — architecture test partial
- **Cross-aggregate transaction ban** — convention, na hard rule

---

# BAKHSH-E DOVOM: DEJBAN — DDD to in proje

## Kernel: Entity + DomainEvent

```csharp
// File: Dejban.Common.Domain/Entity.cs

public abstract class Entity
{
    private readonly List<IDomainEvent> _domainEvents = [];

    protected Entity() { }

    public IReadOnlyCollection<IDomainEvent> DomainEvents => [.. _domainEvents];

    public void ClearDomainEvents() => _domainEvents.Clear();

    protected void Raise(IDomainEvent domainEvent)
        => _domainEvents.Add(domainEvent);
}
```

```csharp
// File: Dejban.Common.Domain/IDomainEvent.cs

public interface IDomainEvent
{
    Guid Id { get; }
    DateTime OccurredOnUtc { get; }
}
```

```csharp
// File: Dejban.Common.Domain/DomainEvent.cs

public abstract class DomainEvent : IDomainEvent
{
    protected DomainEvent()
    {
        Id = Guid.NewGuid();
        OccurredOnUtc = DateTime.UtcNow;
    }

    public Guid Id { get; init; }
    public DateTime OccurredOnUtc { get; init; }
}
```

**Na AggregateRoot:** har `Entity` mitone event raise kone. Consistency boundary = **convention**, na type system.

---

## Best aggregate: Vehicle

```csharp
// File: Vehicles.Domain/Vehicles/Vehicle.cs

public sealed class Vehicle : Entity
{
    private Vehicle() { }  // EF + encapsulation

    public Guid Id { get; private set; }
    public VehiclePlate VehiclePlate { get; private set; } = null!;
    public VehicleStatus Status { get; private set; }

    // True encapsulation — private list, public read-only
    private readonly List<VehicleOwnership> _ownerships = [];
    public IReadOnlyCollection<VehicleOwnership> Ownerships => _ownerships.AsReadOnly();
    public VehicleOwnership? ActiveOwnerShip
        => _ownerships.FirstOrDefault(x => x.IsActive);

    private readonly List<VehicleAssignment> _assignments = [];
    public IReadOnlyCollection<VehicleAssignment> Assignments => _assignments.AsReadOnly();

    // Factories by category
    public static ErrorOr<Vehicle> CreateStandard(VehicleCommonParams p) { /* ... */ }
    public static ErrorOr<Vehicle> CreateCargo(/* ... */) { /* ... */ }
    public static ErrorOr<Vehicle> CreateMotorcycle(VehicleCommonParams p) { /* ... */ }

    private static Vehicle CreateBase(/* ... */)
    {
        var vehicle = new Vehicle { /* ... */ };
        vehicle._ownerships.Add(VehicleOwnership.Create(/* ... */));
        vehicle.Raise(new VehicleCreatedDomainEvent(vehicle.Id));
        return vehicle;
    }
}
```

### Invariants roye Vehicle

```csharp
public ErrorOr<Success> UpdateStatus(VehicleStatus newStatus)
{
    if (Status == newStatus) return Result.Success;

    if (newStatus == VehicleStatus.Sold && Status != VehicleStatus.Active)
        return Error.Validation("Vehicle.InvalidStatusChange",
            "Only active vehicles can be marked as sold.");

    if (newStatus == VehicleStatus.Active && Status == VehicleStatus.Sold)
        return Error.Validation("Vehicle.CannotReactivateSold",
            "Sold vehicles cannot be reactivated.");

    Status = newStatus;
    return Result.Success;
}

public ErrorOr<VehicleOwnership> TransferOwnerShip(OwnerInfo newOwner, DateTime startDate)
{
    var current = ActiveOwnerShip;
    if (current is null)
        return Error.Validation("Ownership.NotFound",
            "Vehicle has no active ownership to transfer from.");

    current.Deactivate(startDate);
    var next = VehicleOwnership.Create(newOwner, startDate);
    _ownerships.Add(next);
    return next;
}
```

**In = real DDD:** mutation controlled, ErrorOr return, private collection, domain event on create.

---

## Best lifecycle aggregate: Asset (Armory)

```csharp
// File: Armory.Domain/Assets/Asset.cs

public sealed class Asset : Entity
{
    private Asset() { }

    public static ErrorOr<Asset> Create(
        Guid siteId, Guid assetDefinitionId, string serial,
        AssetStatus status, int quantity)
    {
        if (siteId == Guid.Empty)
            return AssetError.NotAllowToEmpty(nameof(siteId));
        // ...
        asset.Raise(new AssetCreatedDomainEvent(/* ... */));
        return asset;
    }

    public ErrorOr<Success> AssignTo(Guid personnelId, string fullName)
    {
        if (Status == AssetStatus.Assigned)
            return AssetError.AlreadyAssigned();
        if (Status == AssetStatus.Repairing)
            return AssetError.CannotAssignWhileRepairing();

        Status = AssetStatus.Assigned;
        return Result.Success;
    }

    public ErrorOr<Success> StartMaintenance(Guid maintenanceRecordId)
    {
        if (Status == AssetStatus.Repairing)
            return AssetError.AlreadyInRepair();
        if (Status == AssetStatus.Assigned)
            return AssetError.CannotRepairWhileAssigned();

        Status = AssetStatus.Repairing;
        Raise(new AssetMaintenanceStaredDomainEvent(Id, maintenanceRecordId));
        return Result.Success;
    }
}
```

**State machine to domain:** Assigned / Repairing / Available — rule-ha to entity, na handler.

---

## Softer aggregates: Personnel + Visitor

```csharp
// File: Personnels.Domain/Personnels/Personnel.cs

public sealed class Personnel : Entity, ISiteEntity, ISoftDeletable
{
    private Personnel() { }

    public Guid Id { get; private set; }
    public string FirstName { get; private set; } = null!;
    // private setters...

    // ⚠️ Public ICollection — softer encapsulation
    public ICollection<EmploymentHistory> EmploymentHistory { get; private set; } = [];
    public ICollection<PersonnelDocument> Documents { get; private set; } = [];

    public static async Task<Personnel> CreateAsync(/* ..., IACLUserIdGenerator gen */)
    {
        var personnel = new Personnel { /* ... */ };
        personnel.Raise(new PersonnelCreatedDomainEvent(personnel.Id));
        return personnel;  // plain Personnel, na ErrorOr<Personnel>
    }

    public PersonnelDocument AddDocument(/* ... */)
    {
        var document = PersonnelDocument.Create(/* ... */);
        Documents.Add(document);
        return document;
    }
}
```

```csharp
// File: Visitors.Domain/Visitors/Visitor.cs

public static async Task<Visitor> CreateAsync(/* ... */)
{
    var visitor = new Visitor { /* ... */ };
    visitor.Raise(new VisitorCreatedDomainEvent(visitor.Id));
    return visitor;
}

public void Update(/* ... */)
{
    if (/* nothing changed */) return;
    // mutate fields...
    Raise(new VisitorUpdatedDomainEvent(/* ... */));
}

public void Delete()
    => Raise(new VisitorDeletedDomainEvent(Id, ACLUserId));
```

**Fargh ba Vehicle:**
- Factory often returns `T`, na `ErrorOr<T>` (validation to FluentValidation)
- Collections `ICollection` public — EF-friendly, vali caller mitone `Documents.Add` bedune method
- Hanooz private ctor + private set + Raise → "rich-ish"

### VisitReservation — invariant ba throw

```csharp
// File: Visitors.Domain/Visitors/VisitReservation.cs

public void Update(/* ... */)
{
    if (!CanEdit)
        throw new InvalidOperationException(VisitReservationErrors.EditLocked.Code);
    // ...
}
```

**Smell:** mix-e ErrorOr va exception baraye invariant. Behtar: hame ErrorOr.

---

## Value Objects to Dejban

### VehiclePlate — best VO

```csharp
// File: Vehicles.Domain/Vehicles/VehiclePlate.cs

public record VehiclePlate
{
    public string Value { get; init; }
    public PlateType Type { get; init; }

    private VehiclePlate(string value, PlateType type)
    {
        Value = value;
        Type = type;
    }

    public static ErrorOr<VehiclePlate> CreatePlate(string number, PlateType type)
    {
        if (string.IsNullOrWhiteSpace(number))
            return VehicleErrors.NotAllowToEmpty("Plate");

        return type switch
        {
            PlateType.Standard => CreateStandard(number),
            PlateType.Motorcycle => CreateMotorcycle(number),
            PlateType.Internal => CreateInternal(number),
            PlateType.Diplomatic => CreateDiplomatic(number),
            _ => VehicleErrors.InvalidFormat("Plate")
        };
    }

    // CreateStandard: length + digit rules
    // CreateDiplomatic: letter + digit slicing
}
```

**EF:** `OwnsOne(v => v.VehiclePlate)` — VO embedded to parent table.

### OwnerInfo — VO-ish class

```csharp
// File: Vehicles.Domain/Vehicles/OwnerInfo.cs

// CreateOrganization / CreatePersonnel / CreatePersonnelForImport
// NationalCode must be 10 digits → ErrorOr<OwnerInfo>
```

### Thin records

```csharp
// CargoDetails, ConstructionDetails — category-specific details
// Companion on VisitSchedule:
public sealed record Companion(
    string FirstName, string LastName, string Gender,
    string? NationalCode, string? PhoneNumber, string? Photo = null);
```

### Chi VO nist

| concept | status |
|---|---|
| NationalCode | `string` on entity |
| Money | nist |
| Address | nist (fields flat) |
| Email / Phone | string + FluentValidation |

---

## Domain Events — catalog + Raise

### Mesal-ha

```csharp
public sealed class VisitorCreatedDomainEvent(Guid visitorId) : DomainEvent
{
    public Guid VisitorId { get; init; } = visitorId;
}

public sealed class PersonnelCreatedDomainEvent(Guid personnelId) : DomainEvent
{
    public Guid PersonnelId { get; init; } = personnelId;
}

public sealed class AssetCreatedDomainEvent(
    Guid assetId, Guid siteId, Guid assetDefinitionId, string? serialNumber)
    : DomainEvent { /* ... */ }

public sealed class VehicleCreatedDomainEvent(Guid vehicleId) : DomainEvent
{
    public Guid VehicleId { get; init; } = vehicleId;
}
```

### Module-haei ke domain event daran

| module | mesal |
|---|---|
| Personnels | Created / Updated / Deleted / Restored, Door* |
| Visitors | Visitor*, VisitSchedule*, VisitApproved |
| Vehicles | Vehicle*, Assignment*, MaintenanceCompleted |
| Armory | AssetCreated / Assigned / Returned / Maintenance* |
| SecurityPatrols | PatrolShift* |
| Inventory | TransferApproval* |
| CashLogistics | Vehicle* copies |

**Stub smell:** `GoodsReceiptCreatedDomainEvent` empty class — `: DomainEvent` nadare.

### Raise patterns

```csharp
// On create:
personnel.Raise(new PersonnelCreatedDomainEvent(personnel.Id));

// On update (only if changed):
Raise(new VisitorUpdatedDomainEvent(/* ... */));

// On soft delete:
Raise(new PersonnelDeletedDomainEvent(Id, deletedBy));

// On state transition:
Raise(new AssetMaintenanceStaredDomainEvent(Id, maintenanceRecordId));
```

---

## Outbox pipeline — az Raise ta handler

```csharp
// File: Dejban.Common.Application/Messaging/DomainEventHandler.cs

public abstract class DomainEventHandler<TDomainEvent> : IDomainEventHandler<TDomainEvent>
    where TDomainEvent : IDomainEvent
{
    public abstract Task Handle(TDomainEvent domainEvent, CancellationToken ct = default);

    public Task Handle(IDomainEvent domainEvent, CancellationToken ct = default)
        => Handle((TDomainEvent)domainEvent, ct);
}
```

```
1. Command handler:
   entity.Raise(event)
   repo.Insert(entity)
   await unitOfWork.SaveChangesAsync()

2. InsertOutboxMessagesInterceptor (same transaction):
   ChangeTracker → entity.DomainEvents
   → INSERT outbox_messages
   → entity.ClearDomainEvents()

3. Quartz ProcessOutboxJob:
   SELECT FOR UPDATE outbox rows
   → DomainEventHandlersFactory.Resolve(handlerType)
   → IdempotentDomainEventHandler wraps real handler
   → mark processed

4. Domain event handler (Application):
   await sender.Send(GetPersonnelQuery)
   await eventBus.PublishAsync(new PersonnelCreated(...))  // integration event
```

**Idempotent decorator (Scrutor):** duplicate outbox consumer → skip. (Day 40/41)

---

## Architecture tests — Visitors only

```csharp
// File: Visitors.ArchitectureTests/Domain/DomainTests.cs

// 1. DomainEvent types → sealed
// 2. DomainEvent types → name ends with "DomainEvent"
// 3. Entity types → private parameterless constructor
// 4. Entity types → only private constructors (no public)
```

**Smell:** faghat Visitors module. Personnels / Vehicles / Armory architecture test-e domain **nadaran**.

---

## Anemic contrast — RequestTracker + IdentityServer

### RequestTracker

```csharp
// Request — public setters, na Entity base
var request = command.Adapt<Request>();  // Mapster
request.Status = RequestStatusEnum.InProcess.ToString();
context.Requests.Add(request);

await publisher.Publish(new RequestCreatedDomainEvent(request.Id)); // MediatR INotification
await context.SaveChangesAsync(ct);
```

- "Domain event" = MediatR `INotification`, na `DomainEvent` base
- Publish **ghabl az** SaveChanges → outbox nist
- Logic to handler, entity thin

### IdentityServer

```csharp
public class ApplicationUser : IdentityUser
{
    // public setters — ASP.NET Identity style
}
```

Anemic + Identity framework. Site/Unit errors hastan vali rich aggregate nist.

---

## ErrorOr to domain — 3 style

| style | koja | mesal |
|---|---|---|
| **ErrorOr return** | Vehicle, Asset, VehiclePlate | `return AssetError.AlreadyAssigned()` |
| **throw** | VisitReservation, Asset quantity | `throw new InvalidOperationException` |
| **plain T + app validation** | Personnel, Visitor Create | FluentValidation → factory |

**Best practice (World):** always-valid + ErrorOr everywhere. Dejban mix.

```csharp
// File: Vehicles.Domain/Vehicles/VehicleErrors.cs

public static Error NotAllowToEmpty(string fieldName) =>
    Error.Validation("Vehicle.NotAllowToEmpty", $"خودرو باید دارای {fieldName} باشد");

public static Error InvalidFormat(string fieldName) =>
    Error.Validation("Vehicle.InvalidFormat", $"فرمت {fieldName} پلاک خودرو نامعتبر می‌باشد");
```

---

## Aggregate boundary reality check

| rule (World) | Dejban |
|---|---|
| AggregateRoot type | ❌ na |
| Private child collections | ✅ Vehicle, Asset / ⚠️ Personnel, Visitor |
| Reference other aggregate by Id | ✅ mostly (SiteId, not Site entity in write) |
| One tx = one aggregate | ✅ convention (handler saves one root) |
| Child only via root | ⚠️ children often own Id + separate repo access |
| Cross-module by event | ✅ integration events + read-model copy |

**Read-model copies (Day 10):** Visitors.Site ≠ Personnels.Site — same concept, different types. Bounded context!

---

## Smell-ha

1. **Na AggregateRoot** — hame Entity event raise mikonan
2. **Na ValueObject base** — consistency of equality/immutability weaker
3. **Na Domain Service** — cross-entity logic to handlers miravad
4. **Na Specification** — query logic scattered
5. **Personnel/Visitor soft encapsulation** — public `ICollection`
6. **Mix ErrorOr + throw + plain return** — 3 error styles
7. **Architecture tests faghat Visitors** — baghie module-ha unchecked
8. **GoodsReceiptCreatedDomainEvent stub** — incomplete
9. **RequestTracker MediatR notification ghabl az SaveChanges** — reliability gap
10. **IdentityServer anemic** — expected for Identity, vali contrast ba Dejban
11. **NationalCode string** — bayad VO bashe (checksum Day 07 frontend dare)
12. **Duplicate VehiclePlate** — Vehicles + CashLogistics copy

---

## 20 soal-e mosahebe

1. **Entity vs Value Object?** — Entity: Id. VO: equality by value, immutable
2. **Aggregate Root chie?** — Entry point + consistency boundary. Child-ha via root
3. **Chera private setter?** — Mutation controlled. Invariant protect
4. **Factory method?** — `Create` validates + constructs + raises event
5. **Domain Event chie?** — Something happened. Decouple side effects
6. **Domain vs Integration Event?** — Internal vs cross-boundary / bus
7. **Chera outbox?** — Event + entity same transaction. Reliable publish
8. **Anemic model chie?** — Data bag, logic outside. CRUD smell
9. **Always-valid model?** — Entity never invalid. Every mutate returns ErrorOr
10. **Reference by Id?** — Don't load other aggregate. Use Guid FK
11. **One tx = one aggregate?** — Avoid distributed lock. Events for the rest
12. **Domain Service kei?** — Logic spanning multiple entities, no natural home
13. **Specification?** — Encapsulated query predicate. Reusable
14. **Record as VO?** — Value equality + immutability for free
15. **OwnsOne?** — EF embeds VO columns in parent table
16. **Chera Dejban AggregateRoot nadare?** — Pragmatic. Entity enough for them. Trade-off
17. **Idempotent domain handler?** — Same event twice → skip. Outbox consumer table
18. **Bounded Context?** — Same word, different model (Site in each module)
19. **Chejori test mikoni domain?** — Unit test factory/invariants. No DB. No MediatR
20. **Ubiquitous Language?** — Code names = business names (Visitor, not Guest)

---

## Resume

**short:**

> Applied tactical DDD across an 8-module modular monolith: Entity base with domain-event collection, rich aggregates (Vehicle, Asset) with private collections and ErrorOr invariants, Value Objects (VehiclePlate), and transactional outbox dispatch to domain event handlers.

**bullets:**

- Modeled aggregates with private constructors/setters, static factories, and state-machine methods (`UpdateStatus`, `AssignTo`, `StartMaintenance`) returning `ErrorOr<T>`
- Implemented Value Objects as immutable records (`VehiclePlate`) with typed factory validation per plate type
- Built domain-event pipeline: `Raise` → EF interceptor → outbox → Quartz → idempotent `DomainEventHandler` → integration event publish
- Enforced entity/event design rules via NetArchTest (sealed DomainEvents, private entity constructors) in the Visitors module

**skills:** `Domain-Driven Design, Aggregates, Domain Events, Value Objects, Rich Domain Model, ErrorOr, Transactional Outbox, NetArchTest, Bounded Context`

---

## File-haye mohem

| chi | koja |
|---|---|
| Entity base | `Dejban.Common.Domain/Entity.cs` |
| IDomainEvent | `Dejban.Common.Domain/IDomainEvent.cs` |
| DomainEvent base | `Dejban.Common.Domain/DomainEvent.cs` |
| DomainEventHandler | `Dejban.Common.Application/Messaging/DomainEventHandler.cs` |
| Outbox interceptor | `Dejban.Common.Infrastructure/Outbox/InsertOutboxMessagesInterceptor.cs` |
| Vehicle aggregate | `Vehicles.Domain/Vehicles/Vehicle.cs` |
| VehiclePlate VO | `Vehicles.Domain/Vehicles/VehiclePlate.cs` |
| OwnerInfo | `Vehicles.Domain/Vehicles/OwnerInfo.cs` |
| Asset aggregate | `Armory.Domain/Assets/Asset.cs` |
| Personnel | `Personnels.Domain/Personnels/Personnel.cs` |
| Visitor | `Visitors.Domain/Visitors/Visitor.cs` |
| VisitReservation | `Visitors.Domain/Visitors/VisitReservation.cs` |
| Domain event mesal | `Visitors.Domain/Visitors/VisitorCreatedDomainEvent.cs` |
| Domain event handler | `Personnels.Application/.../PersonnelCreatedDomainEventHandler.cs` |
| Idempotent decorator | `Visitors.Infrastructure/Outbox/IdempotentDomainEventHandler.cs` |
| Architecture tests | `Visitors.ArchitectureTests/Domain/DomainTests.cs` |
| VehicleErrors | `Vehicles.Domain/Vehicles/VehicleErrors.cs` |
| RequestTracker anemic | `RequestTracker/Domain/Entities/` + `CreateRequestCommandHandler.cs` |
| Identity anemic | `IdentityServer/Domain/Entities/ApplicationUser.cs` |

---

*Day 12 tamum. Ba'd: Day 13 — EF Core 10 + Npgsql (multi-schema, migrations). Fehrest: [README.md](./README.md).*
