# Day 49 — Auth UI / Guards / `componentId`

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** ba'd az login, UI chejori midune kodom menu/dokme/page neshan dahad? Va URL mostaghim ra block konad?

**Javab Dejban (FE):**

| layer | component | kar |
|---|---|---|
| Session | `AuthProvider` (`@repo/auth`) | `getMe` → `user`, `siteClaims`, **`claims[]`** |
| Logged-in shell | **`AuthGuard`** | na auth → redirect sign-in |
| Guest pages | **`GuestGuard`** | auth → redirect `returnTo` / home |
| Claim context | **`ComponentGuard`** | Set az claim values |
| Hide widget | **`Guard componentId=…`** | null if no claim |
| Page gate | **`PageGuard`** | 403 redirect |
| URL↔nav | **`RouteAccessGuard`** | longest nav path → componentId |
| Catalog | **`componentPaths`** | derakht ID-haye FE |
| Nav filter | **`filterNavByComponentGuard`** | hide menu items |
| License (jodagane) | **`LicenseProvider`** | module licensed? |

Zincir dashboard (Day 42):

```
AuthGuard
  → DashboardLayout
       filterNavByComponentGuard(nav, claims)
       ComponentGuard
         RouteAccessGuard(navData)
           Page (often PageGuard + componentPaths.… )
             sections with <Guard componentId={…Button}>
```

**Band-e gharardad-e jadid + honesty:** FE Guard = **UX hide**. Source of truth API = JWT claims / Permission policies (Day 37/40). Hide dokme ≠ secure endpoint.

Day 40 = auth e2e tokens. Day 37 = BE claims. **In ruz = FE permission UI.**

---

# BAKHSH-E AVAL: WORLD

## Farz kon — badge + fehrest dastresi

**AuthGuard:** «badge dari?» (logged in).  
**componentId:** shomare-ye har dokme/page to fehrest.  
**claims[] az getMe:** fehrest shomare-ha-i ke in user (to site) dare.  
**Guard:** agar shomare to list nist → dokme ra neshun nade.  
**PageGuard:** agar URL bezani bedun shomare → 403.

---

## Chera na faqat role string?

Role-BasedGuard template hast (Admin/User).  
Dejban asosli: **fine-grained component claims** — `staffCreateButton`, `staffView`, …  
Yek role mitune sad-ha componentId dashte bashe (assign to role to BE).

---

## FE vs BE (mosahebe zarrin)

| | FE Guard | BE Permission |
|---|---|---|
| hadaf | UX / kam click bihode | security |
| bypass | DevTools / API direct | hard |
| data | claims flat getMe | JWT transform + policies |

Resume: «UI gated by componentId claims mirroring backend permission values.»

---

# BAKHSH-E DOVOM: Auth UI session

## Qesmat 1 — `AuthProvider` (`packages/auth`)

```ts
checkUserSession:
  if (!tokenStorage.getAccess()) → clear, loading false
  else GET /auth/getme
    setUser, setSiteClaims, setClaims(string[])

authenticated: !!user
login(accessToken, user) → setAccess + checkUserSession
logout → POST logout + clear + location sign-in
storage event: other tab cleared token → logout state
```

**claims:** flat string array — values match `componentPaths.*.value` (case-insensitive compare).  
**siteClaims:** sites user can pick (Day 46 store).  
**sessionRefreshing:** PageGuard waits (avoid flash deny).

---

## Qesmat 2 — `AuthGuard`

```jsx
if (!loading && !authenticated)
  window.location.href = signInUrl?returnTo=…
if (isChecking) SplashScreen
else children
```

Hard navigation (full) — cookie/LS consistent.  
Dashboard layout wraps children ba AuthGuard.

---

## Qesmat 3 — `GuestGuard`

Sign-in pages: if already authenticated → `safeReturnUrl(returnTo, '/')`.  
Comment in code: avoid loop when redirectPath was sign-in itself.

**Yani chi:** Guest = faqat unauthenticated.

---

## Qesmat 4 — Auth UI surfaces

- Sign-in form (apps/main) → login → token + getMe  
- Account menu logout  
- 403 page `/error/403`  
- Splash/Loading while session check  

Deep form auth = Day 40; inja focus Guards + componentId.

---

# BAKHSH-E SEVOM: `componentId` system

## Qesmat 5 — `componentPaths.js`

Huge tree under `@repo/ui/auth-guard`:

```js
componentPaths.dashboard.humanResourceManagement.staff.value
// e.g. management id
componentPaths.…staff.staffCreateButton.value  // "staffCreateButton"
componentPaths.…staff.staffView.value
```

Comment file: only IDs referenced in Guard / permissions + grid View/Create/Update conventions.

**Access Permission UI** builds tree from `componentPaths` for admins to assign claims to roles (assign claim values = these strings).

**Chera central catalog?** typo-proof; single source FE↔admin matrix.

---

## Qesmat 6 — matching logic

```js
hasComponentAccess(claims, componentId):
  if (!componentId) return true
  return Set(claims lowercase).has(componentId.toLowerCase())
```

Empty componentId = public within auth shell.  
Case-insensitive — BE/FE casing drift safe-ish.

---

## Qesmat 7 — `ComponentGuard` + `Guard`

```jsx
<ComponentGuard>  {/* builds Set once */}
  <Guard componentId={componentPaths.…staffCreateButton.value}>
    <Button>ایجاد</Button>
  </Guard>
</ComponentGuard>
```

`Guard` without access → `null` (no forbidden flash).  
Must be under ComponentGuard for context (dashboard provides it).

Alias prop `value` = same as componentId.

---

## Qesmat 8 — `PageGuard`

```jsx
// staff/page.jsx
<PageGuard componentId={componentPaths.dashboard.humanResourceManagement.staff.value}>
  <StaffListView />
</PageGuard>
```

Waits: `!loading && !sessionRefreshing && siteReady`  
`siteReady`: selectedSiteIds.length > 0 OR user has no sites.  
Deny → `router.replace('/error/403')`.

**Chera siteReady?** claims often site-scoped (Day 16/37/46) — don't judge before site chosen.

---

## Qesmat 9 — `RouteAccessGuard`

Derives required id from **nav config path** vs pathname (longest prefix match).  
Deep URL under `/personnel/staff/...` inherits staff nav componentId if configured.  
If nav item has no componentId → allow (only AuthGuard).

Works with `filterNavByComponentGuard` — hide + block URL.

---

## Qesmat 10 — Nav filter

Dashboard layout:

```js
filteredNavData = filterNavByComponentGuard(navData, claims)
```

Items without claim removed; empty parent groups pruned when only `#` placeholders.

**Yani chi:** user never sees links they can't open (still PageGuard if URL typed).

---

## Qesmat 11 — MRT / action permissions

Staff list passes:

```js
editPermission={componentPaths.…staffEditButton.value}
```

Table actions internally Guard / hasComponentAccess.  
create/delete buttons wrapped `<Guard componentId={…CreateButton}>`.

Pattern: **page view claim** + **action button claims** finer.

---

## Qesmat 12 — License vs claims

`LicenseProvider` / `useLicense`: product module licensed (feature flag commercial).  
Empty licensedModules → all allowed.  
Access-permission tree may `filterTreeByModule`.  

**Joda az** user permission claims — both can apply.

---

## Qesmat 13 — `RoleBasedGuard`

Template leftover — role string allowlist + Forbidden illustration.  
Dejban production path = componentId. Know it exists; don't primary.

---

# BAKHSH-E CHAHAROM: end-to-end story

## Farz kon assign Create Staff

1. Admin Access Permission UI checks `staffCreateButton` on role  
2. BE stores claim value on role / user (Day 37)  
3. User login → getMe returns `claims` including `staffCreateButton`  
4. Nav shows Staff if parent claim present  
5. PageGuard allows staff page  
6. `<Guard staffCreateButton>` shows دکمه ایجاد  
7. API create still checks permission claim server-side  

Agar step 6 skip (hack DOM) → step 7 403 toast (Axios).

---

## Zincir ba Day 40/46

Login → LS access → getMe claims → AuthContext → Guards.  
Site picker Zustand → may refresh effective claims (site-scoped getMe / header).  
X-Site-Id on API — BE filters tenant + permission.

---

# BAKHSH-E PANJOM: smell / debug

## Smell-ha

1. FE-only trust illusion  
2. componentPaths mega-file merge conflicts  
3. Nav componentId missing → RouteAccessGuard open hole  
4. PageGuard vs RouteAccessGuard double — understand both  
5. RoleBasedGuard confusion with component model  
6. AuthGuard `window.location` vs router — full reload  
7. claims not updated until checkUserSession after role change — re-login/refresh  
8. Package guards import `src/routes` / loading — app-coupled  

---

## Debug checklist

| symptom | check |
|---|---|
| Bounce login loop | GuestGuard returnTo / AuthGuard |
| Menu empty | claims empty / wrong site / filter |
| Button missing | Guard componentId vs claim string |
| 403 on page | PageGuard id / getMe claims |
| Deep link 403 | RouteAccessGuard path match |
| Flash content | ready flags sessionRefreshing |
| Works UI fails API | BE permission missing — expected |

---

## 25 soal-e mosahebe

1. AuthGuard vs PageGuard?  
2. componentId chie?  
3. claims az koja?  
4. Guard return null vs 403?  
5. filterNavByComponentGuard?  
6. RouteAccessGuard longest path?  
7. siteReady chera?  
8. FE vs BE security?  
9. componentPaths catalog?  
10. GuestGuard loop fix?  
11. License vs claim?  
12. RoleBasedGuard status?  
13. Case sensitivity?  
14. empty componentId?  
15. sessionRefreshing?  
16. How add new button permission?  
17. getMe after role assign?  
18. Multi-tab logout storage?  
19. editPermission on MRT?  
20. Access permission admin UI?  
21. Authenticated definition?  
22. signInUrl vs redirectPath?  
23. Day 37 link?  
24. Day 40 link?  
25. Day 49 one-liner?

---

## Senario-ha

**S1:** New `staffExportButton` — add componentPaths + Guard + BE claim + assign role.  
**S2:** User bookmarks URL without nav claim — RouteAccessGuard/PageGuard 403.  
**S3:** Site switch — claims may change; ensure getMe/site header consistency.  
**S4:** Superadmin all claims — UI full; still BE audit.  
**S5:** Forgot PageGuard — only RouteAccessGuard if nav mapped.

---

## Mini lab

1. Remove claim from role → button disappears; API 403  
2. Trace staff page PageGuard id in componentPaths  
3. filterNav — log filtered tree  
4. Open /error/403 manually  
5. GuestGuard with returnTo query  

---

## Resume (1 paragraph)

> Implemented fine-grained **Auth UI guards** on Next dashboards: session via **AuthProvider/getMe**, shell **AuthGuard/GuestGuard**, and **componentId** checks (`componentPaths`, `Guard`, `PageGuard`, `RouteAccessGuard`, nav filtering) aligned with backend permission claim values—UI hiding for UX with server enforcement as the real control.

Keywords: `AuthGuard` · `componentId` · `PageGuard` · `claims` · `getMe` · `filterNav` · `RBAC` · `403` · `componentPaths`

---

## File-haye mohem

| path | chera |
|---|---|
| `packages/auth/src/AuthContext.tsx` | session + claims |
| `packages/ui/.../auth-guard.jsx` | login wall |
| `packages/ui/.../guest-guard.jsx` | guest wall |
| `packages/ui/.../component-guard.jsx` | Guard/Page/Route |
| `packages/ui/.../component-guard-utils.js` | hasAccess / filter / path |
| `packages/ui/.../component-paths.js` | ID catalog |
| `apps/dejban/.../dashboard/layout.jsx` | wire guards + filterNav |
| `apps/dejban/.../nav-config-dashboard.jsx` | nav componentIds |
| `apps/dejban/.../staff/page.jsx` | PageGuard example |
| `sections/access-permission/*` | admin assign UI |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 37 | BE permission claims |
| 40 | auth e2e tokens/getMe |
| 42 | dashboard layout |
| 46 | site store siteReady |
| **49** | this |
| 52 | MRT editPermission |

---

## Chejori digest koni

1. Badge vs fehrest shomare  
2. AuthProvider claims  
3. Guard ladder Auth→Component→Page/Route→Guard  
4. componentPaths + staff example  
5. FE≠BE security mantra  

---

## Glossary

| term | ma'ni |
|---|---|
| claim value | string permission id |
| componentId | FE id matched to claim |
| getMe | session + claims endpoint |
| AuthGuard | must login |
| GuestGuard | must logout |
| PageGuard | page claim + 403 |
| RouteAccessGuard | URL→nav claim |
| Guard | hide children |
| filterNav | menu by claims |
| siteReady | site selected before judge |

---

## Deep dive — longest path match

`/a/b/c` matches nav `/a/b` over `/a` if both have componentIds.  
Leaf permissions win — configure nav carefully.

---

## Deep dive — flat claims

getMe returns flat list for **current site context** (product).  
Not nested tree — Set lookup O(1).  
Comment utils: «برای سایت انتخاب‌شده».

---

## Deep dive — naming conventions

`*View`, `*CreateButton`, `*EditButton`, `*DeleteButton` common.  
Grid `X-View` / form `X-Create` mentioned in file header — know convention when adding.

---

## Anti-pattern

| bad | better |
|---|---|
| Only hide button | BE authorize |
| Magic string `'staffCreate'` typo | componentPaths ref |
| Role string only | component claims |
| Skip PageGuard | always page + actions |
| Compare claims case-sensitive local | use hasComponentAccess |
| Show 403 before session ready | wait loading flags |

---

## Interview 60s

«After getMe we keep a flat claims array. The dashboard is behind AuthGuard; menus are filtered by componentId; pages use PageGuard or RouteAccessGuard; buttons use Guard. Those IDs live in componentPaths and match backend permission claim values. UI hiding is UX—APIs still enforce permissions.»

---

## Quick self-test

1. claims source? → getMe  
2. Hide button component? → Guard  
3. Page 403? → PageGuard  
4. Catalog file? → componentPaths  
5. Nav hide? → filterNavByComponentGuard  
6. Login wall? → AuthGuard  
7. Real security? → BE  

---

## Final checklist

- [ ] AuthProvider claims  
- [ ] Auth/Guest guards  
- [ ] componentId model  
- [ ] Guard / Page / Route  
- [ ] nav filter + paths catalog  
- [ ] FE vs BE  
- [ ] resume  

---

## Extra — Farz kon new page

1. Add componentPaths node  
2. Nav item componentId  
3. page.jsx PageGuard  
4. Buttons Guard  
5. BE claim type/value + role assign  
6. Test user without claim  

---

## Extra — 403 UX

forbiddenPath default `/error/403`.  
Don't infinite replace — ensure 403 page not guarded same id.

---

## Extra — Soalat chera

**Chera flat claims?** fast Set lookup.  
**Chera componentPaths?** single catalog admin+FE.  
**Chera siteReady?** tenant-scoped permissions.  
**Chera both Page + Route guards?** defense + nav-derived URLs.  
**Chera not only CSS hide?** still need null render; BE critical.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «AuthProvider loads claims. AuthGuard requires login. ComponentGuard exposes a Set. Menus filter by componentId, pages PageGuard, buttons Guard. IDs come from componentPaths and match backend claims.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| All menus gone | claims [] / getMe fail |
| Button visible API 403 | BE missing / OK UX |
| 403 loop | bad forbiddenPath |
| Login loop | GuestGuard returnTo |
| Deep link open wrongly | missing Route/Page guard |
| Stale permissions | no session refresh |
| Case mismatch | use utils lowercase |

---

## Extra — Layer checklist

| layer | guard |
|---|---|
| App entry guest | GuestGuard |
| Dashboard | AuthGuard |
| Menu | filterNav |
| URL | RouteAccessGuard |
| Page | PageGuard |
| Control | Guard |
| API | BE permission |

---

## Extra — Related days

- 37 BE claims  
- 40 e2e auth  
- 46 site  
- 52 MRT permissions  

---

## Extra — access-permission module

Admin UI tree from componentPaths + Guard on select-all buttons.  
Assigning checks = writing claim values users later receive in getMe.

---

## Extra — Impersonation / support

Agar nist — don't claim.  
Would need getMe claims swap.

---

## Band-e gharardad-e jadid

AuthGuard = darban vorud.  
claims = kart dastresi.  
componentId = shomare otagh/dokme.  
componentPaths = fehrest shomare-ha.  
Guard = parda (hide).  
PageGuard = ghofl dar.  
BE = polisimostaghim.

---

## 10 jomle fluency

1. getMe returns flat permission claims.  
2. AuthGuard blocks anonymous dashboard use.  
3. GuestGuard keeps signed-in users off login.  
4. componentId strings match claim values.  
5. componentPaths is the FE catalog.  
6. Guard hides unauthorized controls.  
7. PageGuard redirects to 403.  
8. RouteAccessGuard maps URL to nav claim.  
9. Nav items filter by the same claims.  
10. Backend authorization remains mandatory.

---

## Extra — Comparison CASL / permission libs

CASL = ability objects.  
Dejban = simple string Set — enough + matches BE claim store.  
Tradeoff: less expression; simpler ops.

---

## Extra — testing guards

Unit: hasComponentAccess pure.  
RTL: render Guard with mock AuthContext claims.  
E2E: user A sees create; user B not.

---

## Extra — sessionRefreshing detail

During getMe refresh, PageGuard shows LoadingScreen — prevents false 403 then content flash.

---

## Extra — signInUrl multi-app

AuthGuard prefers `config.auth.signInUrl` (portal main) with returnTo — monorepo apps (Day 43).

---

## Band-e gharardad — ye bar digar sade

1. **Login session** = AuthProvider.  
2. **Must login** = AuthGuard.  
3. **Must guest** = GuestGuard.  
4. **claims[]** = allowed ids.  
5. **componentPaths** = id dictionary.  
6. **Guard** = hide control.  
7. **PageGuard** = page gate.  
8. **RouteAccessGuard** = URL gate via nav.  
9. **filterNav** = menu gate.  
10. **BE** = real security.

---

## Extra — Capacity

Set of claims small (hundreds).  
componentPaths file large — editor/git cost; runtime just strings used.

---

## Extra — onboarding checklist permission

FE id → nav → page → buttons → BE claim seed → role UI assign → verify getMe.

---

## Extra — whitespace claim values

trim? utils stringify; BE should not emit spaces.  
Validate admin assign UI.

---

## Extra — parallel License + Guard

Module unlicensed → hide whole branch even if claims exist.  
Product packaging.

---

## Extra — interview trap «Is this RBAC or ABAC?»

Mostly RBAC with fine-grained permissions (claim values).  
Site adds tenancy dimension — hybrid with multi-tenant RBAC.

---

## Extra — claim refresh strategies

After admin changes role: user must `checkUserSession` / re-login / token refresh path that reloads getMe.  
Soft: button «بروزرسانی دسترسی» calling checkUserSession.  
Without it — stale UI until reload.

---

## Extra — anonymous public routes

Maintenance / public ticket pages — outside AuthGuard tree (`blank` layout).  
Don't wrap public with PageGuard requiring claims.

---

## Extra — returnTo open redirect

GuestGuard uses `safeReturnUrl` — good.  
AuthGuard builds returnTo from `window.location.pathname` — prefer same-origin only (minimal-shared helper when available).

---

## Extra — debug claims in DevTools

Temporary: log `useAuthContext().claims` length + includes `staffCreateButton`.  
React Query/auth not involved — context state.

---

## Extra — nav `#` parents

Groups with `path: '#'` and no componentId stay if children remain after filter.  
Utils prune empty `#` parents — know behavior when all children denied.

---

## Extra — duplicate componentIds

Two nav items same id OK for access; path match still longest path.  
Don't reuse same id for unrelated features — admin matrix confusion.

---

## Extra — Server Components note

Guards are client (`'use client'`).  
page.jsx can import PageGuard as client child — OK in App Router.

---

## Extra — axios 403 vs PageGuard 403

PageGuard = route-level UX.  
Axios interceptor toast «دسترسی ندارید» = API-level (Day 44).  
Both can fire; different layers.

---

## Extra — claims include vs exact

Lookup is exact string in Set — no prefix inheritance (`staff` ≠ `staffCreateButton`).  
Parent nav claim ≠ child button claim — assign both if needed.

---

## Extra — documentation for admins

Human `displayValue` Farsi in componentPaths feeds Access Permission tree labels.  
Keep displayValue meaningful when adding nodes.

---

## Khoruj-e zehni

> Midunam Auth UI Dejban ba AuthProvider/getMe claims; AuthGuard/GuestGuard; componentId + componentPaths; Guard/PageGuard/RouteAccessGuard/filterNav; va inke hide FE jaye authorize BE nist.

Age in paragraph mal-e to shod — Day 49 done.

---

*Day 49 tamum. Ba'd: Day 50 — SignalR client. Fehrest: [README.md](./README.md).*
