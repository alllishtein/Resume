# Day 53 — SWR

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** server-state cache — faghat TanStack Query (Day 44)?

**Javab monorepo (honesty):**

| app | data library |
|---|---|
| **`apps/dejban`** (asosli) | **TanStack Query** — `*.service.js` |
| **`apps/access-control`** | **SWR** — `src/actions/*.js` |
| `apps/main` / `dejban` package.json | `swr` dep momken **unused** (leftover) |

SWR = **Stale-While-Revalidate**: data neshun bede (stale), posht-sahne revalidate.

Olgu access-control:

```js
// actions/device.js
const swrOptions = {
  revalidateIfStale: false,
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  revalidateOnMount: true,
};

useSWR(url | [url, { params }], api.fetcher, swrOptions)
→ { data, isLoading, error, isValidating, mutate }
```

Mutations: plain `createItem` / `deleteItem` functions → ba'd `mutate()` to refresh cache.

**Band-e gharardad-e jadid:** farz kon / yani chi / chera + **direction:** dejban = Query; AC = SWR legacy/parallel stack.

Day 44 = Query deep. **In ruz = SWR koja / chejori / vs Query.**

---

# BAKHSH-E AVAL: WORLD — SWR chie?

## Farz kon — etiket ghazaye supermarket

Label ghabli (stale) hanooz valid-e baraye namayesh; posht-sahne check kon fresh.  
SWR: cache by **key**; `useSWR(key, fetcher)`.

```js
const { data, error, isLoading, isValidating, mutate } = useSWR('/api/user', fetcher);
```

| mafhum | ma'ni |
|---|---|
| key | cache identity (string / array / null=skip) |
| fetcher | (key) => promise |
| mutate | update/revalidate cache |
| isValidating | background refetch |

Vercel / Next ecosystem classic; lightweight vs Query.

---

## Chera digar Query?

| | SWR | TanStack Query |
|---|---|---|
| API surface | kuchek | bozorg (mutations, infinite, …) |
| Mutations | often manual + mutate | useMutation first-class |
| Devtools / policies | simpler | richer |
| Dejban asosli | na | **bale** |
| access-control | **bale** | kam |

Interview: «We use Query on the main Dejban app; access-control still uses SWR hooks in an actions layer.»

---

# BAKHSH-E DOVOM: DEJBAN — access-control

## Qesmat 1 — `src/actions/` (na services trinity)

Files: `device.js`, `device-type.js`, `access-group.js`, `access-log.js`, `calendar.js`, `device-user.js`, `monitoring.js`, `auth.js`.

Har file: `useGetX` hooks ba SWR + plain CRUD functions.

**Contrast Day 51:** dejban `services/*.http|keys|service`; AC = **actions** bundle.

---

## Qesmat 2 — key shapes

```js
// list with params
const url = [api.endpoints.devices.list, { params: queryParams }];
useSWR(url, api.fetcher, swrOptions);

// detail — empty key skips
const url = id ? `${api.endpoints.devices.detail}/${id}` : '';
useSWR(url, api.fetcher, swrOptions);
```

`api.fetcher` az shared axios helpers — supports `string | [url, config]` (Day 44 `fetcher` in api-client).

**Yani chi:** SWR key serialization includes params → different filters = different cache entries.

---

## Qesmat 3 — swrOptions Dejban-AC

```js
revalidateIfStale: false,
revalidateOnFocus: false,
revalidateOnReconnect: false,
revalidateOnMount: true, // often
```

**Chera disable focus/reconnect?** Kam surprise refetch; control via `mutate()` ba'd az write.  
Tradeoff: multi-tab stale until mutate/remount.

---

## Qesmat 4 — return shape memo

```js
return useMemo(() => ({
  devices: data?.items || [],
  devicesLoading: isLoading,
  devicesTotalCount: data?.totalCount || 0,
  devicesError: error,
  devicesValidating: isValidating,
  devicesEmpty: !isLoading && !data?.items?.length,
  mutate,
}), [...]);
```

UI: `const { devices, devicesLoading, mutate } = useGetDevices(...)`.

Naming prefix domain — AC convention.

---

## Qesmat 5 — writes + mutate

```js
// actions: plain functions
export function deleteDevice(deviceId) {
  return api.deleteItem(url, { ids: [...] });
}

// view after success:
await deleteDevice(id);
await mutate(); // revalidate SWR key
```

No `useSWRMutation` required in current code — imperative.

---

## Qesmat 6 — UI consumer

`DeviceListView` imports `useGetDevices`, `deleteDevice` from `src/actions/device`.  
Table may be MUI Table (not always MRT) — older AC UI.  
Zustand action stores still for dialogs (Day 46).

---

## Qesmat 7 — dejban package.json `swr`

Dependency present; **no `useSWR` imports** in dejban src (current).  
Smell: unused dep — remove later or leftover from template.

**Resume caution:** don't claim «dejban uses SWR» — claim access-control / monorepo dual stack.

---

## Qesmat 8 — fetcher + auth

Same Axios interceptors (Bearer, site, refresh) when AC uses shared apiClient/fetcher.  
SWR doesn't replace auth — only cache/fetch lifecycle.

---

# BAKHSH-E SEVOM: SWR vs Query (mosahebe jadval)

| need | SWR (AC) | Query (dejban) |
|---|---|---|
| List+detail cache | useSWR keys | useQuery + keys factory |
| Mutations | fn + mutate() | useMutation + invalidateQueries |
| Infinite | useSWRInfinite | useInfiniteQuery |
| Devtools | SWR DevTools | RQ Devtools |
| Folder pattern | actions/ | services trinity |
| Revalidate on focus | disabled here | default often on |

**Migration path:** AC → Query possible; not done. Honesty.

---

# BAKHSH-E CHAHAROM: WORLD extras useful

## Conditional fetch

`useSWR(id ? url : null, fetcher)` — null key = no fetch (like `enabled: !!id`).

## Global mutate

`import { mutate } from 'swr'` — mutate by key from outside hook.  
AC mostly returns hook `mutate`.

## SWRConfig

Provider defaults — check if AC sets; often per-hook options enough.

## isLoading vs isValidating

Loading = no data yet.  
Validating = revalidate with existing data (stale show).

---

# BAKHSH-E PANJOM: farz kon / senario

## Se dastan

**1) Open devices list AC**  
useGetDevices → SWR mount fetch → show items.

**2) Delete device**  
deleteDevice API → mutate() → list refresh.

**3) Same engineer on dejban staff**  
useGetStaff + useMutation invalidate — Query world (Day 44/51).

---

## Smell-ha

1. Dual stacks in one monorepo — onboarding cost  
2. swr unused in dejban package.json  
3. Revalidation mostly off — easy stale multi-user  
4. actions/ mixes hooks + CRUD — vs trinity SRP  
5. No shared keys factory — URL strings fragile  
6. useSWRMutation underused  
7. AC tables not unified MRT  

---

## Debug checklist

| symptom | check |
|---|---|
| No fetch | key null/empty |
| Stale after edit | forgot mutate() |
| Duplicate requests | key unstable object identity |
| Focus no refresh | options disabled — expected |
| 401 | axios interceptor not SWR |
| Wrong app pattern | dejban≠AC |

---

## 25 soal-e mosahebe

1. SWR acronym?  
2. key chie?  
3. fetcher array form?  
4. mutate chera?  
5. isValidating vs isLoading?  
6. Dejban uses SWR?  
7. Where SWR lives?  
8. swrOptions why disable focus?  
9. vs TanStack Query?  
10. Conditional key null?  
11. actions/ vs services/?  
12. How delete then refresh?  
13. Unused dep smell?  
14. SWRConfig?  
15. revalidateOnMount?  
16. Cache identity params?  
17. useSWRInfinite?  
18. Day 44 relation?  
19. Auth still Axios?  
20. Migration strategy?  
21. Global mutate?  
22. Stale-while-revalidate UX?  
23. Error handling?  
24. Prefetch?  
25. Day 53 one-liner?

---

## Senario-ha

**S1:** id undefined detail — pass `''` key skip.  
**S2:** Two components same key — share cache (SWR dedupe).  
**S3:** After create navigate list — mutate or remount.  
**S4:** Want focus revalidate — flip option true.  
**S5:** New AC feature — follow actions/ SWR pattern (or propose Query).

---

## Mini lab

1. Read `actions/device.js` useGetDevices  
2. Trace DeviceListView mutate after delete  
3. Confirm no useSWR in dejban (`rg`)  
4. Compare one Query service vs SWR action side-by-side  
5. Toggle revalidateOnFocus mentally — what changes  

---

## Resume (1 paragraph)

> In the monorepo, **access-control** loads server state with **SWR** (`useSWR` + shared Axios `fetcher`, conservative revalidate options, imperative `mutate` after writes in an `actions/` layer), while the main **Dejban** app standardizes on **TanStack Query**—so SWR is a parallel legacy/product stack, not the primary Dejban pattern.

Keywords: `SWR` · `useSWR` · `mutate` · `stale-while-revalidate` · `fetcher` · `revalidateOnFocus` · `TanStack Query vs SWR`

---

## File-haye mohem

| path | chera |
|---|---|
| `apps/access-control/src/actions/*.js` | SWR hooks |
| `apps/access-control/.../device-list-view.jsx` | consumer + mutate |
| `packages/api-client/.../fetcher` | shared GET helper |
| `apps/dejban/.../*.service.js` | Query contrast |
| Day 44 booklet | Query deep |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 43 | monorepo multi-app |
| 44 | Query primary |
| 46 | AC Zustand stores beside SWR |
| 51 | dejban folder trinity |
| **53** | this |
| 54 | Vite SPA (other FE style) |

---

## Chejori digest koni

1. SWR = cache by key + revalidate idea  
2. AC actions pattern  
3. Options disable auto revalidate  
4. vs Query table  
5. Honesty dejban unused dep  

---

## Glossary

| term | ma'ni |
|---|---|
| SWR | stale-while-revalidate lib |
| key | cache id |
| fetcher | load function |
| mutate | update/revalidate |
| isValidating | bg refresh flag |
| revalidateOnFocus | refetch tab focus |
| deduping | share in-flight by key |

---

## Deep dive — key as array

SWR serializes `[url, { params }]` — fetcher receives same.  
Must match api.fetcher contract Day 44.

---

## Deep dive — optimistic UI

`mutate(data, { optimisticData, rollbackOnError })` — WORLD feature; AC code often simple mutate().

---

## Deep dive — provider

Optional `<SWRConfig value={{ fetcher, ... }}>`.  
AC sets options per hook instead.

---

## Anti-pattern

| bad | better |
|---|---|
| Claim all FE is SWR | AC yes, dejban Query |
| Forget mutate after POST | always refresh |
| Unstable key each render | memo params |
| SWR for form local state | RHF |
| Enable all revalidators blindly | match product |

---

## Interview 60s

«Access-control uses SWR with URL keys and a shared Axios fetcher, mostly without focus revalidation, refreshing via mutate after writes. The main Dejban app uses TanStack Query with http/keys/service modules. Same monorepo, two data-fetching styles.»

---

## Quick self-test

1. SWR app? → access-control  
2. Dejban primary? → Query  
3. Folder AC? → actions/  
4. Refresh after delete? → mutate()  
5. Focus revalidate default here? → false  
6. fetcher from? → api / api-client  
7. Unused swr in dejban? → yes smell  

---

## Final checklist

- [ ] SWR mental model  
- [ ] AC actions pattern  
- [ ] options  
- [ ] mutate writes  
- [ ] vs Query  
- [ ] honesty dual stack  
- [ ] resume  

---

## Extra — Farz kon migrate one AC module to Query

1. Add services trinity  
2. Replace useSWR with useQuery  
3. deleteX → useMutation invalidate  
4. Remove action hook  
5. Keep Axios  

Incremental — don't big-bang.

---

## Extra — Soalat chera

**Chera SWR still?** historical AC app.  
**Chera options off?** control refetch cost.  
**Chera shared fetcher?** auth interceptors once.  
**Chera not SWR in dejban lists?** Query standard.  
**Chera keep dep on dejban?** cleanup candidate.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «SWR caches by key and fetches with a function. Access-control wraps that in actions hooks. After mutations they call mutate. Dejban does the same job with React Query instead.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Infinite loading | key always new |
| Old list | no mutate |
| Flash empty | treat loading vs validating |
| 403 loop | auth not SWR |
| Wrong params cache | key incomplete |

---

## Extra — Layer checklist AC

| layer | tech |
|---|---|
| Hook | useSWR |
| Key | url / [url,params] |
| Fetch | api.fetcher |
| Write | api.create/update/delete |
| Refresh | mutate |
| UI | sections + maybe Zustand |

---

## Extra — Related days

44 Query · 43 apps · 46 stores · 51 patterns  

---

## Extra — useSWRMutation (WORLD)

Newer API for posts; AC may not use — know exists for interview.

---

## Extra — suspense

SWR suspense mode — not primary AC pattern.

---

## Extra — compare React Query `staleTime: Infinity`

Similar to disabling auto revalidate — explicit refetch/invalidate.  
AC achieved via SWR flags.

---

## Band-e gharardad-e jadid

SWR = yakhchal ba label ghabli.  
key = shomare ghavati.  
fetcher = avordan.  
mutate = «dobare check kon».  
AC = ashpazkhane SWR.  
Dejban = ashpazkhane Query.  
Yek mall, do ashpaz.

---

## 10 jomle fluency

1. SWR means stale-while-revalidate.  
2. access-control uses useSWR in actions.  
3. Keys are URLs or URL-plus-params arrays.  
4. fetcher is the shared Axios helper.  
5. Auto revalidate on focus is disabled there.  
6. Writes call mutate to refresh.  
7. Dejban lists use TanStack Query instead.  
8. dejban may still list swr unused.  
9. Don't mix patterns inside one feature casually.  
10. Dual stack is historical honesty.

---

## Extra — version

`swr` ^2.3.x in package.json apps.

---

## Extra — monitoring actions

Live-ish endpoints still SWR — may pair SignalR (Day 50) elsewhere.

---

## Extra — auth sessions SWR

`useGetMySessions` in actions/auth.js — same options pattern.

---

## Extra — empty key vs conditional

`useSWR(id ? url : null)` clearer than `''` — both skip-ish; prefer null.

---

## Band-e gharardad — ye bar digar sade

1. **SWR** = lightweight server cache.  
2. **useSWR(key, fetcher)** = read.  
3. **mutate** = refresh/update.  
4. **AC actions/** = home.  
5. **Options** = little auto revalidate.  
6. **Axios** = still transport.  
7. **Dejban** = Query not SWR.  
8. **Compare** for mosahebe.  
9. **Migrate** optional.  
10. **Don't overclaim**.

---

## Extra — Capacity

SWR cache memory per key — fine.  
Dedupe helps parallel mounts.

---

## Extra — testing

Mock fetcher; assert mutate called.  
Or MSW + render hook.

---

## Extra — documentation link

SWR docs: key, mutate, global config — skim before interview.

---

## Extra — when pick SWR today for new app?

Small Next marketing / simple.  
Heavy admin + mutations → Query (dejban choice).

---

## Extra — interview trap «Is SWR only for Next?»

No — works CRA/Vite; popular with Next.  
AC is Next app too (Day 42 family).

---

## Extra — revalidateIfStale false

Even if data stale by age, won't auto revalidate until mutate/mount rules — aggressive cache.

---

## Extra — isValidating UX

Show subtle refresh indicator while keeping rows — better than full skeleton.

---

## Extra — shared cache across routes

Same key in two pages = instant data if warm — SWR win.

---

## Extra — error retry

SWR retries; combine with Axios refresh — careful double storms (usually OK).

---

## Extra — TypeScript

AC JS hooks; typing data generic useSWR<Device[]>() possible later.

---


## Extra — Farz kon supermarket label (ta'ammogh)

1. Rafti ghavati-ye «devices» ra az yakhchal bardashti — label ghabli (stale) hanooz khundani-st.
2. SWR hamzaman be anbar (API) zang mizane: «taze hast?»
3. Age taze bud, label avaz mishe; UI ghablan chizi dasht — flash empty kamtar.
4. To AC, ghadam 2 ro **kamtar** automatic mikonan (`revalidateOnFocus: false`) — faghat mount + `mutate` ba'd az write.

**Yani chi:** SWR default «optimistic about showing cache»; AC team goft «kamtar surprise refetch».

---

## Extra — Code walk `useGetDevices` (khat be khat)

```js
export function useGetDevices(filters, searchTerm) {
  const queryParams = { filters, searchTerm };
  const url = Object.keys(queryParams).length
    ? [api.endpoints.devices.list, { params: queryParams }]
    : api.endpoints.devices.list;
  const { data, isLoading, error, isValidating, mutate } =
    useSWR(url, api.fetcher, swrOptions);
  // ... map to devices / devicesLoading / ...
}
```

| ghesmat | naqsh |
|---|---|
| `queryParams` | filter + search → cache identity |
| array key | fetcher midune `params` Axios |
| `api.fetcher` | GET + unwrap (Day 44) |
| `swrOptions` | kam auto-revalidate |
| `useMemo` return | UI-friendly names |

**Chera `Object.keys(...).length`?** Hamishe keys darad — practically always array form. Smell kuchek: condition almost always true.

---

## Extra — `useGetDevice(id)` empty string

```js
const url = id ? `${api.endpoints.devices.detail}/${id}` : '';
useSWR(url, api.fetcher, swrOptions);
```

Empty string key: SWR may still treat oddly vs `null`.
World best practice: `null` / `undefined` to disable.
**Debug tip:** age detail spurious fetch didi, key ra check kon.

---

## Extra — CRUD naming inconsistency

`CreateDevice` / `UpdateDevice` / `deleteDevice` — casing mixed (Pascal vs camel).
Smell style — mosahebe: «legacy actions file, not critical».
Don't invent new inconsistency when adding hooks.

---

## Extra — Settings hooks same file

`useGetNetworkTypes`, door/reader settings — same `swrOptions`.
One file = device domain kitchen sink (hooks + writes + settings).
Contrast Day 51 trinity SRP — AC chose convenience.

---

## Extra — access-log / monitoring siblings

`access-log.js`, `monitoring.js`, `calendar.js`, `device-user.js`, `device-type.js`, `access-group.js`, `auth.js` — **same** options copy-paste.

**Smell:** no shared `const defaultSwrOptions` module — copy drift risk.
**Fix mental:** `lib/swr-options.js` export once (optional cleanup).

---

## Extra — DedupingInterval

SWR default dedupe ~2s same key.
Two DeviceList mounts = one network.
Query has similar dedupe — concept shared.

---

## Extra — Compare invalidateQueries vs mutate

| Query | SWR |
|---|---|
| `queryClient.invalidateQueries({ queryKey: staffKeys.lists() })` | `mutate()` from hook or `mutate(key)` global |
| prefix match keys factory | exact key / matcher fn |
| often after useMutation onSuccess | after await create/delete |

Same product goal: «list taze she».

---

## Extra — Band-e mosahebe «chera do library?»

**Javab sade:** do app, do history. access-control earlier / template SWR; Dejban product standardized on TanStack Query. Monorepo share Axios + MUI, not necessarily data lib.

**Javab pishrafte:** cost of unifying < cost of dual docs for now; migrate module-by-module when touching AC heavily.

---

## Extra — Farz kon bug «list stale after edit»

1. UpdateDevice success toast
2. Navigate list — cache still old
3. Root: no `mutate` / no remount with revalidateOnMount if key warm

Fix: `await mutate()` before close dialog, or `mutate(listKey)` global, or `router.refresh` not enough for SWR client cache.

---

## Extra — SignalR + SWR

Monitoring may get live events (Day 26/50).
Pattern: hub message → `mutate()` to pull REST snapshot.
Don't put full device list only in SignalR without REST source of truth unless designed.

---

## Extra — Zustand + SWR (Day 46)

Zustand: dialog open, selected row, wizard step.
SWR: server devices list.
Don't put API list into Zustand «because SWR exists» — dual source of truth smell.

---

## Extra — 10 soalat-e sari (pasokh yekkalame)

1. App SWR? → access-control
2. App Query? → dejban
3. Folder? → actions
4. Refresh? → mutate
5. Focus revalidate? → off
6. Transport? → Axios
7. Key list+params? → array
8. Detail skip? → empty/`null` key
9. Unused dep dejban? → swr
10. Next day? → Vite SPA

---

## Extra — Chejori PDF print koni

Az README link Day 53 → print browser → PDF.
Highlight jadval SWR vs Query baraye flashcard.

---

## Extra — Capacity / memory

Har key = cached response.
Filter combinations ziyad = ziyad entry.
Rarely problem; clear via mutate / page reload.

---

## Extra — keepPreviousData / placeholder

Query has `placeholderData`.
SWR: keep showing prior until new key resolves (version-dependent).
Know concept for UX when filters change fast.

---

## Extra — Error boundary

SWR `error` in hook — UI shows Alert.
Not same as Error Boundary crash.
Handle `devicesError` in list view.

---

## Extra — Version pin

`swr@^2.3.6` (dejban package.json even if unused).
AC app own package.json — check match when upgrading.

---

## Extra — Security note

SWR cache is in-memory JS — logout should clear sensitive keys (`mutate` clear / remount / full reload).
Auth token still Axios interceptor — Day 40/49.

---

## Extra — Final fluency drill (bekhoon boland)

«Access-control loads devices with useSWR. The key is the list URL plus params. The fetcher is our Axios helper. After deleteDevice we call mutate. The main Dejban app does not use this pattern; it uses TanStack Query.»

Age 20 sanie ravan gofti — interview-ready.

---
## Khoruj-e zehni

> Midunam SWR chie; to monorepo asosan access-control ba actions/useSWR + mutate estefade mikone; options revalidate kam; dejban Query-e; va dep swr to dejban momken unused bashe.

Age in paragraph mal-e to shod — Day 53 done.

---

*Day 53 tamum. Ba'd: Day 54 — Vite + React Router SPA (amade). Fehrest: [README.md](./README.md).*
