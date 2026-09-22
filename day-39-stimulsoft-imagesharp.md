# Day 39 — Stimulsoft + ImageSharp

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Stimulsoft** = engine + designer + viewer baraye report (`.mrt` template, band, datasource, export PDF/Excel/Word/…). To Dejban microservice **Reporting** malek-e in stack-e: `Stimulsoft.Reports.Engine.NetCore` + `Web.NetCore` **2024.3.2**.

Flow kolli:

1. FE (list pages) → `ReportManagementTrigger` / quick Excel/Print  
2. Reporting **Designer** (tarahi `.mrt`) + **Viewer** (namayesh/print)  
3. `ReportRepository` data az Dejban schemas / API query bind mikone, font RTL normalize, aks guest az path → **byte[]**  
4. Export: `report.Render()` ba'd `ExportDocument(Pdf|Excel2007|…)`  
5. Ops: font Linux (DejaVu) + `/health/reporting-assets` (Day 31)

**ImageSharp (`SixLabors.ImageSharp` 3.1.12):** package to `Reporting.csproj` hast. To code-e proje **direct `using SixLabors` dida nemishe** — aks-ha bishtar raw bytes (file/URL/base64) miran to Stimulsoft Image component. WORLD ImageSharp = library-e modern resize/encode; Dejban = dependency hazer + Stimulsoft-centric image bind. Honest begu.

**Band-e gharardad-e jadid:** tozihat ravoontar va sade-tar.

---

# BAKHSH-E AVAL: WORLD

## Farz kon — chapkhune-ye gozaresh

Excel import (Day 38) = *vorud* data.  
Report = *khoruj* ziba: header sherkat, jadval, barcode, PDF chap.

Bedune tool: HTML print dasti / Crystal / SSRS.  
Stimulsoft = tarahi visual + render server/JS viewer.

---

## Stimulsoft — mafahim-e sade

| mafhum | ma'ni |
|---|---|
| **`.mrt`** | template report (XML/JSON layout) |
| **StiReport** | object runtime template+data |
| **Dictionary / DataSource** | jadval bind (DataTable, …) |
| **Band** | Header/Data/Footer |
| **Designer** | UI tarahi |
| **Viewer** | UI namayesh/print |
| **Render** | mohasebe layout ghabl export |
| **Export** | PDF, XLSX, DOCX, HTML, PNG, … |

```csharp
var report = new StiReport();
report.Load("template.mrt");
// bind data…
report.Render();
report.ExportDocument(StiExportFormat.Pdf, stream);
```

**Yani chi?** Load template → por data → Render → Export/Viewer.

---

## ImageSharp — WORLD (chera mohem-e?)

`System.Drawing` Windows-centric / legacy.  
**SixLabors.ImageSharp** = cross-platform resize, crop, encode JPEG/PNG, mutate pixels — Docker Linux dust.

Mesal WORLD:

```csharp
using var image = Image.Load(stream);
image.Mutate(x => x.Resize(800, 0));
await image.SaveAsJpegAsync(outStream);
```

**Ertebat ba report:** aks guest ke path-e MinIO/DCC-e bayad byte she; gahi resize ghabl embed. Dejban alan bishtar **load bytes** mikone; ImageSharp package reserved/transitive-ready.

---

## Chera report service joda?

Reporting: font, license Stimulsoft, heavy render CPU, wwwroot js/css viewer.  
Joda az Dejban.Api = scale/ops asun-tar (Day 09). YARP proxy routes reporting (Day 07/31 health routes).

---

# BAKHSH-E DOVOM: DEJBAN — Reporting + Stimulsoft

## Naqshe-ye yek negah

```
[FE Next] ReportManagementTrigger / QuickExport / openVisitRowStimulsoftReport
    ↓ ticket / URL (JWT query avoid)
[ApiGateway YARP] → Reporting
    ↓
DesignController  (Designer MVC + CreateAccessTicket)
ViewController    (Viewer callbacks + Export)
ReportRepository  (CreateViewerReportAsync, fonts, projectors, images)
    ↓
StiReport .mrt templates (wwwroot/templates e.g. GuestEnt.mrt)
    ↓
Render → Viewer UI ya Export file
```

---

## Qesmat 1 — Packages

| package | version |
|---|---|
| Stimulsoft.Reports.Engine.NetCore | 2024.3.2 |
| Stimulsoft.Reports.Web.NetCore | 2024.3.2 |
| SixLabors.ImageSharp | 3.1.12 |

Web.NetCore → `StiNetCoreViewer` helpers to ViewController.

---

## Qesmat 2 — Designer vs Viewer

**DesignController** `[Authorize]`:

- Pages Designer / Reports list  
- AJAX Stimulsoft save/load  
- **`CreateAccessTicket`**: opaque short-lived ticket baraye `window.open` — **JWT to query string nazan** (security)

**ViewController**:

- Load report callbacks baraye JS Viewer  
- `GetReportResult(this, report)`  
- Export endpoint: format pdf/excel/word/html/png  

**Yani chi?** Tarahi ba auth; Viewer popup ba ticket; export server-side Render+Export.

---

## Qesmat 3 — ReportRepository (qalb)

File bozorg — mas'uliat-ha:

| area | chikar |
|---|---|
| Registry | `ReportRegistryOptions` modules/entities/params |
| Designer report | CreateDesignerReportAsync — columns az DB |
| Viewer report | CreateViewerReportAsync — data + query filters |
| Fonts | `NormalizeReportFonts` Tahoma↔DejaVu |
| RTL | `EnsureReportFilledDataRtl` |
| Exit slip | GuestEnt.mrt + VisitExitSlipProjector |
| Legacy quick | Unit_Vehicle / Personel templates |
| Images | `EnrichHstPicWithImageBytes`, logo bytes |
| Export path | via controller Render |

**ReportRegistry** (Options Day 34): moduleId → DbContext/schema; entityId → table/DataUrl/parameters (`fromDate`, …).

---

## Qesmat 4 — Export (daqiq)

```csharp
report = await _repository.CreateViewerReportAsync(…);
report.Render(); // الزامی ghabl export

switch (format) {
  case "excel": ExportDocument(Excel2007); …
  case "word":  Word2007; …
  case "html":  Html5; …
  case "png":   ImagePng; …
  default:      Pdf; …
}
return File(stream, contentType, fileName);
```

**Chera Render avval?** Stimulsoft comment: bedune Render export eshtebah/khali.

FE `getReportExportUrl` / `ReportQuickGridExports` — Excel sari' az grid filters.

---

## Qesmat 5 — Fonts + Linux Docker (ops)

Windows designer: Tahoma.  
Container Linux: Tahoma nist → tofu/blank PDF.

```csharp
// ServiceCollectionExtensions — register font files
StiFontCollection.AddFontFile("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf");
…
NormalizeReportFonts → family = Windows? "Tahoma" : "DejaVu Sans"
```

**Health:** `GET /health/reporting-assets` — js/css/lib counts + font candidates exist.  
Gateway `/health/reporting-routes` (Day 31) — YARP paths.

**Yani chi mosahebe?** «Reports need font packs in the image; we health-check assets.»

---

## Qesmat 6 — Images to Stimulsoft (bedune ImageSharp API)

Comment code: *Stimulsoft needs image bytes, not a storage path.*

`TryLoadPublicFileBytes`:

1. `data:image…;base64,…` decode  
2. Absolute http(s) download  
3. Normalize path → Gateway `/files/{…}` (Day 28 public)  
4. Fallback local paths  

`EnrichHstPicWithImageBytes` — column `HstPic` az string → `byte[]` baraye Image band GuestEnt.

Logo Dejban ham bytes.

**ImageSharp role emruz:** package declared; processing pipeline app-level mostaghim nist — mitune ba'd resize ezafe she. Na claim false «we resize with ImageSharp everywhere.»

---

## Qesmat 7 — Visit exit slip (mesal business)

`openVisitRowStimulsoftReport(row)` FE → Viewer.  
BE: project visit row → `Tb_HstView` columns GuestEnt.mrt; photo enrich; A5 layout helpers; font size fix «B Nazanin» empty → readable.

**Yani chi?** Template legacy + projector adapter modern API data.

---

## Qesmat 8 — FE surface

| piece | naqsh |
|---|---|
| `REPORT_MODULES` | moduleId/entityId map per page |
| `ReportManagementTrigger` | open designer/manage |
| `ReportQuickGridExports` | Excel export quick |
| `ReportQuickPrint` | viewer print |
| `report.service.js` | createTabularReport, URLs |
| Guards | permission componentIds |

List views: staff, vehicle, visits, access logs, armory, … hame trigger.

---

## Qesmat 9 — Auth ticket pattern

`window.open(viewerUrl)` nemitune Authorization header bezane asan.  
Options: JWT query (leak referrer/logs) ya **opaque ticket** short TTL store server-side.  
Dejban: `CreateAccessTicket` — behtar.

---

## Se dastan (farz kon)

### A) Excel export az grid staff

Filters FE → create tabular / export URL → Reporting Render Excel2007 → download xlsx.

### B) Chap barghe vorud mosafer

Row visit → Viewer GuestEnt → photo bytes → print PDF/browser.

### C) Docker PDF khali font

Font package missing → health reporting-assets red → install DejaVu → OK.

### D) Designer save

User layout save `.mrt` / DB metadata — DesignController recover report name az Referer (Stimulsoft AJAX quirk).

---

## Smell-ha

1. `ReportRepository` god class (1000s lines)  
2. Console.WriteLine debug leftover  
3. ImageSharp referenced unused directly — confusion  
4. Font Windows vs Linux drift layouts  
5. Ticket + cookie + JWT — auth surface complex  
6. Heavy render sync on request — timeout large data  
7. DataCacheSeconds registry — stale risk  
8. Legacy mrt column names fragile  
9. License Stimulsoft commercial — ops key  
10. Anonymous health assets — OK; don't expose designer  
11. Export without row limit — DoS  
12. Dual FE query builders  

---

## Debug checklist

1. `/health/reporting-assets` fonts/js?  
2. YARP reporting routes?  
3. Ticket expired?  
4. Render before export?  
5. HstPic path → bytes empty log?  
6. Module/entity id mismatch REPORT_MODULES?  
7. Culture/RTL wrong?  
8. Template file missing wwwroot/templates?  
9. SiteId / access token fallback on viewer?  
10. Stimulsoft license valid?  

---

## 25 soal-e mosahebe

1. Stimulsoft chie?  
2. .mrt?  
3. Render vs Export?  
4. Designer vs Viewer?  
5. Chera Reporting joda?  
6. Export formats Dejban?  
7. CreateAccessTicket chera?  
8. ReportRegistryOptions?  
9. NormalizeReportFonts?  
10. DejaVu chera?  
11. reporting-assets health?  
12. Image path → bytes chera?  
13. ImageSharp to proje?  
14. GuestEnt / exit slip?  
15. FE ReportQuickGridExports?  
16. StiNetCoreViewer?  
17. RTL ensure?  
18. DataCacheSeconds?  
19. Smell god repository?  
20. Excel export vs Day 38 import?  
21. Public /files photo?  
22. License?  
23. Parameters fromDate?  
24. Docker font fail symptom?  
25. Resume 60s?

---

## Senario-ha

### A) Export pdf default

format null → Pdf.

### B) Photo missing

bytes empty → blank image box; log path.

### C) Quick excel no designer

createTabularReport + export — user layout fixed/default.

### D) Linux tofu characters

font not registered — health + AddFontFile.

---

## Mini lab

1. Reporting.csproj packages  
2. ViewController export switch  
3. Font registration + HealthController  
4. TryLoadPublicFileBytes skim  
5. DesignController CreateAccessTicket  
6. FE report-quick-excel-export  
7. GuestEnt / VisitExitSlipProjector names  
8. ReportRegistryOptions section  

---

## Resume

**kutah:**

> Delivered operational reporting on Stimulsoft.NET 2024 in the Reporting microservice: designer/viewer with access tickets, registry-driven modules/entities, server-side Render/Export (PDF/Excel/Word/HTML/PNG), Linux font registration and asset health checks, and image binding by resolving storage paths to bytes for templates like guest exit slips—with ImageSharp packaged alongside for cross-platform image work.

**bullet-ha:**

- Integrated Stimulsoft Engine/Web NetCore for design, view, and multi-format export  
- Normalized RTL fonts (Tahoma/DejaVu) and health-checked wwwroot + fonts  
- Bound report photos/logos via byte enrichment from public files/gateway; FE triggers across grids  

**skill-ha:** `Stimulsoft, Reporting, PDF export, Report designer, Image handling, ImageSharp, Docker fonts, ASP.NET MVC, YARP`

---

## File-haye mohem

| chi | koja |
|---|---|
| Packages | `Reporting.csproj`, Directory.Packages.props |
| Viewer/Export | `Controllers/ViewController.cs` |
| Designer/Ticket | `Controllers/DesignController.cs` |
| Core logic | `Infrastructure/ReportRepository.cs` |
| Registry | `ReportRegistryOptions.cs` |
| Fonts DI | `ServiceCollectionExtensions` |
| Health | `HealthController.cs` |
| Templates | `wwwroot/templates/*.mrt` |
| FE | `sections/reports/stimulsoft/*` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 07 YARP | reporting proxy |
| 28 MinIO | /files photos |
| 31 Health | reporting-assets |
| 34 Options | ReportRegistry |
| 38 Excel | export vs import |
| 16 Site | site filters reports |
| 06 JWT | ticket vs query token |

---

## Chejori digest koni

1. WORLD Stimulsoft + ImageSharp (20 min)  
2. Designer/Viewer/Ticket (20 min)  
3. Export Render (15 min)  
4. Fonts + health (15 min)  
5. Image bytes path (15 min)  
6. FE triggers (15 min)  
7. 25 soal (20 min)  

---

## Glossary

| kalame | ma'ni |
|---|---|
| Stimulsoft | report engine commercial |
| mrt | template file |
| Render | layout compute |
| Export | file output format |
| Viewer | display UI |
| Designer | authoring UI |
| DataSource | bound table |
| ImageSharp | .NET image lib |
| Font substitution | Tahoma→DejaVu |
| Access ticket | opaque viewer auth |

---

## Deep dive — Render ghabl Export

Bedune Render, bandha calculate nashode — Excel/PDF empty/wrong.  
Viewer internally render mikone; export API must explicit.

---

## Deep dive — Registry parameters

Entity `Parameters: ["fromDate","toDate"]` → UI collect → query string → repository filter SQL/API.  
Flexible per module bedune hardcode hame reports.

---

## Deep dive — ImageSharp honesty paragraph (seda kon)

«Reporting references SixLabors.ImageSharp. Our current photo pipeline loads bytes for Stimulsoft directly from public file URLs or base64. ImageSharp is the standard tool we’d use for resize/re-encode if we harden that pipeline; Stimulsoft does the report-side image display.»

---

## Anti-pattern

```csharp
// BAD: ExportDocument without Render
// GOOD: Render then Export (Dejban)

// BAD: put JWT in viewer query forever
// GOOD: short-lived access ticket

// BAD: assume Tahoma on Linux
// GOOD: register DejaVu + health check

// BAD: bind image path string to StiImage expecting file on server disk only
// GOOD: enrich byte[] column (Dejban)
```

---

## Interview 60s

> «Reporting is a Stimulsoft.NET service: designers save mrt layouts, viewers open via short-lived access tickets, and exports call Render then ExportDocument for PDF/Excel/Word/HTML/PNG. We map modules/entities through ReportRegistry options, fix RTL fonts for Linux with DejaVu, health-check static assets, and convert guest photo paths into byte arrays so Stimulsoft can render images. ImageSharp is referenced for cross-platform imaging alongside that stack.»

---

## Quick self-test

1. Service? → Reporting  
2. Stimulsoft version? → 2024.3.2  
3. Export need Render? → yes  
4. Ticket chera? → no JWT in URL  
5. Linux font? → DejaVu  
6. Health path? → /health/reporting-assets  
7. HstPic? → bytes enrich  
8. ImageSharp direct code? → no/rare  
9. FE quick excel? → ReportQuickGridExports  
10. Guest template? → GuestEnt.mrt  

---

## Final checklist

- [ ] Stimulsoft concepts  
- [ ] Designer/Viewer/Export  
- [ ] Fonts+health  
- [ ] Image bytes  
- [ ] ImageSharp honest  
- [ ] FE  
- [ ] Resume  

---

## Extra — Farz kon report 50k rows

Render memory/CPU spike.  
Mitigate: filter required, paging server, async job+download (Hangfire Day 29), timeout gateway.  
Alan: interactive mid-size grids.

---

## Extra — Culture fallback

View/Design ApplyCultureFallback — Persian dates/UI Stimulsoft.  
Wrong culture → number/date format odd.

---

## Extra — SiteId / AccessToken fallback on viewer

Viewer requests may lose headers; controller fallbacks az query/form — pragmatic Stimulsoft JS.  
Security: ticket still gate.

---

## Extra — Commercial license

Stimulsoft key to config/env — prod fail without.  
Mosahebe: «licensed third-party reporting.»

---

## Map — Quick Excel

```
FE filters → createTabularReport / getExportUrl
→ Reporting builds StiReport + data
→ Render → Export Excel2007
→ browser download
```

---

## Map — Exit slip print

```
FE row → open viewer URL (+ticket)
→ CreateViewerReportAsync exit slip path
→ EnrichHstPic bytes + layout tweaks
→ StiNetCoreViewer result
→ user print
```

---

## Lab aha

1. Break font in Docker — see PDF  
2. Null HstPic — blank photo  
3. Export without Render mentally  
4. Open CreateAccessTicket — TTL  
5. Grep ImageSharp usings — empty  

---

## What Day 39 is *not*

- Full Stimulsoft designer tutorial  
- Crystal/SSRS compare deep  
- ImageSharp filter pipeline cookbook  

Focus: **Dejban Reporting Stimulsoft ops + image/font reality + ImageSharp context**.

---

## Resume keywords

`Stimulsoft` · `Report designer` · `PDF` · `Excel export` · `ImageSharp` · `RTL` · `Docker fonts` · `ASP.NET` · `Reporting microservice`

---

## Band-e gharardad-e jadid

Ravoon: chapkhune metaphor; Render chera; fonts Linux dastan; ImageSharp honest; ticket vs JWT query.

---

## 10 jomle fluency

1. Stimulsoft = report engine Dejban Reporting.  
2. mrt template + StiReport runtime.  
3. Render ghabl Export.  
4. Designer tarahi; Viewer namayesh.  
5. Access ticket beja-ye JWT query.  
6. Fonts DejaVu Linux + health.  
7. Photos path→byte[] for Stimulsoft.  
8. ImageSharp package; direct use kam.  
9. FE triggers roye list grids.  
10. Registry Options modules/entities.

---

## Extra — Export vs Import Excel

Day 38 import ClosedXML wizard.  
Day 39 export Stimulsoft Excel2007 — layout report, na template HR.  
Har do «Excel» — maqsad mokhalef.

---

## Extra — Barcode / components

ReportRepository imports StiBarCodes — some layouts barcode.  
Skim when debugging print labels.

---

## Extra — wwwroot js/css/lib

Stimulsoft JS viewer assets — health counts files.  
Missing after bad Docker copy → viewer blank; health catches.

---

## Extra — Farz kon user «Gozaresh» mizane az list

1. Guard permission OK  
2. `createTabularReport` ya default report id  
3. `CreateAccessTicket` POST  
4. `window.open` viewer URL ba ticket  
5. Viewer JS → ViewController GetReport callbacks  
6. Data bind + fonts + images  
7. User print / export az viewer toolbar  

**Yani:** FE thin; Reporting thick.

---

## Extra — Module/Entity id sync FE↔BE

`REPORT_MODULES` constants must match `ReportRegistry` / DB seed ids.  
Mismatch → NotFound / wrong schema.  
Smell: dual source — document change process.

---

## Extra — Projectors pattern

`VisitExitSlipProjector`, `LegacyQuickReportProjector`, `VisitGridProjector` — API JSON/grid → DataTable column names template expects.  
**Adapter** beyn modern API va legacy mrt.  
Strategy-ish per report kind (Day 35 vibe).

---

## Extra — CalculationMode Interpretation

Exit slip sets `StiCalculationMode.Interpretation` — expressions evaluate certain way.  
Agar text `{Tb_HstView.X}` bind fail → check NameInSource `t.Tb_HstView` quirks in comments.

---

## Extra — Security surface

| surface | note |
|---|---|
| Designer | Authorize |
| Viewer ticket | short TTL opaque |
| Export | auth + same data rules |
| Health assets | anonymous OK |
| /files photos | public path policy Day 28 |

Don't expose raw SQL from designer to anonymous.

---

## Extra — Performance knobs

- `DataCacheSeconds` registry (default 120)  
- Filter params required  
- Avoid full table export  
- Consider async export job later  

---

## Extra — ImageSharp kabayan useful?

| use case | ImageSharp |
|---|---|
| Resize guest photo 4K → 800px ghabl embed | yes |
| Strip EXIF | yes |
| Convert HEIC→JPEG | yes (format support) |
| Stimulsoft display | bytes enough |

Pipeline pishnahad mosahebe: load → ImageSharp mutate → byte[] → DataTable.

---

## Extra — Soalat chera

**Chera microservice joda?** CPU/fonts/license isolation.  
**Chera ticket?** window.open header limit.  
**Chera byte not path?** Stimulsoft image bind + Docker path hell.  
**Chera health fonts?** silent bad PDF.  
**Chera Render?** export correctness.

---

## Extra — Compare Crystal/SSRS (yek jomle)

Legacy Windows stack; Stimulsoft .NET Core + JS viewer = Docker-friendly Dejban choice.

---

## Extra — YARP reporting static

js/css/lib routes gateway (Day 31 health reporting-routes) — Viewer assets az Gateway.  
Misconfig → 404 scripts → blank viewer.

---

## Extra — Test ideas

- Unit projector column mapping  
- Integration export PDF magic bytes `%PDF`  
- Health fonts in CI image  
- Ticket expire → 401  

---

## Extra — Endpoint mental map

| Controller | naqsh |
|---|---|
| DesignController | Designer UI, save/load, CreateAccessTicket |
| ViewController | Viewer AJAX, export formats |
| HealthController | reporting-assets |

---

## Khoruj-e zehni

> Midunam Reporting ba Stimulsoft designer/viewer/export kar mikone, Render lazeme, font Linux + health mohem-e, aks ba byte bind mishe, ticket auth baraye popup, va ImageSharp package hast ama pipeline asli raw bytes-e. FE az grid-ha report trigger mikone.

Age in paragraph mal-e to shod — Day 39 done.

---

*Day 39 tamum. Ba'd: Day 40 — Auth end-to-end (amade). Fehrest: [README.md](./README.md).*
