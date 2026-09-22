# Day 07 — YARP Reverse Proxy

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**YARP** (Yet Another Reverse Proxy) library-e Microsoft-e ke reverse proxy ra **dakhele** app-e ASP.NET Core-et misaze. Be jaye inke nginx ya Envoy-e joda dashte bashi, khodesh dakhele haman process-e C# run mishe — va in yani tamam-e middleware-ha, auth, rate-limit, CORS va DI ke dari, mostaghim roye proxy ham kar mikonan. Model-esh aslan 4 ta chiz-e: **Route** (che request-i match she), **Cluster** (pool-e server-ha), **Destination** (address-e vagheyi), va **Transform** (rewrite-e path/header).

To Dejban, Gateway ba YARP **2.3.0** sakhtim ke 7+ microservice ra posht-e **yek URL** makhi mikone: IdentityServer, Dejban API, DCC, ACLServer, RequestTracker, Reporting, GateServer. Auth va rate-limit yekja-an; SignalR hub-ha ba `/{**catch-all}` route mishan; JWT baraye WebSocket az `?access_token=` miad (Day 06). Front-end faghat gateway ra mibine — address-e dakheli service-ha az client makhfi mimune.

---

# BAKHSH-E AVAL: WORLD — YARP to donya

## YARP chiye?

YARP makhfaf-e "Yet Another Reverse Proxy"-e. Microsoft khodesh develop-esh mikone va roye GitHub-e organization-e `dotnet` host shode. Akharin version-e stable alan (Sep 2026) **2.3.0** hast ke ba .NET 8+ kar mikone; open-source-e (MIT), va Microsoft khodesh to Azure va chand service-e dakheli azash estefade mikone.

Yaddasht-e mohem: YARP ye **library**-e, na ye **executable**-e. Yani to khodet ye ASP.NET Core app misazi va YARP ra toosh host mikoni — bar khalaf-e nginx ke ye process-e joda-st. Hamin farq-e koochik, aslan chera auth/CORS/rate-limit-e C#-et ba proxy yeki mishavad.

---

## Reverse proxy be zaban-e sade

Farz kon ye restoran dari ke chand ta ashpaz dare. Moshteri nemifahme kodom ashpaz ghaza-sho misaze — faghat be garson (proxy) sefarsho mide, va garson tasmim migire kodom ashpaz in ghaza ro dar miare. Browser ham haminjoor-e: mostaghim ba microservice sohbat nemikone; faghat Gateway ra mibine.

```
Browser  →  Gateway (YARP)  →  IdentityServer
                              →  Dejban API
                              →  DCC (files)
                              →  ACLServer (devices)
                              →  RequestTracker (tickets)
                              →  Reporting (Stimulsoft)
                              →  GateServer
```

In olgu chand ta maziyat-e vagheyi mide:

1. **Yek URL baraye client** — frontend faghat `https://gateway` ra midoone. Service-ha avaz mishan ya migrate mishan, client khabar nadare.
2. **Auth yekja** — JWT, token revoke, rate limit hame roye Gateway-an. Service-ha mitonan dobare check konan (defense in depth), vali asl-e fard filter inja-st.
3. **CORS yekja** — browser faghat ba Gateway sohbat mikone, pas CORS faghat inja lazem-e.
4. **TLS termination** — client HTTPS mizane; Gateway be service-ha HTTP (dakheli network) mifreste.
5. **Network isolation** — microservice-ha to Docker network-e private-an. Browser na address-eshun ra midone, na mitone bereshun.

### Forward proxy vs reverse proxy

In soal to mosahebe ziad miyad. Farq-eshun injuri-e:

- **Forward proxy** — client azash estefade mikone baraye birun raftan. Masalan VPN/proxy-e shoma baraye internet. Client midune proxy-e; server-e destination aslan nemidune.
- **Reverse proxy** — server-side-e. Client nemidune posht-e URL ye proxy hast. Request miad, proxy entekhab mikone kodom backend javab bede.

YARP reverse proxy-e. Client aslan nemidune Dejban API port-e `5042` roye localhost-e ya Docker DNS-e `http://dejban`.

---

## Chera YARP? Moghayese ba alternative-ha

Soal-e mosahebe: "Chera YARP, na nginx ya Ocelot?" — javab bayad trade-off bashe, na "chon Microsoft gofte."

### YARP vs nginx

nginx C-e, fast, mature, va millions site azash estefade mikonan. Vali vaghti stack-et C#-e, dard-e sar peida mishe:

- Auth-e shoma C#-e (JWT, Redis revoke, cookie). To nginx bayad plugin/Lua benevisi ya `auth_request` be ye sidecar bezani.
- CORS-e shoma C#-e, DI dare, `IConfiguration` mikhone. nginx CORS config-e static-e.
- Rate limit-e shoma per-IP ba `SlidingWindow`-e C# va custom logic. nginx `limit_req` dare, vali custom IP extraction az `X-Forwarded-For` sakht-tar-e.
- SignalR/WebSocket: nginx mitone, vali config-e timeout va upgrade header-esh khaas-e. YARP roye Kestrel-e, WebSocket upgrade native-e.
- Hot reload: YARP `IConfiguration` ra watch mikone → route change bedune restart. nginx bayad `nginx -s reload` bezani.
- Monitoring: YARP to haman ASP.NET pipeline-e — OpenTelemetry, Serilog, health check, hamechiz access dari. nginx log-e joda dare.

Kholase: age hame-ye auth/CORS/rate-limit-et C#-e, manteghi-tar-e proxy-et ham C# bashe. Yek process, yek deployment, yek set tool.

### YARP vs Ocelot

Ocelot ham C#-e va marufe, vali emruz dige entekhab-e aval nist:

- Ocelot **dige maintain nemishe** daqiq (community fork-ha ziad-an, vali original pir shode). YARP **active maintenance** az Microsoft dare.
- Ocelot roye ASP.NET middleware-e, vali design-esh ghadimi-tar-e. YARP modern-e, `IConfiguration`-based, minimal.
- Performance: YARP az `HttpForwarder` estefade mikone ke direct socket-to-socket copy dare. Ocelot overhead-e bishtar.
- Ocelot aggregation built-in dare (chand request ba ham). YARP nadare — bayad khodet handler bezani.

### YARP vs Envoy

Envoy (Google/CNCF) kheli powerful-e va vase sidecar mesh (Istio) ideal-e. Vali:

- Envoy ye process-e joda-st (C++). YARP dakhele app-et-e.
- Envoy baraye Kubernetes service mesh ideal-e. Shoma Docker Compose dari — Envoy overkill-e.
- Envoy xDS API dare baraye dynamic config. YARP `IConfiguration` ya custom `IProxyConfigProvider` dare.

### Kholase table

| feature | nginx | Ocelot | Envoy | **YARP** |
|---|---|---|---|---|
| zaban | C | C# (outdated) | C++ | **C# (Microsoft)** |
| ASP.NET pipeline | na | bale | na | **bale** |
| auth-e C# native | plugin | mahdud | na | **kolle pipeline** |
| SignalR | config sakht | zaif | ghabul | **native Kestrel** |
| hot reload | reload command | config | xDS | **IConfiguration** |
| maintained | bale | nime | bale | **bale (Microsoft)** |
| performance | excellent | medium | excellent | **very good** |

---

## 4 ta mojoodi-e asli-e YARP

Kol-e model-e YARP aslan 4 ta chiz-e. Ina ra hifz kon — mosahebe ashegh-e in tafkik-e, chon neshun mide reverse proxy "magic" nist: yek match, yek pool, yek address, yek rewrite.

### 1. Route

Ye ghanun ke mige: "age request in shekli bud, bereshonesh be folan cluster." Har route field-haye zir ra dare:

- **`RouteId`** — unique name. Mesal: `"visitor-routes-v1"`, `"auth-login-route-v1"`.
- **`ClusterId`** — kodom cluster in ra process kone. Mesal: `"dejban-cluster"`.
- **`Match`** — condition-e match:
  - `Path` — pattern. `/Api/v{apiVersion}/Visitors/{**catch-all}`. In `{apiVersion}` segment-e; `{**catch-all}` baghimande-ye path (shamel `/`).
  - `Methods` — optional. Array-e method. Age nabashe hame match-e; age bashe, faghat on method-ha.
  - `Headers` / `QueryParameters` / `Hosts` — optional (kam estefade; multi-domain).
- **`AuthorizationPolicy`** — `"anonymous"` (skip auth), `"default"` (bayad login), ya custom.
- **`RateLimiterPolicy`** — esm-e rate limit policy.
- **`CorsPolicy`** — override-e CORS per route (kam).
- **`Order`** — priority. Koochik-tar = aval match. Default 0. Mesal: public ticket `Order: -10` ghabl az `ticket-routes-v1` ke `Order` nadare.
- **`Transforms`** — taghir-e request/response.
- **`Metadata`** — custom key-value baraye middleware-e custom.

### 2. Cluster

Grooh-e server-hayi ke "in service" hesab mishan. Masalan `dejban-cluster` yani service-e Dejban. Ye cluster mitone chand ta destination dashte bashe baraye load balancing.

Field-ha-ye asli:

- **`ClusterId`** — unique name (implicit az JSON key).
- **`Destinations`** — dictionary az server-ha.
- **`LoadBalancingPolicy`** — algorithm (zir tozih).
- **`HealthCheck`** — active/passive config.
- **`SessionAffinity`** — sticky session.
- **`HttpClient` / `HttpRequest`** — timeout, SSL, HTTP version, activity timeout.

### 3. Destination

Address-e vagheyi-e yek server dakhele cluster. To local development:

```json
"destination1": {
    "Address": "http://localhost:5042"
}
```

Ya to Docker Compose, Docker DNS resolve mikone:

```json
"destination1": {
    "Address": "http://dejban"
}
```

Age 2 ta destination dashte bashi, YARP load balance mikone beyneshun. Shoma alan **faghat 1** destination per cluster darid (jox baskool) — pas load balancing-e multi-node fa'al nist, vali model-esh amade-st.

### 4. Transform

Taghir-e request ya response ghabl az forward. In ha az mohem-tarin concept-haye YARP-an:

**Request transforms:**

- **`RequestHeaderOriginalHost: true`** — Host header ra avaz nemikone. Be jaye inke destination host (`dejban`) bere, host-e original-e client (`gateway.example.com`) mimone. Chera mohem? Stimulsoft va cookie-ha Host ra baraye generate-e URL estefade mikonan. Age Host avaz beshe, redirect ya cookie domain eshtebah mishe.

- **`RequestHeader X-Forwarded-Proto: Set: https`** — be upstream service mige "client HTTPS umade." Chon hop-e dakheli HTTP-e, server bedune in header fikr mikone request HTTP-e va cookie-e Secure set nemishe, redirect-e HTTPS loop mishe, ya link-e generate-shode HTTP mishe.

- **`PathRemovePrefix: /dejbanscalar`** — prefix-e path ra hazf mikone. Request `/dejbanscalar/openapi/v1.json` mishe `/openapi/v1.json` vaghti be Dejban mire. Baraye Scalar API docs ke har service path-e khodesh dare.

- **`PathPattern: /timeserverhub/{**catch-all}`** — kole path ra rewrite mikone. Request `/Api/v1/timeserverhub/negotiate` mishe `/timeserverhub/negotiate`. Baraye SignalR hub-ha ke API version to path-eshan nist.

**Response transforms (kam estefade):**

- `ResponseHeader` — header be response ezafe/avaz kon.
- `ResponseTrailer` — trailer header.

**Request body transform (advanced, shoma nadarid):**

- Body ra midstream avaz kon. Masalan header inject to HTML. Rare use case.

---

## Match algorithm — YARP chejori tasmim migire

Vaghti request miad, YARP in tartib ra check mikone:

1. **Hame-ye route-ha ke pattern match mikonan** ra peida mikone.
2. Age **chand route match** kone:
   - **`Order`** — adad-e koochik-tar barande-ye aval.
   - **Path specificity** — path-e daghigh-tar az catch-all barande-ye. `/Contractors/SetBoardMembers` barande roye `/Contractors/{**catch-all}`.
   - **Methods** — age method-e khaasi set shode va request match-e, in route ra tarjih midahad.
3. Age **hich route nakhore** → YARP 404 ya next middleware.

Masalan Contractors 3 route dare:

```
1. POST /Contractors/SetBoardMembers  →  dejban-cluster
2. POST/PUT/PATCH/DELETE /Contractors/{**catch-all}  →  identity-server-cluster
3. GET /Contractors/{**catch-all}  →  dejban-cluster
```

Request `POST /Contractors/SetBoardMembers`:
- Route 1: path exact match + POST → **barande**
- Route 2: path match (catch-all) + POST → ham match vali specific-tar bude route 1

Request `GET /Contractors/123`:
- Route 1: path namatch (SetBoardMembers ≠ 123)
- Route 2: method na (GET nist to list)
- Route 3: path match + GET → **barande**

Request `DELETE /Contractors/123`:
- Route 1: namatch
- Route 2: path match + DELETE to list → **barande**
- Route 3: method na (faghat GET)

In **method-based routing**-e — ye resource (`Contractors`) beyn-e **do service** tekke shode based on HTTP method. Frontend aslan nemifahme posht 2 service-e.

### `{**catch-all}` vs `{segment}`

- `{segment}` — yek segment (bedune `/`). `/api/{version}/Auth` → `v1` match, `v1/extra` **na**.
- `{**catch-all}` — baghimande-ye path shamel `/`. `/Auth/{**catch-all}` → `Login`, `Login/extra/path`, hamechiz match.

`{apiVersion}` to path YARP baraye **faghat segment-e** — match mikone vali YARP ba maqdar-esh kari nadare. Versioning ra ASP.NET Minimal API handle mikone (Day 02, ruz 15).

---

## AuthorizationPolicy

YARP khodesh policy nemisaze — be system-e Authorization-e ASP.NET delicate mikone. Do ta value-e reserved:

- **`"anonymous"`** — auth skip mishe. Hich check-i nist. Baraye login, refresh, public ticket, Scalar docs, device endpoint (Iclock, PlateReaderEdge, CameraAuth), GateHealth, static asset-haye reporting (js, css, lib).

- **`"default"`** — ASP.NET default policy: bayad **authenticated** bashi. Yani JWT-e valid bayad dashte bashi. Age nadashti → **401 az Gateway**. Request **aslan be microservice nemirese**.

Mitoni custom policy ham tarif koni (masalan `"AdminOnly"` ya `"SuperAdmin"`) — bayad to `AddAuthorization` register koni. Shoma az custom route-level policy estefade nakardid; permission check dakhele handler/endpoint-e (ruz 44).

**Mohem:** `AuthorizationPolicy: "default"` yani **faghat authenticated**. Permission-e daqiq (masalan "mitoni visitor edit koni?") **inja nist** — on dakhele app-e.

---

## Rate limiting roye route

YARP ye field-e `RateLimiterPolicy` dare ke esm-e policy-e ASP.NET ra migire:

```json
"RateLimiterPolicy": "Auth_RateLimiter_PerIp"
```

In policy ra to `Program.cs` / `ServiceCollectionExtensions` ba `AddRateLimiter` tarif mikoni. YARP faghat match mikone "in route in policy ra dare" — logic-e rate limit dakhele ASP.NET-e.

Age rate limit bokhore → **429 Too Many Requests** + `Retry-After` header. Request be microservice **nemirese**.

---

## Load balancing

Vaghti cluster chand destination dare, YARP entekhab mikone kodom javab bede. Algorithm-ha:

| algorithm | chejori | che vaght |
|---|---|---|
| `RoundRobin` | nobat-i: 1, 2, 3, 1, 2, 3 | default, sade |
| `LeastRequests` | kamtarin request-e active | service-e slow/fast mix |
| `Random` | random | simple |
| `PowerOfTwoChoices` | 2 ta random, kamtarin load | balanced, recommended baraye bozorg |
| `FirstAlphabetical` | hamishe avalin (test) | na to production |

Config:

```json
"Clusters": {
    "dejban-cluster": {
        "LoadBalancingPolicy": "RoundRobin",
        "Destinations": {
            "d1": { "Address": "http://dejban-1" },
            "d2": { "Address": "http://dejban-2" }
        }
    }
}
```

Shoma `LoadBalancingPolicy` nadarid chon faghat 1 destination darid. Vali to mosahebe bayad betuni tozih bedi.

---

## Health check

YARP mitone destination-haye down ra az pool in kone:

### Active health check

YARP khodesh ye endpoint (masalan `/health`) ra periodic mizane. Age fail → destination ra "unhealthy" mikone va traffic nemifreste.

```json
"HealthCheck": {
    "Active": {
        "Enabled": true,
        "Interval": "00:00:30",
        "Timeout": "00:00:10",
        "Path": "/health"
    }
}
```

### Passive health check

Connection fail ya timeout → temporary "unhealthy" tag. Bad az muddat-i dobare try.

**Shoma hichkodom ra enable nakardid.** In yani age ye microservice down beshe, YARP hanooz traffic mifreste va 502 Bad Gateway mide. Baraye production-e jedi in smell-e — amma baraye single-instance service (ke hame yek destination-an) fargh-e ziyadi nadare chon alternative nist.

---

## Session affinity (sticky session)

Gahi mikhay request-haye yek client hamisheh be haman server beran. Masalan:

- SignalR WebSocket ke state dare
- Server-side session

YARP session affinity ra ba cookie ya header support mikone:

```json
"SessionAffinity": {
    "Enabled": true,
    "Policy": "Cookie",
    "AffinityKeyName": ".Yarp.Affinity"
}
```

**Shoma estefade nakardid** — service-ha stateless-an (session to Redis, na memory). SignalR hub single-instance-e.

---

## SignalR / WebSocket az posht-e YARP

YARP roye Kestrel-e, pas **WebSocket upgrade native support** dare. Hub-ha ra mesle ye route-e adi tarif mikoni:

```json
"ticket-hub": {
    "ClusterId": "request-tracker-cluster",
    "AuthorizationPolicy": "default",
    "Match": { "Path": "/tickethub/{**catch-all}" }
}
```

Transform nadare — path hamoon mimone. Vaghti browser WebSocket handshake mizane, YARP `Connection: Upgrade` va `Upgrade: websocket` ra forward mikone. Server 101 Switching Protocols javab mide va az inja YARP frame-ha ra relay mikone.

**Auth baraye WebSocket:** browser roye WebSocket handshake header-e custom (Authorization) **nemitone** bezare. Pas JWT bayad az:
- **Cookie** (browser automatic mifreste)
- **Query string** `?access_token=...` (khatarnak — log, Referer)
- `AccessTokenQueryMiddleware` in ra be header copy mikone (bakhsh-e Dejban)

---

## Config per environment

YARP az `IConfiguration` mikhone — haman system-e ASP.NET Core. Yani:

- `appsettings.json` → local development (`localhost:5042`)
- `appsettings.Docker.json` → Docker Compose (`http://dejban`, `http://identityserver`)
- `appsettings.Production.json` → production server

`reloadOnChange: true` — age file-e JSON avaz beshe, YARP route-ha ra **bedune restart** update mikone. In baraye DevOps kheili khoob-e.

Farq-e asli beyn-e local va Docker: **address-e destination**. Logic-e route/match/auth **yeki**-e.

---

## Chizayi ke to YARP vojud dare vali kam estefade mishe (baraye mosahebe va resume)

Ina ra bayad beduni ke hastan, hatta age to Dejban nadarid:

### Custom `IProxyConfigProvider`

Be jaye JSON, route/cluster ra az **DB, Redis, Consul, etcd** load kon. Baraye SaaS ke har tenant route-e khodesh dare. Shoma `LoadFromConfig` (JSON) va `LoadFromMemory` (code) estefade kardid.

### Canary / weighted routing

10% traffic be v2, 90% be v1. Baraye gradual rollout. YARP metadata + custom middleware lazem-e — built-in weight roye destination nist (bar khalaf-e Envoy).

### mTLS (mutual TLS)

Gateway **ham** certificate mikhad, **ham** service-e upstream certificate mikhad. Baraye zero-trust network. Shoma dakheli HTTP-id — mTLS nadarid.

### Direct forwarding (`HttpForwarder`)

Bedune route/cluster model, mostaghim `HttpForwarder.SendAsync(context, destination, ...)` seda bezani. Baraye ye endpoint-e khaas ke logic-e custom mikhad.

### gRPC proxy

YARP mitone gRPC (HTTP/2 h2c) ra ham proxy kone. Shoma gRPC ra mostaghim handle mikonid (TiamGrpcServer, ZKGrpcServer) — az Gateway rad nemishe.

### Body transform

Request ya response body ra modify kon midstream. Masalan HTML response-e upstream ra edit kon va header inject kon. Rare.

### Request header routing

Route ra based on header match kon. Masalan `X-Tenant: acme` → cluster-A, `X-Tenant: beta` → cluster-B.

### Middleware per route

Custom `IProxyPipeline` — middleware-e khaas faghat baraye ye route.

---

# BAKHSH-E DOVOM: DEJBAN — YARP to in proje

## Package va version

Gateway package-e YARP ra az `Directory.Packages.props` migire — version central-e, na per-csproj:

```xml
<PackageReference Include="Yarp.ReverseProxy" Version="2.3.0" />
```

Target: `net10.0`.

---

## Setup to Program.cs

`ApiGateway/Program.cs` in khat-ha YARP ra register mikone:

```csharp
builder.Services.AddReverseProxy()
    .LoadFromMemory(IdentityServerRoutes.routes, [])
    .LoadFromConfig(builder.Configuration.GetSection(ConfigConstants.IdentityServerProxy))
    .LoadFromConfig(builder.Configuration.GetSection(ConfigConstants.RequestTrackerProxy))
    .LoadFromConfig(builder.Configuration.GetSection(ConfigConstants.DCC))
    .LoadFromConfig(builder.Configuration.GetSection(ConfigConstants.ACLServerProxy))
    .LoadFromConfig(builder.Configuration.GetSection(ConfigConstants.DejbanProxy))
    .LoadFromConfig(builder.Configuration.GetSection(ConfigConstants.ReportingProxy))
    .LoadFromConfig(builder.Configuration.GetSection(ConfigConstants.GateServerProxy))
    .LoadFromConfig(builder.Configuration.GetSection(ConfigConstants.PublicFilesProxy));
```

Va akhare pipeline:

```csharp
app.MapReverseProxy();
```

**Nokte-ye mohem:** `LoadFromMemory(IdentityServerRoutes.routes, [])` → age `IdentityServerRoutes.cs` ra baz koni, mibini route-ha **hame comment shodan** va array **khali**-e:

```csharp
public static readonly RouteConfig[] routes = [
    // commented out routes...
];
```

In yani `LoadFromMemory` ba array-e khali seda zade mishe — **dead code**. Route-ha ghablan to C# bude, hame raftand be JSON. In bayad **pak beshe** — smell-e code.

---

## ConfigConstants — esm-e section-ha

```csharp
public const string IdentityServerProxy = "ReverseProxy:IdentityServer";
public const string RequestTrackerProxy = "ReverseProxy:RequestTracker";
public const string DCC                 = "ReverseProxy:DCC";
public const string ACLServerProxy      = "ReverseProxy:ACLServer";
public const string DejbanProxy         = "ReverseProxy:Dejban";
public const string ReportingProxy      = "ReverseProxy:Reporting";
public const string GateServerProxy     = "ReverseProxy:GateServer";
public const string PublicFilesProxy    = "ReverseProxy:PublicFiles";
public const string CameraAuthApi       = "/api/v1/auth/cameraauth";
```

8 ta section-e config, 8 ta group-e route/cluster. Har microservice section-e khodesh dare.

---

## 8 ta section va service-ha-shun

| Section | Service | che chizi-haei proxy mishe |
|---|---|---|
| `IdentityServer` | Auth, Account, Role, Claim, ApiKey, Sites, Units, Positions, UIComponents, Contractors (command), TimeServerHub | login/logout, user management, org structure |
| `RequestTracker` | Requests, Tickets (public + private), TicketHub | ticketing system |
| `DCC` | Files | document/file management |
| `ACLServer` | Devices, Regions, AccessLogs, ACLUsers, ACLServices, ACLCalendars, AccessGroups, VehicleAccessPolicies, Parkings, PlateReaderCameras, Relays, ManualAccess, PlateReaderEdge, DeviceHub, SSMHub, PlateReaderHub, VehiclePolicyHub, ManualAccessHub, Iclock, ACLCards | access control, devices, parking, plate reader |
| `Dejban` | Visitors, Personnels, Vehicles, Armory, Inventory, CashLogistics, SecurityPatrols, WeighBridge, Baskool, + 30 dige | main business logic |
| `Reporting` | Stimulsoft viewer/designer, js/css/lib assets, health | report engine |
| `GateServer` | Gate, GateHealth, GateStatusHub | physical gate control |
| `PublicFiles` | `/files/*` public access | public document links |

In table ra hifz kon — mosahebe "cheghadr microservice dari?" → "7+ service, 8 YARP section, 60+ route."

---

## Naghshe-ye cluster-ha — local vs Docker

| Cluster | Local (appsettings.json) | Docker (appsettings.Docker.json) |
|---|---|---|
| `identity-server-cluster` | `http://localhost:5038` | `http://identityserver` |
| `request-tracker-cluster` | `http://localhost:5039` | `http://requesttracker` |
| `dcc-cluster` | `http://localhost:5043` | `http://dcc` |
| `acl-server-cluster` | `http://localhost:5041` | `http://aclserver` |
| `dejban-cluster` | `http://localhost:5042` | `http://dejban` |
| `dejban-baskool-cluster` | `http://localhost:5053` | `http://host.docker.internal:5053` |
| `reporting-cluster` | `http://localhost:5044` | `http://reporting` |
| `gate-server-cluster` | `http://localhost:5045` | `http://gateserver` |
| `dcc-public-files-cluster` | `http://localhost:5043` | `http://dcc/` |

**Nokte-ye Baskool:** Docker-esh `host.docker.internal:5053` — yani Baskool **dakhele Docker network nist**. Roye host machine run mishe. Chon hardware-e baskool USB ya serial dare ke Docker container nemibine. Gateway in joziat ra az frontend makhfi mikone.

**Nokte-ye DCC double:** `dcc-cluster` (baraye Files API, auth-dar) va `dcc-public-files-cluster` (baraye `/files/*` public, anonymous) — **har do** be haman DCC miran, vali route/auth-eshun farq dare.

---

## Pipeline-e Gateway — tartib-e middleware

In tartib **kheili mohem**-e. Middleware-ha ba in order ejra mishan ghabl az `MapReverseProxy`:

```csharp
// 1. CameraAuth exception — HTTPS redirect skip
app.Use(async (context, next) => {
    if (context.Request.Path.StartsWithSegments("/api/v1/auth/cameraauth"))
    {
        await next();
        return;
    }
    app.UseHttpsRedirection();
    await next();
});

// 2. CORS
app.UseCors();

// 3. Scalar docs (Dev/DockerDev only)
app.MapScalarApiReference(options => { ... });

// 4. Static files ya YARP baraye /files (based on PublicFiles:Provider)

// 5. Rate limiter
app.UseRateLimiter();

// 6. AccessTokenQueryMiddleware — token az query/cookie → header
app.UseMiddleware<AccessTokenQueryMiddleware>();

// 7. Token revoke check (Redis blacklist)
app.UseTokenRevoke();

// 8. JWT Authentication
app.UseAuthentication();

// 9. Authorization
app.UseAuthorization();

// 10. Output cache
app.UseOutputCache();

// 11. Health check endpoint
app.MapGet("/health/reporting-routes", ...);

// 12. MapReverseProxy — YARP inja-st
app.MapReverseProxy();
```

**Chera tartib mohem-e?**

- Rate limiter **ghabl** az auth-e — yani hatta ghabl az inke JWT check she, age IP rate exceed karde, 429 mide. In dorost-e: attacker ke brute-force login mikone bayad ghabl az hame block she.

- `AccessTokenQueryMiddleware` **ghabl** az Authentication — chon aval token ra az query/Referer migire va be header copy mikone, **bad** JWT middleware header ra mikhone. Age order bar'aks bashe, JWT token ra nemibine.

- Authentication **ghabl** az Authorization — bayad aval beshnaset, bad check kone mojavez dare.

- Authorization **ghabl** az MapReverseProxy — yani age route `AuthorizationPolicy: default` dare va JWT-e user motabar nabashe, **aslan be microservice nemirese**. 401 az Gateway.

**Nokte-ye CameraAuth:** doorbin-haye amniati HTTP-an (na HTTPS). HTTPS redirect ina ra loop mikone. Pas baraye in path, redirect skip mishe. Vali in implementation ye **anti-pattern**-e: `UseHttpsRedirection` dakhele ye custom middleware-e dige call mishe. Dorost: `app.UseWhen(ctx => !ctx.Request.Path.StartsWithSegments(...), app => app.UseHttpsRedirection())`.

---

## AccessTokenQueryMiddleware — detail

In middleware ye kare mohem mikone: token va site-id ra az **query string ya Referer** migire va be **header** copy mikone. Chera?

1. **Stimulsoft** reports to `window.open` baz mishan. `window.open` header-e custom **nemitone** befreshe. Pas JWT ra to URL mizarim: `?access_token=...&siteId=...`.

2. **SignalR WebSocket** handshake ham header-e custom support nemikone. Token ra to query bayad.

3. **Report ticket** system: ye `report_ticket` ID to query, middleware az `IReportAccessTicketStore` lookup mikone va access_token ra dar miare.

Code flow:

```csharp
public async Task InvokeAsync(HttpContext context)
{
    // Step 1: az query-e khode request try kon
    await ApplyFromQueryAsync(context, context.Request.Query);

    // Step 2: age hanooz Authorization ya X-Site-Id khali-e,
    //         az Referer header-e request query parse kon
    if (string.IsNullOrWhiteSpace(context.Request.Headers.Authorization) ||
        string.IsNullOrWhiteSpace(context.Request.Headers["X-Site-Id"]))
    {
        var referer = context.Request.Headers.Referer.FirstOrDefault();
        // parse Referer URL query
        // ApplyFromDictionary
    }

    await next(context);
}
```

`ApplyValues` faghat **age header khali bashe** set mikone — override nemikone. Yani age axios `Authorization` frestade bashe, in middleware karish nist.

**Security concern:** token to query → log file, browser history, Referer header-e request-e ba'di. Shoma in ra baraye Stimulsoft/SignalR peda kardid (tradeoff). To mosahebe in risk ra bego.

---

## CORS — configuration-e daqiq

`ServiceCollectionExtensions.cs`:

```csharp
services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyMethod();
        policy.AllowAnyHeader();
        policy.AllowCredentials();
        policy.SetIsOriginAllowed(origin =>
        {
            // Dev/DockerDev: return true (hame origin-ha)
            // Production: list az env variable
            var allowedOriginsEnv = configuration.GetValue<string>("AllowedOrigins");
            return allowedOrigins.Contains(origin);
        });
    });
});
```

**Nokte-haye mohem:**

1. `AllowCredentials` + `AllowAnyOrigin(*)` **mamnoo'**-e to ASP.NET — compile/runtime error. Be hamin dalil `SetIsOriginAllowed` callback estefade shode.

2. Dev hame origin-ha allowed-an (`return true`). In baraye development khub-e vali age Production **eshtebahi** in mode bemoone → har site-e dige ba cookie-e user API-e shoma ra mizane. **Smell-e amniati.**

3. `AllowAnyHeader` yani custom header-haye mesle `Authorization`, `X-Site-Id`, `Accept-Language` to preflight-e OPTIONS allowed-an.

4. `AllowAnyMethod` yani GET, POST, PUT, PATCH, DELETE, OPTIONS hame OK-an.

5. `AllowCredentials` yani browser mitone cookie-e cross-origin ra befreshe (baraye refresh token-e HttpOnly).

6. `Access-Control-Max-Age` **set nashode** — yani browser preflight-e OPTIONS ra cache nemikone va **har POST-e jadid ye OPTIONS-e ezafe dare**. Performance smell-e koochik.

---

## Rate limiting — do sath

### Auth rate limit

```csharp
options.AddPolicy("Auth_RateLimiter_PerIp", httpContext =>
{
    var clientIp = httpContext.Request.Headers["X-Forwarded-For"]
        .FirstOrDefault()?.Split(',')[0].Trim()
        ?? httpContext.Connection.RemoteIpAddress?.ToString()
        ?? "unknown";

    return RateLimitPartition.GetSlidingWindowLimiter(clientIp,
        _ => new SlidingWindowRateLimiterOptions
        {
            PermitLimit = 6,
            Window = TimeSpan.FromSeconds(30),
            SegmentsPerWindow = 6,
            QueueLimit = 0
        });
});
```

**6 request per 30 second per IP** ba sliding window. Roye:
- `auth-login-route-v1`
- `auth-refresh-route-v1`
- `auth-cameraauth-route-v1`
- Public ticket routes (`ticket-public-units`, `ticket-public-create`, `ticket-public-get`, `ticket-public-message`)

**Sliding window** = har 5 saniye ye segment (30/6=5). Smoothing-e traffic. Behtar az fixed window ke edge-e window spike dare.

### Global rate limit

```csharp
options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(httpContext =>
{
    var clientIp = /* same extraction */;
    return RateLimitPartition.GetSlidingWindowLimiter(clientIp,
        _ => new SlidingWindowRateLimiterOptions
        {
            PermitLimit = 500,
            Window = TimeSpan.FromMinutes(1),
            SegmentsPerWindow = 1,
            QueueLimit = 0
        });
});
```

**500 request per minute per IP** — in roye **hame-ye route-ha** apply mishe (jox override-e Auth).

### OnRejected — 429 response

```csharp
options.OnRejected = (context, _) =>
{
    context.HttpContext.Response.Headers.RetryAfter = /* seconds */;
    string errorMessage = currentLanguage == "en-US" 
        ? "Too many requests..." 
        : "تعداد درخواست‌ها بیش از حد مجاز است...";
    context.HttpContext.Response.StatusCode = 429;
    context.HttpContext.Response.WriteAsJsonAsync(new { Title = errorMessage });
};
```

`Retry-After` header mide. Accept-Language check mikone baraye Farsi/English. 429 body-e custom.

### Smell-haye rate limit

1. **IP extraction az `X-Forwarded-For` leftmost bedune `KnownProxies`** — attacker mitone `X-Forwarded-For: fake-ip` header ezafe kone va rate limit ra dor bezane. ASP.NET `ForwardedHeaders` middleware ba `KnownProxies` in ra fix mikone.

2. **Global 500/min** — baraye DataGrid-e bozorg (50 column, sort, filter) + SignalR ke keep-alive dare, momkene kam bashe. Vali baraye aksara-e use case-ha kafi-e.

3. **QueueLimit = 0** — yani vaghti limit bokhori, **foran reject**. Age `QueueLimit > 0` bashe, request-ha saf mishan ta slot azad she.

---

## Scalar API docs

Dev/DockerDev environment:

```csharp
app.MapScalarApiReference(options =>
{
    options.AddDocument("v1", "IdentityServer", routePattern: "/identityserverscalar/openapi/{documentName}.json");
    options.AddDocument("v1", "ACLServer", routePattern: "/aclserverscalar/...");
    options.AddDocument("v1", "DCC", routePattern: "/dccscalar/...");
    options.AddDocument("v1", "Dejban", routePattern: "/dejbanscalar/...");
    options.AddDocument("v1", "Reporting", routePattern: "/reportingscalar/...");
    options.AddDocument("v1", "RequestTracker", routePattern: "/requesttrackerscalar/...");
    options.AddDocument("v1", "GateServer", routePattern: "/gateserverscalar/...");
    options.Servers = [];
    options.WithDefaultHttpClient(ScalarTarget.JavaScript, ScalarClient.Axios);
});
```

Har service OpenAPI-e khodesh ra expose mikone. YARP `/identityserverscalar/{**catch-all}` → identity-server ba `PathRemovePrefix: /identityserverscalar`. Scalar docs hamaro jam mikone.

**Smell:** Scalar route-ha `AuthorizationPolicy: anonymous`-an. To production age in route-ha active bemoonan, har kasi API schema-ye shoma ra mibine. Bayad faghat Dev bashe — va code ham check mikone `IsDevelopment || IsDockerDevelopment`. Vali age environment variable eshtebah set she...

---

## Public files — MinIO vs Local

```json
"PublicFiles": {
    "Provider": "MinIO",
    "Mode": "DccProxy",
    "Bucket": "dcc-files"
}
```

Do mode:

1. **`Provider=Local`** → `UseStaticFiles` az disk (legacy/rollback). File-ha to `/app/public-assets/public` ya local path.
2. **`Provider=MinIO`** → YARP route `/files/{**catch-all}` → DCC API `/api/v1/Files/public/{**catch-all}`. DCC az MinIO fetch mikone.

Frontend hamishe `/files/photo.jpg` mizane — storage posht avaz mishe, URL yeki.

---

## SignalR hub-ha — list-e kamel

| Hub | Cluster | Auth | Chie |
|---|---|---|---|
| `tickethub` | request-tracker | default | ticket updates |
| `ticket-hub-api` (rewrite) | request-tracker | default | versioned path → hub |
| `timeserverhub` (rewrite) | identity-server | default | server time sync |
| `devicehub` | acl-server | default | device status |
| `ssmhub` | acl-server | default | SSM events |
| `platereaderhub` | acl-server | default | plate reader events |
| `vehiclepolicyhub` | acl-server | **anonymous** | vehicle policy push |
| `manualaccesshub` | acl-server | default | manual gate control |
| `baskoolhub` | **dejban-baskool** | default | weighbridge live data |
| `gateStatusHub` | gate-server | **anonymous** | gate status push |

`baskoolhub` cluster-e **joda** dare (`dejban-baskool-cluster`) chon Baskool process joda az Dejban API-e (hardware dependency).

`vehiclepolicyhub` va `gateStatusHub` anonymous-an — chon client-eshun device/kiosk-e ke login nadare.

`ticket-hub-api` va `timeserverhub` **PathPattern transform** daran: versioned API path ra be hub path convert mikonan.

---

## Olguye talayi: Contractors split — deep dive

In ye pattern-e kheili mohem to architecture-e:

Contractor entity beyn-e **do bounded context** split shode:

- **IdentityServer** — CRUD-e contractor (create, update, delete). Chon contractor entity-e organizational-e.
- **Dejban** — query-e contractor data + `SetBoardMembers` action.

YARP in ra ba **method-based routing** piade sazi karde:

```json
"contractor-setboardmembers-route-v1": {
    "ClusterId": "dejban-cluster",
    "Match": {
        "Path": "/Api/v{apiVersion}/Contractors/SetBoardMembers",
        "Methods": ["POST"]
    }
},
"contractor-command-routes-v1": {
    "ClusterId": "identity-server-cluster",
    "Match": {
        "Path": "/Api/v{apiVersion}/Contractors/{**catch-all}",
        "Methods": ["POST", "PUT", "PATCH", "DELETE"]
    }
},
"contractor-query-routes-v1": {
    "ClusterId": "dejban-cluster",
    "Match": {
        "Path": "/Api/v{apiVersion}/Contractors/{**catch-all}",
        "Methods": ["GET"]
    }
}
```

Tartib-e match mohem-e:
- `SetBoardMembers` path-e exact → barande ghabl az catch-all
- Command (POST/PUT/PATCH/DELETE) → IdentityServer
- Query (GET) → Dejban (ba copy-e contractor data)

Frontend **aslan nemifahme** posht-e 2 service-e. Faghat `/api/v1/Contractors/...` mizane.

Jomle-ye mosahabe: "We split Contractors across bounded contexts — writes go to IdentityServer which owns the entity, reads go to Dejban which has a read-model copy. YARP routes by HTTP method."

---

## Nokte-ye AccessGroups — bug-e copy-paste

To `appsettings.json` (ham local ham Docker), route-e `access-group-routes-v1` in transform ra dare:

```json
"RequestHeader": "X-Forwarded-Proto",
"Set": "http"
```

Hame-ye route-haye dige **`https`** mizaran. In yeki **`http`**. In ba ehtemal-e ziad **bug-e copy-paste**-e. Impact: age upstream service `X-Forwarded-Proto` ra baraye generate-e URL ya cookie check kone, eshtebah mibine.

---

## Health check endpoint

```csharp
app.MapGet("/health/reporting-routes", (IConfiguration configuration) =>
{
    var routes = configuration.GetSection("Reporting:Routes");
    string[] required = [
        "reporting-js-routes-v1",
        "reporting-css-routes-v1",
        "reporting-lib-routes-v1",
        "reporting-design-routes-v1",
        "reporting-view-routes-v1",
        "reporting-health-assets-route-v1"
    ];
    // check each route exists and has path
    var healthy = details.All(d => d.configured && !string.IsNullOrWhiteSpace(d.path));
    return healthy ? Results.Ok(...) : Results.Json(..., statusCode: 503);
}).AllowAnonymous();
```

**Smell:** config section `"Reporting:Routes"` check mikone, na `"ReverseProxy:Reporting:Routes"`. Age ina match nakonan, health check eshtebah report mikone. Bayad verify koni ke config path dorost-e.

In health check faghat **config ra check mikone** (aya route-ha tarif shodan), na **actual connectivity** be reporting service. Active health check-e YARP behtar bood.

---

## OutputCache

```csharp
services.AddOutputCache(options =>
{
    options.AddPolicy("Default_CachePolicy", 
        builder => builder.Expire(TimeSpan.FromSeconds(20)));
});
```

Policy tarif shode vali **be hich route chasbide nist**. `UseOutputCache` to pipeline hast vali hich route `OutputCachePolicy` nadare. Dead code-e.

Age chasbide bashe, deghat: GET-e authenticated ba `X-Site-Id` = **khatarnak** baraye cache. User A list-e user B ra az cache mibine. Bayad `VaryByHeader("Authorization", "X-Site-Id")` set she. Khamush gozashtan dorost-tar-e ta vaghti ke policy-e kamele naneveshtin.

---

## Smell-ha va bug-ha — list-e kamel

1. **`LoadFromMemory` ba array-e khali** — dead code. Route-haye C# hame comment shodan.
2. **`UseHttpsRedirection` dakhele custom middleware** — anti-pattern. Dorost: `app.UseWhen(...)`.
3. **`X-Forwarded-Proto: http` roye AccessGroups** — bug-e copy-paste. Baghie `https`-an.
4. **Active health check-e YARP nist** — service down → 502 ta timeout.
5. **`X-Forwarded-For` leftmost bedune `KnownProxies`** — IP spoof baraye rate limit.
6. **Baskool kharej az Docker network** — `host.docker.internal` workaround.
7. **Scalar docs anonymous** — production leak risk.
8. **Global 500/min** — baraye DataGrid + SignalR momkene kam bashe.
9. **Reporting health route config path** — `Reporting:Routes` check mikone, bayad `ReverseProxy:Reporting:Routes` bashe.
10. **OutputCache wired amma be hich route chasbide nist** — dead config.
11. **`Access-Control-Max-Age` set nashode** — har request-e nonsimple ye OPTIONS-e ezafe.
12. **Token to query string** — log/Referer leak (tradeoff-e Stimulsoft/SignalR).
13. **CORS Dev = allow all** — age production leak kone, har origin allowed-e.
14. **Na canary, na mTLS, na active health** — baraye single-instance OK, baraye scale nadarid.

---

## Chi **nadari** (ta resume dorough nashe)

- Custom `IProxyConfigProvider` (az DB/Consul)
- mTLS beyn-e Gateway va service
- Body transform
- Canary / weighted routing
- WAF (Web Application Firewall)
- gRPC proxy
- Active/passive health check
- Session affinity
- Request header-based routing
- Multi-destination load balancing (1 dest per cluster)
- `Access-Control-Max-Age` cache

---

## 20 soal-e mosahabe — ba javab-e kamel

**1. YARP chie?**
Reverse proxy library-e Microsoft-e ke dakhele ASP.NET Core run mishe. Route/cluster/transform model.

**2. Chera YARP na nginx?**
Auth/CORS/rate-limit-emun C#-e. YARP dakhele haman pipeline-e. SignalR native. Hot reload az JSON.

**3. Route vs Cluster vs Destination?**
Route = match rule (path/method → cluster). Cluster = group-e server. Destination = actual address.

**4. Chand LoadFromConfig chera?**
Har service section-e joda dare. Modularity — team-e dige mitone route-e khodesh ra maintain kone.

**5. `{**catch-all}` chie?**
Baghimande-ye path shamel `/`. `/Auth/{**catch-all}` → `Login`, `Login/Sub/Path`, hamechiz.

**6. Order chi kar mikone?**
Priority-e route. Koochik-tar aval match mishe. Public ticket `Order: -10` ghabl az `ticket-routes-v1`.

**7. `anonymous` vs `default`?**
`anonymous` = skip auth. `default` = bayad authenticated bashi (JWT valid).

**8. Transform chie?**
Rewrite-e path/header ghabl az forward. `PathRemovePrefix`, `OriginalHost`, `X-Forwarded-Proto`.

**9. X-Forwarded-Proto chera?**
Hop-e dakheli HTTP-e, client HTTPS umade. Cookie-e Secure va URL generation be in vabaste-st.

**10. OriginalHost chera?**
Cookie domain va Stimulsoft URL-ha host-e public mikhadan, na `http://dejban`.

**11. SignalR chejori proxy mishe?**
WebSocket upgrade native roye Kestrel. Route mesle adi. Auth az cookie/query.

**12. 401 koja sakhte mishe?**
Gateway — ghabl az MapReverseProxy. Route `default` + JWT invalid = 401. Microservice aslan request ra nemibine.

**13. 502 yani chi?**
YARP be upstream connect nashode. Destination down, DNS ghalat, ya service crash.

**14. Rate limit koja-st?**
`UseRateLimiter` + `RateLimiterPolicy` roye route. Auth: 6/30s. Global: 500/1min.

**15. Load balancing dari?**
Na — ye destination per cluster. Vali YARP RoundRobin, LeastRequests, etc. dare.

**16. Health check YARP?**
Active/passive support dare — ma enable nakardim. Service down → 502.

**17. BFF-e?**
Na, transparent proxy. BFF logic-e aggregate/transform dare (masalan chand API call → 1 response).

**18. Ocelot vs YARP?**
YARP official, maintained, faster. Ocelot outdated.

**19. Contractors chera split?**
Bounded context. IdentityServer own mikone (create/update/delete). Dejban read model-e copy dare + SetBoardMembers action. YARP ba method routing joda mikone.

**20. Reload config?**
`IConfiguration` reloadOnChange. JSON avaz → route-ha live update bedune restart.

---

## Resume (English)

**short:**

> Built an ASP.NET Core API Gateway with YARP 2.3 that fronts 7+ microservices (60+ routes, 9 clusters), enforcing JWT auth, Redis token revocation, CORS with credentials, and per-IP rate limiting (sliding window) at the edge. Config-driven routes with path/header transforms, method-based split routing for cross-service resources, and native SignalR/WebSocket proxying.

**bullets:**

- Configured 8 YARP route sections for Identity, Tickets, Files, Access Control, Business Logic, Reporting, Gate, and Public Files with per-environment destinations (localhost / Docker DNS)
- Enforced auth at the edge: anonymous for login/device/public endpoints, default JWT for all others — microservices never see unauthenticated traffic
- Implemented method-based routing to split Contractors across bounded contexts (reads → Dejban, writes → IdentityServer)
- Built AccessTokenQueryMiddleware for Stimulsoft/SignalR scenarios requiring token in query string
- Designed dual rate limiting: 6 req/30s on auth endpoints, 500 req/min global, sliding window per IP

**skills:** `YARP 2.3, ASP.NET Core, Reverse Proxy, API Gateway, Rate Limiting, CORS, JWT, SignalR, Docker, Kestrel`

---

## Checklist-e mastery

Bedune search to IDE, mituni in-ha ra neshun bedi?

- [ ] `AddReverseProxy` va `MapReverseProxy` to `Program.cs`
- [ ] `LoadFromConfig` baraye 8 section — `ConfigConstants.cs` ra baz kon
- [ ] `LoadFromMemory` ba array-e khali — dead code
- [ ] `appsettings.json` vs `appsettings.Docker.json` farq-e destination
- [ ] Contractors 3 route: SetBoardMembers → Dejban, Command → Identity, Query → Dejban
- [ ] `Order: -10` roye public ticket routes
- [ ] `PathRemovePrefix` baraye Scalar routes
- [ ] `PathPattern` baraye timeserverhub va tickethub rewrite
- [ ] `AuthorizationPolicy: anonymous` roye login/refresh/Iclock/PlateReaderEdge/static assets
- [ ] `RateLimiterPolicy: Auth_RateLimiter_PerIp` roye login/refresh/camera/public tickets
- [ ] CORS `SetIsOriginAllowed` — Dev vs Prod
- [ ] `AccessTokenQueryMiddleware` — query → header copy
- [ ] `X-Forwarded-Proto: https` (va http roye AccessGroups — bug)
- [ ] `RequestHeaderOriginalHost: true` — hame routes
- [ ] Baskool cluster-e joda ba `host.docker.internal`
- [ ] PublicFiles MinIO vs Local switch
- [ ] `Default_CachePolicy` — wired, na chasbide
- [ ] Pipeline tartib: CORS → RateLimiter → TokenQuery → TokenRevoke → Auth → AuthZ → Cache → YARP
- [ ] Health endpoint `Reporting:Routes` (na `ReverseProxy:Reporting:Routes`)
- [ ] Scalar docs faghat Dev/DockerDev

---

## File-haye mohem

| chi | koja |
|---|---|
| YARP package version | `Directory.Packages.props` (2.3.0) |
| csproj | `ApiGateway/ApiGateway.csproj` |
| Pipeline + bootstrap | `ApiGateway/Program.cs` |
| Config section names | `ApiGateway/Abstractions/Constants/ConfigConstants.cs` |
| CORS + rate limiter + cache | `ApiGateway/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| In-memory routes (dead) | `ApiGateway/Abstractions/DynamicRoutes/IdentityServerRoutes.cs` |
| Routes local | `ApiGateway/appsettings.json` |
| Routes Docker | `ApiGateway/appsettings.Docker.json` |
| Global config (Redis, JWT) | `GlobalAppsettings/globalAppsettings.json` |
| JWT setup | `Common/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Token query middleware | `Common/Authentication/AccessTokenQueryMiddleware.cs` |
| Token revoke middleware | `Common/Authentication/TokenRevokeMiddleware.cs` |
| Report ticket store | `Common/Reporting/IReportAccessTicketStore.cs` |

---

Day 07 tamum. Ba'd: Day 08 — System Design. Fehrest: [README.md](./README.md).
