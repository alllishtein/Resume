# DCC Code Audit

> Phase 2 Engineering Audit — Application, Domain, Infrastructure, Presentation  
> Scope: `Microservices/DCC/` (all 54 source files) + direct consumer contracts in `Common/`  
> No code was modified. Findings are recommendations only.

---

## Audit Summary

| Severity | Count |
|----------|-------|
| Critical | 5 |
| High | 14 |
| Medium | 18 |
| Low | 12 |
| **Total** | **49** |

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security / Authorization | 4 | 4 | 2 | 0 |
| Architecture / SOLID | 0 | 4 | 6 | 3 |
| Reliability / Transactions | 1 | 3 | 4 | 1 |
| Code Quality / Maintainability | 0 | 3 | 4 | 6 |
| Async / Cancellation | 0 | 0 | 2 | 2 |

---

## Critical Findings

### AUD-CODE-001 — Unauthenticated Purge Endpoint at Controller Level

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Category** | Security / Authorization |
| **File** | `Microservices/DCC/Controllers/FilesController.cs` |
| **Class** | `FilesController` |
| **Method** | `PurgeFile` (lines 77–84) |
| **Problem** | `[AllowAnonymous]` is applied on `PurgeFile`, bypassing the `[Authorize]` requirement inherited from `ApiController`. Authorization relies entirely on handler-level SUPERADMIN detection. |
| **Technical impact** | Unauthenticated callers reach application logic for irreversible file destruction. Any bug or bypass in the handler grants full purge capability without a JWT. |
| **Business impact** | Permanent loss of audit evidence, personnel photos, visitor records references, and potential regulatory exposure. |
| **Recommendation** | Remove `[AllowAnonymous]` from `PurgeFile`. Enforce SUPERADMIN via authorization policy at the controller/filter level in addition to handler checks. |
| **Priority** | P0 — immediate |

---

### AUD-CODE-002 — Delete/Restore Without Authorization Beyond Authentication

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Category** | Security / Authorization |
| **File** | `Microservices/DCC/Application/Files/Commands/DeleteFile/DeleteFileCommandHandler.cs` |
| **Class** | `DeleteFileCommandHandler` |
| **Method** | `Handle` (lines 20–28) |
| **Problem** | Any authenticated user can delete any file by GUID. No ownership, role, site, or permission check. Same applies to `RestoreFileCommandHandler.Handle`. |
| **Technical impact** | Horizontal privilege escalation — any valid JWT is sufficient to delete or restore files belonging to other services/sites/users. |
| **Business impact** | Malicious or compromised accounts can destroy personnel/visitor photos and protected records. |
| **Recommendation** | Introduce authorization consistent with download rules (owner service, creator, site match, roles). Apply before invoking `FileService`. |
| **Priority** | P0 — immediate |

**Also affects:**

- `Microservices/DCC/Application/Files/Commands/RestoreFile/RestoreFileCommandHandler.cs` — `Handle` (lines 20–27)

---

### AUD-CODE-003 — GetFileMeta Exposes Metadata Without Access Control

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Category** | Security / Authorization |
| **File** | `Microservices/DCC/Application/Files/Queries/GetFileMeta/GetFileMetaQueryHandler.cs` |
| **Class** | `GetFileMetaQueryHandler` |
| **Method** | `Handle` (lines 9–15) |
| **Problem** | Metadata (storage path, owner, size, hash, creator) is returned for any file ID with no call to `IFileAccessService`. |
| **Technical impact** | Information disclosure aids targeted attacks (path guessing, correlation with static `/files` serving). |
| **Business impact** | Private file metadata visible to any authenticated user; violates least-privilege for multi-tenant deployment. |
| **Recommendation** | Apply the same access gate used in `DownloadFileQueryHandler` before returning metadata. |
| **Priority** | P0 — immediate |

---

### AUD-CODE-004 — Private Files Accessible to Any Authenticated User

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Category** | Security / Authorization |
| **File** | `Microservices/DCC/Application/Services/FileAccessService.cs` |
| **Class** | `FileAccessService` |
| **Method** | `CanAccessAsync` (lines 19–100) |
| **Problem** | For non-public files where `RequireSiteMatch` is false or `SiteId` is null, access is granted by default (line 98–99). Role, permission, user whitelist, and expiry checks are commented out (lines 33–86). |
| **Technical impact** | `IsPublic = false` provides no meaningful protection today. All private files are downloadable by any authenticated caller. |
| **Business impact** | Document control center fails its core confidentiality requirement for non-public assets. |
| **Recommendation** | Default-deny for non-public files. Uncomment and complete RBAC checks or enforce `RequireSiteMatch` on all uploads from consumers. |
| **Priority** | P0 — immediate |

---

### AUD-CODE-005 — Disk-Before-Database Upload Without Compensation

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Category** | Reliability / Transactions |
| **File** | `Microservices/DCC/Infrastructure/Services/FileService.cs` |
| **Class** | `FileService` |
| **Method** | `UploadFileAsync` (lines 49–65) |
| **Problem** | File bytes are written to disk (`fileStorage.SaveAsync`) before `SaveChangesAsync`. If DB save fails, an orphan file remains on disk with no metadata row. |
| **Technical impact** | Storage leak, inconsistent state, no rollback of filesystem write. Repeated failures fill disk. |
| **Business impact** | Unreferenced files consume storage; no audit trail for uploaded content that failed to persist. |
| **Recommendation** | Use transactional outbox pattern for metadata, temp-file + commit rename, or background orphan cleanup job. Wrap in explicit transaction where possible. |
| **Priority** | P0 — before production scale |

---

## High Findings

### AUD-CODE-006 — Path Traversal Risk in Storage Path Construction

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Security |
| **File** | `Microservices/DCC/Infrastructure/Services/FileService.cs` / `FileStorage.cs` |
| **Class** | `FileService` / `FileStorage` |
| **Method** | `UploadFileAsync` (line 31), `SaveAsync` (lines 27–39) |
| **Problem** | `OwnerService`, `FileName`, and path segments from the upload command are concatenated without sanitization. `FileStorage` does not verify that resolved path stays under `Root`. |
| **Technical impact** | Crafted `FileName` values like `../../sensitive` may write or read outside the intended storage root. |
| **Business impact** | Arbitrary file write/read on the server filesystem. |
| **Recommendation** | Reject path separators and `..` in user inputs; resolve full path and verify prefix against `Root`. |
| **Priority** | P1 |

---

### AUD-CODE-007 — Inconsistent SUPERADMIN Role Detection

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Security / Magic Strings |
| **File** | `Microservices/DCC/Application/Files/Commands/PurgeFile/PurgeFileCommandHandler.cs` |
| **Class** | `PurgeFileCommandHandler` |
| **Method** | `Handle` (lines 26–28) |
| **Problem** | Uses hardcoded `"SUPERADMIN"` with case-sensitive equality. `DownloadFileQueryHandler.IsSuperAdmin` uses `ConfigConstants.DefaultAdminRoleName` (`"SuperAdmin"`) with case-insensitive comparison. |
| **Technical impact** | SuperAdmin users may pass download bypass but fail purge, or vice versa depending on claim casing. |
| **Business impact** | Admin operations inconsistently available; security policy confusion. |
| **Recommendation** | Centralize role-check logic; use `ConfigConstants.DefaultAdminRoleName` and shared extension method. |
| **Priority** | P1 |

**Related:** `DownloadFileQueryHandler.IsSuperAdmin` (lines 39–47) — uses magic string `"role"` claim type.

---

### AUD-CODE-008 — Soft-Deleted Files Remain Downloadable

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Business Rules |
| **File** | `Microservices/DCC/Application/Files/Queries/DownloadFile/DownloadFileQueryHandler.cs` |
| **Class** | `DownloadFileQueryHandler` |
| **Method** | `Handle` (lines 18–36) |
| **Problem** | No check for `FileEntity.IsDeleted` before serving content. |
| **Technical impact** | Soft delete is metadata-only; bytes remain accessible via download API. |
| **Business impact** | "Deleted" protected files are still retrievable, undermining retention and compliance policies. |
| **Recommendation** | Return `FileNotFound` or `AccessDenied` when `IsDeleted == true` unless caller has elevated restore/purge role. |
| **Priority** | P1 |

---

### AUD-CODE-009 — Application Layer Depends on Concrete Infrastructure Service

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Clean Architecture / SOLID (DIP) |
| **File** | All handlers under `Microservices/DCC/Application/Files/` |
| **Class** | e.g. `UploadFileCommandHandler`, `DownloadFileQueryHandler` |
| **Method** | Constructor injection |
| **Problem** | Handlers inject concrete `FileService` from `DCC.Infrastructure.Services` instead of an application-layer abstraction (e.g. `IFileService`). |
| **Technical impact** | Application layer coupled to infrastructure; unit testing requires DB/filesystem; violates dependency inversion. |
| **Business impact** | Higher cost and risk for changes, testing, and alternative storage backends. |
| **Recommendation** | Define `IFileService` (or split read/write ports) in Application; implement in Infrastructure. |
| **Priority** | P1 |

---

### AUD-CODE-010 — UploadFileCommandHandler Injects DbContext Directly

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Clean Architecture / Transaction Boundaries |
| **File** | `Microservices/DCC/Application/Files/Commands/UploadFile/UploadFileCommandHandler.cs` |
| **Class** | `UploadFileCommandHandler` |
| **Method** | `Handle` (lines 47–48) |
| **Problem** | Handler calls `_context.SaveChangesAsync` after `FileService.UploadFileAsync` already saved. Two separate save points for one operation; `IsProtected` update is outside `FileService` transaction. |
| **Technical impact** | Partial state if second save fails (file on disk + DB row without `IsProtected`). Leaks persistence concern into handler. |
| **Business impact** | Protected flag may not persist; inconsistent file lifecycle state. |
| **Recommendation** | Move `IsProtected` assignment into `FileService.UploadFileAsync`; single save boundary per command. |
| **Priority** | P1 |

---

### AUD-CODE-011 — Purge Deletes Disk Before Database

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Reliability / Transactions |
| **File** | `Microservices/DCC/Infrastructure/Services/FileService.cs` |
| **Class** | `FileService` |
| **Method** | `PurgeFileAsync` (lines 253–257) |
| **Problem** | Filesystem delete precedes `ExecuteDeleteAsync`. DB failure leaves metadata for deleted bytes. |
| **Technical impact** | Orphan DB rows pointing to missing files; consumers retain valid-looking `FileId` references. |
| **Business impact** | Broken avatar/image links with no recovery path. |
| **Recommendation** | Delete DB first (soft-mark purged) then async physical delete, or use two-phase commit / outbox cleanup job. |
| **Priority** | P1 |

---

### AUD-CODE-012 — GlobalExceptionHandler Exposes Exception Messages

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Security / Exception Handling |
| **File** | `Microservices/DCC/Abstractions/Exceptions/GlobalExceptionHandler.cs` |
| **Class** | `GlobalExceptionHandler` |
| **Method** | `TryHandleAsync` (lines 17–34) |
| **Problem** | All unhandled exceptions return `Detail = exception.Message` to clients. |
| **Technical impact** | Stack-sensitive information, connection strings, or internal paths may leak in production. |
| **Business impact** | Aids attackers in reconnaissance. |
| **Recommendation** | Return generic message in non-development environments; log full exception server-side only. |
| **Priority** | P1 |

---

### AUD-CODE-013 — No Test Project or Testability Hooks

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Testability |
| **File** | `PG_Microservices.slnx` / entire DCC module |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | DCC has no unit, integration, or architecture test project. Concrete dependencies on `FileService`, `FileStorage`, and `ApplicationDbContext` prevent isolated testing. |
| **Technical impact** | Regressions in authorization and storage flows undetected until manual QA. |
| **Business impact** | High risk deploying security fixes without automated verification. |
| **Recommendation** | Add integration tests for auth matrix; unit tests for `FileAccessService` and path validation. |
| **Priority** | P1 |

---

### AUD-CODE-014 — UploadFile and UploadFileSecure Are Identical

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | API Design / Security |
| **File** | `Microservices/DCC/Controllers/FilesController.cs` |
| **Class** | `FilesController` |
| **Method** | `UploadFile` (lines 26–33), `UploadFileSecure` (lines 36–43) |
| **Problem** | Both endpoints invoke the same command with identical authorization. Naming implies different trust levels but none exists. |
| **Technical impact** | Misleading API contract; internal/service upload path not distinguished from user upload. |
| **Business impact** | Integrators may assume incorrect security model. |
| **Recommendation** | Differentiate auth (service token, m2m policy) or consolidate to one endpoint. |
| **Priority** | P2 |

---

### AUD-CODE-015 — SiteId Assigned from First JWT Site Only

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Multi-Tenancy |
| **File** | `Microservices/DCC/Application/Files/Commands/UploadFile/UploadFileCommandHandler.cs` |
| **Class** | `UploadFileCommandHandler` |
| **Method** | `Handle` (lines 25–26, 44) |
| **Problem** | `siteIds.FirstOrDefault()` picks an arbitrary site when user belongs to multiple sites. |
| **Technical impact** | File may be associated with wrong site; `RequireSiteMatch` enforcement becomes incorrect. |
| **Business impact** | Cross-site data leakage or access denial for legitimate users. |
| **Recommendation** | Require explicit `SiteId` in upload command or use header `X-Site-Ids` intersection. |
| **Priority** | P2 |

---

### AUD-CODE-016 — Download Uses Header Site IDs; Upload Uses JWT Site IDs

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Consistency / Authorization |
| **File** | `DownloadFileQueryHandler.cs` vs `UploadFileCommandHandler.cs` |
| **Class** | Both handlers |
| **Method** | `Handle` |
| **Problem** | Download checks `GetHeaderSiteIds()`; upload assigns site from `GetUserSiteIds()`. Inconsistent tenancy semantics. |
| **Technical impact** | Site-scoped access behaves differently on read vs write paths. |
| **Business impact** | Users may upload to one site context but fail to download in another. |
| **Recommendation** | Align on single site-resolution strategy (middleware effective sites). |
| **Priority** | P2 |

---

### AUD-CODE-017 — DbInitializer Swallows Migration Failures

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Reliability / Logging |
| **File** | `Microservices/DCC/Abstractions/Extensions/DbExtensions.cs` |
| **Class** | `DbExtensions` |
| **Method** | `DbInitializer` (lines 9–27) |
| **Problem** | All exceptions caught; only `Console.WriteLine(e.Message)`. Service starts even if migrations fail. Fixed 10-second delay blocks startup. |
| **Technical impact** | DCC runs against wrong schema silently; health checks absent so orchestrator marks pod healthy. |
| **Business impact** | Runtime failures in production with no clear root cause. |
| **Recommendation** | Fail fast on migration error; use structured logging; replace fixed delay with DB retry policy. |
| **Priority** | P1 |

---

### AUD-CODE-018 — ClaimService Registered but Never Used

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Dead Code / Wrong Abstraction |
| **File** | `Microservices/DCC/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| **Class** | `ServiceCollectionExtensions` |
| **Method** | `AddInfrastructure` (line 99) |
| **Problem** | `IClaimService` → `ClaimService` registered; no handler or service injects it. |
| **Technical impact** | Dead DI registration; misleading signal that claim-based access is implemented. |
| **Business impact** | Developers assume site claims enrich access decisions — they do not. |
| **Recommendation** | Wire into `FileAccessService` or remove registration until needed. |
| **Priority** | P2 |

---

### AUD-CODE-019 — LinkProvider Registered but Unused

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Dead Code |
| **File** | `Microservices/DCC/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| **Class** | `ServiceCollectionExtensions` |
| **Method** | `AddPresentation` (line 88) |
| **Problem** | `LinkProvider` singleton registered with no references in DCC. |
| **Technical impact** | Unnecessary DI graph node; copied from other services without purpose. |
| **Business impact** | None direct; indicates incomplete port from template. |
| **Recommendation** | Remove unless HATEOAS links planned. |
| **Priority** | P3 |

---

## Medium Findings

### AUD-CODE-020 — Anemic Domain Model

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | DDD / Entity Encapsulation |
| **File** | `Microservices/DCC/Domain/Entities/FileEntity.cs` |
| **Class** | `FileEntity` |
| **Method** | N/A (all properties public get/set) |
| **Problem** | No encapsulation, invariants, or domain methods. All lifecycle logic in `FileService`. |
| **Technical impact** | Domain purity violated; entity can be put in invalid states anywhere. |
| **Business impact** | Business rules scattered; harder to enforce consistently. |
| **Recommendation** | Introduce factory/methods: `FileEntity.Create(...)`, `MarkDeleted(...)`, etc. |
| **Priority** | P2 |

---

### AUD-CODE-021 — Large FileService God Class

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | SOLID (SRP) |
| **File** | `Microservices/DCC/Infrastructure/Services/FileService.cs` |
| **Class** | `FileService` |
| **Method** | Multiple (266 lines) |
| **Problem** | Single class handles upload, download, delete, soft delete, restore, purge, search, hashing, revision creation. |
| **Technical impact** | High change risk; difficult to test individual concerns. |
| **Business impact** | Slower feature delivery for storage/access evolution. |
| **Recommendation** | Split into `FileWriteService`, `FileReadService`, `FileLifecycleService`, or similar. |
| **Priority** | P2 |

---

### AUD-CODE-022 — Dead Code: CreateRevisionAsync

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Dead Code |
| **File** | `Microservices/DCC/Infrastructure/Services/FileService.cs` |
| **Class** | `FileService` |
| **Method** | `CreateRevisionAsync` (lines 120–142) |
| **Problem** | Private method never called. Revision logic duplicated inline in `SoftDeleteFileAsync` and `RestoreFileAsync`. |
| **Technical impact** | Duplicated snapshot serialization logic; maintenance drift risk. |
| **Business impact** | Inconsistent audit if one path updated and not the other. |
| **Recommendation** | Use single revision helper or remove dead method. |
| **Priority** | P3 |

---

### AUD-CODE-023 — SearchFilesAsync Has No API Exposure

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Dead Code |
| **File** | `Microservices/DCC/Infrastructure/Services/FileService.cs` |
| **Class** | `FileService` |
| **Method** | `SearchFilesAsync` (lines 100–111) |
| **Problem** | Public method with no controller/handler caller. |
| **Technical impact** | Unused surface area; `FileSearchResultDTO` in Common also unused by DCC. |
| **Business impact** | None until exposed without auth (future risk). |
| **Recommendation** | Remove or expose via authenticated query with pagination and access filters. |
| **Priority** | P3 |

---

### AUD-CODE-024 — GetFileMeta Returns ErrorOr object

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Type Safety / API Contract |
| **File** | `Microservices/DCC/Application/Files/Queries/GetFileMeta/GetFileMetaQuery.cs` |
| **Class** | `GetFileMetaQuery` |
| **Method** | N/A |
| **Problem** | `IRequest<ErrorOr<object>>` loses compile-time type safety; OpenAPI schema less precise. |
| **Technical impact** | Client code cannot rely on stable response shape without documentation. |
| **Business impact** | Integration fragility for consumers of metadata API. |
| **Recommendation** | Return `ErrorOr<FileInfoDTO>` or dedicated response record. |
| **Priority** | P3 |

---

### AUD-CODE-025 — Unused Variable in DeleteFileCommandHandler

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Code Quality |
| **File** | `Microservices/DCC/Application/Files/Commands/DeleteFile/DeleteFileCommandHandler.cs` |
| **Class** | `DeleteFileCommandHandler` |
| **Method** | `Handle` (line 23) |
| **Problem** | `var roles = ...Claims.ToList()` assigned but never used. |
| **Technical impact** | Suggests incomplete authorization implementation. |
| **Business impact** | None direct. |
| **Recommendation** | Remove or implement intended role check. |
| **Priority** | P3 |

---

### AUD-CODE-026 — No Validators for Restore/Purge/Download/GetFileMeta

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Validation Strategy |
| **File** | `Microservices/DCC/Application/Files/` |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | Only `UploadFileCommand` and `DeleteFileCommand` have FluentValidation validators. Route-bound Guids rely on ASP.NET binding only. |
| **Technical impact** | Empty GUID could reach handlers depending on binding behavior. |
| **Business impact** | Low immediate risk; inconsistent validation approach. |
| **Recommendation** | Add validators for all commands/queries or use centralized route constraint validation. |
| **Priority** | P3 |

---

### AUD-CODE-027 — CancellationToken Not Propagated to Infrastructure

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Async Correctness |
| **File** | `Microservices/DCC/Infrastructure/Services/FileService.cs` |
| **Class** | `FileService` |
| **Method** | All public async methods |
| **Problem** | No `CancellationToken` parameters. Handlers accept token but do not pass to EF or storage I/O. |
| **Technical impact** | Client disconnect does not cancel long uploads/downloads; resource waste under load. |
| **Business impact** | Degraded scalability during large file transfers. |
| **Recommendation** | Thread `CancellationToken` through FileService → FileStorage → EF calls. |
| **Priority** | P2 |

---

### AUD-CODE-028 — fileStream.Length Used for Size Before Read

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Correctness |
| **File** | `Microservices/DCC/Infrastructure/Services/FileService.cs` |
| **Class** | `FileService` |
| **Method** | `UploadFileAsync` (line 36) |
| **Problem** | `Size = fileStream.Length` assumes seekable stream. Non-seekable streams may return 0 or throw. |
| **Technical impact** | Incorrect size metadata stored; hash/size audit unreliable. |
| **Business impact** | Reporting and quota features based on `Size` will be wrong. |
| **Recommendation** | Compute size during copy or use `IFormFile.Length` from handler. |
| **Priority** | P2 |

---

### AUD-CODE-029 — Mapster Global Configuration Side Effects

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Mapping |
| **File** | `Microservices/DCC/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| **Class** | `ServiceCollectionExtensions` |
| **Method** | `AddApplication` (lines 118–119) |
| **Problem** | `TypeAdapterConfig.GlobalSettings` mutated at startup — global singleton affects entire AppDomain. |
| **Technical impact** | Test isolation issues; conflicts if multiple modules share process. |
| **Business impact** | Low in dedicated microservice deployment. |
| **Recommendation** | Use scoped Mapster config or explicit mapping profiles. |
| **Priority** | P3 |

---

### AUD-CODE-030 — LocalizerExtensions Static Service Locator

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Anti-Pattern |
| **File** | `Microservices/DCC/Abstractions/Extensions/LocalizerExtensions.cs` |
| **Class** | `LocalizerExtensions` |
| **Method** | `InitializeLocalizerExtension`, `Localizer` (lines 11–20) |
| **Problem** | Static `_localizer` set at startup; `Errors.Files` uses `LocalizerExtensions.Localizer()` statically. |
| **Technical impact** | Hidden dependency; difficult to test error messages; thread-safety depends on single init. |
| **Business impact** | None in production; testability impact. |
| **Recommendation** | Inject `IStringLocalizer` into error factory or handlers. |
| **Priority** | P3 |

---

### AUD-CODE-031 — Empty Placeholder Types

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Dead Code |
| **File** | `Microservices/DCC/Abstractions/Helpers/Utils.cs`, `Abstractions/Constants/ConfigConstants.cs` |
| **Class** | `Utils`, `ConfigConstants` |
| **Method** | N/A |
| **Problem** | Empty classes with no members (DCC-local `ConfigConstants`; global one is in Common). |
| **Technical impact** | Namespace confusion with `Common.Abstractions.Constants.ConfigConstants`. |
| **Business impact** | Developer confusion. |
| **Recommendation** | Remove or populate with DCC-specific constants. |
| **Priority** | P4 |

---

### AUD-CODE-032 — No Health Check Endpoints

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Production Readiness |
| **File** | `Microservices/DCC/Program.cs` |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | Unlike `Dejban.Api`, DCC does not expose `/health` for Postgres, Redis, RabbitMQ, or storage. |
| **Technical impact** | Orchestrator cannot detect degraded dependencies. |
| **Business impact** | Traffic routed to unhealthy instances. |
| **Recommendation** | Add ASP.NET health checks for DB, Redis, disk writable. |
| **Priority** | P2 |

---

### AUD-CODE-033 — Single-Project Layer Boundaries Not Enforced

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Clean Architecture |
| **File** | `Microservices/DCC/DCC.csproj` |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | Domain, Application, Infrastructure, Controllers compile into one assembly with no project-level boundary enforcement. |
| **Technical impact** | Any layer can reference any other; architecture erodes over time. |
| **Business impact** | Long-term maintainability vs Dejban modules. |
| **Recommendation** | Consider multi-project layout or NetArchTest rules like Dejban. |
| **Priority** | P3 |

---

### AUD-CODE-034 — Restore Returns Result.Deleted Semantically Wrong

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Naming / API Semantics |
| **File** | `RestoreFileCommandHandler.cs`, `DeleteFileCommandHandler.cs` |
| **Class** | Both handlers |
| **Method** | `Handle` return `Result.Deleted` |
| **Problem** | Restore operation returns `Deleted` success type with HTTP 204. |
| **Technical impact** | Misleading for API consumers and logs. |
| **Business impact** | Confusion in audit interpretation. |
| **Recommendation** | Use `Result.Success` or dedicated `Restored` type. |
| **Priority** | P4 |

---

### AUD-CODE-035 — Download Route Casing Inconsistency

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Naming Consistency |
| **File** | `Microservices/DCC/Controllers/FilesController.cs` |
| **Class** | `FilesController` |
| **Method** | `Downloadfile` (line 46) |
| **Problem** | Action named `Downloadfile` (lowercase 'f') while others use PascalCase (`GetFileMeta`, `DeleteFile`). |
| **Technical impact** | Public URL `/Downloadfile/` differs from conventional casing; client bugs on Linux deployments. |
| **Business impact** | Integration friction. |
| **Recommendation** | Align naming; maintain route alias for backward compatibility if needed. |
| **Priority** | P3 |

---

### AUD-CODE-036 — ExpiresAt Stored But Never Enforced

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Business Rules |
| **File** | `FileEntity.cs`, `FileAccessService.cs` |
| **Class** | Both |
| **Method** | N/A |
| **Problem** | `ExpiresAt` and `AccessExpiresAt` columns exist; expiry checks commented out or absent. |
| **Technical impact** | Data model promises lifecycle features not implemented. |
| **Business impact** | Retention policies cannot be enforced. |
| **Recommendation** | Implement expiry in access service or remove unused fields. |
| **Priority** | P2 |

---

### AUD-CODE-037 — No Rate Limiting on Upload Endpoint

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Scalability / Abuse |
| **File** | `Microservices/DCC/Controllers/FilesController.cs` |
| **Class** | `FilesController` |
| **Method** | `UploadFile`, `UploadFileSecure` |
| **Problem** | 1 GB request limit but no rate limiter (ApiGateway rate limits auth routes, not file routes). |
| **Technical impact** | Vulnerable to upload flooding / disk exhaustion DoS. |
| **Business impact** | Service outage from storage exhaustion. |
| **Recommendation** | Add rate limiting at gateway or DCC for upload endpoints. |
| **Priority** | P2 |

---

## Low Findings

### AUD-CODE-038 — IFileStorage Registered as Singleton

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Dependency Injection |
| **File** | `ServiceCollectionExtensions.cs` |
| **Class** | `ServiceCollectionExtensions` |
| **Method** | `AddInfrastructure` (line 101) |
| **Problem** | Singleton lifetime for storage holding config-derived root path. |
| **Technical impact** | Cannot swap storage root at runtime; acceptable for current design. |
| **Recommendation** | Document intent; use Scoped if per-tenant roots ever needed. |
| **Priority** | P4 |

---

### AUD-CODE-039 — OpenReadAsync Returns Undisposed Stream Responsibility to Caller

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Resource Management |
| **File** | `FileStorage.cs` |
| **Class** | `FileStorage` |
| **Method** | `OpenReadAsync` (lines 42–50) |
| **Problem** | Stream ownership transferred to MVC `File()` result — correct if framework disposes; fragile if handler reused elsewhere. |
| **Technical impact** | Handle leak if consumption path changes. |
| **Recommendation** | Document ownership contract; use `FileStreamResult` with registered disposal. |
| **Priority** | P4 |

---

### AUD-CODE-040 — CORS Allows All Origins in Development

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Security |
| **File** | `ServiceCollectionExtensions.cs` |
| **Class** | `ServiceCollectionExtensions` |
| **Method** | `AddPresentation` (lines 52–55) |
| **Problem** | Dev/DockerDevelopment CORS allows any origin with credentials. |
| **Technical impact** | Acceptable for local dev; ensure production uses `AllowedOrigins`. |
| **Recommendation** | Verify production env never hits `return true` branch. |
| **Priority** | P4 |

---

### AUD-CODE-041 — Commented-Out Access Control Block (42 lines)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Maintainability |
| **File** | `FileAccessService.cs` |
| **Class** | `FileAccessService` |
| **Method** | `CanAccessAsync` (lines 33–128) |
| **Problem** | Large commented blocks including helper methods reduce readability. |
| **Technical impact** | Unclear whether WIP or abandoned. |
| **Recommendation** | Remove or feature-flag; track in issue backlog. |
| **Priority** | P4 |

---

### AUD-CODE-042 — No Structured Logging in FileService

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Logging Strategy |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | All |
| **Problem** | No `ILogger` injection; operations not logged at info/warn level. |
| **Technical impact** | Difficult to audit uploads/deletes in production troubleshooting. |
| **Business impact** | Compliance audit gaps. |
| **Recommendation** | Add structured logs for lifecycle events with FileId, OwnerService, UserId. |
| **Priority** | P3 |

---

### AUD-CODE-043 — ApplicationAssemblyReference Namespace Mismatch

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Organization |
| **File** | `ApplicationAssemblyReference.cs` |
| **Class** | `ApplicationAssemblyReference` |
| **Method** | N/A |
| **Problem** | Lives in root namespace `DCC` while handlers live under `DCC.Application.*`. |
| **Technical impact** | Confusing discovery for new developers. |
| **Recommendation** | Move to `DCC.Application` namespace. |
| **Priority** | P4 |

---

### AUD-CODE-044 — PurgeFileAsync purgedBy Parameter Unused

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Dead Code |
| **File** | `FileService.cs` |
| **Class** | `FileService` |
| **Method** | `PurgeFileAsync` (line 243) |
| **Problem** | `purgedBy` accepted but never recorded (no revision on purge). |
| **Technical impact** | Purge operations leave no audit trail. |
| **Business impact** | Compliance gap for destructive operations. |
| **Recommendation** | Log or write revision before purge. |
| **Priority** | P2 |

---

### AUD-CODE-045 — No API Versioning Beyond v1

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Maintainability |
| **File** | `FilesController.cs` |
| **Class** | `FilesController` |
| **Method** | N/A |
| **Problem** | Only `[ApiVersion("1.0")]` defined. |
| **Technical impact** | Breaking changes will affect all consumers immediately. |
| **Recommendation** | Plan v2 strategy before breaking auth/storage contract. |
| **Priority** | P4 |

---

### AUD-CODE-046 — Handler Internal Visibility Inconsistent

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Naming / Organization |
| **File** | Application handlers |
| **Class** | Mix of `internal class` and `internal sealed class` |
| **Method** | N/A |
| **Problem** | Some handlers sealed, others not; no documented convention. |
| **Recommendation** | Standardize on `internal sealed` for handlers. |
| **Priority** | P4 |

---

### AUD-CODE-047 — No Hosted Services or Background Jobs

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Scalability |
| **File** | Entire DCC module |
| **Class** | N/A |
| **Method** | N/A |
| **Problem** | No cleanup job for orphan files, expired files, or outbox sweeps beyond MassTransit defaults. |
| **Technical impact** | Storage and DB grow unbounded without external ops scripts. |
| **Recommendation** | Plan background worker for expiry and orphan cleanup. |
| **Priority** | P3 |

---

### AUD-CODE-048 — Errors.Files Uses IdentityError Mapper Unused

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Dead Code |
| **File** | `Application/Files/Errors/Errors.Files.cs` |
| **Class** | `Errors.Files` |
| **Method** | `IdentityErrors`, `DbOperationFailed`, `RevisionDeletionFailed` |
| **Problem** | Error helpers defined but never referenced in DCC handlers. |
| **Recommendation** | Remove or use. |
| **Priority** | P4 |

---

### AUD-CODE-049 — Missing `[ProducesResponseType]` Attributes

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | API Documentation |
| **File** | `FilesController.cs` |
| **Class** | `FilesController` |
| **Method** | All actions |
| **Problem** | OpenAPI/Scalar docs rely on inference; error responses not documented. |
| **Recommendation** | Add response type attributes for client generation. |
| **Priority** | P4 |

---

## Layer Scorecard

| Layer | Grade | Primary Concerns |
|-------|-------|------------------|
| **Presentation** | D | AllowAnonymous purge, no rate limits, inconsistent routes |
| **Application** | C- | Missing auth on mutations/queries, DIP violations, token not propagated |
| **Domain** | D | Anemic, no invariants, unused access fields |
| **Infrastructure** | C | Transaction ordering, god class, path traversal risk |
| **Validators** | C | Only 2 of 6 operations validated |
| **Extensions** | C | Dead registrations, static localizer, migration swallow |
| **Consumers** | B- | Single consumer, adequate for scope |
| **Publishers** | N/A | None exist |
| **Hosted Services** | N/A | None exist |

---

## Recommended Remediation Order

1. **P0** — Authorization matrix (AUD-CODE-001 through 004, 008)
2. **P1** — Path traversal + transaction ordering (AUD-CODE-005, 006, 011, 017)
3. **P1** — SUPERADMIN consistency + exception leakage (AUD-CODE-007, 012)
4. **P2** — Test project, health checks, cancellation tokens, tenancy alignment
5. **P3+** — Dead code cleanup, refactoring, API polish

---

## Related Audits

- [Database Audit](./DCC_DATABASE_AUDIT.md)
- [Event Audit](./DCC_EVENT_AUDIT.md)
- [Storage Audit](./DCC_STORAGE_AUDIT.md)
