# Day 52 — material-react-table

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** list-haye admin (staff, units, tickets, armory, …) — pagination/sort/filter/export/actions — chejori yekja?

**Javab Dejban:** library **`material-react-table`** (MRT) wrapped as **`MRTDataTable`** in `@repo/ui/mrt-table`.

Zincir tipikal (Day 51 list-view):

```
StaffListView
  queryParams state { page, pageSize, searchTerm, sortColumn, sortOrder, filters }
  → useGetStaffWithPagination(queryParams)   // Day 44
  → <MRTDataTable
       data={items}
       rowCount={totalCount}
       columns={...}
       setQueryParams={...}
       onEdit / onDelete
       editPermission={componentPaths.…}
       syncUrl={false|true}
     />
```

**MRT mode Dejban (critical):**

| flag | value | ma'ni |
|---|---|---|
| `manualPagination` | **true** | server pages |
| `manualSorting` | **true** | server sort |
| `manualFiltering` | **true** | server filters |
| `rowCount` | totalCount API | pager knows total |

**Na** client-only filter 10k rows to browser — API + Query.

**Band-e gharardad-e jadid:** farz kon / yani chi / chera.

Day 51 = list-view folder. **In ruz = table engine + wrapper.**

---

# BAKHSH-E AVAL: WORLD — MRT chie?

## Farz kon — Excel zende ba React

MRT = table headful built on TanStack Table ideas + MUI look: columns, sorting UI, column filters, density, export hooks, row actions, virtualization optional.

Alternatives: MUI X Data Grid (ham to deps), plain Table.  
Dejban list screens **asosli = MRT** via shared wrapper.

---

## Chera wrapper `MRTDataTable`?

Raw MRT har list 200 line boilerplate.  
Wrapper adds Dejban standards:

- Server query param bridge (`setQueryParams`)  
- URL sync (page/search/filters) — off when workspace tabs  
- Debounced search (500ms, min 2 chars)  
- FA/EN localization packs  
- Edit/Delete + `Guard` permissions  
- CSV / PDF export (jspdf + vazir font)  
- Theme styles (`useBaseGridStyles`)  
- Sticky actions column  

**Yani chi:** feature author = columns + data + handlers; na re-wire MRT every time.

---

# BAKHSH-E DOVOM: DEJBAN wrapper

## Qesmat 1 — import

```js
import { MRTDataTable } from '@repo/ui/mrt-table';
```

Package export → `packages/ui/.../mrt-datatable/`.

Version: `material-react-table` ^3.x (dejban package.json).

---

## Qesmat 2 — props asosli

| prop | kar |
|---|---|
| `data` | current page rows |
| `columns` | MRT column defs |
| `rowCount` | total server count |
| `isLoading` | spinner state |
| `setQueryParams` | push page/size/search/sort/filters up |
| `onEdit` / `onDelete` / `onView` | row actions |
| `editPermission` / `deletePermission` | componentId → Guard |
| `customRowActions` | extra menu items |
| `enableExportCSV/PDF` | toolbar exports |
| `syncUrl` | write searchParams (default true; false if tabs) |
| `renderDetailPanel` | expand row |
| `enableRowVirtualization` | big client lists rare |

---

## Qesmat 3 — server pipeline

1. User changes page/sort/filter/search in MRT  
2. Internal state + debounce  
3. `buildQueryParams` → operators `eq`/`contains`/…  
4. Calls `setQueryParams({ page, pageSize, searchTerm, sortColumn, sortOrder, filters })`  
5. Parent updates state → React Query refetch  
6. New `data` + `rowCount` back into table  

**manual*** flags ensure MRT doesn't filter local `data` only.

---

## Qesmat 4 — URL sync

When `syncUrl` and **not** workspaceTabs:

- Read `page`, `pageSize`, `searchTerm`, `sortColumn`, `sortOrder`, `filters` from URL  
- Write back on change (shareable list links)  

Staff example: `syncUrl={false}` — tabs / simpler state.  
`effectiveSyncUrl = syncUrl && !settings.state.workspaceTabs`.

---

## Qesmat 5 — search debounce

```js
SEARCH_DEBOUNCE_MS = 500
SEARCH_MIN_LENGTH = 2
```

Typing 1 char → no API spam.  
Digits normalized English (`toEnglishDigits`).

---

## Qesmat 6 — localization

```js
localization: currentLang === 'fa-IR' ? MRT_Localization_FA : MRT_Localization_EN
```

Toolbar strings Farsi/English (Day 48).

---

## Qesmat 7 — permissions

```jsx
editPermission={componentPaths.…staffEditButton.value}
deletePermission={...}
```

Wrapper wraps action buttons in `<Guard componentId={...}>` (Day 49).  
Create button usually **outside** table in breadcrumbs (also Guard).

---

## Qesmat 8 — export

CSV via `export-to-csv`.  
PDF via `jspdf` + `autotable` + registered Vazirmatn font (Persian).  
Extra export slots: Stimulsoft quick exports (Day 39) via `extraExportActions`.

---

## Qesmat 9 — styles / RTL honesty

`useBaseGridStyles`: paper `direction: 'ltr'` forced.

**Chera?** number/date columns + MRT internals often LTR-friendlier; page chrome still RTL (Day 47).  
**Jazire LTR** inside RTL app — interview honesty.

Sticky action column styles; density compact; theme mode colors.

---

## Qesmat 10 — columns in list-view

```js
const columns = useMemo(() => [
  { accessorKey: 'firstName', header: t('...'), enableColumnFilterModes: true },
  { accessorKey: 'contractStartDate',
    Cell: ({ cell }) => JalaliHelper.gregorianToJalali(new Date(cell.getValue())) },
], [t, currentLang]);
```

Filter modes enable → wrapper maps to API operators.  
Jalali display Day 48; sort still server on Gregorian field usually.

---

# BAKHSH-E SEVOM: list-view recipe (staff)

```js
const [queryParams, setQueryParams] = useState({ page: 1, pageSize: 10, ... });
const { data, isLoading, refetch } = useGetStaffWithPagination(queryParams);
const handleSetQueryParams = useCallback((params) => setQueryParams({...}), []);

<MRTDataTable
  data={data?.items || []}
  rowCount={data?.totalCount || 0}
  columns={columns}
  isLoading={isLoading}
  setQueryParams={handleSetQueryParams}
  onEdit={handleEditRow}
  onDelete={handleDelete}
  editPermission={...}
  customRowActions={...}
  syncUrl={false}
/>
```

Dialogs create/edit beside — Day 45/51.

**Smell:** some list-views pass legacy props (`onSort`, `refetchMethod`) — wrapper may ignore; trust `setQueryParams` path.

---

# BAKHSH-E CHAHAROM: farz kon / senario

## Se dastan

**1) User pages to 2**  
MRT pagination → setQueryParams page=2 → Query key change → API → new rows.

**2) Search «علی»**  
Debounce → searchTerm → API contains → rowCount update.

**3) Edit without claim**  
editPermission Guard → pencil hidden; API still protected.

---

## Smell-ha

1. Wrapper file huge (~1000 lines) — god component  
2. Imports `src/locales` / `src/routes` inside `@repo/ui` (app-coupled)  
3. Forced LTR table  
4. Legacy props drift on call sites  
5. `enableRowSelection` prop vs internal `false` hardcode — read source  
6. PDF export font registration complexity  
7. Filter operator mapping fragile per column  
8. Dual MUI X DataGrid still in deps — don't confuse  

---

## Debug checklist

| symptom | check |
|---|---|
| Only one page of data | rowCount / manualPagination |
| Filter no API | setQueryParams wired? |
| Search fires every key | debounce / min length |
| URL not updating | syncUrl / workspaceTabs |
| Edit missing | editPermission claim |
| PDF broken Persian | Vazir font register |
| Wrong dir numbers | ltr island expected |

---

## 25 soal-e mosahebe

1. MRT vs MUI Data Grid here?  
2. manualPagination chera?  
3. MRTDataTable role?  
4. setQueryParams flow?  
5. rowCount az koja?  
6. Debounce search?  
7. syncUrl vs tabs?  
8. editPermission?  
9. Localization packs?  
10. LTR direction smell?  
11. Export CSV/PDF?  
12. Column Cell Jalali?  
13. Filter operators map?  
14. customRowActions?  
15. Virtualization when?  
16. getRowId?  
17. Day 44 link?  
18. Day 49 link?  
19. Sticky actions?  
20. Why not client filter all?  
21. Stimulsoft extra exports?  
22. Density compact?  
23. Wrapper in which package?  
24. How add column filter mode?  
25. Day 52 one-liner?

---

## Senario-ha

**S1:** New list — copy staff pattern + columns + trinity service.  
**S2:** Huge pageSize 9999 — smell; prefer server page.  
**S3:** Detail panel expand — `renderDetailPanel`.  
**S4:** Disable export — `enableExportCSV={false}`.  
**S5:** Workspace tabs on — URL sync auto off.

---

## Mini lab

1. Open staff Network — change page — see page param  
2. Type 1 char search — no request; 2+ after 500ms  
3. Remove edit claim — pencil gone  
4. Inspect table `direction: ltr` in DevTools  
5. Export CSV sample  

---

## Resume (1 paragraph)

> Standardized admin grids with **material-react-table** behind a shared **`MRTDataTable`** wrapper: server-side pagination/sort/filter via query params and React Query, FA/EN localization, permission-gated row actions, CSV/PDF export, and optional URL sync—used across Dejban list views.

Keywords: `material-react-table` · `MRT` · `manualPagination` · `server-side table` · `row actions` · `export` · `MRTDataTable`

---

## File-haye mohem

| path | chera |
|---|---|
| `packages/ui/.../mrt-datatable.jsx` | wrapper |
| `use-base-grid-styles.js` | theme + ltr |
| `apps/dejban/.../staff-list-view.jsx` | consumer |
| many `sections/**/view/*-list-view.jsx` | same pattern |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 44 | Query + params |
| 47 | RTL vs table LTR |
| 48 | Jalali cells + MRT locale |
| 49 | editPermission Guards |
| 51 | list-view folder |
| 39 | Stimulsoft exports |
| **52** | this |

---

## Chejori digest koni

1. Manual server table mantra  
2. MRTDataTable props  
3. queryParams ↔ Query  
4. Staff lab  
5. Resume  

---

## Glossary

| term | ma'ni |
|---|---|
| MRT | material-react-table |
| manualPagination | server controls pages |
| accessorKey | field path |
| rowCount | total records |
| column filter mode | equals/contains UI |
| global filter | search box |
| row actions | edit/delete menu |
| virtualization | windowed rows |

---

## Deep dive — TanStack Table

MRT sits on table headless concepts (TanStack).  
You configure columns/state; MRT renders MUI.  
Knowing headless helps debug `state.pagination`.

---

## Deep dive — filters string

Parent often sends `filters` as serialized string API understands.  
Wrapper builds from columnFilters — contract with BE filter DSL.

---

## Deep dive — single sort

`onSortingChange` keeps last sort only (`[next[last]]`) — multi-sort off by design.

---

## Anti-pattern

| bad | better |
|---|---|
| Load all rows client filter | server page |
| Copy raw MRT 50 times | MRTDataTable |
| Forget rowCount | broken pager |
| Sort only UI | manualSorting + API |
| Hide edit only CSS | editPermission Guard |
| Assume RTL table | expect ltr island |

---

## Interview 60s

«Our lists use material-react-table through a shared MRTDataTable. Everything important is server-driven: manual pagination, sorting, and filtering push query params into React Query. The wrapper handles debounce, localization, exports, and permission-gated row actions.»

---

## Quick self-test

1. Wrapper name? → MRTDataTable  
2. manualPagination? → true  
3. Package import? → `@repo/ui/mrt-table`  
4. Search debounce? → 500ms / min 2  
5. Table direction? → ltr forced  
6. Permissions props? → editPermission / deletePermission  
7. Data source? → Query items + totalCount  

---

## Final checklist

- [ ] MRT role  
- [ ] manual* server mode  
- [ ] setQueryParams bridge  
- [ ] permissions + export + locale  
- [ ] LTR honesty  
- [ ] staff recipe  
- [ ] resume  

---

## Extra — Farz kon infinite scroll

`enableRowVirtualization` + different fetch — rare; most lists pager.  
Infinite elsewhere (`useInfiniteList` Day 44) for autocomplete not MRT main.

---

## Extra — Soalat chera

**Chera MRT?** rich grid + MUI fit.  
**Chera wrapper?** consistency.  
**Chera server manual?** scale + tenancy filters.  
**Chera debounce?** API kindness.  
**Chera ltr table?** layout/control stability.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «List views hold queryParams and call React Query. MRTDataTable is a server-mode MRT wrapper that emits param changes, shows FA/EN UI, exports, and gates edit/delete with componentId Guards.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Page stuck | rowCount 0 / items undefined |
| Double fetch | params object identity |
| Filter ignored | column accessor mismatch |
| URL fight tabs | syncUrl |
| PDF empty FA | font |
| Actions missing | permissions / enableRowActions |

---

## Extra — Layer checklist

| layer | owner |
|---|---|
| Library | material-react-table |
| Wrapper | @repo/ui MRTDataTable |
| Params state | list-view |
| Fetch | *.service.js |
| Auth actions | Guard ids |
| Dates display | JalaliHelper |

---

## Extra — Related days

44 · 47 · 48 · 49 · 51 · 39  

---

## Extra — MUI X DataGrid

Still dependency for some screens / theme overrides.  
Default new list → MRTDataTable unless X-specific need.

---

## Extra — row click

`rowClickActivate` / `onRowActivate` / `selectedRowId` — selection UX variants.  
Read props before inventing.

---

## Extra — toolbar custom

`renderTopToolbarCustomActions` / `extraToolbarActions` / secondary row for complex filters UI.

---

## Band-e gharardad-e jadid

MRT = motor jadval.  
MRTDataTable = dashboard standard car.  
queryParams = steering to API.  
Query = fuel data.  
Guard = seatbelt actions.  
Export = printer.  
LTR grid = dashboard gauges LTR.

---

## 10 jomle fluency

1. Lists use material-react-table via MRTDataTable.  
2. Pagination sorting filtering are manual/server-side.  
3. setQueryParams drives React Query.  
4. rowCount comes from API totalCount.  
5. Search is debounced.  
6. FA/EN localization packs are switched by lang.  
7. editPermission wraps actions in Guard.  
8. CSV and PDF export are built in.  
9. Table paper forces LTR inside RTL apps.  
10. Feature work is mostly columns plus handlers.

---

## Extra — Comparison AG Grid

AG Grid enterprise features; MRT OSS MUI-native.  
Team choice wrapper investment.

---

## Extra — performance

Page size 10–50 typical.  
Avoid rendering heavy Cell components without memo.  
Virtualization for special live feeds.

---

## Extra — accessibility

MRT/MUI keyboard — test tab order actions.  
Don't remove header labels.

---

## Extra — testing

Mock data + columns; assert setQueryParams called on page change (RTL).  
E2E: sort column Network assert.

---

## Band-e gharardad — ye bar digar sade

1. **MRT** = table lib.  
2. **MRTDataTable** = Dejban wrapper.  
3. **manual*** = server mode.  
4. **setQueryParams** = bridge.  
5. **Query** = fetch.  
6. **columns** = feature config.  
7. **permissions** = Guard ids.  
8. **export** = CSV/PDF.  
9. **syncUrl** = optional.  
10. **ltr island** = known.

---

## Extra — Capacity

Wrapper shared → fix once, all lists benefit.  
Regression risk high — test staff + one armory list after wrapper change.

---

## Extra — onboarding

First task: add column to existing MRTDataTable + verify filter mode if needed.

---

## Extra — delete dialog

Wrapper has delete confirm dialog hooks (`deleteDialogExtra`, `onDeleteDialogOpen`).  
Parent `onDelete` receives rows.

---

## Extra — getRowId

`row.id` assumed — GUID entities.  
Composite keys need override carefully.

---

## Extra — interview whiteboard

User → MRT UI → setQueryParams → useQuery → API → items/totalCount → MRT.

---

## Extra — legacy list props

If call site passes `onPageChange` unused — clean when touching file; prefer single setQueryParams API.

---

## Extra — density / fontSize

Settings fontSize shrinks grid font (`smallerFontSize`).  
Compact density default admin.

---

## Extra — expand column

`positionExpandColumn: 'first'` when detail panel — master-detail rare lists.

---

## Extra — column pinning / ordering

Wrapper sets `enableColumnOrdering: false` — stable admin UX.  
Don't enable casually (persist prefs complexity).

---

## Extra — full screen toggle

`enableFullScreenToggle: false` — product choice; fullscreen often breaks dashboard chrome.

---

## Extra — sticky header

`enableStickyHeader: true` — long pages scroll body keep headers.  
Works with paper height constraints.

---

## Extra — layoutMode grid

`layoutMode: 'grid'` — MRT layout mode for column sizing behavior.  
Know when debugging width bugs.

---

## Extra — initialFilters

Prop `initialFilters` when URL empty — default column filters (e.g. status=Active).  
Combine carefully with syncUrl.

---

## Extra — canEditRow / canDeleteRow

Per-row predicates beyond global permission — e.g. cannot edit locked records.  
AND with Guard (both must pass).

---

## Extra — selection

Prop `enableRowSelection` exists but table options may force false — verify before bulk UX.  
Bulk delete often custom toolbar not built-in selection.

---

## Extra — report module bridge

Staff wires `ReportQuickGridExports` into toolbar/export slots — same grid, Stimulsoft path (Day 39).

---

## Extra — gate / access-control apps

Also import MRTDataTable from `@repo/ui` (or local copy in older AC).  
Same wrapper story monorepo.

---

## Extra — when to NOT use MRT

Tiny 5-row static display → plain MUI Table.  
Heavy spreadsheet editing → different tool.  
MRT = **data admin grid**.

---

## Extra — pageSize options

Default 10; users change via MRT pager.  
Parent must pass new pageSize into Query — setQueryParams includes it.

---

## Extra — empty state

isLoading false + data [] → MRT empty message (localized).  
Don't replace whole table with custom empty unless product asks.

---

## Extra — error state

Query `isError` — list-view should show Alert above MRT; wrapper mainly loading flag.

---

## Extra — refetch after dialog

`onRefetch` / `refetch()` after create/edit/delete success — classic beside invalidate in mutation (both OK).

---

## Extra — column size

`size` / `minSize` / `maxSize` on columns + action column sticky sizing props.

---

## Extra — GlobalFilter position

`positionGlobalFilter = 'left'` default — RTL chrome still OK with ltr table island.

---

## Khoruj-e zehni

> Midunam list-haye Dejban ba material-react-table az tarigh MRTDataTable-an; manual server pagination/sort/filter; setQueryParams→Query; Guard edit/delete; export; locale FA/EN; va table LTR island.

Age in paragraph mal-e to shod — Day 52 done.

---

*Day 52 tamum. Ba'd: Day 53 — SWR (amade). Fehrest: [README.md](./README.md).*
