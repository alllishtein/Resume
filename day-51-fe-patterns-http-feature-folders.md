# Day 51 — FE patterns (`*.http.js` / feature folders)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** feature jadid (list + form + API) koja beravad ta chaos nashavad?

**Javab Dejban (apps/dejban) — feature slice + layered names:**

```
src/
├── app/dashboard/.../page.jsx     ← thin route (PageGuard + View)
├── sections/<feature>/            ← UI (views, forms, tabs)
│   ├── view/*-list-view.jsx
│   ├── *-new-edit-form.jsx
│   └── component/...
├── services/<feature>/            ← data hooks + HTTP
│   ├── <feature>.http.js          ← Axios calls only
│   ├── <feature>.keys.js          ← TanStack queryKey factory
│   └── <feature>.service.js       ← useQuery / useMutation
├── lib/api.js                     ← endpoints catalog + apiClient
├── routes/paths.js                ← URL constants
├── layouts/nav-config-*.jsx       ← menu + componentId
├── locales/langs/*/feature.json   ← i18n
└── stores/                        ← legacy Zustand (kam; Day 46)
```

**Olgu-ye seda:**

```
page.jsx → StaffListView (sections)
  → useGetStaffWithPagination (services/*.service.js)
      → queryKey (*.keys.js)
      → getStaffWithPagination (*.http.js)
          → axiosInstance + endpoints (lib/api.js)
```

Approx counts (dejban): **~65** `*.http.js`, **~20** `*.https.js` (typo/legacy name), **~82** keys, **~85** service.

**Band-e gharardad-e jadid:** farz kon / yani chi / chera.

Day 44 = Query+Axios *mechanics*. Day 45 = forms. Day 49 = guards. **In ruz = *folder contract* + checklist feature.**

---

# BAKHSH-E AVAL: WORLD — chera feature folders?

## Farz kon — otagh-haye joda

**Bad:** hame API to `api.js` 5000 line + components flat.  
**Good:** har feature folder — find staff = `sections/staff` + `services/staff`.

| style | fekr |
|---|---|
| Layer-first (`components/`, `hooks/`, `api/`) | horizontal |
| **Feature-first (`sections/x`, `services/x`)** | vertical slice Dejban |

Shared chrome: `components/`, `layouts/`, `hook-form/` — cross-cutting OK.

---

## Chera split http / keys / service?

| file | masool | React? |
|---|---|---|
| `*.http.js` | fetch/post/put/delete | **na** |
| `*.keys.js` | queryKey factory | na |
| `*.service.js` | useQuery/useMutation | **bale** |

**Yani chi:** test http pure; invalidate by keys; UI imports only service hooks.

---

# BAKHSH-E DOVOM: map folders

## Qesmat 1 — `app/` (App Router)

Thin:

```jsx
export default function Page() {
  return (
    <PageGuard componentId={componentPaths.…staff.value}>
      <StaffListView />
    </PageGuard>
  );
}
```

**Rule:** no fat business UI in `page.jsx`.  
Folder path ≈ URL (`dashboard/personnel/staff`).

---

## Qesmat 2 — `sections/<feature>/`

| piece | mesal |
|---|---|
| list | `view/staff-list-view.jsx` |
| form | `staff-new-edit-form.jsx` |
| schema | `component/staff-schema.js` |
| tabs/dialogs | `component/*`, `*-dialog.jsx` |
| excel | `staff-excel-import-dialog.jsx` |

**Import services** az list/form — na axios mostaghim (prefer).

Naming: `*-list-view`, `*-new-edit-form` Minimals heritage.

---

## Qesmat 3 — `services/<feature>/`

Trinity:

```
personnels.http.js / personnels.keys.js / personnels.service.js
staff.http.js / staff.keys.js / staff.service.js
```

**Dual domains:** `personnels` vs `staff` — related HR; don't merge blindly (endpoints differ).

Typo smell: `*.https.js` (~20) — same role as http; normalize when touching.

---

## Qesmat 4 — `*.http.js` contract

```js
import axiosInstance, { endpoints } from 'src/lib/api';

export const getStaffWithPagination = async ({ page, pageSize, ... } = {}) => {
  const response = await axiosInstance.get(endpoints.staff.list, { params });
  return response.data;
};
```

Rules:

1. No hooks  
2. Throw errors (Query needs reject)  
3. Use `endpoints.*` — na hardcoded URL scatter  
4. Return `response.data`  
5. Optional try/catch log + rethrow  

Default export `axiosInstance` = `apiClient` (Day 44).

---

## Qesmat 5 — `*.keys.js` contract

```js
export const staffKeys = {
  all: ['staff'],
  lists: () => [...staffKeys.all, 'list'],
  list: (params) => [...staffKeys.lists(), params],
  detail: (id) => [...staffKeys.all, 'detail', id],
};
```

Invalidate `lists()` after create — Day 44.

---

## Qesmat 6 — `*.service.js` contract

```js
export const useGetStaffWithPagination = (params) =>
  useQuery({
    queryKey: staffKeys.list(params),
    queryFn: () => staffApi.getStaffWithPagination(params),
  });

export const useCreateStaff = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: staffApi.createStaff,
    onSuccess: () => qc.invalidateQueries({ queryKey: staffKeys.lists() }),
  });
};
```

UI: `const { data, isLoading, refetch } = useGetStaffWithPagination(...)`.

---

## Qesmat 7 — `lib/api.js`

- Re-export `apiClient` helpers  
- Mega `endpoints` object (staff, personnels, tickets, …)  
- Smell: merge conflict magnet — still *one* URL dictionary  

New endpoint: add here + http uses it.

---

## Qesmat 8 — `routes/paths.js` + nav

`paths.dashboard.staff.root` for Link/router.  
`layouts/nav-config-dashboard.jsx`: path + `componentId` (Day 49).  
Keep path string sync with `app/` folder.

---

## Qesmat 9 — locales + guards + forms

| concern | koja |
|---|---|
| i18n | `locales/langs/fa-IR|en-US/<ns>.json` |
| Zod | `sections/.../schema` or inline |
| Page claim | `page.jsx` PageGuard |
| Button claim | Guard in list-view |
| SignalR | `sections/.../use-*-hub.js` (Day 50) |

---

## Qesmat 10 — digar folders

| folder | naqsh |
|---|---|
| `components/` | shared UI (hook-form, table helpers) |
| `hooks/` | shared hooks (infinite-list, server-time) |
| `utils/` | pure helpers |
| `stores/` | legacy Zustand API stores |
| `workspace-tabs/` | tabs feature |
| `_mock/` | fake data (if any) |

---

# BAKHSH-E SEVOM: checklist feature jadid

## 12 step (seda kon)

1. `endpoints` in `lib/api.js`  
2. `services/foo/foo.http.js` CRUD  
3. `foo.keys.js`  
4. `foo.service.js` hooks + invalidate  
5. `sections/foo/view/foo-list-view.jsx`  
6. `foo-new-edit-form.jsx` + Zod (Day 45)  
7. `app/dashboard/.../foo/page.jsx` + PageGuard  
8. `paths.js` entry  
9. `nav-config` + `componentPaths` ids (Day 49)  
10. `locales` fa+en JSON (Day 48)  
11. Guards on create/edit/delete buttons  
12. Manual test list/create/edit/delete + 403  

Optional: excel dialog, SignalR listener, reports.

---

## Dependency direction (mohem)

```
app → sections → services → lib/api → @repo/api-client
                 ↘ locales / auth-guard / ui
```

**Forbidden:** `services` import az `sections` (cycle).  
`http` import React — forbidden.

---

# BAKHSH-E CHAHAROM: namings & smells

## Naming table

| pattern | good | smell |
|---|---|---|
| HTTP file | `staff.http.js` | `staff.https.js` |
| List UI | `*-list-view.jsx` | random `Staff.jsx` |
| Form | `*-new-edit-form.jsx` | god file 3k lines OK but split tabs |
| Hook | `useGetX` / `useCreateX` | `fetchX` in component |

---

## Smell-ha

1. `*.https.js` typo inconsistency  
2. `endpoints` mega-file conflicts  
3. page.jsx fat UI  
4. axios in section bypassing service  
5. Zustand store + Query same domain (Day 46)  
6. staff vs personnels confusion  
7. console.error every http  
8. Broad invalidate `queryKey: ''`  
9. Duplicate components still in app vs `@repo/ui`  
10. path string drift nav vs app folder  

---

## Debug checklist

| symptom | check |
|---|---|
| Module not found service | path `src/services/...` |
| 404 API | endpoints spelling |
| Stale list | keys + invalidate |
| Wrong import cycle | services→sections? |
| Guard miss | page vs button ids |
| Form submit no API | Zod / mutation wire |

---

## 25 soal-e mosahebe

1. http vs service vs keys?  
2. Chera page thin?  
3. sections vs components?  
4. endpoints koja?  
5. Feature checklist?  
6. Dependency direction?  
7. https.js smell?  
8. How invalidate after create?  
9. PageGuard koja?  
10. paths.js role?  
11. staff vs personnels?  
12. Can http use hooks?  
13. Where Zod lives?  
14. Shared hook-form?  
15. Legacy stores?  
16. Add endpoint steps?  
17. Why not only services/api.js one file?  
18. Infinite list hook share?  
19. Monorepo packages vs app services?  
20. Test which layer easiest?  
21. SignalR hook folder?  
22. i18n namespace naming?  
23. MRT in which folder? (Day 52)  
24. Day 44 vs 51?  
25. Day 51 one-liner?

---

## Senario-ha

**S1:** New «majors» CRUD — follow 12 steps.  
**S2:** Hotfix endpoint only — change http + endpoints; keys same.  
**S3:** Two list views same API — shared service hooks.  
**S4:** Import excel — dialog in sections; preview/commit http methods.  
**S5:** Refactor https→http rename + update imports.

---

## Mini lab

1. Trace staff: page → list-view → service → http → endpoints  
2. Count `*.https.js` — open one  
3. Add fake key factory method — invalidate mentally  
4. Find a section that calls axios directly (smell hunt)  
5. Draw dependency arrows on paper  

---

## Resume (1 paragraph)

> Structured Dejban feature work as **thin App Router pages**, **`sections/` UI**, and **`services/` data** with a consistent **`*.http.js` / `*.keys.js` / `*.service.js`** trio over a shared `endpoints` map—keeping HTTP pure, React Query in services, and screens composable with guards, forms, and i18n.

Keywords: `feature folders` · `http.js` · `query keys` · `service hooks` · `sections` · `endpoints` · `PageGuard` · `clean architecture FE`

---

## File-haye mohem (canonical)

| path | chera |
|---|---|
| `services/staff/*` | trinity example |
| `sections/staff/view/staff-list-view.jsx` | consumer |
| `app/dashboard/personnel/staff/page.jsx` | thin page |
| `lib/api.js` | endpoints |
| `routes/paths.js` | URLs |
| `layouts/nav-config-dashboard.jsx` | nav+ids |
| `components/hook-form/*` | shared fields |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 42 | app router pages |
| 44 | Query/Axios mechanics |
| 45 | forms in sections |
| 48 | locales per feature |
| 49 | guards on page/buttons |
| 50 | hubs beside sections |
| **51** | this — structure |
| 52 | tables inside list-views |
| 53 | SWR alternate app |

---

## Chejori digest koni

1. Triangle http/keys/service  
2. Thin page mantra  
3. 12-step checklist hafz  
4. Dependency arrow  
5. Resume  

---

## Glossary

| term | ma'ni |
|---|---|
| feature folder | vertical slice files |
| http module | pure API functions |
| keys factory | queryKey builders |
| service hooks | React Query wrappers |
| section | feature UI area |
| thin page | route shell only |
| endpoints map | URL dictionary |
| list-view | main table screen |
| new-edit-form | create/update dialog/page |

---

## Deep dive — when shared `hooks/`

`useInfiniteList` — generic across services.  
`useServerTimeRef` — cross forms.  
If only one feature uses it → keep under `sections/foo` or `services/foo`.

---

## Deep dive — packages vs app

`@repo/api-client` = transport.  
`@repo/ui` = chrome/guards/theme.  
**Domain API** (staff endpoints) stays in **app** `services/` — product-specific.

---

## Deep dive — colocate test later

`staff.http.test.js` next to http — easy.  
Don't require for booklet; pattern ready.

---

## Anti-pattern

| bad | better |
|---|---|
| fetch in useEffect in view | service useQuery |
| URL string in 10 components | endpoints + paths |
| Import http in JSX | import service hooks |
| God `utils/api.js` per call | trinity |
| Circular sections↔services | one-way |
| Skip keys file | always keys |

---

## Interview 60s

«Each feature has UI under sections and data under services. HTTP functions stay pure in `*.http.js`, query keys in `*.keys.js`, and React Query hooks in `*.service.js`. App Router pages only mount a PageGuard and a list or form view. Shared endpoints live in `lib/api.js`.»

---

## Quick self-test

1. Trinity files? → http / keys / service  
2. UI folder? → sections  
3. Thin page does? → Guard + View  
4. endpoints file? → lib/api.js  
5. https.js? → smell typo  
6. http may use hooks? → no  
7. After create? → invalidate lists keys  

---

## Final checklist

- [ ] Folder map  
- [ ] Trinity rules  
- [ ] Thin page  
- [ ] 12-step feature  
- [ ] Dependency direction  
- [ ] smells  
- [ ] resume  

---

## Extra — Farz kon copy-paste feature

Copy `patrol-area` trinity + section + page — rename endpoints/keys/paths/componentIds/locales.  
Faster than from scratch; still run checklist.

---

## Extra — barrel exports?

Some features `index.js` re-export — optional.  
Dejban often deep import `staff.service` — OK explicit.

---

## Extra — Soalat chera

**Chera 3 files?** SRP + testability.  
**Chera sections name?** Minimals/template; means feature UI.  
**Chera not Next server actions?** Axios+Query stack (Day 42/44).  
**Chera endpoints central?** discoverability.  
**Chera app not package for staff?** product-bound.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «Page to section view to service hook to http to shared axios endpoints. Keys define cache identity. Forms and guards live beside the UI; translations beside locales.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Cannot find module | wrong feature folder name |
| Empty list | http params / endpoints |
| Create OK UI stale | no invalidate |
| Build cycle | circular import |
| 403 button visible | forgot Guard |
| Wrong API host | apiClient base |

---

## Extra — Layer checklist new PR

| change | files touched |
|---|---|
| New field API | endpoints + http + form + schema |
| New button perm | componentPaths + Guard + BE |
| New filter | list-view + keys params + http params |

---

## Extra — Related days

44 Query · 45 RHF · 48 i18n · 49 guards · 50 hubs · 52 MRT  

---

## Extra — `view/` subfolder

Keeps list screens grouped when feature has many dialogs.  
Not mandatory for tiny features.

---

## Extra — report / special pages

`personnel-report/` under staff — still section feature; may own http.

---

## Band-e gharardad-e jadid

page = dar.  
section = otagh UI.  
service = ashpazkhane data.  
http = telephone API.  
keys = label yakhchal.  
endpoints = fehrest shomare.  
paths = address khiaban.

---

## 10 jomle fluency

1. Features split into sections and services.  
2. Pages stay thin with PageGuard.  
3. http.js has pure Axios calls.  
4. keys.js builds queryKeys.  
5. service.js exposes React Query hooks.  
6. endpoints live in lib/api.js.  
7. Forms and schemas live under sections.  
8. Nav paths and componentIds wire separately.  
9. Avoid https.js typos and circular imports.  
10. Follow the 12-step checklist for new CRUD.

---

## Extra — Comparison atomic design

Atoms in `components/`; organisms often in sections.  
Don't over-abstract — feature first.

---

## Extra — monorepo multi-app

gate/dcc may copy pattern; shared only via `@repo/*`.  
Don't put dejban staff service in ui package.

---

## Extra — migration from Zustand store

Replace `stores/units-store` usage with services trinity (Day 46 honesty).  
Incremental per screen.

---

## Extra — Code review lens

PR reviewer asks: http pure? keys? invalidate? page thin? guards? locales? endpoints?

---

## Band-e gharardad — ye bar digar sade

1. **Feature** = sections + services.  
2. **http** = API functions.  
3. **keys** = cache addresses.  
4. **service** = hooks.  
5. **page** = route + guard.  
6. **endpoints** = URL map.  
7. **paths** = FE routes.  
8. **One-way** imports.  
9. **Checklist** 12 steps.  
10. **Smells** https / fat page / bypass.

---

## Extra — Capacity / scale repo

100+ service folders OK — discover by name.  
eslint import boundaries optional future.

---

## Extra — onboarding day-1 task

Implement tiny lookup CRUD with full trinity — proves pattern.

---

## Extra — excel / upload methods

Still `*.http.js` (FormData) — same layer; UI dialog in sections (Day 38/41).

---

## Extra — generate?

No official codegen required — convention > generator.  
OpenAPI client possible later — still wrap in http/service.

---

## Extra — index count honesty

Numbers drift; re-count when quoting resume.  
Pattern stable even if counts change.

---

## Extra — `assign-*-to-user` dialogs

Live under sections/staff — feature owns related workflows not only CRUD entity.

---

## Extra — blank / maintenance app routes

Outside feature CRUD — special `app/` layouts; no services needed.

---

## Extra — interview whiteboard folders

Boxes: app | sections | services(http,keys,service) | lib/api | packages.

---

## Extra — PR size advice

One feature vertical slice per PR when possible — easier review than horizontal «all http files».

---

## Extra — TypeScript future

`.ts` trinity with DTO types — same folders; zod infer optional.

---

## Extra — delete bulk pattern

http: `deleteX(ids)` with body `{ ids }`.  
service: mutation invalidate lists.  
list-view: selection + Guard delete button.  
Same trinity — no special folder.

---

## Extra — getById detail page

Optional `app/.../[id]/page.jsx` → detail view → `useGetXById`.  
keys.detail(id); enabled: !!id.

---

## Extra — search params sync

List filters in URL via `useSearchParams` (routes/hooks) + keys.list(params).  
Keeps shareable links; params object stable for keys.

---

## Extra — optimistic UI?

Rare; prefer invalidate.  
If needed: mutation onMutate in service.js — still not in http.

---

## Extra — storybook/sections

Optional Storybook for dumb components under sections/component — data via props; services mocked.

---

## Extra — lint rule wish

`no-restricted-imports`: sections cannot import axios; must use services.  
Not enforced today — discipline + review.

---

## Extra — prefetch on hover

Optional in list-view: `queryClient.prefetchQuery({ queryKey: keys.detail(id), queryFn })`.  
Stays in section/service — not http change.

---

## Extra — error boundary placement

Prefer around section views; failed Query shows empty/error UI inside list-view.  
Don't rely on route error.jsx alone for API errors.

---

## Khoruj-e zehni

> Midunam FE Dejban ba feature folders: page thin, sections UI, services ba http/keys/service; endpoints markazi; dependency yek-tarafe; va checklist 12-step baraye feature jadid — mechanics Query/form/guard ruz-haye digar.

Age in paragraph mal-e to shod — Day 51 done.

---

*Day 51 tamum. Ba'd: Day 52 � material-react-table (amade). Fehrest: [README.md](./README.md).*
