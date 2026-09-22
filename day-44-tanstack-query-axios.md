# Day 44 — TanStack Query + Axios

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** FE chejori data az Gateway begire, cache kone, ba'd az create/update list ro refresh kone — bedun `useEffect` + `useState` jahannam?

**Javab Dejban (apps/dejban):**

| layer | tool | file pattern |
|---|---|---|
| HTTP transport | **Axios** (`apiClient`) | `@repo/api-client` + `src/lib/api.js` |
| Server-state cache | **TanStack Query v5** | `*.service.js` hooks |
| URL map | `endpoints` object | `src/lib/api.js` |
| Raw calls | plain async fn | `*.http.js` |
| Query keys | factory | `*.keys.js` |

Zincir:

```
UI (sections)
  → useGetPersonnels / useCreatePersonnel  (*.service.js)
      → queryKey + queryFn / mutationFn
          → personnels.http.js
              → axiosInstance (default = apiClient)
                  → interceptors: Bearer, X-Site-Id, 401→refresh
                      → Gateway → backend
```

Provider: `@repo/ui` → `ClientProvider` = `QueryClientProvider` (gcTime 5 min).

**Band-e gharardad-e jadid:** farz kon / yani chi / chera.

Day 40 = auth interceptors story. Day 51 = folder patterns deepen. Day 53 = **SWR** (access-control legacy). **In ruz = Query + Axios dar dejban.**

---

# BAKHSH-E AVAL: WORLD — chera in do?

## Farz kon — yakhchal vs telephone

**Axios** = telephone: call API, Bearer, error status.  
**TanStack Query** = yakhchal + label: «list personnels ba in filter» — stale? refetch? ba'd az mutate invalidate?

| faqat Axios + useEffect | + Query |
|---|---|
| loading/error dasti | built-in |
| duplicate fetch 2 component | dedupe by queryKey |
| ba'd az save: `refetch()` dasti har ja | `invalidateQueries` |
| cache? khodet | cache + gcTime |

**Yani chi?** Axios = *how* HTTP. Query = *when/how often* + *cache identity*.

---

## Chera na faqat SWR?

SWR sade; Query ghavi-tar baraye mutations, infinite, key factories.  
Dejban **asosli** → Query.  
`access-control` app hanooz **SWR** (Day 53).  

Interview honesty: monorepo mixed — direction Query.

---

## TanStack Query v5 — WORLD kutah

- `useQuery` / `useMutation` / `useInfiniteQuery` / `useQueryClient`  
- `queryKey` array = identity  
- `gcTime` (ex cacheTime) — chand vaght unused data bemune  
- `staleTime` — chand vaght fresh (default 0 = zud stale)  
- `placeholderData` / `keepPreviousData` — UX pagination  
- `invalidateQueries` ba'd az write  

Dejban: `@tanstack/react-query` ^5.90 to apps + `@repo/ui`.

---

# BAKHSH-E DOVOM: DEJBAN — Axios

## Qesmat 1 — `@repo/api-client` (`createApiClient`)

`packages/api-client/src/axiosInstance.ts`:

```ts
axios.create({ baseURL, withCredentials: true })
```

**withCredentials:** refresh HttpOnly cookie beravad (Day 40).

Request interceptor:

| header / transform | az koja |
|---|---|
| `Accept-Language` | `localStorage i18nextLng` |
| `X-Site-Id` | Zustand `useSiteStore.getState().getSiteIds()` join `,` |
| `Authorization: Bearer` | `tokenStorage` — **na** roye refresh URL |
| digit normalize | params / JSON / FormData → English digits |

Response interceptor:

1. **401** (na login/refresh/public ticket) → single-flight `POST /auth/refresh`  
2. success → `tokenStorage.setAccess` → retry original  
3. refresh fail 401/403/404 → logout + clear + redirect sign-in  
4. **403** → toast Farsi «dastresi nadarid»

**refreshPromise** shared — chand 401 parallel = yek refresh (anti-storm).

---

## Qesmat 2 — `tokenStorage`

```ts
STORAGE_KEY = 'jwt_access_token'
getAccess / setAccess / clear  // localStorage
```

Faqat access. Refresh = cookie.

---

## Qesmat 3 — helpers

| helper | kar |
|---|---|
| `fetcher` | GET → `res.data` (SWR-style arg) |
| `getWithParams` | GET + params |
| `createItem` / `updateItem` / `deleteItem` | CRUD shorthand |

`apiClient` = singleton `createApiClient(resolveBaseUrl())`.  
Base: `NEXT_PUBLIC_SERVER_URL` (ya Vite `VITE_SERVER_URL`).

---

## Qesmat 4 — app bridge `src/lib/api.js`

```js
import { apiClient, fetcher, ... } from '@repo/api-client';
export { apiClient, ... };
export default apiClient;  // ← import axiosInstance as alias
export const endpoints = { personnels: {...}, ... }; // huge map
```

**Pattern http files:**

```js
import axiosInstance, { endpoints } from 'src/lib/api';
// axiosInstance === apiClient (default export)
```

**Yani chi?** App-specific URL catalog local; transport shared package.

---

## Qesmat 5 — `*.http.js` (transport only)

Mesal `personnels.http.js`:

- `getPersonnelsList({ page, pageSize, searchTerm, ... })`  
- `getPersonnelById` / `createPersonnel` / `updatePersonnel` / `deletePersonnels`  

**Rule:** no React hooks inja. Pure async + throw error.  
Service layer hooks seda mizane.

---

# BAKHSH-E SEVOM: DEJBAN — TanStack Query

## Qesmat 6 — `ClientProvider`

`packages/ui/.../client-provider.jsx`:

```jsx
const [queryClient] = useState(() => new QueryClient({
  defaultOptions: { queries: { gcTime: 5 * 60 * 1000 } },
}));
return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
```

**Chera useState factory?** Yek client per app mount — na recreate har render.  
**gcTime 5min:** unused query ba'd az 5 min garbage.  
**staleTime default 0:** focus/refetch behaviors default v5 — midunam.

Root layout Day 42 wraps `ClientProvider`.

---

## Qesmat 7 — `*.keys.js` (identity)

```js
export const personnelKeys = {
  all: ['personnels'],
  lists: () => [...personnelKeys.all, 'list'],
  list: (params) => [...personnelKeys.lists(), params],
  infinite: (params) => [...personnelKeys.all, 'infinite', params],
  detail: (id) => [...personnelKeys.all, 'detail', id],
  groupedByUnit: (params) => [...personnelKeys.all, 'grouped-by-unit', params],
};
```

**Farz kon:** invalidate `personnelKeys.lists()` → hame list variants (har params) invalidate prefix.  
**Chera factory?** typo kam; mosahebe standard TkDodo style.

---

## Qesmat 8 — `*.service.js` hooks

```js
useGetPersonnels(params, enabled) → useQuery({
  queryKey: personnelKeys.list(encodedParams),
  queryFn: () => personnelApi.getPersonnelsList(...),
  placeholderData: (prev) => prev,  // keep old while fetching new filter
  enabled,
});

useCreatePersonnel → useMutation({
  mutationFn: personnelApi.createPersonnel,
  onSuccess: () => qc.invalidateQueries({ queryKey: personnelKeys.lists() }),
});

useUpdatePersonnel → invalidate lists + detail(id)
useDeletePersonnels → invalidate lists
```

**Detail:** `enabled: !!id`, retry skip on 404.

**Yani chi?** UI faqat `const { data, isLoading } = useGetPersonnels(filters)`.

---

## Qesmat 9 — Infinite list

`useInfiniteList` hook shared:

- `useInfiniteQuery`  
- `initialPageParam: 1`  
- `getNextPageParam` az `lastPage.items.length` vs pageSize  
- `placeholderData: keepPreviousData`  

`useInfinitePersonnels` wrap mikone ba `personnelKeys.infinite`.

**Farz kon:** autocomplete / infinite scroll dropdown — na faqat MRT page.

---

## Qesmat 10 — Mutation invalidate pattern

| action | invalidate |
|---|---|
| create | `lists()` |
| update | `lists()` + `detail(id)` |
| delete | `lists()` |

**Optimistic update?** kam; bishtar invalidate-refetch. Honesty.  
Smell: ba'zi service-ha `invalidateQueries({ queryKey: '' })` — too broad / bug.

---

## Qesmat 11 — Query vs Axios responsibility split

| concern | owner |
|---|---|
| 401 refresh | Axios interceptor |
| 403 toast | Axios interceptor |
| X-Site-Id | Axios interceptor |
| Dedupe parallel GET same key | Query |
| Refetch on window focus | Query defaults |
| Form submit create | Mutation → http → invalidate |
| Error message parse | `extractErrorMessage` / getErrorMessage |

**Chera refresh to Axios na Query?** hame HTTP (SWR leftovers, one-off getters) benefit; yek ja.

---

## Qesmat 12 — Digar call-site-ha

- Direct `useQuery` to section (unit-approvers) — exception  
- Report axios instance joda momken (Day 39 ticket)  
- SignalR updates — invalidate dasti (Day 50)

---

# BAKHSH-E CHAHAROM: farz kon / senario

## Se dastan

**1) Open staff list**  
Mount → `useGetPersonnels` → miss cache → http GET → Axios + Bearer + site → data → render MRT.

**2) Change filter**  
New queryKey (params object) → fetch; `placeholderData` previous → kam flicker.

**3) Create personnel success**  
Mutation → POST → `invalidateQueries(lists)` → active list refetch → row jadid.

**4) Access expired mid-list**  
GET 401 → interceptor refresh once → retry → Query success (user maybe na mibine).

---

## Smell-ha

1. `staleTime` default 0 — refetch ziad; momken tune per-query  
2. Broad invalidate `queryKey: ''` in some files  
3. `console.error` to every http catch — noisy  
4. Mixed SWR (access-control) vs Query (dejban)  
5. endpoints object mega-file — merge conflict magnet  
6. Axios import name `axiosInstance` vs export `apiClient` — confusing onboarding  
7. Digit normalize global — surprising if intentional Persian digit field  

---

## Debug checklist

| symptom | check |
|---|---|
| Infinite refresh loop | interceptor exclude refresh URL; Query retry |
| Wrong site data | Zustand site ids / header |
| List not updating after save | forgot invalidate / wrong key prefix |
| 401 → login bounce | refresh cookie / CORS credentials |
| Duplicate requests | different queryKey object identity |
| Empty baseURL | NEXT_PUBLIC_SERVER_URL |
| 403 toast spam | interceptor + permission |

---

## 25 soal-e mosahebe

1. Axios vs Query roles?  
2. queryKey chie?  
3. invalidateQueries chera?  
4. gcTime vs staleTime?  
5. withCredentials chera?  
6. Single-flight refresh?  
7. X-Site-Id koja set?  
8. *.http vs *.service?  
9. keys factory pattern?  
10. placeholderData chera?  
11. enabled: !!id?  
12. useInfiniteQuery pageParam?  
13. Chera na useEffect fetch?  
14. SWR vs Query in this monorepo?  
15. Default export apiClient alias?  
16. 403 handling?  
17. Mutation onSuccess?  
18. tokenStorage vs cookie?  
19. Digit normalization?  
20. QueryClientProvider koja?  
21. How avoid cache sharing wrong user after logout? (clear queries?)  
22. retry on 404?  
23. fetcher helper for what?  
24. Optimistic updates — do we?  
25. Day 44 vs 51?

---

## Senario-ha

**S1:** Two components same `personnelKeys.list(p)` → one network request (dedupe).  
**S2:** Logout — ideally `queryClient.clear()` (check auth flow; smell if leftover).  
**S3:** Site switch → keys maybe same params but header changed → need invalidate on site change (Zustand subscribe / effect).  
**S4:** Upload FormData — interceptor digit normalize strings only.  
**S5:** Public ticket URLs skip 401 refresh redirect logic.

---

## Mini lab

1. Trace staff list: view → service → http → apiClient  
2. React Query Devtools? (if not installed — note gap)  
3. Create mutation — Network: POST then GET list  
4. Force 401 (expire token) — see single refresh  
5. Change site — see X-Site-Id header  

---

## Resume (1 paragraph)

> Implemented client data layer with **Axios** (shared `@repo/api-client`: Bearer, multi-site headers, cookie refresh single-flight) and **TanStack Query v5** hooks (`*.http.js` + `*.keys.js` + `*.service.js`) for cached lists/details, infinite queries, and invalidate-on-mutation.

Keywords: `TanStack Query` · `React Query` · `Axios` · `interceptors` · `queryKey` · `invalidateQueries` · `apiClient` · `withCredentials`

---

## File-haye mohem

| path | chera |
|---|---|
| `packages/api-client/src/axiosInstance.ts` | createApiClient + interceptors |
| `packages/api-client/src/tokenStorage.ts` | access LS |
| `packages/ui/.../client-provider.jsx` | QueryClientProvider |
| `apps/dejban/src/lib/api.js` | endpoints + default apiClient |
| `services/**/**.http.js` | HTTP |
| `services/**/**.keys.js` | keys |
| `services/**/**.service.js` | hooks |
| `hooks/infinite-list/use-infinite-list.js` | infinite helper |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 16 | X-Site-Id tenancy |
| 40 | auth refresh e2e |
| 42 | ClientProvider in layout |
| 43 | `@repo/api-client` package |
| **44** | this |
| 45 | forms submit → mutations |
| 46 | Zustand site store (header source) |
| 51 | FE folder patterns |
| 53 | SWR contrast |

---

## Chejori digest koni

1. Telephone vs yakhchal  
2. Bekhun axios interceptors  
3. Yek feature: keys + http + service  
4. Mutation invalidate  
5. Resume seda  

---

## Glossary

| term | ma'ni |
|---|---|
| server state | data az API (vs UI state) |
| queryKey | cache identity array |
| queryFn | async fetch |
| mutation | write operation |
| invalidate | mark stale → refetch active |
| gcTime | unused cache lifetime |
| staleTime | fresh duration |
| single-flight | yek in-flight shared promise |
| interceptor | Axios middleware |

---

## Deep dive — object identity in queryKey

`list({ page: 1 })` vs new object each render — **same contents** OK agar stable serialize; React Query hash keys.  

Amma `filters` object reorder / undefined vs missing → extra cache entries.  
Normalize params ghabl az key.

---

## Deep dive — logout cache

Ba'd az `tokenStorage.clear`, Query cache momken user ghabli neshan dahad momentary.  
Best: `queryClient.clear()` to AuthProvider logout.  
Lab: verify — honesty agar missing = smell.

---

## Deep dive — site change

Header avaz mishe; queryKey shayad site id **nadarad**.  
Risk: show site A cache under site B header refetch.  
Fix options: include siteIds in key; ya invalidate all on site change.

Interview: «I'd put tenant id in the query key or invalidate on site switch.»

---

## Anti-pattern

| bad | better |
|---|---|
| useEffect + setState fetch | useQuery |
| mutate bedun invalidate | onSuccess invalidate |
| put hooks in *.http.js | keep pure |
| string queryKey random | keys factory |
| catch swallow error in http | throw for Query |
| duplicate axios.create per feature | shared apiClient |

---

## Interview 60s

«We use a shared Axios client with credentials, Bearer access token, X-Site-Id, and a single-flight refresh on 401. TanStack Query wraps reads and writes: query key factories, service hooks, and invalidate lists/details after mutations. HTTP stays in `*.http.js`; React stays in `*.service.js`.»

---

## Quick self-test

1. Package axios? → `@repo/api-client`  
2. Provider? → ClientProvider / QueryClientProvider  
3. gcTime default app? → 5 min  
4. Refresh URL Bearer? → no  
5. keys file? → `*.keys.js`  
6. Infinite helper? → `useInfiniteList`  
7. SWR where? → access-control (Day 53)  

---

## Final checklist

- [ ] Axios interceptors map  
- [ ] Query provider  
- [ ] http / keys / service split  
- [ ] invalidate rules  
- [ ] infinite  
- [ ] smells (site key, logout clear)  
- [ ] resume  

---

## Extra — Farz kon dual tab

Tab A mutate; Tab B stale until focus refetch (default).  
BroadcastChannel invalidate = advanced — na default Dejban.

---

## Extra — Error shape

Backend ErrorOr/ProblemDetails → `extractErrorMessage` Persian prefer.  
Query `error` object = Axios error; UI `error.response?.data`.

---

## Extra — loading flags v5

`isLoading` = no data yet + fetching.  
`isFetching` = any fetch.  
`isPending` mutation.  
MRT: skeleton vs bar — pick right flag.

---

## Extra — prefetch

`queryClient.prefetchQuery` on hover link — optional UX; kam estefade.  
WORLD tool available.

---

## Extra — Comparison React Query vs Redux for server state

Redux possible but boilerplate.  
Query specialized server state; Zustand UI/site (Day 46).  
Dejban split: Query server, Zustand client prefs/site.

---

## Extra — Soalat chera

**Chera withCredentials?** refresh cookie.  
**Chera Bearer na faqat cookie access?** SPA + multi-service (Day 40).  
**Chera keys file?** invalidate precision.  
**Chera placeholderData?** filter UX.  
**Chera throw in http?** Query needs rejection.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «Axios is the HTTP client with auth and tenant headers. TanStack Query sits above it: each list/detail has a query key, hooks live in service files, and mutations invalidate those keys so the UI refetches.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Login loop | refresh fail + redirect |
| Wrong tenant rows | site header / key |
| Stale row after edit | no detail invalidate |
| Double refresh | _retry / promise bug |
| CORS cookie | SameSite / Secure |
| Empty list flash | no placeholderData |
| Mutation ok UI old | invalidate wrong prefix |

---

## Extra — Layer checklist

| layer | file |
|---|---|
| Provider | client-provider.jsx |
| Transport | axiosInstance.ts |
| URLs | lib/api.js endpoints |
| HTTP fn | *.http.js |
| Keys | *.keys.js |
| Hooks | *.service.js |
| UI | sections/* |

---

## Extra — Related days jump

- 40 auth  
- 43 package boundary  
- 46 site store  
- 51 patterns  
- 53 SWR  

---

## Extra — Devtools

`@tanstack/react-query-devtools` — check if wired; if not, recommend for lab.  
Honesty: may be absent in prod bundle.

---

## Extra — retry policy

Default Query retries failed queries.  
Detail: custom skip 404.  
Axios refresh handles 401 before Query sees final fail (after retry request).

---

## Extra — GET delete body

`deletePersonnels` uses `axios.delete(url, { data: { ids } })` — body delete.  
Some proxies dislike — backend contract Dejban.

---

## Extra — createItem helpers

Generic helpers exist; many features still explicit *.http for clarity endpoints.  
Both OK.

---

## Band-e gharardad-e jadid

Telephone = Axios (chejori call + auth).  
Yakhchal = Query (che data, key, invalidate).  
Label = keys.js.  
Dast = http.js.  
Dastkesh React = service.js.  
Soket multi-site = X-Site-Id interceptor.  
Kart toolani = cookie refresh.

---

## 10 jomle fluency

1. Axios carries tokens and site headers.  
2. 401 triggers single-flight refresh.  
3. TanStack Query caches server state.  
4. queryKey identifies cache entries.  
5. *.http.js has no hooks.  
6. *.service.js wraps useQuery/useMutation.  
7. Mutations invalidate list keys.  
8. ClientProvider supplies QueryClient.  
9. Infinite lists use useInfiniteQuery helper.  
10. SWR remains in another app — don't confuse.

---

## Extra — Capacity

Query cache memory: gcTime bounds.  
Huge pageSize 9999 list — smell network; prefer server page.  
Deduping saves parallel mounts.

---

## Extra — Testing

Mock apiClient / msw.  
Test keys factory pure.  
Mutation onSuccess invalidate — assert queryClient.invalidate called (unit).  
E2E: create → see row (Playwright Day 55).

---

## Extra — TypeScript

api-client is TS; dejban services often JS.  
Error typing weak — `error?.response?.status` optional chain.

---

## Extra — when NOT to use Query

- Truly fire-and-forget download blob once  
- Ultra-local UI state  
- WebSocket stream primary (SignalR) — maybe sync into cache  

Still often: fetch initial via Query, live patch via SignalR invalidate.

---

## Extra — version note

v4 → v5: `cacheTime` → `gcTime`; `keepPreviousData` import change.  
Code uses v5 APIs (`gcTime`, `initialPageParam`).

---

## Extra — endpoints sprawl mitigation

Future: split endpoints per domain module file; re-export.  
Today: one big `api.js` — know conflict risk.

---

## Band-e gharardad — ye bar digar sade

1. **Axios** = HTTP + auth interceptors.  
2. **Query** = cache + hooks lifecycle.  
3. **endpoints** = URL dictionary.  
4. **http** = async functions.  
5. **keys** = cache addresses.  
6. **service** = React Query hooks.  
7. **invalidate** = ba'd az write.  
8. **ClientProvider** = app-wide client.  
9. **Site header** = Axios az Zustand.  
10. **SWR** = app digar / Day 53.

---

## Extra — Farz kon interview whiteboard

Bekesh 4 box: UI → service → http → axios → network.  
Kenar: QueryClient cloud ba keys.  
Arrow invalidate az mutation be cloud.

---

## Extra — Parallel queries

`useQueries` — chand id; available, kam.  
Usually multiple `useGetXById`.

---

## Extra — select option

`select: (data) => data.items` — transform cache read.  
Optional; sometimes map in UI.

---

## Extra — structural sharing

Query default structural share — referential stability.  
Helps memo children; rare bugs if mutate cached object in place (**don't**).

---

## Extra — abort / cancel

Axios cancel + Query signal v5 — advanced; check if http passes signal.  
Honesty: many http fn ignore abort.

---

## Khoruj-e zehni

> Midunam data-layer FE dejban ba Axios (`apiClient` + interceptor Bearer/site/refresh) va TanStack Query (keys/http/service, invalidate ba'd az mutate, ClientProvider) kar mikone; va SWR ro ba access-control / Day 53 joda midunam.

Age in paragraph mal-e to shod — Day 44 done.

---

*Day 44 tamum. Ba'd: Day 45 — React Hook Form + Zod (amade). Fehrest: [README.md](./README.md).*
