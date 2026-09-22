# Day 42 — Next.js 16 + React 19

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** FE Dejban chi-ye? SPA khalis (Vite+Router) ya framework server-aware?

**Javab Dejban:** **Next.js 16 (App Router) + React 19** — amma **shive-ye estefade** bishtar *dashboard CSR* hast ta marketing SSR.

Zincir-ezehni:

```
Browser
  → Next app (apps/dejban | main | gate | dcc | …)
      App Router: src/app/**/page.jsx + layout.jsx
      Root layout (Server Component) → providers
      Dashboard layout ('use client') → AuthGuard + nav
      Page thin → sections/* (client heavy)
  → Axios (@repo/api-client) → Gateway → backend
```

Version-ha (repo, approx):

| package | range |
|---|---|
| `next` | `^16.2.6` |
| `react` / `react-dom` | `^19.1.1` |
| Node engines | `>=20` |
| Bundler day-be-day | Turbopack (`next dev --turbo`, `next build --turbopack`) |

**Band-e gharardad-e jadid:** farz kon / yani chi / chera — va **honesty**: Next inja shell-e, data az API client miad na az RSC fetch be Postgres.

Day 43 = Turborepo+workspaces. Day 54 = Vite SPA contrast. **In ruz = Next+React dar Dejban.**

---

# BAKHSH-E AVAL: WORLD — Next 16 + React 19 chie?

## Farz kon — do maghaze

**Maghaze A (classic SPA):** yek `index.html`, JS bundle bozorg, client routing. Server faqat static file mide.

**Maghaze B (Next App Router):** folder `app/` = route; mituni Server Component dashte bashi (HTML az server), Client Component ba `'use client'`, layout share, `basePath`, `standalone` Docker.

Dejban = **B ba ruh-e A**: App Router + layout SSR-ish baraye shell/i18n; **list/form/data** = client + Axios (Day 44).

**Yani chi?** «Next 16» be ma'ni-ye automatic SSR baraye har page nist — be ma'ni-ye *platform* (routing, build, deploy, React 19 runtime).

---

## Chera Next (na faqat Vite) baraye Dejban?

| niyaz | Next midahad | Vite+RR (Day 54) |
|---|---|---|
| Multi-app monorepo ports | `next dev -p 3034` per app | possible, kamtar convention |
| `basePath` `/dejban` | built-in | manual |
| `output: 'standalone'` | Node server slim Docker/PM2 | static + nginx |
| Root async layout (lang) | Server Component | nist |
| Marketing/auth app (main) | same stack | mixed |
| Bundle speed | Turbopack 16 | Vite already fast |

**Chera na full RSC data?** Backend microservices + JWT LS + SignalR + MUI forms — pattern-e team = client fetch. RSC fetch be Gateway ba cookie refresh hybrid sakht-tar-e (Day 40).

---

## React 19 — WORLD (chi mohem-e)

React 19 (va 19.2 to Next canary): Actions, `useOptimistic`, better forms, `use()`, Document Metadata improvements, Compiler path, `useEffectEvent`, View Transitions, …

**Dejban honesty:** codebase bishtar **React 18-style hooks** + chand ja `startTransition`. `useOptimistic` / Server Actions / `useEffectEvent` hanooz markaz-e architecture nistan.

Interview: «We run React 19 on Next 16; product UI is client-driven; we adopt new hooks where they fix real bugs (e.g. startTransition depth).»

---

## Next 16 — WORLD highlight (baraye mosahebe)

Az blog Next 16 (high-level):

- **Turbopack stable** — default bundler direction; Dejban already `--turbo` / `--turbopack`
- **Cache Components / `use cache` / PPR** — model-e cache sarih-tar (Dejban dashboard kam estefade)
- **React Compiler support (stable)** — auto memo; Dejban may not enable yet — check `next.config`
- **proxy.ts** rename direction (middleware) — **Dejban: no `middleware.ts` found** (honesty)
- Node **20.9+** — engines `>=20` match

**Yani chi baraye to?** Version number miduni; feature-ha-i ke *estefade nashode* ra claim nakon.

---

# BAKHSH-E DOVOM: DEJBAN — sakhtar

## Naqshe-ye app-ha

`dejban_frontend_new/apps/`:

| app | naqsh (approx) | tip |
|---|---|---|
| `dejban` | asosli dashboard access control | port **3034**, `basePath: /dejban` |
| `main` | portal / auth entry | HTTPS dev, digar port |
| `gate` | gate-related UI | `basePath: /gate` |
| `dcc` | document center UI | `basePath: /dcc` |
| `access-control` | … | workspace member |

Har app: `package.json` → `next`, `react` 19, scripts `dev`/`build`/`start`.

Shared: `packages/ui`, `auth`, `api-client`, `config` — `transpilePackages` to `next.config.mjs`.

---

## Qesmat 1 — `next.config.mjs` (dejban)

File: `apps/dejban/next.config.mjs`

| key | value / ma'ni |
|---|---|
| `output` | `'standalone'` (ya `'export'` agar static flag) |
| `basePath` | `'/dejban'` — URL public zir path |
| `transpilePackages` | `@repo/ui`, `@repo/auth`, `@repo/api-client`, `@repo/config` |
| `trailingSlash` | `false` |
| `experimental.lockDistDir` | `false` |
| `typescript.ignoreBuildErrors` | `true` (**smell** — build JS-first) |
| `allowedDevOrigins` | LAN IPs baraye dev |
| `headers` | `X-Frame-Options`, nosniff, Referrer-Policy |
| `redirects` | `/` → `/dashboard` |

**Farz kon basePath:** browser miravad `https://host/dejban/dashboard/...`. Asset-ha va Link-ha bayad basePath ra respect konand (Next automatic baraye `next/link`).

**Standalone yani chi?** Build ye folder `.next/standalone` midahad ke ba `node server.js` run mishe — Docker/PM2 dust dare (Day 58).

---

## Qesmat 2 — App Router folder

```
apps/dejban/src/app/
  layout.jsx              ← Root (async Server Component)
  client-init.jsx         ← 'use client' ConfigRegistry
  dashboard/
    layout.jsx            ← 'use client' AuthGuard + DashboardLayout
    personnel/staff/page.jsx
    … 100+ page.jsx
  maintenance/
  blank/
```

**Convention:** `page.jsx` = route UI; `layout.jsx` = wrapper shared; nested layout = nested chrome.

**Yani chi?** File-system routing — na `react-router` Routes tree to app (hooks-e Next: `useRouter` az `next/navigation`).

---

## Qesmat 3 — Root layout (Server)

`src/app/layout.jsx`:

- `export const metadata` / `viewport` — title template Farsi
- `async function getAppConfig()` → `detectLanguage()` (agar na static export)
- `export default async function RootLayout`
- Providers: I18n, Auth (JWT), Settings, Theme (MUI), Motion, Snackbar, ProgressBar, RouteLoading

**Chera async layout?** Server mitune language detect konad ghabl az HTML.  
**Chera `suppressHydrationWarning` roye html?** Theme/dir mismatch SSR vs client common ba MUI color scheme.

**ClientInit:** `ConfigRegistry.set(CONFIG)` — packages shared config az app.

---

## Qesmat 4 — Dashboard layout (Client)

`src/app/dashboard/layout.jsx` — `'use client'`:

```
AuthGuard
  → DashLayout
       DashboardLayout (dynamic import @repo/ui)
       ComponentGuard + RouteAccessGuard
       listeners (SignalR tickets, plate queue)
       children | WorkspacePageHost
```

**Chera dynamic import layout?** Code-split chrome; LoadingScreen ta chunk load.  
**Chera hame dashboard client?** Auth context, nav filter by claims, pathname — browser state (Day 40/49).

**Farz kon:** root shell mitune server bashad; **protected tree** client-e chon token to LS-e.

---

## Qesmat 5 — Page thin pattern

Mesal `personnel/staff/page.jsx`:

```jsx
export default function Page() {
  return (
    <PageGuard componentId={…staff…}>
      <title>{metadata.title}</title>
      <StaffListView />
    </PageGuard>
  );
}
```

**Yani chi?** Route file = permission gate + view import. Logic to `src/sections/staff/...`.

**Chera?** Test/reuse views; App Router folders sholugh nashan; Day 51 feature folders.

---

## Qesmat 6 — Navigation hooks

Wrappers to `src/routes/hooks/`:

- `useRouter` → `next/navigation`
- `usePathname`, `useParams`, `useSearchParams`

**Na** `next/router` (Pages Router). App Router = `next/navigation`.

Interview trap: mix Pages vs App API → runtime error.

---

## Qesmat 7 — React 19 dar codebase (honesty map)

| feature | Dejban? |
|---|---|
| React 19 runtime | **bale** (`react@^19.1.1`) |
| `startTransition` | **bale** (phone-input, image) |
| Server Actions / `'use server'` | **asli na** (API Axios) |
| `useOptimistic` | rare/none for core CRUD |
| `useEffectEvent` | not central |
| React Compiler enabled | check config — **assume off** unless flag |
| Metadata via `<title>` in page | used alongside `metadata` export |

**Band-e sade:** version 19 dareim; pattern-e product hanooz «hooks + Query + RHF».

---

## Qesmat 8 — Turbopack scripts

```json
"dev": "next dev -p 3034 --turbo",
"build": "next build --turbopack"
```

**Yani chi?** Dev HMR sari'-tar; prod build ba Turbopack (Next 16 direction).  
**Smell:** agar plugin webpack-only (svgr custom) → Turbopack edge case — main app has `@svgr/webpack` digar.

---

## Qesmat 9 — Multi-app + basePath

Har product path:

| app | basePath |
|---|---|
| dejban | `/dejban` |
| gate | `/gate` |
| dcc | `/dcc` |
| main | (check config — often root portal) |

Reverse proxy (nginx/Gateway static) path prefix → app. Cookie domain / CORS az Day 40.

---

## Qesmat 10 — Chi Next *nemi*konad inja

- Fetch personnel list az Server Component mostaghim  
- `middleware` auth edge rewrite (file nist)  
- Full PPR marketing pages as primary UX  
- Image optimization as main photo pipeline (DCC/MinIO — Day 28/41)

Next = **host + router + build + React version**. Domain data = backend.

---

# BAKHSH-E SEVOM: farz kon / senario

## Se dastan

**1) Avalin load `/dejban/dashboard/personnel/staff`**  
Next serve HTML shell (layout) → hydrate → AuthGuard check session → getMe → PageGuard → StaffListView → TanStack/SWR/Axios list.

**2) Click nav digar page**  
Client navigation App Router — layout dashboard bemune; faqat `children` avaz. ProgressBar / RouteLoading overlay.

**3) Build deploy**  
`next build --turbopack` → `output standalone` → copy static → PM2/Docker `node server.js` ba port 3034 → proxy `/dejban`.

---

## Smell-ha (dorugh nagu)

1. `typescript.ignoreBuildErrors: true` — type safety weak at CI build  
2. Dashboard almost all client — RSC benefit kam  
3. No middleware — auth faqat client Guard (FOUC / flash?)  
4. Huge `sections/` + MUI — bundle; dynamic import help mikone ama na kafi  
5. React 19 features underused — resume inflated «Actions expert» = risk

---

## Debug checklist

| symptom | check |
|---|---|
| 404 assets | `basePath` / proxy strip |
| Hydration mismatch | theme dir, random id, locale |
| Blank after login | AuthGuard / getMe (Day 40) |
| Slow refresh | Turbopack vs webpack leftover |
| Module not found `@repo/ui` | transpilePackages + workspace install |
| Standalone missing CSS | copy `.next/static` + `public` (main `build:standalone`) |

---

## 25 soal-e mosahebe

1. App Router vs Pages Router?  
2. `'use client'` boundary yani chi?  
3. Chera root layout async?  
4. `basePath` chie?  
5. `output: 'standalone'` chera?  
6. Turbopack vs webpack?  
7. React 19 vs 18 for this app?  
8. Chera data az Axios na RSC?  
9. `next/navigation` vs `next/router`?  
10. Layout nesting?  
11. Dynamic `import()` baraye DashboardLayout?  
12. Metadata API?  
13. Hydration warning common causes?  
14. transpilePackages chera?  
15. Node 20 chera?  
16. Server Actions — estefade mikonim?  
17. middleware — darim?  
18. Static export flag (`isStaticExport`)?  
19. How auth works with LS token + Next?  
20. Multi-app monorepo ports?  
21. startTransition koja?  
22. PPR/Cache Components — claim?  
23. Difference Day 42 vs 54?  
24. How to add new dashboard route?  
25. Security headers in next.config?

---

## Senario-ha (javab kutah)

**S1:** Link be `/dashboard` az birun site bedun `/dejban` → 404. Fix proxy ya Link ba basePath.  

**S2:** Server Component import axiosInstance ba localStorage → crash/undefined. Fix: client only.  

**S3:** Enable React Compiler → unexpected memo; test forms carefully.  

**S4:** `ignoreBuildErrors` hides broken props → runtime. Prefer fix types.  

**S5:** Want SSR personnel SEO → not product goal; intranet app.

---

## Mini lab

1. `npm run dev` in `apps/dejban` — open `/dejban/dashboard`  
2. Read `layout.jsx` root vs dashboard — mark Server vs Client  
3. Add fake `page.jsx` under dashboard — see nav not auto (nav config separate)  
4. Inspect Network: document navigation vs RSC flight (dashboard clicks)  
5. `next build` — find standalone folder  

---

## Resume (1 paragraph)

> Built internal multi-app frontends on **Next.js 16 App Router** and **React 19**, with Turbopack builds, `standalone` deploy, path-based `basePath`, shared monorepo packages via `transpilePackages`, and a client-guarded dashboard shell over JWT/API services.

Keywords: `Next.js 16` · `App Router` · `React 19` · `Turbopack` · `standalone` · `basePath` · `Server Components` · `use client`

---

## File-haye mohem

| path | chera |
|---|---|
| `apps/dejban/package.json` | next/react versions, scripts |
| `apps/dejban/next.config.mjs` | standalone, basePath, transpile |
| `apps/dejban/src/app/layout.jsx` | root RSC providers |
| `apps/dejban/src/app/dashboard/layout.jsx` | client AuthGuard |
| `apps/dejban/src/app/dashboard/**/page.jsx` | routes |
| `apps/dejban/src/app/client-init.jsx` | ConfigRegistry |
| `apps/dejban/src/routes/hooks/*` | navigation wrappers |
| `packages/ui`, `auth`, `api-client` | shared (Day 43) |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 00 | FE tree Turborepo |
| 40 | Auth e2e (Guards, LS, refresh) |
| 41 | Documents FE upload |
| **43** | Turborepo workspaces |
| 44 | TanStack Query + Axios |
| 47 | MUI 7 |
| 49 | Auth UI / componentId |
| 50 | SignalR client |
| 54 | Vite SPA contrast |
| 58 | GitLab CI + PM2 |

---

## Chejori digest koni

1. Farz kon Maghaze A vs B  
2. Bekhun `next.config` + root layout + dashboard layout  
3. Yek `page.jsx` → section trace  
4. Honesty list React 19 features  
5. Resume paragraph seda kon  

---

## Glossary

| term | ma'ni |
|---|---|
| App Router | `app/` file routing |
| Server Component | default, no hooks browser, can async |
| Client Component | `'use client'`, hooks, browser APIs |
| basePath | URL prefix app |
| standalone | minimal Node server output |
| Turbopack | Rust bundler Next |
| hydrate | attach React to SSR HTML |
| Flight | RSC payload protocol (when used) |
| transpilePackages | compile workspace pkgs through Next |

---

## Deep dive — Server vs Client boundary

Default App Router file = Server Component.  
Import-e client library (useState, axios LS) → bayad boundary `'use client'` bala-tarin file.

**Rule of thumb Dejban:**  
- layouts/providers touching auth/theme = client (or wrap)  
- page can stay server if only imports client children (StaffListView is client tree)

**Chera important?** Bundle size + secret leakage (serverenv) + hooks rules.

---

## Deep dive — chera Minimals template?

Package description «Next & JavaScript», version branding 7.x — UI kit Minimals-style.  
Team customized heavily (workspace tabs, SignalR, Jalali, guards).  
Interview: «started from Next admin template, evolved to monorepo product apps.»

---

## Deep dive — JS not TS in apps/dejban

Many `jsx` files; `ignoreBuildErrors: true`.  
Types more in packages/tsconfig; e2e Playwright TS.  
Tradeoff: velocity vs safety — smell for greenfield.

---

## Anti-pattern

| bad | better |
|---|---|
| Fetch in RSC with Bearer from LS | client Query |
| Claim «full SSR app» | «Next shell + CSR dashboard» |
| Put business logic in page.jsx | sections/ |
| Forget basePath in external docs | document `/dejban` |
| Enable every Next 16 cache flag blind | measure |
| Import `next/router` in app dir | `next/navigation` |

---

## Interview 60s

«Our FE is Next 16 App Router on React 19. Root layout is a Server Component for HTML shell and i18n; the dashboard tree is client-side with AuthGuards because tokens live in the browser. We deploy with standalone output and basePath per app, build with Turbopack, and load data through Axios to the YARP gateway—not through RSC database calls.»

---

## Quick self-test

1. Port dejban dev? → 3034  
2. basePath? → `/dejban`  
3. Dashboard layout client? → yes  
4. middleware.ts? → no (current tree)  
5. React major? → 19  
6. Data layer primary? → Axios/client  
7. output prod? → standalone  

---

## Final checklist

- [ ] Next 16 + React 19 versions  
- [ ] App Router map  
- [ ] Server root vs client dashboard  
- [ ] page → section pattern  
- [ ] next.config keys  
- [ ] Turbopack scripts  
- [ ] Honesty React 19 / no middleware  
- [ ] Resume line  

---

## Extra — Farz kon «SSR list personnel»

Agar Server Component `fetch(gateway/personnels)`:  
- koja cookie/refresh?  
- X-Site-Id az koja?  
- cache tag invalidate ba'd az mutate?  

Team javab dad: CSR + TanStack — simpler ba Identity hybrid.  
**Yani chi?** Architecture choice, na Nest weakness.

---

## Extra — Partial Pre-Rendering (WORLD)

PPR = static shell + stream dynamic holes.  
Next 16 Cache Components direction.  
Dejban dashboard dynamic almost everywhere → fayde kam ta redesign.

---

## Extra — React Compiler (WORLD)

Auto memoization — kamtar `useMemo` dasti.  
Risk: libraries assuming referential inequality.  
Dejban: enable gradual + test phone-input / tables.

---

## Extra — `dynamic()` loading

```js
dynamic(() => import('...DashboardLayout'), { loading: () => <LoadingScreen /> })
```

Code split + UX. Hamoon olgu baraye heavy charts (apex, d3 org).

---

## Extra — Title in page body

`<title>{metadata.title}</title>` to Page — React 19 / Next metadata hoisting behavior.  
Root ham `export const metadata`.  
Duplicate strategy — check final document title in DevTools.

---

## Extra — Security headers

next.config `headers()`: frame deny clickjacking-ish SAMEORIGIN, nosniff, referrer.  
Na replacement baraye CSP full — Gateway/nginx momken ezafe.

---

## Extra — allowedDevOrigins

LAN IP list — Next 16+ hardening against cross-origin dev.  
Agar mobile test on `192.168.x` fail → add IP.

---

## Extra — Static export flag

`isStaticExport = false` default.  
Agar `true` → `output: 'export'`, no Node server, `detectLanguage` path change.  
Intranet usually standalone Node.

---

## Map — request types

| type | example |
|---|---|
| Document navigation | first load URL |
| Client transition | click next/link dashboard |
| XHR/fetch | Axios API |
| WS | SignalR (Day 50) |

Next primarily owns first two; Axios third.

---

## Map — folder masooliat

```
app/          routing + providers
sections/     feature UI
services/     *.http.js API
routes/       paths + hooks
layouts/      nav config
packages/*    shared cross-app
```

---

## Lab aha

1. View page source: shell HTML vs empty root  
2. React DevTools: AuthProvider client tree  
3. Break basePath proxy → asset 404  
4. Compare `next build` time turbo vs without (if flag)  
5. Find one `startTransition` usage — read comment why  

---

## What Day 42 is *not*

- Turborepo pipeline deep (Day 43)  
- TanStack Query patterns (Day 44)  
- MUI theme system (Day 47)  
- Guard componentId matrix (Day 49)  
- Vite alternative full (Day 54)  

Focus: **Next 16 + React 19 as the FE runtime in Dejban.**

---

## Resume keywords

`Next.js` · `React 19` · `App Router` · `Turbopack` · `Standalone output` · `basePath` · `Server Components` · `Client Components` · `Monorepo`

---

## Band-e gharardad-e jadid

Next = framing house; React 19 = engine version; dashboard = client rooms; data = Axios trucks to Gateway; Turbopack = faster build tools; standalone = ship container; basePath = street address `/dejban`.

---

## 10 jomle fluency

1. Apps run Next 16 App Router.  
2. React 19 is the UI library version.  
3. Root layout can be async Server Component.  
4. Dashboard layout is client + AuthGuard.  
5. Pages are thin; sections hold UI.  
6. Data loads via Axios, not RSC DB.  
7. basePath prefixes each product app.  
8. standalone output for Node deploy.  
9. Turbopack for dev and build scripts.  
10. Don't overclaim unused Next 16 cache features.

---

## Extra — Comparison «Vite SPA»

| | Next Dejban | Vite Day 54 |
|---|---|---|
| Routing | file app/ | React Router |
| SSR option | yes (underused) | no |
| Deploy | standalone Node | static nginx |
| Monorepo fit | same | same |
| Learning cost | higher | lower |

Hardani: intranet tool → both OK; team chose Next template path.

---

## Extra — Comparison «Pages Router»

Old: `pages/index.js`.  
New: `app/page.jsx`.  
Dejban = App.  
Hook rename + layouts model change — mosahebe classic.

---

## Extra — Soalat chera

**Chera Next 16?** ecosystem + Turbopack + React 19 align.  
**Chera React 19?** dependency of modern Next; forward features.  
**Chera client dashboard?** auth/token/browser APIs.  
**Chera transpilePackages?** workspace source packages.  
**Chera na middleware?** auth model client-centric today.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «Each product is a Next 16 app with App Router. Server root layout boots providers; dashboard is a client subtree behind AuthGuard. Routes are page.jsx files that render section views. We talk to microservices through Axios and the gateway. We build with Turbopack and ship standalone Node with a basePath.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| CSS/js 404 | basePath / assetPrefix / proxy |
| Hydration error | theme, locale, Date.now in render |
| Auth flash | Guard client-only |
| Slow nav | huge client page, no dynamic |
| Build type fail ignored | ignoreBuildErrors |
| `@repo/*` resolve fail | workspaces + transpile |
| Wrong port | 3034 vs proxy target |

---

## Extra — Layer checklist «who renders?»

| layer | renders |
|---|---|
| Node Next server | HTML shell, maybe RSC |
| Browser React | dashboard interactivity |
| Axios | JSON from APIs |
| MUI | components in client tree |

---

## Extra — Related learning days (quick jump)

- Day 00: map apps/packages  
- Day 40: why client auth  
- Day 43: how turbo runs all apps  
- Day 44: data fetching library  
- Day 54: alternate SPA stack  

In ruz = runtime FE asosli.

---

## Extra — Farz kon upgrade 15 → 16

Checklist: Node 20, Turbopack try, async params if dynamic routes, middleware→proxy rename watch, image defaults, remove deprecated lint cmd.  
Test AuthGuard + file upload + SignalR after upgrade.

---

## Extra — Bundle thinking

Heavy: MUI, charts, maps, org-chart d3, tiptap, jspdf.  
Mitigate: route-level code split, dynamic import, don't import all sections in layout.  
Next helps per-page bundles; still client weight.

---

## Extra — Env & CONFIG

`src/global-config` + `@repo/config` — API base URLs, auth method `jwt`, assetsDir.  
ClientInit registers config for packages.  
`.env` Next public vars — never put refresh secrets in `NEXT_PUBLIC_*`.

---

## Extra — Accessibility of architecture

Screen reader / title template Farsi.  
`dir` from settings.  
Not Next-specific — but root layout sets `lang`/`dir` on `<html>`.

---

## Extra — Testing angle

Playwright hits Next server (e2e scripts on app).  
Unit: Vitest more on main; dejban heavy e2e.  
Next route = URL in tests (`/dejban/...`).

---

## Extra — WorkspacePageHost

Optional tabs host inside dashboard layout when setting on.  
Keeps children mounted-ish for multi-page UX — app-like (Next 16.3 narrative) but custom.

---

## Band-e gharardad — ye bar digar sade

1. **Next 16** = framework routing + build + server.  
2. **React 19** = library UI.  
3. **App Router** = folder = URL.  
4. **Server layout** = shell + providers bootstrap.  
5. **Client dashboard** = guards + real app.  
6. **page.jsx** = thin gate + view.  
7. **Axios** = data (ba'dan Day 44).  
8. **standalone + basePath** = deploy reality.  
9. **Turbopack** = sari' build/dev.  
10. **Honesty** = CSR product, na full RSC platform.

---

## Extra — Capacity mental model

Yek user → yek Next Node process mitune chand connection.  
CPU: SSR shell cheap; heavy = browser.  
Scale FE: horizontal Next replicas + sticky na lazeme for JWT LS model.  
Static assets often CDN/nginx in front.

---

## Extra — Error boundaries

React error boundary mostly client trees.  
Next `error.jsx` / `global-error.jsx` — check if present; else MUI crash = white screen.  
Lab: throw in section → behavior?

---

## Extra — Loading UI

`loading.jsx` App Router optional.  
Dejban: ProgressBar + RouteLoadingProvider + dynamic loading screen.  
Multiple systems — midunam koja look.

---

## Extra — Parallel routes / intercepting

Advanced App Router (modals).  
Dejban primarily classic nested dashboard — claim nakon unless file `@folder` didi.

---

## Khoruj-e zehni

> Midunam FE Dejban roye Next.js 16 App Router + React 19 hast; root layout server-e, dashboard client ba AuthGuard; page-ha thin-an; data ba Axios; build Turbopack; deploy standalone ba basePath; va feature-haye Next 16/React 19 ke estefade nashodan ro inflated claim nemikonam.

Age in paragraph mal-e to shod — Day 42 done.

---

*Day 42 tamum. Ba'd: Day 43 — Turborepo + workspaces (amade). Fehrest: [README.md](./README.md).*
