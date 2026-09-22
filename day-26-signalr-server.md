# Day 26 — SignalR (server)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**SignalR** abstraction-e realtime-e ASP.NET-e, ke ru-ye WebSocket kar mikone va age WebSocket dar dastres nabashe, khodesh miad ru-ye long-polling fallback mikone. Samt-e server, do chiz asli darim: **Hub** (ya `Hub<TClient>` baraye typed) ke client mostaghim be method-hash zang mizane, va **IHubContext** ke az biroon-e hub — masalan az ye handler ya background service — mishe seda zad va be client-ha push kard.

To Dejban in olgu to chand ta hub piyade shode: **TicketHub** (har user group-e khodesho dare), **TimeHub** ke har daghighe zaman broadcast mikone, **DeviceHub** (terminal-ha o access log-haye ACL), **ManualAccessHub** (group bar asas-e site + check-e permission), **VehiclePolicyHub** (agent-ha ba API-key az tarigh-e `IHubFilter` vasl mishan, hub-esh `AllowAnonymous`-e), **PlateReaderHub**, **SSMHub** (gRPC stream ke tabdil be SignalR stream mishe), va **BaskoolHub** (stream-e vazn az scale). Gateway ham YARP-e ke har hub ro ba `/{**catch-all}` route mikone va JWT ro az `?access_token=` migire (Day 06/07). Samt-e front-end (client) baraye Day 50-e — inja faghat samt-e server-o dari mibini.

---

# BAKHSH-E AVAL: WORLD — chera realtime lazeme

## Chera SignalR ba jaye HTTP polling sade?

| polling-e ma'mooli | realtime |
|---|---|
| client har chand saniye ye bar GET mizane | server hamun lahze-i ke event mioftad push mikone |
| ham resource hadar mide ham latency dare | latency kam-e |
| piade-sazish sade-tar-e | vase in bayad connection state ro negah dashte bashi |

Ja-hayi ke be dard mikhore: chat, dashboard-haye zende, status-e device-ha, badge-ye cartable-e ticket, vazn-e zende-ye scale, sync-e policy baraye agent-ha.

---

## Transport-ha

| transport | tozih |
|---|---|
| **WebSockets** | default o avaliyat-e SignalR-e; do-tarafe va full-duplex-e |
| **Server-Sent Events** | faghat server be client mifreste (SignalR asli-an in ro dge nadare) |
| **Long polling** | vaghti WebSocket block she, SignalR khodesh miad ru-ye in fallback mikone |

Sequence-esh injuri-e: client avval negotiate mizane, transport entekhab mishe, ba'd ye connection-e persistent bar gharar mishe:

```
Client                    Gateway (YARP)              Service
  │  POST /hub/negotiate       │                        │
  │───────────────────────────▶│───────────────────────▶│
  │  connectionToken           │                        │
  │◀───────────────────────────│◀───────────────────────│
  │  WS upgrade /hub?id=…      │                        │
  │═══════════════════════════▶│═══════════════════════▶│
  │  Hub methods / client RPCs │                        │
```

---

## Mafahim-e asli

| mafhum | ma'ni |
|---|---|
| **Hub** | ye class-e ke method-haye public-esh az samt-e client ghabel-e seda zadan hastan |
| **ConnectionId** | ye id-e mojezaz vase har connection |
| **User** | `Context.User` / `UserIdentifier` — ba'd az authenticate shodan por mishe |
| **Group** | ye majmue az connectionId-ha ba ye esm |
| **Clients** | rah-haye khetab kardan: `All`, `Caller`, `Others`, `Group(name)`, `User(id)` |
| **IHubContext\<THub\>** | vaghti mikhay az biroon-e hub (masalan ye handler ya hosted service) push koni |
| **Strongly typed hub** | `Hub<IXxxClient>` — esm-e method-haye client compile-time check mishe, dge magic string nist |

```csharp
public interface IChatClient
{
    Task MessageReceived(string text);
}

[Authorize]
public class ChatHub : Hub<IChatClient>
{
    public async Task Send(string text)
        => await Clients.All.MessageReceived(text);
}

// az ye ja-ye dge (masalan ye handler):
await hubContext.Clients.Group("room-1").MessageReceived("hi");
```

---

## Lifetime-e Hub va DI

- Har bar ke ye method-e hub call mishe, ye instance-e jadid az hub sakhte mishe (mesle transient).
- To constructor mishe service-haye **scoped** (masalan DbContext) inject kard — vase method-haye hub moshkeli nadare.
- `IHubContext` khodesh **singleton**-e va amn-e — hamun chizi-e ke to BackgroundService ya MediatR handler-ha azash estefade mishe.
- **Smell:** age ye service-e singleton to-ye event-e daraz-modat-esh reference-e connection-e ye hub ro negah dare bedun-e unregister kardan, memory leak mide. Baskool ba dghat az `ConnectionAborted` estefade mikone ke in moshkel pish nayad.

---

## Olgu-ye Group

```csharp
await Groups.AddToGroupAsync(Context.ConnectionId, "site:abc");
await hubContext.Clients.Group("site:abc").Something(dto);
```

Vaghti multi-tenant hasti ya mikhay be tor-e khas be ye user beresi, in az `Clients.All` kheili behtar-e. Faghat yadet bashe join kardan bayad **authorize** she — nabayad be siteId-i ke khod-e client ferestade e'temad koni.

---

## Auth — moshkel-e WebSocket

Browser-e JS ma'mulan nemitune be rahati header `Authorization` ro ru-ye WebSocket set kone (bastegi be client dare). Vase hamin ye olgu-ye ma'mul in-e:

```
accessTokenFactory → ?access_token=JWT ru-ye negotiate/WS URL
```

Samt-e server, `JwtBearerEvents.OnMessageReceived` in query ro mikhune va to `context.Token` migozarad.

**Risk-esh:** vaghti token to URL bashe, mire to log-ha, Referer header, va log-e proxy-ha ham mimune (Day 06 in ro tozih dade). In ye trade-off-e ke ageh dashte bashim.

Age cookie-based auth dashte bashim va cookie same-site bashe, WebSocket khodesh cookie ro mifreste — Dejban to `OnMessageReceived` cookie ro ham check mikone, hattam faghat query nist.

---

## Scale-out

| ye instance | chand instance |
|---|---|
| naghshe-ye connection-ha to memory kafi-e | instance A az connection-haye instance B khabar nadare |
| | injast ke be **Redis backplane** ya Azure SignalR niaz peyda mikoni |

```csharp
services.AddSignalR().AddStackExchangeRedis("...");
```

Bedun-e backplane, `Clients.All` faghat ru-ye hamun node-i ke connection rush-e kar mikone. Alan-e Dejban baraye aksar-e hub-ha Redis backplane nadare — age bekhay hub-ha ro horizontal scale koni, in ye smell-e mohem-e ke bayad hal beshe (Day 08).

---

## Streaming

| API | karbord |
|---|---|
| `IAsyncEnumerable<T>` az method-e hub return mishe | server data ro be soorat-e stream be client mifreste |
| `ChannelReader<T>` return mishe | event-ha ro push mikoni to channel |
| Stream az client be server | inja kamtar estefade shode |

SSMHub: stream-e gRPC ro migire va yield mikone be SignalR. BaskoolHub: event-haye port-e serial ro to Channel migozare.

---

## Hub filter-ha (`IHubFilter`)

Shabih-e middleware-e vase hub-ha-n: `OnConnectedAsync`, `OnDisconnectedAsync`, `InvokeMethodAsync` ro migiran.

Karbordeshun: authentication-e API-key, logging, ya set kardan-e tenancy ghabl az inke hub asli ejra she.

---

## Typed vs dynamic

```csharp
Clients.All.SendAsync("OnlineTerminals", list); // magic string
Clients.All.OnlineTerminals(list);              // Hub<IDeviceHubClient>
```

Typed behtar-e — rename-safe-e va IDE ham komak mikone.

---

## Reliability

- Delivery-esh ma'mulan **at-most-once**-e — age connection ghat beshe, message-e in bein miss mishe.
- Vaghti reconnect mishe, client bayad khodesh **resync** kone (TicketHub dobare group-esho `OnConnected` join mikone; VehiclePolicy age version aghab bashe snapshot mifreste).
- SignalR ro nabayad manba-e haghighat hesab kard — database manba-e haghighat-e, SignalR faghat ye kanal-e notification-e.

---

## SignalR dar barabar MassTransit

| | SignalR | MassTransit |
|---|---|---|
| mokhatab | browser ya agent-i ke alan vasl-e | service-haye dge |
| persistence | nadare | outbox/inbox dare |
| fanout | connection-haye alan vasl | queue/exchange |

Momken-e ye event-e vahed injuri handle beshe: avval to DB save mishe → ba'd (age lazem bud) az tarigh-e MassTransit be service-haye dge ettela dade mishe → ba'd az tarigh-e SignalR be UI push mishe.

---

# BAKHSH-E DOVOM: DEJBAN — hub-hayi ke to proje darim

## Inventory-e hub-ha (MapHub to server)

| Hub | Service | Path | Auth |
|---|---|---|---|
| `TicketHub` | RequestTracker | `/tickethub` | `[Authorize]` |
| `TimeHub` | IdentityServer | `/timeserverhub` | `[Authorize]` |
| `DeviceHub` | ACLServer | `/devicehub` | `[Authorize]` |
| `SSMHub` | ACLServer | `/ssmhub` | `[Authorize]` |
| `PlateReaderHub` | ACLServer | `/platereaderhub` | `[Authorize]` |
| `VehiclePolicyHub` | ACLServer | `/vehiclepolicyhub` | `[AllowAnonymous]` + API-key filter |
| `ManualAccessHub` | ACLServer | `/manualaccesshub` | `[Authorize]` |
| `BaskoolHub` | BaskoolService | `/baskoolhub` | `[Authorize]` |
| `GateConnectionStatusHub` | GateServer | `/gateStatusHub` | hub-esh baz-e; join-e gate joda check mishe |

YARP: har kodum `/{**catch-all}` dare (va ba'zi-hashun ham `/Api/v{apiVersion}/...` rewrite mishan). Jadval-e kamel to Day 07 hast.

---

## 1) TicketHub — cartable-e shakhsi-e har user

```csharp
[Authorize]
public sealed class TicketHub : Hub<ITicketHubClient>
{
    public static string UserGroup(Guid userId) => $"user:{userId}";

    public override async Task OnConnectedAsync()
    {
        var userId = Context.UserIdentifier;
        if (Guid.TryParse(userId, out var parsed))
            await Groups.AddToGroupAsync(Context.ConnectionId, UserGroup(parsed));
        await base.OnConnectedAsync();
    }
}

// TicketRealtimeNotifier
await hubContext.Clients.Group(TicketHub.UserGroup(userId))
    .TicketUpdated(payload);
```

**Olgu:** group ro mostaghim az `UserIdentifier` (yani `sub` / NameIdentifier-e JWT) misazan, na az chizi ke client bede — pas ye user nemitune group-e ye user-e dge ro jaali kone bedun-e inke token-e un ro dashte bashe.

`ITicketRealtimeNotifier` ba'd az `SaveChanges` az to command handler-haye ticket seda zade mishe, ta UI (badge, list) bedun-e poll kardan refresh beshe.

---

## 2) TimeHub + TimeBroadcastHostedService

```csharp
[Authorize]
public sealed class TimeHub : Hub<IRealtimeClockClient>
{
    public override async Task OnConnectedAsync()
    {
        await Clients.Caller.ServerTime(new ServerTimePayload(IranTime.GetZoneNow()));
        await base.OnConnectedAsync();
    }
}

// BackgroundService: har 1 sanie check mikone; vaghti daghighe-ye Tehran avaz beshe → Clients.All.ServerTime
```

**Chera lazem-e?** Ta saat-haye UI (namayesh-haye Jalali) hamash sync bemunan, bedun-e inke N ta client peyvaste `GetServerTime` ro seda bezanan. Vaghti vasl mishi, fori zaman-e alan ro migiri; ba'd har tick-e daghighe ham update migiri.

---

## 3) DeviceHub — terminal-ha va access log-haye ACL

```csharp
[Authorize]
public sealed class DeviceHub : Hub<IDeviceHubClient>
{
    public override async Task OnConnectedAsync()
    {
        // snapshot-e terminal-haye online az gRPC wrapper-ha → Clients.All.OnlineTerminals(...)
    }
}
```

Method-haye contract-e client: `OnlineTerminals`, `TerminalStatus`, `RealtimeAccessLog`, `FirmwareUpgrade`, `UserFileUpgrade`, …

Manba-e push: `ZKStartupService` / `VirdiStartupService`, `ACLUserAuthService`, `RealtimeAccessLogEventHandler` — hame az tarigh-e `IHubContext<DeviceHub, IDeviceHubClient>`.

**Smell:** `Clients.All` estefade shode — yani har operator-e ACL-i ke vasl-e, sedaye hame-ye site-ha ro migire; ru-ye DeviceHub hich group-e bar asas-e site nadarim (bar khalaf-e ManualAccessHub). Pas isolation-e multi-tenant-esh za'if-tar-e.

Ye chiz-e dge ham: `OnConnected` be **All** broadcast mikone (na faghat Caller) — yani har bar ye nafar vasl mishe, hame bidar mishan.

---

## 4) ManualAccessHub — group-e site + check-e permission

```csharp
public async Task JoinSite(Guid siteId)
{
    if (siteId == Guid.Empty || !CanWatchSite(Context.User, siteId))
        return; // silent no-op

    await Groups.AddToGroupAsync(Context.ConnectionId, GroupName(siteId));
}

// CanWatchSite: claim-haye permission ke ba "{siteId}|" shoru mishan bayad
// ManualApprove ya TrafficManagement dashte bashan
```

Push-e server:

```csharp
await hub.Clients.Group(ManualAccessHub.GroupName(dto.SiteId))
    .ManualAccessRequested(dto);
```

**Olgu-ye khub:** client bayad khodesh `JoinSite` ro seda bezane; server claim-ha ro check mikone; payload momken-e aks-e base64 ham dashte bashe (sangin-e — hajmesh ro yadet bashe).

---

## 5) VehiclePolicyHub — kanal-e agent-ha (API key)

```csharp
[AllowAnonymous]
public sealed class VehiclePolicyHub(...) : Hub<IVehiclePolicyHubClient>
{
    // Heartbeat, AckSnapshot — agent → server
    // Method-haye client: ApplyPolicySnapshot, ApplyRelayCommand, ...
}

services.AddSignalR().AddHubOptions<VehiclePolicyHub>(o =>
    o.AddFilter<VehiclePolicyHubFilter>());
```

**VehiclePolicyHubFilter.OnConnectedAsync in cara-ha ro tay mikone:**

1. Header-e `X-Plate-Reader-Key` bayad bashe (age nabud ya `apiKey` to query bud, reject mikone — ta to log leak nashe)
2. Key ro hash mikone va to `PlateReaderAgents` donbalesh migarde
3. `TenantContextAccessor` ro ru-ye `SiteId`-e agent set mikone
4. Agent ro to `Context.Items` negah midare
5. Group-e `vehicle-policy:{siteId}` ro join mikone
6. `LastSeen` / `SyncStatus` ro be Online update mikone
7. Age version-e policy ya device aghab bud, `PushToAgentAsync` seda mizane

`OnDisconnect`: ConnectionId ro pak mikone, age connection-e dge-i baghi namunde offline mikone.

**Server be agent:** in kar ro `IVehiclePolicyPushService` / `RelayCommandDispatcher` ba `Clients.Group(site)` anjam mide.

In kanal-e device/agent-e, na browser-e JWT — az avval ghasdan model-e auth-esh farghe.

---

## 6) PlateReaderHub

Hub-e browser-e ke Authorize-e; `OnConnected` ye ack be Caller mifreste. Access log-ha az tarigh-e Postgres notify / service-ha be client-ha mirese (jofteshm samt-e FE lazem-e). To comment-e code neveshte: app-e plate reader to DB save mikone → ACL migire → push mikone.

---

## 7) SSMHub — pol-e stream-e gRPC

```csharp
public async IAsyncEnumerable<LogEntry> StreamLogs(
    string serviceName, int tailLines = 50,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
{
    using var call = ssmClient.StreamServiceLogs(...);
    await foreach (var entry in call.ResponseStream.ReadAllAsync(cancellationToken))
        yield return entry;
}
```

Browser midune log-haye zende-ye service ro bebine bedun-e inke mostaghim gRPC az FE baz she. Cancellation-esh be ghat-e connection vasl-e.

---

## 8) BaskoolHub — stream-e hardware

```csharp
public async Task<ChannelReader<object>> StreamWeight(...)
{
    // age lazem bud gush dadan be port-e serial ro shoru mikone
    // WeightReceived ro subscribe mikone → channel.Writer
    // vaghti ConnectionAborted beshe → unsubscribe + complete
    return channel.Reader;
}
```

`RequestWeight` ham ye method-e one-shot-e. Process-esh ma'mulan **joda**-e (BaskoolService) va ru-ye cluster-e YARP-e `dejban-baskool-cluster` — chun be port-e COM affinity dare, ye machine-e khas-o mikhad.

---

## 9) GateConnectionStatusHub

```csharp
public async Task JoinGateGroup(string gateId)
    => await Groups.AddToGroupAsync(Context.ConnectionId, gateId);
```

`IHubContext` az `GateStatusCheckerService` / event handler-ha status ro be group-haye gate push mikonan. Sabk-esh sade-tar-e (`Hub` sade, na `Hub<T>`).

---

## Registration-e hub-ha

```csharp
services.AddSignalR(); // + age lazem bud AddHubOptions filter
// Program.cs
app.MapHub<TicketHub>("/tickethub");
app.MapHub<DeviceHub>("/devicehub").WithMetadata(versionNeutralHub);
```

`[ApiVersionNeutral]` / metadata — hub-ha bar khalaf-e Minimal API-haye REST version nemishan (Day 17).

---

## JWT wiring (to Common-e moshtarak)

```csharp
OnMessageReceived = context =>
{
    // 1) age header Authorization bud
    // 2) vagarna cookie-ye AccessToken
    // 3) vagarna query-e access_token (ba underscore) / AccessToken
    context.Token = ...;
};
```

`AccessTokenQueryMiddleware` ham baraye halat-haye gheyr-e SignalR (masalan Stimulsoft) query ro be header copy mikone. Vali khode masir-e SignalR ziad-tar be `OnMessageReceived` vabaste-s.

---

## YARP (gateway)

- Masir-e `/tickethub/{**catch-all}` ro be cluster-e RequestTracker match mikone
- `/Api/v{ver}/tickethub/{**catch-all}` ham version ro rewrite/strip mikone
- Hamin olgu baraye timeserver, device, plate, manual, vehicle, baskool, gate ham hast

Upgrade-e WebSocket bayad az YARP be soorat-e native radd she (Day 07). Timeout-ha ham mohem-an: chun connection-ha tulani mimunan, config-e idle timeout-e gateway ro bayad check koni.

`vehiclepolicyhub` va `gateStatusHub` ma'mulan to layer-e auth-e gateway **anonymous**-an — khod-e service-e ke API-key va ghavanin-e join ro check mikone.

---

## Push az layer-e application (pishnahadi)

```
Command handler
  → SaveChanges / kar-e domain
  → ITicketRealtimeNotifier.NotifyAsync(...)  // ya IManualAccessPopupService
       → IHubContext.Clients.Group(...).Method(...)
```

Ghavanin-e business nabayad to method-haye hub bashan, magar join/ack/heartbeat. Hub faghat lebe-ye transport-e — mantegh-e asli jash injani.

---

## Cheat sheet-e group-ha (Dejban)

| group | hub | join |
|---|---|---|
| `user:{guid}` | TicketHub | khodkar to `OnConnected` |
| `manual-access:{siteId}` | ManualAccessHub | `JoinSite` + check-e permission |
| `vehicle-policy:{siteId}` | VehiclePolicyHub | to filter-e `OnConnected` |
| `{gateId}` | GateConnectionStatusHub | `JoinGateGroup` |
| (hich groupi / All) | DeviceHub, TimeHub | broadcast-e mostaghim |

---

## Smell-ha

1. **Redis backplane nadarim** — scale-e horizontal, `All`/`Group` beyn-e node-ha ro kharab mikone
2. **`Clients.All` to DeviceHub** — hich scope-e site-i nadare
3. **`OnConnected` → All to DeviceHub** — seda-ye ziadi tolid mikone
4. **Token to query** — ehtemal-e log leak
5. **`VehiclePolicy` ba `AllowAnonymous`** — filter-esh hich vaght nabayad skip beshe; query-e apiKey ham mamnu-e (in khubi-e khodesh-e)
6. **`ManualAccess` silent fail to `JoinSite`** — client fekr mikone join shode vali nashode
7. **DTO-haye sangin** (aks be soorat-e base64) ru-ye SignalR — bandwidth ro mikhore
8. **Gate hub untyped** — az string-e `gateId` e'temad mikone bedun-e check
9. **Baskool** — age masir-e abort-e event handler fail beshe, momkene leak she
10. **`TimeHub` be `Clients.All`** har daghighe — baraye tedad-e ma'mooli-e user mas'ale-i nist
11. **Hub + DbContext to Heartbeat-e VehiclePolicy** — vaghti agent ziad beshe contention peyda mikone
12. **Delivery-e at-most-once** — FE bayad ru-ye reconnect refetch kone

---

## Checklist-e debug

1. Negotiate 401 mide? → token to query/cookie/header hast?
2. Frame-haye WS / log-e client-e SignalR to browser ro check kon
3. Masir-e catch-all to YARP dorost-e?
4. Group join shode? (breakpoint ru-ye `OnConnected` / `JoinSite`)
5. Push seda zade shode vali group-esh eshtebah-e?
6. Multi-instance-i? faghat ba'zi client-ha event migiran → yani backplane nadari
7. Agent-e: header-e `X-Plate-Reader-Key` hast? paygham-e HubException ro bekhun
8. CORS / credentials baraye negotiate az origin-e FE dorost tanzim shode?

---

## 25 soal-e mosahebe

1. SignalR chie, chi farghi ba raw WebSocket dare?
2. Negotiate chikar mikone?
3. Fargh-e Hub va IHubContext chie?
4. Strongly typed hub chie?
5. Group-ha chetori kar mikonan?
6. Chera token ro to query mizarim (`access_token`)?
7. Scale-out bedun-e Redis chi mishe?
8. `IHubFilter` chi kar mikone?
9. To TicketHub `UserIdentifier` az koja miad?
10. Model-e auth-e VehiclePolicy chie va chera farghe?
11. Streaming ba `IAsyncEnumerable` chetori kar mikone?
12. Fargh-e SignalR ba MassTransit chie?
13. Ma'ni-e at-most-once chie va che asari dare?
14. YARP chetori WebSocket ro pass mide?
15. `ApiVersionNeutral` chera lazem-e?
16. To ManualAccess check-e permission chetorie?
17. Key-e daghighe to TimeBroadcast chie?
18. Chera `Clients.All` to multi-tenant smell-e?
19. `ConnectionAborted` che vaght seda zade mishe?
20. Lifetime-e DI-e Hub chetorie?
21. Olgu-ye resync ru-ye reconnect chie?
22. Risk-haye `AllowAnonymous` ru-ye hub chie?
23. `ChannelReader` baraye stream chetori estefade mishe?
24. Fargh-e backplane ba Azure SignalR Service chie?
25. Amniat-e broadcast-e PII ru-ye hub chetorie?

---

## Senario-ha

### A) Ticket update shode
Handler save mikone → userId-ha ro notify mikone → har group-e `user:{id}` `TicketUpdated` migire → FE toast/badge neshun mide.

### B) Operator UI-e manual access ro baz mikone
Be ManualAccessHub vasl mishe → `JoinSite(site)` seda mizane → age permission-esh OK bud join mishe → request-haye pending ru-ye `NotifyRequested` push mishan.

### C) Agent-e plate reader boot mishe
Be vehiclepolicyhub vasl mishe + header-e API key → filter check mikone → group join mishe → age version aghab bud snapshot push mishe → Heartbeat/AckSnapshot edame dare.

### D) Tick-e daghighe
`TimeBroadcastHostedService` → be `All` `ServerTime` mifreste → saat-ha update mishan.

### E) ACL ro bedun-e backplane ru-ye 2 pod scale mikoni
Push-e access log az pod A miad → faghat client-haye ru-ye pod A migiran. Age sticky session ham dashte bashi (yani load balancer hamishe ye user ro be hamun instance beferste) baz kamel hal nemishe, chun `Clients.All`/`Group` bayad hame-ye instance-ha ro poshesh bede. **In to production bug mishe** magar Redis backplane ezafe koni.

---

## Mini lab

1. Hame-ye `MapHub`-haye to Program.cs-ha ro list kon
2. `TicketHub` ro az `OnConnected` ta group ta notifier donbal kon
3. `VehiclePolicyHubFilter` ro (connect va disconnect) bekhun
4. Ru-ye `OnMessageReceived`-e JWT, ba URL-e hub-i ke `?access_token=` dare breakpoint bezar
5. Masir-haye YARP-e `devicehub` va `vehiclepolicyhub` ro peyda kon
6. Loop-e `TimeBroadcastHostedService` ro bekhun
7. Ekhtiari: FE ro disconnect kon → mottma'en sho crash nemikone; reconnect kon → resync ro bebin

---

## Resume

**kutah:**

> Implemented ASP.NET Core SignalR hubs across microservices for tickets, server time, ACL device telemetry, manual access popups, plate-reader agent policy sync (API-key hub filter), SSM log streaming, and weighbridge live weights — fronted by YARP WebSocket routes and JWT via query/cookie.

**bullet-ha:**

- Designed per-user and per-site SignalR groups with authorization on join
- Pushed domain events to clients through `IHubContext` from application services / hosted services
- Secured agent hub with `IHubFilter` API-key validation and tenant context
- Bridged gRPC and serial-port streams to browsers via SignalR streaming APIs

**skill-ha:** `SignalR, WebSockets, IHubContext, Hub Groups, IHubFilter, Real-time Systems, YARP, JWT, Streaming, ASP.NET Core`

---

## File-haye mohem

| chi | koja |
|---|---|
| TicketHub | `RequestTracker/Hubs/TicketHub.cs` |
| TicketRealtimeNotifier | `RequestTracker/.../TicketRealtimeNotifier.cs` |
| TimeHub + broadcast | `IdentityServer/Infrastructure/Hubs`, `.../TimeBroadcastHostedService.cs` |
| DeviceHub | `ACLServer/Hubs/DeviceHub.cs` |
| ManualAccessHub | `ACLServer/Hubs/ManualAccessHub.cs` |
| VehiclePolicyHub + Filter | `ACLServer/Hubs/VehiclePolicyHub*.cs` |
| PlateReaderHub / SSMHub | `ACLServer/Hubs/` |
| BaskoolHub | `BaskoolService/Hubs/BaskoolHub.cs` |
| Gate hub | `GateServer/Application/SignalR/GateConnectionStatusHub.cs` |
| JWT query token | `Common/.../ServiceCollectionExtensions.cs` — `OnMessageReceived` |
| YARP routes | `ApiGateway/appsettings.json` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 01/07 HTTP + YARP | WS upgrade, masir-haye hub |
| 06 JWT | access_token to query, blacklist ham ru-ye negotiate-e HTTP asar mizare |
| 16 Tenancy | group-haye site; TenantContext-e agent |
| 18 DI | `AddSignalR` to module-ha |
| 20 MT | masir-e movazi be service-haye dge; SignalR faghat UI-e |
| 25 Redis | cache ba backplane-e SignalR farghe (do mozu-e joda-n) |
| 27 gRPC | Device/SSM device SDK-ha ro wrap mikonan |
| 50 FE | client-haye `@microsoft/signalr` |

---

## Chejori digest koni

1. Negotiate + WS ro bekesh (5 daghighe)
2. TicketHub + notifier (15 daghighe)
3. Filter-e VehiclePolicy (20 daghighe)
4. Authorization-e `JoinSite`-e ManualAccess (10 daghighe)
5. YARP + JWT-e to query (10 daghighe)
6. 25 soal (20 daghighe)

---

## Glossary

| kalame | ma'ni |
|---|---|
| Hub | class-e endpoint-e SignalR |
| Negotiate | dast dadan ghabl az entekhab-e transport |
| ConnectionId | id-e mokhtas-e har connection |
| Group | majmue-ye pub-sub-e connection-ha |
| IHubContext | push az kod-e biroon-e hub |
| Backplane | fanout-e beyn-e node-ha (Redis) |
| Strongly typed hub | `Hub<TClient>` |
| Hub filter | middleware-e mokhtas-e hub-ha |
| Streaming hub | `IAsyncEnumerable` / `Channel` |

---

## Deep dive — UserIdentifier az koja miad

SignalR khodesh `Context.UserIdentifier` ro az claim-ha migire (default-esh `ClaimTypes.NameIdentifier` / `sub`-e). TicketHub in ro Guid parse mikone va group misaze. Age claim-esh nabashe ya type-esh dorost nabashe, hich group-i saakhte nemishe va notification-ha be sourat-e silent miss mishan. Baraye hamin config-e claim-e JWT bayad ba entezar-e hub ham-khani dashte bashe.

---

## Deep dive — Blacklist va SignalR

Negotiate ye request-e HTTP-e — `TokenRevokeMiddleware` mitune JWT-e revoke-shode ro ghabl az upgrade reject kone. Vali connection-e WebSocket-i ke **ghabl** az revoke bar gharar shode bud, mitune ta reconnect-e ba'di baghi bemune — client bayad 401-e reconnect ro handle kone; disconnect-e khodkar-e server ru-ye revoke ehtemalan hamishe piade nashode (arzesh-e mention kardan to security review dare).

---

## Deep dive — chera filter query-e apiKey ro reject mikone

```csharp
if (string.IsNullOrWhiteSpace(apiKey) || http?.Request.Query.ContainsKey("apiKey") == true)
    throw new HubException("API key is required");
```

Hata age header khali bashe va faghat query key dashte bashe, baz throw mikone. In majbur mikone secret faghat az tarigh-e header bere, ta to log-e access-e browser ya history-e URL nayofte. (Moghayese kon ba token-e JWT to query — un ye mahdudiyat-e browser-e, chun agent-ha mitunan raahat header set konan, in mahdudiyat rushun nist.)

---

## Deep dive — reconnect va version-e Ack

VehiclePolicy: agent `LastAckedVersion`-esho negah midare. Vaghti vasl mishe, age `LastAckedVersion < CurrentVersion` bashe ya `HasPendingPush` true bashe, ye push-e kamel mizane. In olgu baraye **agent-haye stateful** khubie: SignalR patch-ha ro mirasune, vali version-haye DB ta'in mikonan ke reconnect dorost anjam beshe.

Ticket: ru-ye reconnect dobare group-e `user:` join mishe; FE ham bayad list ro refetch kone chun mishe payload-i to in bein miss shode bashe.

---

## Jadval-e moghayese — strategy-haye broadcast

| strategy | mesal-e Dejban | key vaght estefade beshe |
|---|---|---|
| `Clients.All` | tick-e TimeHub, DeviceHub | vaghti audience kuchik ya global-e |
| Group bar asas-e user | TicketHub | inbox-e shakhsi |
| Group bar asas-e site | ManualAccess, VehiclePolicy | operation-e tenant/site |
| Faghat Caller | `OnConnected`-e TimeHub, ack-e PlateReader | handshake-e khosusi |
| `Clients.User(id)` | mojud-e vali estefade nashode (Ticket az Group estefade mikone) | age `UserIdProvider` set shode bashe |

---

## Anti-pattern-ha

```csharp
// BAD: be client e'temad mikoni
public Task Join(string userId) => Groups.AddToGroupAsync(..., "user:"+userId);

// GOOD: TicketHub faghat az Context.UserIdentifier estefade mikone
```

```csharp
// BAD: transaction-e business faghat to hub-e, bedun-e tartib-e commit-e DB
public async Task Approve() { await hub.Clients...; await db.SaveChanges(); }

// GOOD: avval save kon, ba'd notify kon (ya ba'd az commit-e UoW)
```

```csharp
// BAD: farz mikoni delivery hatman anjam mishe
await Clients.Group(g).ImportantMoneyEvent(...);
// GOOD: avval persist kon + notify kon; client khodesh reconcile kone
```

---

## Interview 60s

> «We use SignalR hubs per bounded context. Tickets join a user group from the JWT user id and get pushes via IHubContext after commands. Manual access joins site groups after permission checks. Plate-reader agents use an anonymous hub secured by an API-key hub filter and site groups for policy snapshots. Everything is published behind YARP with WebSocket support; browsers pass JWT as access_token on negotiate.»

---

## Lab — laheze-haye «aha»

1. Bedun-e group join, `Notify` hich asari nadare
2. Permission-e site eshtebah bashe → `JoinSite` silent no-op mishe → hich popup-i nemiad
3. Instance-e dovom-e ACL bedun-e backplane → log-haye zende flaky mishan
4. Agent-i ke apiKey ro to query mifreste → `HubException` migire
5. JWT revoke beshe → negotiate fail mishe; vali socket-e ghadimi momkene hanuz baghi bemune

---

## Resume keywords (ATS)

`SignalR` · `WebSockets` · `real-time` · `IHubContext` · `hub groups` · `IHubFilter` · `server push` · `streaming` · `YARP` · `JWT` · `multi-tenant realtime`

---

## In che chizi-e Day 26 *nist*

- Setup-e client-e FE (`@microsoft/signalr`) — un Day 50-e
- Rahnama-ye omigh-e ops-e Redis backplane — hamun ye gap-e ke bayad ba'dan por she
- Jaygozin-e MassTransit nist
- Jozeiyat-e protocol-haye gRPC-e device-ha — un Day 27-e

---

## Self-test-e sari

1. Format-e group-e ticket chie? → `user:{guid}`
2. Cadence-e push-e zaman chie? → sar-e har taghir-e daghighe-ye Tehran
3. Auth-e VehiclePolicy chie? → header-e API key + filter
4. Check-e join-e ManualAccess chie? → permission-haye ba prefix-e site
5. Chi khas-e Baskool-e? → `ChannelReader` + COM
6. Pol-e SSM chie? → gRPC stream → `IAsyncEnumerable`
7. Smell-e scale-e asli chie? → backplane nadarim
8. JWT ru-ye WS chetori mire? → query/cookie to `OnMessageReceived`
9. Isolation-e DeviceHub chetorie? → `Clients.All` (za'if-e)
10. Push key vaght anjam mishe? → ba'd az write, az tarigh-e notifier/popup service

Age 8/10 ya bishtar dorost bud → beri sar-e Day 27.

---

## Checklist-e nahaei

- [ ] Fargh-e Hub va IHubContext
- [ ] 9 hub + model-e auth-e har kodum
- [ ] Naghshe-ye group-ha
- [ ] Catch-all-e YARP
- [ ] Jaryan-e API key to filter
- [ ] Mahdudiyat-e scale-out
- [ ] Bullet-haye resume

---

## Extra — andaze-ye message va backpressure

DTO-haye manual access aks-e pelak/mashin ro be soorat-e data-URL to khodeshun jasazi mikonan. Vaghti chand ta operator hamzaman aks-haye bozorg migiran, mesre va farim-e WS ro por mikone. Rahkar-ha: faghat id befrest va FE khodesh aks ro az tarigh-e HTTP begire; compress kon; ya limit-e size bezar. Hub-haye streaming (SSM/Baskool) az channel-e unbounded (`CreateUnbounded`) estefade mikonan — age consumer kond bashe, memory ziad mishe — in ye smell-e mohem-e baraye production ke bayad be `CreateBounded` (ba policy-e wait ya drop) taghir kone.

---

## Extra — tartib (ordering)

SignalR tartib-e global beyn-e hub-ha ro tazmin nemikone. Dakhel-e ye connection, ma'mulan har invocation be tartib mire. Age do ta notify (masalan Requested ba'd Resolved) az ye masir-e server be tartib await beshan, tartibeshun hefz mishe — bazam UI bayad idempotent tarahi she (masalan `Resolved`-i ke `Requested`-e nashenakhte dare bayad refetch kone, na crash).

---

## Extra — test kardan-e hub-ha

- Unit: helper-haye naming-e group va check-e permission ro joda kon va test kon
- Integration: `WebApplicationFactory` + connect-e client-e SignalR (sangin-tar-e)
- Contract: mottma'en sho esm-e method-haye `ITicketHubClient` ba `.on('TicketUpdated')`-e FE ye-san-e — **casing** ro yadet nare: serializer-e default JSON camelCase-e, FE ham ma'mulan az esm-e camelCase estefade mikone — tanzimat-e serializer ro check kon

---

## Extra — protocol va tanzimat-e timeout

**Protocol:** be default, SignalR az JSON estefade mikone (hamun ke Hub method-ha va client contract-ha ba camelCase serialize mishan). Ye protocol-e dge ham hast be esm-e **MessagePack** (`Microsoft.AspNetCore.SignalR.Protocols.MessagePack`) ke binary-e va sabok-tar-e vali debug-esh sakht-tar-e — age ye service payload-e sangin ya throughput-e ziad dasht, arzesh-e barresi dare, vali chon binary-e, az browser DevTools mostaghim nemishe khund.

**Timeout-ha:** se ta config-e mohem hast ke to Dejban ma'mulan default mimune, vali baraye production khubie beduni:

```csharp
services.AddSignalR(options =>
{
    options.KeepAliveInterval = TimeSpan.FromSeconds(15);      // har chand vaght ping mifreste
    options.ClientTimeoutInterval = TimeSpan.FromSeconds(30);  // che modat bedun-e javab, connection dead hesab mishe
    options.HandshakeTimeout = TimeSpan.FromSeconds(15);       // che modat baraye handshake-e avaliye vaght dari
    options.EnableDetailedErrors = false;                      // faghat to dev true kon — vagarna stack trace be client mire
});
```

`ClientTimeoutInterval` bayad hatman az `KeepAliveInterval` bozorg-tar bashe (documentation-e Microsoft pishnahad mide 2 barabar). Age gateway-e YARP ye idle-timeout-e kutah-tar az in-ha dashte bashe, connection ghabl az inke SignalR befahme ghat mishe — pas in do ta bayad ham-khani dashte bashan.

`EnableDetailedErrors` — age true bashe, exception-haye samt-e server (stack trace) mostaghim to `HubException` be client mire; khubie baraye debug-e local vali to production bayad `false` bemune ta etela'at-e dakheli leak nashe.

---

*Day 26 tamum. Ba'di: Day 27 — gRPC (ZK / Tiam / Virdi). Fehrest: [README.md](./README.md).*
