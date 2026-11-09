# DCC Implementation Guidelines

> Normative coding standards for DCC platform implementation

---

## 1. Layer Rules (Mandatory)

| Layer | May reference | Must NOT reference |
|-------|---------------|-------------------|
| DCC.Domain | Nothing external | EF, MassTransit, ASP.NET, Infrastructure |
| DCC.Application | Domain, DCC.Contracts | Infrastructure concrete classes |
| DCC.Infrastructure | Domain, Application ports | DCC.Api |
| DCC.Api | Application, Contracts | Domain aggregates directly |
| DCC.Contracts | Nothing | All implementation |

**Enforcement:** `DCC.Architecture.Tests` using NetArchTest — CI blocking.

---

## 2. CQRS Handler Rules

1. One handler per command/query file
2. Handlers are `internal sealed class`
3. Return `ErrorOr<T>` — never throw for business failures
4. Inject `IAccessPolicyEvaluator` first — evaluate before any mutation
5. Pass `CancellationToken` to all I/O
6. No `DbContext` in handlers — repositories only
7. Single `IUnitOfWork.SaveChangesAsync` per command where possible

### Command handler template (conceptual)

```
1. Validate request (FluentValidation pipeline)
2. Evaluate permissions
3. Load aggregate via repository
4. Invoke domain method
5. Collect domain events
6. Save via unit of work (includes outbox)
7. Return result DTO
```

---

## 3. Domain Rules

1. Aggregates expose behavior methods — no public setters on state fields
2. Domain events raised inside aggregate methods
3. Value objects immutable — factory methods validate
4. Guard clauses in constructors
5. No infrastructure concerns in domain language

---

## 4. Repository Implementation

- EF configurations in `Infrastructure/Persistence/Configurations/`
- Global query filter: `Status != Destroyed` on Documents
- Tenant filter: `SiteId IN @tenantContext.SiteIds OR @tenantContext.IsSuperAdmin`
- `AsNoTracking()` on all read queries
- Explicit `Include` only when needed — avoid lazy load

---

## 5. Permission Engine Implementation

**Single class:** `AccessPolicyEvaluator` implements `IAccessPolicyEvaluator`

All controllers and handlers **must** call evaluator — no inline role checks.

Remove patterns from legacy code:
- Hardcoded `"SUPERADMIN"` strings
- `[AllowAnonymous]` on destructive endpoints
- Commented-out permission blocks

Use `ConfigConstants.DefaultAdminRoleName` from Common.

---

## 6. Storage Implementation

1. Never expose `ObjectKey` outside Infrastructure
2. Sanitize filenames — reject `..`, `/`, `\`
3. Verify resolved path under root (filesystem dev provider)
4. Temp upload → commit → promote pattern
5. Blob delete async after DB commit on purge
6. ReferenceCount on dedup — never delete shared blob prematurely

---

## 7. Outbox Pattern

```csharp
// Normative sequence
await unitOfWork.SaveChangesAsync(ct); // Saves aggregate + outbox in same transaction
// MassTransit bus outbox dispatches asynchronously
```

Never publish directly to bus from handler without outbox.

---

## 8. Logging

| Level | When |
|-------|------|
| Information | Document lifecycle transitions (DocumentId, OwnerModule, Action) |
| Warning | Quarantine, permission denied, retry |
| Error | Storage failure, outbox failure |
| Debug | Permission evaluation detail |

Structured properties: `DocumentId`, `OwnerModule`, `OwnerEntityId`, `CorrelationId`

**Never log:** blob keys, file content, JWT tokens

---

## 9. Testing Requirements

| Test type | Coverage target |
|-----------|-----------------|
| Domain unit tests | Aggregates, VOs — 90%+ |
| Application tests | Handlers with fakes — 80%+ |
| Architecture tests | 100% rule enforcement |
| Integration tests | Upload → download → purge → event — critical paths |

Minimum integration scenarios:
- Upload with permission denied → 403
- Upload virus EICAR → quarantine
- Purge → integration event → module handler clears ref
- Concurrent version upload → concurrency conflict

---

## 10. Migration Guidelines

1. EF migrations reviewed by two engineers
2. No destructive migration without data migration script
3. Legacy `Files` table migration — idempotent background job
4. Dual-write period max 4 weeks
5. Feature flags per module for SDK v2 cutover

---

## 11. API Versioning

- v2 additive changes → minor version
- Breaking DTO changes → v3 path or new fields with deprecation
- Minimum 6-month deprecation for v1 removal

---

## 12. Configuration

| Key | Purpose |
|-----|---------|
| `ConnectionStrings:Postgres` | dccdb |
| `ConnectionStrings:Redis` | Cache |
| `DocumentPlatform:Storage:Provider` | S3 / MinIO / FileSystem |
| `DocumentPlatform:Storage:Bucket` | Default bucket |
| `DocumentPlatform:Search:OpenSearchUrl` | Phase B |
| `DocumentPlatform:Scan:Enabled` | ClamAV |

Global JWT from `GlobalAppsettings/` — not duplicated.

---

## 13. Forbidden Patterns

| Pattern | Reason |
|---------|--------|
| `FileEntity` in new code | Use Document aggregate |
| Handler → `FileService` god class | Split by engine |
| Module stores `StoragePath` | Architecture violation |
| Direct `File.WriteAllBytes` in modules | Use SDK |
| Publish without outbox | Reliability |
| `[AllowAnonymous]` purge | Security |
| Static public file serve without signed URL | Security |

---

## 14. Code Review Checklist

- [ ] Permission evaluator called?
- [ ] Outbox used for integration events?
- [ ] No storage paths in DTOs?
- [ ] CancellationToken propagated?
- [ ] Audit entry written?
- [ ] Architecture tests pass?
- [ ] OpenAPI updated?

---

## Related Documents

- [Architecture Bible](./DCC_ARCHITECTURE_BIBLE.md)
- [Decision Records](./DCC_DECISION_RECORDS.md)
- [Module Integration Guide](./DCC_MODULE_INTEGRATION_GUIDE.md)
