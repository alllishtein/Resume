# Day 40 — Auth end-to-end

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

In ruz **zincir-e kamel** auth-e: az dokme Login to FE ta JWT, cookie refresh, Gateway, Identity, blacklist, getMe, site header, Guard UI, ta 401→refresh→retry.

Na library-e jadid — **jam'-e** Day 06 (JWT+blacklist) + 16 (tenancy) + 36 (Identity) + 37 (permissions) + 39 (report ticket) + FE packages (`@repo/auth`, `@repo/api-client`, guards).

**Model Dejban (hybrid):**

| chi | koja zendegi mikone |
|---|---|
| **Access JWT** | `localStorage` (Bearer) — kutah-omr |
| **Refresh token** | **HttpOnly cookie** (`withCredentials`) — toolani |
| **User + flat permission claims** | `GET /auth/getme` → AuthContext |
| **Site selection** | Zustand → header `X-Site-Id` |
| **Revocation** | Redis blacklist + `TokenRevokeMiddleware` |
| **API authorize** | JWT + claims transform + Permission/Endpoint policies |

**Band-e gharardad-e jadid:** tozihat ravoontar va sade-tar — ye dastan az login ta API call.

---

# BAKHSH-E AVAL: WORLD — auth e2e chie?

## Farz kon — kart vorud + kart-e toolani

- **Badge access** (JWT): har dar (API) neshan midi — zud expire.  
- **Kart-e toolani** (refresh cookie): faghat pishkhan (Identity refresh) — browser automatic mifreste, JS nemikhune (HttpOnly).  
- **List siah** (blacklist): badge ghabli cancel.  
- **Fehrest dastresi** (getMe claims): UI midune dokme neshan bedahad.  
- **Shobe** (X-Site-Id): hamin badge, otagh digar.

---

## Chera hybrid access localStorage + refresh cookie?

| approach | fayde | za'f |
|---|---|---|
| Faqat cookie session | XSS kamtar roye token | CSRF; SPA harder |
| Faqat localStorage JWT | sade Bearer | XSS steal access; refresh ham expose |
| **Dejban hybrid** | refresh HttpOnly; access Bearer Axios | access XSS still; cookie Secure/SameSite |

**Yani chi?** Refresh ra dast-e JS nade; access ra Bearer kon baraye microservice/YARP.

---

# BAKHSH-E DOVOM: DEJBAN — zincir kamel

## Naqshe-ye master (seda kon)

```
[1] FE sign-in (apps/main JwtSignInView)
      POST /auth/login  {username,password}
      withCredentials
        ↓
[2] Gateway YARP → IdentityServer LoginCommandHandler
      Identity CheckPasswordSignInAsync
      CreateAccessToken + refresh hash store
      Set-Cookie AccessToken + RefreshToken (HttpOnly)
      Body: { user, accessToken }
        ↓
[3] FE tokenStorage.setAccess(accessToken)  // localStorage
      checkUserSession → GET /auth/getme
        ↓
[4] GetMeQueryHandler
      ClaimService → SiteClaims + flat permission values
        ↓
[5] AuthContext: user, siteClaims, claims, authenticated=true
      AuthGuard lets dashboard in
      ComponentGuard / Guard(componentId) hide/show
      Zustand site picker → X-Site-Id on every request
        ↓
[6] API call Axios
      Authorization: Bearer <access>
      Cookie refresh (automatic)
      X-Site-Id, Accept-Language
        ↓
[7] Gateway
      AccessTokenQueryMiddleware (optional query/ticket→header)
      TokenRevokeMiddleware (blacklist?)
      JWT Bearer validate
      YARP → Dejban/ACL/…
        ↓
[8] Microservice
      UseAuthentication / UseTokenRevoke
      CustomClaimsTransformation (site|permission)
      TenantContext from X-Site-Id
      PermissionAuthorization / RequirePermissions
        ↓
[9] Age 401
      Axios interceptor → POST /auth/refresh (cookie)
      new accessToken → retry
      refresh fail → logout + redirect sign-in
```

---

## Qesmat 1 — Login (FE → Identity)

### FE

`signInWithPassword` → `POST /auth/login` → `tokenStorage.setAccess(accessToken)`.

`JwtSignInView`: zod form → signIn → `checkUserSession` → `returnTo` redirect.

Sign-in page often on **apps/main**; dashboard **apps/dejban** — shared api-client/auth packages.

### BE (Day 36 reminder)

Find user phone/username/email → `CheckPasswordSignInAsync` → JWT + cookies + session token row.

**Yani chi?** Password Identity; transport JWT+cookie; FE stores access for Bearer.

---

## Qesmat 2 — Session bootstrap: getMe

`AuthProvider.checkUserSession`:

```
if (!tokenStorage.getAccess()) → logged out
else GET /auth/getme
  → user, SiteClaims[], claims[] (flat permission strings)
```

**GetMe** (Identity):

- Load user  
- `ClaimService.GetUserSiteClaimsAsync`  
- Flat `claims` = union permission values across sites (guards stable)  
- `SiteClaims` = list sites for picker  

**Chera flat claims?** FE `Guard` set.has(componentId) — sade.  
**Site-scoped API** hanuz ba header + transform `siteId|value` (Day 37).

---

## Qesmat 3 — Guards (FE)

| guard | soal |
|---|---|
| **AuthGuard** | authenticated? else → sign-in + returnTo |
| **ComponentGuard** | context claim set |
| **Guard componentId=…** | hide children if no claim |
| **PageGuard** | redirect 403 |
| **RouteAccessGuard** | nav filter by claims |

`authenticated = !!user` (az getMe), na faqat token exist.

Loading/Splash ta session check tamum.

---

## Qesmat 4 — Axios: Bearer + cookie + site + refresh

`createApiClient`:

**Request:**

- `Authorization: Bearer` az localStorage (except refresh URL)  
- `X-Site-Id` az Zustand multi-select  
- `Accept-Language`  
- `withCredentials: true` → cookies  

**Response 401:**

- single-flight `refreshPromise`  
- `POST /auth/refresh` (cookie)  
- setAccess new token → retry original  
- fail 401/403/404 → logout + redirect sign-in  
- 403 toast «دسترسی ندارید»

**Yani chi?** Access expire → silent refresh; refresh murde → login page.

---

## Qesmat 5 — Gateway pipeline (edge)

Typical order (concept):

1. CORS  
2. **AccessTokenQueryMiddleware** — `access_token` / `report_ticket` / siteId az query ya Referer → headers (Day 39 Stimulsoft window.open)  
3. **TokenRevoke** — blacklist → 401  
4. JWT auth  
5. Rate limit / cache  
6. YARP reverse proxy  

**Yani chi?** Yek darvaze: token shape + revoke + route.

---

## Qesmat 6 — Microservice pipeline

Ba'd az Gateway (ya mostaghim):

- `UseTokenRevoke`  
- `UseAuthentication` / `UseAuthorization`  
- `CustomClaimsTransformation` enrich permission/endpoint/role  
- `UseTenantContext` (X-Site-Id)  
- Endpoint filters / `[PermissionAuthorization]`  

Login path Identity; business APIs Dejban/ACL/… hamin JWT.

---

## Qesmat 7 — Refresh & logout & sessions

| endpoint | naqsh |
|---|---|
| `/auth/refresh` | cookie → new access (+ rotate refresh) |
| `/auth/logout` | revoke / clear cookie + client clear storage |
| `/auth/getmysessions` | list sessions |
| terminate session(s) | blacklist + remove token rows |

Single-session Identity (Day 36): login jadid → stamp + blacklist ghabli.

Assign claims (Day 37): blacklist hame tokens user → next API 401 → refresh may fail → re-login.

---

## Qesmat 8 — Site switch (tenancy UX)

1. getMe midahad sites  
2. User entekhab / multi  
3. Zustand persist  
4. Har request `X-Site-Id: id1,id2`  
5. BE tenant filter + permission evaluator site-scoped  

FE claims flat **re-fetch nemikone** on site change (GetMe comment) — UI buttons stable; API 403 age oon site permission nadare.

---

## Qesmat 9 — Reporting exception path

Viewer `window.open` → nemitune Axios interceptor.  
Ticket opaque ya query token → **AccessTokenQueryMiddleware** header misaze.  
Haman JWT validate + revoke.

---

## Se dastan (farz kon)

### A) Sobh login

Password OK → cookies + access LS → getMe → dashboard → Guard show Import Excel.

### B) Access expire mid-day

API 401 → refresh cookie OK → new access → retry — user nemibine.

### C) Admin revoke / claim change

Blacklist → 401 → refresh fail ya short → sign-in.

### D) Site B bedune permission

UI button shayad hast (flat claim); API PermissionAuthorization 403 toast.

### E) XSS steal localStorage access

Attacker short window ta expire; refresh HttpOnly hard-ish steal. Mitigate CSP/XSS hygiene.

---

## Smell-ha / tradeoffs

1. Access token localStorage — XSS risk  
2. Flat FE claims vs site-scoped API — UX mismatch possible  
3. getMe fail catch — user null? loading false — edge  
4. Refresh single-flight good; thundering herd handled  
5. Dual apps main vs dejban sign-in URL config  
6. Cookie SameSite=None Secure — HTTPS required  
7. Gateway + service double TokenRevoke — OK defense  
8. Authenticated=!!user not !!token — need getMe success  
9. 403 toast global — noisy?  
10. Public ticket routes skip refresh redirect  

---

## Debug checklist (e2e)

1. Login 200 + Set-Cookie + body accessToken?  
2. localStorage key set?  
3. getMe 200 claims/sites?  
4. AuthGuard loop redirect?  
5. X-Site-Id on Network tab?  
6. 401 → refresh 200 → retry?  
7. Blacklist → 401 at Gateway?  
8. Permission 403 vs Auth 401 farq  
9. Cookie not sent — withCredentials / domain / Secure  
10. Report ticket path Authorization header injected?  

---

## 25 soal-e mosahebe

1. Access vs refresh Dejban?  
2. Chera withCredentials?  
3. tokenStorage koja?  
4. getMe chi mide?  
5. AuthGuard vs Guard?  
6. Flat claims chera?  
7. X-Site-Id chejori set?  
8. 401 interceptor flow?  
9. single-flight refresh?  
10. TokenRevoke koja?  
11. AccessTokenQueryMiddleware?  
12. Login Identity steps?  
13. ClaimsTransformation?  
14. Assign claims → chejori logout feel?  
15. Single-session?  
16. XSS vs HttpOnly?  
17. 403 vs 401?  
18. Site switch claims refetch?  
19. returnTo?  
20. apps/main vs dejban?  
21. Cookie SameSite?  
22. Permission FE vs BE?  
23. Report auth?  
24. Logout steps?  
25. Resume 60s?

---

## Senario matrix

| event | access | refresh cookie | UI |
|---|---|---|---|
| Login OK | set LS | set | getMe → in |
| Access TTL | expire | valid | silent refresh |
| Refresh TTL | — | expire | sign-in |
| Blacklist access | revoked | ? | 401→refresh/out |
| Logout | clear | clear server | sign-in |

---

## Mini lab

1. Trace Network: login → getMe → any API headers  
2. Delete access LS → next API → refresh?  
3. Clear cookies → refresh fail → redirect  
4. Guard without claim — button gone  
5. Wrong X-Site-Id — 403  
6. Read axiosInstance interceptor  
7. Read AuthContext + GetMeHandler  
8. Gateway AccessTokenQuery + TokenRevoke  

---

## Resume

**kutah:**

> Owned Dejban’s end-to-end auth: Identity login issuing JWT access tokens plus HttpOnly refresh cookies, FE session via getMe and componentId guards, Axios Bearer + X-Site-Id with single-flight refresh-on-401, and Gateway/microservice JWT validation with Redis blacklist revocation and claims transformation for site-scoped authorization.

**bullet-ha:**

- Wired hybrid token storage (localStorage access + cookie refresh) and AuthProvider/getMe bootstrap  
- Implemented Axios interceptors for site headers and coordinated refresh/logout  
- Enforced edge revoke + query/ticket-to-header for reporting popups alongside permission policies  

**skill-ha:** `JWT, OAuth-style refresh, HttpOnly cookies, Axios interceptors, ASP.NET Identity, API Gateway, RBAC/claims, SPA auth, Multi-tenancy`

---

## File-haye mohem

| chi | koja |
|---|---|
| Axios client | `packages/api-client/src/axiosInstance.ts` |
| tokenStorage | `packages/api-client/src/tokenStorage.ts` |
| AuthProvider | `packages/auth/src/AuthContext.tsx` |
| signIn action | `packages/ui/.../jwt/action.js` |
| Guards | `packages/ui/src/auth/guard/*` |
| Sign-in UI | `apps/main/.../jwt-sign-in-view.jsx` |
| Login/Refresh/GetMe | IdentityServer Application/Auth |
| TokenRevoke | `Common/Caching/TokenRevokeMiddleware.cs` |
| Query→header | `AccessTokenQueryMiddleware.cs` |
| Blacklist | `TokenBlackListService` Redis |
| Claims transform | `CustomClaimsTransformation.cs` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 06 JWT+blacklist | token mechanics |
| 16 Tenancy | X-Site-Id |
| 36 Identity | login password |
| 37 Permissions | getMe claims + API |
| 07 YARP | Gateway |
| 39 Reporting | ticket middleware |
| 49 Auth UI | deeper FE (ba'd) |

Day 40 = **glue**. Day 49 = FE patterns omigh-tar.

---

## Chejori digest koni

1. Master diagram 5 bar seda (20 min)  
2. Login + getMe + Guards (25 min)  
3. Axios refresh lab (25 min)  
4. Gateway revoke + query (15 min)  
5. Site + permission mismatch (15 min)  
6. 25 soal (20 min)  

---

## Glossary

| kalame | ma'ni |
|---|---|
| Access token | JWT Bearer short |
| Refresh token | cookie long |
| getMe | session profile+claims |
| AuthGuard | must login |
| ComponentGuard | must claim |
| Blacklist | revoked access strings |
| Single-flight refresh | yek refresh share |
| returnTo | post-login path |
| withCredentials | send cookies cross-origin |

---

## Deep dive — authenticated = !!user

Token to LS bedune getMe success → `user` null → AuthGuard redirect.  
Prevent «ghost token» UI.  
Age getMe 500, catch log — user null — harsh; smell retry.

---

## Deep dive — FE flat vs BE site-scoped

| layer | permission check |
|---|---|
| FE Guard | `claims.includes(componentId)` union |
| BE | `siteId\|componentId` + X-Site-Id |

Design: UI optimistic across sites; server authoritative per site.

---

## Deep dive — Cookie names

Login sets Access + Refresh cookies HttpOnly Secure SameSite=None.  
FE still puts access in LS for Authorization header (cookie access may duplicate purpose).  
Refresh path relies on cookie; interceptor skips Bearer on refresh URL.

---

## Anti-pattern

```javascript
// BAD: store refresh in localStorage
// GOOD: HttpOnly cookie (Dejban)

// BAD: infinite refresh loop on /auth/refresh 401
// GOOD: exclude refresh URL + redirect (Dejban)

// BAD: trust only FE Guard
// GOOD: BE PermissionAuthorization always
```

---

## Interview 60s

> «End-to-end, users log in through Identity which validates passwords with ASP.NET Identity, returns a JWT access token and sets HttpOnly refresh cookies. The SPA stores the access token, calls getMe for profile and permission claims, and guards routes/components by componentId. Axios sends Bearer plus X-Site-Id, and on 401 performs a single-flight refresh using the cookie before retrying. The gateway and services validate JWT, check a Redis blacklist, enrich claims per site, and enforce permissions—while reporting popups use query/ticket middleware to supply the bearer header.»

---

## Quick self-test

1. Access storage? → localStorage  
2. Refresh? → HttpOnly cookie  
3. getMe? → user+sites+claims  
4. 401 next? → refresh then retry  
5. X-Site-Id source? → Zustand  
6. Blacklist middleware? → TokenRevoke  
7. Report open? → AccessTokenQuery / ticket  
8. AuthGuard check? → authenticated user  
9. Guard check? → componentId in claims  
10. Login service? → IdentityServer  

---

## Final checklist

- [ ] Master flow seda  
- [ ] Hybrid tokens  
- [ ] getMe + guards  
- [ ] Axios refresh  
- [ ] Gateway + transform  
- [ ] Site + permission  
- [ ] Resume  

---

## Extra — Sequence login (shomare)

1. Submit password  
2. Identity OK  
3. Cookies + JSON access  
4. LS set  
5. getMe  
6. Context fill  
7. Navigate dashboard  
8. First API with Bearer+Site  

---

## Extra — Sequence 401 recovery

1. API 401  
2. Interceptor lock refreshPromise  
3. POST refresh (cookie only)  
4. 200 accessToken → LS  
5. Retry original with new Bearer  
6. Parallel 401s wait same promise  

---

## Extra — Logout

FE: POST logout → clear LS → context null → sign-in.  
BE: blacklist access + invalidate refresh/session.  
Other tabs: storage event clears auth state.

---

## Extra — Security checklist mosahebe

- HTTPS everywhere (SameSite=None)  
- Short access TTL  
- Refresh rotation  
- Blacklist on logout/claim change/single-session  
- XSS defenses (CSP)  
- Never log tokens  
- BE authorize always  

---

## Extra — Farq 401 / 403

| code | ma'ni UX |
|---|---|
| 401 | shenakht na / token bad → refresh/login |
| 403 | shenakhti ama dastresi na → toast |

Interceptor: 401 refresh path; 403 toast.

---

## Map — packages FE

```
@repo/api-client  → axios + tokenStorage + endpoints
@repo/auth        → AuthProvider / useAuth
@repo/ui auth     → guards, signIn action, site store, component-paths
apps/main         → sign-in page
apps/dejban       → dashboard AuthGuard layout
```

---

## Map — BE services

```
IdentityServer → login refresh getMe logout sessions
ApiGateway → query middleware, revoke, JWT, YARP
Dejban/ACL/… → revoke, JWT, transform, tenant, permissions
Redis → blacklist
```

---

## Lab aha

1. DevTools Application: LS + Cookies after login  
2. Expire access mentally — watch refresh call  
3. Remove claim — button disappear; API still 403 if forced  
4. Multi-tab logout storage sync  

---

## What Day 40 is *not*

- OIDC/OAuth2 external IdP deep  
- Passkeys  
- Full Day 49 FE patterns  

Focus: **Dejban SPA ↔ Gateway ↔ Identity e2e glue**.

---

## Resume keywords

`JWT` · `Refresh token` · `HttpOnly cookie` · `Axios interceptor` · `ASP.NET Identity` · `API Gateway` · `Token blacklist` · `RBAC` · `SPA authentication` · `getMe`

---

## Band-e gharardad-e jadid

Dastan hotel badge; zincir 1–9; farq flat/site; honest XSS; lab Network.

---

## 10 jomle fluency

1. Access LS + refresh cookie.  
2. Login Identity → JWT+cookies.  
3. getMe por mikone AuthContext.  
4. AuthGuard login; Guard componentId.  
5. Axios Bearer + X-Site-Id.  
6. 401 → single-flight refresh.  
7. Gateway revoke + JWT.  
8. Transform site-scoped permissions.  
9. Claim change → blacklist.  
10. Report ticket → header middleware.

---

## Extra — Chera in ruz «end-to-end»?

Har ruz ghabl yek layer.  
Inja mosahebe: «walk me through login» — to mituni **az browser ta DB** seda koni bedune gap.

---

## Extra — Common interview follow-ups

**Where is refresh stored?** HttpOnly cookie.  
**Where is access?** localStorage + Authorization.  
**How multi-tenant?** X-Site-Id + claim format.  
**How logout all devices?** terminate sessions + blacklist.  
**How FE knows buttons?** getMe claims / componentId.

---

## Extra — Farz kon «Session expired» banner

Ideal product: detect refresh fail → soft modal.  
Dejban: hard redirect sign-in. Clear UX; abrupt mid-form — save draft? (client form preferences package exists — related).

---

## Extra — Rate limit login

Gateway `Auth_RateLimiter_PerIp` on login route (Day 07/YARP config).  
Brute force slowdown + Identity lockout (Day 36). Defense in depth.

---

## Extra — SignalR auth

Hubs often access_token query (Day 26) — shabih report.  
Same JWT; revoke still applies when middleware runs.

---

## Extra — Change password mid-session

`/auth/changepassword` → shayad stamp/blacklist.  
FE ba'd re-login ya refresh. Check handler when debugging sudden 401s.

---

## Extra — Terminate other sessions

UI sessions list → terminate → blacklist other JTIs.  
Current tab may keep working until access TTL — then refresh may still work for current cookie; design detail Identity.

---

## Extra — CORS + credentials

`withCredentials` needs API `AllowCredentials` + specific origin (na `*`).  
Misconfig = cookie refresh never sent — classic bug.

---

## Extra — Clock skew

JWT validate `ClockSkew`; getServerTime endpoint exists (auth.http).  
Client/server time drift → random 401. Rare but real.

---

## Extra — Testing e2e

Playwright: login → dashboard visible → API 200.  
Steal cookie jar + LS in test.  
Mock 401 once → assert refresh called once (single-flight).

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «Browser holds access in LS and refresh in HttpOnly cookie. Every API goes Gateway: revoke check, JWT, then service. Permissions come from getMe for UI and from claims transformation for APIs, scoped by X-Site-Id.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Login OK dashboard bounce | getMe fail / AuthGuard |
| Infinite login redirect | authenticated false loop |
| Refresh storm | interceptor not excluding /refresh |
| No cookie | CORS credentials / Secure on http |
| Button visible API 403 | flat vs site scope |
| Report 401 popup | ticket/middleware |

---

## Extra — Layer checklist «who authenticates?»

| hop | auth |
|---|---|
| Browser→Gateway | JWT (+cookie on auth routes) |
| Gateway→Service | often forward Authorization |
| Service | re-validate JWT + revoke |
| Identity login | anonymous + rate limit |

---

## Extra — Related learning days (quick jump)

- Day 06: JWT structure, jti, blacklist Redis  
- Day 16: X-Site-Id tenant filters  
- Day 36: CheckPasswordSignInAsync, cookies set  
- Day 37: ClaimService, PermissionAuthorization  
- Day 39: report_ticket → AccessTokenQueryMiddleware  

In ruz = bridge beyn ina.

---

## Khoruj-e zehni

> Mitunam auth Dejban ro az Login FE ta Identity, cookie/JWT, getMe, Guards, Axios refresh, Gateway blacklist, claims transform, va Permission API be surat-e yek dastan seda konam — va midunam koja FE optimistic-e va koja BE source of truth-e.

Age in paragraph mal-e to shod — Day 40 done.

---

*Day 40 tamum. Ba'd: Day 41 — Files/Documents (Dejban → DCC) (amade). Fehrest: [README.md](./README.md).*
