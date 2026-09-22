# Day 33 — OpenAPI + Scalar

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**OpenAPI** = standard-e tosiif-e HTTP API (ghadiman «Swagger spec»). Ye JSON/YAML mige: kodom path, method, body, response, auth.  
**Scalar** = UI-ye modern baraye *khandan* va *test* kardan-e un document (jaygozin-e Swagger UI to in proje).

To Dejban:

1. Har microservice (`AddOpenApi` + `MapOpenApi`) document JSON midahad — **faghat** Development / DockerDevelopment.  
2. **ApiGateway** `MapScalarApiReference` midahad — ye UI ke **7 document** (Identity, ACL, DCC, Dejban, Reporting, RequestTracker, Gate) ro az tarigh-e YARP path-haye `/*scalar/openapi/...` load mikone.  
3. Package-ha: `Microsoft.AspNetCore.OpenApi` 10 · `Microsoft.OpenApi` 2.10 · `Scalar.AspNetCore` 2.11.  
4. **Swashbuckle / Swagger UI nist** — olgu-ye .NET 9/10 native OpenApi + Scalar.

**Band-e gharardad-e jadid:** tozihat ravoontar va sade-tar — bishtar «farz kon / yani chi / chera».

---

# BAKHSH-E AVAL: WORLD — OpenAPI chie?

## Farz kon — menu-ye restaurant vs ashpazkhune

Ashpazkhune = code-e API (controller / minimal endpoint).  
**Menu** = OpenAPI document — mosafer (FE / mobile / partner) midune chi order kone bedune beravad ashpazkhune.

Bedune menu: «endpoint chi bud? body chi? 401 chi?» → Slack / hafze.  
Ba menu: contract-e rasmi; codegen; UI test.

---

## OpenAPI vs Swagger — esm-ha

| esm | ma'ni-ye emruzi |
|---|---|
| **OpenAPI Specification** | standard (3.0 / 3.1) — format document |
| **Swagger** | brand-e ghadimi; mardom hanuz migan «swagger.json» |
| **Swagger UI** | ye UI baraye document |
| **Swashbuckle** | library .NET classic ke swagger generate + UI midad |
| **Microsoft.AspNetCore.OpenApi** | generate native to ASP.NET Core 8+ / 9 / 10 |
| **Scalar** | UI-ye digar (ziba, multi-document, code snippet) |

**Yani chi?** To mosahebe: «We use OpenAPI documents with Scalar UI, not Swashbuckle.»

---

## Document chie dakhelesh?

Mesal-e zehnii:

```json
{
  "openapi": "3.0.x",
  "info": { "title": "Dejban", "version": "v1" },
  "paths": {
    "/api/v1/personnels": {
      "get": {
        "tags": ["Personnels"],
        "parameters": [],
        "responses": { "200": { "description": "OK" } }
      }
    }
  },
  "components": {
    "schemas": { },
    "securitySchemes": { }
  }
}
```

| bakhsh | ma'ni |
|---|---|
| paths | URL + verb |
| operation | yek GET/POST |
| tags | group to UI |
| schemas | DTO / body shape |
| securitySchemes | Bearer JWT, … |

---

## Chera OpenAPI to team?

1. **Kashf** — developer jadid endpoint mibine  
2. **Try-it** — az UI request mizane (ba token)  
3. **Contract** — FE midune field chi-e (kamtar «chizi avaz shod?»)  
4. **Codegen** (optional) — client az spec  
5. **Gate** — review: metadata kam = smell  

**Chera prod mamulan off?**  
Surface attack + info leak (internal path-ha) + niaz nist baraye user-e nahayi.

---

## Scalar vs Swagger UI (WORLD)

| | Swagger UI | Scalar |
|---|---|---|
| look | classic | modern |
| multi-doc | sakht-tar | `AddDocument` asun |
| code samples | kam | Axios/JS default (Dejban) |
| ASP.NET package | Swashbuckle | `Scalar.AspNetCore` |

Har do **consumer**-e OpenAPI JSON-an. Generate = OpenApi middleware; UI = Scalar ya Swagger UI.

---

## Minimal APIs + OpenAPI (.NET)

Classic controller: attribute `[Produces]` / Swashbuckle reflection.  
Minimal API: metadata az `TypedResults`, `.WithTags()`, `.WithName()`, `.Produces<T>()`.

**Yani chi?** Age endpoint metadata nadahad, document *thin* mishe — UI hast ama body schema za'if. Day 17 in ro zade.

---

# BAKHSH-E DOVOM: DEJBAN — chejori peiyade shode?

## Naqshe-ye yek negah

```
[Browser]
    │  GET /scalar  (ya path-e default Scalar UI)
    ▼
[ApiGateway]  MapScalarApiReference
    │  UI fetch mikone:
    │  /dejbanscalar/openapi/v1.json
    │  /identityserverscalar/openapi/v1.json
    │  …
    ▼
[YARP]  PathRemovePrefix /dejbanscalar
    │  → /openapi/v1.json
    ▼
[Dejban.Api]  MapOpenApi()   ← faghat Dev / DockerDevelopment
```

**Yani chi be zaban-e adam?**  
Yek «ketabkhune» ru-ye Gateway: az unja hame service-ha ro mikhuni. Har service khodesh JSON misaze; Gateway UI + proxy.

---

## Qesmat 1 — Microservice: AddOpenApi + MapOpenApi

### Dejban.Api

```csharp
// DI
services.AddScalarDocumentation(); // AddOpenApi + bind Scalar options

// Pipeline — faqat non-prod-ish
if (Development || DockerDevelopment)
{
    app.MapOpenApi();
}
```

`ScalarExtensions.cs`:

```csharp
services.AddOpenApi();
services.AddOptions<ScalarOptions>().BindConfiguration("Scalar");
```

**Chera AddOpenApi to DI va MapOpenApi to pipeline?**  
Add = register document generator. Map = endpoint HTTP ke JSON midahad (default ≈ `/openapi/{documentName}.json`).

### Hamin olgu digar service-ha

Identity, ACL, DCC, Reporting, RequestTracker, Gate:

```csharp
services.AddOpenApi();
services.AddOptions<ScalarOptions>().BindConfiguration(ConfigConstants.ScalarOptions); // "Scalar"
// …
app.MapOpenApi(); // under same env guard
```

**Yani chi?** Har bounded context document-e **khodesh**-e — na yek mega-spec baraye hame monorepo. Multi-service = multi-document (Scalar Gateway).

### Env guard — mohem

```csharp
Development || DockerDevelopment → MapOpenApi
Production → nadare
```

**Chera?** Amniat + surface kam. Scalar UI ham faqat to Gateway ba hamin env.

---

## Qesmat 2 — ApiGateway: Scalar UI + multi-document

```csharp
if (Development || DockerDevelopment)
{
    app.MapScalarApiReference(options =>
    {
        options.AddDocument("v1", "IdentityServer",
            routePattern: "/identityserverscalar/openapi/{documentName}.json");
        options.AddDocument("v1", "ACLServer",
            routePattern: "/aclserverscalar/openapi/{documentName}.json");
        options.AddDocument("v1", "DCC",
            routePattern: "/dccscalar/openapi/{documentName}.json");
        options.AddDocument("v1", "Dejban",
            routePattern: "/dejbanscalar/openapi/{documentName}.json");
        options.AddDocument("v1", "Reporting",
            routePattern: "/reportingscalar/openapi/{documentName}.json");
        options.AddDocument("v1", "RequestTracker",
            routePattern: "/requesttrackerscalar/openapi/{documentName}.json");
        options.AddDocument("v1", "GateServer",
            routePattern: "/gateserverscalar/openapi/{documentName}.json");

        options.Servers = [];
        options.WithDefaultHttpClient(ScalarTarget.JavaScript, ScalarClient.Axios);
    });
}
```

### Yani chi, option be option?

| option | ma'ni-ye sade |
|---|---|
| `AddDocument("v1", "Dejban", routePattern: …)` | ye tab/document to UI; JSON az in URL |
| `routePattern` | koja OpenAPI JSON biad (az did-e browser = Gateway URL) |
| `Servers = []` | server list khali — Try-it relative / current host (Gateway) |
| `WithDefaultHttpClient(JS, Axios)` | snippet code pishfarz Axios — FE stack nazdik |

**Farz kon:** developer Gateway `https://localhost:7xxx` baz mikone → Scalar → tab Dejban → operation mizane. Request miravad be **Gateway** (YARP) → Dejban. Yani haman path-i ke FE estefade mikone — realistic-tar az hit mostaghim service port.

---

## Qesmat 3 — YARP scalar routes (glue)

Mesal `dejban-scalar-route-v1`:

```
Match: /dejbanscalar/{**catch-all}
AuthorizationPolicy: anonymous
Transform: PathRemovePrefix /dejbanscalar
→ cluster Dejban
```

**Flow-e request document:**

1. Browser: `GET /dejbanscalar/openapi/v1.json`  
2. YARP prefix pak → `GET /openapi/v1.json` be Dejban  
3. `MapOpenApi` javab JSON  

**Chera prefix joda (`dejbanscalar` na `dejban`)?**  
Ta route-haye API asli (`/Api/v1/...`) ba route-e doc conflict nakonan; va har service namespace-e doc-e khodesh dashte bashe.

**Anonymous:** document to Dev bedune JWT load she — UI baz she. (Prod off.)

Hamin olgu: `identityserverscalar`, `aclserverscalar`, `dccscalar`, `reportingscalar`, `requesttrackerscalar`, `gateserverscalar`.

---

## Qesmat 4 — Package versions (repo)

`Directory.Packages.props`:

| package | version |
|---|---|
| Microsoft.AspNetCore.OpenApi | 10.0.0 |
| Microsoft.OpenApi | 2.10.0 |
| Scalar.AspNetCore | 2.11.0 |

**Yani chi?** Stack .NET 10-aligned. ApiGateway **faghat** Scalar package dare (UI); OpenApi generate ro microservice-ha mikonan. Gateway khodesh `AddOpenApi` / `MapOpenApi` nadare — proxy + UI.

---

## Farz kon — sobh-e developer (dastan-e kamel)

1. Compose + Gateway + Dejban up (DockerDevelopment ya Dev).  
2. Browser → Scalar UI ro-ye Gateway.  
3. Tab **Dejban** entekhab.  
4. Endpoint Personnels → Authorize (JWT az Identity Login) → Try.  
5. Age 401: token / blacklist / tenant header (`X-Site-Id` Day 16).  
6. Age 404 document: service MapOpenApi off-e (env ghalat) ya YARP route typo.

**Yani:** Scalar = postman-lite-e stack; na jaygozin-e test-e automated.

---

## Ertebat ba Minimal APIs (Day 17) — metadata

Document *khub* niaz dare:

- `.WithTags("Personnels")` → group to Scalar  
- `.WithName("GetPersonnels")` → operationId  
- `TypedResults.Ok<T>()` / `.Produces<T>()` → schema  
- Auth metadata → security requirement  

**Dejban daqiq:** Presentation layer bishtar `.WithTags(Tags.Personnels)` / `Tags.Visitors` / `Tags.Assets` mizane; ba'zija `.WithName("GetVisitReservations")` ham hast. `MapGroup("/api/v{version:apiVersion}/...")` + tag = Scalar group + versioned path.

**Smell-e honest:** chand sad endpoint; ba'ziha metadata kamtar → Scalar list dare ama schema thin. Improve = discipline roye `IEndpoint` map.

Controller-based service-ha (Identity, ACL, …): reflection az action + attributes — classic.

---

## Farz kon — WithTags chejori tu UI miad

Code:

```csharp
app.MapGroup("/api/v{version:apiVersion}/Reservations")
   .WithTags(Tags.VisitReservations);
// …
}).WithName("GetVisitReservations")
```

**Yani chi?**  
To Scalar tab Dejban, ye group be esm VisitReservations mibini; operationId = GetVisitReservations. Bedune tag, hame chiz zir-e default / clutter. Bedune WithName, esm-e generated za'if-tar baraye codegen.

**Chera Tags class per module?**  
Typo kam; rename refactor asun; OpenAPI consistent.

---

## OpenAPI ≠ health ≠ traces

| tool | soal |
|---|---|
| OpenAPI/Scalar | «API che shekli dare?» |
| Health (Day 31) | «zende-am?» |
| Serilog/OTel (Day 30) | «chi shod to request?» |

Se ta complementary.

---

## Smell-ha (kamel + tozih)

1. **Prod on by mistake** — info leak; guard env check kon  
2. **Document stale** — code avaz, metadata na → FE gij  
3. **Thin schemas** — TypedResults / Produces kam  
4. **Multi-doc confusion** — developer wrong tab (Identity vs Dejban)  
5. **Servers = []** — Try-it be host-e eshtebah age UI az URL odd baz she  
6. **Anonymous scalar routes** — OK Dev; prod nabayad Map she  
7. **CORS** — Scalar az Gateway; OK. Mostaghim service port shayad CORS dard  
8. **Version document "v1"** vs URL `api/v{version}` — do concept; sync zehni  
9. **Gateway Scalar bedune service up** — tab fail load JSON  
10. **Auth Try-it** — Bearer + shayad `X-Site-Id` faramush  
11. **No Swagger UI** — hire jadid «swagger» migarde; begu Scalar  
12. **ScalarOptions bind** — config section shayad khali; defaults OK  

---

## Debug checklist (sade)

1. Env Development / DockerDevelopment?  
2. `GET /dejbanscalar/openapi/v1.json` az Gateway — 200 JSON?  
3. Mostaghim Dejban `/openapi/v1.json` — kar mikone?  
4. YARP PathRemovePrefix dorost?  
5. Service up / healthy?  
6. Scalar UI path default — docs Scalar.AspNetCore  
7. JWT Try-it — token expire / blacklist (Day 06)?  
8. Tenant header?  
9. Endpoint to document nist — metadata / MapEndpoints?  

---

## 25 soal-e mosahebe

1. OpenAPI chie?  
2. Swagger vs OpenAPI?  
3. Scalar chie?  
4. Chera Swashbuckle na?  
5. `AddOpenApi` vs `MapOpenApi`?  
6. Chera faqat Dev?  
7. Multi-document chera?  
8. `AddDocument` + routePattern?  
9. YARP `*scalar` prefix chera?  
10. PathRemovePrefix yani?  
11. `Servers = []` chera?  
12. Axios default snippet chera?  
13. ApiGateway khodesh OpenApi generate mikone?  
14. Package versions?  
15. Tags / WithName naqsh?  
16. TypedResults va schema?  
17. Anonymous scalar route risk?  
18. FE chejori az OpenAPI sood?  
19. OpenAPI vs health?  
20. Document v1 vs api versioning?  
21. Controller vs Minimal OpenAPI?  
22. Prod enable smell?  
23. Try-it 401 debug?  
24. Codegen optional?  
25. Resume one-liner?

---

## Senario-ha (ba tozih-e ravoon)

### A) FE developer endpoint jadid mikhad

Scalar → Dejban → tag → request/response shape.  
**Yani:** self-serve discovery.

### B) DockerDevelopment, Production off

Compose docker-dev → Scalar baz. Deploy prod → MapOpenApi/Scalar nist.  
**Yani:** env guard kar mikone.

### C) Dejban down, Gateway up

Scalar UI miad; tab Dejban JSON fail.  
**Yani:** UI ≠ service health; check route + service.

### D) Typo `dejbanscalar` vs `dejban-scalar`

404.  
**Yani:** prefix must match AddDocument + YARP.

### E) Try-it bedune X-Site-Id

Multi-tenant fail / empty.  
**Yani:** document shayad header ra highlight nakone — tribal knowledge (Day 16).

---

## Mini lab

1. Open `ApiGateway/Program.cs` — 7 AddDocument bekhon  
2. `appsettings` YARP `dejban-scalar-route-v1`  
3. Dejban `MapOpenApi` env if  
4. `ScalarExtensions` / Identity `AddOpenApi`  
5. Browser Gateway Scalar — tab switch  
6. curl `/dejbanscalar/openapi/v1.json` | head  
7. Grep Swashbuckle — expect empty  

---

## Resume

**kutah:**

> Documented a multi-service ASP.NET Core 10 stack with native `Microsoft.AspNetCore.OpenApi` per microservice and a Scalar UI on the YARP ApiGateway that aggregates seven OpenAPI documents via dedicated `*scalar` reverse-proxy routes, enabled only in Development/DockerDevelopment.

**bullet-ha:**

- Registered `AddOpenApi` / `MapOpenApi` on Identity, ACL, DCC, Dejban, Reporting, RequestTracker, Gate  
- Hosted Scalar multi-document UI on ApiGateway with Axios snippets and empty Servers for gateway-relative try-it  
- Wired anonymous YARP routes (`/dejbanscalar/...`) with PathRemovePrefix to each service’s `/openapi/{document}.json`  

**skill-ha:** `OpenAPI, Scalar, Microsoft.AspNetCore.OpenApi, YARP, API documentation, ASP.NET Core 10, Minimal APIs, Developer Experience`

---

## File-haye mohem

| chi | koja |
|---|---|
| Scalar UI multi-doc | `ApiGateway/Program.cs` |
| YARP scalar routes | `ApiGateway/appsettings*.json` (`*-scalar-route-v1`) |
| Dejban OpenApi DI | `Dejban.Api/Extensions/ScalarExtensions.cs` |
| Dejban MapOpenApi | `Dejban.Api/Program.cs` |
| Digar services | `*/Abstractions/Extensions/ServiceCollectionExtensions.cs` + `Program.cs` |
| Packages | `Directory.Packages.props` |
| Constant | `ConfigConstants.ScalarOptions = "Scalar"` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 07 YARP | scalar proxy routes |
| 17 Minimal APIs | tags, metadata, TypedResults |
| 06 JWT | Try-it Authorize |
| 16 Tenancy | X-Site-Id header |
| 01 HTTP/REST | status, verbs to document |
| 31 Health | complementary; reporting-routes health joda |

---

## Chejori digest koni (ravesh-e sade)

1. WORLD menu/restaurant + OpenAPI vs Swagger (15 min)  
2. Microservice Add/MapOpenApi (15 min)  
3. Gateway Scalar 7 doc (20 min) — **qalb-e Dejban**  
4. YARP prefix story (15 min)  
5. Metadata / smells (15 min)  
6. Lab curl + UI (20 min)  
7. 25 soal (20 min)  

---

## Glossary (sade)

| kalame | ma'ni-ye yek khati |
|---|---|
| OpenAPI | standard tosiif-e HTTP API |
| Document | ye JSON OpenAPI (mesal v1) |
| Scalar | UI baraye document |
| Swagger UI | UI-ye classic (inja nist) |
| Swashbuckle | lib ghadimi .NET (inja nist) |
| `AddOpenApi` | register generator |
| `MapOpenApi` | serve JSON endpoint |
| `MapScalarApiReference` | serve UI |
| `AddDocument` | multi-spec to Scalar |
| operationId | esm amal (WithName) |
| tag | group UI |
| schema | shape-e DTO |
| Try-it | request az UI |

---

## Deep dive — chera Gateway UI, na UI ru-ye har service?

**Farz kon:** 7 Swagger UI ru-ye 7 port — bookmark hell; JWT/CORS per port; FE hichvaght mostaghim port nemizane.

**Ba Gateway Scalar:**

- yek URL  
- haman path-e reverse proxy ke production-ish-e  
- multi-tab document  

Service-ha **faghat** JSON midan (`MapOpenApi`). UI markazi.

**Yani chi baraye resume?**  
«Centralized Scalar on the API gateway aggregating per-service OpenAPI docs.»

---

## Deep dive — `{documentName}` 

routePattern: `/dejbanscalar/openapi/{documentName}.json`  
AddDocument avvalin arg `"v1"` → documentName = v1 →  
URL: `/dejbanscalar/openapi/v1.json`

`MapOpenApi` default naming ba in align mishe. Age custom document name, hardo taraf bayad match.

---

## Deep dive — Axios snippet

`WithDefaultHttpClient(ScalarTarget.JavaScript, ScalarClient.Axios)`  
FE Dejban (TanStack Query + Axios later days) → copy-paste az Scalar nazdik-e reality.

Python/C# snippet ham Scalar mitune; default team = JS Axios.

---

## Deep dive — security to OpenAPI

Ideal document:

```yaml
components:
  securitySchemes:
    Bearer:
      type: http
      scheme: bearer
```

+ operation security requirement.

Native OpenApi + JWT setup — metadata shayad auto/partial. Try-it: manually Authorize paste token mamul-e.

**Smell:** developer fekr mikone Scalar «login» darad — nadare; token az Identity Login migiri.

---

## Anti-pattern (ba tozih)

```csharp
// BAD: MapOpenApi in Production bedune auth
// GOOD: Dev/DockerDevelopment only (Dejban)

// BAD: yek OpenAPI mega-file baraye 7 service dasti
// GOOD: per-service generate + Scalar AddDocument

// BAD: Scalar Try-it mostaghim be container hostname
// GOOD: via Gateway routes (Servers=[] + proxy)

// BAD: faramush YARP scalar route ba'd AddDocument
// GOOD: hardo sync
```

---

## Interview 60s (ravoon)

> «Each microservice exposes an OpenAPI document with Microsoft.AspNetCore.OpenApi via MapOpenApi, but only in Development and DockerDevelopment. The ApiGateway hosts Scalar with seven AddDocument entries that load those specs through YARP routes like /dejbanscalar/openapi/v1.json, stripping the prefix to the service’s /openapi endpoint. We don’t use Swashbuckle; Scalar is the UI, and try-it goes through the same gateway paths the frontend uses.»

---

## Quick self-test

1. UI koja? → ApiGateway Scalar  
2. JSON koja generate? → har microservice MapOpenApi  
3. Package UI? → Scalar.AspNetCore 2.11  
4. OpenApi ASP.NET? → 10.0.0  
5. Chand document? → 7  
6. Prefix Dejban? → `/dejbanscalar`  
7. Env? → Development \| DockerDevelopment  
8. Swashbuckle? → na  
9. Servers? → []  
10. Default client snippet? → JS Axios  

---

## Final checklist

- [ ] OpenAPI vs Swagger vs Scalar  
- [ ] AddOpenApi / MapOpenApi  
- [ ] Env guard  
- [ ] Gateway multi-doc  
- [ ] YARP *scalar routes  
- [ ] Metadata Day 17  
- [ ] Smells + resume  

---

## Extra — «Swagger» goftan to mosahebe

Begu:

«Mardom hanuz migan swagger; manzur OpenAPI document-e. UI-e ma Scalar-e, na Swagger UI. Generate ba Microsoft.AspNetCore.OpenApi-e.»

In jomle = clear + modern + honest.

---

## Extra — Farz kon partner-e khareji

Age API public bashe: OpenAPI publish + versioning + auth docs.  
Dejban alan internal product + Dev-only docs.  
**Yani:** pattern amade-st; policy publish joda.

---

## Extra — Reporting / Gate tabs

Reporting Stimulsoft-heavy; Gate device-ish. Hanuz OpenApi Map daran ta endpoint-haye HTTP to Scalar biyand.  
Kamtar az Dejban surface — ama multi-doc complete.

---

## Extra — Output cache / rate limit

Gateway rate limiter + auth middleware — scalar routes **anonymous**.  
Try-it API routes — auth + rate limit normal.  
Document fetch ≠ API call.

---

## Extra — .http files vs Scalar

Ba'zi team `.http` / RestClient. Scalar = interactive + discoverability.  
Har do OK; Dejban investment = Scalar Gateway.

---

## Map — request Try-it Personnels

```
Scalar UI (Gateway)
  → Authorize Bearer
  → Execute GET /Api/v1/... (via Gateway host)
  → YARP Dejban cluster
  → Auth + Tenant + Endpoint
  → JSON response → Scalar panel
```

Document load joda:

```
Scalar → GET /dejbanscalar/openapi/v1.json
  → YARP strip → Dejban MapOpenApi
```

---

## Map — file masir zehni

```
Directory.Packages.props (versions)
  → each *.csproj PackageReference
  → AddOpenApi (DI)
  → MapOpenApi (Dev)
  → YARP *scalar
  → MapScalarApiReference (Gateway Dev)
```

---

## Lab aha (sade)

1. Stop Dejban → Scalar tab Dejban break → start → OK  
2. Change env Production locally → MapOpenApi nist  
3. Compare Identity controller routes vs Dejban minimal to UI  
4. Copy Axios snippet — compare ba FE client  

---

## What Day 33 is *not*

- Full OpenAPI 3.1 schema authoring manual  
- NSwag / Kiota codegen workshop  
- Public developer portal  
- GraphQL schema  

Focus: **native OpenApi + Scalar Gateway multi-doc + YARP glue**.

---

## Resume keywords (ATS)

`OpenAPI` · `Scalar` · `Microsoft.AspNetCore.OpenApi` · `API documentation` · `YARP` · `ApiGateway` · `ASP.NET Core 10` · `Developer Experience` · `Minimal APIs`

---

## Band-e gharardad-e jadid — chejori in fasl neveshte shode

> **Tozihat ravoontar va sade-tar.** Dastan → yani chi → chera → smell.

In ruz:

- menu/restaurant baraye OpenAPI  
- farq-e clear generate (service) vs UI (Gateway)  
- YARP prefix ba dastan  
- honest: metadata thin, Swagger esm, prod off  

---

## 10 jomle ke bayad betuni seda koni (fluency drill)

1. OpenAPI = contract JSON baraye HTTP API.  
2. Scalar = UI; Swashbuckle/Swagger UI inja nist.  
3. Har service AddOpenApi + MapOpenApi.  
4. Faqat Development va DockerDevelopment.  
5. Gateway MapScalarApiReference ba 7 document.  
6. JSON az `/xxxscalar/openapi/v1.json` miad.  
7. YARP PathRemovePrefix → `/openapi/v1.json`.  
8. Servers khali = try via Gateway.  
9. Default snippet Axios.  
10. Tags/TypedResults = document richer.

---

## Soalat-e «chera» (javab-e yek + nim khat)

**Chera UI ru-ye Gateway?**  
Yek ja + haman proxy path-e FE.

**Chera per-service document?**  
Bounded context; deploy joda; mega-file dard.

**Chera anonymous scalar?**  
UI betune Dev bedune token doc load kone.

**Chera prod off?**  
Info leak + niaz nist.

**Chera na Swashbuckle?**  
Native OpenApi .NET 10 + Scalar DX.

---

## Khoruj-e zehni (ye paragraph baraye khodet)

> Midunam OpenAPI document-e contract-e API-e va Scalar UI-e khandanesh. To Dejban har microservice JSON misaze ba MapOpenApi to Dev, va ApiGateway ba Scalar haft document ro az YARP path-haye *scalar aggregate mikone. Midunam PathRemovePrefix chejori /openapi ro fash mikone, chera prod off-e, va chera metadata-ye Minimal API roye quality-e document asar dare.

Age in paragraph mal-e to shod — Day 33 done.

---

*Day 33 tamum. Ba'd: Day 34 — Options pattern (amade). Fehrest: [README.md](./README.md).*
