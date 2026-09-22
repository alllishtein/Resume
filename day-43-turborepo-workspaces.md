# Day 43 — Turborepo + workspaces

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** chand Next app (`dejban`, `main`, `gate`, `dcc`, …) + shared UI/auth/axios — chejori yek repo, yek `npm install`, yek `build`?

**Javab Dejban:** **npm workspaces** (link packages) + **Turborepo 2** (orchestrate tasks + cache).

```
dejban_frontend_new/          ← root package: pg_frontend
├── apps/*                    ← Next apps (workspace members)
├── packages/*                ← @repo/ui, auth, api-client, config, …
├── package.json              ← workspaces + turbo scripts
├── turbo.json                ← task graph (build/dev/lint/…)
└── .gitlab-ci.yml            ← turbo build --concurrency=1 → PM2
```

Root scripts:

| script | anjam |
|---|---|
| `npm run dev` | `turbo run dev` — hame app-haye `dev` parallel (persistent) |
| `npm run build` | `turbo run build` — ba dependency `^build` |
| `npm run lint` | `turbo run lint` |
| `npm run start` | `turbo run start` (ba'd az build) |
| `test:e2e` / `test:unit` | turbo, **cache: false** |

**Band-e gharardad-e jadid:** farz kon / yani chi / chera — monorepo = *chand maghaze yek mall*.

Day 42 = yek Next app. **In ruz = chand app + shared packages + Turbo pipeline.**

---

# BAKHSH-E AVAL: WORLD — monorepo chie?

## Farz kon — mall vs maghaze-ye joda

**Bad (multi-repo):** har app clone joda, copy-paste AuthGuard, version drift Axios.

**Good (monorepo):** yek git; packages shared; taghir `@repo/ui` → hame app-ha mibinan (ba'd az rebuild).

| tool | kar |
|---|---|
| **npm/pnpm/yarn workspaces** | install + symlink `node_modules/@repo/...` |
| **Turborepo** | run `build`/`lint` ba tartib + **cache** output |
| (optional) Nx / Bazel | hamin idea, tool digar |

Dejban: **npm workspaces + turbo@^2.10** — na pnpm-workspace file.

---

## Chera Turborepo (na faqat `npm run -w`)?

Workspaces = *che package-ha hastan*.  
Turbo = *che task-ha, tartib, cache, filter*.

```
turbo run build
  → topological: packages first (^build), ba'd apps
  → cache hit? skip rebuild
  → outputs: .next/**, dist/**
```

**Yani chi?** CI sari'-tar; local `build` hoshmand; `dev` concurrent multi-app.

---

## `^build` yani chi? (mohem)

to `turbo.json`:

```json
"build": { "dependsOn": ["^build"], "outputs": [".next/**", "!.next/cache/**", "dist/**"] }
```

`^` = dependency workspace-ha-ye *upstream* bayad `build` konan ghabl az to.

**Farz kon:** app `dejban` depend `@repo/ui`. Agar ui script `build` dashte bashad → aval ui.  

**Honesty Dejban:** `@repo/ui` bishtar **source export** (`.jsx`/`.js`) — Next `transpilePackages` compile mikone; package `build` script kam/empty. Graph hanuz useful baraye app-ha-i ke `build` daran + cache keys.

---

# BAKHSH-E DOVOM: DEJBAN — root

## Qesmat 1 — root `package.json`

```json
"name": "pg_frontend",
"private": true,
"packageManager": "npm@10.9.2",
"workspaces": ["apps/*", "packages/*"],
"engines": { "node": ">=20" }
```

`devDependencies` root: `turbo`, `typescript`, `prettier`, Playwright/Vitest tooling shared.

`optionalDependencies`: platform binaries (`@turbo/windows-64`, `@next/swc-*`) — install sari'tar/CI.

**Chera private?** Publish be npm nist — internal monorepo.

---

## Qesmat 2 — `turbo.json` (kamels)

Schema: `v2-10-12`. `"ui": "tui"` — terminal UI Turbo 2.

| task | cache | dependsOn | notes |
|---|---|---|---|
| `build` | yes (default) | `^build` | env `NODE_ENV`, `BUILD_STATIC_EXPORT`; passThrough `NEXT_PUBLIC_*`, `PLAYWRIGHT_*`; inputs default + `.env*` |
| `dev` | **false** | — | `persistent: true` (long-running) |
| `start` | **false** | `build` | persistent; prod serve |
| `lint` | | `^lint` | |
| `check-types` | | `^check-types` | |
| `test:e2e` | **false** | — | passThrough CI/Playwright env |
| `test:unit` | **false** | — | |

**Chera e2e/unit no cache?** Side-effect + flaky; wrong cache = false green.

**Chera dev no cache?** Dev server state; cache meaningless.

---

## Qesmat 3 — apps (workspace members)

| folder | naqsh |
|---|---|
| `apps/dejban` | asosli AC dashboard |
| `apps/main` | portal / auth entry |
| `apps/gate` | gate UI |
| `apps/dcc` | documents UI |
| `apps/access-control` | access-control product |

Har kodam `package.json` name joda + scripts `dev`/`build`/`lint` ke Turbo seda mizane.

Dependencies moshtarak:

```json
"@repo/ui": "*",
"@repo/auth": "*",
"@repo/api-client": "*",
"@repo/config": "*"
```

`*` to workspace = *local version*, na semver npm registry.

---

## Qesmat 4 — packages

| name | masooliat |
|---|---|
| `@repo/ui` | theme, layouts, guards, snackbar, MRT, SignalR util, branding, … **exports map** bozorg |
| `@repo/auth` | auth helpers (thin; depend api-client) |
| `@repo/api-client` | Axios instance, tokenStorage, error extract |
| `@repo/config` | `ConfigRegistry`, `AppConfig` / `createAppConfig` |
| `@repo/eslint-config` | shared ESLint (`./base`, `./next-js`, …) |
| `@repo/typescript-config` | shared tsconfig presets |

**Farz kon:** taghir `tokenStorage` → hame app-ha ba yek fix.  
**Chera ui exports granular?** `import { x } from '@repo/ui/auth-guard'` — tree-shake / clear public API (na deep relative path).

---

## Qesmat 5 — link flow (yani chi install)

```
npm ci   (root)
  → npm workspaces hoist + symlink
  → node_modules/@repo/ui → ../../packages/ui
  → apps/dejban/node_modules/@repo/... → same
```

Next: `transpilePackages: ['@repo/ui', ...]` (Day 42) chon source JS/TS az package mikhune, na prebuilt dist.

**Smell:** duplicate heavy deps (MUI) to app + peerDependencies ui — version align carefully.

---

## Qesmat 6 — dependency graph (zehni)

```
@repo/typescript-config / eslint-config   (tooling)
         ↑
@repo/config
@repo/api-client
         ↑
@repo/auth
         ↑
@repo/ui  (depends config, api-client, auth + peers MUI/react)
         ↑
apps/* (Next)
```

Cycle na: ui ↔ app. App import ui; ui **na** import az `apps/dejban`.

---

## Qesmat 7 — CI deploy (vaghe'i)

`.gitlab-ci.yml` (kholase):

1. SSH server  
2. `nvm use 22`  
3. pull `dejban_frontend_new_turborepo`  
4. `npm ci --prefer-offline`  
5. `NODE_OPTIONS=--max-old-space-size=3072`  
6. **`npx turbo run build --concurrency=1 --no-daemon`**  
7. PM2 restart `dejban_frontend_new_turborepo` → `npm start`

**Chera concurrency=1?** Comment: OOM kill Node — chand Next build parallel RAM mikhore.  
**Chera --no-daemon?** CI clean process; no leftover turbo daemon.  
**Yani chi?** Turbo *mitune* parallel; production server *policy* serialize.

Day 58 deepen PM2 — inja faqat monorepo build story.

---

## Qesmat 8 — filter (WORLD + handy)

Turbo CLI (common):

```bash
npx turbo run build --filter=dejban
npx turbo run dev --filter=main
npx turbo run lint --filter=@repo/ui
```

**Farz kon:** faqat gate taghir — build hame apps waste. Filter = local productivity.

---

## Qesmat 9 — cache mental model

Inputs: source files + env listed + `.env*`.  
Outputs: `.next/**` (minus cache) + `dist/**`.  
Hit = restore outputs, skip work.

**CI cold:** cache empty ya remote cache nist (Dejban CI local server build — remote Turbo cache maybe not configured).  
**Honesty:** fayde cache bishtar local + repeat build; CI always full-ish ba concurrency 1.

---

## Qesmat 10 — packageManager field

`"packageManager": "npm@10.9.2"` — Corepack pin.  
Team npm; **na** pnpm lock.  
Agar kasi yarn/pnpm mix → hell. Stick to npm.

---

# BAKHSH-E SEVOM: farz kon / senario

## Se dastan

**1) Developer morning**  
`npm run dev` → Turbo starts `dev` on apps that define it → chand port (3034 dejban, …). Edit `@repo/ui` → HMR through Next transpile.

**2) Fix axios refresh**  
Taghir `packages/api-client` → hame apps inherit; rebuild/test affected apps.

**3) Release**  
Push master → GitLab SSH → `turbo build --concurrency=1` → PM2 `turbo run start` (root script).

---

## Smell-ha

1. Root `dependencies` xlsx — odd hoist; prefer app-level if only one consumer  
2. ui peerDependencies optional meta — confusing for newcomers  
3. No remote cache → CI always heavy  
4. concurrency 1 = slow deploy (trade RAM)  
5. `access-control` vs `dejban` overlap risk — product split discipline  
6. Duplicate components still in some apps (historical) + packages/ui — migration incomplete possible  

---

## Debug checklist

| symptom | check |
|---|---|
| Cannot find `@repo/ui` | root `npm i`; workspaces; delete nested broken node_modules |
| Old UI after edit | Next cache; restart dev; transpilePackages list |
| Turbo skip wrong | `--force`; check outputs path |
| OOM build | concurrency 1; NODE_OPTIONS heap |
| Wrong app started | `--filter=` |
| Peer react mismatch | align 19.x across apps |
| CI npm ci fail | lockfile commit; Node 22 vs engines 20 |

---

## 25 soal-e mosahebe

1. Workspace vs Turbo?  
2. Chera `*` version?  
3. `^build` chie?  
4. Chera `dev` cache false?  
5. transpilePackages chera ba monorepo?  
6. exports map `@repo/ui`?  
7. Filter turbo?  
8. concurrency CI chera 1?  
9. packageManager field?  
10. Cycle dependency chejori avoid?  
11. Hoisting?  
12. optionalDependencies turbo binary?  
13. start dependsOn build?  
14. passThroughEnv NEXT_PUBLIC?  
15. Difference monorepo vs multi-repo?  
16. pnpm vs npm workspaces here?  
17. Remote cache?  
18. Persistent tasks?  
19. How add new package?  
20. How add new app?  
21. eslint-config share?  
22. Why ui not always prebuild dist?  
23. PM2 one process vs many?  
24. NODE_OPTIONS 3072?  
25. Day 42 vs 43?

---

## Senario-ha

**S1:** Import `@repo/ui/auth-guard` fail → check `exports` key spelling.  
**S2:** Two React copies → hooks break → dedupe / peer align.  
**S3:** Change only README → turbo still rebuild? inputs — maybe not; force if needed.  
**S4:** `turbo run start` without build → dependsOn build runs first.  
**S5:** Want build only packages — filter `@repo/*` pattern.

---

## Mini lab

1. Az root: `npm run build -- --filter=dejban` (syntax turbo filter)  
2. Bekhun `turbo.json` + explain each task  
3. Trace `@repo/api-client` → axiosInstance → app import  
4. List `packages/ui/package.json` exports — pick 5 used by dejban layout  
5. Read `.gitlab-ci.yml` concurrency comment  

---

## Resume (1 paragraph)

> Frontend is an **npm workspaces monorepo** orchestrated by **Turborepo 2**: multiple Next apps under `apps/*` share `@repo/ui`, `@repo/auth`, `@repo/api-client`, and `@repo/config`. Root scripts delegate to `turbo run`; CI builds with `--concurrency=1` to avoid OOM, then PM2 restarts the workspace.

Keywords: `Turborepo` · `npm workspaces` · `monorepo` · `@repo/*` · `^build` · `transpilePackages` · `turbo filter` · `PM2`

---

## File-haye mohem

| path | chera |
|---|---|
| `package.json` (root) | workspaces, scripts, turbo dep |
| `turbo.json` | task graph |
| `packages/*/package.json` | names `@repo/...` |
| `apps/*/package.json` | workspace deps `*` |
| `apps/*/next.config.mjs` | transpilePackages |
| `.gitlab-ci.yml` | turbo build CI |
| `package-lock.json` | single lockfile |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 00 | FE tree intro |
| 40 | auth packages used cross-app |
| 42 | Next per app + transpile |
| **43** | this — Turbo + workspaces |
| 44 | api-client + Query |
| 49 | guards in `@repo/ui` |
| 55 | e2e via turbo |
| 58 | CI + PM2 deepen |

---

## Chejori digest koni

1. Mall metaphor  
2. Workspaces = link; Turbo = run  
3. Bekhun turbo.json tasks  
4. Graph packages → apps  
5. CI concurrency story  
6. Resume seda  

---

## Glossary

| term | ma'ni |
|---|---|
| monorepo | chand project yek git |
| workspace | member package linked |
| hoist | deps bala root node_modules |
| Turborepo | task runner + cache |
| `^dependsOn` | upstream workspace tasks |
| filter | subset packages |
| persistent | long-running task (dev/start) |
| remote cache | share turbo cache across machines |
| transpilePackages | Next compiles workspace source |

---

## Deep dive — exports map vs barrel

`@repo/ui` **na** yek `main` bozorg — chand `exports` entry.  

**Fayde:** clear public surface; avoid importing internal paths.  
**Hazine:** har export jadid = package.json edit.

Interview: «We treat the UI package like an internal library with an explicit export map.»

---

## Deep dive — ConfigRegistry

`@repo/config` holds `AppConfig` shape; each app `ClientInit` `ConfigRegistry.set(CONFIG)`.  
Packages (ui/api) midunand serverUrl bedun import az `apps/dejban/global-config`.  

**Yani chi?** Invert dependency — packages read registry, app writes.

---

## Deep dive — peerDependencies on ui

React/MUI as **peers** → app provides single React instance.  
Agar ui bundle own React → duplicate = broken hooks.

---

## Anti-pattern

| bad | better |
|---|---|
| Copy AuthGuard into each app | `@repo/ui/auth-guard` |
| `npm install` only inside apps/dejban | always root |
| Circular app↔package | packages never import apps |
| Parallel turbo build on weak CI RAM | concurrency 1 |
| Publish `@repo/ui` public by mistake | private: true |
| Different axios major per app | one `@repo/api-client` |

---

## Interview 60s

«Our frontend monorepo uses npm workspaces for apps and shared packages under `@repo/*`, and Turborepo to run build, lint, and tests with a dependency graph. Next apps transpile those packages. CI runs turbo build single-threaded to avoid OOM, then PM2 starts the workspace.»

---

## Quick self-test

1. Workspaces globs? → `apps/*`, `packages/*`  
2. Turbo major? → 2.x  
3. `^build`? → upstream first  
4. Why concurrency 1? → OOM  
5. Shared axios where? → `@repo/api-client`  
6. UI import style? → `@repo/ui/...` exports  
7. packageManager? → npm 10.9.2  

---

## Final checklist

- [ ] workspaces vs turbo  
- [ ] turbo.json tasks  
- [ ] package graph  
- [ ] transpilePackages link  
- [ ] CI concurrency  
- [ ] filter mental model  
- [ ] resume  

---

## Extra — Farz kon add package `@repo/utils`

1. `packages/utils/package.json` name `@repo/utils`  
2. exports/main  
3. `npm i` root  
4. add dep to apps `"@repo/utils": "*"`  
5. if Next: transpilePackages ezafe  
6. turbo — if has build script, `^build` pulls it  

---

## Extra — Farz kon add app `apps/reports`

1. Next app scaffold  
2. workspace auto `apps/*`  
3. deps `@repo/*`  
4. scripts `dev`/`build` matching turbo task names **exact** (`build` not `build:app`)  
5. CI automatically includes unless filter  

**Chera name task match?** Turbo task name = script name in package.json.

---

## Extra — TUI

`"ui": "tui"` — interactive terminal dashboard when running turbo.  
CI often non-interactive — still works; logs plain.

---

## Extra — inputs `.env*`

Build cache invalidates when env files change — good (NEXT_PUBLIC embed).  
**Smell:** secret in `.env` committed? process issue — not turbo bug.

---

## Extra — passThroughEnv vs env

`env` = hashed into cache key (must match for hit).  
`passThroughEnv` = available to process, **not** always part of cache identity the same way — know docs; Dejban lists NEXT_PUBLIC in passThrough for build.

Interview-level: «We declare which env vars affect reproducibility.»

---

## Extra — Comparison Nx

Nx: richer project graph, generators, optional.  
Turbo: lighter, Vercel-aligned, enough for Dejban.  
Choice = team velocity + CI simplicity.

---

## Extra — Comparison multi-repo

| | multi-repo | Dejban monorepo |
|---|---|---|
| version sync | hard | easy `*` |
| CI | many pipelines | one turbo |
| clone size | small | larger |
| access control | per repo | CODEOWNERS paths |

---

## Extra — Soalat chera

**Chera npm na pnpm?** team lockfile + packageManager pin.  
**Chera Turbo na only workspaces?** cache + graph + UX multi-dev.  
**Chera concurrency 1?** RAM safety server.  
**Chera --no-daemon?** CI hygiene.  
**Chera private packages?** no npm publish.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «One repo, npm workspaces linking apps and `@repo` packages. Turborepo runs scripts in order with caching. Shared auth and axios live in packages; Next apps consume them via transpilePackages. CI builds with turbo concurrency one, then PM2 restarts.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Module not found `@repo/...` | forgot root install |
| Stale package | turbo cache / Next cache |
| OOM killed | concurrency too high |
| Wrong React version | peer not aligned |
| Script not run by turbo | name mismatch `build` |
| PM2 starts empty | build failed earlier |
| Lockfile conflict | install inside nested app |

---

## Extra — Layer checklist

| layer | tool |
|---|---|
| Link packages | npm workspaces |
| Run tasks | Turborepo |
| Compile shared src | Next transpilePackages |
| Lint share | `@repo/eslint-config` |
| Deploy | GitLab → turbo build → PM2 |

---

## Extra — Related learning days

- Day 42: Next app internals  
- Day 44: api-client usage  
- Day 55: turbo test:e2e  
- Day 58: PM2 + CI full  

---

## Extra — Daemon

Turbo daemon speeds local; CI `--no-daemon`.  
Windows optional `@turbo/windows-64` binary.

---

## Extra — check-types pipeline

Root `check-types` → turbo → packages with `tsc --noEmit` (ui has it).  
Apps JS-heavy may skip — honesty uneven type coverage (Day 42 ignoreBuildErrors).

---

## Extra — Format vs lint

`format` root = prettier **direct**, na turbo task.  
`lint` = turbo.  
Don'y confuse.

---

## Extra — xlsx at root

Root dependencies xlsx — shared binary import convenience; can create phantom coupling. Prefer package or app dep when cleaning.

---

## Band-e gharardad-e jadid

Mall = monorepo. Maghaze = app. Anbar moshtarak = packages. Manager = npm workspaces (link). Scheduler = Turborepo (ki key build). Security guard CI = concurrency 1. Delivery = PM2.

---

## 10 jomle fluency

1. Frontend is an npm workspaces monorepo.  
2. Turborepo orchestrates build/dev/test.  
3. Shared code lives under `@repo/*`.  
4. Apps depend with version `*`.  
5. `^build` runs upstream first.  
6. Next transpiles package source.  
7. Dev tasks are persistent and uncached.  
8. CI builds with concurrency 1.  
9. Filter runs a subset of packages.  
10. Packages must not import apps.

---

## Extra — Version alignment strategy

React 19 + MUI 7 across apps — bump carefully all package.json.  
Turbo doesn't enforce versions; **human/CI** does.  
Consider syncpack later — not required today.

---

## Extra — Local only one app

```bash
cd apps/dejban && npm run dev
```

Works if node_modules linked; root `turbo run dev --filter=dejban` cleaner for env consistency.

---

## Extra — Hotfix shared package

Edit `packages/ui/...` → Next Fast Refresh usually picks via transpile.  
Agar na: restart dev; check file outside exports accidentally.

---

## Extra — Security of monorepo

Yek clone = hame products. Access control via path CODEOWNERS / review.  
Secret in one app `.env` — don't commit; turbo inputs mention `.env*` for cache not for git.

---

## Extra — Migration smell «copy leftover»

Older apps may still have local duplicates of snackbar/hooks.  
Direction: move to `@repo/ui`, delete dup.  
Day 43 mindset: **prefer package**.

---

## Extra — Turbo vs Make/scripts

Could `npm-run-all`; lose cache + graph.  
Turbo standard for JS monorepos 2024–26.

---

## Extra — `persistent: true`

Tells Turbo: process stays alive (dev server).  
Without it, Turbo may treat as finite task and hang/kill oddly.

---

## Extra — outputs careful

`!.next/cache/**` exclude — don't poison cache artifact with webpack/turbo cache folder.  
If custom out dir — add to outputs or cache miss forever.

---

## Band-e gharardad — ye bar digar sade

1. **Workspace** = app ya package member.  
2. **`@repo/*`** = shared library.  
3. **`*`** = local link.  
4. **Turbo** = run + tartib + cache.  
5. **`^build`** = aval dependency.  
6. **transpilePackages** = Next source package.  
7. **filter** = faqat ye app.  
8. **CI concurrency 1** = anti-OOM.  
9. **PM2** = start workspace.  
10. **No cycle** app↔package.

---

## Extra — Capacity & scale

5 Next apps build sequential ≈ time sum.  
Remote cache (Vercel Remote Cache / custom) future win.  
RAM: each Next build hungry — why serialize.

---

## Extra — Onboarding checklist new hire

1. Node 20+  
2. Clone FE repo  
3. `npm ci` root  
4. `npx turbo run dev --filter=dejban`  
5. Read `packages/ui` exports + `api-client`  
6. Don't commit from nested wrong lockfile  

---

## Extra — Interview trap «Is Turbo a bundler?»

**Na.** Bundler = Turbopack/webpack/vite inside each Next app (Day 42).  
**Turborepo** = monorepo task orchestration.  
Esme shabih — mosahebe classic mix-up.

---

## Extra — Naming `pg_frontend`

Root package name historical PayamGostar; folder `dejban_frontend_new`.  
Resume: «Dejban frontend monorepo» — clarify product.

---

## Extra — Testing strategy monorepo

- unit: packages + apps that define `test:unit`  
- e2e: per-app Playwright via `turbo run test:e2e`  
- cache false — always run when asked  
- filter in CI job matrix possible later  

---

## Extra — Breaking change in `@repo/ui`

1. Change export  
2. Fix all apps compile  
3. Single PR preferred (atomic monorepo benefit)  
4. Avoid publish versioning pain — private  

---

## Khoruj-e zehni

> Midunam FE Dejban monorepo-ye npm workspaces + Turborepo-st; apps to `apps/*`, shared `@repo/*`; turbo task graph ba `^build`; Next transpilePackages; CI `turbo build --concurrency=1`; va Turborepo ba Turbopack ethtebaah nemigiram.

Age in paragraph mal-e to shod — Day 43 done.

---

*Day 43 tamum. Ba'd: Day 44 — TanStack Query + Axios (amade). Fehrest: [README.md](./README.md).*
