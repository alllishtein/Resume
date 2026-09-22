# Day 55 — Playwright + Vitest

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** FE Dejban chejori test mishe — unit? e2e? koja?

**Javab monorepo (honesty):**

| layer | tool | koja |
|---|---|---|
| **E2E / smoke / regression** | **Playwright** (`@playwright/test`) | `apps/dejban/tests/**`, `apps/main/tests/**` |
| **Unit** | **Vitest** (`vitest run`) | root dep + `apps/main` script `test:unit` — **suite hanuz thin/empty** |
| Orchestration | Turbo | `test:e2e` / `test:unit` **cache: false** |

Zincir-ezehni e2e:

```
npm run test:e2e[:local]
  → turbo run test:e2e
  → apps/dejban|main: playwright test
  → projects: smoke | regression | e2e (chromium)
  → fixtures: loginViaApi → localStorage jwt → Page Objects
  → assert UI (MUI roles/text)
```

Olgu auth fixture (dejban):

```ts
// tests/utils/fixture.ts — override page
const { accessToken } = await loginViaApi(request);
await context.addInitScript((token) => {
  localStorage.setItem('jwt_access_token', token);
}, accessToken);
await page.goto(config.baseURL);
```

Config dual-target:

| mode | script | baseURL |
|---|---|---|
| remote (default) | `test:e2e` | production host locked |
| local | `test:e2e:local` + `PLAYWRIGHT_TARGET=local` | `PLAYWRIGHT_BASE_URL` ya localhost |

**Band-e gharardad-e jadid:** farz kon / yani chi / chera + **honesty Vitest**: tooling hast, unit files kam.

Day 43 = turbo test tasks. Day 54 = Vite≠Vitest. **In ruz = Playwright deep + Vitest place.**

---

# BAKHSH-E AVAL: WORLD — Playwright vs Vitest

## Farz kon — baresi karkhane

**Vitest (unit):** yek ghete charkh — function/component izole, sari, bedune browser full.  
**Playwright (e2e):** tamame khat → browser vaghe'i, click, network, localStorage.

| | Vitest | Playwright |
|---|---|---|
| Speed | ms–s | s–min |
| Scope | unit / component | user journey |
| Runtime | Node / jsdom | Chromium/Firefox/WebKit |
| Flake risk | kamtar | bishtar (timing/UI) |
| Dejban emruz | wired, thin | **asli** |

---

## Playwright chie?

Microsoft browser automation + test runner.

```ts
import { test, expect } from '@playwright/test';
test('login', async ({ page }) => {
  await page.goto('/auth/jwt/sign-in');
  await page.getByLabel('...').fill('...');
  await expect(page).toHaveURL(/home/);
});
```

| mafhum | ma'ni |
|---|---|
| `page` | tab |
| `locator` | auto-waiting selector |
| `expect` | web-first assertions |
| `fixture` | inject deps (auth, PO) |
| `project` | suite grouping |
| `trace` / screenshot | debug fail |
| storageState | save cookies/localStorage |

---

## Vitest chie?

Vite-native test runner (Jest-like API). Fast transform via Vite.  
Ba `@testing-library/react` + `jsdom` → component tests.

```ts
import { describe, it, expect } from 'vitest';
describe('sum', () => {
  it('adds', () => expect(1+1).toBe(2));
});
```

Dejban root: `vitest`, `@testing-library/react`, `jsdom` — **ready**.  
`apps/main`: `"test:unit": "vitest run"` — config/file suite still light.

**Chera in ruz har do?** Resume: «E2E Playwright mature; unit Vitest scaffolded.»

---

## Page Object Model (POM)

WORLD pattern: encapsulate selectors + actions in classes.

```ts
class LoginPage {
  constructor(private page: Page) {}
  async login(user, pass) { ... }
}
```

Specs thin; pages fat. Dejban: `tests/pages/**` + `BasePage`.

---

# BAKHSH-E DOVOM: DEJBAN — Playwright

## Qesmat 1 — koja zende-st

| app | scripts | config |
|---|---|---|
| `apps/dejban` | `test:e2e`, `test:e2e:local` | `playwright.config.ts` |
| `apps/main` | same + `test:unit` | `playwright.config.ts` |
| root | turbo wrappers | `@playwright/test`, `vitest` |

AC / gate / dcc: e2e dedicated kam — focus dejban+main.

---

## Qesmat 2 — `playwright.config.ts` (dejban)

```ts
export default defineConfig({
  testDir: './tests',
  outputDir: './test-results',
  testIgnore: ['**/unitTest/**'],
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  use: {
    baseURL: config.baseURL,
    ignoreHTTPSErrors: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'smoke', testMatch: /.*smoke\/.*\.spec\.ts/ },
    { name: 'regression', testMatch: /.*regression\/.*\.spec\.ts/ },
    { name: 'e2e', testMatch: /.*e2e\/.*\.spec\.ts/ },
  ],
});
```

**Chera workers 1 / not parallel?** Shared backend data + less flake on mutating e2e (create personnel).  
**Chera CI retries 2?** Transient network/UI.  
**Chera trace on failure?** `npx playwright show-trace` ba'd az fail.

main: `fullyParallel: true` default; smoke-auth/regression force `fullyParallel: false`.

---

## Qesmat 3 — projects pyramid

```
smoke     → zud, critical path (dashboard cards, login)
regression→ mid
e2e       → flows deep (personnel CRUD, centers, vehicle, …)
```

Run one project:

```bash
npx playwright test --project=smoke
```

Folder layout mirrors projects (`tests/smoke`, `tests/e2e/...`).

---

## Qesmat 4 — config dual target

`tests/config/config.ts`:

```ts
const isLocal = env('PLAYWRIGHT_TARGET') === 'local';
const baseURL = isLocal
  ? trimSlash(env('PLAYWRIGHT_BASE_URL') || 'http://localhost:3035')
  : PRODUCTION_BASE_URL;
const apiURL = isLocal
  ? ... PLAYWRIGHT_API_URL || NEXT_PUBLIC_SERVER_URL ...
  : `${PRODUCTION_BASE_URL}/api/v1`;
```

Env via `vite`'s `loadEnv('test', ...)` + `process.env`.  
Credentials: `PLAYWRIGHT_USERNAME` / `PLAYWRIGHT_PASSWORD` (fallback defaults in code — **override in real use**).

**Yani chi:** yek suite, do target — CI/remote vs laptop.

**Chera production locked for default e2e?** Comment in code: remote script → production host. Local opt-in.

---

## Qesmat 5 — API login + initScript (core trick)

```ts
// auth.ts
await request.post(`${config.apiURL}/Auth/Login`, {
  data: { username, password },
});
return { accessToken: data.accessToken };

// fixture
await context.addInitScript((token) => {
  localStorage.setItem('jwt_access_token', token);
}, accessToken);
```

**Chera na UI login har test?** Sari + kam flake.  
UI login still tested in **main smoke-public** Login.spec.

**Yani chi:** same key app mikhune (Day 40/49 jwt_access_token).

dejban fixture **overrides default `page`** → almost all specs auto-auth.  
main: public tests use raw `page`; authed use `pageWithAuth`.

---

## Qesmat 6 — fixtures as DI

```ts
export const test = base.extend<MyFixtures>({
  personnel: async ({ page }, use) => {
    await use(new Personnel(page));
  },
  // dashboard, center, vehicle, ...
});
```

Spec:

```ts
import { test, expect } from 'tests/utils/fixture';
test('...', async ({ personnel, dashboard }) => { ... });
```

**Chera?** Type-safe POM inject; no `new X(page)` har test.

---

## Qesmat 7 — BasePage + domain pages

`helpers/BasePage`: fillInput, selectOption, checkTreeItem, openTab, isExists.  
Domain: `Personnel`, `Center`, `Door`, `Vehicle`, `Dashboard`, …

Selectors: `getByRole`, `getByText`, MUI class hooks — mix.  
Smell: some CSS class hashes fragile — prefer role/text.

---

## Qesmat 8 — sample flows

**Smoke dashboard (dejban):** cards/charts/tables visible + sidebar toggle.  
**E2E personnel:** open → create with timestamp unique codes → search verify → pagination → assign role.  
**Main login smoke:** valid/invalid/empty validation + refresh stays logged in.

Timestamp in names → parallel-ish unique data (with workers 1 still good hygiene).

---

## Qesmat 9 — saveAuth.spec (main)

`testIgnore: saveAuth.spec.ts` in config — helper to dump `auth.json` storageState.  
Manual/debug — not default suite. Pattern for storageState workflows.

---

## Qesmat 10 — Turbo + root scripts

```json
"test:e2e": "turbo run test:e2e",
"test:e2e:local": "cross-env PLAYWRIGHT_TARGET=local turbo run test:e2e",
"test:unit": "turbo run test:unit"
```

turbo.json: cache false; passThroughEnv `CI`, `PLAYWRIGHT_*`, `NEXT_PUBLIC_*`.

**Chera no cache?** Flaky + env-dependent → false green risk (Day 43).

---

## Qesmat 11 — reporters / artifacts

- list + steps console  
- html → `playwright-report/`  
- `test-results/` output  
- fail → screenshot + retained trace  

CI: upload report artifact (ops Day 58).

---

## Qesmat 12 — URLS helper

```ts
export const URLS = {
  base: '/',
  login: '/auth/jwt/sign-in?returnTo=%2Fhome',
  home: '/home',
  dejban: '/dejban/dashboard',
  vehicle: '/dejban/dashboard/car/vehicle',
};
```

Paths relative to `baseURL` (main portal + /dejban rewrite — Day 42/54 family).

---

# BAKHSH-E SEVOM: DEJBAN — Vitest (honesty)

## Place emruz

| item | status |
|---|---|
| root `vitest` ^4 | yes |
| `@testing-library/react` + `jsdom` | yes |
| `apps/main` `test:unit` | script exists |
| `vitest.config.*` dedicated | not prominent |
| Real unit `*.test.ts` suite | **thin / absent** |
| `testIgnore unitTest/**` in Playwright | reserved folder name |

**Resume caution:** claim «Playwright e2e for main/dejban»; «Vitest available for unit, expanding» — not «full unit coverage».

**Chera Vitest next to Vite?** Shared transform story; Day 54 Vite app unrelated to why Vitest chosen — ecosystem fit.

---

## WORLD mini — good first Vitest targets

1. pure utils (`packages/*` formatters)  
2. Zod schemas parse  
3. query key factories  
4. small presentational components  

Not: full MRT tables in jsdom (pain) — leave to Playwright.

---

# BAKHSH-E CHAHAROM: jadval mosahebe

| question | answer |
|---|---|
| Primary FE test? | Playwright e2e |
| Auth in e2e? | API login + localStorage initScript |
| Parallel dejban? | workers 1 |
| Local vs prod? | PLAYWRIGHT_TARGET=local |
| POM? | tests/pages + fixtures |
| Unit? | Vitest scaffold |
| Turbo cache tests? | false |
| Trace? | retain-on-failure |

---

# BAKHSH-E PANJOM: farz kon / senario

## Se dastan

**1) CI nightly smoke**  
`turbo test:e2e -- --project=smoke` against remote → green = login+dashboard alive.

**2) Dev feature personnel**  
`test:e2e:local` ba backend local + `PLAYWRIGHT_BASE_URL` → run personnel.spec create.

**3) Flaky fail**  
Open html report + trace → see timeout on MUI option — fix selector / wait.

---

## Smell-ha

1. Default password in config source — secrets better env-only  
2. Production e2e mutates real data risk — use dedicated QA tenant  
3. workers 1 = slow suite  
4. Fragile CSS class selectors in BasePage tree  
5. Vitest script without suite = false sense coverage  
6. Timestamp Persian names — encoding/search edge  
7. pageerror throw in smoke — strict, good but catch third-party noise  

---

## Debug checklist

| symptom | check |
|---|---|
| Login failed API | apiURL / creds / CORS |
| Stuck sign-in | token key name / initScript timing |
| Timeout locator | role/text change / loading |
| 404 base | PLAYWRIGHT_BASE_URL port |
| CI only flake | retries/trace; race |
| Wrong env | PLAYWRIGHT_TARGET |
| Empty unit | vitest no tests found — expected today |

---

## 25 soal-e mosahebe

1. Playwright vs Vitest?  
2. Kodom apps e2e?  
3. chejori auth bedune UI?  
4. jwt key name?  
5. workers dejban?  
6. projects names?  
7. local flag?  
8. POM koja?  
9. BasePage chie?  
10. turbo cache e2e?  
11. retries CI?  
12. trace policy?  
13. saveAuth?  
14. Vitest status honesty?  
15. fixture.extend?  
16. ignoreHTTPSErrors?  
17. testIgnore unitTest?  
18. loadEnv from vite?  
19. personnel unique data?  
20. main vs dejban fixture diff?  
21. HTML report folder?  
22. passThroughEnv?  
23. smoke vs e2e?  
24. Day 40 link?  
25. One-liner Day 55?

---

## Senario-ha

**S1:** Add door e2e — page object + fixture key + spec under e2e/Center.  
**S2:** Run only smoke locally — `--project=smoke`.  
**S3:** Debug fail — `npx playwright show-report`.  
**S4:** First Vitest util test — add under packages + wire config.  
**S5:** Parallelize later — isolate data per worker + remove shared mutations.

---

## Mini lab

1. Read dejban `playwright.config.ts` projects  
2. Read `fixture.ts` + `auth.ts`  
3. Run mental path personnel.spec beforeEach  
4. Compare main Login.spec (UI auth) vs API auth  
5. `rg vitest` — confirm thin unit  
6. Check turbo.json test:e2e cache false  

---

## Resume (1 paragraph)

> Frontend quality gates center on **Playwright**: `apps/dejban` and `apps/main` use project-split smoke/regression/e2e suites, **Page Objects**, and **API login + localStorage** fixtures, with **Turbo** `test:e2e` (no cache) and dual **local/production** targets via `PLAYWRIGHT_TARGET`. **Vitest** is installed for unit/component tests (`test:unit`) but the unit suite is still early compared to e2e.

Keywords: `Playwright` · `fixture` · `Page Object` · `loginViaApi` · `addInitScript` · `projects` · `Vitest` · `turbo test:e2e`

---

## File-haye mohem

| path | chera |
|---|---|
| `apps/dejban/playwright.config.ts` | projects/workers |
| `apps/main/playwright.config.ts` | smoke-public/auth split |
| `apps/*/tests/utils/fixture.ts` | DI + auth |
| `apps/*/tests/utils/auth.ts` | API login |
| `apps/*/tests/config/config.ts` | local/prod URLs |
| `apps/*/tests/pages/**` | POM |
| `apps/*/tests/e2e|smoke/**` | specs |
| root `package.json` / `turbo.json` | orchestration |
| Day 43 | turbo tasks |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 40 | Auth JWT — same token key |
| 43 | turbo test:e2e/unit |
| 49 | Auth UI — Login.spec covers |
| 52 | MRT — e2e tables exercise |
| 54 | Vitest ≠ Vite SPA |
| **55** | this |
| 56 | backend xUnit |
| 58 | CI runs these |

---

## Chejori digest koni

1. E2E = Playwright primary  
2. API auth fixture  
3. POM + fixtures  
4. smoke/e2e projects  
5. Vitest honesty  

---

## Glossary

| term | ma'ni |
|---|---|
| e2e | end-to-end |
| smoke | critical shallow tests |
| POM | page object model |
| fixture | Playwright DI |
| initScript | pre-page JS inject |
| trace | timeline debug fail |
| storageState | persisted auth file |
| web-first assert | auto-wait expect |
| jsdom | fake DOM for unit |
| flake | intermittently fail |

---

## Deep dive — why override `page` in dejban

Every test gets authed context automatically — less boilerplate.  
Cost: hard to test logged-out in same fixture without second fixture (main separates better).

---

## Deep dive — web-first assertions

`expect(locator).toBeVisible()` waits until timeout — less `waitForTimeout`.  
Prefer over manual sleeps.

---

## Deep dive — mutating prod

Create personnel on production e2e = data pollution.  
Mitigate: QA env, cleanup steps, unique prefix `qa-`, dedicated site.

---

## Anti-pattern

| bad | better |
|---|---|
| UI login every test | API + initScript |
| CSS hash selectors | role/label |
| sleep(5000) | expect auto-wait |
| Claim 100% unit | honesty Vitest early |
| Cache e2e in CI | cache false |
| One giant spec | projects + describe |

---

## Interview 60s

«We run Playwright against main and dejban with smoke and e2e projects. Tests use Page Objects and a fixture that logs in through the Auth API then injects the JWT into localStorage. Suites can target local or production via PLAYWRIGHT_TARGET. Vitest is set up for unit tests but e2e is where most coverage lives today.»

---

## Quick self-test

1. Primary tool? → Playwright  
2. Auth trick? → API + localStorage  
3. dejban workers? → 1  
4. Local env var? → PLAYWRIGHT_TARGET=local  
5. POM folder? → tests/pages  
6. Vitest mature? → no / early  
7. Turbo cache? → false  

---

## Final checklist

- [ ] Playwright vs Vitest  
- [ ] config projects  
- [ ] dual target  
- [ ] fixture auth  
- [ ] POM  
- [ ] turbo  
- [ ] Vitest honesty  
- [ ] resume  

---

## Extra — Farz kon supermarket QA

Smoke = check darvaze + cheragh asosli.  
E2E = kharid complete yek moshtari test.  
Unit = vazn kardan yek gheiych.  
Dejban emruz: bishtar smoke+e2e; vazn kardan (Vitest) hanuz kam.

---

## Extra — Chromium only

Projects set `browserName: 'chromium'`.  
Cross-browser possible — not current matrix. Cost/time tradeoff.

---

## Extra — forbidOnly

`test.only` left in CI → fail build. Good hygiene.

---

## Extra — page.on('pageerror')

Dashboard smoke throws if console page error — catches React crash early.

---

## Extra — cross-env

Windows-friendly `PLAYWRIGHT_TARGET=local` via `cross-env` in npm scripts.

---

## Extra — HTML report open never

CI-friendly; open manually: `playwright show-report`.

---

## Extra — compare Cypress

Interview: Playwright multi-browser, trace, MS ecosystem; team chose Playwright — don't need Cypress debate deep.

---

## Extra — component testing Playwright

Playwright CT exists — Dejban uses classic e2e + future Vitest RTL. Honesty.

---

## Extra — data files

`tests/data/loginData.ts` — valid/invalid users for main login smoke.

---

## Extra — URL returnTo

Login path encodes `returnTo=%2Fhome` — AuthGuard redirect contract (Day 49).

---

## Band-e gharardad-e jadid

Playwright = robot browser.  
Fixture = karto-ye vorud API.  
localStorage = angaosht-zani token.  
POM = dastor-kar safhe.  
Project smoke/e2e = tabaghe-bandi.  
Vitest = microscopic — hanuz kuchek.  
Turbo = conductor bedune cache false green.

---

## 10 jomle fluency

1. E2E runs on Playwright for dejban and main.  
2. Auth uses API login plus initScript.  
3. Token key is jwt_access_token.  
4. Page Objects live under tests/pages.  
5. Fixtures inject those pages.  
6. dejban uses one worker to reduce flake.  
7. PLAYWRIGHT_TARGET=local switches base URL.  
8. Turbo test:e2e disables cache.  
9. Vitest is present but early.  
10. Traces retain on failure.

---

## Extra — version pins

| pkg | range |
|---|---|
| `@playwright/test` | ^1.61 (lock ~1.62) |
| `vitest` | ^4.1 |
| `@testing-library/react` | ^16 |
| `jsdom` | ^30 |

---

## Extra — install browsers

First machine: `npx playwright install` (chromium).  
CI image must install deps.

---

## Extra — selector priority (team tip)

1. getByRole  
2. getByLabel / getByText  
3. testid if added  
4. CSS last  

---

## Extra — flaky triage order

1. Is env wrong (prod vs local)?  
2. Auth token fail?  
3. Locator renamed?  
4. Timing — increase expect timeout targeted  
5. Backend 500 — not FE  

---

## Extra — main smoke-auth vs public

public: login page tests (no token).  
auth: settings/logout need `pageWithAuth`.  
regression setting.spec parallel off.

---

## Extra — e2e domains covered (dejban)

Personnel, Centers (Center/Unit/Door), Contractors, Info (Employment/Status/Major), Vehicle, Dashboard smoke.

---

## Extra — not covered yet (honesty)

AC Vite SPA e2e thin; visual regression; a11y axe; full Vitest packages.

---

## Extra — link Day 56

Backend tests = xUnit — mirror «unit vs e2e» story other side.

---

## Extra — security note for learning

Don't commit real prod passwords; rotate if leaked; prefer CI secrets. Code fallbacks are convenience for internal QA — treat carefully.

---

## Extra — show-trace workflow

1. Fail with trace zip in test-results  
2. `npx playwright show-trace path`  
3. Inspect network + DOM snapshot  

---

## Extra — codegen

`npx playwright codegen URL` — scaffold selectors; still refactor into POM.

---

## Extra — expect.poll / toPass

For eventual UI (SignalR Day 50) — useful later.

---

## Extra — 10 soalat sari

1. E2E tool? Playwright  
2. Unit tool? Vitest  
3. API login? yes  
4. workers dejban? 1  
5. local var? PLAYWRIGHT_TARGET  
6. POM? yes  
7. cache turbo? false  
8. projects? smoke/regression/e2e  
9. main Login UI tested? yes  
10. Vitest full? no  

---

## Extra — Diagram 30s

Begu: «Turbo starts Playwright per app. Config picks local or prod URL. Fixture logs in via API and sets JWT. Specs call Page Objects and assert with web-first expect. Vitest waits for real unit files.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| 401 after goto | initScript / wrong key |
| Login API 404 | apiURL path `/Auth/Login` |
| Empty table assert | filter leftover / site |
| Strict mode violation | locator matched 2 |
| Timeout CI only | slower env — retries |

---

## Extra — Layer checklist

| layer | tech |
|---|---|
| Runner e2e | Playwright |
| Auth bootstrap | request.post + initScript |
| Abstraction | POM + fixtures |
| Grouping | projects |
| Unit runner | Vitest |
| Orchestrator | Turbo |
| Artifacts | report + trace |

---

## Extra — Farz kon add Vitest properly

1. `vitest.config.ts` in package  
2. environment jsdom  
3. include `src/**/*.test.ts`  
4. script already `vitest run`  
5. turbo picks up test:unit  

---

## Extra — parallel future

When DB fixtures isolated: raise workers; use `test.describe.configure({ mode: 'serial' })` only for dependent flows.

---

## Extra — RTL vs Playwright

RTL: render(<Btn/>) click — unit.  
Playwright: real Next app — e2e.  
Both complementary.

---

## Extra — Final fluency drill

«Playwright covers dejban and main with smoke and e2e projects. We authenticate through the login API and inject the JWT. Page Objects keep specs readable. Vitest is ready for unit tests but most coverage is still end-to-end.»

---

## Khoruj-e zehni

> Midunam FE test asosan Playwright-e (dejban+main, smoke/e2e, POM, API login+localStorage); local/prod ba PLAYWRIGHT_TARGET; turbo cache false; va Vitest tooling hast ama suite unit hanuz thin.

Age in paragraph mal-e to shod — Day 55 done.

---

*Day 55 tamum. Ba'd: Day 56 — xUnit + NetArchTest (amade). Fehrest: [README.md](./README.md).*