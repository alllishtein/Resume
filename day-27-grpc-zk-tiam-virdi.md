# Day 27 — gRPC (ZK / Tiam / Virdi)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Vendor SDK-haye device (ZK / Tiam / Virdi) ra nemishe be soorat-e clean dakhel-e ACLServer negah dasht: ba'zi-hashun native / x86-an, socket-haye tulani baz mikonan, va ba COM kar mikonan. Dejban inha ro to **3 microservice-e gRPC** joda karde: `ZKGrpcServer`, `TiamGrpcServer`, `VirdiGrpcServer`.

Contract-ha `.proto` hastan to `Common/Protos/{ZK,Tiam,Virdi}/`. ACL samt-e **client**-e: `*GrpcClientWrapper` unary call mizane, ba `SubscribeToEvents` (server-stream) event migire va age ghat shod reconnect mikone. Sync-e business bar asas-e brand ba `IDeviceSyncStrategy` anjam mishe (Day 35). Event-ha az StartupService-ha miran be MediatR / SignalR `DeviceHub`. Yek gRPC-e dge ham hast be esm-e SSM baraye ops. In RPC-haye device az YARP/HTTP-e public nemiran — ACL mostaghim be address-e sidecar gRPC mizane.

---

# BAKHSH-E AVAL: WORLD — gRPC to donya

## gRPC chie?

**gRPC** = RPC framework roye **HTTP/2** + **Protocol Buffers** (binary schema).

| REST/JSON | gRPC/Protobuf |
|---|---|
| human-readable | compact binary |
| loose OpenAPI | `.proto` = contract + codegen |
| unary mostly | unary + streaming |
| browser-native | needs grpc-web / gateway for browsers |

Ideal for **service-to-service**, especially chatty device control.

---

## Four RPC styles

| style | shape | Dejban use |
|---|---|---|
| **Unary** | req → res | `AddUser`, `GetFirmwareVersion`, … |
| **Server streaming** | req → stream res | `SubscribeToEvents` |
| **Client streaming** | stream req → res | rare here |
| **Bidi** | stream ↔ stream | not primary |

```protobuf
rpc GetDeviceInfo(DeviceBaseRequest) returns (GetDeviceInfoResponse);      // unary
rpc SubscribeToEvents(google.protobuf.Empty) returns (stream ZKEvent);   // server stream
```

---

## `.proto` workflow

```
zk_service.proto + zk_types.proto
        │
        ▼  (Grpc.Tools / Protobuf MSBuild)
┌───────────────────┐     ┌────────────────────┐
│ Server stubs      │     │ Client stubs       │
│ ZKServiceBase     │     │ ZKServiceClient    │
│ (GrpcServers)     │     │ (ACLServer)        │
└───────────────────┘     └────────────────────┘
```

```xml
<!-- GrpcServer.csproj -->
<Protobuf Include="..\..\Common\Protos\ZK\*.proto" GrpcServices="Server" />

<!-- ACLServer.csproj -->
<Protobuf Include="..\..\Common\Protos\**\*.proto" GrpcServices="Client" />
```

`option csharp_namespace = "Common.Protos.ZK";` — shared namespace feel.

---

## Why not REST for devices?

1. Hundreds of methods (users, FP, holidays, doors, firmware)  
2. Binary templates / face bytes — protobuf `bytes` natural  
3. Long-lived **event stream** without polling  
4. Strict versioning via proto field numbers  
5. Vendor SDK already «RPC-shaped»

---

## HTTP/2 + h2c

Local often `http://localhost:5051` (**h2c** cleartext). Prod may TLS (`https://`). `GrpcChannel.ForAddress(...)`.

Kestrel must allow HTTP/2. Behind some proxies HTTP/2 break — device gRPC usually **sidecar same host / docker network**, not public YARP.

---

## Status codes (RpcException)

| StatusCode | ma'ni |
|---|---|
| OK | success |
| Cancelled | client/server cancel |
| Unavailable | channel down |
| DeadlineExceeded | timeout |
| NotFound / InvalidArgument | … |

Dejban often wraps vendor errors in **response message** (`Error`, `Success=false`) + client maps to **ErrorOr** — dual channel: transport vs business error.

---

## Deadlines / timeouts

```csharp
var callOptions = new CallOptions(deadline: DateTime.UtcNow.AddSeconds(30));
await client.SomeRpcAsync(req, callOptions);
```

Settings: `TimeoutSeconds`, sometimes per-call `CommandTimeoutMS` on Virdi-style APIs.

---

## Streaming reconnect pattern

```
while (!cancel)
  try subscribe
    while MoveNext → handle event
  catch → log → Delay(5s) → retry
```

At-most-once during disconnect gap — ACL handlers must tolerate missed events + reconcile on TerminalConnected (pull logs).

---

## Codegen types vs domain DTOs

Proto messages ≠ ACL domain entities. Wrappers **map** proto ↔ `TerminalDTO` / ErrorOr. Don't leak `Common.Protos.*` into Application handlers when avoidable (wrappers + strategies absorb).

---

## Security (WORLD)

| concern | practice |
|---|---|
| Auth | mTLS / token metadata; Dejban often trusted network |
| Exposure | don't publish device gRPC on public gateway |
| Payload | biometrics sensitive — encrypt in transit |
| Authz | ACL already JWT; gRPC servers trust ACL caller |

---

## gRPC vs MassTransit vs SignalR

| | gRPC | MT | SignalR |
|---|---|---|---|
| who | ACL ↔ device sidecar | service ↔ service domain events | browser/agent UI |
| sync? | sync RPC + stream | async messaging | push to connected |
| contract | .proto | C# message types | hub methods |

Access log path example: device → SDK → gRPC stream → ACL wrapper event → handler → DB → SignalR DeviceHub.

---

# BAKHSH-E DOVOM: DEJBAN — 3 brand + ACL

## Architecture (big picture)

```
┌──────────────────────────────────────────────────────────┐
│ ACLServer (business + JWT + EF + SignalR DeviceHub)      │
│  *GrpcClientWrapper (Singleton)                          │
│  StartupServices (Virdi/ZK/Tiam)                         │
│  IDeviceSyncStrategy{Virdi,ZK,Tiam}                      │
└────────────▲────────────────────▲───────────────────▲────┘
             │ gRPC unary+stream  │                   │
    ┌────────┴──────┐   ┌─────────┴────────┐   ┌──────┴─────────┐
    │ VirdiGrpcServer│   │ TiamGrpcServer   │   │ ZKGrpcServer   │
    │ VirdiSdkWrapper│   │ TiamSdkWrapper   │   │ ZKSdkWrapper   │
    │ (vendor DLL)   │   │ (WS to devices)  │   │ zkemkeeper x86 │
    └───────┬────────┘   └────────┬─────────┘   └───────┬────────┘
            ▼                     ▼                     ▼
         Virdi terminals      Tiam devices           ZK terminals
```

**Chera process joda?**

1. **ZK `PlatformTarget=x86`** + COM `Interop.zkemkeeper.dll` — can't mix casually with x64 ACL  
2. Vendor SDK crash isolation  
3. Windows Service / systemd hosting per brand  
4. Independent deploy/restart without killing ACL API  

---

## Proto layout

```
Common/Protos/
  ZK/     zk_service.proto  zk_types.proto
  Tiam/   tiam_service.proto tiam_types.proto
  Virdi/  virdi_service.proto virdi_types.proto
  SSM/    ssm_service.proto ssm_types.proto   ← ops, not device brand
```

### Shared patterns in services

| capability | ZK | Tiam | Virdi |
|---|---|---|---|
| Start/stop listener | `StartServer` | `StartWebSocketListener` | `StartServer`/`StopServer` |
| Users CRUD on device | Add/Delete/Clear | Send/Delete/Clean | Add/Delete/DeleteAll |
| Access groups / timezone | yes | SetAccess / holidays | SetAccessControlData |
| Access logs pull | GetAllAccessLogs | GetNewLogs/GetAllLogs | GetAccessLog… |
| Biometrics | fingerprints | face bytes etc. | FP enroll/verify, face |
| **SubscribeToEvents** | stream ZKEvent | stream TiamEvent | stream VirdiEvent |
| Online terminals | via events | via events | GetOnlineTerminals + events |

Tiam keys devices often by **serial_number**. ZK/Virdi use IP/port/password or TerminalID depending on API.

---

## GrpcServer process (ZK example)

```csharp
builder.Services.AddGrpc(o => o.EnableDetailedErrors = IsDev);
builder.Services.AddSingleton<ZKSdkWrapper>();
builder.Services.AddSingleton<ZKGrpcService>();
app.MapGrpcService<ZKGrpcService>();
// Dev: MapGrpcReflectionService
// Host: UseWindowsService / UseSystemd
```

```csharp
public partial class ZKGrpcService : ZKService.ZKServiceBase
{
    // ConcurrentDictionary subscribers for event fan-out
    public override async Task SubscribeToEvents(..., IServerStreamWriter<ZKEvent> stream, ...)
    {
        _eventSubscribers.TryAdd(id, stream);
        await Task.Delay(Timeout.Infinite, context.CancellationToken); // hold
        // finally remove
    }
    // unary overrides → SdkWrapper → map ErrorOr/exceptions → proto response
}
```

SDK events → broadcast to all `_eventSubscribers` writers.

---

## ACL client wrappers

```csharp
services.AddOptions<ZKGrpcClientSettings>().BindConfiguration(...);
services.AddSingleton<ZKGrpcClientWrapper>(); // same Virdi/Tiam
```

```csharp
_channel = GrpcChannel.ForAddress(settings.ServerAddress);
_client = new ZKService.ZKServiceClient(_channel);
_eventStreamTask = StartEventStreamAsync(...); // auto on ctor
```

**API surface of wrapper ≈ old in-process SdkWrapper** — events with same names (`TerminalConnectedEvent`, `RealTimeAccessLogEvent`, …) so StartupServices barely care transport is gRPC.

Unary methods return `ErrorOr<T>`:

```csharp
var response = await _client.GetDeviceFirmwareVersionAsync(request);
if (response.Error != null) return MapFromGrpcError(response.Error);
return response.FirmwareVersion;
// catch → Error.Failure("GRPC_ERROR", ex.Message)
```

---

## StartupServices — glue to domain

| service | brand | role |
|---|---|---|
| `VirdiStartupService` | Virdi | subscribe wrapper events → handlers / SignalR; `StartServerAsync` |
| `ZKStartupService` | ZK | similar + online terminals to DeviceHub |
| `TiamStartupService` | Tiam | `StartWebSocketListenerAsync` on wrapper |

On connect: often **pull backlog logs**, firmware check, enqueue device sync (`DeviceSyncService`).

Realtime access log → MediatR / `RealtimeAccessLogEventHandler` → DB + `DeviceHub.Clients.All.RealtimeAccessLog`.

---

## Strategy pattern (preview Day 35)

```csharp
IDeviceSyncStrategyFactory.Create(DeviceBrands.ZK|Tiam|Virdi)
  → ZKDeviceSyncStrategy / Tiam… / Virdi…
       injects matching *GrpcClientWrapper
```

Handlers (`CreateDevice`, `GetTerminalFirmwareVersion`, sync jobs) ask factory by `device.DeviceType.Brand` — **no switch soup in Application**.

---

## Settings

```json
"ZKGrpcClientSettings": {
  "ServerAddress": "http://localhost:5051",
  "TimeoutSeconds": 30,
  "EnableRetry": true,
  "MaxRetryAttempts": 3
}
```

Similar sections for Tiam/Virdi. Server side: `ZKServerSettings` (ports, SDK options) on GrpcServer process.

---

## Error model

Two layers:

1. **Transport:** `RpcException` (Unavailable when sidecar down)  
2. **Business in payload:** `Success=false`, `ErrorCode`, nested `Error` message  

Client maps (2) → ErrorOr; (1) → Failure. UI/API sees ErrorOr consistently (Day 11).

---

## SSM gRPC (side note)

`ServerServiceManagement` + `Common/Protos/SSM` — manage/restart services including the three GrpcServers; ACL `SSMHub` streams logs via SSM client (Day 26). Not a fourth device brand — **ops plane**.

---

## Why ACL is Singleton wrapper?

Event stream must live for process lifetime. Scoped wrapper would tear stream each request. **Tradeoff:** singleton holds channel; careful with thread-safety of `ObservableCollection` online terminals; don't inject scoped DbContext into wrapper — handlers create scope.

---

## IclockController (ZK HTTP quirk)

Some ZK devices speak vendor HTTP (`/iclock/...`) directly to ACL — **parallel** to gRPC path for certain models/push protocols. Day 27 focus = gRPC sidecar; know HTTP push exists so you don't assume every ZK byte goes through GrpcServer.

---

## Smell-ha

1. **x86 ZK process** vs x64 ACL — deploy matrix pain  
2. **No auth on gRPC** between ACL↔sidecar (network trust)  
3. **Clients.All** DeviceHub after gRPC event (Day 26 tenant smell)  
4. **Event gap** on stream reconnect — must pull on connect  
5. **Proto comment typo** («Main Virdi» on ZK file) — copy-paste debt  
6. **Huge proto / wrappers** — hard to review; generated noise in PRs  
7. **EnableDetailedErrors** only Dev — good; don't leave on prod  
8. **Fire-and-forget** `_ = HandleIncomingEvent` — exception logging discipline  
9. **Dual DTO worlds** ACL contracts vs proto — mapping bugs  
10. **TestingZKGrpc hosted** — ensure not destructive in prod profiles  
11. **Biometric bytes** in logs if careless  
12. **Timeout** vendor SDK blocks thread — gRPC deadline vs SDK hang  

---

## Debug checklist

1. Sidecar process up? `curl`/grpcui reflection Dev  
2. `ServerAddress` ACL matches Kestrel URL  
3. HTTP/2 enabled?  
4. Stream connected? logs «subscribed» / «Reconnecting»  
5. OnlineTerminals count after physical connect  
6. Unary: capture RpcException StatusCode  
7. Brand strategy wrong? DeviceType.Brand enum parse  
8. ZK: x86 runtime / COM registration  
9. Tiam: device WS reachability from TiamGrpcServer host  
10. Compare: event received in wrapper but not SignalR → Startup handler  

---

## 25 soal-e mosahebe

1. Chera gRPC na REST baraye device?  
2. Chera process joda?  
3. Proto kojast?  
4. Server vs Client GrpcServices MSBuild?  
5. SubscribeToEvents pattern?  
6. Reconnect chejori?  
7. ErrorOr vs RpcException?  
8. Wrapper Singleton chera?  
9. Strategy factory rabt?  
10. ZK x86?  
11. Tiam StartWebSocketListener?  
12. Event → SignalR path?  
13. YARP for device gRPC? (no)  
14. Four RPC types?  
15. Deadline?  
16. h2c?  
17. SSM vs device protos?  
18. Map proto ↔ DTO?  
19. At-most-once stream?  
20. Windows Service host?  
21. Reflection Dev?  
22. Biometric security?  
23. Iclock vs gRPC?  
24. Multi-subscriber fan-out on server?  
25. Chejori brand ezafe koni (brand 4)?  

---

## Senario-ha

### A) Terminal connects (Virdi)  
SDK event → VirdiGrpcService writes VirdiEvent to streams → ACL VirdiGrpcClientWrapper HandleIncomingEvent → TerminalConnectedEvent → handler pulls logs / sync → DeviceHub OnlineTerminals.

### B) Sync user to device  
Admin saves ACL user assignment → DeviceSyncService → strategy by brand → wrapper `AddUser*` unary → GrpcServer → SdkWrapper → device.

### C) Sidecar restart  
Stream drops → wrapper retry 5s → resubscribe → terminals may re-connect events; online list rebuilt.

### D) Wrong ServerAddress  
All unary Failure GRPC_ERROR; stream reconnect loop warnings — ACL API up but devices «ghost offline».

### E) Add brand «Foo»  
New protos + FooGrpcServer + FooSdkWrapper + FooGrpcClientWrapper + FooDeviceSyncStrategy + factory case + StartupService — **pattern clone**.

---

## Mini lab

1. Open `zk_service.proto` — list 5 RPCs + SubscribeToEvents  
2. Trace ZKGrpcService.SubscribeToEvents hold + dictionary  
3. Trace ZKGrpcClientWrapper StartEventStreamAsync retry  
4. Find `AddSingleton<*GrpcClientWrapper>` in ACL DI  
5. Open DeviceSyncStrategyFactory switch/brands  
6. Note ZK csproj `PlatformTarget=x86` + Interop reference  
7. Find SSM proto briefly  

---

## Resume

**short:**

> Isolated ZK/Tiam/Virdi vendor SDKs behind dedicated gRPC microservices with shared Protobuf contracts, ACL-side client wrappers offering unary device ops plus resilient server-streaming event subscriptions, feeding sync strategies and realtime SignalR updates.

**bullets:**

- Defined Protobuf contracts under `Common/Protos` with server/client codegen split  
- Implemented GrpcServers wrapping vendor SDKs (incl. x86 ZK COM) hosted as Windows/systemd services  
- Built reconnecting `SubscribeToEvents` clients mapping streams to .NET events and ErrorOr unary APIs  
- Routed brand-specific sync through strategy factory over gRPC wrappers  

**skills:** `gRPC, Protocol Buffers, Grpc.AspNetCore, Grpc.Net.Client, Server Streaming, Vendor SDK Integration, Microservices, ErrorOr, Device Integration, HTTP/2`

---

## File-haye mohem

| chi | koja |
|---|---|
| Protos | `Common/Protos/{ZK,Tiam,Virdi,SSM}/` |
| ZK server | `Microservices/ZKGrpcServer/` |
| Tiam server | `Microservices/TiamGrpcServer/` |
| Virdi server | `Microservices/VirdiGrpcServer/` |
| Clients | `ACLServer/Infrastructure/Services/*GrpcClientWrapper.cs` |
| DI | `ACLServer/.../ServiceCollectionExtensions.cs` |
| Strategies | `ACLServer/Infrastructure/Strategies/*` |
| Startup | `*StartupService.cs` in ACL |
| Settings | `*GrpcClientSettings.cs` |

---

## Connection to other days

| day | rabt |
|---|---|
| 08 System design | anti-corruption / sidecars |
| 09 Microservices | device adapters as services |
| 11 ErrorOr | wrapper return type |
| 18 DI | Singleton wrappers |
| 26 SignalR | DeviceHub fed by gRPC events |
| 35 Factory+Strategy | brand sync |
| 29 Hangfire/Quartz | sync jobs calling strategies |

---

## Chejori digest koni

1. Draw ACL ↔ 3 sidecars (10 min)  
2. Read one proto service block (15 min)  
3. GrpcService Subscribe + one unary (20 min)  
4. Client stream retry + one ErrorOr method (20 min)  
5. Strategy factory touch (10 min)  
6. 25 soal (20 min)

---

## Glossary

| kalame | ma'ni |
|---|---|
| Protobuf | schema + binary encoding |
| Unary | single req/res |
| Server streaming | one req, many res |
| GrpcChannel | client connection |
| Sidecar | colocated helper process |
| SdkWrapper | vendor SDK facade |
| Codegen | generated C# from .proto |
| h2c | HTTP/2 cleartext |
| Reflection | grpcui/grpcurl discovery |
| Anti-corruption | isolate vendor model |

---

## Deep dive — event fan-out on server

```csharp
ConcurrentDictionary<string, IServerStreamWriter<TEvent>> _eventSubscribers;

// on SDK event:
foreach (var writer in _eventSubscribers.Values)
    await writer.WriteAsync(mappedEvent);
```

Multiple ACL instances each Subscribe → each gets copy. **Or** one ACL — one subscriber typically. If write fails, remove dead subscriber (implementation-dependent). Ordering: SDK thread → serialize carefully (channel/queue) to avoid blocking SDK.

---

## Deep dive — mapping ErrorOr across process

SdkWrapper returns ErrorOr → GrpcService packs into proto Error fields → Client unpacks to ErrorOr. **Don't** throw for expected vendor «user not found» — keep ErrorOr. Throw/RpcException for infrastructure.

---

## Deep dive — Tiam WebSocket vs ZK COM

| | Tiam | ZK | Virdi |
|---|---|---|---|
| device link | WS listener in TiamGrpcServer | COM/zkemkeeper | Virdi SDK server |
| ACL sees | gRPC only | gRPC only | gRPC only |
| start API | StartWebSocketListener | StartServer(devices) | StartServer |

Unified ACL mental model; divergent physics inside sidecars — interview gold.

---

## Deep dive — versioning protos

- Never reuse field numbers  
- Reserve deleted fields  
- Add optional fields backward compatible  
- Breaking change → new rpc name or package version  
- ACL + all 3 servers must deploy compatible builds together (or careful compat window)

---

## Decision: new device brand checklist

1. `Common/Protos/Foo/*`  
2. `FooGrpcServer` project (SDK refs, hosting)  
3. Implement `FooServiceBase` + SdkWrapper  
4. ACL Protobuf client include  
5. `FooGrpcClientWrapper` + settings + Singleton DI  
6. `FooStartupService`  
7. `FooDeviceSyncStrategy` + factory  
8. Docker/compose + docs ports  
9. SignalR online terminal DTO brand string  

---

## Interview 60s

> «Vendor SDKs for ZK, Tiam, and Virdi run in dedicated gRPC microservices. Shared .proto contracts live in Common. ACL uses generated clients with unary calls for sync and a reconnecting server-stream for device events, then strategies per brand drive sync while StartupServices forward realtime logs to SignalR. Isolation lets us keep ZK on x86 COM without polluting the main ACL process.»

---

## Quick self-test

1. Proto root? → `Common/Protos`  
2. Stream RPC name? → `SubscribeToEvents`  
3. Client retry delay? → ~5s  
4. Wrapper lifetime? → Singleton  
5. ZK platform? → x86  
6. Tiam start? → WebSocket listener  
7. Errors to API? → ErrorOr  
8. YARP device gRPC? → no (direct)  
9. Strategy day? → 35  
10. SSM? → ops not brand  

---

## Final checklist

- [ ] 3 sidecars + why  
- [ ] proto codegen Server/Client  
- [ ] stream + unary  
- [ ] wrapper ≈ SDK events  
- [ ] strategy link  
- [ ] resume bullets  

---

## Extra — load & blocking

Vendor SDK calls may be **sync/blocking** inside SdkWrapper. GrpcService should `await Task.Run` or ensure SDK async to avoid starving gRPC thread pool. Under mass sync (1000 users), queue/job (Hangfire) better than request-thread RPC storm.

---

## Extra — observability

- Serilog on GrpcServers (Seq)  
- Log subscriber connect/disconnect  
- Metrics: stream reconnects, unary latency, online count  
- Correlate `TerminalID` / serial in scopes  

---

## Extra — docker networking

Compose: ACL `http://virdi-grpc:port` DNS. Don't use `localhost` inside container (that's the container itself). Windows host + COM may force **process on host** not Linux container for ZK.

---

## Extra — partial classes

`ZKGrpcService.Additional.cs` — split huge generated-override surface for maintainability. Same idea client wrappers (large files).

---

## Comparison — put SDK in ACL? (rejected)

| in-ACL SDK | sidecar gRPC |
|---|---|
| one deploy | two+ deploys |
| crash kills API | crash isolates |
| x86 forces whole ACL | only ZK server x86 |
| hard to multi-lang later | proto boundary |

Chosen: sidecar. Correct anti-corruption for hardware.

---

## Lab aha moments

1. grpcurl list services on Dev reflection  
2. Stop GrpcServer → ACL stream warnings, devices stale  
3. Brand mismatch strategy → wrong wrapper calls  
4. Proto field rename without regen → subtle bugs  
5. Event without TerminalConnected reconcile → missing logs until reconnect  

---

## Map — sync user (sequence)

```
API Create/Update assignment
  → DeviceSyncService
  → Factory.Create(brand)
  → VirdiDeviceSyncStrategy.AddUser...
  → VirdiGrpcClientWrapper.AddUserToTerminalAsync
  → gRPC unary
  → VirdiGrpcService
  → VirdiSdkWrapper
  → physical terminal
  → ErrorOr back up stack
```

---

## Map — realtime log (sequence)

```
Terminal verify OK
  → Vendor SDK callback
  → SdkWrapper event
  → GrpcService WriteAsync(Event)
  → Client stream MoveNext
  → Wrapper raise RealTimeAccessLogEvent
  → Startup/handler
  → Persist + DeviceHub.RealtimeAccessLog
  → Browser
```

---

## Anti-patterns

```csharp
// BAD: call GrpcServer from browser via public YARP
// GOOD: browser → ACL REST/SignalR → ACL → gRPC sidecar

// BAD: new GrpcChannel per request
// GOOD: long-lived channel on Singleton wrapper

// BAD: ignore stream cancel and leak subscribers
// GOOD: finally Remove from dictionary

// BAD: switch(brand) in every handler
// GOOD: IDeviceSyncStrategyFactory
```

---

## Resume keywords (ATS)

`gRPC` · `Protocol Buffers` · `Grpc.AspNetCore` · `server streaming` · `device integration` · `anti-corruption layer` · `microservices` · `ErrorOr` · `vendor SDK` · `HTTP/2`

---

## What Day 27 is *not*

- Not full Strategy implementation detail (Day 35)  
- Not Hangfire job internals (Day 29)  
- Not every RPC catalog memorization — patterns matter  
- Not SSM deep dive  

Focus: **contract + sidecar + client stream/unary + ACL integration**.

---

## Proto field discipline (cheatsheet)

| rule | example |
|---|---|
| New field | next number, optional semantics |
| Remove | `reserved 12;` + reserved name |
| Rename | keep number; only change name in proto (wire same) |
| Enum | don't reorder values carelessly |

---

## Culture / SDK quirks

GrpcServers use helpers like `CultureScope` — some vendor SDKs expect specific culture for parsing. Another reason isolation helps: ACL culture/localization ≠ SDK thread culture.

---

## End-to-end failure matrix

| failure | symptom | mitigate |
|---|---|---|
| Sidecar down | GRPC_ERROR / reconnect loop | health check + alert |
| Device offline | business ErrorOr from SDK | UI offline state |
| Stream gap | missed realtime log | pull on TerminalConnected |
| Wrong brand strategy | odd errors / no-op | validate DeviceType.Brand |
| Proto skew | deserialize errors | version lock deploy |
| x86 COM missing | ZK server won't start | install runtime/reg |

---

## Interview follow-ups (short answers)

**Q: Why Protobuf field numbers?**  
A: Stable binary tags; names can change.

**Q: Can FE call VirdiService?**  
A: Shouldn't; authz + network; use ACL façade.

**Q: Exactly-once events?**  
A: No; design idempotent handlers + DB unique where needed.

**Q: Link to outbox?**  
A: Device side effects usually imperative RPC; domain integration events to other services still outbox (Days 21–23). Don't confuse.

---

## Size note

Virdi proto is large (many RPCs). Interview: «we expose a wide device surface area via one service definition per brand; ACL strategies call the subset needed for sync.»

---

## Self-check diagram (draw from memory)

```
[Device]--SDK--[GrpcServer]--proto--[Wrapper]--events--[Handlers]
                              \--unary--[Strategy/Sync]
```

Agar 30 saniye mikeshi → amade.

---

*Day 27 tamum. Ba'd: Day 28 — MinIO / S3 (amade). Fehrest: [README.md](./README.md).*
