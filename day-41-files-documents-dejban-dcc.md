# Day 41 — Files/Documents (Dejban → DCC)

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** PDF/aks document-e personnel ya visitor koja save she?

**Javab Dejban:** byte-ha **na** to Postgres-e Personnels — microservice **DCC** (Document/Content Center) malek-e file-e. Dejban faqat **metadata domain** negah midare (`PersonnelDocument.DccFileId`, title, size, …).

Zincir:

```
FE multipart → Dejban API (Documents)
  → DccHttpClient (JWT forward) → DCC UploadFile
  → IFileStorage (Local | MinIO/S3)  [Day 28]
  → DCC FileEntity row
  → Dejban PersonnelDocument.Create(dccFileId, …)
```

Download:

- **Stream proxy:** Dejban → DCC Download → `Results.File`  
- **Presign (prefer):** Dejban → DCC `/presigned` → FE mostaghim MinIO URL (TTL)  
- **Public:** `/files/...` Gateway → DCC/MinIO public (Reporting aks — Day 39)

**Band-e gharardad-e jadid:** tozihat ravoontar — «farz kon / yani chi / chera».

Day 28 = storage engine. **In ruz = product flow documents** Dejban↔DCC↔FE.

---

# BAKHSH-E AVAL: WORLD — chera file service joda?

## Farz kon — ketabkhune vs anbar

Ketabkhune (Dejban): «in personnel 3 sanad dare, title-ha ina».  
Anbar (DCC): «byte-haye file + hash + path».

| ravesh | moshkel |
|---|---|
| BYTEA to Dejban DB | DB inflat; backup; streaming |
| Disk local on Dejban pod | multi-instance share na |
| **DCC + object store** | scale, ACL file, reuse cross-module |

**Yani chi?** Bounded context Files joda (Day 09) — Personnels/Visitors/Reporting hame customer-e DCC.

---

## Olgu-ye reference

Domain table: `DccFileId` FK lojik (cross-service — na EF FK).  
Consistency: upload DCC success ba'd insert document; fail upload → no row.  
Delete: delete document + DCC file (order careful orphan).

---

# BAKHSH-E DOVOM: DEJBAN → DCC

## Naqshe-ye upload (Personnel)

```
POST /api/v1/Personnels/{id}/Documents  (multipart: file + title)
  UploadPersonnelDocumentCommandHandler
    validate personnel exists, file, title
    DccHttpClient.UploadFileAsync(
      ownerService: "Dejban.Personnels",
      folderName: "personnel/documents",
      creatorId: personnelId,
      isPublic: false,
      accessToken: Bearer from incoming request)
    PersonnelDocument.Create(..., dccFileId: uploaded.Id, ...)
    InsertDocument + SaveChanges
  ← PersonnelDocumentResponse (domain id, dccFileId, meta)
```

**Chera JWT forward?** DCC `[Authorize]` + FileAccess — haman user.  
**Chera ownerService/folder?** Search/organize + multi-tenant logic DCC.

---

## Qesmat 1 — `DccHttpClient` (bridge)

`Common/FileService/DccHttpClient.cs` — typed HttpClient:

| method | DCC path |
|---|---|
| UploadFileAsync | POST `/api/v1/Files/UploadFile` |
| GetFileMetadataAsync | GET `.../GetFileMeta/{id}` |
| DownloadFileAsync | GET `.../Downloadfile/{id}` (+ X-Site-Id) |
| GetPresignedDownloadUrlAsync | GET `.../Downloadfile/{id}/presigned` |
| DeleteFileAsync | DELETE `.../DeleteFile/{id}` |
| SearchFilesAsync | GET `.../Search` |

Register: `AddDccHttpClient` → BaseAddress az config.  
**Smell Day 32:** no Polly resilience handler — transient DCC fail = user error.

---

## Qesmat 2 — Domain `PersonnelDocument`

```csharp
public sealed class PersonnelDocument : Entity
{
    public Guid PersonnelId { get; }
    public Guid DccFileId { get; }      // pointer to DCC
    public string Title { get; }
    public string OriginalFileName { get; }
    public string ContentType { get; }
    public long Size { get; }
    // StoragePath, FolderName cached from upload response
    public DateTime CreatedAt { get; }
}
```

**Yani chi?** List documents **bedune** call DCC (meta local).  
Download niyaz DccFileId → DCC.

Visitor: `VisitorDocument` hamin pattern.

Insert tip: `InsertDocument` direct — avoid concurrency soft-delete parent (comment handler).

---

## Qesmat 3 — Endpoints Personnels Documents

| Method | Path | naqsh |
|---|---|---|
| POST | `.../Documents` | upload (+ DisableAntiforgery) |
| GET | `.../Documents` | list domain rows |
| GET | `.../Documents/{docId}/Download` | stream via Dejban |
| GET | `.../Documents/{docId}/DownloadUrl` | presign JSON |
| DELETE | `.../Documents/{docId}` | delete domain + DCC |

Auth required. Tags.Personnels (OpenAPI Day 33).

---

## Qesmat 4 — Download do masir

### A) Stream (Download)

Handler: load document → `dccClient.DownloadFileAsync(DccFileId, token, siteIds)` → `Results.File(stream, contentType, fileName)`.

**Yani:** FE yek request be Gateway/Dejban; Dejban proxy bytes.  
Simple; Dejban bandwidth.

### B) Presign (DownloadUrl) — prefer MinIO

```csharp
// comment: Prefer MinIO presign (client direct). Auth check happens on DCC.
var presign = await dccClient.GetPresignedDownloadUrlAsync(...);
→ { Url, ExpiresAtUtc, IsPresigned }
```

FE: `window.open(url)` ya `<a href>` — traffic MinIO, na Dejban.  
Auth: DCC validates JWT **ghabl** emza URL (TTL ~5 min Day 28).  
Local storage: PresignNotSupported → FE fallback stream.

**PublicEndpoint** (Day 28): signature ba URL-i ke browser mibine.

---

## Qesmat 5 — DCC `FileEntity` (anbar metadata)

Id, ContentType, Size, OriginalFileName, FileName, OwnerService, FolderName, CreatorId, IsPublic, StoragePath, HashSha256, ExpiresAt, revisions, soft delete,  
ACL fields: AllowedRoles/Users/Services, **RequiredPermission**, SiteId, RequireSiteMatch, …

`IFileStorage`: Local vs S3 (`StorageOptions` Day 34/28).

Upload command writes entity + blob.  
`FileAccessService.CanAccessAsync`: IsPublic → allow; digar checks (permission/roles) **commented** — authenticated private files currently broad. Honest smell.

---

## Qesmat 6 — Public files

`isPublic: true` → path under public; Gateway `/files/{path}` (static or MinIO proxy).  
Reporting `TryLoadPublicFileBytes` / FE `resolve-public-file-url.js` → `${origin}/files/...`.

Avatar/signature import Excel: DCC upload private-ish; reporting guest photo often public path.

---

## Qesmat 7 — FE

- `documents-tab` staff — upload accept pdf/images/office  
- `staff.service` / `visitor.service` — React Query upload/delete invalidate  
- `optimize-document-file.js` — compress image ghabl upload (client)  
- DownloadUrl vs Download — check staff http helpers  

**Yani:** UX optimize client; server still DCC.

---

## Qesmat 8 — Digar call-site-haye DccHttpClient

| caller | usage |
|---|---|
| Personnel/Visitor documents | CRUD docs |
| Create/Update Visitor (+photo) | upload media |
| Excel import commit | avatar/signature |
| Identity (AddDccHttpClient) | possible avatars |

Yek client — chand ownerService string.

---

## Se dastan (farz kon)

### A) Upload PDF personnel

FE FormData → Dejban → DCC MinIO private key → Document row → list shows title.

### B) Download presign

FE DownloadUrl → JWT check DCC → signed URL → browser GET MinIO 5 min.

### C) DCC down

UploadFailed ErrorOr — document row nist (good).  
Partial: DCC OK Dejban SaveChanges fail → orphan file DCC (smell; cleanup job?).

### D) Report needs guest photo

Public `/files/...` ya enrich bytes Reporting (Day 39) — na Document private flow.

---

## Smell-ha

1. Orphan DCC file age Dejban insert fail  
2. FileAccess permission checks commented  
3. No Polly on DccHttpClient  
4. Meta duplicate (DCC + Document size/path) — drift  
5. Delete order orphan/dangling  
6. Large file memory buffer DownloadFileAsync (copy MemoryStream)  
7. creatorId = personnelId string — semantic «creator user» vs owner entity  
8. Cross-service consistency eventual  
9. DisableAntiforgery upload — auth still  
10. Search DCC by owner — multi-tenant care  

---

## Debug checklist

1. DccHttpClient BaseAddress correct (Docker hostname)?  
2. Bearer forwarded? DCC 401  
3. Upload 200 but no Document — SaveChanges?  
4. Presign 403 PublicEndpoint?  
5. Stream OK presign fail → Local provider?  
6. X-Site-Id on download?  
7. File not found — wrong DccFileId  
8. MinIO bucket/CORS  
9. FE CORS on presigned host  
10. Orphan: Search DCC ownerService  

---

## 25 soal-e mosahebe

1. Chera DCC joda?  
2. PersonnelDocument chi negah midare?  
3. DccFileId?  
4. DccHttpClient naqsh?  
5. Chera JWT forward?  
6. ownerService/folderName?  
7. Upload sequence?  
8. Stream vs presign?  
9. Auth check koja for presign?  
10. Public /files?  
11. FileEntity fields?  
12. IFileStorage?  
13. FileAccessService smell?  
14. Orphan problem?  
15. Visitor same?  
16. Excel import DCC?  
17. Reporting photo path?  
18. DisableAntiforgery?  
19. InsertDocument tip?  
20. Polly gap?  
21. HashSha256?  
22. Soft delete file?  
23. FE optimize?  
24. RequiredPermission field?  
25. Resume 60s?

---

## Senario-ha

### A) Presign expire

TTL pass → 403 MinIO; FE re-fetch DownloadUrl.

### B) Private file IsPublic false

Anonymous /files fail; need auth download path.

### C) Delete document

Handler: delete DCC then domain (or reverse) — check code order orphans.

### D) Two services same fileId

Id Guid DCC global; Document points one.

---

## Mini lab

1. PersonnelDocuments endpoints  
2. UploadPersonnelDocumentCommandHandler  
3. DccHttpClient methods  
4. GetPersonnelDocumentDownloadUrlQueryHandler  
5. FileEntity + FileAccessService  
6. Day 28 StorageOptions link  
7. FE documents-tab + resolve-public-file-url  
8. Grep DccHttpClient call sites  

---

## Resume

**kutah:**

> Implemented document management as a Dejban→DCC integration: domain `PersonnelDocument`/`VisitorDocument` store DCC file ids and titles while `DccHttpClient` uploads/downloads with forwarded JWTs; supported streaming downloads and MinIO presigned URLs after DCC auth, with public `/files` for report assets and Local/S3 storage behind DCC.

**bullet-ha:**

- Separated blob ownership (DCC FileEntity + IFileStorage) from HR/visitor document aggregates  
- Built upload/list/download/presign/delete APIs forwarding bearer tokens and site headers  
- Documented orphan/consistency tradeoffs and FE upload optimization  

**skill-ha:** `Microservices, Document management, Presigned URLs, HttpClient, Multipart upload, MinIO/S3, DDD references, ASP.NET Minimal APIs`

---

## File-haye mohem

| chi | koja |
|---|---|
| DccHttpClient | `Common/FileService/DccHttpClient.cs` |
| Upload handler | `UploadPersonnelDocumentCommandHandler.cs` |
| Domain doc | `PersonnelDocument.cs` |
| Endpoints | `PersonnelDocuments.cs` |
| Presign query | `GetPersonnelDocumentDownloadUrlQueryHandler.cs` |
| DCC entity | `DCC/Domain/Entities/FileEntity.cs` |
| Access | `FileAccessService.cs` |
| Storage | Local/S3 Day 28 |
| FE | `documents-tab`, staff/visitor services |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 28 MinIO | IFileStorage, PublicEndpoint, presign |
| 09 Microservices | DCC bounded context |
| 37 Permissions | RequiredPermission field (future) |
| 38 Excel | avatar upload DCC |
| 39 Reporting | public file bytes |
| 40 Auth | JWT forward |
| 32 Polly | gap HttpClient |
| 34 Options | Storage section |

---

## Chejori digest koni

1. WORLD ketabkhune/anbar (15 min)  
2. Upload sequence code (25 min)  
3. Download stream vs presign (20 min)  
4. FileEntity + access (15 min)  
5. Public vs private (10 min)  
6. FE + smells (15 min)  
7. 25 soal (20 min)  

---

## Glossary

| kalame | ma'ni |
|---|---|
| DCC | file microservice |
| DccFileId | Guid pointer |
| OwnerService | which app uploaded |
| Presign | temporary signed URL |
| Stream proxy | API pipes bytes |
| Public file | /files anonymous-ish |
| FileEntity | DCC metadata row |
| Orphan | blob bedune domain row |

---

## Deep dive — consistency patterns

| pattern | Dejban emruz |
|---|---|
| Upload then DB | yes |
| Outbox delete file | no |
| Saga | no |
| Idempotent upload key | filename Guid |

Mosahebe: acknowledge orphan; propose cleanup by ownerService+orphan detect.

---

## Deep dive — cherа meta duplicate?

Document copies size/contentType/path az DCC response — list UI bedune N+1 DCC.  
Drift age DCC revise file — CurrentRevision field DCC; Dejban may stale. Tradeoff.

---

## Deep dive — MemoryStream download

`DownloadFileAsync` copy full body to MemoryStream — large PDF = RAM.  
Better: stream forward `HttpCompletionOption.ResponseHeadersRead` end-to-end. Smell scale.

---

## Anti-pattern

```csharp
// BAD: save PDF bytes on Personnel entity
// GOOD: DccFileId reference (Dejban)

// BAD: FE upload mostaghim MinIO bedune auth
// GOOD: DCC auth then presign (private)

// BAD: ignore JWT on service-to-service upload
// GOOD: forward user token (or service credential design)
```

---

## Interview 60s

> «Documents aren’t stored in the Personnels database. Dejban keeps PersonnelDocument rows with a DccFileId; uploads go through DccHttpClient to the DCC service, which persists FileEntity metadata and bytes in Local or MinIO storage. Downloads either stream via Dejban or return a MinIO presigned URL after DCC authorizes the caller. Public assets use the gateway /files path for reports. That keeps the modular monolith free of blobs while centralizing file ACL and storage.»

---

## Quick self-test

1. Blob koja? → DCC (+ MinIO/Local)  
2. Domain pointer? → DccFileId  
3. Client class? → DccHttpClient  
4. ownerService personnel? → Dejban.Personnels  
5. folder? → personnel/documents  
6. Presign auth? → DCC ghabl sign  
7. Public URL? → /files/…  
8. List need DCC? → no (local meta)  
9. Access service? → FileAccessService  
10. Polly? → gap  

---

## Final checklist

- [ ] Separation DCC vs domain  
- [ ] Upload flow  
- [ ] Stream vs presign  
- [ ] Public files  
- [ ] Smells orphan/access  
- [ ] FE  
- [ ] Resume  

---

## Extra — Farz kon Visitor passport scan

Hamin: VisitorDocuments endpoints + DccHttpClient ownerService Visitors folder.  
UI visitor documents tab. Pattern copy-paste intentional modular.

---

## Extra — Identity avatar?

Identity may use DCC for user Avatar string path — check CreateUser TODO.  
Personnel avatar import = DCC private/public mix.

---

## Extra — HashSha256

DCC stores hash — dedupe/integrity future.  
Not exposed heavily on PersonnelDocument.

---

## Extra — Revisions

FileEntity CurrentRevision + FileRevision collection — replace file keep history.  
Document domain may still point same File Id — product choice.

---

## Extra — Security layers

1. FE auth + maybe Guard  
2. Dejban endpoint Authorize (+ future permission)  
3. DCC Authorize + FileAccess  
4. Presign TTL  
5. Private bucket  

Defense in depth; smell middle layers weak if FileAccess loose.

---

## Extra — Network topology

```
Browser → Gateway → Dejban.Api
Dejban.Api → (internal) DCC:port  (BaseAddress)
Browser → (presign) MinIO PublicEndpoint
Browser → Gateway /files → MinIO or static
```

Docker: Dejban must resolve `dcc` hostname not localhost.

---

## Map — delete

```
DELETE Documents/{id}
  load PersonnelDocument
  dccClient.DeleteFileAsync(DccFileId)
  remove domain row SaveChanges
```

Agar DCC fail — domain? transactional outbox ideal.

---

## Map — list

```
GET Documents
  query PersonnelDocuments by personnelId
  return DTOs (no DCC call)
```

---

## Lab aha

1. Upload → DB Document + DCC FileEntity ids match  
2. Stop DCC → upload error no Document  
3. Presign URL host = PublicEndpoint  
4. Download stream vs url Network tab  
5. Public avatar in report  

---

## What Day 41 is *not*

- Full MinIO IAM (Day 28)  
- Virus scanning  
- Chunked resumable upload  

Focus: **Dejban document product integration with DCC**.

---

## Resume keywords

`Document management` · `Microservices` · `Presigned URL` · `MinIO` · `HttpClient` · `Multipart` · `DCC` · `File storage` · `DDD`

---

## Band-e gharardad-e jadid

Ketabkhune/anbar; upload dastan; stream vs presign; orphan honest; FileAccess comment honest.

---

## 10 jomle fluency

1. Bytes in DCC; meta link in Dejban.  
2. DccFileId = pointer.  
3. DccHttpClient + JWT forward.  
4. Upload then InsertDocument.  
5. List local; download hits DCC.  
6. Presign after DCC auth.  
7. Public /files for reports.  
8. OwnerService + folder organize.  
9. Orphan risk acknowledged.  
10. Same pattern Visitors.

---

## Extra — Comparison «FE → DCC direct»

Alternative: browser upload DCC.  
Dejban: orchestrate title+personnel link transactional-ish; one API for FE.  
Tradeoff: Dejban hop extra latency.

---

## Extra — Content-Type / extension

Handler fixes image extension if missing.  
DCC stores ContentType from upload.  
FE optimize may convert to jpeg.

---

## Extra — Soalat chera

**Chera na EF blob?** Scale/backup.  
**Chera forward user JWT?** Audit + ACL as user.  
**Chera presign?** Offload bandwidth.  
**Chera cache path on Document?** List perf.  
**Chera DisableAntiforgery?** Multipart SPA + Bearer.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «Dejban owns document *product* rows — title, personnelId, folder. Bytes live in DCC/MinIO. Upload: FE → Dejban multipart → DccHttpClient → DCC → then InsertDocument with DccFileId. Download: either stream proxy or short-lived presign. Public `/files/{id}` for report images without Bearer.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Upload 502/timeout | DCC down / BaseAddress wrong |
| Document without file | rare race; usually upload fails first |
| Download 404 | wrong DccFileId / deleted in DCC |
| Presign host localhost | PublicEndpoint misconfigured |
| Avatar broken in PDF | public URL blocked / CORS / expired |
| List OK open fail | FileAccess / JWT not forwarded |
| Double upload | FE retry without idempotency key |

---

## Extra — Layer checklist «who stores what?»

| layer | stores |
|---|---|
| FE form | File blob + title fields |
| Dejban Document | meta + DccFileId + path cache |
| DCC FileEntity | name, contentType, size, storage key |
| MinIO/S3 | actual bytes |

---

## Extra — Related learning days (quick jump)

- Day 28: MinIO, IFileStorage, presign, PublicEndpoint  
- Day 16: multi-tenant site filters on personnel  
- Day 38: Excel import — another binary pipeline, different product  
- Day 39: reports may embed public file URLs  
- Day 40: JWT + refresh — same token DccHttpClient forwards  

In ruz = glue beyn product meta va storage service.

---

## Extra — Farz kon orphan cleanup job

Farz kon: nightly Quartz job list DCC files older than N days with no Document.DccFileId.  
Chera hard-e? Cross-DB join nisti — bayad export id set az Dejban, query DCC.  
Chera valuable-e? Disk cost + privacy (old passport scans).  
Honesty: codebase may not ship this yet — interview answer = «gap I'd design».

---

## Extra — Stream vs FileResult memory

Download through Dejban often buffers to MemoryStream then File().  
Large video? Bad — prefer redirect/presign.  
Documents (PDF/ID card) usually OK size.  
Interview: «I choose stream proxy for ACL control; presign when payload is heavy.»

---

## Extra — Multipart boundary pitfalls

FE must send `multipart/form-data` with file field name matching endpoint (`file` / `document`).  
Axios: don't set Content-Type manually — browser sets boundary.  
If you set `application/json` by mistake → 400 empty file.

---

## Extra — Delete order debate

**A)** Delete Document then DCC file  
**B)** Delete DCC then Document  
**A** risk: orphan bytes. **B** risk: broken link if DCC ok DB fail.  
Common: soft-delete Document first; async delete DCC; or outbox event.  
Day 41 honesty: check actual Delete handler order in code before claiming saga.

---

## Extra — Testing strategy

1. Contract test DccHttpClient against WireMock DCC  
2. Integration: Testcontainers MinIO + DCC + Dejban upload  
3. FE: upload fixture PDF → assert list row + download blob  
4. Negative: revoke JWT mid-download  

---

## Extra — Capacity & limits (mosahebe)

Soal: max upload size koja enforce mishe?  
Javab-haye momken: Kestrel/IIS limit, Gateway YARP, DCC middleware, MinIO policy.  
Dejban bayad error-e user-friendly bede (413) na generic 500.  
FE: client-side size check = UX, na security.

---

## Extra — Content disposition

Download stream: `Content-Disposition: attachment; filename="..."`  
Inline preview (PDF in tab): `inline`.  
Presign: MinIO response-content-disposition query param.  
Bug classic: Persian filename → RFC 5987 `filename*`.

---

## Extra — Idempotent upload? (honest)

Aksaran upload idempotent nist — har POST file jadid misaze.  
Agar FE double-click → do Document.  
Mituni: client requestId + unique constraint, ya disable button.  
Outbox pattern inja kamtar common-e ta domain events.

---

## Band-e gharardad — ye bar digar sade

1. **Ketabkhune** = Dejban Document (chi, male ki, title).  
2. **Anbar** = DCC + MinIO (khode file).  
3. **DccFileId** = shomare-ye quti dar anbar.  
4. **Upload** = aval anbar, ba'd ketabkhune.  
5. **Download** = ya Dejban miyare (stream), ya link-e movaqat (presign).  
6. **Public** = baraye ax-e gozaresh bedun Bearer.  
7. **Smell** = orphan + FileAccess comment — dorugh nagu.

---

## Khoruj-e zehni

> Midunam sanad-haye personnel/visitor ba DCC save mishan; Dejban DccFileId + title dare; upload/download/presign az DccHttpClient ba JWT; public files baraye report; va orphan/access smell-ha ro tozih midam.

Age in paragraph mal-e to shod — Day 41 done.

---

*Day 41 tamum. Ba'd: Day 42 — Next.js 16 + React 19 (amade). Fehrest: [README.md](./README.md).*
