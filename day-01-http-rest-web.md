# Day 01 — HTTP / REST / Web

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Har chizi ke to in system etefagh miofte, asasan ye **HTTP request/response**-e. Browser (ya axios, ya device) ye request mizane; server ye response mide. Method + path migan «chi mikhay», header-ha context mibaran (ki-i, kodom site, che zabani), body payload-e write-ha-st, va status code natije ra be zaban-e standard mige. **REST** ye set ghanun-e ke mige resource-ha ra ba URL va method-haye standard manage kon — vali Dejban REST-e khales nist: kenar-e CRUD-e resource-oriented, POST-haye RPC-style ham darim (Login, Import, CreateVisitorAndVisitSchedule).

To Dejban in olgu az browser ta Postgres zendegi mikone: Axios Bearer + cookie + `X-Site-Id` → Gateway (CORS, rate limit, JWT) → YARP → Minimal API / Controller → MediatR → DB. Error-ha ba ProblemDetails (RFC 7807) barmigardan; auth dual-channel-e (access to header/memory, refresh to HttpOnly cookie). In fasl WORLD-e HTTP/REST ra midahad, ba’d DEJBAN neshan mide hamin mafahim koja pin shodan.

---

# BAKHSH-E AVAL: WORLD — HTTP va REST to donya

## HTTP chiye?

HTTP = HyperText Transfer Protocol. Protocol-e **request/response** roye model-e client-server. Yani client ye chizi mikhad (request), server javab mide (response) — va in exchange asasan **stateless**-e: server az request-e ghabli chizi yadesh nist, pas har request bayad hame-ye info-ye lazem ra ba khodesh biarad.

```
Client (browser / axios / device)  →  Server
Client                             ←  Server
```

Vijegi-haye asli ke bayad hifz koni:

- **Stateless** — be hamin dalil har bar `Authorization` (va gahi `X-Site-Id`) mifresti; session-e server-side default nist.
- **Text-based** (HTTP/1.1) — message ghabel-e khandan-e (debug ba DevTools/curl sade-st).
- **Application layer** — roye TCP (va mamulan TLS) neshaste.
- **Extensible** — header-e jadid mesle `X-Site-Id` ejaze dari; protocol khodesh break nemishe.

## Stack-e shabake

```
Browser
  → HTTP message  (method, path, headers, body)
  → TLS 1.2/1.3   (encrypt + certificate = HTTPS)
  → TCP            (reliable, ordered, retransmission)
  → IP             (routing)
```

TCP reliable-e (retry, order). UDP fast-e vali guarantee nadare. HTTP/1.1 va HTTP/2 roye TCP-an. HTTP/3 az QUIC/UDP estefade mikone ke head-of-line blocking ra hal kone.

HTTPS = HTTP + TLS. Certificate identity-e server ra sabet mikone. Bedune TLS, data plaintext-e — Wi-Fi sniffer hame chiz ra mibine.

## Anatomi-e ye HTTP message

### Request

```
POST /api/v1/Reservations HTTP/1.1
Host: gateway.example.com
Authorization: Bearer eyJ...
Content-Type: application/json

{"visitorId":"...","from":"2026-09-20T08:00:00Z"}
```

4 bakhsh: **request line** (method path version), **headers**, **empty line**, **body** (optional).

### Response

```
HTTP/1.1 201 Created
Content-Type: application/json
Set-Cookie: AccessToken=...; HttpOnly; Secure

{"id":"9c2e..."}
```

4 bakhsh: **status line** (version code reason), **headers**, **empty line**, **body**.

## URL

```
https://gateway.example.com:443/api/v1/Visitors/abc?page=1&size=20#tab
\___/   \__________________/ \__/\__________________/ \________/ \__/
scheme        host           port       path            query    fragment
```

- **scheme:** `https` = TLS on
- **host:** domain-e public. Client `localhost:5042` ra aslan nemibine
- **path:** resource + version. `/api/v1/Visitors/{id}`
- **query:** filter, sort, pagination. Cache-key ham hast
- **fragment:** `#tab` — **server aslan nemibine**; faghat browser estefade mikone

## Method-ha

Method yani «che amali mikhay ru resource». Do mafhum-e mosahebe-i ke bayad joda koni: **safe** (resource ra avaz nemikone) va **idempotent** (N bar zadan = 1 bar — state-e naha'i yeki mimane). Jadval-e zir hamin fargh ra neshan mide:

| method | body? | safe? | idempotent? | baraye chi |
|---|---|---|---|---|
| GET | na | bale | bale | bekhoon |
| HEAD | na | bale | bale | mesle GET vali body nadare (metadata) |
| POST | bale | na | **na** | create / action |
| PUT | bale | na | **bale** | replace-e kamel |
| PATCH | bale | na | mamulan bale | update-e jozi |
| DELETE | gahi | na | bale | hazf |
| OPTIONS | na | bale | bale | CORS preflight |

POST idempotent nist — 2 bar POST mamulan = 2 ta create. PUT idempotent-e — 2 bar PUT haman resource ro be haman state miare. DELETE ham idempotent-e — 2 bar delete, bar-e dovom 404 ya 204, vali state-e server digar avaz nashode.

## REST chiye?

REST = Representational State Transfer — Roy Fielding to PhD-esh in constraint-ha ra tarif karde. Yani REST «framework» nist; ye set ghanun-e ke age follow koni, API-t predictable va cache-friendly mishe. 6 ta gheyd:

1. **Client-server** — UI joda az data
2. **Stateless** — har request khod-kafa
3. **Cacheable** — GET-ha ghabel-e cache
4. **Uniform interface** — resource ba URL, method-e standard, self-descriptive message
5. **Layered system** — client nemifahme posht-e proxy chi-e
6. **Code on demand** (optional) — JS az server

**Richardson maturity** ye scale-e amali-e ke mige API-t cheghadr «RESTful»-e:

- Level 0: ye URL, hamechiz POST (SOAP-style)
- Level 1: chand resource URL
- Level 2: HTTP method + status dorost
- Level 3: HATEOAS (link to response — bishtar-e API-ha nadaran)

Dejban mamulan beyn-e Level 1–2-e: resource CRUD + gahi RPC POST.

## Status code — guide-e kamel

Status code zaban-e kootah-e beyn-e client va server-e: «success?», «client ghalat?», ya «server kharab?». FE bayad 401 ra az 403 joda kone; Gateway bayad 502/504 ra az 500-e app joda kone.

**2xx — success:**

- 200 OK — hamechiz dorost. GET list, POST ba body
- 201 Created — resource sakhte shod. Hatman POST. Ideally `Location` header
- 202 Accepted — ghobool kardm, vali hanooz tamum nashode (async job)
- 204 No Content — success, body nist. PUT/DELETE

**3xx — redirect:**

- 301 Moved Permanently — URL avaz shode. Browser cache mikone
- 302 Found — temporary redirect
- 307 Temporary Redirect — method hefz mishe (POST mimone POST)
- 308 Permanent Redirect — method hefz, permanent
- 304 Not Modified — cache valid-e, body nemifreste

**4xx — client ghalat karde:**

- 400 Bad Request — validation fail, payload ghalat
- 401 Unauthorized — **ki hasti?** Token nist ya invalid
- 403 Forbidden — **shenakhtamet, ejaze nadari**
- 404 Not Found — resource ya route nist
- 405 Method Not Allowed — PUT roye endpoint-e faghat-GET
- 409 Conflict — state conflict (duplicate, version mismatch)
- 413 Payload Too Large — file bozorg-e
- 415 Unsupported Media Type — Content-Type ghalat
- 422 Unprocessable Entity — semantic validation (gahi be jaye 400)
- 429 Too Many Requests — rate limit. `Retry-After` header

**5xx — server kharab karde:**

- 500 Internal Server Error — unhandled exception
- 502 Bad Gateway — proxy be upstream naresid
- 503 Service Unavailable — server overloaded ya maintenance
- 504 Gateway Timeout — upstream javab nadad to moghe'

**401 vs 403 — hifz kon:** 401 = "ki hasti?" (login/refresh). 403 = "shenakhtamet, mojavez nadari" (UI button ra disable kon).

## ProblemDetails (RFC 7807 / 9457)

Standard-e error-e HTTP API:

```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.1",
  "title": "Visitors.NationalIdInUse",
  "status": 409,
  "detail": "in code melli tekrari ast",
  "traceId": "00-abc..."
}
```

`title` baraye machine logic (FE switch), `detail` baraye ensan. ASP.NET `Results.Problem` va `ValidationProblem` in format ra generate mikone.

Validation-e chand error:

```json
{
  "status": 400,
  "errors": { "NationalId": ["required", "length 10"] }
}
```

## Header-ha

Header = metadata; body = payload. Header-e request context mide (ki-i, che zabani, chi mikhay). Header-e response natije mide (cache, cookie, CORS). Hop-by-hop header-ha (`Connection`, `Keep-Alive`, `Upgrade`) ra proxy bayad hazf kone; `Authorization` / `Cookie` / `Content-Type` bayad bemoonan. Header size limit mamulan 8–16KB-e — JWT-e bozorg + cookie → 431.

**Request headers-e mohem:**

- `Authorization: Bearer {jwt}` — shenasaei
- `Content-Type: application/json` — body chi format-e
- `Accept: application/json` — chi format mikhay
- `Accept-Language: fa-IR` — zaban
- `Origin` — az koja miyam (CORS)
- `Cookie` — browser-managed credential

**Response headers-e mohem:**

- `Set-Cookie` — cookie minevise
- `Cache-Control` — cache policy
- `Location` — 201 Created, address-e resource-e jadid
- `WWW-Authenticate` — 401, scheme (Bearer)
- `Retry-After` — 429, key saniye wait
- `Access-Control-Allow-*` — CORS

## Cookie

Cookie ye key-value-e ke server ba `Set-Cookie` mifreste, browser zakhire mikone, va har request-e matching **automatic** mibare — yani JS lazem nist attach kone. In baraye refresh token khoob-e (HttpOnly), vali CSRF risk ham miad chon browser khodesh mifreste.

Flag-haye mohem:

- **HttpOnly** — JavaScript `document.cookie` nemibine → XSS cookie ra nemitune bedozde
- **Secure** — faghat roye HTTPS ferestade mishe
- **SameSite** — `Strict` (faghat same-site), `Lax` (top-level GET cross-site), `None` (hameja, hatman Secure)
- **MaxAge / Expires** — omr-e cookie
- **Path / Domain** — scope

**SameSite values:**

- `Strict` — safest, vali link-e cross-site cookie ra nemibare
- `Lax` — link OK, vali XHR/axios cross-origin cookie nemibare
- `None` — hameja; **hatman Secure** lazem-e. Baraye SPA-ye cross-origin

## CORS

CORS = Cross-Origin Resource Sharing. In **browser policy**-e (na security-e server): mige «JS-e origin A nemitone response-e origin B ra bekhone magar server B ejaze bedahad.» Origin = scheme + host + port — pas `https://app:3034` ≠ `https://gateway:443`. curl, Postman, va device CORS nadaran; security-e vagheyi hanuz JWT + permission-e.

**Preflight:** ghabl az POST-e cross-origin ba custom header (Authorization, X-Site-Id, Content-Type: application/json), browser aval OPTIONS mizane:

```
OPTIONS /api/v1/Reservations
Origin: https://app:3034
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization,x-site-id
```

Server javab mide:

```
Access-Control-Allow-Origin: https://app:3034
Access-Control-Allow-Credentials: true
Access-Control-Allow-Headers: *
Access-Control-Allow-Methods: *
```

`AllowCredentials` + `AllowAnyOrigin(*)` **mamnoo'-e** — bayad origin-e moshakhas ya callback.

CORS faqat **browser**-e. curl, Postman, device/doorbin CORS nadaran. Security-e vagheyi JWT + permission-e.

`Access-Control-Max-Age` — cache-e preflight. Bedunesh har POST ye OPTIONS-e ezafe dare.

## Body va Content-Type

- `application/json` — default-e REST API. Axios automatic set mikone
- `multipart/form-data` — file + data ba ham. Baraye upload
- `application/x-www-form-urlencoded` — HTML form classic. Kam to SPA
- Khali — GET, DELETE, HEAD

## Koja chi bezari

| koja | baraye chi | mesal |
|---|---|---|
| path | identity-e resource | `/Reservations/{id}` |
| query | filter, sort, page | `?page=1&size=20` |
| header | protocol/auth/tenant/locale | `Authorization`, `X-Site-Id` |
| cookie | credential-e browser-managed | refresh token |
| body | payload-e write | create/update JSON |

Rule: GET body nadare. Secret to query bad-e (log, Referer, history). ID-e resource to path. Filter-ha to query.

## Versioning

4 ravesh:

| ravesh | mesal | mohem |
|---|---|---|
| **URL** | `/api/v1/...` | sade, clear, cache-friendly |
| header | `api-version: 1.0` | clean URL, cache sakht |
| query | `?api-version=1.0` | hybrid |
| media type | `Accept: application/vnd.x.v1+json` | academic |

URL version mamul-tarin-e to donya. Breaking change = v2. Non-breaking (field-e jadid-e optional) = haman v1.

## HTTPS va TLS

TLS handshake: client hello → server certificate → key exchange → symmetric encrypt.

**TLS termination:** HTTPS ta edge (load balancer/gateway). Dakhele network HTTP-e internal. `X-Forwarded-Proto: https` be upstream mige "client HTTPS umade." Cookie-e Secure bedune in set/send nemishe.

`X-Forwarded-For: client-ip, proxy-ip` — leftmost client-e. Bedune `KnownProxies` spoof-e.

## Cache

```
Cache-Control: public, max-age=60
ETag: "v3"
If-None-Match: "v3"  →  304 Not Modified (body nemifreste)
```

- `no-store` — aslan cache nakon (auth data)
- `no-cache` — cache kon vali revalidate
- `private` — faghat browser, na CDN
- `max-age=n` — saniye

GET-e authenticated ba `X-Site-Id` = **khatarnak** baraye shared cache. User A list-e user B ra mibine.

## Rate limit

429 Too Many Requests + `Retry-After: 12` header. Client bayad wait kone.

4xx-e vali retry **ma'nidar-e** (bar khalaf-e 400/401).

## WebSocket vs HTTP

HTTP = yek request, yek response, baste. WebSocket = connection-e toolani, frame-haye do-tarafe.

WebSocket az HTTP shoru mishe (Upgrade handshake → 101 Switching Protocols), bad dige HTTP semantics nist. SignalR roye WebSocket-e (ya fallback be long-polling).

## HTTP/1.1 vs HTTP/2 vs HTTP/3

| | 1.1 | 2 | 3 |
|---|---|---|---|
| transport | TCP | TCP | QUIC/UDP |
| multiplex | 1 req / connection | chand stream / connection | chand stream, bedune TCP head-of-line |
| headers | text, tekrar | HPACK compress | QPACK |
| HTTPS | optional | de-facto required | required |

Browser be gateway mamulan HTTP/2. Gateway be service dakheli HTTP/1.1. SignalR WebSocket joda az in-e.

## CSRF

CSRF = site-e hamle form POST mizane be API-e to, browser cookie ra automatic mifreste.

Defa-ha:

1. `SameSite` cookie — cross-site request cookie nemibare
2. Custom header (`Authorization`, `X-Site-Id`) — attacker site az JS nemitone header be API-e to ezafe kone (CORS block mikone)
3. Antiforgery token — server ye token mide, form POST bayad bargardone
4. Origin/Referer check

JWT to Authorization header CSRF ra mikoshe (attacker header-e Bearer-e victim ra nadare). Cookie-only endpoint-ha (mesle refresh) hanooz sensitive-an.

## Idempotency

Mohem baraye reliability. User 2 bar "save" mizane — 2 reservation?

Rah-ha:

1. FE disable button (zaif — network retry hanooz 2 bar mire)
2. **Idempotency-Key header** (Stripe style) — `Idempotency-Key: guid`, server 24h zakhire
3. Unique constraint DB — duplicate → 409
4. PUT be jaye POST baraye update

POST ra idempotent farz nakon. In risk-e business-e.

## Chizayi ke vojud dare vali kam estefade mishe

- **HATEOAS** — link to response ke client betone navigate kone. RESTful-tarin, vali aksar-e API-ha nadaran
- **ETag / conditional request** — 304, bandwidth save. Bishtar baraye static/CDN
- **Accept negotiation** — server JSON ya XML bede based on `Accept`. Aksar faghat JSON-e
- **PATCH with JSON Merge Patch / JSON Patch** — RFC 7396/6902. Standard-e partial update
- **Server-Sent Events (SSE)** — yek-tarafe az server be client. Sade-tar az WebSocket baraye push-e yek-tarafe
- **HTTP/3 QUIC** — UDP-based, mobile-friendly, head-of-line fix
- **Trailer headers** — header ba'd az body (streaming checksum)
- **103 Early Hints** — preload resource ghabl az response-e asli
- **Idempotency-Key header** — standard-e draft baraye POST idempotency

---

# BAKHSH-E DOVOM: DEJBAN — HTTP to in proje

## Request-e vagheyi chejori zendegi mikone

Senario: user to app-e dejban, site entekhab karde, «create reservation» mizane. In 10 step haman Day 00 lifecycle-e, vali ba detail-e HTTP-e:

1. Click → `apiClient.post('/api/v1/Reservations', body)`
2. Axios interceptor:
   - `Accept-Language: fa-IR`
   - `X-Site-Id: <ids>` az Zustand
   - `Authorization: Bearer <access>` az tokenStorage
   - `withCredentials: true` → Cookie header
3. Browser CORS: preflight cache nist? → OPTIONS. Gateway 204
4. POST HTTPS be Gateway
5. Gateway pipeline: rate limit → token query → revoke → JWT → authorize
6. YARP match → `dejban-cluster`
7. Transform Host + Proto, forward `http://dejban/api/v1/Reservations`
8. Dejban Minimal API → MediatR handler → DB
9. Success: `200 {"id":"..."}`
10. Axios 200 → `response.data.id`
    401 → refresh cookie → access jadid → retry original request
    403 → toast "dastresi nadarid"

## Method-ha to Reservations

`VisitReservationEndpoints.cs`:

| method | path | response | |
|---|---|---|---|
| POST | `/Reservations` | 200 + `{id}` | create |
| GET | `/Reservations` | 200 + list | safe |
| GET | `/Reservations/{id}` | 200 + detail | safe |
| PUT | `/Reservations/{id}` | 204 | update |
| PATCH | `.../items/{itemId}/allow` | 204 | partial update |
| DELETE | `/Reservations/{id}` | 204 | hazf |

**Smell:** create 200 mide, na 201. REST-e classic 201 + Location mikhad. Moshkele bozorg nist vali to mosahebe bego: "Spec 201 ra pishnahad mikone, ma 200 + body {id} midim."

## POST-haye RPC-style

```
POST /api/v1/Visitors/CreateVisitorAndVisitSchedule
POST /api/v1/Personnels/ImportFromExcel/Preview
POST /api/v1/Auth/Login
```

Ina verb to path-e — REST-e khales nist, RPC over HTTP-e. Chera ghabul-e: ye action chand aggregate ra misaze (visitor + schedule + photo). Import excel chand step dare. Login side-effect dare (cookie).

Jomle-ye mosahebe: "Ma resource-oriented CRUD baraye standard entity-ha darim, va command/RPC POST baraye workflow-haye complex. REST-e khales nistim va in ra midanam."

## Multipart form-data

`CreateVisitorAndVisitSchedule.cs`: aks + JSON ba ham.

```csharp
[FromForm] string payload,
[FromForm] IFormFile? visitorPhoto,
```

JSON ra dasti `Deserialize` mikonan. `.DisableAntiforgery()` lazem-e chon SPA antiforgery token nemifreste.

## ProblemDetails mapping

`ApiResults.cs`:

```csharp
ErrorType.Validation   → 400
ErrorType.Unauthorized → 401
ErrorType.Forbidden    → 403
ErrorType.NotFound     → 404
ErrorType.Conflict     → 409
ErrorType.Failure      → 400
_                      → 500
```

`title` = `error.Code` (stable, baraye FE switch). `detail` = `error.Description` (ensani).

Identity `ApiController` `title` ra `error.Description` mizare (na Code). Do service, do shape-e koochik — inconsistency.

## Cookie-haye Dejban

`LoginCommandHandler.cs`:

```csharp
Response.Cookies.Append(AccessToken, accessToken, new CookieOptions {
    HttpOnly = true,
    Secure = true,
    SameSite = SameSiteMode.None,
    MaxAge = TimeSpan.FromDays(sessionDays)
});
```

`SameSite=None` chon SPA roye origin-e dige-ye — `Lax` axios-e cross-origin ra bedune cookie mikone va refresh mishkane.

Do kanal-e token: Cookie HttpOnly baraye refresh, memory/header baraye access.

## Axios interceptor

`axiosInstance.ts`:

- Request: `Accept-Language`, `X-Site-Id`, `Authorization` automatic ezafe mishe
- Response 401: refresh cookie → access jadid → retry original. Age refresh ham fail → logout
- Response 403: toast, logout nemikone
- `withCredentials: true` → browser cookie-e cross-origin ra mifreste
- Public ticket URL-ha az refresh logic **estexna** shodan

`refreshPromise` single-flight: 100 ta 401-e hamzaman → 1 refresh.

## CORS-e Gateway

`ServiceCollectionExtensions.cs`:

- Dev: `SetIsOriginAllowed` = hame true
- Prod: list-e env
- `AllowCredentials` + custom headers
- `AllowAnyMethod`

**Smell:** Dev allow-all age production leak kone, har origin + credentials = khatr.

`Access-Control-Max-Age` set nashode → har POST ye OPTIONS-e ezafe.

## Custom header `X-Site-Id`

Multi-tenant scope. Axios az Zustand set mikone. Chand site: `X-Site-Id: id1,id2`. Server bayad ba claim-e JWT match kone (ruz 44) — header ja'l-pazir-e.

## Rate limit

Do sath to Gateway:

- **Global:** 500 req/min per IP
- **Auth:** 6 req/30s per IP (Login, Refresh, CameraAuth)

IP az `X-Forwarded-For` leftmost. 429 + `Retry-After`. Axios 429 ra special handle nemikone (smell).

## Versioning-e Dejban

URL: `/api/v{version}/...`. Asp.Versioning roye endpoint: `HasApiVersion(1.0)`, `MapToApiVersion(1.0)`. Alan hame v1.0. Header `api-supported-versions: 1.0`.

## Next proxy vs YARP

Do laye proxy:

| | Next rewrite | YARP |
|---|---|---|
| chi | HTML/JS-e sub-app | API + hub + files |
| mesal | `/dejban/dashboard` → dejban:3034 | `/api/v1/Visitors` → :5042 |
| auth | na | bale |

`basePath: '/dejban'` baraye frontend route. API path basePath nadare — mostaghim be Gateway.

404-e `/dejban/api/v1/...` = FE eshtebah URL ra ba basePath mix karde.

## Token to query

Stimulsoft / SignalR: `?access_token=...` chon WebSocket handshake va `window.open` header-e custom nemitonan. `AccessTokenQueryMiddleware` copy-ash mikone be Authorization header. Khatarnak (log, Referer leak).

## DELETE ba body

```js
await apiClient.delete(url, { data: ids });
```

HTTP DELETE mitone body dashte bashe, vali proxy-haye ghadimi gahi body ra mindazan. Bulk-delete ba list-e id. Alternative: `POST /Assets/Delete` ya `?ids=`.

## Chi **nadari** (ta resume dorough nashe)

- HATEOAS / hypermedia links
- ETag / 304 conditional request
- Idempotency-Key header
- JSON Merge Patch (RFC 7396) baraye PATCH
- GraphQL
- gRPC-Web az browser (gRPC faghat server-to-server — ruz 18)
- HTTP/3 (client browser dare, server side configure nashodoe)

## Smell-ha

1. Create → 200 na 201
2. RPC path (`/CreateX`) kenar-e resource path
3. DELETE ba body
4. Token to query (Stimulsoft/SignalR) — log leak
5. SameSite=None + DisableAntiforgery — CSRF surface
6. CORS Dev = allow all — production risk
7. Identity 500 baraye Failure, Dejban Failure=400 — inconsistency
8. Accept-Language faghat 429 ra localize mikone, na hame error-ha
9. 429 FE handle nemishe
10. `X-Site-Id` trust bedune claim check (ta ruz 44)
11. `Access-Control-Max-Age` nist — extra preflight
12. Validation 400 na 422 (convention-e ASP.NET — ghabul)

## 20 soal-e mosahabe

1. HTTP chie? — protocol-e request/response, stateless, roye TCP/TLS
2. Stateless yani chi? — server connection-state negah nemidare; auth har request
3. GET vs POST? — GET safe+idempotent, POST side-effect
4. PUT vs PATCH? — PUT replace-e kamel, PATCH jozi
5. Idempotent? — N bar = 1 bar. PUT/DELETE bale, POST na
6. 401 vs 403? — nashenakhti vs bi-mojavez
7. 204? — success, body nist
8. CORS chie? — browser policy baraye cross-origin. curl nadare
9. Preflight? — OPTIONS ghabl az request-e nonsimple
10. SameSite=None chera? — SPA va API origin-e joda
11. HttpOnly? — JS nemibine; zed-e XSS
12. Secure cookie bedune HTTPS? — ferestade nemishe
13. REST chie? — constraint: client-server, stateless, cache, uniform, layered
14. HATEOAS? — link to response; aksar nadaran
15. `/CreateVisitor` REST-e? — na, RPC. Verb to path
16. ProblemDetails? — RFC-e standard error; status+title+detail
17. WebSocket chejori? — HTTP Upgrade → 101
18. 502? — proxy be upstream nareside
19. CSRF ba JWT header? — attacker Bearer ra nadare; cookie-only still sensitive
20. HTTP/2 chie? — multiplex-e chand stream roye 1 TCP

---

## Deep dive — Status code decision tree (API design)

```
Success with body (GET/list/detail)?
  → 200 OK
Created new resource?
  → 201 Created + Location (Dejban gahi 200 + {id} — document mismatch)
Success, no body (update/delete)?
  → 204 No Content
Accepted async job?
  → 202 Accepted + poll URL (kam dar Dejban)

Client sent bad JSON / validation?
  → 400 (+ ValidationProblem)
Not authenticated?
  → 401
Authenticated, no permission?
  → 403
Resource missing?
  → 404
Duplicate / state conflict?
  → 409
Rate limited?
  → 429 + Retry-After

Unhandled bug?
  → 500
Gateway upstream dead?
  → 502 / 504
```

**502 vs 504:** 502 = bad/invalid response from upstream; 504 = upstream **timeout**. FE often same toast — debug ba gateway logs.

---

## Deep dive — CORS + credentials (edge cases)

```
Browser rule:
  Access-Control-Allow-Origin: *  +  Allow-Credentials: true  → INVALID

Dejban prod:
  explicit origins + AllowCredentials + AllowAnyHeader/Method
```

**Preflight cache:** `Access-Control-Max-Age: 86400` → kamtar OPTIONS. Dejban set nashode — SPA ba har custom header (Authorization, X-Site-Id) **non-simple** → OPTIONS.

**Credential request:** `withCredentials: true` → response `Allow-Origin` **cannot** be `*` — bayad exact origin FE.

---

## Deep dive — Cookie + Bearer dual channel

| channel | storage | sent how | risk |
|---|---|---|---|
| Access JWT | memory / module `tokenStorage` | `Authorization: Bearer` | XSS read memory if leaked |
| Refresh | HttpOnly cookie | automatic browser | CSRF if cookie-only API |

Dejban: access to header, refresh to cookie → refresh **na** to JS. Login `Set-Cookie` + body/token access.

**Logout:** server cookie expire + client clear access.

---

## Deep dive — YARP reverse proxy (Dejban)

```
Client → ApiGateway (YARP)
  clusters: dejban-cluster, identity-cluster, acl-cluster, ...
  routes: Path /api/v1/{**catch-all} → cluster by prefix/service map
  transforms: RequestHeaderOriginalHost, X-Forwarded-Proto
```

**Chera YARP na faghat Next rewrite?**
- Next rewrite = **browser** navigation sub-apps (`/dejban` → port 3034)
- YARP = **API** traffic `:443` → backend Kestrel `:5042` etc.
- SignalR / file upload / long request — YARP tuned for proxy

**Token query middleware:** `?access_token=` for WebSocket/Stimulsoft → copy to `Authorization` — **security smell** (logs, Referer).

---

## Deep dive — Asp.Versioning URL

```csharp
// endpoint group
app.MapGroup("/api/v{version:apiVersion}/Visitors")
   .HasApiVersion(1.0);
```

Response header: `api-supported-versions: 1.0` — FE mitone detect. Breaking change → v2 route parallel, deprecate v1.

---

## Deep dive — FE axios error surface

`packages/api-client/src/axiosInstance.ts`:
- **401:** refresh single-flight (`refreshPromise`) → retry original; fail → sign-in redirect
- **403:** toast — logout **na**
- **Public ticket** URLs skip refresh loop
- **Digits:** Persian → English normalization on params/body (search consistency)

`getErrorMessage` / Day 09: `ProblemDetails.detail` ya validation `errors` dict → UI string.

**Gap:** 429 no backoff — user spam click → hammer gateway.

---

## Dejban endpoint examples (beyond Reservations)

| area | pattern | note |
|---|---|---|
| Personnels | `POST /Personnels/Create`, `GET` list | command + ErrorOr |
| Vehicles | multipart + nested owner rules | large payload |
| Auth (Identity) | `/auth/login` lowercase path | cookie + Problem shape |
| Reports Stimulsoft | GET + query token | header limitation workaround |
| Health | `/health` anonymous | k8s probe |

**OpenAPI / Scalar:** dev doc from Minimal API metadata + tags per module.

---

## ProblemDetails — FE consumption tips

```javascript
// validation 400
const errors = error.response?.data?.errors;
// { NationalCode: ["الزامی است"], ... }

// single business error
const title = error.response?.data?.title; // stable code: Personnel.NationalCodeExists
const detail = error.response?.data?.detail; // human Persian
```

Switch UI on **`title`**, show user **`detail`**. Identity sometimes swaps — handle both services in FE if shared client.

---

## HTTP semantics — practical REST cheatsheet (Dejban)

| action | prefer | Dejban reality |
|---|---|---|
| List + filter | GET + query | ✅ |
| Create | POST 201 | POST 200 sometimes |
| Full replace | PUT 204 | ✅ reservations |
| Partial | PATCH 204 | ✅ allow/deny items |
| Delete one | DELETE 204 | ✅ |
| Bulk delete | DELETE body / POST Delete | ⚠️ both exist |
| Workflow | POST verb path | ✅ Import, Login |

---

## Chejori in fasl ra «digested» koni (lab — ~40 min)

1. DevTools Network: yek POST — OPTIONS? headers? (5 min)
2. 401 force — watch refresh + retry duplicate (10 min)
3. Gateway vs direct Dejban port — same ProblemDetails? (5 min)
4. curl **bedune** CORS — API still works (5 min)
5. Compare 403 vs 401 toast behavior (5 min)
6. Read `ApiResults.cs` mapping table (5 min)
7. 20 soal boland (5 min)

---

## 5 soal-e ezafe (bonus)

21. **Chera fragment (#) server nemibine?** — client-only routing
22. **HEAD vs GET?** — metadata/cache check bedune body
23. **307 vs 302 for POST redirect?** — method preservation
24. **Hop-by-hop header chi?** — proxy strip list
25. **YARP vs nginx to interview?** — both L7 reverse proxy; YARP native .NET config code-first

---

## Resume

**short:**

> Designed and consumed versioned HTTP APIs (ASP.NET Minimal APIs + Axios) behind a YARP gateway, using cookie+Bearer auth, CORS credentials, multi-tenant headers, and RFC 7807 ProblemDetails.

**bullets:**

- Modeled CRUD resources with GET/PUT/PATCH/DELETE + 204, plus RPC-style POST for multi-aggregate workflows (visitor+schedule+multipart)
- Mapped domain ErrorOr to HTTP 400/401/403/404/409 via ProblemDetails; distinguished gateway 401/429/502 from app errors
- Implemented cross-origin SPA auth with SameSite=None, Secure, HttpOnly cookies, withCredentials, and 401→refresh→retry interceptor

**skills:** `HTTP, REST, CORS, Cookies, TLS, ProblemDetails, Axios, Minimal APIs`

## File-haye mohem

| chi | koja |
|---|---|
| Reservations CRUD | `...Visitors.Presentation/Visitors/VisitReservationEndpoints.cs` |
| Multipart create | `.../CreateVisitorAndVisitSchedule.cs` |
| ProblemDetails map | `Dejban.Common.Presentation/Results/ApiResults.cs` |
| Identity Problem | `IdentityServer/Controllers/ApiController.cs` |
| Cookie login | `IdentityServer/.../Login/LoginCommandHandler.cs` |
| CORS + rate limit | `ApiGateway/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Axios instance | `packages/api-client/src/axiosInstance.ts` |
| Next rewrite | `apps/main/next.config.mjs` |

---

Day 01 tamum. Ba'd: Day 02 — C# async / concurrency / GC. Fehrest: [README.md](./README.md).
