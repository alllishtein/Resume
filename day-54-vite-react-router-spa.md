# Day 54 — Vite + React Router SPA

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** hame-ye FE monorepo Next-e (Day 42)? SPA Vite+Router kojast?

**Javab monorepo (honesty):**

| app | bundler / router |
|---|---|
| `apps/dejban`, `main`, `gate`, `dcc` | **Next.js 16** App Router |
| **`apps/access-control`** | **Vite 6 + React Router 8** (SPA) |
| `apps/gate` | Next — ama `react-router-dom` dep **unused** (leftover) |

Zincir-ezehni access-control:

```
Browser → https://host/access-control/...
  → (prod) main Next rewrites → Vite static / Vite preview
  → index.html + main.jsx
  → createBrowserRouter({ basename: '/access-control' })
  → App providers (auth/theme/i18n)
  → dashboardRoutes (lazy pages) + AuthGuard
  → Axios (@repo/api-client) → Gateway
```

Olgu:

```js
createBrowserRouter([{ Component: AppShell, children: routesSection }],
  { basename: '/access-control' })
→ <RouterProvider router={router} />
```

Vite: `base: VITE_BASE || '/access-control'`, port **3033**, plugin `@vitejs/plugin-react-swc`.

**Band-e gharardad-e jadid:** farz kon / yani chi / chera + **direction:** product asosli Next; AC = SPA zir-masir.

Day 42 = Next. Day 43 = monorepo. Day 53 = SWR (AC data). **In ruz = Vite + React Router.**

---

# BAKHSH-E AVAL: WORLD — Vite + SPA + React Router

## Farz kon — forushgah vs kiosk

**Next (Day 42):** forushgah bozorg — server mitune HTML avaliye bede, route file-based.

**Vite SPA:** kiosk — yek `index.html`, JS hame route-ha ra client handle mikone. Refresh deep link → server bayad `index.html` bede (fallback).

**Yani chi:** SPA = Single Page Application. Navigation = client history API, na full document load.

---

## Vite chie?

Build tool / dev server: esbuild+Rollup ecosystem, HMR sari, config kuchek.

| mafhum | ma'ni |
|---|---|
| `vite` | dev server |
| `vite build` | production bundle → `dist/` |
| `vite preview` | serve dist |
| `import.meta.env` | env vars (`VITE_*`) |
| plugin-react-swc | Fast Refresh ba SWC |
| `base` | public path prefix |

Vs Next: Vite na App Router, na RSC, na `page.jsx` file convention — to khodet router mizari.

---

## React Router (v6/v7/v8 data APIs)

Classic: `<BrowserRouter><Routes><Route/></Routes></BrowserRouter>`.

Modern (AC):

```js
createBrowserRouter(routes, { basename })
<RouterProvider router={router} />
```

| API | naqsh |
|---|---|
| `createBrowserRouter` | route tree + data APIs |
| `Outlet` | child slot |
| `Navigate` | redirect |
| `Link` / `NavLink` | client links |
| `useNavigate` | imperative nav |
| `useParams` / `useLocation` / `useSearchParams` | URL state |
| `useRouteError` | errorElement |
| `lazy` + `Suspense` | code split pages |

Package name: AC uses **`react-router`** (v8) — unified package; older tutorials `react-router-dom`.

---

## Chera SPA digar Next?

| need | Vite SPA | Next |
|---|---|---|
| SEO marketing | za'if (CSR) | SSR/SSG |
| Admin dashboard | ali | ali (Dejban style) |
| Deploy static | `dist/` + nginx | Node server / standalone |
| Subpath embed | `base` + `basename` | basePath / rewrites |
| Shared monorepo packages | alias / optimizeDeps | transpilePackages |

Dejban: asosli Next; AC deliberately Vite — product split + Minimals Vite template history.

---

# BAKHSH-E DOVOM: DEJBAN — access-control

## Qesmat 1 — `vite.config.js`

```js
const PORT = 3033;
export default defineConfig({
  build: { target: 'es2021' },
  plugins: [react(), checker({ eslint: ... })],
  base: process.env.VITE_BASE || '/access-control',
  resolve: { alias: [ { find: /^src(.+)/, replacement: ... } ] },
  server: { port: PORT, host: true, hmr: { protocol: 'ws', host: 'localhost', port: PORT } },
  preview: { port: PORT, host: true },
});
```

**Chera `base`?** Asset URLs mesl `/access-control/assets/...` — app zir-domin/path main zendegi mikone.

**Chera alias `src/`?** Import `src/routes/...` bedune deep relative.

**Chera checker plugin?** ESLint overlay dar dev.

---

## Qesmat 2 — `index.html` entry

```html
<base href="/access-control/" />
<div id="root"></div>
<script src="config.js"></script>
<script type="module" src="src/main.jsx"></script>
```

SPA classic: HTML shell + module entry.  
`config.js` runtime config (env-like without rebuild — pattern deploy).

---

## Qesmat 3 — `main.jsx` router bootstrap

```js
const router = createBrowserRouter(
  [{
    Component: () => (
      <ConfigProvider value={CONFIG}>
        <App><Outlet /></App>
      </ConfigProvider>
    ),
    errorElement: <ErrorBoundary />,
    children: routesSection,
  }],
  { basename: '/access-control' }
);
createRoot(...).render(<RouterProvider router={router} />);
```

**Yani chi:**

- `basename` = route paths relative to `/access-control`
- Root layout wraps **all** children ba App providers
- `errorElement` = React Router error boundary

**Dev-only hash token:**

```js
if (import.meta.env.DEV) {
  // #accessToken=... from main app cross-origin
  localStorage.setItem('jwt_access_token', token);
}
```

Prod: same-origin via rewrites → localStorage share. Day 40/49 auth.

---

## Qesmat 4 — `routes/sections`

```
routes/
  paths.js              ← path helpers (links)
  sections/index.jsx    ← routesSection merge
  sections/dashboard.jsx
  sections/main.jsx     ← 404/403/500
  hooks/use-router.js   ← Next-like push/replace
  components/error-boundary.jsx
  components/router-link.jsx
```

`routesSection` = dashboardRoutes + mainRoutes + `*` → Navigate `/404`.

---

## Qesmat 5 — dashboard routes + lazy

```js
const DevicesPage = lazy(() => import('src/pages/dashboard/device/list'));
// ...
export const dashboardRoutes = [{
  path: '/',
  element: CONFIG.auth.skip
    ? <DashboardLayoutWrapper />
    : <AuthGuard><DashboardLayoutWrapper /></AuthGuard>,
  children: [
    { index: true, element: <IndexPage /> },
    { path: 'device', children: [
      { index: true, element: <DevicesPage /> },
      { path: 'list', element: <DevicesPage /> },
      { path: ':id', element: <DevicePage /> },
      { path: ':id/edit', element: <EditDevicePage /> },
      { path: 'create', element: <NewDevicePage /> },
    ]},
    // deviceType, region, calendar, accessGroup, ...
  ],
}];
```

`DashboardLayoutWrapper`: `Outlet` + Suspense + `@repo/ui` DashboardLayout + navData.

**Chera lazy?** Code-split — first paint kuchektar; har page chunk.

**Chera AuthGuard?** Same shared package as Next apps (Day 49).

---

## Qesmat 6 — `paths.js`

Central path builders:

```js
dashboard: {
  device: {
    root: `/device`,
    create: `/device/create`,
    edit: (id) => `/device/${id}/edit`,
    details: (id) => `/device/${id}`,
  },
  // ...
}
```

UI: `router.push(paths.dashboard.device.edit(id))` — string magic kam.

**Note:** paths relative to basename (no `/access-control` prefix inside helpers) — Router adds basename.

---

## Qesmat 7 — `useRouter` adapter

```js
export function useRouter() {
  const navigate = useNavigate();
  return useMemo(() => ({
    back: () => navigate(-1),
    push: (href, state = {}) => navigate(href, { state }),
    replace: (href) => navigate(href, { replace: true }),
    refresh: () => {}, // no-op — Next parity stub
  }), [navigate]);
}
```

**Chera?** Shared UI / mental model Next `useRouter` — AC implements subset.  
`refresh` empty: SPA nadare Next router.refresh.

---

## Qesmat 8 — App providers stack

`app.jsx`: I18n → Auth → Settings → Localization → Theme (`noSsr`) → Motion → Snackbar → children.

**Chera `noSsr` Theme?** Vite SPA — SSR nist; skip SSR hydration theme dance.

Shared: `@repo/ui`, `@repo/config` ConfigRegistry — monorepo (Day 43) works with Vite too (alias/source), not only Next transpilePackages.

---

## Qesmat 9 — main Next rewrite bridge

`apps/main/next.config.mjs`:

```js
source: '/access-control'
destination: `${subAppDomains.accessControl}/access-control/`
source: '/access-control/:path+'
destination: `.../access-control/:path+`
```

**Farz kon:** user az portal main miravad `/access-control/device` — Next rewrite proxy/proxy-like be Vite app.  
Browser URL still under main host path — one origin feeling.

`proxy.js` matcher includes `/access-control/:path*`.

---

## Qesmat 10 — env: `import.meta.env`

```js
import.meta.env.VITE_SERVER_URL
import.meta.env.VITE_SIGNALR_HUB_URL
import.meta.env.DEV
import.meta.env.VITE_APP_VERSION
```

Vite only exposes `VITE_*` (security).  
Contrast Next: `NEXT_PUBLIC_*` / `process.env`.

`global-config.js` → `createAppConfig` az `@repo/config`.

---

## Qesmat 11 — data layer reminder

AC lists = **SWR** actions (Day 53), na TanStack Query.  
Router ≠ data cache — faghat URL/navigation.

---

## Qesmat 12 — gate leftover

`apps/gate` = Next + unused `react-router-dom`.  
Don't claim gate is Vite SPA. Cleanup candidate.

---

# BAKHSH-E SEVOM: Vite SPA vs Next (jadval mosahebe)

| topic | access-control (Vite) | dejban (Next) |
|---|---|---|
| Entry | `index.html` + `main.jsx` | `app/layout.jsx` |
| Routes | `createBrowserRouter` objects | file `app/**/page.jsx` |
| Nav helper | `useRouter` adapter | next/navigation |
| Env | `import.meta.env.VITE_*` | `NEXT_PUBLIC_*` |
| Deploy unit | static `dist` / preview | Node Next server |
| Path prefix | `base` + `basename` | rewrite / basePath |
| Data fetch | SWR actions | TanStack Query services |
| Auth UI | same `@repo/ui` AuthGuard | same |
| Port dev | 3033 | 3034 (dejban) etc. |

---

# BAKHSH-E CHAHAROM: WORLD extras useful

## History modes

- Browser history (`createBrowserRouter`) — clean URLs, needs server fallback  
- Hash router — `#/device` — rare admin  

AC = browser + basename.

## Nested routes

Parent layout `Outlet` — dashboard shell; child pages swap.  
Same idea Next layout.jsx — different API.

## Loaders / actions (RR data APIs)

WORLD: `loader` before render.  
AC mostly **doesn't** use loaders — fetch in SWR hooks instead. Honesty.

## Link vs `<a>`

`<Link>` client nav; raw `<a href>` full reload — break SPA feel + lose cache warm.

## 404

`{ path: '*', element: <Navigate to="/404" replace /> }` + mainRoutes pages.

---

# BAKHSH-E PANJOM: farz kon / senario

## Se dastan

**1) Dev AC alone**  
`yarn dev` Vite :3033 → open `/access-control/` (base) → login/token → devices list.

**2) Prod via main**  
User clicks Access Control in portal → `/access-control/...` rewrite → SPA chunks → basename matches.

**3) Deep link refresh**  
`/access-control/device/123` — server must serve SPA index for that path (Vite preview / nginx try_files / rewrite). Age 404 static file — misconfig.

---

## Smell-ha

1. Dual FE frameworks in monorepo (Next + Vite) — onboarding cost  
2. `useRouter.refresh` no-op — fake Next parity  
3. gate unused react-router-dom  
4. Day 43 docs sometimes say «all Next» — AC exception  
5. Copy-paste Minimals — `clean` script mentions `.next` on Vite app  
6. Empty string detail keys in SWR (Day 53) orthogonal smell  
7. Hash token only DEV — prod assumes shared origin  

---

## Debug checklist

| symptom | check |
|---|---|
| White screen assets 404 | `base` / `<base href>` mismatch |
| Routes always 404 | `basename` vs deployed path |
| Refresh 404 | server fallback to index.html |
| HMR broken | server.hmr host/port |
| Auth lost cross-origin dev | hash token / localStorage origin |
| Shared UI not updating | Vite optimizeDeps / restart |
| Wrong app mental model | AC≠dejban router |

---

## 25 soal-e mosahebe

1. Kodom app Vite?  
2. createBrowserRouter vs BrowserRouter?  
3. basename chera?  
4. Vite `base` chera?  
5. import.meta.env vs process.env?  
6. lazy routes chera?  
7. AuthGuard koja?  
8. useRouter.push underneath?  
9. refresh no-op yani chi?  
10. main rewrite?  
11. Port AC?  
12. SWR ya Query in AC?  
13. ErrorBoundary RR?  
14. index.html role?  
15. vs Next file routes?  
16. SWC plugin?  
17. ConfigRegistry?  
18. gate SPA?  
19. Deep link refresh need?  
20. Link vs a?  
21. Outlet?  
22. paths.js?  
23. DEV accessToken hash?  
24. Day 42 relation?  
25. One-liner Day 54?

---

## Senario-ha

**S1:** Change base to `/ac` — must update basename + HTML base + rewrite.  
**S2:** Add page `firmware` — lazy import + child route + paths helper.  
**S3:** Navigate with state — `push(href, state)` → `useLocation().state`.  
**S4:** Build CI — `vite build` artifact; nginx root + try_files.  
**S5:** Share button to device detail — URL must include `/access-control` prefix externally.

---

## Mini lab

1. Read `vite.config.js` base + port  
2. Read `main.jsx` createBrowserRouter  
3. Trace `dashboard.jsx` device children  
4. Open `apps/main/next.config.mjs` rewrites  
5. `rg "from 'react-router'" apps/access-control`  
6. Confirm no useSWR in routing files (separation)

---

## Resume (1 paragraph)

> The monorepo's **access-control** app is a **Vite 6 SPA** routed with **React Router 8** (`createBrowserRouter`, basename `/access-control`), lazy dashboard pages under a shared AuthGuard/layout from `@repo/ui`, while the main Dejban product apps stay on **Next.js**—with **main** rewriting `/access-control/*` to the Vite deployment.

Keywords: `Vite` · `createBrowserRouter` · `basename` · `base` · `RouterProvider` · `lazy` · `SPA` · `import.meta.env`

---

## File-haye mohem

| path | chera |
|---|---|
| `apps/access-control/vite.config.js` | Vite base/port/alias |
| `apps/access-control/index.html` | SPA shell |
| `apps/access-control/src/main.jsx` | router bootstrap |
| `apps/access-control/src/routes/**` | route tree + hooks |
| `apps/access-control/src/app.jsx` | providers |
| `apps/main/next.config.mjs` | rewrites bridge |
| Day 42 / 43 / 53 | Next / monorepo / SWR |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 42 | Next contrast |
| 43 | workspaces — AC member |
| 49 | AuthGuard shared |
| 50 | SignalR client possible in AC |
| 53 | SWR data on AC |
| **54** | this |
| 55 | Playwright/Vitest (tooling) |

---

## Chejori digest koni

1. SPA = client router + index.html  
2. AC = only Vite app that matters  
3. basename + base + rewrite triangle  
4. lazy dashboard routes  
5. Next vs Vite honesty table  

---

## Glossary

| term | ma'ni |
|---|---|
| SPA | single page app |
| Vite | FE build/dev tool |
| base | asset public path |
| basename | router URL prefix |
| createBrowserRouter | RR data router factory |
| Outlet | nested child slot |
| lazy | dynamic import page |
| HMR | hot module replace |
| rewrite | Next proxy path to AC |
| import.meta.env | Vite env object |

---

## Deep dive — basename vs base

| | Vite `base` | RR `basename` |
|---|---|---|
| Affects | JS/CSS/asset URLs | matching location.pathname |
| Config | vite.config / HTML base | createBrowserRouter option |
| Must | align with deploy path | align with deploy path |

Mismatch = broken CSS or blank routes.

---

## Deep dive — code splitting

`lazy(() => import(...))` → separate chunk per page.  
Suspense fallback LoadingScreen / SplashScreen.  
First visit device list downloads that chunk once (cached).

---

## Deep dive — ConfigProvider

Root route Component wraps ConfigProvider + App.  
Packages read CONFIG via registry — same monorepo pattern as Next apps initializing config.

---

## Anti-pattern

| bad | better |
|---|---|
| Claim all apps Vite | only AC |
| Hardcode `/access-control` in every Link | paths + basename |
| Full page `<a>` for in-app | `Link` / useRouter |
| Forget server fallback | try_files / rewrite |
| Put loaders unused then expect SSR | AC is CSR+SWR |
| Copy Next `use client` everywhere | irrelevant in Vite |

---

## Interview 60s

«Access-control is a Vite SPA with React Router's createBrowserRouter under basename /access-control. Pages are lazy-loaded inside an AuthGuard dashboard layout from shared packages. The main Next app rewrites that path to the Vite deployment. Other product apps remain Next.js.»

---

## Quick self-test

1. Vite app? → access-control  
2. Router API? → createBrowserRouter  
3. basename? → /access-control  
4. Port? → 3033  
5. Data? → SWR  
6. Bridge? → main rewrites  
7. refresh()? → no-op  

---

## Final checklist

- [ ] SPA mental model  
- [ ] Vite config base  
- [ ] RR bootstrap  
- [ ] lazy + AuthGuard  
- [ ] paths + useRouter  
- [ ] rewrite bridge  
- [ ] vs Next table  
- [ ] resume  

---

## Extra — Farz kon deploy nginx

```
location /access-control/ {
  alias /var/www/ac/dist/;
  try_files $uri $uri/ /access-control/index.html;
}
```

Bedune try_files → refresh /device → 404.

---

## Extra — Vitest vs Vite

Root monorepo has `vitest` — unit test runner (Day 55).  
Vitest powered by Vite transform — related tooling, not AC router.

---

## Extra — plugin-basic-ssl

AC package.json may include `@vitejs/plugin-basic-ssl` — HTTPS local optional.  
Check if enabled in config (current config snippet may omit) — know exists for CORS/cookie experiments.

---

## Extra — Scroll restoration

`useScrollToTop` on pathname change in App — SPA doesn't auto scroll like full navigation.

---

## Extra — ProgressBar

Minimals ProgressBar on route change — UX polish SPA.

---

## Extra — compare Remix/RR loaders

If mosahebe asks loaders: AC chose hooks (SWR) over route loaders — valid CSR admin style.

---

## Extra — TypeScript

AC JS; Vite supports TS out of box. Migration orthogonal.

---

## Extra — turbo pipeline

`turbo run build` includes AC `vite build` if pipeline lists it.  
Concurrency OOM note Day 43 — Vite lighter than Next usually.

---

## Extra — public assets

`public/` copied as-is under base.  
Logo paths respect `/access-control/...`.

---

## Extra — React 19

AC uses React 19 with Vite — createRoot same as Next client.  
RSC features not available — honesty.

---

## Band-e gharardad-e jadid

Vite = ashpazkhane sari build.  
index.html = zarf.  
React Router = nagshe-ye agahi dakhel maghaze.  
basename = shomare tabaghe (`/access-control`).  
lazy = asansor per section.  
AuthGuard = amniat dar.  
main rewrite = darvaze az forushgah Next be kiosk AC.  
SWR = anbar data (Day 53).  

Yek mall, do noe maghaze: Next + Vite.

---

## 10 jomle fluency

1. access-control is our Vite SPA.  
2. Routing uses createBrowserRouter.  
3. basename is /access-control.  
4. Vite base matches that path.  
5. Pages are React.lazy imports.  
6. AuthGuard wraps the dashboard layout.  
7. useRouter wraps useNavigate.  
8. main rewrites proxy the path.  
9. Env vars are import.meta.env.VITE_*.  
10. Dejban core apps stay on Next.

---

## Extra — version pins

| pkg | AC |
|---|---|
| vite | ^6.3.5 |
| react-router | ^8.3.0 |
| @vitejs/plugin-react-swc | ^3.8.1 |

---

## Extra — HMR websocket

`server.hmr` explicit host localhost + port — behind docker/proxy sometimes need tune.  
Symptom: full reload instead of hot — check hmr config.

---

## Extra — ErrorBoundary classes

Custom dark error UI for route errors — `useRouteError` + `isRouteErrorResponse`.  
Different from React class error boundary — RR-aware.

---

## Extra — Navigate replace

`Navigate to="/404" replace` — dirty history stack avoidance.

---

## Extra — index vs list paths

Both `device` index and `device/list` → same DevicesPage — convenience URLs.

---

## Extra — state on navigate

`push(href, state)` for pass ephemeral UI state without query string — refresh loses state (expected).

---

## Extra — why not convert AC to Next?

Cost vs benefit; works; SWR+Vite template; separate product surface.  
Possible future — not current.

---

## Extra — why not convert dejban to Vite?

SSR options, already invested App Router structure, Query ecosystem docs, team standard.  

---

## Extra — security same-origin

Prod rewrite same host → cookie/localStorage simpler.  
DEV multi-port → hash token bridge.

---

## Extra — Bundle analyzer

Optional `rollup-plugin-visualizer` — not required; know for perf interview.

---

## Extra — CSS

Emotion/MUI same as Next apps via `@repo/ui`.  
`@repo/ui/global-css` imported in App.

---

## Extra — Testing routes

MemoryRouter / createMemoryRouter in unit tests — WORLD tip.  
E2E = Playwright against base URL (Day 55).

---

## Extra — 10 soalat sari

1. SPA app? AC  
2. Next apps? dejban/main/gate/dcc  
3. basename? /access-control  
4. Factory? createBrowserRouter  
5. Env? import.meta.env  
6. Lazy? yes  
7. Guard? AuthGuard  
8. Data? SWR  
9. Bridge? rewrite  
10. gate Vite? no  

---

## Extra — Diagram 30s mosahebe

Begu: «Vite builds a static SPA. React Router owns client URLs under /access-control. Shared Auth and UI packages wrap lazy pages. Main Next rewrites that prefix to the SPA.»  

---

## Extra — Common bugs

| symptom | likely |
|---|---|
| JS loads, routes blank | basename |
| CSS 404 | base |
| API CORS local | different ports — expected |
| Token missing after jump from main | DEV hash not applied |
| Chunk load error after deploy | old index + new hashed assets — cache |

---

## Extra — Layer checklist AC FE

| layer | tech |
|---|---|
| Bundler | Vite 6 |
| Router | React Router 8 |
| Auth | @repo/ui AuthGuard |
| Data | SWR actions |
| UI kit | MUI + @repo/ui |
| Config | @repo/config + VITE_* |
| Host bridge | main rewrites |

---

## Extra — Farz kon add route step-by-step

1. `pages/dashboard/foo/list.jsx`  
2. `lazy(() => import(...))` in dashboard.jsx  
3. children path `foo`  
4. `paths.dashboard.foo`  
5. nav-config-dashboard item  
6. SWR action if list API  

---

## Extra — import.meta.glob

Vite feature for many pages — AC uses explicit lazy instead (clearer).

---

## Extra — SSR Vite (WORLD)

Vite SSR / Remix possible — **not** AC architecture. Don't invent.

---

## Extra — PM2 / CI

Build outputs `dist`; serve static or preview.  
Exact PM2 process name = ops Day 58 — know artifact type differs from Next `.next`.

---

## Extra — Concurrent AC + dejban dev

Two ports; from main rewrite need subAppDomains point to 3033.  
Local env files matter.

---

## Extra — React StrictMode

If enabled, double mount effects — SWR/devtools awareness.

---

## Extra — Final fluency drill

«Access-control runs on Vite with React Router under /access-control. The main app rewrites that path. Pages are lazy and guarded. Data still goes through Axios and SWR. Dejban itself is Next, not Vite.»

---

## Khoruj-e zehni

> Midunam access-control SPA-ye Vite + React Router-e ba basename /access-control; createBrowserRouter + lazy dashboard + AuthGuard; base/VITE env; main rewrite bridge; va baghiye product apps Next mimanand.

Age in paragraph mal-e to shod — Day 54 done.

---

*Day 54 tamum. Ba'd: Day 55 — Playwright + Vitest (amade). Fehrest: [README.md](./README.md).*