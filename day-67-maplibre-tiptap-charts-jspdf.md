# Day 67 — MapLibre + TipTap + Charts + jsPDF

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Dejban FE faghat MUI table (Day 47/52) nist — **4 ta lib-e dge** ham dare ke har kodum resume-worthy-e: **MapLibre** (naghshe-ye open-source), **TipTap** (rich text editor headless), **Recharts** (chart-haye composable-e React) baraye module dashboard-ha, **ApexCharts** (lazy-loaded) baraye template chart component, va **jsPDF + jspdf-autotable** baraye PDF export az MRT table ba font-e **Vazirmatn** baraye Farsi RTL. In ruz ye "UI lib inventory" va pattern-e har kodum ro mibini — focus ru-ye **tech mechanism** na domain.

---

# BAKHSH-E AVAL: WORLD — har lib ra dar dunya bebin

## MapLibre — open-source map rendering

### Farz kon
Google Maps $$ mikhad va API key lock-in dare. MapLibre (fork-e Mapbox GL JS) **open-source**-e va ba tile server-e khodet kar mikone.

### Core concepts

| concept | tozih |
|---|---|
| **Tile source** | raster ya vector tile-ha az server (masalan TileServer GL, Maptiler) |
| **Style** | JSON file ke layer-ha, rang-ha, font-ha ro define mikone |
| **Layer** | ye laaye-ye visuali (road, building, marker, polygon) |
| **Marker** | icon/pin ru-ye map |
| **Popup** | tooltip vaghti click mikoni |
| **Control** | navigation, zoom, geolocate button |

### MapLibre vs alternatives

| lib | license | cost | tiles |
|---|---|---|---|
| **MapLibre GL JS** | BSD | free | bring your own (open tiles) |
| Mapbox GL JS | proprietary (v2+) | paid after free tier | Mapbox tiles |
| Google Maps | proprietary | paid | Google tiles |
| Leaflet | BSD | free | any tiles (raster only, no GL) |
| OpenLayers | BSD | free | any tiles (heavy API) |

**Chera MapLibre?** Free, WebGL-based (smooth), vector tiles, large community. Trade-off: tile hosting khodet bayad handle koni.

### react-map-gl

```jsx
import Map from 'react-map-gl/maplibre';

<Map
    initialViewState={{ longitude: 51.3, latitude: 35.7, zoom: 12 }}
    mapStyle="https://tiles.example.com/style.json"
>
    <Marker longitude={51.3} latitude={35.7}>📍</Marker>
    <Popup longitude={51.3} latitude={35.7}>Tehran</Popup>
    <NavigationControl />
</Map>
```

`react-map-gl` ye React wrapper-e baraye Mapbox GL JS **va** MapLibre GL JS — import path avaz mishe: `react-map-gl/maplibre`.

---

## TipTap — headless rich text editor

### Farz kon
User bayad text-e formatted (bold, link, list, code) type kone — ye textarea kafi nist. CKEditor sangin-e va config-esh asabi-e. TipTap **headless**-e — khodesh UI nadare, to UI ro misazi.

### Core concepts

| concept | tozih |
|---|---|
| **ProseMirror** | engine-e zir-e TipTap ke document model + transactions ro manage mikone |
| **Extension** | modular plug-in: StarterKit (bold, italic, heading, ...), Link, Image, CodeBlock, ... |
| **StarterKit** | ye bundle-e default extensions |
| **Editor instance** | `useEditor()` — control-e editor (setContent, getHTML, commands) |
| **Node view** | custom React component baraye ye ProseMirror node (masalan code-block ba highlight) |
| **Transaction** | atomic change to document model |

### TipTap vs alternatives

| lib | approach | React native | UI |
|---|---|---|---|
| **TipTap** | headless (ProseMirror) | yes (useEditor) | bring your own |
| Quill | opinionated | wrapper needed | built-in |
| CKEditor 5 | opinionated | wrapper | built-in (heavy) |
| Draft.js | low-level | yes | bring your own |
| Slate.js | low-level | yes | bring your own |
| Lexical (Meta) | framework-agnostic | plugin | plugin-based |

**Chera TipTap?** Headless = kamel customizable ba MUI. ProseMirror engine robust-e. Extensions modular-an.

### RHF integration

```jsx
// react-hook-form + TipTap
<Controller
    name="description"
    control={control}
    render={({ field }) => (
        <Editor
            value={field.value}
            onChange={field.onChange}
            error={!!errors.description}
            helperText={errors.description?.message}
        />
    )}
/>
```

Editor `onChange` HTML string mide → RHF store mikone → submit mikoni, HTML mishe.

---

## Recharts vs ApexCharts — do ta lib-e chart

### Farz kon
Dashboard-e har module (center-grouping, traffic-ops, weigh-bridge) chart dare. Ye chart lib bashe ya do ta?

### Recharts

| property | detail |
|---|---|
| **approach** | React composable — har element ye component |
| **rendering** | SVG |
| **bundle** | ~45KB gzip |
| **API style** | `<BarChart><Bar /><XAxis /><Tooltip /></BarChart>` |
| **customization** | JSX children — kheili flexible |

```jsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

<ResponsiveContainer width="100%" height={300}>
    <BarChart data={chartData}>
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="value" fill="#2196f3" />
    </BarChart>
</ResponsiveContainer>
```

### ApexCharts

| property | detail |
|---|---|
| **approach** | config object → render |
| **rendering** | SVG + canvas hybrid |
| **bundle** | ~125KB gzip (sangin-tar) |
| **API style** | `<Chart type="bar" series={[...]} options={{...}} />` |
| **features** | bozorg-tar: zoom, annotations, sparklines, heatmaps |

```jsx
import Chart from 'react-apexcharts';

<Chart
    type="bar"
    series={[{ name: 'Sales', data: [30, 40, 35, 50] }]}
    options={{ xaxis: { categories: ['Jan', 'Feb', 'Mar', 'Apr'] } }}
/>
```

### Chera Dejban har do dare?

| | Recharts | ApexCharts |
|---|---|---|
| **use case to Dejban** | module dashboard-ha (custom charts) | template `Chart` component (lazy) |
| **loaded when** | dashboard page → direct import | lazy → `React.lazy(() => import('react-apexcharts'))` |
| **chera** | lightweight; composable; custom layout | pre-built feature-rich; template charts |
| **code location** | `sections/*/dashboard/*-dashboard-view.jsx` | `components/chart/chart.jsx` |

**Template Chart** (`chart.jsx`) — ye component-e ke az template-e MUI Minimal miad. Lazy load mishe ta bundle size kam bemune. Baraye sidebar-haye kuchik ya analytics-haye sade estefade mishe.

**Module dashboard** — chart-haye custom ke developer ba Recharts misaze. Composable-tar-e va bundle-e kamtari dare.

---

## jsPDF — client-side PDF generation

### Farz kon
User jadval-e MRT ro mibine va mikhad PDF export kone — bedun-e server call. jsPDF ye PDF to browser misaze.

### Core concepts

| concept | tozih |
|---|---|
| **jsPDF** | client-side PDF generator |
| **jspdf-autotable** | plugin baraye table generation |
| **Font embedding** | custom font baraye non-Latin scripts (Farsi) |
| **halign** | text alignment (right baraye RTL) |
| **orientation** | portrait / landscape |

### Challenge-e Farsi/RTL

**Problem:** jsPDF default font (Helvetica) Farsi character nadare → "☐☐☐" neshun mide.

**Solution:** font-e Vazirmatn ro be soorat-e Base64 embed mikoni:

```js
// Vazirmatn-Regular-normal.js
import { jsPDF } from 'jspdf';

const font = '...base64 encoded TTF...';

export function registerVazirmatnFont() {
    const callAddFont = function () {
        this.addFileToVFS('Vazirmatn-Regular.ttf', font);
        this.addFont('Vazirmatn-Regular.ttf', 'Vazirmatn', 'normal');
    };
    jsPDF.API.events.push(['addFonts', callAddFont]);
}
```

**ba'd to export:**

```js
const doc = new jsPDF({ orientation: 'landscape' });
doc.setFont('Vazirmatn');

autoTable(doc, {
    head: [headers],
    body: rows,
    styles: {
        font: 'Vazirmatn',
        halign: isRTL ? 'right' : 'left',  // ← RTL alignment
    },
    headStyles: {
        font: 'Vazirmatn',
        halign: isRTL ? 'right' : 'left',
    },
});

doc.save('exported-table.pdf');
```

### Server PDF vs Client PDF

| | Client (jsPDF) | Server (Stimulsoft, Puppeteer, etc.) |
|---|---|---|
| **dependency** | browser only | server process |
| **data** | client-side data (current page/selection) | any data (DB query) |
| **complexity** | low | medium-high |
| **layout** | limited (table, text) | full (charts, images, page breaks) |
| **performance** | fast (no network) | slower (render + download) |
| **Dejban** | MRT export button | Stimulsoft reports (Day 39/64) |

**Key vaght server PDF?** Vaghti layout complex-e (charts, images, multi-page report), ya data az server-e (na client), ya bayad barcode/QR generate koni.

---

# BAKHSH-E DOVOM: DEJBAN — piade-sazi-e vaghei

## 1) MapLibre — `packages/ui/src/components/map/map.jsx`

```jsx
import { lazy, Suspense } from 'react';
import { useIsClient } from 'minimal-shared/hooks';
import Skeleton from '@mui/material/Skeleton';
import { styled } from '@mui/material/styles';

const LazyMap = lazy(() => import('react-map-gl/maplibre'));

export function Map({ ref, sx, ...other }) {
  const isClient = useIsClient();

  return (
    <MapRoot sx={sx}>
      {isClient ? (
        <Suspense fallback={<Skeleton variant="rectangular" sx={{ width: 1, height: 1 }} />}>
          <LazyMap ref={ref} {...other} />
        </Suspense>
      ) : (
        <Skeleton />
      )}
    </MapRoot>
  );
}

const MapRoot = styled('div')({ width: '100%', overflow: 'hidden', position: 'relative' });
```

**Pattern-ha:**
- **Lazy loading:** `react-map-gl/maplibre` bundle-e sangin-e (~200KB) — lazy import mikone ta initial load sabok bemune
- **SSR safety:** `useIsClient()` — MapLibre `window` lazem dare; SSR crash mikone → faghat client render mishe
- **Suspense fallback:** Skeleton neshun mide ta map load beshe
- **Styled wrapper:** consistent sizing

**Related files:**
- `map-marker.jsx` — custom marker component
- `map-popup.jsx` — popup on click
- `map-controls.jsx` — zoom/navigation

**Locations to FE:**
- `packages/ui/src/components/map/` — shared map
- `apps/dejban/src/components/map/` — app-level override
- `apps/main/src/components/map/` — main portal map

## 2) TipTap — `packages/ui/src/components/editor/editor.jsx`

```jsx
import StarterKitExtension from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import ImageExtension from '@tiptap/extension-image';
import TextAlignExtension from '@tiptap/extension-text-align';
import PlaceholderExtension from '@tiptap/extension-placeholder';
import LinkExtension from '@tiptap/extension-link';
import CodeBlockLowlightExtension from '@tiptap/extension-code-block-lowlight';
import { useEditor, EditorContent } from '@tiptap/react';

export function Editor({ value, onChange, editable = true, placeholder, ... }) {
    const editor = useEditor({
        content: value,
        editable,
        immediatelyRender: false,
        shouldRerenderOnTransaction: false,
        extensions: [
            Underline,
            StarterKitExtension.configure({
                codeBlock: false,  // custom CodeBlockLowlight instead
                heading: { HTMLAttributes: { class: editorClasses.content.heading } },
                // ...more HTML class config
            }),
            PlaceholderExtension.configure({ placeholder }),
            ImageExtension,
            TextAlignExtension.configure({ types: ['heading', 'paragraph'] }),
            LinkExtension.configure({ autolink: true, openOnClick: false }),
            CodeBlockLowlightExtension.extend({
                addNodeView: () => ReactNodeViewRenderer(CodeHighlightBlock),
            }).configure({ lowlight: createLowlight(common) }),
        ],
        onUpdate({ editor }) {
            onChange?.(editor.getHTML());
        },
    });

    return (
        <EditorRoot>
            <Toolbar editor={editor} fullScreen={fullScreen} />
            <EditorContent editor={editor} />
        </EditorRoot>
    );
}
```

**Pattern-ha:**
- **`immediatelyRender: false`** — jelo-ye hydration mismatch to SSR migire
- **`shouldRerenderOnTransaction: false`** — performance: har keystroke re-render nemikone
- **`onUpdate → getHTML`** — output HTML-e ke to DB save mishe
- **Custom code block:** `CodeBlockLowlightExtension` ba `ReactNodeViewRenderer` — syntax highlighting ba `lowlight`
- **Full screen toggle:** portal + backdrop → editor full-screen mishe

**`resetValue` effect:**
```jsx
useEffect(() => {
    if (resetValue && !content) editor?.commands.clearContent();
}, [content]);
```
Vaghti form reset mishe, editor ham clear mishe.

## 3) Charts — Recharts to module dashboards

```jsx
// center-grouping-dashboard-view.jsx
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const PIE_COLORS = ['#2196f3', '#4caf50', '#ff9800', '#9c27b0', '#f44336', '#00bcd4'];

<ResponsiveContainer width="100%" height={300}>
    <PieChart>
        <Pie data={doorStatusDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%">
            {doorStatusDistribution.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
            ))}
        </Pie>
        <Tooltip />
    </PieChart>
</ResponsiveContainer>
```

**Karbord-ha to Dejban:**
- `center-grouping-dashboard-view.jsx` — sites/units/doors statistics
- `traffic-operations-dashboard-view.jsx` — vehicle flow charts
- `weigh-bridge-dashboard-view.jsx` — weighing statistics
- `contractors-dashboard-view.jsx` — contractor analytics
- `cartable-dashboard-view.jsx` — request pipeline
- `human-resource-dashboard-view.jsx` — staff metrics
- `reports-dashboard-view.jsx` — report analytics
- `arrangements-dashboard-view.jsx` — patrol arrangement charts
- `cars-management-dashboard-view.jsx` — vehicle fleet
- `guest-visitor-dashboard-view.jsx` — visitor trends

**Har module dashboard Recharts estefade mikone** — composable, lightweight, va consistent.

## 4) ApexCharts — template Chart component (lazy)

```jsx
// packages/ui/src/components/chart/chart.jsx
const LazyChart = lazy(() =>
    import('react-apexcharts').then(m => ({ default: m.default }))
);

export function Chart({ type, series, options, ... }) {
    const isClient = useIsClient();
    return (
        <ChartRoot>
            {isClient ? (
                <Suspense fallback={<ChartLoading />}>
                    <LazyChart type={type} series={series} options={options} width="100%" height="100%" />
                </Suspense>
            ) : (
                <ChartLoading />
            )}
        </ChartRoot>
    );
}
```

**`useChart` hook** — base config baraye ApexCharts:

```jsx
export function useChart(updatedOptions) {
    const theme = useTheme();
    const baseOptions = baseChartOptions(theme);  // colors, fonts, grid, etc.
    return merge(baseOptions, updatedOptions);     // deep merge
}
```

**Pattern:** ApexCharts config-e sangin-e (~125KB) → lazy load. `useChart` base config ro az MUI theme misaze → consistent look.

## 5) jsPDF — MRT PDF export

```jsx
// mrt-datatable.jsx (export section)
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { registerVazirmatnFont } from './Vazirmatn-Regular-normal';

registerVazirmatnFont();  // register once

const handleExportPDFRows = (rows) => {
    const exportableCols = table.getVisibleLeafColumns()
        .filter(col => col.columnDef.exportable !== false && col.id !== 'mrt-row-select' && col.id !== 'mrt-row-actions');

    // RTL: reverse column order
    const orderedCols = RTLLanguages.includes(currentLang.value)
        ? [...exportableCols].reverse()
        : exportableCols;

    const flatRows = rows.map(row =>
        orderedCols.map(col => {
            const value = row.getValue(col.id);
            if (col.columnDef.type === 'dateTime') return fDateTime(value, true);
            if (col.columnDef.type === 'boolean') return value === 'true' ? t('yes') : t('no');
            return value ?? '';
        })
    );

    const doc = new jsPDF({ orientation: 'landscape' });
    doc.setFont('Vazirmatn');

    autoTable(doc, {
        head: [orderedCols.map(col => col.columnDef.header)],
        body: flatRows,
        styles: { font: 'Vazirmatn', halign: isRTL ? 'right' : 'left' },
        headStyles: { font: 'Vazirmatn', halign: isRTL ? 'right' : 'left' },
    });

    doc.save('exported-table.pdf');
};
```

**RTL tricks:**
1. **Column order reversed** — rightmost column first to PDF (matches RTL reading)
2. **`halign: 'right'`** — text alignment
3. **Vazirmatn font** — embedded as Base64 TTF; bedun-esh glyphs break

**CSV export ham khodesh dare** — `export-to-csv` library, sade-tar chun font issue nadare.

---

## Smell-ha

1. **MapLibre lazy but large** — even lazy, 200KB for map; users ke map nadaran pay namikonan (✅ lazy handles it)
2. **TipTap HTML output** — XSS risk age render beshi bedun-e sanitize; server bayad sanitize kone
3. **Two chart libs** — bundle includes both Recharts AND Apex; could standardize
4. **Apex lazy but config eager** — `useChart` hook hamishe run mishe hata vaghti chart render nemishe
5. **Vazirmatn Base64** — ~200KB base64 font to JS bundle; lazem-e vali sangin-e
6. **No server PDF for tables** — large export (10K rows) browser-e kond mikone; server PDF behtar-e
7. **RTL column reverse dasti** — age developer faramush kone, PDF LTR neshun mide ba Farsi text → confusing
8. **MapLibre tile server dependency** — age tile server down bashe, map tohi-e; no graceful fallback
9. **CodeBlock lowlight bundle** — `lowlight` ba `common` languages ~50KB; mitune lazy she
10. **No chart accessibility** — Recharts/Apex chart-ha screen reader-friendly nistand; `aria-label` lazem-e

---

## Debug checklist

1. Map tohi neshun mide? → tile server URL dorost-e? style.json load mishe? (Network tab)
2. Editor content save nemishe? → `onChange` seda zade? HTML string mire? form submit check kon
3. Chart render nemishe? → `data` hast? `isClient` true-e? Suspense boundary dorost-e?
4. PDF Farsi tohi/☐☐☐? → `registerVazirmatnFont` seda zade? `doc.setFont('Vazirmatn')` hast?
5. PDF column order eshtebah? → `RTLLanguages.includes` dorost-e? `currentLang.value` chi-e?
6. Map crash to SSR? → `useIsClient` check dari? `typeof window` guard?
7. Editor hydration mismatch? → `immediatelyRender: false` set shode?
8. Chart loading slow? → lazy import check kon; bundle analyzer run kon

---

## 25 soal-e mosahebe

1. MapLibre chie? — **A:** open-source WebGL map renderer; fork-e Mapbox GL JS.
2. react-map-gl chie? — **A:** React wrapper baraye Mapbox/MapLibre.
3. Chera lazy load baraye map? — **A:** ~200KB bundle; load vaghti lazem-e.
4. TipTap chie? — **A:** headless rich text editor bar paye-ye ProseMirror.
5. Headless yani chi? — **A:** engine-e logic/model dare, UI nadare; developer UI misaze.
6. Extension to TipTap chi hast? — **A:** modular plugin (bold, link, image, code block, ...).
7. StarterKit chie? — **A:** bundle-e default extensions (heading, bold, italic, list, ...).
8. `onUpdate → getHTML` chie? — **A:** har change → HTML output → parent (RHF ya state).
9. Recharts vs ApexCharts? — **A:** Recharts composable/lightweight; Apex config-based/feature-rich.
10. Chera har do to Dejban? — **A:** Recharts baraye custom dashboard charts; Apex baraye template component.
11. Lazy chart chie? — **A:** ApexCharts ba `React.lazy` load mishe — initial bundle sabok.
12. `useChart` hook chikar mikone? — **A:** MUI theme → ApexCharts base config (merge ba custom options).
13. jsPDF chie? — **A:** client-side PDF generation library.
14. jspdf-autotable chie? — **A:** plugin baraye generate kardan-e table to PDF.
15. Chera Vazirmatn font embed mikoni? — **A:** default font Farsi glyph nadare → ☐☐☐.
16. RTL alignment to PDF chetori? — **A:** `halign: 'right'` + column order reverse.
17. Server PDF key vaght? — **A:** complex layout, large data, charts/images, barcode.
18. SSR safety chetori handle mishe? — **A:** `useIsClient` + conditional render (no `window` to SSR).
19. `immediatelyRender: false` chie? — **A:** TipTap editor to SSR render nemikone → no hydration mismatch.
20. XSS risk-e TipTap? — **A:** HTML output mitune malicious bashe; server sanitize bayad kone.
21. Chart accessibility? — **A:** screen reader support za'if-e; `aria-label` lazem-e.
22. MapLibre vs Google Maps? — **A:** free/open vs paid/proprietary; tile hosting khodet.
23. Module dashboard chand ta Recharts dare? — **A:** 10+ (center, traffic, weigh, contractor, cartable, HR, ...).
24. CSV export vs PDF? — **A:** CSV sade-tar (no font issue); PDF visual/printable.
25. `ReactNodeViewRenderer` chie? — **A:** TipTap API baraye render-e React component to ProseMirror node.

---

## Senario-ha

### A) User personnel ro ru-ye map bebine
Dashboard → Map component load mishe (lazy) → tile server tiles mifreste → marker-ha render mishan → click → popup ba details.

### B) User description-e ticket ro type mikone
Form → TipTap editor → user bold/link/list type mikone → `onChange` HTML → RHF store → submit → server save HTML.

### C) Module dashboard load mishe
Dashboard page → Recharts components render → API data fetch → chart update → user statistics ro mibine.

### D) User jadval ro PDF export mikone
MRT table → click "Export PDF" → `handleExportPDFRows` → jsPDF + Vazirmatn → column reverse (RTL) → `halign: right` → `doc.save('exported-table.pdf')` → browser download.

### E) Chart-e template lazy load mishe
Component ba `<Chart>` render mikone → `React.lazy(() => import('react-apexcharts'))` → Suspense fallback → chunk load → chart render.

---

## Anti-pattern-ha

```jsx
// BAD: map without SSR guard → crash
import Map from 'react-map-gl/maplibre';
export default function Page() { return <Map />; }  // SSR: window is not defined!

// GOOD: lazy + useIsClient
const LazyMap = lazy(() => import('react-map-gl/maplibre'));
function MapComponent() {
    const isClient = useIsClient();
    if (!isClient) return <Skeleton />;
    return <Suspense><LazyMap /></Suspense>;
}
```

```jsx
// BAD: load Apex on every page
import Chart from 'react-apexcharts';  // 125KB on every route!

// GOOD: lazy import
const LazyChart = lazy(() => import('react-apexcharts'));
```

```js
// BAD: PDF without Farsi font
const doc = new jsPDF();
// doc uses Helvetica → Farsi = ☐☐☐☐

// GOOD: register + set Vazirmatn
registerVazirmatnFont();
const doc = new jsPDF();
doc.setFont('Vazirmatn');
```

```jsx
// BAD: render TipTap HTML unsanitized
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// GOOD: sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userContent) }} />
```

---

## Interview 60s

> «Beyond MUI and MRT, our frontend uses MapLibre via react-map-gl for maps — lazy loaded with SSR guards. Rich text is TipTap with ProseMirror extensions, wired to React Hook Form. Module dashboards use Recharts for composable charts; the template Chart component lazy-loads ApexCharts. For PDF export from tables we use jsPDF with autotable and an embedded Vazirmatn font for Farsi RTL, reversing column order and setting right-alignment.»

---

## Resume

**kutah:**

> Integrated **MapLibre** maps, **TipTap** rich text editing, **Recharts/ApexCharts** dashboards, and client-side **jsPDF** table export with RTL Farsi font support across a multi-app monorepo frontend.

**bullet-ha:**

- MapLibre GL JS: Lazy-loaded open-source WebGL maps with react-map-gl, SSR-safe via useIsClient
- TipTap: Headless ProseMirror editor with syntax-highlighted code blocks, integrated with React Hook Form
- Recharts: Composable SVG charts for 10+ module dashboards (bar, pie, line)
- ApexCharts: Lazy-loaded template chart component with MUI theme integration via useChart hook
- jsPDF + autotable: Client-side PDF export with embedded Vazirmatn font, RTL column reversal, and right-alignment

**skill-ha:** `MapLibre · react-map-gl · TipTap · ProseMirror · Recharts · ApexCharts · jsPDF · RTL · PDF generation · lazy loading · React`

---

## File-haye mohem

| chi | koja |
|---|---|
| Map component | `packages/ui/src/components/map/map.jsx` |
| Map marker/popup | `packages/ui/src/components/map/map-marker.jsx`, `map-popup.jsx` |
| TipTap Editor | `packages/ui/src/components/editor/editor.jsx` |
| Editor toolbar | `packages/ui/src/components/editor/toolbar.jsx` |
| Chart (Apex lazy) | `packages/ui/src/components/chart/chart.jsx` |
| useChart hook | `packages/ui/src/components/chart/use-chart.js` |
| MRT datatable (PDF) | `packages/ui/src/custom-components/mrt-datatable/mrt-datatable.jsx` |
| Vazirmatn font | `packages/ui/.../mrt-datatable/Vazirmatn-Regular-normal.js` |
| Dashboard (Recharts) | `apps/dejban/src/sections/*/dashboard/*-dashboard-view.jsx` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 42 Next.js | SSR safety, lazy loading |
| 47 MUI | styled components, theme integration |
| 52 MRT | table component ke PDF export dare |
| 54 Vite AC | access-control ham map/editor dare |
| 39 Stimulsoft | server-side reporting (Day 64 architecture) |
| 43 Turbo | shared packages (map, editor, chart to `@repo/ui`) |

---

## Glossary

| kalame | ma'ni |
|---|---|
| MapLibre | open-source WebGL map renderer |
| react-map-gl | React wrapper baraye Mapbox/MapLibre |
| TipTap | headless rich text editor bar paye-ye ProseMirror |
| ProseMirror | document editing framework |
| Extension | modular TipTap plugin |
| StarterKit | bundle-e default extensions |
| Recharts | React composable SVG chart library |
| ApexCharts | config-based feature-rich chart library |
| jsPDF | client-side PDF generation |
| jspdf-autotable | jsPDF plugin baraye table |
| Vazirmatn | open-source Farsi font |
| halign | horizontal alignment to jspdf-autotable |
| RTL | Right-to-Left text direction |
| lazy loading | code splitting — load vaghti lazem-e |
| useIsClient | SSR safety hook — true vaghti to browser-i |

---

## Deep dive — font embedding size optimization

Vazirmatn Base64 ~200KB to JS bundle-e. Rah-e optimization:
1. **Subset font:** faghat glyph-haye lazem (Farsi + numbers + basic Latin) → 50-70KB
2. **Dynamic import:** font ro vaghti PDF export click mishe load kon (lazy)
3. **Woff2 az server:** font ro az URL load kon be jaye bundle

Dejban feli option 1 ro nadare — kol-e font embed shode. Baraye table-haye ke export nadarand, font load nemishe (registerVazirmatnFont faghat to mrt-datatable seda zade mishe).

---

## Deep dive — chart data flow

```
API server → useQuery/service → component state → Recharts props
                                                  → <BarChart data={state.chartData}>
```

Data transformation (reshape, aggregate) to **component** anjam mishe — API raw data mide, FE chart-ready misaze-sh. In separation-e khoob-e: API agnostic-e az UI needs.

---

## Deep dive — when NOT to use client PDF

1. **> 5000 rows** — browser memory issue; jsPDF kond mishe
2. **Charts/images to PDF** — jsPDF text/table khoob-e; chart render sakht-e
3. **Barcode/QR** — server library behtar handle mikone
4. **Consistent layout** — Stimulsoft/SSRS template → pixel-perfect
5. **Audit trail** — server PDF log mishe; client PDF bi-trace-e

Dejban baraye MRT export client PDF estefade mikone (sade, fast, no server round-trip). Baraye formal reports → Stimulsoft (Day 39/64).

---

## Self-test-e sari

1. MapLibre chera free-e? → BSD license, fork-e Mapbox
2. TipTap engine chie? → ProseMirror
3. Recharts rendering? → SVG
4. ApexCharts bundle size? → ~125KB gzip
5. Farsi PDF bedun-e font? → ☐☐☐☐
6. RTL PDF column order? → reversed
7. `halign` baraye RTL? → 'right'
8. Chera lazy load chart? → bundle size reduction
9. SSR guard map? → useIsClient
10. TipTap output format? → HTML string

Age 8/10 ya bishtar dorost bud → Day 60-67 complete.

---

## Chejori digest koni

1. MapLibre + react-map-gl concept + lazy (10 daghighe)
2. TipTap + ProseMirror + RHF (15 daghighe)
3. Recharts vs ApexCharts va karbord (10 daghighe)
4. jsPDF + Vazirmatn + RTL (15 daghighe)
5. Smell-ha + when server PDF (10 daghighe)
6. 25 soal (20 daghighe)

---

## Resume keywords (ATS)

`MapLibre` · `react-map-gl` · `TipTap` · `ProseMirror` · `Recharts` · `ApexCharts` · `jsPDF` · `RTL` · `PDF export` · `lazy loading` · `React` · `rich text editor` · `data visualization`

---

## Checklist-e nahaei

- [ ] MapLibre concept + Dejban lazy pattern
- [ ] TipTap + ProseMirror + extensions + RHF
- [ ] Recharts composable + module dashboards
- [ ] ApexCharts lazy + useChart hook
- [ ] jsPDF + autotable + Vazirmatn + RTL
- [ ] Server PDF vs client PDF
- [ ] Smell-ha (bundle size, XSS, accessibility)
- [ ] Resume bullets baraye har lib
- [ ] Interview 60s

---

*Day 67 tamum. Phase tech 60–67 complete. Fehrest: [README.md](./README.md).*
