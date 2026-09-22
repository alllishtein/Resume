# Day 35 — Factory + Strategy (device sync)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

To ACLServer se brand-e dastgah-e vorud/khoruj hast: **Virdi**, **ZK**, **Tiam**. Har kodum protocol / gRPC / quirk-e khodesh ro dare — ama *kar-e business* yeksan-e: user be device befrest, az device bekesh, setting sync kon, biometric, restart, …

**Strategy pattern:** interface-e moshtarak `IDeviceSyncStrategy` + se class (`VirdiDeviceSyncStrategy`, `ZKDeviceSyncStrategy`, `TiamDeviceSyncStrategy`) ke *chejori* anjam midan farq dare.

**Factory pattern:** `IDeviceSyncStrategyFactory.Create(DeviceBrands)` — ba brand (+ flag `DeviceGrpcServices:*.Enabled`) strategy-e dorost ro az DI migire.

**Orchestrator:** `DeviceSyncService` — device load mikone, brand parse, factory.Create, Hangfire queue `devices_queue` chain, SignalR status. Handler-ha bishtar ba service harf mizanan; ba'zi command-ha (CreateDevice, UpdateDevice, firmware, network save) mostaghim factory.

Day 27 = gRPC sidecar. In ruz = *chejori* code brand-ha ro joda mikone bedune `if (brand==Virdi) … else if …` to har handler.

**Band-e gharardad-e jadid:** tozihat ravoontar va sade-tar — bishtar «farz kon / yani chi / chera».

---

# BAKHSH-E AVAL: WORLD — Strategy + Factory

## Farz kon — se printer, yek dokme Print

Dokme «Chap» yeksan-e. Printer HP / Epson / Brother har kodum driver digar.

- **Strategy** = driver (algorithm joda, contract yeksan: `Print(doc)`)
- **Factory** = «brand chi-e? → driver-e dorost bede»
- **Service** = dokme: document load → factory → print → status UI

Bedune in: har dokme `if HP … else if Epson` — hell vaghti brand 4om miad.

---

## Strategy pattern — be zaban-e adam

**Mas'ale:** yek *raftar* chand *piyade-sazi* dare; runtime entekhab mishe.

```
IDeviceSyncStrategy
  ├─ VirdiDeviceSyncStrategy   (gRPC Virdi, TerminalId)
  ├─ ZKDeviceSyncStrategy      (push command queue + gRPC ZK)
  └─ TiamDeviceSyncStrategy    (gRPC Tiam, SerialNumber pages)
```

Caller faghat:

```csharp
await strategy.GetUsersFromDeviceAsync(device);
```

**Chera?** Open/Closed: brand jadid = class jadid + case factory — na edit 40 handler.

**SOLID:** OCP + SRP (har strategy mas'ul brand-e khodesh).

---

## Factory pattern — be zaban-e adam

Factory = object creator ba *logic*.

```csharp
IDeviceSyncStrategy Create(DeviceBrands brand);
```

Na `new VirdiDeviceSyncStrategy(...)` to handler (ctor dependencies ziad: gRPC wrapper, repo, options, logger, MediatR…).

Factory az **`IServiceProvider.GetRequiredService<T>()`** migire — DI lifetime Scoped dorost mimune.

**Yani chi?** Factory *selektor* + *resolver DI*-e, na duplicate ctor wiring.

---

## Factory vs Strategy — farq-e yek khati

| | Strategy | Factory |
|---|---|---|
| soal | *chejori* anjam bedam? | *kodom* object ro besazam/bedeham? |
| output | algorithm | instance |
| Dejban | `IDeviceSyncStrategy` methods | `DeviceSyncStrategyFactory.Create` |

Har do *ba ham* miayan: Factory Strategy mide.

---

## Anti-pattern bedune ina

```csharp
// BAD — to har command
if (brand == Virdi) { /* 200 line gRPC */ }
else if (brand == ZK) { /* push commands */ }
else { /* Tiam */ }
```

Copy-paste, test sakht, bug-e yek brand to branch digar.

---

# BAKHSH-E DOVOM: DEJBAN — peiyade-sazi

## Naqshe-ye yek negah

```
Command / Consumer / Hangfire job
        │
        ▼
 DeviceSyncService  (ya handler + factory)
        │  load Device + DeviceType.Brand
        │  Enum.Parse<DeviceBrands>
        ▼
 IDeviceSyncStrategyFactory.Create(brand)
        │  check DeviceGrpcServices.*.Enabled
        │  GetRequiredService<XxxDeviceSyncStrategy>()
        ▼
 IDeviceSyncStrategy  (Virdi | ZK | Tiam)
        │  gRPC wrapper / push queue
        ▼
 Device / sidecar (Day 27)
```

---

## Qesmat 1 — Contract: `IDeviceSyncStrategy`

File: `Infrastructure/Strategies/IDeviceSyncStrategy.cs`

Method-haye asosi (kholase):

| method | ma'ni-ye sade |
|---|---|
| `GetUsersFromDeviceAsync` | user-ha az terminal → DB |
| `GetSelectedUsersFromDeviceAsync` | subset |
| `SetUsersToDeviceAsync` / `RemoveUsers…` / `SyncAllUsers…` | push / sync |
| `SetAccessSettingsToDeviceAsync` | access group rules |
| `SetFingerprints…` / `SetFaceTemplates…` | biometric |
| `Set/Save Interface|Network|Security Options` | config device |
| `GetFirmwareVersionAsync` | version string |
| `UpdateDeviceAsync` / `SetDefaultOptionsAsync` | create/update defaults |
| `ClearDeviceAccessLogsAsync` / `RestartDeviceAsync` / `SyncDeviceTimeAsync` | ops |
| `GetDeviceInfoAsync` / `GetDeviceAccessLogsAsync` | read |
| `SetUsersStatusToDevices` | enable/disable user on device |

Return: `ErrorOr<Success>` ya `ErrorOr<string>` — Day 11.

**Yani chi?** Yek «remote control» API baraye hame brand-ha. Dakhel hardo jahan farq dare.

---

## Qesmat 2 — Factory

```csharp
public class DeviceSyncStrategyFactory(
    IServiceProvider serviceProvider,
    IOptions<DeviceGrpcServicesSettings> deviceGrpcSettingsOptions)
    : IDeviceSyncStrategyFactory
{
    public IDeviceSyncStrategy Create(DeviceBrands brand)
    {
        return brand switch
        {
            DeviceBrands.Virdi => _deviceGrpcSettings.Virdi.Enabled
                ? serviceProvider.GetRequiredService<VirdiDeviceSyncStrategy>()
                : throw new InvalidOperationException("Virdi sync strategy is disabled…"),
            DeviceBrands.ZK => … ZK.Enabled ? GetRequiredService<ZK…>() : throw …
            DeviceBrands.Tiam => … Tiam.Enabled ? …
            _ => throw new ArgumentOutOfRangeException(…)
        };
    }
}
```

### Yani chi?

1. **Brand** entekhab mikone kodom class.  
2. **Enabled flag** (Options Day 34) — brand disable = throw clear, na NullRef.  
3. **DI resolve** — strategy Scoped ba dependencies-esh.

### Config

```csharp
public class DeviceGrpcServicesSettings
{
    public const string SectionName = "DeviceGrpcServices";
    public DeviceGrpcServiceSettings Virdi { get; init; }
    public DeviceGrpcServiceSettings Tiam { get; init; }
    public DeviceGrpcServiceSettings ZK { get; init; }
}
// Enabled default true
```

**Farz kon:** site faghat ZK dare → `Virdi.Enabled=false` → DI asan Virdi strategy register nemikone + factory throw age kasi brand Virdi bekhade.

---

## Qesmat 3 — DI register (smart)

```csharp
services.AddScoped<IDeviceSyncStrategyFactory, DeviceSyncStrategyFactory>();

if (deviceGrpcSettings.Virdi.Enabled)
    services.AddScoped<VirdiDeviceSyncStrategy>();
if (deviceGrpcSettings.ZK.Enabled)
    services.AddScoped<ZKDeviceSyncStrategy>();
if (deviceGrpcSettings.Tiam.Enabled)
    services.AddScoped<TiamDeviceSyncStrategy>();

services.AddScoped<DeviceSyncService>();
```

**Chera conditional register?**  
Comment code: «Register sync strategies only for enabled brands so DI works with any enabled subset.»  
Age hame register + sidecar down → shayad ctor fail. Enable flag = deploy flexible.

**Yani chi baraye mosahebe?** Factory + feature flag Options + selective DI.

---

## Qesmat 4 — Se strategy — farq-e raftar (ravoon)

### Virdi

- Online check ba `TerminalId`  
- `VirdiGrpcClientWrapper.GetUserInfoListFromTerminalAsync` / `GetUserDataFromTerminalAsync`  
- Loop user + Delay(300) — rate limit device  
- Encrypt password ba `ACLSettings` keys  
- `IPublisher` baraye event-haye dakheli

### ZK

- Online ba `SerialNumber`  
- **Push command queue** static `ZKPushCommands` — command string mesl `DATA QUERY USERINFO`  
- `TaskCompletionSource` + timeout — wait javab asycn az device/push path  
- Style-e digar az Virdi sync gRPC-only

### Tiam

- Online ba `SerialNumber`  
- Pagination loop `GetUsersListAsync` ta hame page  
- Map identification types (finger/card/password…)  
- gRPC Tiam wrapper

**Yani chi?** Haman method interface — se jahan-e implementation. In *dalil*-e Strategy-e.

Day 27 omigh gRPC; inja faghat «strategy joda mikone».

---

## Qesmat 5 — `DeviceSyncService` = facade / orchestrator

Ctor: repo + factory + logger + SignalR hub + localizer + Hangfire `JobStorage`.

Olgu-ye tekrar:

```csharp
var device = await _repository.GetDeviceWithTypeAsync(deviceId);
var strategy = _strategyFactory.Create(Enum.Parse<DeviceBrands>(device.DeviceType.Brand));
return await strategy.SetInterfaceOptionsAsync(device);
```

Hangfire jobs (`_GetUsersFromDevice`, …):

1. Load device + access group  
2. `CurrentStatus = SettingUsers…` → SignalR `DeviceCurrentStatusInfo`  
3. SaveChanges  
4. `Create(brand)` → strategy method  
5. Status → Ready → SignalR  

Public API-ha mesl `GetUsersFromDevice(Guid[] deviceIds)` → per device `ChainDeviceJobs` roye queue `devices_queue`.

**Yani chi?**  

- Handler nemidanad Virdi ya ZK  
- Service = orchestration + queue + UI status  
- Strategy = protocol detail  

Day 29 Hangfire Memory — inja consumer asosi-ye device queue.

---

## Qesmat 6 — Handler mostaghim ba factory

`CreateDeviceCommandHandler`:

```csharp
bool isKnownBrand = Enum.TryParse(deviceType.Brand, false, out DeviceBrands brand);
if (!isKnownBrand) return Errors.Devices.UnknownBrand;

var strategy = _strategyFactory.Create(brand);
var setDefaultsResult = await strategy.SetDefaultOptionsAsync(device);
// Save device
if (command.SyncSettingsWithAccessGroup)
    _deviceSyncService.SyncDevicesSettingsWithAccessGroup([device.Id]);
if (command.SyncUsersWithAccessGroup)
    _deviceSyncService.SyncDevicesUsersWithAccessGroup([device.Id]);
```

**Yani chi?** Create: defaults brand-specific *sync* ghabl save; ba'd Hangfire sync asycn.

Digar: `UpdateDevice`, `SaveDeviceNetworkOptions`, `GetTerminalFirmwareVersion`, … — factory for ops ke service wrapper nadaran ya thin.

Aksar ACLUser / AccessGroup / Visitor consumer → **faqat** `DeviceSyncService`.

---

## Qesmat 7 — Enum `DeviceBrands`

```csharp
public enum DeviceBrands { Virdi, ZK, Tiam /* … */ }
```

`DeviceType.Brand` string to DB → `Enum.Parse` / `TryParse`.  
Unknown → error `UnknownBrand` ya log skip.

**Smell:** Parse bedune TryParse → exception. Ba'zi path-ha TryParse; ba'ziha Parse — inconsistent.

---

## Se dastan (farz kon)

### A) Create device ZK

FE CreateDevice Brand=ZK → factory ZK strategy → SetDefaultOptions → save → Hangfire sync users/settings → ZK push/gRPC.

### B) Visitor updated (MassTransit)

`VisitorUpdatedConsumer` → DeviceSyncService set/remove users → per device Create(brand) → strategy.

### C) Virdi disabled to config

Deploy `Virdi.Enabled=false` → strategy register nist. Device ba Brand Virdi → factory throw. Ops midune bayad enable ya device type avaz.

---

## Ertebat ba pattern-haye digar

| pattern | koja |
|---|---|
| Strategy | 3 sync class |
| Factory | DeviceSyncStrategyFactory |
| Facade/Service | DeviceSyncService |
| Repository | IDeviceSyncRepository |
| Options | DeviceGrpcServices, ACLSettings |
| Hangfire | queue + chain |
| SignalR | status hub |
| ErrorOr | strategy returns |
| gRPC | wrappers to sidecar |

---

## Smell-ha (kamel + tozih)

1. **Interface god** — 20+ method; ISP za'if (Interface Segregation). Brand shayad method na-support → empty/error.  
2. **Static ConcurrentDictionary ZKPushCommands** — test/hard multi-instance; state process-local.  
3. **Enum.Parse** vs TryParse mix  
4. **Factory throw** vs ErrorOr — ba'zi path exception, ba'zi ErrorOr  
5. **Service + Hangfire `async void`** entrypoints — fire-and-forget careful  
6. **AutomaticRetry Attempts=0** — fail = manual; ok for device ama document  
7. **Huge strategy files** (1000+ line) — SRP pressure; still better than if-else hell  
8. **serviceProvider.GetRequiredService** to factory — Service Locator smell-e soft; common ba strategy DI  
9. **Brand string** to DB — typo risk; enum DB better? tradeoff  
10. **Enabled false + old devices** — runtime throw  
11. **Duplicate online-check** per strategy — shared helper?  
12. **LogError for control flow** (Tiam while) — noisy  

---

## Debug checklist (sade)

1. DeviceType.Brand exact match enum?  
2. `DeviceGrpcServices:ZK:Enabled`?  
3. Strategy registered to DI?  
4. Sidecar/gRPC up? OnlineTerminals?  
5. Hangfire `devices_queue` worker?  
6. SignalR status stuck «syncing»?  
7. Factory InvalidOperationException disabled?  
8. ZK push TCS timeout?  
9. ErrorOr FirstError message  
10. Access group / user ids empty?  

---

## 25 soal-e mosahebe

1. Strategy chie?  
2. Factory chie?  
3. Chera ba ham?  
4. OCP chejori?  
5. IDeviceSyncStrategy naqsh?  
6. Create(brand) chikar?  
7. Enabled flag chera?  
8. Chera GetRequiredService na new?  
9. DeviceSyncService naqsh?  
10. Hangfire koja?  
11. Farq Virdi vs ZK sync style?  
12. ErrorOr chera?  
13. CreateDevice flow?  
14. Visitor consumer?  
15. ISP smell interface?  
16. Service Locator?  
17. Parse brand risk?  
18. SignalR status?  
19. Day 27 ertebat?  
20. Options DeviceGrpcServices?  
21. Brand jadid cheqad kar?  
22. Test strategy chejori?  
23. Multi-instance ZK static dict?  
24. Facade vs Strategy?  
25. Resume 60s?

---

## Senario-ha

### A) Brand jadid «Foo»

1. `DeviceBrands.Foo`  
2. `FooDeviceSyncStrategy : IDeviceSyncStrategy`  
3. Factory case + Enabled  
4. DI if Enabled register  
5. gRPC wrapper Day 27 style  

Handler-ha **taghir nemikhan** (ideal).

### B) Device offline

Strategy `IsDeviceOnline` → `Errors.Devices.DeviceOffline` → service log → status Ready/fail path.

### C) Wrong brand string `"zk"` vs `"ZK"`

TryParse case sensitivity — CreateDevice `false` = case-sensitive → UnknownBrand. Daghhat.

---

## Mini lab

1. Read `IDeviceSyncStrategy` method list  
2. Read `DeviceSyncStrategyFactory` switch  
3. DI block Enabled  
4. `DeviceSyncService._GetUsersFromDevice`  
5. `CreateDeviceCommandHandler` defaults + sync flags  
6. Skim ZK push queue vs Virdi GetUser list  
7. Grep `IDeviceSyncStrategyFactory` call-sites  

---

## Resume

**kutah:**

> Implemented device synchronization in ACLServer with the Strategy and Factory patterns: a shared `IDeviceSyncStrategy` for Virdi/ZK/Tiam, a `DeviceSyncStrategyFactory` that resolves the correct scoped strategy from DI based on `DeviceBrands` and feature flags, and a `DeviceSyncService` that orchestrates Hangfire-queued sync jobs and SignalR status updates.

**bullet-ha:**

- Defined rich `IDeviceSyncStrategy` (users, biometrics, settings, ops) returning `ErrorOr`  
- Built factory with `DeviceGrpcServices.*.Enabled` gates and conditional DI registration  
- Centralized orchestration in `DeviceSyncService` (queue `devices_queue`) while create/update paths call factory for brand-specific defaults  

**skill-ha:** `Strategy pattern, Factory pattern, SOLID OCP, DI, Hangfire, gRPC, ErrorOr, SignalR, ACL/device integration`

---

## File-haye mohem

| chi | koja |
|---|---|
| Interface | `Infrastructure/Strategies/IDeviceSyncStrategy.cs` |
| Factory | `DeviceSyncStrategyFactory.cs` + `IDeviceSyncStrategyFactory.cs` |
| Strategies | `Virdi/ZK/TiamDeviceSyncStrategy.cs` |
| Service | `Infrastructure/Services/DeviceSyncService.cs` |
| DI | `ServiceCollectionExtensions` Hangfire block |
| Options | `DeviceGrpcServicesSettings.cs` |
| Enum | `DeviceBrands.cs` |
| Mesal handler | `CreateDeviceCommandHandler.cs` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 03 OOP/SOLID | Strategy/Factory theory |
| 11 ErrorOr | return type |
| 27 gRPC | wrappers sidecars |
| 29 Hangfire | devices_queue |
| 26 SignalR | DeviceHub status |
| 34 Options | Enabled flags |
| 20 MT | Visitor* consumers |

---

## Chejori digest koni (ravesh-e sade)

1. WORLD printer + Strategy/Factory (20 min)  
2. Interface + Factory code (20 min)  
3. DI Enabled (10 min)  
4. DeviceSyncService + Hangfire (20 min)  
5. Farq 3 strategy skimming (20 min)  
6. CreateDevice lab (10 min)  
7. 25 soal (20 min)  

---

## Glossary (sade)

| kalame | ma'ni-ye yek khati |
|---|---|
| Strategy | algorithm joda posht interface |
| Factory | entekhab/sakhte instance |
| Brand | Virdi/ZK/Tiam |
| Device sync | DB ↔ terminal sync |
| Orchestrator | DeviceSyncService |
| Feature flag | Enabled per brand |
| Push command (ZK) | queue command be device |
| OnlineTerminals | list terminal connected |
| ChainDeviceJobs | Hangfire per-device chain |
| ErrorOr | success ya error typed |

---

## Deep dive — cherа Scoped strategy + factory

Hangfire job Scoped scope misaze (ya equivalent). Strategy dependencies (DbContext, gRPC client) Scoped/safe.  

Factory har `Create` → `GetRequiredService` to **haman scope**.  

Age Singleton factory + Singleton strategy + Scoped DbContext → captive dependency bug. Inja Scoped factory + Scoped strategies = dorost.

---

## Deep dive — Interface Segregation tension

Ideal WORLD: `IUserSyncStrategy`, `IDeviceOptionsStrategy`, …  
Dejban: yek fat interface — pragmatic chon hame brand «bayad» hame ops ro peiyade konan (ya stub error).

**Mosahebe:** begu tradeoff — speed vs ISP. Refactor later possible.

---

## Deep dive — ZK push vs Virdi pull

| | Virdi | ZK |
|---|---|---|
| style | request/response gRPC relative sync | command queue + wait TCS |
| id | TerminalId | SerialNumber |
| complexity | loop + delay | concurrent dict + timeout |

Strategy in complexity ro *encapsulate* mikone — service fargh nemibine.

---

## Anti-pattern (ba tozih)

```csharp
// BAD
new VirdiDeviceSyncStrategy(…15 deps…);

// GOOD
_factory.Create(DeviceBrands.Virdi);

// BAD
switch(brand) { case Virdi: /* business in handler */ }

// GOOD
await strategy.SetUsersToDeviceAsync(…);

// BAD: register all strategies always even when sidecar absent
// GOOD: Enabled gate (Dejban)
```

---

## Interview 60s (ravoon)

> «ACL talks to three device brands—Virdi, ZK, and Tiam—through one IDeviceSyncStrategy. Each brand has its own strategy class that knows the gRPC or push-command details. A DeviceSyncStrategyFactory picks the strategy from DeviceBrands and DeviceGrpcServices enabled flags via DI. DeviceSyncService loads the device, creates the strategy, and runs Hangfire jobs on devices_queue while pushing status over SignalR. Handlers stay brand-agnostic; adding a brand is mainly a new strategy plus a factory case.»

---

## Quick self-test

1. 3 brand? → Virdi ZK Tiam  
2. Interface? → IDeviceSyncStrategy  
3. Factory method? → Create(DeviceBrands)  
4. Enabled section? → DeviceGrpcServices  
5. Orchestrator? → DeviceSyncService  
6. Queue? → devices_queue  
7. ZK special? → push command dict  
8. CreateDevice? → SetDefaultOptions + optional sync  
9. Return type? → ErrorOr  
10. DI lifetime strategies? → Scoped  

---

## Final checklist

- [ ] Strategy vs Factory seda  
- [ ] Factory + Enabled + DI  
- [ ] Service orchestration  
- [ ] 3 strategy behavioral farq  
- [ ] CreateDevice  
- [ ] Smells ISP/static ZK  
- [ ] Resume  

---

## Extra — «chejori brand 4om ezafe koni» (ravoon)

1. Enum value  
2. Sidecar + GrpcClientWrapper (Day 27)  
3. `FooDeviceSyncStrategy` hame method (ya NotSupported ErrorOr)  
4. Factory case + settings Enabled  
5. DI if Enabled  
6. DeviceType seed Brand string  
7. Test yek GetUsers / SetUsers  

**Handler change = 0** (ideal). In = OCP demo.

---

## Extra — Farz kon do device yek access group, do brand

Sync users ba service: foreach deviceId → har device brand khodesh → factory do strategy digar.  
Yek command, do protocol — Strategy win.

---

## Extra — Testing

- Unit: mock `IDeviceSyncStrategyFactory` → fake strategy  
- Ya test yek strategy ba mock gRPC wrapper  
- Integration: Hangfire + real sidecar — gerun

Factory interface = test seam.

---

## Extra — Map CreateDevice

```
Validate AccessGroup/Door/Region/DeviceType
Parse Brand
Factory.Create
SetDefaultOptionsAsync (brand-specific defaults on entity)
Save Device
Optional Hangfire: sync settings / sync users
Return id
```

---

## Extra — Map Hangfire GetUsers

```
Enqueue per deviceId
Job: load device → status Syncing → SignalR
Create(brand) → GetUsersFromDeviceAsync
Persist users via repository inside strategy
status Ready → SignalR
```

---

## Lab aha (sade)

1. Disable ZK Enabled → Create ZK device → exception message  
2. Follow one SetFingerprints path service→factory→strategy  
3. Count IDeviceSyncStrategy methods — ISP discussion  
4. Find VisitorDeletedConsumer → DeviceSyncService only  

---

## What Day 35 is *not*

- Full SDK command reference per brand  
- Plate reader relay (related ACL ama digar)  
- Hangfire dashboard deep (Day 29)  
- gRPC proto deep (Day 27)  

Focus: **Factory + Strategy around device sync**.

---

## Resume keywords (ATS)

`Strategy pattern` · `Factory pattern` · `SOLID` · `Dependency Injection` · `Device integration` · `Hangfire` · `gRPC` · `ErrorOr` · `SignalR` · `ACL`

---

## Band-e gharardad-e jadid — chejori in fasl neveshte shode

> **Tozihat ravoontar va sade-tar.** Dastan printer → yani chi → chera → code Dejban → smell.

In ruz:

- Strategy/Factory ba mesal-e adam  
- Factory + Enabled + DI selective  
- Service vs strategy mas'uliat  
- honest: fat interface, ZK static queue  

---

## 10 jomle ke bayad betuni seda koni (fluency drill)

1. Strategy = chejori; Factory = kodom.  
2. IDeviceSyncStrategy yek contract baraye 3 brand.  
3. Create(brand) + Enabled check.  
4. Strategies Scoped az DI.  
5. DeviceSyncService orchestrate + Hangfire.  
6. Handler-ha brand-agnostic.  
7. Virdi gRPC loop; ZK push queue; Tiam pages.  
8. ErrorOr baraye fail typed.  
9. Brand jadid ≈ strategy + factory case.  
10. ISP smell: interface chagh.

---

## Extra — Farz kon UI «Sync users» ro mizane

1. API command → MediatR handler  
2. Handler `DeviceSyncService.SyncDevicesUsersWithAccessGroup(ids)`  
3. Per device Hangfire job enqueue (chain)  
4. Worker: brand az DeviceType → factory → `SyncAllUsers…` / set users  
5. FE az SignalR status «Syncing» → «Ready» mibine  

**Yani chi?** Pattern-ha posht sahne; user faghat dokme. Resume: end-to-end device sync ba Strategy/Factory.

---

## Extra — Chera na MediatR behavior per brand?

Mitunesti pipeline behavior ba brand — overkill. Strategy klassik-tar baraye *family of algorithms*. MediatR baraye use-case; Strategy baraye variation *dakhel* use-case.

---

## Extra — Repository naqsh

`IDeviceSyncRepository` — query-haye moshtarak (GetDeviceWithType, ACL users for group, SaveChanges). Strategy-ha DB access-e sync-specific ro az tarigh repo / context pattern mikonan — na SQL raw to har brand be shekl-e copy.

Factory strategy mide; repo data access shared.

---

## Khoruj-e zehni (ye paragraph baraye khodet)

> Midunam sync-e dastgah-haye Virdi/ZK/Tiam ba Strategy joda shode va Factory ba brand (+ flag) strategy mide. DeviceSyncService orchestration va Hangfire/SignalR ro handle mikone. Midunam chera DI conditional-e va chejori brand jadid ezafe mishe bedune if-else to handlers.

Age in paragraph mal-e to shod — Day 35 done.

---

*Day 35 tamum. Ba'd: Day 36 — ASP.NET Identity (amade). Fehrest: [README.md](./README.md).*
