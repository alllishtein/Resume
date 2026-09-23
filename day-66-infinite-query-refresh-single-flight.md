# Day 66 — useInfiniteQuery + refresh single-flight

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Do ta pattern-e mohem-e FE** ke hameja estefade mishan: **`useInfiniteQuery`** baraye list-haye bi-payan (autocomplete, scroll pagination) va **single-flight refresh** to axios interceptor ke vaghti access token expire mishe, faghat **ye** refresh call mizane — na N ta. Refresh token to **httpOnly cookie**-e (XSS-safe), access token to memory/tokenStorage-e (fast access baraye header). Har do in-ha to mosahebe khub miyan chun pattern-haye production-grade-an ke kheili team-ha azashun bi-khabar-an.

---

# BAKHSH-E AVAL: WORLD — infinite query

## Farz kon

Ye autocomplete field dari ke "personnel" search mikone. Page 1 ro migiri (20 ta), user scroll mikone → page 2 → page 3 → ... In "infinite scroll" ya "load more" pattern-e.

## useInfiniteQuery vs useQuery

| | `useQuery` | `useInfiniteQuery` |
|---|---|---|
| **data structure** | single response | `data.pages` — array of page responses |
| **pagination** | manual (page state + refetch) | automatic (`fetchNextPage`) |
| **accumulation** | replace (ya manual merge) | built-in accumulation |
| **typical use** | table ba page buttons (MRT Day 52) | scroll / load-more / autocomplete |
| **query key** | `['personnel', { page, size }]` | `['personnel', 'infinite', params]` |

## Core API

```js
const result = useInfiniteQuery({
    queryKey: ['items', 'infinite', params],
    queryFn: ({ pageParam }) => fetchItems({ page: pageParam, pageSize: 20 }),
    initialPageParam: 1,
    getNextPageParam: (lastPage, allPages) => {
        if (!lastPage?.items?.length) return undefined;       // no data
        if (lastPage.items.length < pageSize) return undefined; // last page
        return allPages.length + 1;                            // next page number
    },
    placeholderData: keepPreviousData,
});
```

**`initialPageParam: 1`** — avvalin page ke fetch mishe.

**`getNextPageParam`** — key function: az last response migire ke page-e ba'di chie. Age `undefined` return kone, `hasNextPage` false mishe va `fetchNextPage` kari nemikone.

**`placeholderData: keepPreviousData`** — vaghti search term avaz mishe, data-ye ghabli neshun dade mishe ta data-ye jadid biad. Bedun-esh, UI flash mikone be loading state.

## Data structure

```js
result.data = {
    pages: [
        { items: [...20 items...], totalCount: 150 },  // page 1
        { items: [...20 items...], totalCount: 150 },  // page 2
        { items: [...15 items...], totalCount: 150 },  // page 3
    ],
    pageParams: [1, 2, 3],
};
```

Baraye render: `result.data.pages.flatMap(p => p.items)` → ye flat list az hame-ye item-ha.

## Cursor-based vs offset-based

| | offset (page number) | cursor (last ID / timestamp) |
|---|---|---|
| **getNextPageParam** | `allPages.length + 1` | `lastPage.cursor` |
| **cons** | skip/shift vaghti data ezafe/hazf she | hich skip/shift nadare |
| **Dejban** | ✅ page-number based | ❌ estefade nashode |

Cursor-based amn-tar-e baraye realtime list-ha (chat, feed). Dejban az page-number estefade mikone chun API-hash pagination-e classic-e.

## hasNextPage / fetchNextPage / isFetchingNextPage

```jsx
<IntersectionObserver onIntersect={() => {
    if (hasNextPage && !isFetchingNextPage) fetchNextPage();
}}>
    <LoadingSpinner />
</IntersectionObserver>
```

Ya sade-tar:

```jsx
{hasNextPage && <Button onClick={() => fetchNextPage()}>Load more</Button>}
{isFetchingNextPage && <CircularProgress />}
```

## refetch vs fetchNextPage

- `refetch()` → hame-ye page-ha ro dobare fetch mikone (az aval)
- `fetchNextPage()` → faghat page-e ba'di ro fetch mikone
- vaghti search term avaz mishe → query key avaz mishe → auto refetch az page 1

---

# WORLD — single-flight refresh

## Farz kon

50 ta API call hamzaman fail mishan ba 401 (token expired). Bedun-e single-flight, 50 ta refresh call hamzaman fire mishan → server 50 bar token refresh mikone → race condition → ba'zi fail mishan → logout-e bi-dalil.

## Pattern

```
Request A → 401  ─┐
Request B → 401  ─┤
Request C → 401  ─┤── share ONE refresh promise ──→ new token
Request D → 401  ─┘                                  │
                                                      ├── retry A with new token
                                                      ├── retry B
                                                      ├── retry C
                                                      └── retry D
```

**Implementation:**

```js
let refreshPromise = null;

interceptor.response.use(null, async (error) => {
    if (error.response?.status === 401 && !config._retry) {
        config._retry = true;
        if (!refreshPromise) {
            refreshPromise = client.post('/auth/refresh')
                .finally(() => { refreshPromise = null; });
        }
        const { data } = await refreshPromise;  // all 401s wait here
        config.headers.Authorization = `Bearer ${data.accessToken}`;
        return client(config);  // retry original request
    }
    return Promise.reject(error);
});
```

**`refreshPromise`** — ye closure-level variable ke **hame-ye interceptor call-ha** share mikonan. Avvalin 401 ke biad, refresh ro trigger mikone; baghie-ha hamun promise ro await mikonan.

## httpOnly cookie — chera baraye refresh token?

| storage | XSS risk | CSRF risk | accessibility |
|---|---|---|---|
| localStorage | ✅ JS mitune bekhune | ❌ | easy |
| memory (variable) | ❌ | ❌ | page refresh = lost |
| httpOnly cookie | ❌ JS nemitune bekhune | ⚠️ mitigated by SameSite | auto-sent |

**Dejban approach:**
- **Refresh token** → httpOnly cookie (auto-sent ba `withCredentials: true`)
- **Access token** → `tokenStorage` (memory wrapper) — baraye Authorization header

**Chera in combo?**
- Access token short-lived-e (minutes) — leak-esh kam-asare
- Refresh token long-lived-e (hours/days) — leak-esh khatarnak-e → httpOnly
- JS hich vaght refresh token ro nemikhune — faghat browser khodesh mifreste

## Thundering herd

Bedun-e single-flight:
1. 50 request 401 migiran
2. 50 ta `/auth/refresh` call hamzaman
3. Server 50 bar token pair mint mikone (ya 49 ta fail mishan chun refresh token yek-bar masraf mishe)
4. Race condition: ba'zi request-ha token-e ghadimi ro migiran, fail mishan
5. User logout mishe bi-dalil

Ba single-flight: **ye** refresh call → **ye** token pair → hame retry mikonan → smooth.

## refreshBlockedUntil — cooldown

```js
const REFRESH_RETRY_AFTER_MS = 5_000;
let refreshBlockedUntil = 0;

// Vaghti refresh fail mikone ba non-auth error (500, network error):
refreshBlockedUntil = Date.now() + REFRESH_RETRY_AFTER_MS;

// Vaghti 401 miad va cooldown active-e:
if (Date.now() < refreshBlockedUntil && !refreshPromise) {
    return Promise.reject(error);  // skip refresh, fail fast
}
```

**Chera?** Age refresh endpoint khodesh down bashe (500), nabayad har saniye retry koni — 5 saniye sabr kon. In az bombardeman kardan-e server-e mariz jelo migire.

## Logout on refresh failure

```js
catch (refreshError) {
    const status = refreshError.response?.status;
    if (status === 401 || status === 403 || status === 404) {
        try { await client.post('/auth/logout'); } catch {}
        finally {
            tokenStorage.clear();
            redirectToSignIn();
        }
    }
    return Promise.reject(refreshError);
}
```

**Logic:** age refresh khodesh 401/403/404 bede, yani session revoke shode ya token na-ma'tebar-e → clean logout → redirect be sign-in.

**404:** chera? Age refresh endpoint ro peyda nakone (misconfigured URL), ham 404 mide — behtar-e logout koni ta ye loop-e bi-enteha besazi.

---

# BAKHSH-E DOVOM: DEJBAN — piade-sazi-e vaghei

## use-infinite-list.js — hook-e kamel

```js
import { useInfiniteQuery, keepPreviousData } from '@tanstack/react-query';

export function useInfiniteList({ queryKey, fetchFn, params = {}, pageSize = 20, enabled = true }) {
  const { enabled: enabledFromParams, ...fetchParams } = params ?? {};
  const isEnabled = enabledFromParams !== undefined ? Boolean(enabledFromParams) : enabled;

  return useInfiniteQuery({
    queryKey: [...queryKey, 'infinite', fetchParams],
    queryFn: ({ pageParam }) =>
      fetchFn({
        page: pageParam,
        pageSize,
        ...fetchParams,
      }),
    initialPageParam: 1,
    enabled: isEnabled,
    placeholderData: keepPreviousData,
    getNextPageParam: (lastPage, pages) => {
      if (!lastPage?.items?.length) return undefined;
      if (lastPage.items.length < pageSize) return undefined;
      return pages.length + 1;
    },
  });
}
```

**Line-by-line:**
- `queryKey: [...queryKey, 'infinite', fetchParams]` — params to query key ezafe mishe → search term avaz beshe, auto-refetch
- `enabled` — mitune az params ya prop biad; `false` = query run nemishe
- `fetchFn` — ye function ke `{ page, pageSize, ...filters }` migire va API call mizane
- `getNextPageParam` — age last page items < pageSize, ta'in mikone ke dge page nadare

**Estefade:**

```js
// services/units/units.service.js
export function useInfiniteUnits(params) {
    return useInfiniteList({
        queryKey: ['units'],
        fetchFn: (p) => apiClient.get('/api/v1/Units', { params: p }).then(r => r.data),
        params,
        pageSize: 20,
    });
}

// Component
const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteUnits({ searchTerm: debouncedSearch });
const allItems = data?.pages?.flatMap(p => p.items) ?? [];
```

## Fargh ba MRT pagination (Day 52)

MRT (Material React Table) az `useQuery` ba manual pagination estefade mikone:

```js
// MRT approach (Day 52)
const { data, isLoading } = useQuery({
    queryKey: ['personnel', pagination, sorting, filters],
    queryFn: () => api.get('/Personnels', { params: { page: pagination.pageIndex + 1, pageSize: pagination.pageSize, ... } }),
});

// data = { items: [...], totalCount: 150 }
// MRT khodesh page button-ha ro neshun mide
```

| | useInfiniteList (Day 66) | MRT useQuery (Day 52) |
|---|---|---|
| **UX** | scroll / load-more | table ba page buttons |
| **data** | accumulated pages | single page |
| **use case** | autocomplete, dropdown | full table |
| **server load** | incremental | per-page |

## axiosInstance.ts — kamel

```ts
export function createApiClient(baseURL?: string) {
  const client = axios.create({
    baseURL,
    withCredentials: true,  // httpOnly refresh cookie auto-sent
  });

  // REQUEST interceptor
  client.interceptors.request.use((config) => {
    config.headers['Accept-Language'] = localStorage.getItem('i18nextLng') || 'fa-IR';

    // Multi-site header from Zustand store
    const siteIds = useSiteStore.getState().getSiteIds();
    if (siteIds.length > 0) config.headers['X-Site-Id'] = siteIds.join(',');

    // Access token (skip for refresh request itself)
    if (config.url !== endpoints.auth.refresh) {
      const accessToken = tokenStorage.getAccess();
      if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
    }

    // Normalize Persian/Arabic digits → English for API params
    if (config.params) config.params = normalizeParams(config.params);
    if (config.data) config.data = normalizeDigitsDeep(config.data);

    return config;
  });

  // RESPONSE interceptor — single-flight refresh
  const REFRESH_RETRY_AFTER_MS = 5_000;
  let refreshPromise = null;
  let refreshBlockedUntil = 0;

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const req = error.config;

      if (
        error.response?.status === 401 &&
        !req._retry &&
        !req.url.includes('/auth/login') &&
        !req.url.includes('/auth/refresh') &&
        !isPublicTicketRequest(req.url)
      ) {
        req._retry = true;

        // Cooldown active?
        if (Date.now() < refreshBlockedUntil && !refreshPromise)
          return Promise.reject(error);

        // Single-flight: only first 401 triggers refresh
        if (!refreshPromise) {
          refreshPromise = client.post(endpoints.auth.refresh)
            .then(res  => { refreshBlockedUntil = 0; return res; })
            .catch(err => {
              const s = err.response?.status;
              refreshBlockedUntil = (s === 401 || s === 403 || s === 404)
                ? 0
                : Date.now() + REFRESH_RETRY_AFTER_MS;
              throw err;
            })
            .finally(() => { refreshPromise = null; });
        }

        try {
          const { data, status } = await refreshPromise;
          if (status === 200 && data?.accessToken) {
            tokenStorage.setAccess(data.accessToken);
            req.headers.Authorization = `Bearer ${data.accessToken}`;
            return await client(req);  // retry
          }
          return Promise.reject(error);
        } catch (refreshError) {
          const s = refreshError.response?.status;
          if (s === 401 || s === 403 || s === 404) {
            try { await client.post(endpoints.auth.logout); } catch {}
            finally { tokenStorage.clear(); redirectToSignIn(); }
          }
          return Promise.reject(refreshError);
        }
      }

      if (error.response?.status === 403 && !isPublicTicketRequest(req?.url))
        toast.error('شما دسترسی لازم را ندارید.');

      return Promise.reject(error);
    }
  );

  return client;
}

export const apiClient = createApiClient(resolveBaseUrl());
```

## isPublicTicketRequest — bypass

```js
const isPublicTicketRequest = (url = '') =>
  /Tickets\/(GetPublicTicketUnits|CreatePublicTicket|GetPublicTicket|AddPublicTicketMessage)/i.test(url);
```

Public ticket endpoint-ha (Day 50) authentication nadarand — pas 401-eshun nabayad refresh trigger kone. Bedun-e in check, ye unauthenticated public request momkene refresh loop besaze.

## tokenStorage — memory wrapper

```js
// tokenStorage.ts (simplified)
let accessToken = '';
export const tokenStorage = {
    getAccess: () => accessToken,
    setAccess: (t) => { accessToken = t; },
    clear: () => { accessToken = ''; },
};
```

Access token to **memory** negah dashte mishe — XSS nemitune az localStorage bekhune-sh. Vali **page refresh** = token gom mishe → avvalin request 401 mide → refresh trigger mishe → dobare token migire. In by-design-e.

## Persian digit normalization

```js
config.params = Object.fromEntries(
    Object.entries(config.params).map(([key, value]) => [
        key,
        typeof value === 'string' ? toEnglishDigits(value) : value,
    ])
);
```

User "۱۳۹۹" type mikone → API "1399" migire. Bedun-e in, server side filter/search fail mikone chun Unicode-e digit-ha farghe.

---

## Smell-ha

1. **refreshBlockedUntil module-scope** — age do ta `createApiClient` seda bezani, har kodum variable-e khodesh dare → isolation OK; vali singleton `apiClient` export mishe
2. **No refresh token rotation detection** — age server refresh token ro rotate kone (new cookie), client nemidune; feli server rotate nemikone
3. **Page-number pagination** — skip/shift vaghti item ezafe/hazf she; cursor-based amn-tar-e
4. **keepPreviousData** — old data neshun dade mishe vaghti search avaz mishe; user momkene confuse she
5. **No retry limit** — age refresh success bede vali retry baz 401 bede (race), infinite loop momkene (protected by `_retry` flag vali...)
6. **localStorage baraye i18n** — XSS mitune language preference ro avaz kone; kam-risk vali exist dare
7. **`flatMap` ru-ye pages** — baraye list-haye bozorg memory-intensive-e
8. **SiteId az Zustand to interceptor** — tight coupling; mock kardan-esh sakht-e to test

---

## Debug checklist

1. Infinite list data neshun nemide? → `enabled` false-e? `fetchFn` error dare?
2. Load more kaar nemikone? → `hasNextPage` false-e? `getNextPageParam` undefined return karde?
3. Duplicate item-ha? → page-number shift; server data avaz shode beyn-e fetch-ha
4. Refresh loop? → refresh endpoint khodesh 401 mide? `isPublicTicketRequest` match mikone?
5. Logout-e bi-dalil? → refresh fail ba 401/403/404 → check server-side session
6. 50 refresh call hamzaman? → `refreshPromise` share nemishe? do ta axios instance dari?
7. Access token ba'd az refresh nadare? → `tokenStorage.setAccess` seda zade? `data.accessToken` hast?
8. Persian digits to server search fail? → `toEnglishDigits` dorost kar mikone? config.data normalize shode?
9. Cookie na mirese? → `withCredentials: true` hast? Same origin? `SameSite` attribute?

---

## 25 soal-e mosahebe

1. useInfiniteQuery chie? — **A:** TanStack hook baraye paginated data ke page-ha accumulate mishan.
2. getNextPageParam chikar mikone? — **A:** az last response ta'in mikone next page chie; undefined = no more pages.
3. initialPageParam chie? — **A:** avvalin page ke fetch mishe (1-based to Dejban).
4. Fargh-e useInfiniteQuery va useQuery? — **A:** infinite accumulate mikone; useQuery single response dare.
5. keepPreviousData chie? — **A:** vaghti query key avaz mishe, old data neshun mide ta new biad.
6. Single-flight refresh chie? — **A:** faghat ye refresh call baraye hame-ye 401-ha; baghie share mikonan.
7. Chera httpOnly baraye refresh? — **A:** XSS nemitune JS-e az cookie bekhune.
8. withCredentials chikar mikone? — **A:** browser httpOnly cookie ro auto attach mikone be cross-origin request.
9. refreshBlockedUntil chie? — **A:** 5s cooldown ba'd az refresh fail (non-auth error) — prevent bombardment.
10. Key vaght logout mishe? — **A:** refresh 401/403/404 bede.
11. Race condition-e do tab? — **A:** har tab instance-e khodesh dare; har kodum joda refresh mikone (smell).
12. Thundering herd chie? — **A:** N client hamzaman resource request mikonan → server overload.
13. tokenStorage chie? — **A:** in-memory wrapper baraye access token; page refresh = lost (by design).
14. _retry flag chie? — **A:** prevent infinite retry loop; ye request faghat ye bar retry mishe.
15. isPublicTicketRequest chie? — **A:** bypass refresh baraye unauthenticated endpoints.
16. Persian digit normalization chera? — **A:** backend filter ba English digits kar mikone.
17. Cursor-based pagination chie? — **A:** next page az last item's ID/timestamp ta'in mishe; no skip/shift.
18. flatMap ru-ye pages chie? — **A:** hame-ye page items ro flat mikone baraye render.
19. SiteId az koja miad? — **A:** Zustand store to interceptor mikhune → `X-Site-Id` header.
20. fetchNextPage vs refetch? — **A:** fetchNextPage = next page; refetch = all pages from start.
21. Age refresh token expire she? — **A:** refresh 401 mide → logout.
22. localStorage vs memory baraye access token? — **A:** memory amn-tar-e (XSS-safe); localStorage persistent-e.
23. isFetchingNextPage chie? — **A:** loading state faghat baraye next page (na initial load).
24. queryKey chetori impact dare? — **A:** change = auto-refetch; params to key → search term change = new query.
25. `finally(() => refreshPromise = null)` chera? — **A:** cleanup — next 401 ye refresh-e jadid trigger kone.

---

## Senario-ha

### A) User to autocomplete type mikone
"ali" type mishe → `queryKey: ['personnel', 'infinite', { searchTerm: 'ali' }]` → page 1 fetch mishe → 20 result → user scroll mikone → `fetchNextPage()` → page 2 → ...

### B) Token expire mishe — 50 request hamzaman
Dashboard load mishe → 50 API call → hame 401 migiran → first one triggers refresh → 49 ta await `refreshPromise` → refresh success → new token → all 50 retry → success.

### C) Refresh token revoke shode (admin session ro kill karde)
Request → 401 → refresh call → server 401 bede (refresh token revoked) → client logout → redirect to sign-in → user bayad dobare login kone.

### D) Server-e auth down-e
Request → 401 → refresh → 500 → `refreshBlockedUntil = Date.now() + 5000` → next 401 in 5s: skip refresh, fail fast → 5s ba'd: try again.

### E) Public ticket 401
Unauthenticated user creates public ticket → server 401 mide (bug) → `isPublicTicketRequest` match mikone → refresh skip mishe → error propagate mishe → FE error neshun mide (na logout).

---

## Anti-pattern-ha

```js
// BAD: har 401 refresh seda mizane
if (status === 401) {
    const res = await client.post('/auth/refresh');  // N parallel calls!
}

// GOOD: single-flight
if (!refreshPromise) {
    refreshPromise = client.post('/auth/refresh').finally(() => refreshPromise = null);
}
await refreshPromise;
```

```js
// BAD: refresh token to localStorage
localStorage.setItem('refreshToken', token);  // XSS readable!

// GOOD: httpOnly cookie — JS nemitune bekhune
// server Set-Cookie: refresh=...; HttpOnly; Secure; SameSite=Lax
```

```js
// BAD: infinite query bedun-e end condition
getNextPageParam: (lastPage, pages) => pages.length + 1  // infinite loop!

// GOOD: check for empty/partial page
getNextPageParam: (lastPage, pages) => {
    if (lastPage.items.length < pageSize) return undefined;
    return pages.length + 1;
}
```

```js
// BAD: useQuery ba manual page accumulation
const [allItems, setAllItems] = useState([]);
const { data } = useQuery({ queryKey: ['items', page] });
useEffect(() => { setAllItems(prev => [...prev, ...data.items]); }, [data]);

// GOOD: useInfiniteQuery handles accumulation
```

---

## Interview 60s

> «For paginated pickers we wrap useInfiniteQuery in a useInfiniteList hook — it accumulates pages, uses keepPreviousData for smooth UX, and getNextPageParam decides when to stop based on page size. On the network layer, our axios interceptor implements single-flight refresh: the first 401 triggers a cookie-based refresh call and all concurrent 401s share that promise, preventing a thundering-herd of refresh requests. The refresh token lives in an httpOnly cookie so JavaScript can't read it.»

---

## Resume

**kutah:**

> Implemented **useInfiniteQuery**-based paginated pickers and **single-flight axios refresh** with **httpOnly** refresh cookies, preventing thundering-herd 401 storms across concurrent API calls.

**bullet-ha:**

- Built `useInfiniteList` hook wrapping TanStack `useInfiniteQuery` with page-number params, `keepPreviousData`, and auto-stop via `getNextPageParam`
- Designed single-flight axios interceptor sharing one refresh promise across all concurrent 401 responses
- Secured refresh token in httpOnly cookie (`withCredentials`) while keeping access token in memory
- Added 5-second cooldown (`refreshBlockedUntil`) to prevent refresh bombardment on server errors

**skill-ha:** `TanStack Query · useInfiniteQuery · axios interceptors · token refresh · httpOnly cookies · single-flight · XSS mitigation · React hooks`

---

## File-haye mohem

| chi | koja |
|---|---|
| useInfiniteList hook | `apps/dejban/src/hooks/infinite-list/use-infinite-list.js` |
| axiosInstance | `packages/api-client/src/axiosInstance.ts` |
| tokenStorage | `packages/api-client/src/tokenStorage.ts` |
| service example | `apps/dejban/src/services/units/units.service.js` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 40 Auth e2e | refresh flow, cookie setup |
| 44 TanStack Query | useQuery basics, queryKey, staleTime |
| 46 Zustand | useSiteStore to interceptor |
| 48 i18n | Accept-Language header, digit normalization |
| 50 SignalR FE | access token for WS |
| 52 MRT | useQuery + manual pagination |

---

## Glossary

| kalame | ma'ni |
|---|---|
| useInfiniteQuery | TanStack hook baraye paginated data accumulation |
| getNextPageParam | function ke next page cursor/number ro return mikone |
| keepPreviousData | old data neshun mide ta new query resolve she |
| single-flight | faghat ye in-flight request; baghie share mikonan |
| refreshPromise | shared promise ke hame-ye 401-ha await mikonan |
| thundering herd | N client hamzaman resource request mikonan |
| httpOnly cookie | cookie ke JS nemitune bekhune (document.cookie) |
| withCredentials | axios config ke cookie ro attach mikone |
| _retry | flag ru-ye request config ke jelo-ye infinite loop ro migire |
| tokenStorage | in-memory access token wrapper |
| cooldown | modat-e sabr ba'd az failure ghabl az retry |
| capability ticket | Day 64; bypass baraye public ticket-ha |

---

## Deep dive — multi-tab refresh race

Do ta tab baz-e → har kodum axios instance-e khodesh dare → har kodum joda refresh mikone. Agar server refresh token rotation dashte bashe (ye bar masraf), avvalin tab success migire, dovomi fail mikone → logout.

**Raah-hal-ha:**
1. `BroadcastChannel` API: vaghti ye tab token jadid migire, be baghie broadcast mikone
2. Server rotation nandashte bashe (Dejban feli nandare)
3. `localStorage` event listener: vaghti token avaz she, dge tab-ha listen mikonan

Dejban feli na rotation dare na BroadcastChannel — multi-tab masale-i nist. Vali age rotation ezafe she, bayad ye mekaanism-e cross-tab piade she.

---

## Deep dive — page accumulation va memory

`useInfiniteQuery` hame-ye page-ha ro to memory negah midare. Age 100 page × 20 item fetch koni, 2000 object to memory-e. Baraye autocomplete ke user search mikone va query key avaz mishe, page-haye ghabli GC mishan. Vali baraye infinite feed (social media style), momkene memory issue beshe.

**TanStack `maxPages` option:** mituni limit bezari ke max N page negah dare va ghadimi-ha drop beshan. Dejban feli estefade nemikone chun autocomplete-ha kam page darand.

---

## Self-test-e sari

1. useInfiniteList pageSize default? → 20
2. getNextPageParam key return undefined? → items < pageSize ya empty
3. refreshPromise az chi type-e? → `Promise<AxiosResponse> | null`
4. httpOnly cookie JS mitune bekhune? → Na
5. refreshBlockedUntil chand millisecond? → 5000
6. Logout key vaght? → refresh 401/403/404
7. _retry chikar mikone? → prevent infinite retry
8. keepPreviousData chie? → old data visible during refetch
9. withCredentials chie? → cookie auto-attach
10. isPublicTicketRequest chera? → bypass refresh for unauth endpoints

Age 8/10 ya bishtar dorost bud → beri sar-e Day 67.

---

## Chejori digest koni

1. useInfiniteQuery concept + getNextPageParam (10 daghighe)
2. useInfiniteList hook-e Dejban (10 daghighe)
3. Single-flight refresh pattern (15 daghighe)
4. axiosInstance interceptor code (15 daghighe)
5. httpOnly cookie + tokenStorage tradeoff (10 daghighe)
6. 25 soal (20 daghighe)

---

## Resume keywords (ATS)

`TanStack Query` · `useInfiniteQuery` · `axios` · `interceptors` · `token refresh` · `httpOnly` · `single-flight` · `React` · `pagination` · `XSS` · `cookie-based auth`

---

## Checklist-e nahaei

- [ ] useInfiniteQuery vs useQuery
- [ ] useInfiniteList hook code
- [ ] getNextPageParam logic
- [ ] Single-flight refresh pattern
- [ ] axiosInstance interceptor (full flow)
- [ ] httpOnly cookie vs localStorage
- [ ] refreshBlockedUntil cooldown
- [ ] Logout on refresh failure
- [ ] Smell-ha (multi-tab, page-number pagination, memory)
- [ ] Resume + interview 60s

---

## Extra — testing interceptor logic

Unit test-e interceptor sakht-e chun closure state dare. Strategy:

```js
// 1. Mock axios adapter (nock / msw)
// 2. Trigger two 401 responses simultaneously
// 3. Assert only ONE /auth/refresh call made
// 4. Assert both original requests retried

import nock from 'nock';
const scope = nock('http://api')
    .get('/a').reply(401)
    .get('/b').reply(401)
    .post('/auth/refresh').reply(200, { accessToken: 'new' })
    .get('/a').reply(200, { ok: true })
    .get('/b').reply(200, { ok: true });

const [resA, resB] = await Promise.all([
    apiClient.get('/a'),
    apiClient.get('/b'),
]);
// Both succeed after shared refresh
```

**Key assertion:** `/auth/refresh` faghat **ye bar** call shode. Age do bar call shode bashe, single-flight kaar nemikone.

---

## Extra — SWR vs TanStack infinite query

| | TanStack `useInfiniteQuery` | SWR `useSWRInfinite` |
|---|---|---|
| data shape | `data.pages` | `data[0], data[1], ...` |
| next page | `getNextPageParam` | `getKey(pageIndex, prevData)` |
| mutation | `useMutation` | `mutate` |
| Dejban | ✅ | Day 53 mentioned; not used for infinite |

SWR-e `useSWRInfinite` ham hamun concept-e — vali TanStack-e approach explicit-tar-e va `keepPreviousData` built-in dare.

---

## Extra — access token rotation vs fixed

Dejban access token-e jadid ro az refresh response migire:

```js
if (data?.accessToken) {
    tokenStorage.setAccess(data.accessToken);
}
```

Har refresh ye **access token-e jadid** mide. Vali refresh token khodesh avaz nemishe (no rotation). Age refresh token rotation bud:

```
Refresh → server returns new access + new refresh (in Set-Cookie)
→ old refresh invalidated
→ concurrent tabs = only first succeeds, second fails
```

Baraye hamin Dejban refresh rotation **nadare** — multi-tab safe-tar-e.

---

## Extra — error toast baraye 403

```js
if (error.response?.status === 403 && !isPublicTicketRequest(req?.url))
    toast.error('شما دسترسی لازم را ندارید.');
```

**403** (Forbidden) — user authenticated-e vali permission nadare. Ye global toast neshun mide. In user-friendly-e vali smell-esh in-e ke **hame-ye 403-ha** hamun toast ro migirani — bazi momkene context-e khasi dashte bashan. Ideally, component-e seda-zade khodesh error ro handle kone.

---

## Extra — `resolveBaseUrl` va environment detection

```js
function resolveBaseUrl(): string {
    if (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_SERVER_URL)
        return process.env.NEXT_PUBLIC_SERVER_URL;
    try {
        const viteUrl = import.meta.env.VITE_SERVER_URL;
        if (typeof viteUrl === 'string') return viteUrl;
    } catch {}
    return '';
}
```

In function **cross-framework**-e — ham Next.js ham Vite ro support mikone. `process.env.NEXT_PUBLIC_*` baraye Next.js, `import.meta.env.VITE_*` baraye Vite. `@repo/api-client` ye shared package-e — hame-ye app-ha (Next.js + Vite) azash estefade mikonan.

---

## Extra — stale closure trap to interceptor

Axios interceptor vaghti attach mishe, closure reference migire be `tokenStorage`, `refreshPromise`, etc. Age in variable-ha avaz beshan (masalan hot reload to dev), interceptor hanuz reference-e ghadimi ro dare. **In to dev kharab nemishe** chun `refreshPromise` va `refreshBlockedUntil` module-scope-an va hot reload module ro reload mikone. Vali age kasi khodesh interceptor dynamic attach kone, in ye trap-e.

---

## Extra — sequence diagram — complete refresh flow

```
Tab A                          Server                     Tab A (retry)
│  GET /api/staff  ───────────▶│                          │
│  ◄── 401                     │                          │
│  POST /auth/refresh ────────▶│                          │
│  (cookie sent automatically)  │                          │
│  ◄── 200 { accessToken }    │                          │
│  tokenStorage.setAccess(t)   │                          │
│  GET /api/staff (Bearer t) ──▶│──── 200 data ──────────▶│
│                               │                          │
│ (concurrent)                  │                          │
│  GET /api/units ─────────────▶│                          │
│  ◄── 401                     │                          │
│  await refreshPromise (same) │                          │
│  GET /api/units (Bearer t) ──▶│──── 200 data ──────────▶│
```

---

*Day 66 tamum. Ba'di: Day 67 — MapLibre + TipTap + Charts + jsPDF. Fehrest: [README.md](./README.md).*
