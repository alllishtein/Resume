# Day 60 — Mapster (Object Mapping)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mapster** library-e object mapping-e ke Dejban be ja-ye AutoMapper azash estefade mikone. Vaghti entity ro be DTO tabdil mikoni ya az JObject-e device-ha be strongly typed event-args miri, Mapster hamun jomle-i-e ke boilerplate-ye dasti-e copy kardan-e property-ha ro hazf mikone. Do ta API-e asli dare: `entity.Adapt<Dto>()` baraye one-shot-e sade, va `TypeAdapterConfig<Src,Dest>.NewConfig()` baraye complex mapping-ha ke esm-e field-ha ya shape-e source farghe. Dejban to `ApplicationConfiguration.cs` ye bar `GlobalSettings.Scan` va `NameMatchingStrategy.Flexible` set mikone va tamum — har handler-i ke `using Mapster;` dashte bashe mitune `Adapt` ro seda bezane. Hamchenin `Dapper.DefaultTypeMap.MatchNamesWithUnderscores = true` ham to hamun file hast ke baraye raw SQL query-ha-ye Dapper, column-haye snake_case-e Postgres be PascalCase-e C# map beshan.

---

# BAKHSH-E AVAL: WORLD — chera mapping lazeme

## Farz kon

Farz kon ye kargah-e baste-bandi dari. Kalat (domain entity) ye chizi-e ba koli joziyat-e dakheli — vazn, tarkibat, tarikh-e tolid, batch number, hazine-ye mavad. Vali label-i ke mituni ruyash va be moshtari bedahish (DTO) ye chiz-e sade-tar-e ba faghat esm, gheymat, va tarikh-e engheza. Mapper hamun dastgah-e chapgari-e ke az kalaye asli label tolid mikone. Bedun-e in dastgah, bayad ye nafar beshinad va dasti har field ro copy kone — khaste-kunande-ye, mosta'ed-e khata, va vaghti shape avaz beshe kharab mishe. Hamin anology baraye software ham sadegh-e: entity-ye domain-e to ba 30 ta property ya bish-tar mostaghim be client nemirese, va client ham hagh nadare hame-ye internal state-e domain ro bebine.

## Yani chi — mapping chetori kar mikone

Object mapping yani yek shape-e data ro be shape-e dge tabdil koni. To ye CQRS handler, entity-ye domain ro az DB mikhooni va mikhay be API bargarduni — vali API nabayad hame-ye property-haye domain ro bekhune (masalan secrets, internal state, navigation property-ha). Ye mapper in tabdil ro automatic anjam mide, ya ba convention (esm-haye yeki), ya ba explicit config ke migi kodum property az kodum field por beshe.

**Chera farghi mikhore az dasti neveshan:**

To ye handler age dasti map koni, in mishe:

```csharp
var dto = new StaffDto
{
    Id = entity.Id,
    FirstName = entity.FirstName,
    LastName = entity.LastName,
    NationalId = entity.NationalId,
    PhoneNumber = entity.PhoneNumber,
    Email = entity.Email,
    BirthDate = entity.BirthDate,
    EmploymentType = entity.EmploymentType,
    // ... 25 ta property-e dge ...
};
```

Ba Mapster mishe:

```csharp
var dto = entity.Adapt<StaffDto>();
```

Ye khat — va vaghti property ezafe beshe, age esm-esh yeki bashe, khodkar map mishe. Age 10 ta handler dashte bashi ke hameye DTO-ye Staff ro tolid mikonan, 10 ta ja bayad dasti avaz koni age field-e jadid biad — ba Mapster sefr ja avaz mikoni (ta vaghti convention-e esm hefz beshe).

---

## Mapster vs AutoMapper — moghayese-ye kamel

| vizhegi | Mapster | AutoMapper |
|---|---|---|
| API-e asli | `src.Adapt<Dest>()` — extension method; DI niaz nadare | `mapper.Map<Dest>(src)` — bayad `IMapper` inject beshe |
| Config | `TypeAdapterConfig<Src,Dest>.NewConfig()` / `IRegister` | `Profile` class — inherit mikoni va to `CreateMap` config mizani |
| Performance | expression tree compile; benchmark-ha often 20-40% sari-tar-e | mature-tar-e va heavier; allocate-e bishtar dare |
| DI niaz dare? | na — mishe az har ja seda zad | are — `IMapper` singleton-e ya scoped-e |
| Learning curve | kam — API sade-ye | bishtare — concept-haye Profile, ForMember, ReverseMap, ... |
| Validation-e config | mishe `Compile()` kard to startup | `AssertConfigurationIsValid()` to startup |
| IQueryable support | `ProjectToType<T>()` | `ProjectTo<T>()` |
| Community | kuchiktar vali active | bozorg, documentation-e kamel |
| Dejban | **are — estefade mishe** | **na — to repo nist, to Directory.Packages.props ham nist** |

**Chera Dejban Mapster entekhab kard:** saboktar-e, niaz be DI nadare (handler-haye CQRS bedun-e inject-e mapper kar mikonan — faghat `using Mapster;` lazeme), performance-e behtar dare, va baraye olgu-ye current-eshun ke har handler ye mesal-e one-shot `Adapt` dare kheili kafi-ye. Hich ja-ye code niaz be ye interface-ye `IMapper` nist ke mock beshe ya inject beshe.

**Ehrli budi to resume:** age to resume AutoMapper benevisid vali to repo nabud, mosahebe-chi ke code ro check kone migire. AutoMapper library-e kheili mashur-e va kheili-ha fekr mikonan hame azash estefade mikonan, vali to in proje Mapster-e. Resume ro dorost benevis.

---

## WORLD concept-ha — yek be yek

### Convention-based mapping

Vaghti property-haye source va dest esm-eshun yeki bashe (case-insensitive), Mapster khodkar map mikone. In "convention over configuration"-e — ta zamani ke exception nabashe, config lazem nist. Masalan age source `FirstName` dare va dest ham `FirstName` dashte bashe, khodkar map mishe. Age source `firstName` (camelCase) va dest `FirstName` (PascalCase) bashe, ba default match nemikone magar `NameMatchingStrategy.Flexible` set koni.

### NameMatchingStrategy.Flexible

Dejban in ro global faal karde. **Yani chi?** Vaghti esm-e source `first_name` bashe va dest `FirstName` bashe, Flexible strategy underscore/camelCase/PascalCase ro normalize mikone va match mide. Bedun-e Flexible, default strategy faghat exact-match-e case-insensitive mikone — yani `FirstName` ba `firstname` match mishe vali `first_name` match nemishe.

```csharp
TypeAdapterConfig.GlobalSettings.Default.NameMatchingStrategy(NameMatchingStrategy.Flexible);
```

In kheili mohem-e vaghti ba JSON-e device-ha ya DB column-haye snake_case kar mikoni — bedun-e in, har field bayad explicit `.Map()` dashte bashe.

### Explicit config — `TypeAdapterConfig<Src,Dest>.NewConfig()`

Vaghti source va dest shape-eshun kamelan farghe — masalan `JObject`-e device ke field-hash `sn`, `enrollid`, `devinfo.modelname` hastan — convention help nemikone va bayad Map() bezani:

```csharp
TypeAdapterConfig<JObject, AccessLogDTO>.NewConfig()
    .Map(dest => dest.UserId, src => src["enrollid"])
    .Map(dest => dest.DateTime, src =>
        DateTime.ParseExact(src["time"]!.ToString(), "yyyy-MM-dd HH:mm:ss", Culture))
    .Map(dest => dest.Image, src => !string.IsNullOrWhiteSpace(src.Value<string>("image")) ?
        Convert.FromBase64String(src.Value<string>("image")!) : Array.Empty<byte>());
```

### Ignore — exclude kardan-e property

```csharp
TypeAdapterConfig<Command, Entity>.NewConfig()
    .Ignore(dest => dest.Id)
    .Ignore(dest => dest.CreatedAt);
```

Vaghti property-i to dest dari ke nabayad az source por beshe — masalan Id ke server generate mikone, ya `CreatedAt` ke khodkar por mishe — bayad ignore koni vagarna source value (ke momkene default ya null bashe) overwrite mikone.

### ProjectToType — IQueryable-level mapping

```csharp
var dtos = await dbContext.Staff
    .Where(s => s.IsActive)
    .ProjectToType<StaffDto>()
    .ToListAsync();
```

In query ro to SQL tabdil mikone (faghat column-haye lazem ro SELECT mikone) — behtar az inke kamel entity load koni ba hame-ye navigation-hash va ba'd `Adapt` koni ke yek iteration-e dge to memory mikhore. Baraye list-haye bozorg in critical-e.

### IRegister — module-e config

```csharp
public class MyMappingConfig : IRegister
{
    public void Register(TypeAdapterConfig config)
    {
        config.NewConfig<Source, Dest>()
            .Map(d => d.FullName, s => s.First + " " + s.Last);
    }
}
```

`GlobalSettings.Scan` in class-ha ro to assembly peyda mikone va register mikone. Dejban az in estefade nakarde — vali TiamMapsterConfiguration manual `Configure()` dare ke hamun naghsh ro mide.

### Collections — list mapping

`List<Entity>.Adapt<List<Dto>>()` — Mapster khodkar list/array/IEnumerable ro handle mikone. Niaz be loop ya `.Select(x => x.Adapt<Dto>())` nist — khodesh iterate mikone va baraye har item config-e type-e mosakhkhas ro estefade mikone.

---

## Khatarat-e mapping — smell-ha-ye WORLD

### 1. Mapping into aggregate (bypass-e invariant)

Bozorg-tarin khatare hamine. Vaghti `Adapt` ro mostaghim be entity-e domain mizani, invariant-haye domain (validation-e dakheli, required field-ha, state machine, domain events to constructor) hameye skip mishan. Entity-haye ke factory ya constructor-e private daran, nabayad ba mapper sakhte beshan:

```csharp
// BAD — domain factory skip mishe:
var order = command.Adapt<Order>();
dbContext.Orders.Add(order);

// GOOD — domain logic-e Create ejra mishe:
var order = Order.Create(command.CustomerId, command.Items);
dbContext.Orders.Add(order);
```

### 2. Silent property miss

Mapster be default property-i ke match nadashte bashe ro ignore mikone — hich exception-i nemide, hich warning-i nemide. Yani age esm-e property ro typo koni ya source property hazf beshe, dto-ye bargashti field-e null/default dare va to production taze motevajeh mishi. **Rah-e hal:** to test ya startup, `RequireDestinationMemberSource` bezar, ya assertion test benevis.

### 3. Mapping to khodesh (circular reference)

Navigation property-haye EF momkene circular reference dashan (Order → Customer → Orders → ...). Mapster mitune infinite loop bezane ya ye graph-e bozorg tolid kone ke memory por kone. `MaxDepth` ya `PreserveReference` config-esh bayad set beshe ya navigation-ha bayad ignore beshan.

### 4. Mapping to hot loop — GC pressure

Age to ye loop-e 10,000-tayi dari va har iteration `Adapt` seda mizani, overhead-e allocation bala mire. Mapster avvalin bar compile mikone va cache mikone expression ro, vali har `Adapt` ye object-e jadid allocate mikone. Baraye bulk data, `ProjectToType` (ya dasti SELECT) kheili behtar-e.

### 5. Map kardan-e secret-ha

`user.Adapt<UserDto>()` — age `UserDto` property-e `PasswordHash` dashte bashe va `User` ham dashte bashe, khodkar copy mishe. Bayad ya Ignore bezari ya DTO ro dorost design koni ke secret nadashte bashe.

---

## Jadval-e 4 strategy-e mapping — key kodum ro bezan

| strategy | key estefade beshe | mesal | pros | cons |
|---|---|---|---|---|
| `Adapt<T>()` | flat DTO, esm-ha yeki | `result.Adapt<DoorResponse>()` | ye khat, clean | silent miss, domain bypass risk |
| Explicit `NewConfig().Map()` | esm-ha farghe, transformation lazeme | TiamMapsterConfiguration JObject | flexible, documentable | verbose baraye 80 field |
| `ProjectToType<T>()` | IQueryable list, performance mohem | (Dejban kam estefade karde) | SQL-level, efficient | faghat IQueryable, config bayad match kone |
| Dasti mapping | aggregate ba invariant, complex logic | `Personnel.Create(...)` | full control, explicit | boilerplate, miss risk vaghti field ziad bashe |
| `Adapt(existing)` in-place | update-e entity-ye tracked | `command.Adapt(entity)` baraye update | clean update | overwrite-e Id/CreatedAt risk |

**Gha'ede-ye khoob:** az **right-most column** ke kar mikone shoru kon:
- Flat read DTO? → `Adapt<T>()`
- JObject ya mismatched names? → `NewConfig().Map()`
- Big list query? → `ProjectToType`
- Domain aggregate? → Dasti factory
- In-place update? → `Adapt(existing)` ba Ignore

---

## Dapper MatchNamesWithUnderscores — hamun file, mafahim-e mokhtalef

In Mapster nist — vali to hamun file-ye `ApplicationConfiguration.cs` hast va ajib-e age nafahmi. Dapper (micro ORM) vaghti raw SQL mizani, column-haye natije ro be property-haye C# class map mikone. Postgres convention-esh `snake_case` (masalan `first_name`, `national_id`) va C# convention-esh `PascalCase` (masalan `FirstName`, `NationalId`). In ye khat:

```csharp
Dapper.DefaultTypeMap.MatchNamesWithUnderscores = true;
```

Be Dapper mige: `first_name` ro be `FirstName` map kon (underscore hazf kon va PascalCase farz kon). Bedun-e in, kamel-e Dapper query-hat null bargardune chun hich column-i match nadare va to az in bug gij mishi chon query ejra mishe vali hame-ye field-ha null/zero-an.

**Fargh ba Mapster Flexible:** Mapster-e Flexible baraye object-to-object mapping-e; Dapper-e MatchNamesWithUnderscores baraye SQL column → C# property. Do ta mechanism-e joda hastan ke **har do** lazem-an chon source-haye farghi daran (DB vs object).

---

# BAKHSH-E DOVOM: DEJBAN — tech proof

## ApplicationConfiguration.cs — markaz-e setup

```csharp
public static class ApplicationConfiguration
{
    public static IServiceCollection AddApplication(
        this IServiceCollection services,
        Assembly[] moduleAssemblies)
    {
        Dapper.DefaultTypeMap.MatchNamesWithUnderscores = true;

        services.AddMediatR(config =>
        {
            config.RegisterServicesFromAssemblies(moduleAssemblies);
            config.AddOpenBehavior(typeof(ExceptionHandlingPipelineBehavior<,>));
            config.AddOpenBehavior(typeof(RequestLoggingPipelineBehavior<,>));
            config.AddOpenBehavior(typeof(ValidationPipelineBehavior<,>));
        });

        services.AddValidatorsFromAssemblies(moduleAssemblies, includeInternalTypes: true);
        TypeAdapterConfig.GlobalSettings.Scan(Assembly.GetExecutingAssembly());
        TypeAdapterConfig.GlobalSettings.Default.NameMatchingStrategy(NameMatchingStrategy.Flexible);

        services.AddSingleton<LinkProvider>();
        return services;
    }
}
```

**Zincir-e in method:**

1. `MatchNamesWithUnderscores` — Dapper-e raw SQL-ha be PascalCase match mishe
2. MediatR pipeline — exception handling, logging, FluentValidation → in-ha ghabl az handler-e asli run mishan
3. `GlobalSettings.Scan` — IRegister-haye Mapster ke to `Dejban.Common.Application` assembly bashan ro peyda mikone
4. `NameMatchingStrategy.Flexible` — underscore/camelCase/PascalCase hamegi match mishan to Mapster

In ye bar ejra mishe to startup-e Dejban modular monolith. Hame-ye module-ha (Personnels, Vehicles, Armory, CashLogistics, SecurityPatrols, WeighBridge, Visitors, Inventory) az in config bahreh mibaran chun hameye `Adapt` az `GlobalSettings` estefade mikone.

---

## Olgu-ye dorost — handler flow to Dejban

Pattern-e ma'mul to CQRS handler-haye Dejban:

```
1. Validate command (FluentValidation pipeline behavior)
2. Domain Create / factory method
3. Persist (dbContext.Add + SaveChanges)
4. Adapt to response DTO / integration event
```

**Mesal-e dorost — DoorCreatedDomainEventHandler:**

```csharp
var mapedResult = result.Value.Adapt<DoorResponse>();
await eventBus.PublishAsync(new DoorCreatedIntegrationEvent(..., mapedResult));
```

Inja entity avval ba factory sakhte shode, ba'd save shode, ba'd `Adapt` be DTO baraye integration event estefade shode. In doroste — domain invariant-ha check shodan, data persist shode, va DTO faghat baraye push be service-haye dge-ye.

**Mesal-e dge — VehicleAssignmentEndedDomainEventHandler:**

```csharp
var mapedResult = result.Value.Adapt<VehicleAssignmentResponse>();
await eventBus.PublishAsync(new VehicleAssignmentEndedIntegrationEvent(mapedResult));
```

Hamun pattern: entity avval sakht mishe, persist mishe, ba'd Adapt. Khoob-e.

**Mesal-e khatabar — az chand ta handler:**

```csharp
// CreateUnitCommandHandler:
var unit = command.Adapt<Unit>();
context.Units.Add(unit);
await context.SaveChangesAsync();

// CreateRegionCommandHandler:
var region = command.Adapt<Region>();
region.Id = Guid.NewGuid();
_context.Regions.Add(region);

// CreateDeviceTypeCommandHandler:
var deviceType = command.Adapt<DeviceType>();
deviceType.Id = Guid.NewGuid();
_context.DeviceTypes.Add(deviceType);
```

In pattern to chand ta handler-e IdentityServer va ACLServer hast. **Chera bad-e?** Chon `Unit`/`Region`/`DeviceType` entity-haye domain hastan va `Adapt` hich validation-e domain-i run nemikone. Age farda `Unit` ye invariant-e jadid bezare (masalan "Name unique bashe" ya "bayad ParentUnit dashte bashe"), mapper khodesh ra ignore mikone va entity-ye invalid persist mishe.

| olgu | mesal | verdict |
|---|---|---|
| Factory → persist → Adapt to DTO | DoorCreatedDomainEventHandler | ✓ dorost |
| command.Adapt\<Entity\>() → persist | CreateUnitCommandHandler | ✗ smell |
| JObject.Adapt\<EventArgs\>() (read-only DTO) | TiamMapsterConfiguration | ✓ dorost — read-only event DTO, na entity |

---

## TiamMapsterConfiguration — JObject mapping-e device-ha

In file kheili mohem-e chon neshun mide Mapster faghat baraye DTO-ye sade nist — baraye complex JSON ham mitune kar kone ba explicit config. Tiam SDK device-haye ZK (fingerprint/face recognition terminal) ke ba JSON socket communication mikonan, field-hashun injuri-e:

```json
{
  "sn": "ABC123",
  "enrollid": "42",
  "name": "Ali Mohammadi",
  "time": "2026-01-15 08:30:00",
  "mode": 1,
  "inout": 0,
  "event": 0,
  "image": "iVBORw0KGgo..."
}
```

In esm-ha hich rabti be C# convention nadaran — `sn` yani SerialNumber, `enrollid` yani UserId, `mode` ye int-e ke bayad be enum cast beshe, `image` ye base64 string-e ke bayad be `byte[]` tabdil beshe. Bedun-e Mapster, baraye har type-e event 20-30 khat dasti assignment lazeme. Ba Mapster:

```csharp
TypeAdapterConfig<JObject, AccessLogDTO>.NewConfig()
    .Map(dest => dest.UserId, src => src["enrollid"])
    .Map(dest => dest.UserName, src => src["name"])
    .Map(dest => dest.DateTime, src =>
        DateTime.ParseExact(src["time"]!.ToString(), "yyyy-MM-dd HH:mm:ss", Culture))
    .Map(dest => dest.Mode, src => (IdentificationMode)src.Value<int>("mode"))
    .Map(dest => dest.InOut, src => src["inout"])
    .Map(dest => dest.Event, src => src["event"])
    .Map(dest => dest.Image, src => !string.IsNullOrWhiteSpace(src.Value<string>("image")) ?
        Convert.FromBase64String(src.Value<string>("image")!) : Array.Empty<byte>());
```

**Nokte-haye mohem:**

- `src["enrollid"]` → `dest.UserId` — esm-ha kamel farghan, Flexible ham help nemikone, **bayad** explicit bashe
- `DateTime.ParseExact` — device format-e khasesho dare ke ba C# default parse nemishe
- `Convert.FromBase64String` — image ro az base64 string be `byte[]` tabdil mikone baraye save to file system ya forward be SignalR
- `(IdentificationMode)src.Value<int>("mode")` — int be enum cast — type-safe mishe
- Ternary baraye image: age khali bashe, `Array.Empty<byte>()` return mikone ta null reference pish nayad

### Nested Adapt — zincir-e list mapping

```csharp
TypeAdapterConfig<JObject, RealTimeAccessLogEventArgs>.NewConfig()
    .Map(dest => dest.SerialNumber, src => src["sn"])
    .Map(dest => dest.Count, src => src["count"])
    .Map(dest => dest.LogIndex, src => src["logindex"])
    .Map(dest => dest.AccessLogs,
         src => src["record"]!.ToObject<List<JObject>>().Adapt<List<AccessLogDTO>>());
```

Inja `record` ye JSON array-e — avval ba Newtonsoft `ToObject<List<JObject>>()` parse mishe be ye list az JObject, ba'd `.Adapt<List<AccessLogDTO>>()` har item ro ba config-e AccessLogDTO ke bala define shode map mikone. In zincir-e nested-e ke elegant-e vali debug kardanesh sakht mishe — age ye field-e dakheli khali bashe ya format avaz beshe, exception az dakhel-e Mapster expression miad va stack trace kheili clear nist.

Hamun pattern baraye `GetNewLogsEventArgs`, `GetAllLogsEventArgs`, `GetUsersListEventArgs`, va `GetAccessEventArgs` ham tekrar mishe — hame nested list-e JObject daran ke ba `Adapt` map mishan.

### DeviceRegisterRequestEventArgs — nested JSON object

```csharp
TypeAdapterConfig<JObject, DeviceRegisterRequestEventArgs>.NewConfig()
    .Map(dest => dest.SerialNumber, src => src["sn"])
    .Map(dest => dest.ModelName, src => src["devinfo"]!["modelname"])
    .Map(dest => dest.MaxUserStorage, src => src["devinfo"]!["usersize"])
    .Map(dest => dest.FaceCount, src => src["devinfo"]!["usedface"])
    .Map(dest => dest.Firmware, src => src["devinfo"]!["firmware"])
    .Map(dest => dest.Time, src =>
        DateTime.ParseExact(src["devinfo"]!["time"]!.ToString(), "yyyy-MM-dd HH:mm:ss", Culture))
    .Map(dest => dest.Mac, src => src["devinfo"]!["mac"]);
    // ... 20+ field dge
```

In neshun mide masir-haye **nested** — `src["devinfo"]!["modelname"]` do sathe JSON traverse mikone. Ba Mapster config in 20+ khat-e (ke bazi-hash 3 sathe-ye "devinfo" → "subfield" → value), vali bedun-e Mapster 40+ khat mishod ba manual null check. `GetSettingEventArgs` ham 80+ field dare ke kamelesh to TiamMapsterConfiguration piyade shode — ye mesal-e vaghei az inke mapper baraye chand field-e sade nist, baraye yek dars-e enterprise ham estefade mishe.

---

## Masir-haye estefade to Dejban — inventory-e kamel

| layer | mesal | pattern |
|---|---|---|
| Command handler → entity (smell) | `command.Adapt<Unit>()`, `command.Adapt<Region>()`, `command.Adapt<ACLUser>()`, `command.Adapt<Site>()`, `command.Adapt<Position>()` | Command mostaghim be Entity — domain bypass |
| Domain event → integration DTO (khoob) | `result.Value.Adapt<DoorResponse>()`, `result.Value.Adapt<VehicleAssignmentResponse>()` | Entity → DTO ba'd az persist |
| gRPC/device wrapper | `JResult.Adapt<RealTimeAccessLogEventArgs>()`, `JResult.Adapt<DeviceRegisterRequestEventArgs>()` | JObject → typed event ba explicit config |
| ACL sync strategy | `accessGroup.AllowedAuthTypes.Adapt<AllowedAuthTypeConfig>()`, `aclUser.Adapt<VirdiACLUserDTO>()` | VO/Entity → DTO baraye device SDK call |
| Hub broadcast | `onlineTerminals.Adapt<List<OnlineTerminalDTO>>()` | Collection → broadcast DTO baraye SignalR |
| Public API cross-module | `result.Value.Adapt<DoorsResponse>()` | Module-to-module DTO mapping |

---

## Domain factory vs Adapt — deep dive

**Chera domain factory mohem-tar az Adapt baraye sakht-e entity:**

Entity-haye domain bayad invariant dashte bashan — ghavanin-i ke hamishe true hastan. Masalan:

```csharp
public class Personnel
{
    private Personnel() { }

    public static ErrorOr<Personnel> Create(string nationalId, string firstName, ...)
    {
        if (string.IsNullOrWhiteSpace(nationalId))
            return Errors.Personnel.InvalidNationalId;
        if (nationalId.Length != 10)
            return Errors.Personnel.InvalidNationalIdLength;
        return new Personnel { NationalId = nationalId, FirstName = firstName };
    }
}
```

`Adapt<Personnel>()` constructor-e private ro bypass mikone (Mapster az reflection estefade mikone va mitune private constructor-ha ro seda bezane va property-haye private set ro set kone). Pas validation-e `Create` ejra nemishe, va ye entity-ye invalid to DB save mishe. In mozu kheili mohem-e baraye mosahebe — neshun mide farahmi ke mapper tool-e, na jaygozin-e domain logic.

**Gha'ede-ye talaee:** age entity-ye domain invariant dare (private constructor, factory, required fields, state machine), **hargez** `Adapt` nazane be entity. Adapt ro baraye **DTO-ha va event-ha** estefade kon ke flat/anemic hastan va invariant nadaran.

---

## Debug checklist

1. **Property null-e ya default-e?** → esm-e source va dest match nadare + Flexible ham kafi nist → explicit `.Map()` lazeme
2. **Collection-e khali miad?** → nested `ToObject<List<JObject>>()` null bargardunde → check kon `src["record"]` null nabud
3. **DateTime crash mikone?** → format-e device avaz shode → `ParseExact` pattern ro check kon
4. **Image byte[] khali-e?** → `src.Value<string>("image")` null ya whitespace-e → ternary check ro bebin
5. **Handler result wrong type dare?** → `Adapt<WrongDto>()` compile mishe vali field-ha match nadaran → ye unit test benevis
6. **Mapper slow to bulk?** → avvalin call compile mikone; ba'd cache mishe — vali allocation bala-s. `ProjectToType` ya dasti SELECT behtar-e
7. **Circular reference stack overflow?** → navigation property-e EF → `.MaxDepth(2)` ya `.Ignore(d => d.Children)` ezafe kon
8. **NullReferenceException az dakhel-e Mapster?** → `src["devinfo"]!["field"]` — `devinfo` null bude → null check ezafe kon
9. **Property overwrite shode?** → `Adapt(existingEntity)` in-place map — `Id` ya `CreatedAt` overwrite shode → Ignore lazeme

---

## Smell-haye Dejban — jadval

| # | smell | koja | risk |
|---|---|---|---|
| 1 | `command.Adapt<Entity>()` | CreateUnit, CreateRegion, CreateDeviceType, CreateACLUser, CreateSite, CreatePosition | Domain invariant bypass |
| 2 | `Clients.All` broadcast ba Adapt | VirdiStartupService → `Adapt<List<OnlineTerminalDTO>>()` | Har connection list-e kamel-e map o send mikone |
| 3 | JObject `!` operator bedun-e null check | TiamMapsterConfiguration → `src["devinfo"]!["modelname"]` | NullRef age device field nafreste |
| 4 | Silent property miss | hame-ye Adapt-ha | `RequireDestinationMemberSource` set nashode |
| 5 | Mapping test nadare | kamel-e proje | Bug silent-e — property avaz beshe, DTO khali miad |

---

# BAKHSH-E SEVOM: mosahebe + resume

## 25 soal-e mosahebe (ba javab-e kutah)

1. **Mapster chie?** → Library-e object mapping baraye .NET; alternative-e saboktar-e AutoMapper.
2. **`Adapt<T>()` chikar mikone?** → Extension method ru-ye har object ke source ro be type-e T map mikone.
3. **Fargh-e Mapster ba AutoMapper?** → Mapster DI niaz nadare, sari-tar-e; AM mature-tar-e va ecosystem-e bozorg-tar dare.
4. **`TypeAdapterConfig.NewConfig()` key estefade mishe?** → Vaghti esm-haye source/dest match nadaran ya transformation lazeme.
5. **`GlobalSettings.Scan` chikar mikone?** → Assembly ro scan mikone baraye class-haye `IRegister`.
6. **`NameMatchingStrategy.Flexible` chie?** → snake_case, camelCase, PascalCase hameye match mishan.
7. **Khatare mapping to domain entity chie?** → Factory/constructor validation skip mishe.
8. **`ProjectToType` chie?** → IQueryable extension — mapping to SQL push mishe, efficient-tar-e.
9. **`Ignore` key estefade mishe?** → Property-i to dest ke nabayad az source por beshe (Id, CreatedAt).
10. **Collection mapping chetorie?** → `list.Adapt<List<Dto>>()` — khodkar iterate mikone.
11. **`IRegister` chie?** → Interface baraye class-haye config ke `Scan` peyda-shun mikone.
12. **Runtime-e ya compile-time?** → Avvalin call expression compile mikone (runtime code-gen); cache mishe.
13. **Silent property miss yani chi?** → Un-matched property null/default mimune — error namide.
14. **Test chetori mikonim?** → `RequireDestinationMemberSource` ya assertion unit test.
15. **JObject mapping chetorie?** → Explicit `TypeAdapterConfig<JObject,T>.NewConfig().Map(...)`.
16. **Nested Adapt chie?** → Dakhel-e `.Map()`, `.Adapt()` baraye child collection seda zade mishe.
17. **`Dapper.MatchNamesWithUnderscores` chie?** → snake_case SQL column → PascalCase C# property.
18. **Chera Dejban AutoMapper nadare?** → Team choice; Mapster saboktar bud va DI-free bud.
19. **Circular reference smell?** → EF navigation → infinite loop. Fix: MaxDepth ya Ignore.
20. **`command.Adapt<Entity>()` smell-e?** → Are — domain factory bypass mishe.
21. **Mapster version-e Dejban?** → 7.4.x.
22. **Performance-e Mapster?** → Avvalin call slow (compile); ba'd near-manual speed.
23. **Key bayad dasti map koni?** → Domain entity ba invariant, ya complex logic ke to Adapt unclear-e.
24. **`BeforeMapping`/`AfterMapping` dare?** → Are — hook-haye ghabl va ba'd az map.
25. **Mapster ba record type?** → Kar mikone; init-only property niaz be config dare.

---

## Anti-pattern-ha

```csharp
// BAD: Map secrets be public DTO
var dto = user.Adapt<UserDto>(); // PasswordHash copy mishe!
// GOOD: DTO ke PasswordHash nadare ya Ignore

// BAD: Adapt mostaghim be aggregate root
var order = command.Adapt<Order>();
// GOOD: Order.Create(command.CustomerId, ...);

// BAD: Resume claim — "Used AutoMapper" vaghti Mapster-e
// GOOD: "Used Mapster for object mapping"

// BAD: Adapt to tight loop-e 100K
foreach (var item in bigList) result.Add(item.Adapt<Dto>());
// GOOD: bigList.Adapt<List<Dto>>() ya ProjectToType
```

---

## Jadval-e moghayese — kamel-e WORLD mapper-ha

To donya-ye .NET chand ta object mapping library hast. Jadval-e moghayese:

| library | release | approach | speed | DI required | IQueryable | community |
|---|---|---|---|---|---|---|
| **Mapster** | 2017+ | expression compile + code gen | sari | na | ProjectToType | medium |
| **AutoMapper** | 2009+ | expression compile | moderate | are (IMapper) | ProjectTo | bozorg |
| **Mapperly** | 2022+ | **source generator** (compile-time) | kheili sari | na | partial | growing |
| **Dasti** | - | manual code | baseline | - | manual Select | - |

**Mapperly** jadid-tar-e va kamelan compile-time source-generated-e — hich runtime overhead nadare. Age Dejban ye ruz mikhad migrate kone, Mapperly gozine-ye khobi-e chon ham DI niaz nadare va ham error-e compile-time mide (na silent miss). Vali falan Mapster-e va arzesh-e danestan dare.

---

## Senario-ha

### A) Handler-e CreateSite
Command miad → FluentValidation check mikone → `command.Adapt<Site>()` → `context.Sites.Add(site)` → SaveChanges. Smell-e vali kar mikone chon Site-e Dejban relatively anemic-e. Age farda invariant ezafe beshe, bug mishe.

### B) Tiam device register mishe
JSON-e device miad ba `{"cmd":"reg","sn":"ABC","devinfo":{...}}` → Tiam SDK `JResult.Adapt<DeviceRegisterRequestEventArgs>()` ba config-e `TiamMapsterConfiguration` → 20+ field explicit map mishan az nested devinfo → event handler device ro to DB register mikone.

### C) Realtime access log az terminal
`{"sn":"..","count":1,"record":[{...}]}` → `Adapt<RealTimeAccessLogEventArgs>()` → `record` array nested Adapt be `List<AccessLogDTO>` → image base64 be byte[] → log save mishe va SignalR push mishe (Day 26).

### D) Online terminal list broadcast
`VirdiStartupService` → `OnlineTerminals.Adapt<List<OnlineTerminalDTO>>()` → `Clients.All.OnlineTerminals(...)`. Har connection-e jadid in list ro kamel re-map mikone — kari-e ama yek smell-e.

### E) Dapper query ba snake_case
Raw SQL: `SELECT first_name, last_name, national_id FROM staff WHERE ...` → Dapper ba `MatchNamesWithUnderscores = true` → `FirstName`, `LastName`, `NationalId` por mishan. Bedun-e in config, hame `null`.

---

## Resume

**kutah:**

> Object mapping with **Mapster** (`Adapt<>`, `TypeAdapterConfig`, `GlobalSettings.Scan`, `NameMatchingStrategy.Flexible`) across CQRS handlers and device-SDK JSON payloads; Dapper `MatchNamesWithUnderscores` for PostgreSQL snake_case columns.

**bullet-ha:**

- Configured global Mapster with flexible name matching and assembly scanning for modular CQRS mapping
- Built explicit `TypeAdapterConfig` maps for ZK/Tiam device JObject → strongly typed event DTOs with base64 image, nested list, and enum conversions
- Mapped domain event results to integration DTOs post-persist (factory-first pattern)
- Enabled Dapper underscore matching for PostgreSQL snake_case → PascalCase bridging

**skill-ha:** `Mapster` · `Object Mapping` · `TypeAdapterConfig` · `Dapper` · `CQRS` · `DTO Patterns` · `Code Generation`

---

## Lab — lahze-haye «aha»

1. `ApplicationConfiguration.cs` ro baz kon — ye file-e ke hame-ye Mapster + Dapper + MediatR setup-eshe; yani mapping, ORM, va CQRS hame dar ye ja config mishan — in neshun mide framework-e Dejban chetori centralized-e
2. TiamMapsterConfiguration ro scroll kon — 80+ field mapping baraye GetSettings neshun mide ke Mapster baraye enterprise scale-e, na toy project
3. `CreateUnitCommandHandler` ro baz kon va `command.Adapt<Unit>()` ro bebin — inja domain factory nabud; farz kon Unit farda ye invariant-e «Name unique» ezafe kone — Adapt-esh miss mikone
4. `DoorCreatedDomainEventHandler` ro baz kon va `result.Value.Adapt<DoorResponse>()` ro bebin — pattern-e dorost: entity ghablan ba factory sakhte shode, persist shode, ba'd Adapt
5. `VirdiStartupService` ro bebin — `Adapt<List<OnlineTerminalDTO>>()` va `Clients.All` — double smell: mapping + broadcast-e global
6. `Directory.Packages.props` ro search kon baraye `Mapster` — version ro bebin, motmaen sho AutoMapper nist
7. Dasti ye unit test benevis ke JObject → AccessLogDTO map kone — bebin chi feel-i dare vaghti test green mishe

---

## Mini lab — hands-on tamrin

1. To ye test project, JObject-e AccessLog besaz va `Adapt<AccessLogDTO>()` kon — assert hame-ye field-ha
2. Ye property-ye jadid be `AccessLogDTO` ezafe kon ke to JObject nabud — bebin chi mishe (silent null)
3. `RequireDestinationMemberSource(true)` set kon — dobare Adapt kon — bebin exception mide
4. Ye entity class ba private constructor besaz — bebin `Adapt` mitune sakhte bashe ya na (spoiler: mitune)
5. Do ta list-e 10K item map kon — ye bar ba `Adapt<List<>>` ye bar ba `Select(x => x.Adapt<>())` — Stopwatch bezar
6. `NameMatchingStrategy.Flexible` ro gheyrefaal kon — bebin JObject mapping-ha break mishe ya na (answer: na — chon explicit Map daran; vali convention-based-ha chi?)

---

## Masir-e vaghei-e yek request — az HTTP ta Adapt

Farz kon ye request-e `POST /api/v1/Regions/Create` miad:

```
1. HTTP request be ApiGateway miad
2. YARP route-esh mikone be ACLServer
3. Minimal API endpoint → ISender.Send(command)
4. MediatR pipeline:
   a. ExceptionHandlingBehavior
   b. RequestLoggingBehavior
   c. ValidationBehavior (FluentValidation)
5. CreateRegionCommandHandler.Handle():
   a. Validation check to DB (parent region exists?)
   b. var region = command.Adapt<Region>();   ← INJA: mapper call
   c. region.Id = Guid.NewGuid();
   d. _context.Regions.Add(region);
   e. await _context.SaveChangesAsync();
6. Return OK
```

**Nokte:** Adapt to gadam-e 5b ejra mishe — ba'd az validation vali **ghabl az** persist. Age Region ye factory dashte bashe ba validation-e domain, in ja-ye mapper-e ke problem-e. Age Region anemic bashe, OK-e.

---

## Jadval-e decision matrix — key Adapt bezan, key nazane

| shart | Adapt? | dalil |
|---|---|---|
| Entity be flat read DTO | ✓ | safe, read-only |
| Command be anemic entity (no invariant) | ⚠ borderline | kar mikone vali fragile |
| Command be domain entity ba factory | ✗ | factory seda bezan |
| JObject be typed event DTO (ba explicit config) | ✓ | explicit + read-only |
| Entity be integration event DTO | ✓ | ba'd az persist, safe |
| Entity be entity (cross-module) | ✗ | bounded context violation |
| Bulk list (10K+) | ⚠ | `ProjectToType` ya dasti better |
| Entity ba navigation property be flat DTO | ⚠ | circular risk; flatten ya ignore |

---

## Interview 60s

> «We use Mapster across the stack instead of AutoMapper. Most handlers do a simple `.Adapt<Dto>()` after persisting via domain factories. For device JSON we have explicit `TypeAdapterConfig` maps — JObject fields like `enrollid`, `sn`, nested `devinfo` — including base64 image decoding and nested list Adapt. Global config sets `NameMatchingStrategy.Flexible` so snake_case, camelCase, PascalCase all match. Dapper queries also benefit from `MatchNamesWithUnderscores` in the same startup. The main smell is `command.Adapt<Entity>()` which bypasses domain invariants — we're gradually replacing those with factory calls.»

---

## File-haye mohem

| chi | koja |
|---|---|
| Global config + Dapper | `Dejban.Common.Application/ApplicationConfiguration.cs` |
| TiamMapsterConfiguration | `TiamGrpcServer/Abstractions/MappingConfigs/TiamMapsterConfiguration.cs` |
| command.Adapt smell | `IdentityServer/.../CreateUnitCommandHandler.cs`, `ACLServer/.../CreateRegionCommandHandler.cs`, `CreateACLUserCommandHandler.cs` |
| result.Adapt khoob | `Personnels/.../DoorCreatedDomainEventHandler.cs`, `Vehicles/.../VehicleAssignmentEndedDomainEventHandler.cs` |
| Nested Adapt list | TiamMapsterConfiguration: AccessLogs, GetNewLogs, GetAllLogs, GetAccess, GetUsersList |
| Hub broadcast Adapt | `ACLServer/VirdiStartupService.cs` — OnlineTerminals |
| Package version | `Directory.Packages.props` — Mapster 7.4.x |

---

## Deep dive — thread safety-e GlobalSettings

`TypeAdapterConfig.GlobalSettings` ye static field-e — har thread ke `Adapt` seda bezane, az hamun config mikhune. **Khoob-e chon:**
- Config ro to startup ye bar set mikoni, ba'd faghat **read** mishe
- Read concurrent safe-e to .NET

**Khatarnak mishe vaghti:**
- Config ro to runtime avaz koni (masalan to ye handler) → race condition, undefined behavior
- Do ta test concurrent run beshan ke har kodum config avaz kone → flaky test

**Best practice:** hame-ye config to startup bezar. Ba'd az avvalin `Adapt` call, **hargez** config avaz nakon. Age niaz be per-request config dari (rare), ye `TypeAdapterConfig` instance-e jadid besaz va `Adapt(dest, config)` overload estefade kon — vali in pattern kamtar estefade mishe.

---

## Deep dive — Mapster internal: chera sari-tar az AutoMapper

Mapster expression tree-haye ke compile mikone optimized-tar hastan — kam-tar lambda nesting va kam-tar null check tolid mikone bar khalaf-e AutoMapper ke defense-in-depth approach dare. Ham-chenin Mapster az `DynamicMethod` (IL emit) ham estefade mikone baraye ba'zi path-ha ke az Expression.Compile sari-tar-e. Natije: baraye flat object-ha, Mapster **2-3x sari-tar**-e. Baraye deep nested object-ha fargh kamtar mishe chon bottleneck allocation-e, na mapping-e.

Vali in farghe speed to 99% application-ha bi-ma'ni-e — agar ye API-e ke 50ms database time dare 15ns ya 25ns mapping bokone, user hich farghi hes nemikone. Speed argument-e Mapster baraye **hot path** ya **bulk data pipeline** relevance dare, na baraye ye CQRS handler-e normal.

---

## Deep dive — mapping va serialization — do chiz-e joda

Gahi developer-ha mapping ro ba serialization ghati mikonan. Fargh-eshun:

| | Mapping | Serialization |
|---|---|---|
| **Chi mikone** | Object A → Object B (dar memory) | Object → byte[]/string (baraye transfer) |
| **Tool** | Mapster, AutoMapper | System.Text.Json, Newtonsoft |
| **Output** | ye .NET object-e jadid | JSON/XML/binary string |
| **Key lazeme** | shape transform (entity→DTO) | data transport (API response, message) |

To Dejban: avval `Adapt<Dto>()` mishe (mapping), ba'd ASP.NET khodesh DTO ro `System.Text.Json.Serialize` mikone (serialization). Do ta gadam-e joda hastan.

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 01 HTTP | DTO-haye API ke Adapt tolid mikone |
| 09 CQRS | handler-ha pattern-e factory → persist → Adapt |
| 15 Soft Delete | entity-haye ke Adapt mishan momkene soft-deleted bashan |
| 18 DI | Mapster DI niaz nadare — GlobalSettings singleton-e |
| 26 SignalR | hub broadcast-e DTO ke ba Adapt sakhte shode |
| 27 gRPC | TiamMapsterConfiguration JObject device mapping |
| 38 Excel Import | bulk mapping momkene Adapt dashte bashe |

---

## Deep dive — compilation lifecycle

Mapster avvalin bar ke ye combination-e `Source→Dest` estefade beshe, ye Expression Tree misaze, compile mikone be delegate, va cache mikone to `TypeAdapterConfig`. In delegate reuse mishe baraye hame-ye call-haye ba'd. Pas:

- **Cold start:** avvalin `Adapt<AccessLogDTO>()` sangin-tar-e (expression build + compile)
- **Warm:** call-haye ba'di nazdik be dasti-e assignment hastan
- **Config change:** age ba'd az avvalin estefade config avaz koni, cache invalidate nemishe — bayad `TypeAdapterConfig.GlobalSettings.Compile()` seda bezani ya process restart koni

**Benchmark-e typical (approximate):**

| senario | Mapster | dasti | AutoMapper |
|---|---|---|---|
| 1 object, 10 flat property | ~15ns | ~8ns | ~25ns |
| 1000 object flat | ~12μs | ~7μs | ~20μs |
| Nested 3 level | ~50ns | ~25ns | ~60ns |
| Avvalin call (cold) | ~2ms | 0 | ~5ms |

In adad-ha approximate-an — relative order mohem-tar-e az absolute.

---

## Deep dive — Mapster ba EF Core interaction

Vaghti entity-e EF-e track-shode ro `Adapt<Dto>()` mikoni, Mapster ye instance-e **jadid** az Dto misaze ke EF Change Tracker azash khabar nadare — in khobie, nemikhai DTO track beshe.

Vali ye API-e dge ham hast: `source.Adapt(destination)` ke **in-place** map mikone — property-haye `destination` ro overwrite mikone. Age `destination` ye entity-ye tracked bashe, Change Tracker detect mikone ke property-ha avaz shodan va to `SaveChanges` update mikone. In baraye update scenario khobie:

```csharp
var entity = await context.Staff.FindAsync(id);
command.Adapt(entity); // in-place update
await context.SaveChangesAsync();
```

Vali **khatarnake** age `Id`, `CreatedAt`, ya computed property-ha overwrite beshan — bayad Ignore bezari.

---

## Deep dive — Mapster va Newtonsoft JObject

To `TiamMapsterConfiguration`, source type `JObject`-e ke az Newtonsoft.Json miad. Mapster khodesh JSON library nadare — faghat ye source object dare ke `src["key"]` azash mikhune (chon JObject indexer dare). Age proje mikhad be System.Text.Json migrate kone:

| ghabl (Newtonsoft) | ba'd (System.Text.Json) |
|---|---|
| `src["sn"]` → `JToken` | `src["sn"]?.GetValue<string>()` → `JsonNode` |
| `src.Value<int>("mode")` | `src["mode"]?.GetValue<int>()` |
| `src["record"]!.ToObject<List<JObject>>()` | `src["record"]?.Deserialize<List<JsonObject>>()` |

In ye refactor-e bozorg-e ke bayad ba test coverage dashte bashi.

---

## Extra — config-e RequireDestinationMemberSource

```csharp
TypeAdapterConfig.GlobalSettings.Default.RequireDestinationMemberSource(true);
```

In vaghti destination property-i source match nadashte bashe, **exception throw mikone** be ja-ye silent null. Khobie baraye catch kardan-e typo va refactor-e property-ha. Dejban in ro set nakarde — vali age mikhai mapping-ha ro robust-tar koni, in avvalin ghadam-e.

---

## Extra — Mapster DI container integration

Mapster ye optional package `Mapster.DependencyInjection` dare:

```csharp
services.AddMapster(config => { config.Scan(typeof(MyConfig).Assembly); });
```

Dejban in ro estefade nakarde — az static `GlobalSettings` estefade mikone. Fargh-e asli: ba DI mishe scope-based config dashte bashi va per-request config avaz koni (rare case); ba static, global-e va ye bar baraye hamishe set mishe ke baraye 99% case-ha kafi-e.

---

## Extra — Compile() to startup baraye early failure

```csharp
TypeAdapterConfig.GlobalSettings.Compile();
```

In to startup seda bezani, Mapster hame-ye config-ha ro compile mikone va age moshkeli bashe (masalan type incompatible bashe, ya constructor-e dest peida nashe), **hamin ja exception mide** — na vaghti avvalin request miad. In kheili mohem-e baraye production chon bug-e mapping ro to deploy catch mikoni na to runtime. Dejban in ro set nakarde — age ezafe koni, confidence-e deploy bala mire.

---

## Extra — test kardan-e mapping

Beh-tar-in rah:

```csharp
[Fact]
public void Adapt_AccessLogDTO_MapsAllFields()
{
    TiamMapsterConfiguration.Configure();

    var json = JObject.Parse(@"{""enrollid"":""42"",""name"":""Ali"",
        ""time"":""2026-01-15 08:30:00"",""mode"":1,""inout"":0,
        ""event"":0,""image"":""""}");

    var dto = json.Adapt<AccessLogDTO>();

    Assert.Equal("42", dto.UserId);
    Assert.Equal("Ali", dto.UserName);
    Assert.Equal(new DateTime(2026, 1, 15, 8, 30, 0), dto.DateTime);
    Assert.Equal(IdentificationMode.Fingerprint, dto.Mode);
    Assert.Empty(dto.Image);
}
```

In test fail mishe age field-e JSON avaz beshe ya mapping eshtebah bashe — kheili behtar az manual debug to production.

---

## Deep dive — GetSettingEventArgs: 80+ field mapping

TiamMapsterConfiguration ye config dare baraye `GetSettingEventArgs` ke **80+ property** map mikone az ye JObject-e tekhi ke device mifreste. Shoma-ye field-ha: `deviceid`, `language`, `managers`, `verifymode`, `volume`, `date_format`, `time_format`, `use_dst`, `show_avatar`, `screensavertime`, `netipaddress`, `commpassword`, va dahs-ha-ye dge. In neshun mide ke Mapster baraye enterprise-scale mapping ham kar mikone — na faghat baraye 5-6 ta property.

Nokte-ye mohem: ba'zi az in field-ha conversion-e khas daran — `src.Value<int>("show_avatar") == 1` be `bool`, `Enum.GetName(typeof(IdentifyDistance), src.Value<int>("identify_distance"))` be string, va `DateTime.ParseExact`. Age ye device ye field-e jadid ezafe kone ya format avaz kone, faghat ye khat to in config bayad avaz beshe — na 80 ja to code.

Vali risk-esh: **80 ta `.Map()` call to ye zincir** — age error beshe, stack trace faghat mige "Mapster mapping failed" va neshun nemide kodum `.Map()` bud. Debug baraye in file-ha sakhte va bayad az binary search estefade koni (nisf-e Map-ha ro comment kon, bebin pass mishe ya na).

---

## Deep dive — fargh-e Adapt va Map to CQRS pipeline

To Dejban-e CQRS pipeline, do ta ja mapping lazem mishe:

1. **Voroodi:** command/query miad be handler — inja Adapt be entity (smell) ya domain factory
2. **Khorooji:** result-e handler (entity ya ValueObject) bayad be DTO tabdil beshe baraye API response ya integration event

**Pipeline-e kamel:**

```
HTTP Request
  → MediatR (command/query)
    → ValidationBehavior (FluentValidation)
      → Handler
        → Domain factory ya Adapt (sakht-e entity)
        → DbContext.SaveChanges
        → result.Value.Adapt<ResponseDto>()    ← inja OK-e
  → API response (JSON serialize)
```

Masir-e **khorooji** (entity → DTO) amn-e chon entity ghablan validate va persist shode. Masir-e **voroodi** (command → entity) khatarnake chon domain logic-e skip mishe.

---

## Extra — Mapster va source generation (.NET 7+)

Mapster az version 7+ ye source generator ham dare (`Mapster.Tool`) ke to compile-time class-haye mapping generate mikone be ja-ye runtime expression tree. Mesal:

```csharp
[AdaptTo("[name]Dto")]
public class Staff { ... }
// Generate mishe: StaffDto + mapper extension
```

Dejban in ro estefade nakarde (runtime expression estefade mikone), vali age performance-e cold start mohem bashe (masalan serverless ya container-e ke ziad restart mishe), source gen behtar-e chon hich runtime compilation nadare.

---

## Extra — flattening va unflattening

Mapster mishe nested object ro flat kone:

```csharp
// Source:
public class Order { public Customer Customer { get; set; } }
public class Customer { public string Name { get; set; } }

// Dest:
public class OrderDto { public string CustomerName { get; set; } }
```

Mapster khodkar `Customer.Name` ro be `CustomerName` map mikone (flattening). In baraye DTO-haye flat ke field-haye nested entity-ha ro daran kheili mofiede va niaz be explicit config nadare.

**Unflattening** (barsh-e akbar — `CustomerName` → `Customer.Name`) ham support mishe vali bayad `Unflattening(true)` set koni to config. Dejban in ro estefade nakarde va ma'mulan unflatten lazem nemishe chon command-ha flat hastan va entity-ha ba factory sakhte mishan.

---

## Extra — Mapster va immutable types (records / init-only)

C# record-ha ba `init` property kheili ma'mul shodan. Mapster ba record kar mikone vali bayad beduni:

```csharp
public record StaffDto(string FirstName, string LastName, string NationalId);
```

Mapster mitune constructor-e primary ro seda bezane va parameter-ha ro ba name match kone. Vali:
- Age parameter-haye constructor ba property-ha match nakonan, fail mishe
- Age `required init` property-ha darid ke to constructor nistan, bayad config-e `MapToConstructor(true)` ya explicit Map dashte bashid

```csharp
TypeAdapterConfig<Staff, StaffDto>.NewConfig().MapToConstructor(true);
```

Dejban az record baraye DTO-haye response estefade mikone — in config ro ghablan set nakarde chon property-haye public set daran, na init-only.

---

## Extra — Mapster Fluent API-e kamel

Kholase-ye method-haye zincirei ke to `NewConfig()` mishe estefade kard:

| method | karbord |
|---|---|
| `.Map(d => d.X, s => s.Y)` | explicit field mapping |
| `.Ignore(d => d.X)` | skip property |
| `.IgnoreNullValues(true)` | null property-ha ro copy nakon |
| `.PreserveReference(true)` | circular ref handle |
| `.MaxDepth(n)` | nested depth limit |
| `.MapToConstructor(true)` | constructor-e dest ro estefade kon |
| `.RequireDestinationMemberSource(true)` | hame-ye dest bayad source dashte bashe |
| `.AddDestinationTransform(...)` | transform-e global (masalan Trim) |
| `.BeforeMapping(...)` | hook ghabl az map |
| `.AfterMapping(...)` | hook ba'd az map |
| `.ConstructUsing(s => new Dest(...))` | constructor-e custom |
| `.NameMatchingStrategy(...)` | override-e global strategy |

---

## Extra — migration az AutoMapper be Mapster

Age ye proje-ye dge dari ke AutoMapper estefade mikone va mikhay be Mapster migrate koni, in-ha ro yadet bashe:

| AutoMapper | Mapster equivalent |
|---|---|
| `CreateMap<S,D>()` to Profile | `TypeAdapterConfig<S,D>.NewConfig()` |
| `.ForMember(d => d.X, opt => opt.MapFrom(s => s.Y))` | `.Map(d => d.X, s => s.Y)` |
| `.ReverseMap()` | `TypeAdapterConfig<D,S>.NewConfig()` — explicit, na khodkar |
| `services.AddAutoMapper(assemblies)` | `TypeAdapterConfig.GlobalSettings.Scan(assemblies)` |
| `IMapper.Map<T>(src)` | `src.Adapt<T>()` — DI niaz nist |
| `ProjectTo<T>(config)` | `ProjectToType<T>()` — config az GlobalSettings miad |
| `AssertConfigurationIsValid()` | `TypeAdapterConfig.GlobalSettings.Compile()` — throw mikone age moshkeli bashe |

---

## Chejori digest koni

1. `ApplicationConfiguration.cs` ro bekhun — Scan + Flexible + Dapper (5 daghighe)
2. TiamMapsterConfiguration ro bekhun — JObject → typed ba nested Adapt (15 daghighe)
3. 3 ta handler ke `command.Adapt<Entity>()` daran peyda kon — smell ra explain kon (10 daghighe)
4. Ye handler ke `result.Adapt<Dto>()` dare peyda kon — pattern-e dorost (5 daghighe)
5. 25 soal ro bedun-e negah kardan javab bede (20 daghighe)

---

## Glossary

| kalame | ma'ni |
|---|---|
| Adapt | extension method-e Mapster baraye source → dest |
| TypeAdapterConfig | class-e explicit mapping config |
| NewConfig | start-e mapping config-e jadid |
| GlobalSettings | static singleton config-e Mapster |
| Scan | assembly scan baraye IRegister |
| NameMatchingStrategy | strategy-e name match (Exact, Flexible) |
| IRegister | interface baraye config class |
| ProjectToType | IQueryable mapping (SQL-level) |
| MatchNamesWithUnderscores | Dapper: snake_case → PascalCase |
| Convention mapping | auto-map bar asas-e esm-e yeksan |
| Expression tree | compiled code ke Mapster baraye fast map misaze |
| Silent miss | property ke match nadashte null mimune bedun-e error |

---

## Resume keywords (ATS)

`Mapster` · `Object Mapping` · `TypeAdapterConfig` · `DTO Pattern` · `CQRS` · `Dapper` · `Code Generation` · `Expression Trees` · `.NET` · `Newtonsoft.Json` · `PostgreSQL`

---

## In che chizi-e Day 60 *nist*

- Rahnama-ye AutoMapper nist — Dejban AutoMapper nadare
- Rahnama-ye domain modeling nist — faghat fargh-e factory vs Adapt ro tozih midim
- FE mapping nist — in faghat backend-e
- Dapper query writing nist — faghat ye config ro tozih midim ke to hamun file bud
- Source generator-e Mapster ro estefade nakardam — faghat mention kardam

---

## Extra — naming convention-haye device JSON va chera Flexible kafi nist

Device-haye ZK field-haye kheili ajib daran: `sn`, `enrollid`, `devinfo`, `fpsize`, `usedface`, `fpalgo`, `logindex`, `bellcount`, `screensavertime`. In-ha hich convention-e standard nadaran — na snake_case-an, na camelCase-an, na PascalCase-an. Ye mix-e abbreviated lowercased hastan ke az firmware-e Chinese manufacturer umade. Vase hamin `NameMatchingStrategy.Flexible` baraye in-ha help nemikone — `sn` be `SerialNumber` match nemishe hich vaght. **Hamishi** bayad explicit `.Map()` dashte bashe. Flexible faghat baraye property-haye normal-e code ke masalan `firstName` be `FirstName` tabdil mishe mofiede.

---

## Extra — Adapt va ErrorOr pattern

Dejban az `ErrorOr<T>` (ye Result type library) estefade mikone. Pattern-e ma'mul:

```csharp
ErrorOr<Door> result = Door.Create(...);
if (result.IsError) return result.Errors;

var dto = result.Value.Adapt<DoorResponse>();
return dto;
```

**Nokte:** `Adapt` faghat ru-ye `result.Value` seda zade mishe — yani avval check mikoni ke error nist, ba'd map mikoni. **Hargez** `result.Adapt<DoorResponse>()` nazan chon ErrorOr khodesh mappable nist va Mapster ya crash mikone ya ye DTO-ye khali mide.

---

## Self-test-e sari

1. API-e asli-e Mapster chie? → `Adapt<T>()`
2. Config-e global-e Dejban koja-st? → `ApplicationConfiguration.cs`
3. Flexible chi mikone? → snake_case/camelCase/PascalCase ro match mikone
4. `command.Adapt<Entity>()` chera smell-e? → domain factory skip mishe
5. TiamMapsterConfiguration baraye chie? → JObject device JSON → typed DTOs
6. Nested Adapt chetorie? → `src["record"].ToObject<List<JObject>>().Adapt<List<AccessLogDTO>>()`
7. `MatchNamesWithUnderscores` chi-e? → Dapper snake_case → PascalCase
8. AutoMapper to Dejban hast? → Na
9. `ProjectToType` key behtar-e? → IQueryable — mapping to SQL mire
10. `GlobalSettings.Scan` chikar mikone? → IRegister ro peyda mikone

Age 8/10 ya bishtar dorost bud → beri sar-e Day 61.

---

## Extra — mapping va open/closed principle

Vaghti mapping config to ye class-e `IRegister` bashe, entity-ye jadid ke ezafe mishe mitune khod-e module-ye khodesh register-e khodesh ro ezafe kone bedun-e inke `ApplicationConfiguration` avaz beshe. In **open/closed principle**-e: system baraye extension baz-e (module-e jadid IRegister-e khodesh ro ezafe mikone) vali baraye modification baste-s (ApplicationConfiguration avaz nemishe).

Dejban alan in olgu ro kamel riayat nemikone — TiamMapsterConfiguration manual `Configure()` dare ke khodesh call mishe, na az tarigh-e `Scan`. Vali baraye Dejban module-haye asli ke az Scan estefade mikonan, age ye module-e Armory ye mapping-e jadid bezare, khodkar to startup peida mishe.

**Masir-e ideal:**
- Har module ye `IRegister` class dare
- `Scan(moduleAssemblies)` hamaro peida mikone
- Module-e jadid ezafe mishe → mapping-hash khodkar register mishe
- Hich file-e markazi avaz nemishe

---

## Extra — chetori az Mapster debug koni to Visual Studio

Vaghti ye Mapster mapping fail mishe ya result-esh ghalat-e:

1. **Breakpoint ru-ye khat-e Adapt** — bebin source object chi dare (Watch window)
2. **Breakpoint ru-ye return-e handler** — bebin dest object chi dare (hame-ye property-ha por shodan?)
3. **Exception dar Adapt:** ma'mulan `InvalidOperationException` ya `NullReferenceException` — stack trace be TypeAdapterConfig-e compiled ishare mikone ke kam-komak-e. **Rah-e hal:** source ro manually inspect kon ke hame-ye expected field-ha non-null hastan
4. **Mapping result null ya empty:** property name mismatch-e — to Immediate Window `TypeAdapterConfig<Src,Dest>.NewConfig()` ro run kon (ya debug-e Config ro check kon) ke bebin chi config shode
5. **Conditional breakpoint:** age list-e bozorg map mikoni va ye item-e khas moshkel dare, conditional breakpoint ba `item.Id == targetId` bezar ghabl az `Adapt`

---

## Checklist-e nahaei

- [ ] Fargh-e Adapt va TypeAdapterConfig
- [ ] ApplicationConfiguration: Scan + Flexible + Dapper
- [ ] TiamMapsterConfiguration: JObject → typed ba nested Adapt
- [ ] Smell: command.Adapt\<Entity\> vs domain factory
- [ ] Mapster vs AutoMapper jadval
- [ ] Debug checklist 9 nokte
- [ ] 25 soal ba javab
- [ ] Resume bullet-ha

---

## Extra — Mapster va value objects

Dejban to domain az ValueObject pattern estefade mikone (masalan `AllowedAuthTypeConfig`). Vaghti VO Adapt mishe — `accessGroup.AllowedAuthTypes.Adapt<AllowedAuthTypeConfig>()` — in OK-e chon VO immutable-e va mapper faghat field-ha ro copy mikone. Vali age VO logic-e validation dakhel-e constructor dashte bashe va Mapster constructor ro skip kone (az reflection estefade mikone va mitune private ya parameterized constructor ro bypass kone), hamun moshkel-e entity-e domain pish miad.

**Gha'ede-ye koli:**
- VO ba sade constructor (public, bi-logic): Adapt OK
- VO ba validating constructor (throw baraye invalid): Adapt risk — dasti besaz
- VO ba private constructor + factory: Adapt skip mikone → ConstructUsing(...) lazeme

In pattern to kol-e DDD codebase-ha relevance dare, na faghat Dejban. To mosahebe age beporsad "how does your mapper interact with DDD patterns?" in javab ro bedahish: "We only Adapt read DTOs post-persist; domain entities are created through factories."

---

## Khoruj-e zehni

> In ruz ra vaghti digeri kardi ke betuni bedune look-up, mafhoum-e Adapt, TypeAdapterConfig, Flexible matching, va fargh-e domain factory vs Adapt ro ba 5 jomle tozih bedi va ye mesal az TiamMapsterConfiguration ya ApplicationConfiguration biyari.

Age in paragraph mal-e to shod — Day 60 done.

---

*Day 60 tamum. Ba'di: Day 61 — Postgres LISTEN/NOTIFY. Fehrest: [README.md](./README.md).*
