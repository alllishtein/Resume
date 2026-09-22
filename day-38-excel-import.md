# Day 38 — Excel import

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Excel import = karbar ye `.xlsx` por mikone (ya template download), system mikhone, **validate** mikone, **preview** mide, eslah mikone, ba'd **commit** be DB.

**Gold path Dejban — Personnels:**

1. `GET ImportTemplate` → `personnel-import-template.xlsx` (ClosedXML)  
2. `POST ImportFromExcel/Preview` (multipart file) → parse + `PersonnelImportPlanner` → session in-memory (`importId`)  
3. FE jadval preview; `PUT UpdateRow` eslah  
4. `POST Revalidate` → Plan dobare  
5. `POST Commit` → Create personnel + upload avatar/signature be DCC  

Library: **ClosedXML** (xlsx + pictures) + jayja **ExcelDataReader** (xls / Vehicles / Identity Units).

Digar: Vehicles BulkImport, Identity `ImportUnitsAsExcel`, FE `StaffExcelImportDialog` + Guard `staffImportExcelButton`.

**Band-e gharardad-e jadid:** tozihat ravoontar va sade-tar.

---

# BAKHSH-E AVAL: WORLD — chera Excel import sakht-e?

## Farz kon — list HR to Excel

HR 200 nafar to Excel dare. Dasti form = dard. Import = batch.

Ama:

| moshkel | chera |
|---|---|
| Header typo | «کدملی» vs «کد ملی» |
| Lookup name | «مرکز تهران» vs SiteId Guid |
| Duplicate national code | conflict DB |
| Date Jalali/Gregorian | parse |
| Image to cell | ClosedXML drawings |
| Partial fail | 199 OK 1 bad — che konim? |
| Huge file | memory / timeout |

**Pattern-e profesionals:** **Preview → Fix → Commit** (na direct insert silent).

---

## Library landscape (.NET)

| lib | notes |
|---|---|
| **ClosedXML** | xlsx friendly API; Dejban Personnels+Vehicles |
| **ExcelDataReader** | read xls/xlsx stream; Units + Vehicles legacy xls |
| EPPlus | commercial license newer |
| NPOI | Java port |

Dejban: ClosedXML **0.105.1**, ExcelDataReader **3.9.0** (`Directory.Packages.props`).

---

## Olgu-ye session import

```
Upload → Parse rows → Validate/Plan → Store session (temp)
→ User edits invalid rows → Revalidate
→ Commit only if all valid (ya policy)
→ Clear session
```

**Yani chi?** Commit idempotent-ish ba status `Committed`; preview stateful ba `importId`.

---

# BAKHSH-E DOVOM: DEJBAN — Personnels (asli)

## Naqshe-ye flow

```
[FE] download template
[FE] pick xlsx → FormData
    POST …/ImportFromExcel/Preview
[BE] PersonnelExcelImporter.ReadRows (ClosedXML)
[BE] Mapper → PersonnelImportSession
[BE] PersonnelImportPlanner.PlanAsync (lookup + rules)
[BE] PersonnelImportSessionStore.Set (memory, 2h TTL)
    ← importId + rows (IsValid, ErrorMessage, Action)
[FE] edit cell → PUT UpdateRow
[FE] Revalidate → POST Revalidate
[FE] Commit → POST Commit
[BE] Plan again → reject if any invalid
[BE] Personnel.CreateAsync + UoW + DccHttpClient images
```

Endpoints: `ImportPersonnelsFromExcel` IEndpoint — Preview `DisableAntiforgery` (multipart).

---

## Qesmat 1 — Template

`PersonnelImportTemplate.Build()` + `GET /Personnels/ImportTemplate` → File xlsx.

Headers (Farsi) az `PersonnelExcelImporter.TemplateHeaders`:

کد پرسنلی، نام، نام خانوادگی، کد ملی، … مرکز، واحد، شناسه تردد، مقطع/رشته، عکس، امضا، …

**Chera template?** Kamtar header mismatch; FE `downloadStaffImportTemplate` blob download.

---

## Qesmat 2 — Parse: `PersonnelExcelImporter`

- ClosedXML workbook / worksheet  
- Header aliases: Farsi + English (`nationalcode`, `firstname`, …)  
- Cell → string fields  
- **Pictures:** avatar/signature az drawings cell — max **5MB**  
- Gender / dates raw string (parse to Planner)

**Yani chi?** Import = na faqat text; media to Excel support.

Error file → `PersonnelImport.InvalidFile`. Empty → `PersonnelImport.Empty`.

---

## Qesmat 3 — Session model

```csharp
PersonnelImportSession {
  Id, Status (Previewed|Committed), FileName, CreatedAt, Rows[]
}
PersonnelImportSessionRow {
  editable strings…,
  images bytes…,
  IsValid, ErrorMessage, Action,  // planning
  SiteId, UnitId, … resolved Guids,
  ParsedGender, ParsedDateOfBirth, …
}
```

**Action** mesal `"Create"` — Planner decide (duplicate → error na update, check code).

---

## Qesmat 4 — Session store (mohem / smell)

```csharp
ConcurrentDictionary<Guid, PersonnelImportSession>
Expiration = 2 hours
```

**Yani chi?** Session **in-process memory** — na Redis/DB.

| OK | moshkel |
|---|---|
| Dev single instance | multi-pod: Preview on A, Commit on B → SessionNotFound |
| sari' | restart app → gom |

Mosahebe: «preview session is in-memory with 2h TTL; sticky session or distributed store would be needed at scale.»

---

## Qesmat 5 — Planner

`PersonnelImportPlanner` load lookups: Sites, Units(+SiteId), EmploymentType/Status, Position, Degree, Major, Contracts, existing NationalCodes…

Per row:

- required fields  
- resolve name → Id (site/unit match)  
- unit belongs to site?  
- parse gender/dates/access code  
- duplicate national code → invalid  
- set `IsValid` / `ErrorMessage` / resolved IDs / `Action`

**Yani chi?** Excel *name-based*; DB *id-based*. Planner = bridge + validation domain-lite.

Revalidate & Commit **dobare Plan** — data DB shayad avaz shode.

---

## Qesmat 6 — UpdateRow / Revalidate / Commit

**UpdateRow:** field-haye string session row avaz (FE edit).

**Revalidate:** `PlanAsync` + return preview jadid.

**Commit:**

1. Session exist? not already Committed?  
2. PlanAsync  
3. Age har invalid → `PersonnelImport.HasErrorRows` — **reject all** (no partial)  
4. Foreach valid Create → `Personnel.CreateAsync` + employment history  
5. SaveChanges  
6. Avatar/Signature → `DccHttpClient.UploadFileAsync` (Day 28)  
7. Mark session Committed  

**Chera all-or-nothing baraye error rows?** Consistency UX — user fix konad. (Valid rows wait.)

---

## Qesmat 7 — FE

- `ExcelImportButton` + Guard `staffImportExcelButton` (Day 37)  
- `StaffExcelImportDialog` — dropzone xlsx, preview table, chips, commit  
- `staff.http.js`: preview / getPreview / updateRow / revalidate / commit / template  

**Yani chi:** full wizard UI, na silent upload.

---

## Digar import-ha (kholase)

### Vehicles BulkImport

ClosedXML + ExcelDataReader (xlsx/xls).  
Resolvers: ownership, site, personnel.  
Commit command — shabih bulk; check Preview/Commit pattern to module.

### Identity Units

`UnitImportPlanner.ReadExcel` ba **ExcelDataReader** — hierarchical units plan.

### Reporting

Stimulsoft **export** Excel — import nist (Day 39).

---

## Se dastan (farz kon)

### A) Happy path

Template → 50 row valid → Preview green → Commit → 50 personnel + photos DCC.

### B) Bad site name

Planner ErrorMessage «مرکز یافت نشد» → FE edit SiteName → Revalidate → Commit.

### C) Commit after 3h

Session expired → SessionNotFound → upload dobare.

### D) Two API instances

Preview→instance1, Commit→instance2 → fail. Smell memory store.

---

## Smell-ha

1. In-memory session multi-instance  
2. Session holds image bytes — RAM  
3. Commit sequential SaveChanges per row — slow bulk  
4. All-or-nothing vs partial commit debate  
5. Name matching fragile (spacing/typo)  
6. No virus scan upload  
7. Max rows? (check validators)  
8. Jalali date ambiguity  
9. Header alias incomplete → silent empty column  
10. AlreadyCommitted — good; double-click FE?  
11. DisableAntiforgery Preview — auth still; CSRF tradeoff multipart  
12. Two Excel libs — cognitive load  

---

## Debug checklist

1. Template headers exact?  
2. Preview error InvalidFile — xls vs xlsx?  
3. SessionNotFound — TTL / instance  
4. HasErrorRows — kodom ErrorMessage  
5. Lookup name mismatch Site/Unit  
6. Duplicate NationalCode  
7. Image too big 5MB  
8. DCC upload fail ba'd create? (order code)  
9. Permission staffImportExcelButton  
10. Multipart field name `file`  

---

## 25 soal-e mosahebe

1. Chera preview ghabl commit?  
2. ClosedXML vs ExcelDataReader?  
3. Personnels endpoints?  
4. Template chera?  
5. Header aliases?  
6. Planner chikar?  
7. Session store koja?  
8. TTL?  
9. Multi-instance smell?  
10. UpdateRow / Revalidate?  
11. Commit reject invalid?  
12. Images chejori?  
13. DCC ertebat?  
14. Action Create?  
15. FE Guard?  
16. DisableAntiforgery?  
17. Vehicles import?  
18. Units import?  
19. Idempotent commit?  
20. Memory images?  
21. Name→Id resolve?  
22. Partial import?  
23. Max image size?  
24. FormData field?  
25. Resume 60s?

---

## Senario-ha

### A) Empty sheet

Empty validation.

### B) Duplicate in file + DB

Planner marks invalid.

### C) Unit wrong site

Validation unit.SiteId ≠ row.SiteId.

### D) Revalidate ba'd master data add

Site jadid ezafe → Revalidate OK.

---

## Mini lab

1. Read ImportPersonnelsFromExcel endpoints  
2. Skim PersonnelExcelImporter headers + ReadRows  
3. SessionStore TTL  
4. Planner PlanAsync start  
5. Commit handler Create + DCC  
6. FE staff.http import functions  
7. Grep ClosedXML / ExcelDataReader usages  

---

## Resume

**kutah:**

> Implemented Excel bulk onboarding for Personnels with ClosedXML: downloadable templates, multipart preview into an in-memory import session, name-to-id planning/validation, row edit + revalidate, and commit that creates aggregates and uploads embedded photos/signatures to DCC—plus related bulk flows for Vehicles and Identity units using ClosedXML/ExcelDataReader.

**bullet-ha:**

- Built preview→fix→revalidate→commit API for personnel Excel import  
- Parsed bilingual headers and cell images via ClosedXML; planned lookups against sites/units/positions  
- Wired FE import dialog with permission guard and template download  

**skill-ha:** `ClosedXML, ExcelDataReader, Bulk import, File upload, Validation, ASP.NET Minimal APIs, DDD aggregates, UX wizards`

---

## File-haye mohem

| chi | koja |
|---|---|
| Endpoints | `…Presentation/Personnels/ImportPersonnelsFromExcel.cs` |
| Importer | `PersonnelExcelImporter.cs` |
| Planner | `PersonnelImportPlanner.cs` |
| Session | `PersonnelImportSession*.cs` + Store |
| Handlers | Preview/Update/Revalidate/Commit* |
| Template | `PersonnelImportTemplate.cs` |
| FE dialog | `staff-excel-import-dialog.jsx` |
| FE http | `staff.http.js` |
| Vehicles | `Modules/Vehicles/…/BulkImport/` |
| Units | `IdentityServer/…/ImportUnitsAsExcel/` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 17 Minimal + antiforgery | Preview multipart |
| 12 DDD | Personnel.CreateAsync |
| 28 MinIO/DCC | avatar upload |
| 37 Permission | staffImportExcelButton |
| 11 ErrorOr | import errors |
| 14 UoW | SaveChanges commit |
| 39 Stimulsoft | export Excel (mirror) |

---

## Chejori digest koni

1. WORLD preview pattern (15 min)  
2. Endpoints + FE wizard (20 min)  
3. Importer + headers/images (20 min)  
4. Planner + session store (25 min)  
5. Commit + DCC (15 min)  
6. Smells multi-instance (10 min)  
7. 25 soal (20 min)  

---

## Glossary

| kalame | ma'ni |
|---|---|
| Preview | parse+validate bedune persist final |
| Commit | apply to DB |
| Session | temp state importId |
| Planner | resolve+validate rows |
| Template | empty xlsx ba headers |
| Header alias | chand esm → yek field |
| ClosedXML | xlsx library |
| Bulk import | chand entity yekja |

---

## Deep dive — cherа Plan dobare on Commit?

Bein Preview va Commit: kas digar haman national code sakht; site rename.  
Plan dobare = fresh truth. Cost = DB reads; safety >.

---

## Deep dive — images in xlsx

Excel drawings linked to cells; ClosedXML `XLPicture` / worksheet Pictures.  
Bytes to session → Commit stream to DCC.  
Fail upload: check handler — personnel shayad created; compensate? smell.

---

## Deep dive — ClosedXML vs ExcelDataReader

| | ClosedXML | ExcelDataReader |
|---|---|---|
| Write template | easy | no |
| Pictures | yes | weak |
| Old .xls | no | yes |
| API | workbook OO | reader forward |

Vehicles ReadXlsx ClosedXML, ReadXls ExcelDataReader — format fork.

---

## Anti-pattern

```csharp
// BAD: insert while reading Excel, no preview
// GOOD: preview session + commit (Dejban)

// BAD: trust Excel SiteId Guid from HR
// GOOD: name resolve + validate

// BAD: memory session on farm bedune sticky
// GOOD: Redis/DB session store
```

---

## Interview 60s

> «Personnel Excel import is a wizard: users download a ClosedXML template, upload for Preview which parses rows—including cell images—runs a planner that resolves site/unit/position names and validates duplicates, stores an in-memory session for two hours, lets the UI edit and revalidate rows, then Commit creates Personnel aggregates and uploads photos to DCC only if every row is valid. Vehicles and units have related bulk readers with ClosedXML/ExcelDataReader.»

---

## Quick self-test

1. Lib Personnels? → ClosedXML  
2. Steps? → Preview Edit Revalidate Commit  
3. Session? → memory ConcurrentDictionary 2h  
4. Planner? → name→Id + rules  
5. Invalid on commit? → reject  
6. Images? → drawings → DCC  
7. Template route? → ImportTemplate  
8. FE guard? → staffImportExcelButton  
9. Units lib? → ExcelDataReader  
10. Multipart antiforgery? → disabled on Preview  

---

## Final checklist

- [ ] Preview pattern  
- [ ] Endpoints  
- [ ] Importer/Planner/Store  
- [ ] Commit+DCC  
- [ ] FE  
- [ ] Smells  
- [ ] Resume  

---

## Extra — Farz kon 5000 row

Memory session + images = pressure.  
Better: stream validate, blob storage session, background Hangfire commit (Day 29), progress SignalR (Day 26).  
Alan: interactive mid-size HR lists.

---

## Extra — Security

Auth required hame endpoints.  
Permission button FE; API bayad endpoint/permission claim ham dashte bashe (Day 37).  
File type: trust extension + ClosedXML parse fail.  
PII to Excel — audit/log careful.

---

## Extra — i18n headers

Template Farsi; aliases English.  
FE i18n labels preview columns — map to API field names.

---

## Map — Preview handler

```
Open stream → ReadRows
Empty? error
New session + map rows
PlanAsync
Store
Return DTO (importId, counts, rows)
```

---

## Map — Commit handler

```
Get session
Already committed? conflict
PlanAsync
Any !IsValid? conflict
For each Create row:
  Personnel.CreateAsync…
  Insert + SaveChanges
  Upload avatar/signature DCC
Status = Committed
Return counts
```

---

## Lab aha

1. Download template — open headers  
2. Break site name — see ErrorMessage  
3. Fix UpdateRow + Revalidate  
4. Wait/fake expire session  
5. Compare Vehicles BulkImportExcelReader  

---

## What Day 38 is *not*

- Full ClosedXML chart API  
- Google Sheets  
- CSV-only pipeline  
- Stimulsoft export deep (Day 39)  

Focus: **Excel import wizard Personnels + siblings**.

---

## Resume keywords

`ClosedXML` · `ExcelDataReader` · `Bulk import` · `File upload` · `Validation` · `Preview/Commit` · `ASP.NET Core` · `DDD`

---

## Band-e gharardad-e jadid

Tozihat ravoon: HR dastan; preview chera; memory session honest; Plan dobare.

---

## 10 jomle fluency

1. Import = Preview→Fix→Commit.  
2. ClosedXML xlsx + pictures.  
3. Template download kam header error.  
4. Planner name→Guid + validate.  
5. Session memory 2h — scale smell.  
6. Revalidate = Plan dobare.  
7. Commit all valid ya reject.  
8. Images → DCC ba'd create.  
9. FE dialog + permission guard.  
10. Vehicles/Units variants.

---

## Extra — Error codes yadbegir

`PersonnelImport.InvalidFile` · `Empty` · `SessionNotFound` · `AlreadyCommitted` · `HasErrorRows`

FE map i18n.

---

## Extra — Unit of Work per row

Har Create SaveChanges — fail mid-loop = partial DB.  
Smell vs single transaction hame creates. Tradeoff memory/timeout. Interview aware.

---

## Extra — Farz kon HR file az Excel 2003 (.xls)

Personnels path ClosedXML → xlsx expect.  
Vehicles `BulkImportExcelReader` do branch: ReadXlsx / ReadXls.  
Units ExcelDataReader.  
**Yani:** format policy per feature — document to user «xlsx only» baraye staff.

---

## Extra — Column mapping table (zehni)

| Excel header | Session field | Resolve |
|---|---|---|
| کد پرسنلی | PersonnelCode | unique business |
| کد ملی | NationalCode | duplicate check |
| مرکز | SiteName | → SiteId |
| واحد | UnitName | → UnitId + site match |
| سمت | PositionName | → PositionId |
| عکس | AvatarImageBytes | DCC upload |

Planner por mikone Id columns; Commit az Id estefade.

---

## Extra — FE dialog states (ravoon)

1. Idle — download template + dropzone  
2. Uploading preview  
3. Preview table — red rows ErrorMessage  
4. Editing — UpdateRow debounce/save  
5. Revalidating  
6. Committing — disable double click  
7. Done — onRefetch list  

Cancel mid-way = session expire later; no explicit delete API lazeme (TTL).

---

## Extra — Chera na pure CSV?

CSV: image nadare, encoding Excel Persian dard, types weak.  
Xlsx: HR familiar + pictures. Cost: binary lib.

---

## Extra — Validation layers

| layer | mesal |
|---|---|
| File | empty, corrupt |
| Row required | FirstName empty |
| Format | date/gender/accessCode |
| Referential | site/unit exist |
| Business | duplicate national |
| Commit gate | errorCount==0 |

FluentValidation on commands (ImportId) + Planner domain rules.

---

## Extra — ACLUserIdGenerator on Create

Commit `Personnel.CreateAsync(…, aclUserIdGenerator, …)` — access identity for devices (Day 35 sync ba'd).  
Import faghat HR data nist; ACL id allocate.

---

## Extra — Concurrent two imports same user

Do importId joda to dictionary.  
Commit hardo — duplicate national: dovomi Plan fail. OK.

---

## Extra — Observability

Log importId, fileName, row counts, commit duration.  
Seq (Day 30): filter PersonnelImport.*.  
Metric: import_commit_rows.

---

## Extra — Test strategy

- Unit: Importer ba small xlsx fixture  
- Planner ba in-memory repos fake  
- Session store TTL test  
- Integration: Preview→Commit Testcontainers  

---

## Extra — Comparison «silent upsert»

Ba'zi system-ha Excel = upsert by code.  
Dejban Personnels Preview Action Create-focused + duplicate error — safer explicit.  
Vehicles interpreter shayad update paths — check BulkImportRowInterpreter.

---

## Soalat-e chera (yek+nim khat)

**Chera 2h TTL?** Balance abandon vs memory.  
**Chera DisableAntiforgery?** Multipart + SPA token auth common.  
**Chera bilingual headers?** Mixed HR files.  
**Chera Commit Plan again?** TOCTOU safety.  
**Chera DCC ba'd SaveChanges?** Need Personnel Id for file metadata — order tradeoff.

---

## Extra — Package versions (repo)

`ClosedXML` 0.105.1 · `ExcelDataReader` (+ DataSet) 3.9.0 — central `Directory.Packages.props`.  
Personnels.Application ClosedXML; Vehicles hardo.

---

## Extra — Endpoint list cheat-sheet

| Method | Path | naqsh |
|---|---|---|
| GET | `/Personnels/ImportTemplate` | template file |
| POST | `…/ImportFromExcel/Preview` | upload+plan |
| GET | `…/GetPreview/{importId}` | reload session |
| PUT | `…/UpdateRow` | edit |
| POST | `…/Revalidate` | plan again |
| POST | `…/Commit` | persist |

Versioned `api/v{version}` + Tags.Personnels (Day 17/33).

---

## Extra — Farz kon commit mid-fail DCC

Personnel saved; avatar upload 500.  
User list mibine bedune aks — retry manual upload UI.  
Ideal: outbox file upload / compensating delete — advanced. Honest gap.

---

## Khoruj-e zehni

> Midunam Excel import Personnels ba ClosedXML template/preview/session/planner/commit-e; FE wizard dare; session memory-e; commit faghat bedune error row; aks miravad DCC. Farq Vehicles/Units va smell multi-instance ro midunam.

Age in paragraph mal-e to shod — Day 38 done.

---

*Day 38 tamum. Ba'd: Day 39 — Stimulsoft + ImageSharp (amade). Fehrest: [README.md](./README.md).*
