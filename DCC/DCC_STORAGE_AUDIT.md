# DCC Storage Audit

> Phase 2 Engineering Audit — Filesystem storage, upload/download/delete flows, integrity  
> Scope: `IFileStorage`, `FileStorage`, `FileService`, and ApiGateway static file serving

---

## Audit Summary

| Severity | Count |
|----------|-------|
| Critical | 2 |
| High | 9 |
| Medium | 10 |
| Low | 5 |
| **Total** | **26** |

---

## Storage Architecture

```mermaid
flowchart TB
    subgraph Upload Flow
        U1[HTTP Multipart] --> U2[UploadFileCommandHandler]
        U2 --> U3[FileService.UploadFileAsync]
        U3 --> U4[FileStorage.SaveAsync]
        U4 --> U5[Disk: Root/public|private/OwnerService/yyyy-MM/FileName]
        U3 --> U6[ComputeSha256]
        U3 --> U7[PostgreSQL Files table]
    end

    subgraph Download Flow
        D1[DownloadFileQueryHandler] --> D2[FileAccessService]
        D2 --> D3[FileService.DownloadFileAsync]
        D3 --> D4[FileStorage.OpenReadAsync]
        D4 --> D5[Stream to HTTP response]
    end

    subgraph Static Bypass
        S1[ApiGateway /files/*] --> S2[public/ volume read-only]
    end
```

**Abstraction:** `IFileStorage` (application interface) → `FileStorage` (infrastructure, singleton)

**Provider support:** Local filesystem only — no S3, Azure Blob, or NFS abstraction.

---

## Critical Findings

### AUD-STO-001 — Path Traversal via Unsanitized FileName and OwnerService

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Category** | Security |
| **File** | `FileService.cs`, `FileStorage.cs` |
| **Class** | `FileService` / `FileStorage` |
| **Method** | `UploadFileAsync` (line 31), `SaveAsync` (lines 32–39) |
| **Problem** | `Path.Combine(baseFolder, ownerService, datePath, fileName)` accepts `../` segments. `FileStorage` joins with Root without canonical path verification. |
| **Technical impact** | Attacker with upload permission may write outside `uploads/` root. |
| **Business impact** | Full filesystem compromise on container/host. |
| **Recommendation** | Sanitize segments; use `Path.GetFullPath` and verify starts with Root + Path.DirectorySeparatorChar. |
| **Priority** | P0 |

---

### AUD-STO-002 — Public Files Served Without Authentication via ApiGateway

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Category** | Security / Architecture |
| **File** | `ApiGateway/Program.cs` |
| **Class** | N/A (top-level) |
| **Method** | Static files middleware (lines 76–96) |
| **Problem** | `/files` maps directly to `public/` subdirectory of DCC storage volume with no authentication. |
| **Technical impact** | Anyone knowing or guessing URL path ` /files/{OwnerService}/{yyyy-MM}/{fileName}` accesses content without JWT. |
| **Business impact** | Personnel/visitor photos marked `IsPublic=true` are world-readable if path is discovered. |
| **Recommendation** | Document as intentional CDN-style delivery or proxy through DCC download with signed URLs. |
| **Priority** | P0 — confirm business acceptance |

---

## High Findings

### AUD-STO-003 — Write to Disk Before Database Commit

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Consistency |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `UploadFileAsync` (lines 49–65) |
| **Problem** | Bytes persisted before metadata transaction succeeds. |
| **Technical impact** | Orphan files on DB failure; no automated cleanup. |
| **Business impact** | Storage costs; data without governance. |
| **Recommendation** | Write to temp path; commit DB; atomic rename to final path. |
| **Priority** | P1 |

---

### AUD-STO-004 — Delete Disk Before DB on Purge

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Consistency |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `PurgeFileAsync` (lines 253–257) |
| **Problem** | `fileStorage.DeleteAsync` before `ExecuteDeleteAsync`. |
| **Technical impact** | DB row survives disk deletion on failure — ghost metadata. |
| **Business impact** | Broken image links in Dejban with 404 on download. |
| **Recommendation** | Delete metadata first (tombstone), then async physical delete job. |
| **Priority** | P1 |

---

### AUD-STO-005 — Hard Delete Removes Disk Then DB Row

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Consistency |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `DeleteFileAsync` (lines 93–95) |
| **Problem** | Same ordering issue for non-protected deletes. |
| **Technical impact** | DB failure after disk delete leaves no file and lingering reference in Dejban. |
| **Recommendation** | Transactional outbox for delete notification + ordered cleanup. |
| **Priority** | P1 |

---

### AUD-STO-006 — No Hash Verification on Download

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Integrity |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `DownloadFileAsync` (lines 69–77) |
| **Problem** | SHA-256 computed at upload and stored in `HashSha256` but never verified on read. |
| **Technical impact** | Bit rot, manual disk edits, or partial writes undetected. |
| **Business impact** | Corrupted photos served without error; legal evidence integrity questionable. |
| **Recommendation** | Optional hash verify on download; periodic integrity scan job. |
| **Priority** | P2 |

---

### AUD-STO-007 — Size Metadata May Be Wrong

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Metadata |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `UploadFileAsync` (line 36) |
| **Problem** | `Size = fileStream.Length` before stream fully consumed; non-seekable streams report 0. |
| **Technical impact** | Incorrect quota/reporting; mismatch with actual bytes on disk. |
| **Recommendation** | Count bytes during `CopyToAsync` or use `IFormFile.Length`. |
| **Priority** | P2 |

---

### AUD-STO-008 — Environment-Specific Root Path Logic Fragile

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Configuration |
| **File** | `FileStorage.cs` |
| **Class** | `FileStorage` |
| **Method** | Constructor (lines 14–24) |
| **Problem** | Development AND Production use `ContentRoot/uploads`; Docker environments use `Storage:RootPath`. Docker Production env name may not match either branch. Empty string fallback if config missing. |
| **Technical impact** | Files written to unexpected location; volume mount mismatch in Docker. |
| **Business impact** | Upload succeeds but file not in shared volume — gateway static serve broken. |
| **Recommendation** | Explicit env matrix; fail startup if Root empty; align with docker-compose volume mount at `/app/uploads`. |
| **Priority** | P1 |

---

### AUD-STO-009 — Docker Volume vs Config Path Mismatch Risk

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Deployment |
| **File** | `docker-compose.docker-development.yml`, `appsettings.DockerDevelopment.json` |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | Volume mounts to `/app/uploads`; config says `Storage:RootPath: /data/dcc/files`. |
| **Technical impact** | Unless DockerDevelopment env triggers config branch correctly, files may not land on shared volume. |
| **Business impact** | ApiGateway cannot serve uploaded public files. |
| **Recommendation** | Unify on `/app/uploads` in Docker configs. |
| **Priority** | P1 |

---

### AUD-STO-010 — No Provider Abstraction Beyond IFileStorage

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Scalability |
| **File** | `IFileStorage.cs`, `FileStorage.cs` |
| **Class** | Both |
| **Method** | N/A |
| **Problem** | Local disk only; singleton binding. Multi-instance DCC deployment requires shared NFS/blob — not supported. |
| **Technical impact** | Horizontal scaling of DCC pods breaks unless all share volume. |
| **Business impact** | Cannot scale upload/download tier independently. |
| **Recommendation** | Introduce blob provider interface (S3-compatible) for cloud deployment. |
| **Priority** | P2 |

---

### AUD-STO-011 — 1 GB Upload Limit Without Streaming Throttle

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Large File Handling |
| **File** | `FilesController.cs` |
| **Class** | `FilesController` |
| **Method** | `UploadFile`, `UploadFileSecure` |
| **Problem** | `RequestSizeLimit(1_000_000_000)` allows 1 GB in memory-backed multipart before streaming to disk. |
| **Technical impact** | Memory pressure under concurrent large uploads; OOM kill risk. |
| **Business impact** | Service crash under bulk photo/video upload scenarios. |
| **Recommendation** | Configure Kestrel `MultipartBodyLengthLimit`, stream directly to disk, reduce limit per business need. |
| **Priority** | P2 |

---

## Medium Findings

### AUD-STO-012 — FileMode.Create Overwrites Without Backup

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Upload Flow |
| **File** | `FileStorage.cs` |
| **Class** | `FileStorage` |
| **Method** | `SaveAsync` (line 38) |
| **Problem** | `FileMode.Create` truncates existing file at same path silently. |
| **Technical impact** | Re-upload same path replaces bytes; DB upsert may desync revision history. |
| **Business impact** | Accidental overwrite without version retention (content versioning not implemented). |
| **Recommendation** | Use unique names (UUID prefix) or versioned filenames. |
| **Priority** | P2 |

---

### AUD-STO-013 — FolderName Not Used in Physical Path

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Folder Naming |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `UploadFileAsync` (lines 29–31) |
| **Problem** | `FolderName` stored in DB only; physical path uses `OwnerService/datePath/FileName`. Logical folder hierarchy not reflected on disk. |
| **Technical impact** | Operational confusion; backup policies by folder impossible. |
| **Business impact** | `FolderName` misleading for ops teams browsing disk. |
| **Recommendation** | Include `FolderName` in path or document as logical-only field. |
| **Priority** | P3 |

---

### AUD-STO-014 — File Naming Predictable

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Security |
| **File** | Dejban consumers + `FileService` |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | Consumers upload `{entityId}.jpg` — predictable names enable static URL guessing on `/files`. |
| **Technical impact** | Enumeration of public photos if OwnerService and month known. |
| **Business impact** | Privacy risk for personnel/visitor photos. |
| **Recommendation** | Use non-guessable storage names; keep original name in metadata only. |
| **Priority** | P2 |

---

### AUD-STO-015 — ContentType Trusted From Client

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Security |
| **File** | `UploadFileCommandHandler.cs` |
| **Class** | `UploadFileCommandHandler` |
| **Method** | `Handle` (line 35) |
| **Problem** | `command.File.ContentType` stored and returned on download without magic-byte validation. |
| **Technical impact** | XSS if browser renders downloaded file with wrong MIME; malware upload as image/jpeg. |
| **Business impact** | Security scan bypass. |
| **Recommendation** | Validate file signature; serve with `Content-Disposition: attachment` for non-image types. |
| **Priority** | P2 |

---

### AUD-STO-016 — No Virus/Malware Scanning Hook

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Security |
| **File** | Upload pipeline |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | No ClamAV or similar integration in upload path. |
| **Business impact** | Malware storage liability. |
| **Recommendation** | Add scanning middleware or async scan before marking file available. |
| **Priority** | P3 |

---

### AUD-STO-017 — Buffered Upload via CopyToAsync Only

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Streaming |
| **File** | `FileStorage.cs` |
| **Class** | `FileStorage` |
| **Method** | `SaveAsync` (line 39) |
| **Problem** | Streams to disk with 81920 buffer — acceptable streaming but entire multipart already buffered by ASP.NET model binding. |
| **Technical impact** | Not true end-to-end streaming from client to disk. |
| **Recommendation** | Use `MultipartReader` manual streaming for large files. |
| **Priority** | P3 |

---

### AUD-STO-018 — Download Stream Lifetime

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Resource Management |
| **File** | `FileStorage.cs`, `FilesController.cs` |
| **Class** | `FileStorage` / `FilesController` |
| **Method** | `OpenReadAsync`, `Downloadfile` |
| **Problem** | `FileStream` returned through handler to MVC `File()` — disposal depends on framework. |
| **Technical impact** | Handle exhaustion under error paths. |
| **Recommendation** | Verify disposal; use `FileStreamResult` with callback. |
| **Priority** | P3 |

---

### AUD-STO-019 — Exists() Method Never Called

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Dead Code |
| **File** | `IFileStorage.cs`, `FileStorage.cs` |
| **Class** | `FileStorage` |
| **Method** | `Exists` |
| **Problem** | Interface method implemented but unused in codebase. |
| **Priority** | P4 |

---

### AUD-STO-020 — Soft Delete Retains Bytes Indefinitely

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Delete Flow |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `SoftDeleteFileAsync` |
| **Problem** | Soft delete marks metadata only; disk space never reclaimed until purge. |
| **Technical impact** | Storage grows monotonically. |
| **Business impact** | Increased storage costs; no retention policy enforcement. |
| **Recommendation** | Scheduled purge of soft-deleted files after retention period. |
| **Priority** | P3 |

---

### AUD-STO-021 — PublicUrl in Upload Response Uses API Path Not Static Path

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | API Contract |
| **File** | `UploadFileCommandHandler.cs` |
| **Class** | `UploadFileCommandHandler` |
| **Method** | `Handle` (lines 53–55) |
| **Problem** | `PublicUrl` returns `/api/v1.0/Files/Downloadfile/{id}` requiring auth, not `/files/...` static path. |
| **Technical impact** | Consumers expecting direct public URL get authenticated endpoint. |
| **Business impact** | Frontend may embed wrong URL for public assets. |
| **Recommendation** | Return static URL pattern for public files when gateway path known. |
| **Priority** | P3 |

---

## Low Findings

### AUD-STO-022 — SHA256 Computed Synchronously After Async Save

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Performance |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `ComputeSha256` (lines 113–117) |
| **Problem** | Blocking `File.OpenRead` + hash after async save; large files block thread pool. |
| **Recommendation** | Use async hash computation. |
| **Priority** | P3 |

---

### AUD-STO-023 — Buffer Size Hardcoded 81920

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Configuration |
| **File** | `FileStorage.cs` |
| **Class** | `FileStorage` |
| **Method** | `SaveAsync`, `OpenReadAsync` |
| **Problem** | Magic number 81920 without named constant or config. |
| **Priority** | P4 |

---

### AUD-STO-024 — DeleteAsync Silent No-Op When Missing

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Delete Flow |
| **File** | `FileStorage.cs` |
| **Class** | `FileStorage` |
| **Method** | `DeleteAsync` (lines 53–60) |
| **Problem** | No error if file already absent — idempotent but hides disk/DB desync. |
| **Recommendation** | Return bool; log warning on missing file during purge. |
| **Priority** | P4 |

---

### AUD-STO-025 — No Storage Quota per OwnerService

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Scalability |
| **File** | N/A |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | No limit on total storage per service/site. |
| **Priority** | P4 |

---

### AUD-STO-026 — IFileStorage Singleton Holds IWebHostEnvironment

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Dependency Injection |
| **File** | `FileStorage.cs` |
| **Class** | `FileStorage` |
| **Method** | Constructor |
| **Problem** | Singleton service captures `IWebHostEnvironment` at construction — standard pattern, acceptable. |
| **Priority** | P4 — informational |

---

## Flow Analysis

### Upload Flow

| Step | Component | Risk |
|------|-----------|------|
| 1 | Multipart binding | Memory buffer |
| 2 | Validation | No path/content validation |
| 3 | OpenReadStream | — |
| 4 | Path build | Traversal risk |
| 5 | SaveAsync | Overwrite, no temp file |
| 6 | Hash | Blocking, post-write |
| 7 | DB upsert | Orphan disk on fail |
| 8 | IsProtected save | Second transaction |

### Download Flow

| Step | Component | Risk |
|------|-----------|------|
| 1 | GetFileEntityAsync | No soft-delete check |
| 2 | FileAccessService | Permissive for private files |
| 3 | OpenReadAsync | No hash verify |
| 4 | File() result | Stream disposal |

### Delete Flow

| Type | Disk | DB | Audit |
|------|------|-----|-------|
| Hard delete | Delete first | Remove row | None |
| Soft delete | Retain | Flag + revision | FileRevision |
| Purge | Delete first | ExecuteDelete | None |
| Restore | Retain | Unflag + revision | FileRevision |

---

## Storage Path Convention

```
{Root}/
  public/
    {OwnerService}/
      {yyyy-MM}/
        {FileName}
  private/
    {OwnerService}/
      {yyyy-MM}/
        {FileName}
```

**Consumers in production:**

| OwnerService | FolderName (logical) | FileName |
|--------------|---------------------|----------|
| Dejban.Personnels | personnel/photos | `{personnelId}.jpg` |
| Dejban.Visitors | visitors/photos | `{visitorId}.jpg` |
| Dejban.Visitors | visitors/companion-photos | `{scheduleId}-companion-{n}.jpg` |

---

## Integrity Model

| Mechanism | Implemented | Enforced |
|-----------|-------------|----------|
| SHA-256 at upload | Yes | No verify on download |
| Unique StoragePath index | Yes | Yes |
| Content length | Partial | Often wrong |
| MIME validation | No | — |
| ETag / checksum header | No | — |

---

## Scalability Assessment

| Dimension | Current capability | Limit |
|-----------|-------------------|-------|
| Horizontal DCC replicas | Requires shared volume | Local disk per pod fails |
| Max file size | 1 GB configured | Memory bound |
| Concurrent uploads | Limited by disk I/O | No queue |
| Total storage | Unbounded | No quota |
| CDN integration | Static /files only | No signed URLs |

---

## Test Scenarios for Future QA

1. Upload with `FileName=../../../tmp/evil` — expect rejection
2. Upload 1 GB file with 10 concurrent clients — memory profile
3. Kill DB during upload — count orphan files
4. Purge during DB outage — verify metadata state
5. Access public file via `/files/...` without JWT — expect 200
6. Access private file via static path — expect 404 or not found
7. Docker deployment — verify file lands on shared volume
8. Re-upload same filename same month — verify overwrite behavior

---

## Related Audits

- [Code Audit](./DCC_CODE_AUDIT.md)
- [Database Audit](./DCC_DATABASE_AUDIT.md)
- [Event Audit](./DCC_EVENT_AUDIT.md)
