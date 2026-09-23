# Day 65 — Next.js basePath + rewrites (multi-app one origin)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Dejban FE** ye monorepo-ye Turborepo (Day 43) ke chand ta app dare: **main** (portal), **dejban** (core), **gate**, **dcc**, va **access-control** (Vite, Day 54). Hame-ye in-ha ru-ye **ye origin** serve mishan — user faghat ye domain mibine. In karo ba do ta mechanism anjam midim: har child app ye **`basePath`** dare (`/dejban`, `/gate`, `/dcc`, `/access-control`) va main app ba **`rewrites`** request-ha ro proxy mikone be upstream-e har app. In "multi-zone lite" — na ye monolith-e FE-e, na Module Federation-e kamel, balke ye rahe-hal-e pragmatic-e ke ba Next.js built-in khoob kar mikone.

---

# BAKHSH-E AVAL: WORLD — basePath, rewrite, redirect, multi-zone

## Farz kon

Ye mall (main) ke 4 ta forushgah dare — Dejban, Gate, DCC, Access Control. Hamash ye dar-e vorud daran (ye origin/domain). Moshtari mire `/dejban` — mall khodesh mibare-sh be forushgah-e Dejban. URL-e browser avaz nemishe (rewrite), na inke redirect kone.

## basePath — chi hast?

`basePath` ye config-e Next.js-e ke be app mige: "hame-ye route-haye man prefix-eshun in-e". Vaghti `basePath: '/dejban'` set koni:

| bedun-e basePath | ba basePath |
|---|---|
| `/dashboard` → `localhost:3001/dashboard` | `/dashboard` → `localhost:3001/dejban/dashboard` |
| `/_next/static/...` → root | `/_next/static/...` → `/dejban/_next/static/...` |
| `<Link href="/about">` → `/about` | `<Link href="/about">` → `/dejban/about` |

**Yani:** Next.js khodesh hame-ye asset-ha, route-ha, va link-ha ro ba in prefix generate mikone. Browser vaghti `/dejban/dashboard` ro baz mikone, Next.js mige "oh, root-e man `/dejban`-e, pas route-e vaghei `dashboard`-e".

**Gotcha-ye asli:** age `basePath` set koni vali asset-ha ya link-ha ro hardcode koni bedun-e prefix, **404** migiri. `next/link` khodesh handle mikone, vali `<a href="/foo">` handle nemikone — bayad `<Link>` estefade koni.

## rewrite vs redirect — farghe asli

| | rewrite | redirect |
|---|---|---|
| **URL-e browser** | avaz nemishe | avaz mishe |
| **server-side** | server internally proxy mikone | 301/302 be client mide |
| **user experience** | seamless; ye origin | user mibine URL avaz shod |
| **cookie scope** | same origin = same cookies | age domain avaz she, cookie na |
| **SEO** | ye URL | do URL (canonical lazem) |

**Dejban az rewrite estefade mikone** chun mikhad user hamishe ye domain bebine va cookie-ha share bashan.

## redirect key vaght estefade mishe?

- Vaghti permanently moved-i (SEO migration)
- Vaghti user ro be ye domain-e dge mifresti
- Vaghti authentication redirect (login → returnTo)

Dejban az redirect faghat baraye root → `/dejban` estefade mikone:

```js
async redirects() {
    return [{ source: '/', destination: '/dejban', permanent: false }];
}
```

## Multi-zone — Next.js native

Next.js ye feature-e be esm-e "multi-zones" dare ke exactly hamin kar ro mikone: ye app rewrites mikone be app-haye dge. Dejban essentially hamin approach ro dasti piade karde ba `rewrites`. Farghesh: multi-zones-e official az `assetPrefix` ham estefade mikone va documentation-e behtari dare, vali pragmatically hamun kar ro mikone.

## Module Federation (Webpack 5)

| | Module Federation | Multi-zone / rewrite |
|---|---|---|
| **granularity** | component-level share | page/app-level |
| **runtime share** | yes (React, libs) | no — har app bundle-e khodesh |
| **complexity** | bala | payin |
| **deploy independence** | partial | kamel |
| **UX transition** | SPA-like | full page load beyn-e app-ha |

Dejban Module Federation estefade **nemikone** — har app joda build mishe, joda deploy mishe, joda run mishe. Transition beyn-e app-ha ye full page load-e (bedtar az SPA, vali sade-tar va stable-tar).

## One-origin cookies — chera mohem-e

Vaghti hame-ye app-ha ru-ye ye origin-an (`https://example.com`):
- httpOnly refresh cookie ke Path `/` dare, **hame-ye app-ha** behesh dastresi darand
- `Set-Cookie: ...; Path=/; HttpOnly; Secure; SameSite=Lax` → for all paths
- Nabayad cookie-e joda per app bezari (magar ghasdan mikhay isolation dashte bashi)

Age har app ru-ye subdomain-e joda bud (`dejban.example.com`, `gate.example.com`):
- Cookie-ha share nemishan (magar `Domain=.example.com` set koni)
- CORS config lazem mishe
- Complexity bala mire

**Pas:** one-origin simplifies auth significantly.

---

## Dev environment — port-ha va trap-ha

| app | dev port | basePath |
|---|---|---|
| main | 3000 | (none) |
| dejban | 3001 | `/dejban` |
| gate | 3002 | `/gate` |
| dcc | 3003 | `/dcc` |
| access-control | 5173 (Vite) | `/access-control` |

Vaghti **main** ro local run mikoni, `rewrites` proxy mikone:
- `/dejban/:path+` → `http://localhost:3001/dejban/:path+`
- `/gate/:path+` → `http://localhost:3002/gate/:path+`

**Trap:** age dejban ro run nakoni (port 3001 down bashe), main-e rewrite 502 ya timeout mide — user ye safhe-ye tohi mibine bedun-e error-e clear. Dev tip: hame-ye app-ha ro ba `turbo dev` (Day 43) hamzaman run kon.

**Asset 404:** age `basePath` ro eshtebahi remove koni ya avaz koni:
1. `/_next/static/chunks/...` hame 404 mishan chun browser az root mikhad
2. CSS load nemishe → safhe tohi ya broken
3. JS load nemishe → hydration fail

**Debug:** DevTools → Network → check kon asset path-ha `/dejban/_next/...` hastand ya faghat `/_next/...`.

---

# BAKHSH-E DOVOM: DEJBAN — chetori piade shode

## apps/main/next.config.mjs — portal

```js
const subAppDomains = {
  accessControl: process.env.NEXT_PUBLIC_ACCESS_CONTROL_DOMAIN,
  dejban: process.env.NEXT_PUBLIC_DEJBAN_DOMAIN,
  gate: process.env.NEXT_PUBLIC_GATE_DOMAIN,
  dcc: process.env.NEXT_PUBLIC_DCC_DOMAIN,
};

const rewrites = async function () {
    return [
        { source: '/access-control',        destination: `${subAppDomains.accessControl}/access-control/` },
        { source: '/access-control/:path+', destination: `${subAppDomains.accessControl}/access-control/:path+` },
        { source: '/dejban',                destination: `${subAppDomains.dejban}/dejban` },
        { source: '/dejban/:path+',         destination: `${subAppDomains.dejban}/dejban/:path+` },
        { source: '/gate',                  destination: `${subAppDomains.gate}/gate` },
        { source: '/gate/:path+',           destination: `${subAppDomains.gate}/gate/:path+` },
        { source: '/dcc',                   destination: `${subAppDomains.dcc}/dcc` },
        { source: '/dcc/:path+',            destination: `${subAppDomains.dcc}/dcc/:path+` },
    ];
};
```

**Nokteh-ha:**
- Har app **do ta** rewrite dare: ye root (`/dejban`) va ye catch-all (`:path+`)
- `destination` be domain-e واقعی-e app point mikone (production: internal DNS; dev: localhost:port)
- `NEXT_PUBLIC_*` env var-ha per environment set mishan (docker-compose, PM2 ecosystem, .env.local)
- `outputType === 'export'` bashe → rewrites disable mishe (static export proxy nadare)

**Root redirect:**

```js
async redirects() {
    return [{ source: '/', destination: '/dejban', permanent: false }];
}
```

User `/` baz kone → redirect be `/dejban` → rewrite be dejban app.

## apps/dejban/next.config.mjs — child app

```js
const nextConfig = {
  output: 'standalone',
  basePath: '/dejban',
  // ...
  async redirects() {
    return [{ source: '/', destination: '/dashboard', permanent: false }];
  },
};
```

**Key:** `basePath: '/dejban'` — in hame chi ro prefix mikone. `standalone` output baraye Docker/PM2 deployment (Day 58).

**Internal redirect:** `/` (yani `/dejban/`) → `/dashboard` (yani `/dejban/dashboard`). Next.js khodesh basePath ro apply mikone.

## apps/gate/next.config.mjs

```js
const nextConfig = {
  output: 'standalone',
  basePath: '/gate',
  // ...
};
```

Hamun pattern — faghat `basePath` fargh mikone.

## apps/dcc/next.config.mjs

```js
const nextConfig = {
  output: 'standalone',
  basePath: '/dcc',
  // ...
};
```

## Vite access-control — Day 54

Access-control ye Vite SPA-ye (na Next.js). Equivalent-e `basePath` to Vite in-e:

```js
// vite.config.js
export default defineConfig({
  base: '/access-control/',  // ← asset prefix (same as basePath for assets)
});

// React Router
<BrowserRouter basename="/access-control">
```

**Fargh:** Next.js `basePath` ham asset ham routing ro handle mikone. Vite in-ha joda-n: `base` baraye asset, `basename` baraye React Router. Age yeki ro set koni va digari ro faramush koni, ya asset-ha 404 mishan ya route-ha match nemikonan.

---

## Security headers — hame-ye app-ha

```js
async headers() {
    return [{
        source: '/:path*',
        headers: [
            { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
            { key: 'X-Content-Type-Options', value: 'nosniff' },
            { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
    }];
}
```

Hame-ye app-ha in header-ha ro set mikonan. `X-Frame-Options: SAMEORIGIN` clickjacking ro prevent mikone; `Referrer-Policy` leak-e URL ro limit mikone. Main ham ye `Cache-Control: no-store` ezafe dare (baraye portal ke dynamic-e).

## allowedDevOrigins

```js
allowedDevOrigins: ['192.168.10.73', '192.168.10.71', 'localhost', '192.168.1.19'],
```

Next.js 14+ baraye dev mode, age request az origin-e nashnas biad, warn ya reject mikone. In list IP-haye dev team-e.

---

## PM2 deployment — Day 58 connection

```yaml
# ecosystem.config.cjs (simplified)
apps:
  - name: main
    script: apps/main/.next/standalone/server.js
    env: { PORT: 3000 }
  - name: dejban
    script: apps/dejban/.next/standalone/server.js
    env: { PORT: 3001 }
  - name: gate
    script: apps/gate/.next/standalone/server.js
    env: { PORT: 3002 }
  - name: dcc
    script: apps/dcc/.next/standalone/server.js
    env: { PORT: 3003 }
```

Har app ye PM2 process-e joda-e ba port-e khodesh. Main-e rewrite-ha be in port-ha proxy mikonan. Production: `NEXT_PUBLIC_DEJBAN_DOMAIN=http://localhost:3001` (ya Docker service name).

---

## Turbo build — Day 43 connection

```bash
turbo build --filter=dejban --filter=main
```

Turbo task dependency-ha ro resolve mikone: `@repo/ui` avval build mishe, ba'd app-ha. basePath impact-i ru-ye build nadare — faghat runtime behavior-e.

---

## Sequence-ye kamel — user `/dejban/dashboard` ro baz mikone

```
Browser: GET https://example.com/dejban/dashboard
    │
    ▼
Main Next.js (port 3000)
    │ rewrites: /dejban/:path+ → http://dejban-app:3001/dejban/:path+
    │
    ▼
Dejban Next.js (port 3001, basePath: /dejban)
    │ route match: /dashboard
    │ renders page, assets prefixed: /dejban/_next/static/...
    │
    ▼
Browser receives HTML
    │ loads /dejban/_next/static/chunks/...
    │ (main proxies these too via rewrite)
    │
    ▼
Hydration complete → SPA navigation within dejban
```

**HMRE (Hot Module Replacement) to dev:**
Next.js WebSocket baraye HMR ham basePath ro mikhune. Age basePath eshtebah bashe, HMR connect nemishe → live reload kaar nemikone → dev experience bad mishe.

---

## Smell-ha

1. **Hardcoded domain to rewrite** — age env var set nashe, rewrite be `undefined` proxy mikone → 500
2. **Asset proxy overhead** — hame-ye `/_next/static` ham az main rad mishe → ye hop-e ezafi baraye har asset
3. **Full page load beyn-e app-ha** — na SPA transition; user experience jarring-e
4. **No shared layout** — har app sidebar/header-e khodesh dare; inconsistency momken-e
5. **basePath typo** — ye `/` ya esm-e eshtebah → **hame-ye asset-ha 404** → safhe-ye tohi (ye common trap)
6. **Cookie Path mismatch** — age cookie `Path=/dejban` set beshe, app-haye dge behesh dastresi nadarand
7. **Trailing slash inconsistency** — `trailingSlash: false` vali rewrite-e access-control trailing slash dare → redirect loop momken-e
8. **Dev port collision** — do ta app ro ru-ye ye port run koni → ye-kish kaar mikone
9. **HMR break** — basePath eshtebah → WebSocket connect nemishe → no live reload
10. **Static export mode** — `output: 'export'` ba rewrites sazegar nist (documented)

---

## Debug checklist

1. Asset 404? → DevTools Network → path-e asset `/dejban/_next/...` hast ya faghat `/_next/...`?
2. Rewrite kaar nemikone? → `NEXT_PUBLIC_DEJBAN_DOMAIN` set shode? `console.log(subAppDomains)` to config
3. Redirect loop? → trailing slash mismatch? `trailingSlash` setting check kon
4. Cookie na mirese? → `Path=/` hast ya `Path=/dejban`? DevTools → Application → Cookies
5. HMR na kaar mikone? → basePath match mikone? WS connection to DevTools Network → WS tab
6. 502 az rewrite? → upstream app run mishe? port dorost-e?
7. CORS error? → hame-ye app-ha same origin-an? ya subdomain dari?
8. Build fail? → `transpilePackages` hame-ye shared packages ro dare?

---

## 25 soal-e mosahebe

1. basePath chie? — **A:** prefix baraye hame-ye route-ha va asset-haye ye Next.js app.
2. rewrite vs redirect? — **A:** rewrite URL-e browser ro avaz nemikone (server proxy); redirect avaz mikone.
3. Chera one-origin? — **A:** cookie sharing, no CORS, simpler auth.
4. Chand ta app to monorepo? — **A:** main, dejban, gate, dcc, access-control (+ packages).
5. main chikar mikone? — **A:** portal/hub ke rewrites proxy mikone be child app-ha.
6. Dev port-ha kodum-an? — **A:** 3000 main, 3001 dejban, 3002 gate, 3003 dcc, 5173 AC.
7. Asset 404 key vaght mishe? — **A:** basePath eshtebah ya remove beshe.
8. Module Federation chie va chera estefade nashode? — **A:** component-level share; too complex, partial independence.
9. Multi-zone chie? — **A:** Next.js native feature baraye multi-app rewrite; Dejban manually misaze.
10. Vite base vs basename? — **A:** `base` baraye asset prefix, `basename` baraye React Router.
11. Cookie problem ba subdomain? — **A:** cookie share na mishe magar `Domain=.example.com`.
12. standalone output chie? — **A:** self-contained Node.js server baraye Docker/PM2.
13. HMR chera break mishe? — **A:** basePath eshtebah → WS connect fail.
14. trailing slash impact? — **A:** mismatch → redirect loop ya 404.
15. Security headers chi set mishan? — **A:** X-Frame-Options, X-Content-Type-Options, Referrer-Policy.
16. allowedDevOrigins chie? — **A:** IP-hayi ke to dev mode reject nashan.
17. turbo build chetori impact dare? — **A:** shared packages avval build mishan; basePath faghat runtime.
18. PM2 chetori app-ha ro manage mikone? — **A:** har app ye process ba port-e joda; Day 58.
19. Agar env var set nashe chi mishe? — **A:** rewrite be `undefined` proxy mikone → 500/502.
20. Static export ba rewrite? — **A:** sazegar nist; rewrite server-side-e.
21. transpilePackages chie? — **A:** Next.js in package-ha ro khudash build mikone (na pre-built).
22. Root redirect chie? — **A:** `/` → `/dejban` (non-permanent).
23. `source: ':path+'` yani chi? — **A:** catch-all — har path ba'd az prefix match mishe.
24. Chetori ye app-e jadid ezafe mikoni? — **A:** app besaz, basePath bede, to main rewrite ezafe kon, env var set kon.
25. Full page load beyn-e app-ha — mituni fix koni? — **A:** Module Federation ya shared shell; tradeoff-e complexity.

---

## Senario-ha

### A) User `/gate/dashboard` ro baz mikone
Browser → main (3000) → rewrite → gate (3002, basePath `/gate`) → route `/dashboard` → render → assets `/gate/_next/...` → main proxy → browser.

### B) Dev basePath ro eshtebah avaz mikone
`basePath: '/dejban2'` vali main rewrite hanuz `/dejban/:path+` dare → rewrite be `/dejban2/...` → route match fail → 404 for all pages.

### C) Ye app-e jadid (monitoring) ezafe mishe
1. `apps/monitoring/` besaz ba `basePath: '/monitoring'`
2. `NEXT_PUBLIC_MONITORING_DOMAIN=http://localhost:3004` set kon
3. To main `next.config.mjs` rewrite ezafe kon: `{ source: '/monitoring/:path+', destination: ... }`
4. PM2 ecosystem ye process ezafe kon
5. Deploy → monitoring available at `/monitoring`

### D) Cookie-e auth az gate be dejban nemirese
Check: cookie `Path` chie? Age `Path=/gate` bashe, `/dejban` behesh dastresi nadare. Fix: cookie `Path=/` set kon (server-side).

### E) Production nginx reverse proxy
```nginx
server {
    listen 443 ssl;
    location / {
        proxy_pass http://main:3000;
    }
}
```
Nginx faghat main ro mibine; main khodesh rewrite mikone. Nginx nabayad per-app location dashte bashe.

---

## Jadval-e moghayese — multi-app strategies

| strategy | build coupling | runtime coupling | UX | complexity |
|---|---|---|---|---|
| **Rewrite + basePath** (Dejban) | low (Turbo) | medium (proxy) | full page load | low |
| Module Federation | medium (shared deps) | high (runtime share) | SPA-like | high |
| Single monolith app | high | none | SPA | lowest |
| Separate domains | none | none | domain switch | medium (auth) |
| iframes | none | none | jarring | medium (postMessage) |

---

## Anti-pattern-ha

```js
// BAD: hardcode domain to rewrite
rewrites: [{ source: '/dejban/:path+', destination: 'http://192.168.1.5:3001/dejban/:path+' }]

// GOOD: env var
destination: `${process.env.NEXT_PUBLIC_DEJBAN_DOMAIN}/dejban/:path+`
```

```jsx
// BAD: hardcode link bedun-e basePath
<a href="/dashboard">Dashboard</a>

// GOOD: next/link handles basePath automatically
<Link href="/dashboard">Dashboard</Link>
```

```js
// BAD: cookie ba Path-e specific
Set-Cookie: token=abc; Path=/dejban

// GOOD: cookie ba root path
Set-Cookie: token=abc; Path=/
```

```js
// BAD: trailing slash inconsistency
// app: trailingSlash: false
// rewrite destination: '...access-control/'  ← trailing slash

// GOOD: match trailing slash config
```

---

## Interview 60s

> «We serve multiple Next.js apps — dejban, gate, dcc — behind a single origin. Each child app sets a basePath like /dejban. The main portal app rewrites incoming requests to the appropriate upstream using environment-variable domains. This gives us independent deploys and builds while users stay on one domain and share cookies. For the Vite-based access-control app, we use base and React Router basename for the same effect.»

---

## Resume

**kutah:**

> Built a **multi-app frontend architecture** using Next.js **`basePath`** per app and **`rewrites`** from a main portal, serving 5 independently deployed apps on one origin — plus Vite SPA basename integration.

**bullet-ha:**

- Architected multi-zone-lite frontend: 4 Next.js apps + 1 Vite SPA behind a single origin via rewrites
- Configured `basePath` per app ensuring correct asset prefixing and router behavior
- Designed dev/prod environment variable strategy for upstream domains (PM2 + Docker)
- Maintained shared httpOnly cookie auth across all apps via one-origin same-path cookie scope

**skill-ha:** `Next.js · basePath · rewrites · multi-zone · monorepo · Turborepo · PM2 · Vite · SPA routing · cookie management`

---

## File-haye mohem

| chi | koja |
|---|---|
| Main rewrites | `apps/main/next.config.mjs` |
| Dejban basePath | `apps/dejban/next.config.mjs` |
| Gate basePath | `apps/gate/next.config.mjs` |
| DCC basePath | `apps/dcc/next.config.mjs` |
| AC Vite config | `apps/access-control/vite.config.js` |
| PM2 ecosystem | `ecosystem.config.cjs` (Day 58) |
| Turbo config | `turbo.json` (Day 43) |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 40 Auth e2e | cookie-e refresh ke hame-ye app-ha share mikonan |
| 42 Next.js | basePath, next.config fundamentals |
| 43 Turbo | monorepo build, dev server orchestration |
| 54 Vite AC | base + basename equivalent-e basePath |
| 58 PM2 | deployment-e chand process ba port-haye joda |
| 47 MUI | transpilePackages baraye @repo/ui |

---

## Glossary

| kalame | ma'ni |
|---|---|
| basePath | prefix-e global baraye route/asset-haye ye Next.js app |
| rewrite | server-side proxy ke URL-e browser ro avaz nemikone |
| redirect | server 301/302 mide → browser URL avaz mikone |
| multi-zone | Next.js feature baraye chand app ru-ye ye domain |
| Module Federation | Webpack 5 feature baraye runtime component sharing |
| standalone output | Next.js self-contained server build |
| catch-all | `:path+` — match everything after prefix |
| origin | protocol + domain + port = cookie/CORS scope |
| SPA | Single Page Application — client-side routing |
| HMR | Hot Module Replacement — dev live reload |
| transpilePackages | Next.js config baraye compile kardan-e external packages |

---

## Deep dive — chetori environment variable-ha kar mikonan

`NEXT_PUBLIC_*` env var-ha **build time** inline mishan to client bundle. Pas:
- `NEXT_PUBLIC_DEJBAN_DOMAIN` bayad vaght-e **build** available bashe
- Age ba'd az build avaz koni, effect nadare (magar server-side code bashe)
- Baraye rewrite-ha in OK-e chun rewrites **server-side** run mishan va az `process.env` mikhunan → **runtime**
- Vali client-side `process.env.NEXT_PUBLIC_SERVER_URL` → build-time inline

**Trap:** developer fek mikone env var ro avaz karde va effect dare, vali client bundle change nakhorde.

---

## Deep dive — asset caching va basePath

Vaghti `basePath: '/dejban'` set koni, hame-ye chunk-ha under `/dejban/_next/static/` serve mishan. Nginx ya CDN-e to bayad in path-ha ro cache kone. Age basePath avaz beshe (masalan `/dejban-v2`), hame-ye cache-e ghadimi invalid mishe — in khoob-e baraye cache busting, vali bad-e age bi-ghasd bashe.

`Cache-Control: no-store` ke main dare yani portal hich vaght cache nemishe — har request fresh-e. Child app-ha in header ro nadarand — `_next/static` khodesh content-hash dare pas long-term cacheable-e.

---

## Deep dive — WebSocket va rewrite

Next.js dev server ye WebSocket baraye HMR baz mikone. Vaghti main rewrite mikone be dejban, HTTP request-ha proxy mishan vali **WebSocket upgrade momkene proxy nashe** (bastegi be Next.js version va config dare). Dev workaround: browser mostaghim `localhost:3001` ro baz kone baraye dejban dev (bypass main). Production: WebSocket-haye non-HMR (masalan SignalR Day 26) az YARP gateway proxy mishan, na az Next.js rewrite.

---

## Self-test-e sari

1. basePath-e dejban chie? → `/dejban`
2. Main chi kar mikone? → rewrite proxy be child app-ha
3. Chand ta rewrite per app? → 2 (root + catch-all)
4. Vite equivalent-e basePath? → `base` + `basename`
5. Cookie chera share mishe? → same origin, `Path=/`
6. Asset 404 dalil-esh chie? → basePath mismatch
7. Module Federation chera estefade nashode? → too complex; full page load OK-e
8. HMR break chera? → basePath eshtebah → WS fail
9. standalone output chie? → self-contained Node server
10. Root redirect koja-e? → main: `/` → `/dejban`

Age 8/10 ya bishtar dorost bud → beri sar-e Day 66.

---

## Chejori digest koni

1. basePath concept + asset impact (10 daghighe)
2. rewrite vs redirect (5 daghighe)
3. main next.config.mjs — rewrite-ha (15 daghighe)
4. Child app config-ha (10 daghighe)
5. Vite equivalent (5 daghighe)
6. Smell-ha + debug (10 daghighe)
7. 25 soal (20 daghighe)

---

## Resume keywords (ATS)

`Next.js` · `basePath` · `rewrites` · `multi-zone` · `monorepo` · `Turborepo` · `PM2` · `Vite` · `multi-app frontend` · `cookie management` · `standalone` · `reverse proxy`

---

## Checklist-e nahaei

- [ ] basePath concept + gotcha-ha
- [ ] rewrite vs redirect
- [ ] main config (rewrite-ha + env vars)
- [ ] Child app config-ha (dejban, gate, dcc)
- [ ] Vite AC equivalent
- [ ] One-origin cookie benefit
- [ ] Dev port-ha + trap-ha
- [ ] PM2 + Turbo connection
- [ ] Smell-ha (asset 404, trailing slash, HMR)
- [ ] Resume + interview 60s

---

## Extra — `output: 'standalone'` deep dive

Next.js `standalone` output ye `.next/standalone` folder tolid mikone ke khodesh `node_modules`-e lazem ro dare — nabayad kol-e `node_modules` ro copy koni to Docker. In size-e Docker image ro az ~1GB be ~100MB mikone:

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/apps/dejban/.next/standalone ./
COPY --from=builder /app/apps/dejban/.next/static ./.next/static
COPY --from=builder /app/apps/dejban/public ./public
CMD ["node", "server.js"]
```

**Gotcha:** `standalone` `public/` va `.next/static` ro auto-copy nemikone — bayad dasti copy koni. Age faramush koni, favicon/images va JS chunk-ha 404 mishan.

**basePath interaction:** vaghti `standalone` + `basePath: '/dejban'` dari, `server.js` khodesh basePath ro handle mikone. Nginx nabayad `/dejban` ro strip kone — bayad as-is pass kone.

---

## Extra — CORS va multi-app

Chon hame-ye app-ha ru-ye ye origin-an, **CORS aslam moshkeli nist**. Vali API server (backend) CORS dare chun az origin-e dge-i call mishe:

```csharp
// backend CORS
policy.AllowCredentials();
policy.SetIsOriginAllowed(origin => ...);
```

Age roozi app-ha ro be subdomain migrate koni, CORS-e beyn-e FE app-ha ham lazem mishe — in ye reason-e dge ke one-origin sade-tar-e.

---

## Extra — i18n va basePath

Next.js i18n routing (locale prefix) **ba basePath combine mishe:**

```
/dejban/fa/dashboard  →  basePath=/dejban + locale=fa + route=/dashboard
/dejban/en/dashboard  →  basePath=/dejban + locale=en + route=/dashboard
```

Dejban az `i18next` estefade mikone (Day 48) ke client-side locale switch dare, na Next.js built-in i18n routing. Pas locale to URL nist — faghat basePath + route. In sade-tar-e vali SEO baraye multilingual content za'if-tar-e.

---

## Extra — monitoring va health check

Vaghti PM2 app-ha ro manage mikone, health check bayad per-app bashe:

```bash
# PM2 ecosystem
apps:
  - name: dejban
    script: apps/dejban/.next/standalone/server.js
    env: { PORT: 3001 }
    # health check: curl http://localhost:3001/dejban/api/health
```

Age health check endpoint `basePath` ro include nakone, 404 mide. Baraye Kubernetes/Docker health check ham hamin mas'ale hast — path bayad ba basePath start she.

---

## Extra — ISR (Incremental Static Regeneration) va basePath

ISR page-ha to `.next/server/pages/` save mishan. Ba `basePath`, Next.js khodesh path-ha ro dorost handle mikone. Vali age CDN ya edge cache dari, cache key bayad basePath ro include kone — vagarna cache-e `/dashboard` az app-e `dejban` ba cache-e `/dashboard` az app-e `gate` ghaati mishe.

Dejban ISR estefade **nemikone** (server-rendered + client SPA), vali age mikhay ezafe koni, in ro yadet bashe.

---

## Extra — `transpilePackages` chie va chera lazem-e

```js
transpilePackages: ['@repo/ui', '@repo/auth', '@repo/api-client', '@repo/config'],
```

In packages to monorepo hastand (`packages/` folder). Normal Next.js faghat `node_modules`-e pre-compiled ro load mikone. Chon in package-ha source code-an (JSX, TS), Next.js bayad khodesh compile-eshun kone. Bedun-e `transpilePackages`, import-e JSX az `@repo/ui` → "unexpected token `<`" error.

**Vali:** vaghti hame-ye app-ha in list ro darand, change to `@repo/ui` → hame rebuild mishan. Turbo in dependency-ha ro dorost track mikone (Day 43).

---

## Extra — assetPrefix vs basePath

| config | chi kar mikone |
|---|---|
| `basePath` | prefix-e route + asset + link |
| `assetPrefix` | **faghat** prefix-e asset (CDN URL) |

Age asset-ha ro az CDN serve koni, `assetPrefix: 'https://cdn.example.com'` set mikoni. In ba basePath compatible-e — Next.js har do ro apply mikone: route az basePath, asset az assetPrefix. Dejban assetPrefix estefade **nemikone** (hame az same origin serve mishe).

---

## Extra — production Nginx config

```nginx
upstream main_app {
    server 127.0.0.1:3000;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    location / {
        proxy_pass http://main_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Key:** faghat ye location `/` lazem-e — main khodesh routing mikone. `Upgrade` header baraye WebSocket (HMR + SignalR passthrough). Nabayad per-app location benevisim — in responsibility-e main-e.

---

## Extra — migration strategy — az multi-rewrite be micro-frontend

Age roozi team bozorg-tar she va SPA transition lazem she:

1. **Phase 1 (alan):** rewrite + basePath — independent deploy, full page load
2. **Phase 2:** shared layout component to `@repo/ui` — visual consistency
3. **Phase 3:** Module Federation ya import maps — runtime component sharing
4. **Phase 4:** single-SPA ya equivalent — SPA transition bedun-e full page load

Har phase complexity ezafe mikone. Phase 1 baraye team size-e alan kafi-e.

---

## Extra — debugging production rewrite failure

**Senario:** production-e, `/gate/dashboard` 502 mide.

1. SSH be server → `pm2 list` → gate process run mishe?
2. `curl http://localhost:3002/gate/dashboard` → age 200 mide, moshkel main rewrite-e
3. `NEXT_PUBLIC_GATE_DOMAIN` to main-e environment check kon → dorost point mikone?
4. main log check kon → rewrite destination chi-e? Network error?
5. Age Docker-e: `docker network inspect` → service-ha hamdigar ro resolve mikonan?
6. Age PM2-e: port clash? `netstat -tlnp | grep 3002`

**Common fix:** env var set nashode ya eshtebah → rewrite be `undefined:3002` proxy mikone.

---

## Extra — comparison: Next.js rewrites vs Nginx reverse proxy

| | Next.js rewrites | Nginx reverse proxy |
|---|---|---|
| config location | `next.config.mjs` (code) | `nginx.conf` |
| restart needed | ya (redeploy) | `nginx -s reload` |
| layer | application (Node.js) | infrastructure |
| WebSocket | limited (depends on version) | native support |
| performance | OK for moderate traffic | optimized for high traffic |
| flexibility | JS logic (conditional) | regex-based |

Dejban Next.js rewrites ro estefade mikone chun sade-tar-e baraye dev va config to code-e. Production-e bozorg-tar momkene Nginx-level routing behtare bashe.

---

*Day 65 tamum. Ba'di: Day 66 — useInfiniteQuery + refresh single-flight. Fehrest: [README.md](./README.md).*
