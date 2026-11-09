# DCC Architecture Decision Records (ADRs)

> Normative decisions — deviations require new ADR

---

## ADR-001: DCC as Platform Module, Not Standalone DMS

**Status:** Accepted  
**Date:** 2026-07-20

**Context:** Initial analysis positioned DCC against SharePoint/Box as product competitor.

**Decision:** DCC is the **internal document platform** for Dejban. End-user collaboration features are out of scope unless they serve all modules.

**Alternatives considered:**
- Standalone DMS product — rejected (wrong business model)
- Per-module file storage — rejected (duplicate logic, security gaps)

**Consequences:** Roadmap prioritizes SDK, events, OwnerModule model over sharing portals and desktop sync.

---

## ADR-002: Business Modules Store DocumentId Only

**Status:** Accepted

**Decision:** Business databases store only `Guid` references (`DocumentId`, `AvatarDocumentId`). No paths, hashes, blobs, metadata, versions.

**Alternatives:**
- Store path + DocumentId — rejected (path leaks infrastructure)
- Store metadata copy — rejected (consistency burden)

**Consequences:** Mandatory integration event handlers; architecture tests in modules.

---

## ADR-003: Single Microservice with Internal Modular Monolith

**Status:** Accepted

**Decision:** DCC remains **one deployable microservice** with Clean Architecture projects (Domain, Application, Infrastructure, Api).

**Alternatives:**
- Split storage and metadata services — rejected until proven scale need
- Embed DCC inside Dejban.Api — rejected (independent scaling, DB isolation)

**Consequences:** NetArchTest enforcement; independent `dccdb`.

---

## ADR-004: Object Storage as Primary Blob Backend

**Status:** Accepted

**Decision:** Production uses S3-compatible object storage (MinIO dev, S3/Azure prod). Filesystem provider dev-only.

**Alternatives:**
- PostgreSQL bytea — rejected (scale)
- NAS filesystem in prod — rejected (HA, horizontal pod scaling)

**Consequences:** StorageObject table with ProviderKey + ObjectKey; migration from current disk paths.

---

## ADR-005: CQRS with OpenSearch Read Side

**Status:** Accepted

**Decision:** Writes to PostgreSQL aggregates; search queries OpenSearch projection (Phase B).

**Alternatives:**
- PostgreSQL FTS only — acceptable fallback if OpenSearch delayed
- Single model for read/write — rejected at scale

**Consequences:** Event-driven index updates; eventual search consistency (seconds).

---

## ADR-006: MassTransit Outbox for All Integration Events

**Status:** Accepted

**Decision:** Every integration event published via EF outbox in same transaction as aggregate save.

**Alternatives:**
- Direct bus publish — rejected (dual-write problem)
- HTTP callbacks to modules — rejected (coupling, reliability)

**Consequences:** Outbox tables in dccdb; existing infra finally utilized.

---

## ADR-007: Permission Engine Single Pipeline

**Status:** Accepted

**Decision:** All access via `IAccessPolicyEvaluator` — no ad-hoc checks in handlers.

**Alternatives:**
- ASP.NET authorization attributes only — rejected (insufficient for document ACL)
- Module-side authorization — rejected (inconsistent security)

**Consequences:** Refactor all legacy handlers; remove AllowAnonymous purge.

---

## ADR-008: OwnerModule + OwnerEntityId Ownership Model

**Status:** Accepted

**Decision:** Primary document grouping via `OwnerModule` + `OwnerEntityId`, not user-created folder trees.

**Alternatives:**
- SharePoint folder hierarchy primary — rejected (modules already have aggregates)
- Content-addressable only — rejected (business correlation need)

**Consequences:** Optional Folder aggregate Phase C for admin only.

---

## ADR-009: DocumentType Registry with JSON Schema Metadata

**Status:** Accepted

**Decision:** Modules register DocumentTypes with versioned JSON Schema MetadataProfiles.

**Alternatives:**
- EAV columns per field — rejected (schema evolution pain)
- Unrestricted JSONB — rejected (validation need)

**Consequences:** MetadataEngine validates all uploads.

---

## ADR-010: Default Deny for Private Documents

**Status:** Accepted

**Decision:** Non-public documents require explicit permission match — no implicit allow for authenticated users.

**Alternatives:**
- Authenticated = allow — rejected (Phase 2 audit finding)

**Consequences:** Breaking change for legacy private files — migrate with IsPublic flags.

---

## ADR-011: Recycle Before Purge

**Status:** Accepted

**Decision:** Default delete is Recycle (soft). Purge is retention job or admin only.

**Alternatives:**
- Immediate hard delete — rejected (audit, recovery)

**Consequences:** DocumentPurged event only on purge; modules keep ref until then.

---

## ADR-012: Signed URLs Replace Static Public File Serving

**Status:** Accepted

**Decision:** ApiGateway anonymous `/files` static serving removed; replaced by time-limited signed URLs from DCC.

**Alternatives:**
- Keep static serve for performance — rejected (security)
- All content through download API only — acceptable for private; public uses signed URL

**Consequences:** Gateway config change; UI updates in modules.

---

## ADR-013: Workflows Stay in Business Modules

**Status:** Accepted

**Decision:** DCC does not implement approval workflows. RequestTracker and module handlers own state machines.

**Alternatives:**
- Embedded BPMN in DCC — rejected (scope)
- SharePoint-style approval — rejected

**Consequences:** DCC exposes document status hooks only; Contracts integrates externally.

---

## ADR-014: REST + SDK First; GraphQL Read Later

**Status:** Accepted

**Decision:** Primary contract is REST v2 + `IDocumentPlatformClient`. GraphQL read layer optional Phase D+.

**Alternatives:**
- GraphQL first — rejected (module integration is server-side .NET)

**Consequences:** DTOs in DCC.Contracts designed for future GraphQL mapping.

---

## ADR-015: Virus Scan Gate Before Available Status

**Status:** Accepted

**Decision:** DocumentTypes with `ScanRequired=true` remain in Scanning until ClamAV passes.

**Alternatives:**
- Scan async after Available — rejected (serve malware risk)
- No scan — rejected (platform liability)

**Consequences:** Media pipeline runs after scan pass.

---

## ADR-016: Dedup via StorageObject Reference Count

**Status:** Accepted (Phase B)

**Decision:** Optional dedup by checksum — multiple DocumentVersions may reference one StorageObject.

**Alternatives:**
- Always unique blobs — simpler but costly
- Content-addressable primary keys — complicates versioning

---

## ADR-017: Audit Log Immutability

**Status:** Accepted

**Decision:** AuditEntries insert-only; DB trigger prevents UPDATE/DELETE.

**Alternatives:**
- Mutable audit — rejected (compliance)

---

## ADR-018: Schema Namespace `dcc`

**Status:** Accepted

**Decision:** All DCC tables in PostgreSQL schema `dcc`, not `public`.

**Alternatives:**
- public schema — rejected (clarity in shared DB scenarios)

---

## ADR-019: Legacy v1 API Deprecation Timeline

**Status:** Accepted

**Decision:** v1 `/Files/*` deprecated Phase A; removed 6 months after Phase A gate.

**Alternatives:**
- Immediate removal — rejected (migration risk)
- Forever dual — rejected (maintenance)

---

## ADR-020: Integration Event Contract Assembly

**Status:** Accepted

**Decision:** `DCC.Contracts` NuGet-internal package contains integration events and public DTOs.

**Alternatives:**
- Events in Common — rejected (DCC ownership unclear)
- Duplicate event defs in modules — rejected (drift)

---

## Decision Log Template (Future)

```
## ADR-XXX: Title
Status: Proposed | Accepted | Superseded
Decision:
Alternatives:
Consequences:
```

New ADRs require architect approval before implementation.

---

## Related Documents

- [Architecture Bible](./DCC_ARCHITECTURE_BIBLE.md)
- [Implementation Guidelines](./DCC_IMPLEMENTATION_GUIDELINES.md)
- [Previous Analysis Review](./DCC_PREVIOUS_ANALYSIS_REVIEW.md)
