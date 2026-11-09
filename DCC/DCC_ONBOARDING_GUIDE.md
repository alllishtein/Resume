# DCC Onboarding Guide

> How a senior developer should approach understanding the Document Control Center module.

---

## Welcome

You are taking ownership of **DCC (Document Control Center)** — a file storage microservice in the PayamGostar platform. This guide provides a structured learning path based on a complete reverse-engineering of the codebase. Read the companion documents as you progress:

1. [DCC Workspace Map](./DCC_WORKSPACE_MAP.md) — where DCC lives in the monorepo
2. [DCC Architecture](./DCC_ARCHITECTURE.md) — how it is built and communicates
3. [DCC Domain Model](./DCC_DOMAIN_MODEL.md) — business entities and rules

---

## What DCC Does (30-Second Version)

DCC stores files (photos, documents) on disk, tracks metadata in PostgreSQL, and serves downloads with basic access control. Other services upload via HTTP and store the returned `FileId` in their own databases. The ApiGateway proxies external API calls and serves public files statically at `/files`.

**It is not** a full document management system — there is no workflow, versioning of content, full-text search API, or rich ACL UI.

---

## Recommended Learning Path

### Phase 1: Platform Context (Day 1 — 2 hours)

Understand where DCC sits before reading its code.

**Read:**

- Root `README.md`
- `PG_Microservices.slnx` — note DCC is a standalone project under `/Microservices/`
- `docker-compose.yml` — find `dccdb`, `dcc-storage` volume, `eventbus`, `redis`

**Run locally (optional but valuable):**

```bash
# From repo root — start infrastructure
docker compose -f docker-compose.yml -f docker-compose.development.yml up -d dccdb eventbus redis

# Run DCC
dotnet run --project Microservices/DCC/DCC.csproj
```

DCC listens on `http://localhost:5043`. Database: `payamgostar_dcc` on port `18005` (dev).

**Key insight:** DCC is one of ~12 microservices. External traffic normally flows through ApiGateway (`7036`), not directly to DCC.

---

### Phase 2: Entry Point & Request Flow (Day 1 — 2 hours)

Trace one request end-to-end before exploring handlers.

**Read in order:**

1. `Microservices/DCC/Program.cs` — startup, middleware order
2. `Microservices/DCC/Abstractions/Extensions/ServiceCollectionExtensions.cs` — all DI registration
3. `Microservices/DCC/Controllers/FilesController.cs` — API surface
4. `Microservices/DCC/Controllers/ApiController.cs` — error mapping

**Trace an upload:**

```
FilesController.UploadFileSecure
  → MediatR → ValidationBehavior
  → UploadFileCommandHandler
  → FileService.UploadFileAsync
  → FileStorage.SaveAsync (disk)
  → ApplicationDbContext.SaveChangesAsync
```

**Trace a download:**

```
FilesController.Downloadfile
  → DownloadFileQueryHandler
  → FileAccessService.CanAccessAsync (authorization)
  → FileService.DownloadFileAsync
  → FileStorage.OpenReadAsync
```

Draw this flow on paper. You should be able to explain it without looking at code.

---

### Phase 3: Domain & Persistence (Day 2 — 3 hours)

**Read:**

- `Domain/Entities/FileEntity.cs`
- `Domain/Entities/FileRevision.cs`
- `Infrastructure/Persistence/ApplicationDbContext.cs`
- `Infrastructure/Persistence/Configurations/FileEntityConfiguration.cs`
- `Infrastructure/Persistence/Migrations/20260708095740_Initial.cs`

**Study the state machine** in [DCC Domain Model — Section 8](./DCC_DOMAIN_MODEL.md#8-entity-lifecycle--state-transitions).

**Questions you should be able to answer:**

- What happens when you delete a protected vs unprotected file?
- What is stored in `FileRevision.Snapshot`?
- Why is `StoragePath` unique?
- Does soft delete remove bytes from disk?

---

### Phase 4: Infrastructure Services (Day 2 — 2 hours)

**Read:**

- `Infrastructure/Services/FileStorage.cs` — path resolution per environment
- `Infrastructure/Services/FileService.cs` — all file operations (largest file in module)
- `Application/Services/FileAccessService.cs` — access rules (note commented code)

**Understand storage paths:**

```
uploads/public/Dejban.Visitors/2026-07/{guid}.jpg
uploads/private/...
```

**Docker nuance:** DCC writes to `/app/uploads`; ApiGateway reads `public/` from the same `dcc-storage` volume at `/app/public-assets`.

---

### Phase 5: Shared Client & Consumers (Day 3 — 3 hours)

DCC is consumed by other services. Understanding the client is essential.

**Read:**

- `Common/Abstractions/Contracts/IDccClient.cs`
- `Common/FileService/DccHttpClient.cs`
- `Common/FileService/DccAuthForwardingHandler.cs`
- `Common/Abstractions/Extensions/ServiceCollectionExtensions.cs` → `AddDccClient`

**Read a real consumer:**

- `Dejban.Modules.Personnels.Application/.../CreatePersonnelCommandHandler.cs` (avatar upload)
- `Dejban.Modules.Visitors.Application/.../CreateVisitorAndVisitScheduleCommandHandler.cs` (visitor + companion photos)

**Observe the pattern:**

1. Business entity saved first (gets an ID)
2. Photo uploaded to DCC with that ID in filename
3. `FileId` stored as string in `AvatarImage` field
4. Upload failure is logged/warned but does not fail the main operation (Visitors) or is silently skipped (Personnels only saves if success)

---

### Phase 6: Gateway & Static Files (Day 3 — 1 hour)

**Read:**

- `ApiGateway/Program.cs` — static file middleware for `/files`
- `ApiGateway/appsettings.json` → `ReverseProxy:DCC` section

**Test mentally:**

| URL | Handler |
|-----|---------|
| `GET /Api/v1.0/Files/Downloadfile/{id}` via gateway | Proxied to DCC with JWT |
| `GET /files/Dejban.Visitors/2026-07/abc.jpg` via gateway | Static file from volume |
| `POST /api/v1.0/Files/UploadFileSecure` direct to DCC | DCC controller |

---

### Phase 7: Event Bus & Cross-Cutting (Day 4 — 2 hours)

**Read:**

- `Application/Consumers/GetDCCServiceEndpointsConsumer.cs`
- `Common/EventBus/Contracts/Requests/GetDCCServiceEndpoints.cs`
- `IdentityServer/.../GetServicesEndpointsQueryHandler.cs` — note DCC is **not** in the request list

**Read shared infrastructure used by DCC:**

- `Common/Tenancy/TenantContextMiddleware.cs`
- `Common/Caching/TokenRevokeMiddleware.cs`
- `Common/Authorization/AuthorizationServiceCollectionExtensions.cs`

**Understand:** DCC has MassTransit outbox configured but publishes no business events today. The endpoint discovery consumer is infrastructure for IdentityServer permissions.

---

## Mental Model Checklist

After completing the path, verify you can answer:

- [ ] What projects reference DCC directly vs via `Common`?
- [ ] What is the difference between `UploadFile` and `UploadFileSecure`? (Hint: currently none in code)
- [ ] How does a Dejban module authenticate to DCC?
- [ ] Where are public files served without going through DCC access checks?
- [ ] What database does DCC use and what tables exist?
- [ ] What happens on purge vs delete vs restore?
- [ ] Which access control fields on `FileEntity` are actually enforced?
- [ ] Why does DCC register `ClaimService` and is it used?

---

## Files You Can Safely De-Prioritize

These exist but carry little active behavior:

| File | Reason |
|------|--------|
| `Abstractions/Helpers/Utils.cs` | Empty partial class |
| `Abstractions/Constants/ConfigConstants.cs` | Empty class |
| `Infrastructure/Services/ClaimService.cs` | Registered, never injected |
| `Common/Abstractions/Contracts/DCCFolders.cs` | Single unused constant |
| `FileService.SearchFilesAsync` | No API endpoint |
| `FileService.CreateRevisionAsync` | Private, unused (dead code) |

---

## Known Gaps (Expect These in Production)

Documented during reverse-engineering — not bugs you introduced:

1. **Access control incomplete** — role/permission/user checks commented out in `FileAccessService`
2. **GetFileMeta has no authorization** — anyone authenticated can read metadata for any file ID
3. **PurgeFile allows anonymous at controller level** — relies on handler SUPERADMIN check
4. **Soft-deleted files may still download** — `DownloadFileQueryHandler` doesn't check `IsDeleted`
5. **DCC endpoints not in IdentityServer sync** — permission claims won't include DCC API routes
6. **IdentityServer registers DCC client but doesn't use it**
7. **No DCC test project** — changes require manual verification
8. **DbInitializer catches all exceptions** — migration failures may go unnoticed

Understanding these gaps is part of being the module owner.

---

## How to Test Changes Manually

### Upload via curl (with JWT)

```bash
curl -X POST "http://localhost:5043/api/v1.0/Files/UploadFileSecure" \
  -H "Authorization: Bearer {token}" \
  -F "File=@photo.jpg" \
  -F "OwnerService=Dejban.Test" \
  -F "FileName=test.jpg" \
  -F "FolderName=test/photos" \
  -F "CreatorId=00000000-0000-0000-0000-000000000001" \
  -F "IsPublic=true" \
  -F "RequireSiteMatch=false"
```

### Download

```bash
curl -O -J "http://localhost:5043/api/v1.0/Files/Downloadfile/{fileId}" \
  -H "Authorization: Bearer {token}"
```

### Via gateway

Replace host with `http://localhost:7036` and use gateway route casing (`/Api/v1.0/Files/...`).

---

## Configuration Reference

| Setting | File | Purpose |
|---------|------|---------|
| `ConnectionStrings:Postgres` | `appsettings.json` | DCC database |
| `ConnectionStrings:Redis` | `appsettings.json` | Token blacklist cache |
| `RabbitMqTransport` | `appsettings.json` | MassTransit |
| `Storage:RootPath` | `appsettings.json` | Docker file storage root |
| `JwtSettings` | `GlobalAppsettings/` | Shared JWT validation |
| `Dcc:BaseUrl` | Consumer appsettings (optional) | HTTP client target; defaults to `:5043` |

---

## Relationship to Dejban Modules

DCC is **infrastructure**, not a Dejban module. Dejban modules follow strict Clean Architecture with separate Domain/Application/Infrastructure projects. DCC is a single project microservice with a similar logical structure but less domain richness.

When Dejban features need file storage:

1. Inject `IDccClient` in the application handler
2. Upload after the domain entity has an ID
3. Store `FileId.ToString()` in a string field on the entity
4. Never store raw file bytes in Dejban's PostgreSQL

---

## Suggested First Tasks for a New Owner

Non-code exploratory tasks to validate understanding:

1. **Upload a file** through the API and locate it on disk
2. **Find the DB row** in `payamgostar_dcc.Files`
3. **Create a personnel with avatar** in Dejban and trace the DCC call in logs
4. **Soft-delete a protected file** and inspect `FileRevisions`
5. **Compare** gateway static `/files/...` access vs API download access
6. **Review** IdentityServer endpoint sync and confirm DCC routes are absent

---

## Documentation Maintenance

When you change DCC behavior, update:

- This onboarding guide if the learning path shifts
- `DCC_DOMAIN_MODEL.md` for entity/rule changes
- `DCC_ARCHITECTURE.md` for new integrations or pattern changes
- `DCC_WORKSPACE_MAP.md` for new consumers or dependencies

---

## Quick Reference Links

| Resource | Path |
|----------|------|
| DCC project | `Microservices/DCC/` |
| DCC client | `Common/FileService/` |
| Gateway DCC routes | `ApiGateway/appsettings.json` → `ReverseProxy:DCC` |
| Docker DCC service | `docker-compose.docker-development.yml` |
| Solution entry | `PG_Microservices.slnx` |

---

## Getting Help

| Question type | Where to look |
|---------------|---------------|
| How does auth work? | `Common/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| How do other services use DCC? | Grep for `IDccClient` |
| What endpoints exist? | `FilesController.cs` or Scalar at `/dccscalar` via gateway |
| Database schema | `Infrastructure/Persistence/Migrations/` |
| Platform-wide patterns | Compare with `Microservices/Dejban/Modules/Visitors/` |

You now have a map. Read the code in the order above, and you will understand DCC better than a developer who wrote a single feature without seeing the whole module.
