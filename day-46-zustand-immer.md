# Day 46 — Zustand + immer

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** state-i ke *na* form-e (Day 45) va *na* cache-e server (Day 44) — mesalan **site-e entekhabi**, **workspace tabs**, UI flags — koja zendegi mikone?

**Javab Dejban:** **Zustand** (store kuchek, bedun Provider hell). Ba'zi store-ha **`zustand/middleware/immer`** baraye update.

| store (mohem) | koja | immer? | naqsh |
|---|---|---|---|
| `useSiteStore` | `@repo/ui` `site-storage.js` | **na** | selected site → LS + `X-Site-Id` (Axios) |
| `useWorkspaceTabsStore` | `apps/dejban/.../workspace-tabs-store.js` | **na** | multi-tab keep-alive UI |
| `useUnitsStore` / positions / employment | `apps/dejban/src/stores/*` | **bale** | **legacy-ish** API+loading to store |
| access-control `*-store.js` | `apps/access-control/src/stores` | mixed | UI actions + ba'zi fetch |

**Band-e gharardad-e jadid + honesty:**

> Ideal: **Zustand = client/UI state**. **TanStack Query = server state**.  
> Reality: chand store-e ghadimi hanooz list/CRUD ra to Zustand negah midarand (parallel ba Query pattern). Resume inflated «hame data Zustand» = dorugh.

Day 44/45 = server/form. **In ruz = global client store + immer middleware.**

---

# BAKHSH-E AVAL: WORLD — Zustand chie?

## Farz kon — yek jabe roye miz (na Redux warehouse)

Redux/Context: Provider tree, boilerplate, ya re-render pahn.  
**Zustand:** `create((set, get) => ({ ... }))` → hook `useStore()` — har component subscribe.

```js
const useBearStore = create((set) => ({
  bears: 0,
  increase: () => set((s) => ({ bears: s.bears + 1 })),
}));
// UI: const bears = useBearStore((s) => s.bears);
```

**Yani chi?** Global state sade; `getState()` birun az React (Axios interceptor!).

---

## Chera Zustand (na Redux Toolkit)?

| | Zustand | Redux |
|---|---|---|
| boilerplate | kam | bishtar |
| outside React | `getState()` easy | store export |
| learning | 30min | 1–2 ruz |
| Dejban fit | site + tabs + small stores | overkill |

---

## immer chie? (WORLD)

Immer = «draft mutate kon, immutable produce mishe».

```js
set((state) => {
  state.tabs.push(tab); // ba immer middleware OK
});
```

Bedun immer: bayad copy spread (`[...tabs, tab]`).

**Zustand middleware:** `import { immer } from 'zustand/middleware/immer'`  
`create()(immer((set) => ({ ... })))`

**Honesty Dejban:** chand store immer daran amma bishtar `set(() => ({ items: ... }))` immutable-style — fayde immer kam estefade shode; draft mutation pattern kam didi.

---

## Client state vs server state (mohem mosahebe)

| | client (Zustand) | server (Query) |
|---|---|---|
| source of truth | browser UI | backend DB |
| mesal | selectedSiteId, open tabs, sidebar | personnels list |
| persist | optional LS | cache gcTime |
| invalidate | n/a | ba'd az mutate |

**Anti-pattern:** fetch list → `set({ items })` to Zustand *va* hamin data Query — do source.

---

# BAKHSH-E DOVOM: DEJBAN — `useSiteStore` (ghalb)

## Qesmat 1 — file

`packages/ui/src/auth/utils/site-storage.js`

```js
const SITE_KEY = 'selectedSiteId';

useSiteStore = create((set, get) => ({
  selectedSiteIds: readStoredSiteIds(),
  setSiteIds(siteIds) { /* normalize → LS → set */ },
  removeSiteIds() { /* clear LS + state */ },
  getSiteIds() { /* state ya fallback LS */ },
}));

export const siteStorage = { get, set, remove }; // facade getState()
```

**normalizeSiteIds:** `slice(0, 1)` — **alan max yek site** (array shape for future multi).

---

## Qesmat 2 — cherа in store critical-e?

Axios (`@repo/api-client`):

```ts
useSiteStore.getState().getSiteIds()
→ headers['X-Site-Id'] = ids.join(',')
```

**Farz kon:** user site picker avaz → store + LS → har request ba'di tenant right (Day 16/40/44).  
**Birun React:** interceptor React hook nist — `getState()` zarrin.

Dashboard layout: `useSiteStore()` + `setSiteIds` on select.

`useUserSites` / `ComponentGuard`: subscribe `selectedSiteIds` baraye scope UI.

---

## Qesmat 3 — persist dasti (na middleware persist)

Inja **dasti** `localStorage.setItem(SITE_KEY, ids[0])` — na `zustand/middleware/persist`.

**Chera?** sade; key single string.  
**Alternative WORLD:** `persist` middleware — Dejban site store nah.

SSR note: `typeof window === 'undefined'` → `[]` — Next root safe.

---

## Qesmat 4 — selector pattern

```js
useSiteStore((state) => state.selectedSiteIds)  // narrow subscribe
// vs
useSiteStore()  // whole store — more rerenders
```

Guards use selector — good.  
Layout sometimes destructure whole — OK for small store.

---

# BAKHSH-E SEVOM: workspace tabs

## Qesmat 5 — `useWorkspaceTabsStore`

Client-only UI:

- `tabs[]`, `activeTabId`  
- `openTab` / `activateTab` / `closeTab` / `closeOtherTabs` / `closeAllTabs`  
- `setTabDirty`  
- `MAX_WORKSPACE_TABS = 8` + eviction oldest  

Updates: **immutable spreads** — no immer.  
Perfect Zustand use-case (na server).

**Farz kon:** setting `workspaceTabs` on → Dashboard hosts tabs (Day 42). Store = memory of open pages.

---

# BAKHSH-E CHAHAROM: immer stores (legacy fetch)

## Qesmat 6 — pattern `useUnitsStore`

```js
export const useUnitsStore = create()(
  immer((set) => ({
    allUnitsByPagination: [],
    loading: { ... },
    error: { ... },
    getUnitsWithPagination: async (...) => {
      set((state) => ({ loading: { ...state.loading, fetch: true } }));
      const response = await fetcher([...]);
      set(() => ({ allUnitsByPagination: response.items, totalCount }));
      ...
    },
    createUnits / updateUnits / deleteUnit ...
  }))
);
```

Hamoon olgu: positions, employment-type.

**Yani chi?** Zustand = mini Redux async thunk + list cache.  
**Conflict:** Day 44 `*.service.js` Query hamin domain-ha.  

**Interview honesty:** «Some older screens still use Zustand stores that call the API; newer code prefers TanStack Query. Immer is wrapped but updates are often written as immutable object returns.»

---

## Qesmat 7 — immer misuse smell

Ba immer, idiomatic:

```js
set((state) => {
  state.loading.fetch = true; // mutate draft
});
```

Dejban bishtar:

```js
set((state) => ({
  loading: { ...state.loading, fetch: true },
}));
```

Hala worked (immer accepts return replace). Fayde draft kam.  
**Lab:** yek update ra draft-style neveshtan.

---

## Qesmat 8 — access-control stores

Mix: action stores (open dialog flags) + immer device-user/calendar fetch stores.  
Same lesson: UI flags = good Zustand; server lists → migrate Query.

---

# BAKHSH-E PANJOM: API surface

## Qesmat 9 — `set` / `get` / `getState`

| API | koja |
|---|---|
| `set(partial)` / `set(fn)` | update |
| `get()` | dakhel store actions |
| `useStore.getState()` | Axios, non-React |
| `useStore.subscribe` | rare advanced |
| `useStore.setState` | tests / external |

`siteStorage` facade = thin wrapper around getState — useful for packages.

---

## Qesmat 10 — versions

dejban: `zustand` ^5, `immer` ^10 (peer via middleware; package immer present).  
Zustand 5: `create()` curried with middleware sometimes `create()(immer(...))` — syntax Dejban uses.

---

## Qesmat 11 — na form state

Staff form = RHF (Day 45), **na** Zustand.  
Site selection global = Zustand.  
List personnels = Query (preferred).

**Seh-ganeh zehni:** RHF / Query / Zustand.

---

# BAKHSH-E SHESHOM: farz kon / senario

## Se dastan

**1) User picks site**  
Layout `setSiteIds([id])` → LS + store → next Axios call `X-Site-Id` → tenant data.

**2) Open workspace tab**  
`openTab({ path, title })` → if exists activate; else add; cap 8 evict.

**3) Old units page**  
Component `useUnitsStore` → `getUnitsWithPagination()` → items in store → table.  
(New page might `useGetUnits` Query instead.)

---

## Smell-ha

1. Server data in Zustand + Query dual  
2. immer without draft style  
3. Site normalize max 1 vs header join multi  
4. loading/error shape inconsistent (`error: null` vs object)  
5. No persist middleware — custom LS only site  
6. Large async stores hard test  
7. Forget invalidate Query when Zustand mutate sibling screen  

---

## Debug checklist

| symptom | check |
|---|---|
| Wrong tenant API | site store + LS key `selectedSiteId` |
| Header empty | getSiteIds / set before first call |
| Tab lost refresh | tabs not persisted (by design?) |
| Stale units list | Zustand not refetched; or use Query |
| Rerender storm | select whole store |
| SSR crash LS | window guard |

---

## 25 soal-e mosahebe

1. Zustand vs Redux?  
2. Zustand vs Context?  
3. Client vs server state?  
4. `getState` chera for Axios?  
5. immer middleware chie?  
6. draft vs return object?  
7. useSiteStore persist chejori?  
8. Why max one site in normalize?  
9. Workspace tabs Zod? (na — Zustand)  
10. When NOT Zustand?  
11. Selector subscription?  
12. Middleware persist vs manual LS?  
13. create()() double call?  
14. Mutate server via Zustand smell?  
15. How test store?  
16. Multiple stores vs one big?  
17. Relation Day 44?  
18. Relation Day 45?  
19. siteStorage facade?  
20. Eviction tabs algorithm?  
21. Immer structural sharing?  
22. Zustand 5 changes?  
23. Can Query replace units-store?  
24. subscribe outside React?  
25. Day 46 one-liner?

---

## Senario-ha

**S1:** Two tabs same path → openTab reuses id.  
**S2:** Logout — clear site? (check auth flow removeSiteIds).  
**S3:** Multi-site product later — remove `slice(0,1)`.  
**S4:** Component uses store items + Query same URL → desync.  
**S5:** setState during render — avoid; use effects/actions.

---

## Mini lab

1. Bekhun `site-storage.js` + axios interceptor line  
2. Change site — DevTools Application LS + Network header  
3. Trace `openTab` eviction  
4. Compare units-store vs a `*.service.js` Query for same domain  
5. Rewrite one `set` as draft mutate under immer  

---

## Resume (1 paragraph)

> Used **Zustand** for cross-cutting client state—especially selected site (localStorage + `getState()` for Axios `X-Site-Id`) and workspace tabs—plus **immer middleware** on some feature stores. Prefer TanStack Query for server lists; treat older Zustand API stores as transitional.

Keywords: `Zustand` · `immer` · `getState` · `client state` · `X-Site-Id` · `localStorage` · `middleware` · `workspace tabs`

---

## File-haye mohem

| path | chera |
|---|---|
| `packages/ui/.../site-storage.js` | useSiteStore |
| `packages/api-client/.../axiosInstance.ts` | getState site ids |
| `packages/ui/.../dashboard/layout.jsx` | site picker wiring |
| `apps/dejban/.../workspace-tabs-store.js` | tabs UI |
| `apps/dejban/src/stores/*-store.js` | immer+API legacy |
| `apps/access-control/src/stores/*` | more examples |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 16 | tenancy header meaning |
| 40 | auth + site claims |
| 42 | workspace tabs host |
| 44 | Query vs Zustand server |
| 45 | RHF ≠ Zustand |
| **46** | this |
| 49 | guards read site store |

---

## Chejori digest koni

1. Seh-ganeh RHF/Query/Zustand  
2. Site store + Axios getState  
3. Tabs = pure client  
4. Immer stores honesty  
5. Resume  

---

## Glossary

| term | ma'ni |
|---|---|
| store | global state container |
| set/get | update / read inside |
| getState | read outside React |
| selector | subscribe slice |
| immer | mutable draft → immutable |
| middleware | wrap create (immer/persist) |
| client state | UI/session browser |
| server state | remote data |
| facade | siteStorage over store |

---

## Deep dive — why not Context for site?

Context + provider nesting; update rerender subtree.  
Zustand selector finer.  
Axios cannot `useContext` — needs getState. **Dealbreaker for interceptors.**

---

## Deep dive — persist middleware (WORLD)

```js
persist((set) => ({...}), { name: 'site' })
```

Dejban site = custom because normalize + single key string.  
Tabs intentionally maybe ephemeral.

---

## Deep dive — equality / rerender

Default Object.is.  
Select primitives.  
For objects return stable or use shallow compare middleware.

---

## Anti-pattern

| bad | better |
|---|---|
| All API data in Zustand | Query |
| Form values in Zustand | RHF |
| useStore() without selector on big store | select fields |
| Mutate state outside set | always set |
| Duplicate site in React state + Zustand | single store |
| Claim immer expert while only spreading | honest |

---

## Interview 60s

«We use Zustand for client state. The critical store is selected site: it’s persisted to localStorage and read via getState in the Axios interceptor for X-Site-Id. Workspace tabs are another Zustand store. Some older feature stores still fetch with immer middleware, but new server state should go through TanStack Query.»

---

## Quick self-test

1. Site key LS? → `selectedSiteId`  
2. Axios reads site how? → `useSiteStore.getState()`  
3. Tabs immer? → no  
4. Units store immer? → yes  
5. Max sites normalize? → 1  
6. Form state tool? → RHF  
7. Server list preferred? → Query  

---

## Final checklist

- [ ] Zustand basics set/get/getState  
- [ ] Site store + LS + header  
- [ ] Tabs store  
- [ ] immer middleware + honesty usage  
- [ ] Client vs server split  
- [ ] smells dual data  
- [ ] resume  

---

## Extra — Farz kon migrate units-store → Query

1. Add `units.http.js` / keys / service  
2. Replace components hooks  
3. Delete store methods fetch  
4. Keep Zustand only if UI-only flags remain  

Monorepo gradual — na big bang.

---

## Extra — testing stores

```js
useSiteStore.setState({ selectedSiteIds: ['x'] });
expect(useSiteStore.getState().getSiteIds()).toEqual(['x']);
useSiteStore.getState().removeSiteIds();
```

No React render needed.

---

## Extra — Soalat chera

**Chera Zustand for site?** global + getState for Axios.  
**Chera LS?** survive refresh.  
**Chera na Redux?** simplicity.  
**Chera immer?** nested updates easier (intent); adoption uneven.  
**Chera na Query for tabs?** not server data.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «Three state tools: React Hook Form for forms, TanStack Query for server cache, Zustand for client globals. Site selection lives in Zustand, persists to localStorage, and Axios reads it with getState. Immer wraps some older stores.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| API wrong site | stale LS / not setSiteIds |
| Infinite layout effect | siteOptions sync deps |
| Tabs > 8 weird | eviction skipped if only active |
| Store loading stuck | finally set missing |
| Hydration mismatch | read LS in render SSR |

---

## Extra — Layer checklist

| need | tool |
|---|---|
| Selected site | Zustand + LS |
| Open workspace tabs | Zustand |
| Personnel list | Query |
| Staff create form | RHF+Zod |
| Nested draft edit UI temp | Zustand or local useState |

---

## Extra — Related days jump

- 16/40 tenancy auth  
- 42 tabs host  
- 44 Query  
- 45 forms  
- 49 guards  

---

## Extra — `create()` curry

```js
create()(immer((set) => (...)))
```

Middleware typing/compose in v4/v5.  
Without middleware: `create((set) => (...))` site store style.

---

## Extra — multiple selected sites future

Array already; normalize `slice(0,1)` temporary product rule.  
Axios already `join(',')`.  
UI multi-select later = relax normalize + picker.

---

## Extra — dirty tab flag

`setTabDirty` — warn before close unsaved form.  
Bridge RHF `isDirty` → store for tab chrome.

---

## Band-e gharardad-e jadid

Zustand = jabe abzar roye miz (site, tabs).  
getState = dast rasidan bedun React.  
LS = yadashat site.  
immer = ghalam roye draft (agar dorost estefade).  
Query = baygani server.  
RHF = formul.  
Ethtebaah: hame chiz yek jabe.

---

## 10 jomle fluency

1. Zustand holds client/global UI state.  
2. useSiteStore drives X-Site-Id.  
3. Axios uses getState, not hooks.  
4. Site id persists in localStorage.  
5. Workspace tabs are pure client Zustand.  
6. Immer middleware enables draft updates.  
7. Many immer stores still return new objects.  
8. Prefer Query for server lists.  
9. Prefer RHF for forms.  
10. Older Zustand API stores are transitional.

---

## Extra — Comparison Jotai/Recoil

Atom model; team chose Zustand — one store style familiar.  
No need deep compare unless asked.

---

## Extra — Devtools

`redux-devtools` middleware optional for Zustand.  
Check if enabled — often not; use log set.

---

## Extra — memory

Tabs keepAlive components — memory cost (Day 42 host).  
Store only metadata; heavy UI elsewhere.

---

## Extra — security

Site id in LS — tamperable.  
BE must enforce tenant (Day 16). FE store convenience not security.

---

## Extra — reset on logout

Call `removeSiteIds` + clear tabs on logout for clean next user on shared PC.  
Verify auth logout path — smell if missing.

---

## Band-e gharardad — ye bar digar sade

1. **Zustand** = global client store.  
2. **set/get/getState** = update/read.  
3. **Site store** = tenant picker + LS.  
4. **Axios** = mikhune getState.  
5. **Tabs store** = UI chrome.  
6. **immer** = middleware optional.  
7. **Query** = server data (prefer).  
8. **RHF** = forms.  
9. **Legacy** = API-in-Zustand.  
10. **Honesty** = don't oversell immer usage.

---

## Extra — Capacity

Tiny stores cheap.  
Avoid stuffing megabyte lists long-term in Zustand without gc — Query gcTime better.

---

## Extra — onboarding rule

New feature:  
- UI flag → Zustand or useState  
- List/detail from API → Query  
- Form → RHF  
- Site? → existing useSiteStore only  

---

## Extra — role-management-api store

Another dejban zustand file — same family.  
Skim pattern when touching roles UI.

---

## Extra — access-group-actions naming

«actions» stores often dialog open + selected row ids — good client state.  
Keep; don't force Query.

---

## Extra — snapshot for interview whiteboard

Boxes: [SiteStore]→[Axios]→[API] ; [TabsStore]→[Dashboard] ; [Query cache] separate ; [RHF] per form.

---

## Extra — shallow compare

Agar selector object barmigardune (`(s) => ({ a: s.a, b: s.b })`) har bar reference jadid → rerender.  
Fix: select primitives joda; ya `useShallow` az zustand/react/shallow.

---

## Extra — middleware stack (WORLD)

```js
create()(persist(immer((set) => (...)), { name: 'x' }))
```

Tartib mohem. Dejban site = no persist middleware; feature stores = immer only.

---

## Extra — replace vs merge set

`set({ tabs: next })` replace keys given.  
Partial merge default top-level. Nested objects replace whole key unless immer draft mutate.

---

## Extra — when Zustand overkill

Yek boolean modal to yek page → `useState`.  
Zustand vaghti *chand* component door az ham share mikonand ya non-React reader hast.

---

## Extra — naming conventions

`useXStore` hook export.  
Actions verbs: `setSiteIds`, `openTab`.  
Avoid `useX` alone — confuse ba Query hooks `useGetX`.

---

## Extra — race site sync layout

Layout effect auto-picks first site when empty — race ba user clear.  
Bekhun `dashboard/layout.jsx` deps — mosahebe debug classic.

---

## Khoruj-e zehni

> Midunam Zustand baraye client state-e (site + tabs + flags); site ba LS va getState miravad to Axios X-Site-Id; immer middleware roye ba'zi store-ha-st amma draft kam estefade; server list-ha prefer Query; form-ha RHF — va API-in-Zustand legacy-e.

Age in paragraph mal-e to shod — Day 46 done.

---

*Day 46 tamum. Ba'd: Day 47 — MUI 7 + Emotion + RTL (amade). Fehrest: [README.md](./README.md).*
