# Day 28 — MinIO / S3

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**MinIO** ye object store-e S3-compatible-e (mesl-e AWS S3, ama mitune on-prem / Docker bashe). To Dejban, byte-haye file (aks, PDF, document) diga ru-ye disk-e Gateway ya ACL nemimunan — microservice-e **DCC** malek-e file-e. Metadata (esm, size, hash, site, permission) to Postgres-e DCC save mishe; khode byte-ha az tarigh-e abstraction-e **`IFileStorage`** miran be disk **Local** ya be **MinIO/S3** — ba flag-e `Storage:Provider`.

Do masir-e download mohem hast: (1) **private** — JWT + check-e dastresi, ba'd ya stream az DCC, ya **presigned URL** ke browser mostaghim az MinIO migire (TTL ~5 daghighe); (2) **public** — URL-e sabet `/files/...` az YARP miravad be DCC proxy (na anonymous bucket), ta Reporting/FE taghir nakonan. Trick-e amali: signature-e presign bayad ba **`PublicEndpoint`** (host-i ke browser mibine) zade she, na ba endpoint-e dakheli Docker — vagarna 403.

---

# BAKHSH-E AVAL: WORLD — object storage chie va chera

## Chera file ro to DB ya disk-e API nazanim?

| ravesh | moshkel |
|---|---|
| BYTEA / BLOB to Postgres | DB inflat mishe; backup/restore sakht; streaming za'if |
| Disk local ru-ye API pod | multi-instance share nemishe; scale/restart file gom mishe |
| **Object storage (S3 API)** | durable, scalable, URL/presign, joda az compute |

Object store yani: **bucket** (ye container-e lojik) + **key** (path-like string) + object (bytes + metadata). API-ash Put/Get/Delete/List-e — na filesystem POSIX.

---

## S3 API — mafahim-e sade

| mafhum | ma'ni |
|---|---|
| **Bucket** | nam-e space (inja `dcc-files`) |
| **Key** | mesal: `private/Personnels/2026-09/uuid.pdf` |
| **PutObject** | upload |
| **GetObject** | download stream |
| **DeleteObject** | delete |
| **Head/Metadata** | exist + size bedune body |
| **Presigned URL** | URL ba emza + TTL; bedune AccessKey to browser |

Client library ma'mulan **AWS SDK** (`AWSSDK.S3`) — ba MinIO ham kar mikone age `ServiceURL` + `ForcePathStyle` dorost bashe.

---

## MinIO vs AWS S3

| | MinIO | AWS S3 |
|---|---|---|
| koja | Docker / on-prem | cloud AWS |
| API | S3-compatible | native S3 |
| path style | ma'mulan **ForcePathStyle=true** (`endpoint/bucket/key`) | modern virtual-hosted (`bucket.s3.region...`) |
| credential | `MINIO_ROOT_USER` / password | IAM / access key |
| gheymat | self-host | pay-per-use |

Fekr kon MinIO = «S3-e khodemun to LAN». Code-e Dejban `Provider=S3` mige — provider-agnostic; endpoint MinIO ya AWS.

---

## Presigned URL — chera in ghad mohem-e?

Bedune presign:

```
Browser → Gateway → DCC → MinIO → … bytes bargard → Gateway → Browser
```

Har file-e 50MB do bar az network-e app rad mishe (DCC load + latency).

Ba presign:

```
Browser → DCC: «ejaze daram?» (JWT + site)
DCC → Browser: URL signed (5 min)
Browser → MinIO mostaghim GET
```

DCC faghat **authZ** mikone; traffic-e sangin az object store mire. Hamin olgu to CDN/cloud standard-e.

**CORS:** browser az origin-e FE be MinIO cross-origin request mizane — bayad CORS ru-ye bucket set she (Dejban: `minio-cors.json` + `minio-init`).

---

## Path-style vs virtual-hosted (403 trap)

MinIO ma'mulan:

```
http://localhost:19000/dcc-files/private/...
```

AWS modern:

```
https://dcc-files.s3.eu-west-1.amazonaws.com/private/...
```

`ForcePathStyle=true` baraye MinIO. Age eshtebah bashe, Put/Get fail ya signature invalid.

---

## Public vs private objects

| | public | private |
|---|---|---|
| access | URL sade / CDN | auth ya presign |
| risk | har ki ba URL | bayad token/permission |
| use | avatar, logo, static report asset | document-e personel, shenasname |

**Smell:** «public» to MinIO ba anonymous policy = har ki key ro hads bezane download mikone. Dejban public-ha ra **az DCC proxy** serve mikone (credential poshte service mimune).

---

## Consistency — metadata vs bytes

Pattern-e dorost:

1. Upload bytes → object store  
2. Save row to DB (path, hash, size, owner)  
3. Download: DB → path → OpenRead / presign  

Age faghat DB bashe va object nabashe → broken link. Age object bashe va DB nabashe → orphan. Migration/cutover bayad har do ra sync kone.

---

## Security checklist (WORLD)

1. AccessKey/Secret to secret store — na hardcode FE  
2. Presign TTL kutah  
3. AuthZ **ghabl** az dadan-e URL  
4. Path traversal (`../`) block  
5. Bucket policy minimal  
6. TLS to prod  
7. PII documents = private + audit  

---

# BAKHSH-E DOVOM: DEJBAN — DCC + MinIO

## Ki chi kar mikone?

```
FE / Reporting
    │  /files/... (public)     │  upload/download private
    ▼                          ▼
 ApiGateway (YARP)          Dejban / digar services
    │                          │  DccHttpClient
    │ DccProxy                 ▼
    └──────────────►  DCC  ─── IFileStorage ───► MinIO (ya Local disk)
                       │
                       └── Postgres: FileEntity (meta)
```

- **DCC** = Document/Content Center — API-e file  
- **Dejban modules** (Personnels, Visitors, …) mostaghim MinIO seda nemizanand; az **`DccHttpClient`** (Common) estefade mikonan  
- **Gateway** `/files/{**}` → DCC public endpoint (Phase 4)

---

## Abstraction — `IFileStorage`

```csharp
public interface IFileStorage
{
    Task<StorageSaveResult> SaveAsync(string relativePath, Stream content, ...);
    Task<Stream?> OpenReadAsync(string relativePath, ...);
    Task DeleteAsync(string relativePath, ...);
    Task<bool> ExistsAsync(string relativePath, ...);
}
```

Business (`FileService`) **nemidune** Local-e ya S3. In Strategy/ISP-e khub — mosahebe gold.

```csharp
// DI — Storage:Provider
if (Provider == "S3")
{
    AddSingleton<S3FileStorage>();
    IFileStorage → S3FileStorage
    IPresignedUrlProvider → S3FileStorage  // IsSupported=true
}
else
{
    LocalFileStorage  // IPresignedUrlProvider.IsSupported=false
}
```

---

## Config — `Storage` / `S3`

```json
"Storage": {
  "Provider": "S3",
  "S3": {
    "Endpoint": "http://minio:9000",
    "PublicEndpoint": "http://localhost:19000",
    "AccessKey": "...",
    "SecretKey": "...",
    "Bucket": "dcc-files",
    "Region": "us-east-1",
    "ForcePathStyle": true,
    "PresignTtlSeconds": 300
  }
}
```

| field | chera |
|---|---|
| `Endpoint` | DCC az dakhel-e Docker be MinIO (`minio:9000`) |
| `PublicEndpoint` | host-i ke **browser** MinIO ro mibine (`localhost:19000`) — baraye **sign** |
| `ForcePathStyle` | MinIO |
| `PresignTtlSeconds` | default 300 |

---

## `S3FileStorage` — AWS SDK ru-ye MinIO

- `PutObject` / `GetObject` / `DeleteObject` / `GetObjectMetadata`  
- Key = `relativePath` ba `/` (Normalize: trim `\` → `/`)  
- Ghabl az Put: `StorageHashing.BufferAndHashAsync` → Size + SHA256 (ContentLength baraye S3)  
- Presign GET/PUT ba client-i ke `ServiceURL = PublicEndpoint` — comment to code: **rewrite bad az sign = 403**

```csharp
// CreateSigningClient: age PublicEndpoint != Endpoint dakheli
// → AmazonS3Client ba ServiceURL=PublicEndpoint
var url = signingClient.GetPreSignedURL(new GetPreSignedUrlRequest {
    BucketName, Key, Verb = GET, Expires = UtcNow + ttl
});
```

---

## `LocalFileStorage` — fallback / dev ghadimi

- Root: `uploads/` zir-e content root (ya `Storage:RootPath`)  
- `IsSupported` baraye presign = **false** → `Files.PresignNotSupported`  
- Haman `IFileStorage` — cutover asan

---

## Metadata — `FileEntity`

Postgres row, na byte:

| field | naqsh |
|---|---|
| `StoragePath` | key-e object / relative path |
| `HashSha256` | integrity |
| `Size`, `ContentType`, `FileName` | download headers |
| `OwnerService`, `FolderName`, `CreatorId` | ownership |
| `IsPublic` | public vs private prefix |
| `SiteId`, `RequireSiteMatch` | tenancy (Day 16) |
| `AllowedRoles/Users/...` | fine-grained ACL |
| `IsDeleted`, revisions | soft lifecycle |

---

## Path layout (mohem)

```
{public|private}/{ownerService}/{yyyy-MM}/{fileName}
```

Mesal:

```
private/Personnels/2026-09/a1b2....pdf
public/personnels/2026-09/avatar.jpg
```

Public URL az FE: `/files/personnels/2026-09/avatar.jpg`  
→ DCC: `public/personnels/...`  
→ MinIO key: `public/personnels/...`

Private: **faghat** `Downloadfile/{id}` ya `/presigned` ba JWT — key-e raw public nist.

---

## Upload flow (Dejban → DCC → MinIO)

```
Module handler (masalan UpdatePersonnel photo)
  → DccHttpClient.UploadFileAsync (multipart + Bearer)
  → DCC UploadFileCommand
  → FileService.UploadFileAsync
       build StoragePath
       fileStorage.SaveAsync → PutObject
       Save FileEntity (Size, Hash)
  → FileInfoDTO (Id, …) bargard be module
```

Module Id-e file ro to entity-e business save mikone (FK lojiki), na path-e disk.

---

## Download — se halat

### A) Stream az DCC (classic)

`GET .../Downloadfile/{id}` → auth → `OpenReadAsync` → stream response.  
Local ya S3 — kar mikone. Load ru-ye DCC.

### B) Presigned (modern private)

`GET .../Downloadfile/{id}/presigned`

1. `GetFileEntity`  
2. `IFileAccessService.CanAccess` (JWT + site + roles…) — **haman ghavanin-e Download**  
3. Age Local → `PresignNotSupported`  
4. Age S3 → `CreateGetUrlAsync` ba TTL  
5. Client `GET` mostaghim be MinIO  

`DccHttpClient.GetPresignedDownloadUrlAsync` hamin endpoint ro seda mizane; caller age error → stream fallback.

### C) Public `/files/...`

YARP anonymous → DCC `AllowAnonymous` public path → faghat prefix `public/` + path-traversal guard → `OpenRead`.  
Reporting Stimulsoft / `<img src>` taghir nemikhad.

---

## Docker — MinIO stack

`docker-compose.yml` / `docker-compose.minio.yml`:

| service | naqsh |
|---|---|
| `minio` | API `:9000` (host map ma'mulan `19000`), console `19001` |
| `minio-init` | `mc` alias + `mb dcc-files` + CORS az `minio-cors.json` |
| volume `minio-data` | persist |

Health: `curl minio/health/live`.

Cutover docs: `Microservices/DCC/docs/MINIO-PHASE*.md` (migrate, cutover, public proxy, presign, FE wire). Script: `MigrateLocalFilesToS3` / `migrate-local-to-minio.ps1`.

---

## Phase story (chizi ke to docs neveshtan)

| phase | chi |
|---|---|
| 2 | migrate local → MinIO (copy objects) |
| 3 | `Provider=S3` cutover — DCC write/read MinIO |
| 4 | `/files` az disk Gateway → **DccProxy** → MinIO |
| 5 | Presigned private download |
| 6 | FE wire (browser follow URL) |

Inja Day 28 = infra + DCC server. FE depth = Day 41 / 50-ha.

---

## Access control (kholase)

Download/presign:

- SuperAdmin bypass  
- vagarna `FileAccessService.CanAccess(file, user, siteIds)`  
- `X-Site-Id` az header (Day 16)  

Public endpoint: **auth nadare**, ama faghat `public/` — private key serve nemishe.

---

## Smell-ha

1. **Rewrite URL bad az sign** → 403 (PublicEndpoint faramush)  
2. **CORS set nashe** → FE browser block  
3. **Anonymous MinIO public** (Dejban avoid karde — khub)  
4. **Orphan object** age DB delete nashe / reverse  
5. **Hash buffer** hame file to memory — file kheili bozorg = pressure (smell scale)  
6. **AccessKey to appsettings** committed — secret management  
7. **Presign TTL tulani** = URL share risk  
8. **Local + multi-pod** = inconsistent files  
9. **Path traversal** age guard nabashe ru-ye public  
10. **Provider Local to prod** be eshtebah  
11. **ContentType** eshtebah → browser bad render  
12. **SiteId null** + RequireSiteMatch → access bug  

---

## Debug checklist

1. MinIO up? `19000` / health  
2. Bucket `dcc-files` hast? (`mc ls`)  
3. DCC `Storage:Provider=S3`?  
4. Endpoint dakheli vs PublicEndpoint  
5. Put ok — console MinIO object bebin  
6. Presign 403 → signing host  
7. Browser CORS error → cors.json  
8. `/files` 404 → YARP PublicFiles DccProxy  
9. Private 401/403 → JWT + FileAccess  
10. Hash mismatch → corrupt upload / partial  

---

## 25 soal-e mosahebe

1. Object storage vs filesystem?  
2. MinIO chie nesbat be S3?  
3. Bucket / key?  
4. Chera metadata joda az bytes?  
5. `IFileStorage` chera?  
6. ForcePathStyle?  
7. Presigned URL chie?  
8. Chera auth ghabl az presign?  
9. PublicEndpoint trap?  
10. CORS chera?  
11. Chera public az DCC proxy?  
12. Path layout Dejban?  
13. DccHttpClient naqsh?  
14. Local vs S3 DI?  
15. SHA256 key vaght?  
16. Stream vs presign tradeoff?  
17. Multi-instance ba Local?  
18. Orphan object?  
19. Soft delete file?  
20. Tenancy ru-ye file?  
21. Put presign (upload direct) use case?  
22. CDN + S3?  
23. Secret rotation?  
24. Migration Local→MinIO?  
25. Chejori AWS real cutover?

---

## Senario-ha

### A) Upload document personel  
Dejban → DCC Upload → PutObject `private/Personnels/...` → DB Id → save on Personnel.

### B) Download private ba FE modern  
Presign endpoint → URL → browser MinIO GET → TTL expire → dobare begir.

### C) Avatar to report  
DB path relative → `<img src="/files/...">` → YARP → DCC public → MinIO.

### D) Dev bedune MinIO  
`Provider=Local` → uploads folder; presign fail → stream fallback.

### E) Cutover  
Migrate script copy keys → flip Provider → smoke presign + /files.

---

## Mini lab

1. `docker compose` MinIO + init — console `19001`  
2. DCC appsettings S3 + PublicEndpoint  
3. Upload az Swagger/FE — object to bucket  
4. Presign curl ba JWT — URL ra to browser baz kon  
5. `PublicEndpoint` ra eshtebah kon → 403 bebin  
6. `/files/...` avatar  
7. Provider Local — `PresignNotSupported`  

---

## Resume

**kutah:**

> Built an S3-compatible storage layer for DCC on MinIO using a provider-agnostic `IFileStorage`, with Postgres metadata, path-based public/private layout, YARP-proxied public `/files`, and authenticated short-lived presigned downloads signed against the browser-facing endpoint.

**bullet-ha:**

- Switched DCC from local disk to MinIO via AWS SDK (`ForcePathStyle`, bucket `dcc-files`) behind `Storage:Provider`  
- Separated metadata (`FileEntity`) from object bytes; SHA-256 on save  
- Implemented presigned GET with authZ-first design and `PublicEndpoint` signing to avoid 403  
- Kept stable `/files` URLs via DCC proxy instead of anonymous bucket policies  

**skill-ha:** `MinIO, Amazon S3, AWSSDK.S3, Presigned URLs, Object Storage, IFileStorage, ASP.NET Core, YARP, Docker, CORS`

---

## File-haye mohem

| chi | koja |
|---|---|
| IFileStorage / IPresignedUrlProvider | `DCC/Application/Services/` |
| S3FileStorage | `DCC/Infrastructure/Services/S3FileStorage.cs` |
| LocalFileStorage | `.../LocalFileStorage.cs` |
| StorageOptions | `DCC/Infrastructure/Options/StorageOptions.cs` |
| FileService | `DCC/Infrastructure/Services/FileService.cs` |
| Presign handler | `.../GetPresignedDownloadUrl/` |
| DccHttpClient | `Common/FileService/DccHttpClient.cs` |
| Docker MinIO | `docker-compose.yml`, `docker-compose.minio.yml` |
| CORS | `DCC/Scripts/minio-cors.json` |
| Phase docs | `DCC/docs/MINIO-PHASE*.md` |
| Gateway PublicFiles | `ApiGateway/appsettings*.json` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 07 YARP | `/files` route + DccProxy |
| 16 Tenancy | SiteId / RequireSiteMatch / X-Site-Id |
| 18 DI | Provider switch Singleton storage |
| 25 Redis | joda — cache ≠ object store |
| 26 SignalR | aks to popup base64 vs file URL tradeoff |
| 41 Files/Documents | FE + domain depth Dejban↔DCC |

---

## Chejori digest koni

1. Draw meta DB vs bytes MinIO (5 min)  
2. Read IFileStorage + DI switch (15 min)  
3. S3FileStorage Save + CreateGetUrl + PublicEndpoint (25 min)  
4. Public /files proxy path (15 min)  
5. Lab MinIO + presign (30 min)  
6. 25 soal (20 min)

---

## Glossary

| kalame | ma'ni |
|---|---|
| Object storage | zakhire ba bucket/key |
| MinIO | S3-compatible self-hosted |
| Presigned URL | URL emza-shode ba TTL |
| ForcePathStyle | endpoint/bucket/key |
| PublicEndpoint | host baraye browser sign |
| DCC | microservice-e file |
| DccProxy | YARP → DCC baraye /files |
| Orphan | object bedune DB row |

---

## Deep dive — chera sign ba PublicEndpoint

Signature-e AWS S3 **Host** (va ba'zi header-ha) ro to canonical request mizare. Age ba `http://minio:9000` sign koni va browser bere `http://localhost:19000/...`, Host fargh mikone → **SignatureDoesNotMatch / 403**.

Rah-e Dejban: client-e joda baraye signing ba `ServiceURL = PublicEndpoint`. Dakhel-e cluster, Put/Get ba `Endpoint` dakheli mimune.

---

## Deep dive — buffering + hash

`StorageHashing.BufferAndHashAsync` stream ro mikhune, SHA256 midahad, `MemoryStream` baraye Put (S3 ContentLength mikhad).  
File-e multi-GB: in model memory-heavy-e — production bozorg momkene multipart upload + streaming hash bekhade (gap-e possible).

---

## Deep dive — ISP (`IPresignedUrlProvider`)

Na hame storage-ha presign daran. Joda kardan az `IFileStorage` yani Local majbur nist empty implement kone ba throw; `IsSupported` + error domain. Client modern: try presign → catch → stream.

---

## Anti-pattern-ha

```csharp
// BAD: FE AccessKey MinIO
// GOOD: FE → DCC auth → presign ya /files proxy

// BAD: url = signed.Replace("minio:9000", "localhost:19000")
// GOOD: sign ba PublicEndpoint az avval

// BAD: anonymous GetObject rooye hame bucket
// GOOD: private auth; public faghat az DCC path guard

// BAD: save path Windows `\` to DB baraye URL
// GOOD: always `/` (FileService Replace)
```

---

## Interview 60s

> «We store file bytes in MinIO behind an IFileStorage abstraction in the DCC service, with metadata in Postgres. Private downloads authorize in DCC then return a short-lived presigned URL signed for the browser-facing host. Public assets keep stable /files URLs through the gateway to a DCC proxy so we never open the bucket anonymously.»

---

## Quick self-test

1. Provider flag? → `Storage:Provider` Local|S3  
2. Bucket default? → `dcc-files`  
3. Presign TTL default? → 300s  
4. Public path prefix? → `public/`  
5. Chera PublicEndpoint? → valid signature for browser host  
6. Local presign? → not supported  
7. Who calls MinIO from Personnels? → nobody; DccHttpClient → DCC  
8. /files auth? → anonymous at edge; DCC serves only public/  
9. Hash field? → HashSha256  
10. ForcePathStyle MinIO? → true  

8/10+ → Day 29.

---

## Final checklist

- [ ] IFileStorage vs S3FileStorage  
- [ ] meta vs bytes  
- [ ] private stream vs presign  
- [ ] public DccProxy  
- [ ] PublicEndpoint  
- [ ] Docker minio-init + CORS  
- [ ] resume bullets  

---

## Extra — multipart / large files

AWS multipart upload baraye file-haye bozorg. Dejban alan PutObject-e yek-phase + buffer. Baraye video/huge PDF: future = CreatePutUrlAsync (presign PUT) mostaghim az browser, ya multipart server-side. Interface `CreatePutUrlAsync` **hast** — path-e upload direct Phase 5 optional; upload asli hanuz az DCC multipart form mire.

---

## Extra — versioning va soft delete

`FileEntity` soft-delete field dare; object delete physically to `DeleteFileAsync` (`fileStorage.DeleteAsync`). Purge/Restore command-ha to DCC hastan — lifecycle-e document. Object versioning-e MinIO (bucket versioning) joda-st; Dejban bishtar app-level revision (`FileRevision`) dare.

---

## Extra — observability

Log kon: bucket, key (bedune secret), duration Put/Get, presign issue count, 403 rate. Metric: DCC stream bytes vs redirect-to-presign ratio — neshun mide cutover FE cheghad pish rafte.

---

## Extra — disaster recovery

MinIO volume backup / site replication. DB backup bedune object = metadata-ye bi-fayde. Restore order: objects → DB, ya sync tool. Test restore to staging.

---

## Map — request private presign

```
FE (JWT)
  → Gateway → DCC GET Downloadfile/{id}/presigned
  → CanAccess?
  → S3FileStorage.CreateGetUrlAsync(PublicEndpoint, TTL)
  → { url, expiresAtUtc, isPresigned:true }
FE
  → GET url (MinIO)  // no Bearer
  → file bytes
```

---

## Map — request public img

```
Browser GET /files/personnels/2026-09/x.jpg
  → YARP PublicFiles (anonymous)
  → DCC /api/v1/Files/public/personnels/2026-09/x.jpg
  → guard: only public/, no ..
  → IFileStorage.OpenRead("public/personnels/...")
  → stream
```

---

## Decision guide — koja file bezaram?

| data | koja |
|---|---|
| PDF shenasname | DCC private + presign/stream |
| Avatar | DCC public + /files |
| Temp export 1-bar | DCC private + short ExpiresAt |
| Config JSON kuchik | appsettings / Options — na MinIO |
| Message queue payload | Rabbit — na file store |

---

## Lab aha

1. PublicEndpoint wrong → 403  
2. CORS off → browser red  
3. Flip Local → stream works, presign dies  
4. Delete DB row, object mimune → orphan to console  
5. `/files/../private/...` → block  

---

## What Day 28 is *not*

- FE component-e upload full (ba'd)  
- Full Stimulsoft image pipeline  
- AWS IAM policy encyclopedia  
- CDN CloudFront setup  

Focus: **DCC storage abstraction + MinIO + presign + public proxy**.

---

## Resume keywords (ATS)

`MinIO` · `Amazon S3` · `object storage` · `presigned URL` · `AWSSDK.S3` · `IFileStorage` · `multipart upload` · `CORS` · `YARP` · `Docker`

---

## Connection note — Day 41

Day 41 «Files/Documents (Dejban → DCC)» domain/UX ra omigh midahad. Inja zamin-e storage. Age har do ro bekhooni, story kamel mishe: product flow + infra.

---

## Extra — API surface-e FilesController (daqiq)

| endpoint | auth | naqsh |
|---|---|---|
| `POST UploadFile` | AllowAnonymous (dakheli) | multipart upload — size limit **1GB** |
| `POST UploadFileSecure` | authenticated | haman upload ba JWT |
| `GET Downloadfile/{id}` | auth + CanAccess | stream bytes az IFileStorage |
| `GET Downloadfile/{id}/presigned` | auth + CanAccess | URL MinIO ba TTL |
| `GET GetFileMeta/{id}` | auth | metadata bedune body |
| `DELETE DeleteFile/{id}` | auth | soft/hard delete path (protected soft) |
| `POST RestoreFile/{id}` | auth | bargardundan soft-delete |
| `DELETE PurgeFile/{id}` | AllowAnonymous labeled admin | physical purge — smell-e auth surface |
| `GET public/{**path}` | AllowAnonymous | faghat prefix public + traversal guard |

**Smell:** `UploadFile` va `PurgeFile` ba `AllowAnonymous` — ehtemalan shabake-ye dakheli / gateway auth; to mosahebe begu «edge bayad mahdud bashe; ideal = service auth ya mTLS beyn DCC va callers».

---

## Extra — FileAccessService (alan vs field-haye entity)

`FileEntity` field-haye fine-grained dare (`RequiredPermission`, `AllowedRoles`, `AllowedUsers`, `AccessExpiresAt`). To `FileAccessService` ye bakhsh az in check-ha **comment** shode — jaryan-e fa'al bishtar: authenticated + (IsPublic ya digar ghavanin-e sade) + site match to download handler.

Yani: **model-e data amade-ye ACL-e file-e**, ama hame rule-ha hatman enforce nemishan. In gap-e honest-e codebase-e — mosahebe: «entity rich-e; service layer ba'dan ghavanin-e permission ra fa'al mikone».

Download/presign handler SuperAdmin + `CanAccess` + `X-Site-Id` ra check mikone — inja focus-e amniat-e private.

---

## Extra — appsettings vs Docker

`DCC/appsettings.json` default `Provider=Local` (dev sade). Docker composecutover `Provider=S3` + Endpoint `http://minio:9000`. Localhost-e developer ke MinIO publish shode: Endpoint/PublicEndpoint har do `http://localhost:19000` mitunan yeki bashan — oon vaght CreateSigningClient haman client-e asli ro barmigardune.

---

## Extra — RequestSizeLimit 1GB

`[RequestSizeLimit(1_000_000_000)]` ru-ye upload — Kestrel/YARP ham bayad limit-hashun ba in ham-khani dashte bashan. Age gateway zudtar cut kone, client 413 migire ghabl az DCC. Checklist-e ops.

---

## Extra — OwnerService / FolderName

`OwnerService` (mesalan Personnels, Visitors) + `FolderName` baraye search va organize. Path az OwnerService sakhte mishe; FolderName bishtar metadata/UI. Search API ba keyword + ownerService filter mikone.

---

## Extra — Hash baraye chi?

1. Integrity ba'd az migrate Local→S3 (moghayese)  
2. Dedup/debug corrupt  
3. Security audit (file avaz shode?)  

Smoke migrate scripts mitunan hash-e DB ro ba object check konan.

---

## Senario F — Reporting image

Report Stimulsoft path `/files/...` dare. Ba Phase 4, hich code-e Reporting avaz nashod — faghat YARP target az StaticFiles be DccProxy raft. In **stable URL** olgu-ye architecture-e — storage posht avaz mishe, contract-e FE/report sabet.

---

## Senario G — TTL expire mid-download

Presign 5 min. Download-e file-e bozorg ke bishtar az TTL tool bekeshad — momkene nime-rah 403. Rahkar: TTL bolandtar baraye large files, ya stream az DCC, ya multipart range (pishrafte). Dejban default 300s baraye document-e ma'mooli.

---

## Jadval — Local vs S3 (Dejban vaghe'i)

| feature | Local | S3/MinIO |
|---|---|---|
| Save/Open/Delete | ✓ | ✓ |
| Presign | ✗ IsSupported=false | ✓ |
| Multi-pod share | ✗ (volume shared lazem) | ✓ |
| /files proxy | mitune StaticFiles | DccProxy → GetObject |
| Prod pishnahad | faqat dev/small | ✓ |

---

## Chejori ba Day 26/27 rabt midahad?

DeviceHub aks-e pelak ro ba **base64 to SignalR** mifreste (Day 26 smell). Ideal-e ziad: upload to DCC → URL `/files` ya presign → SignalR faghat Id/URL. Object store inja zamin-e hamin clean-up-e ayande-st.

gRPC (Day 27) ba file farghe — binary device protocol ≠ document store.

---

*Day 28 tamum. Ba'd: Day 29 — Quartz + Hangfire (amade). Fehrest: [README.md](./README.md).*
