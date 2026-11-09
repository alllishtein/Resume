# DCC Previous Analysis Review

> Re-evaluation of Phase 1–3 deliverables against the **Platform-first** vision  
> DCC is a **core Dejban platform module**, not a standalone DMS product.

---

## 1. Assumption That Changed

| Previous assumption | Corrected vision |
|--------------------|------------------|
| DCC becomes an enterprise DMS competing with SharePoint, Box, Alfresco | DCC is the **internal Document Platform** for all Dejban modules |
| End-user collaboration is a primary deliverable | **Module integrators** (Visitors, Personnels, etc.) are the primary consumers |
| External guest sharing, desktop sync, mobile apps are roadmap items | Platform **API + SDK + events**; UIs live in Dejban modules |
| Admin console as standalone product surface | Governance APIs consumed by Dejban admin / IdentityServer |
| Benchmark features adopted wholesale | Enterprise patterns **cherry-picked** only when they strengthen platform reuse |

SharePoint, M-Files, Box, etc. remain **architectural inspiration** for storage, versioning, audit, and search — not the target product shape.

---

## 2. Document Inventory Reviewed

| Document | Status |
|----------|--------|
| DCC_WORKSPACE_MAP.md | Mostly valid — update consumer framing |
| DCC_ARCHITECTURE.md | Valid technical baseline — reframe as platform service |
| DCC_DOMAIN_MODEL.md | Valid current state — extend with platform model |
| DCC_CODE/DATABASE/EVENT/STORAGE audits | **Keep** — platform must be production-safe |
| DCC_PRODUCT_VISION.md | **Superseded** by DCC_PLATFORM_VISION.md |
| DCC_ENTERPRISE_FEATURES.md | **Superseded** — many features reclassified |
| DCC_MODULE_ROADMAP.md | **Superseded** by DCC_PLATFORM_ROADMAP.md |
| DCC_IMPLEMENTATION_PLAN.md | **Superseded** by DCC_REVISED_IMPLEMENTATION_PLAN.md |

---

## 3. Feature Recommendation Review

Legend: **Keep** | **Modify** | **Remove**

### 3.1 Core Platform (Storage & Document Engine)

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-CORE-001 Pluggable storage (S3/MinIO/Azure) | **Keep** | Platform must scale independently of Dejban module DBs |
| F-CORE-002 Folder hierarchy | **Modify** | Folders scoped by `OwnerModule` + optional logical path — not user-created SharePoint libraries |
| F-CORE-003 Collections / smart folders | **Modify** | Rename to **Document Sets** bound to business aggregate (e.g. all attachments for VisitSchedule X) |
| F-CORE-004 Bulk upload/download | **Keep** | Migration and batch module operations (Inventory import) |
| F-CORE-005 Storage tiering | **Keep** | Platform cost control at scale |

### 3.2 Document & Version Engine

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-DOC-001 Document versioning | **Keep** | Core platform capability; modules reference DocumentId, versions internal |
| F-DOC-002 Check-in / check-out | **Modify** | **Edit lock** API for modules that need exclusive write (Contracts draft) — not co-authoring product |
| F-DOC-003 Metadata templates / content types | **Modify** | Rename **Document Types + Metadata Profiles** registered by modules (e.g. `Personnel.Avatar`) |
| F-DOC-004 Tags & labels | **Modify** | Platform tags optional; primary classification via DocumentType + OwnerModule |
| F-DOC-005 Recycle bin | **Keep** | Platform lifecycle; modules react via events to clear references |
| F-DOC-006 Duplicate detection | **Keep** | Storage efficiency for repeated uploads across modules |

### 3.3 Search Engine

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-SRC-001 Full-text search | **Keep** | Platform search API filtered by OwnerModule, SiteId, DocumentType |
| F-SRC-002 Faceted search | **Keep** | Module UIs embed faceted queries — not a standalone search portal |
| F-SRC-003 AI semantic search | **Modify** | **Phase D optional** — exposed as platform query API if modules need similarity |
| F-SRC-004 Visual similarity search | **Modify** | Narrow to **Visitor/Personnel photo dedup** use case — not general DAM |

### 3.4 Security & Permission Engine

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-SEC-001 Unified authorization | **Keep** | **Critical** — platform gate for all module access |
| F-SEC-002 Encryption at rest | **Keep** | Platform infrastructure requirement |
| F-SEC-003 Virus scanning | **Keep** | Protect entire Dejban ecosystem from malicious uploads |
| F-SEC-004 Audit timeline | **Keep** | Platform audit; modules may subscribe to events |
| F-SEC-005 Download/access history | **Keep** | Compliance for security domain |
| F-SEC-006 Watermark on download | **Modify** | Policy per DocumentType (e.g. classified patrol reports) — module-configured |
| F-SEC-007 Digital signature | **Modify** | **Platform integration adapter** — Contracts module invokes; DCC stores signed blob + metadata |

### 3.5 Workflow & Retention Engine

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-WF-001 Approval workflow | **Remove** (from DCC) | **Business modules own workflows** (RequestTracker, module handlers). DCC exposes document state hooks only |
| F-WF-002 Retention policy | **Keep** | Platform Retention Engine — policies by DocumentType + Site |
| F-WF-003 Legal hold | **Modify** | Platform flag modules can set via API when legal/compliance module requires |
| F-WF-004 Archive policy | **Keep** | Platform lifecycle + storage tiering |

### 3.6 Media Processing Engine

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-MED-001 OCR | **Modify** | Platform pipeline; searchable metadata returned to Search Engine — modules don't store OCR text |
| F-MED-002 Preview generation | **Keep** | Dejban UIs request preview URL from DCC — no local preview logic in modules |
| F-MED-003 Thumbnails | **Keep** | Same — platform-generated derivative blobs |
| F-MED-004 PDF conversion | **Keep** | Normalization service for modules accepting mixed formats |
| F-MED-005 Image optimization | **Keep** | Enforce profiles on DocumentTypes like `*.Avatar`, `Visitor.Photo` |

### 3.7 Sharing & Delivery (Standalone DMS bias)

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-SHR-001 Signed URLs / temporary links | **Keep** | **Primary delivery mechanism** for Dejban UI and gateway — replaces static `/files` |
| F-SHR-002 External guest sharing | **Remove** | Not platform scope — if needed, Visitors module owns guest access rules; DCC issues token via module-authenticated request |
| F-SHR-003 CDN integration | **Modify** | **Optional infra** behind signed URLs for public DocumentTypes — not a product feature |

### 3.8 Administration & Analytics

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-ADM-001 Quota per site/service | **Modify** | Quota per **OwnerModule + Site** — chargeback to modules |
| F-ADM-002 Storage analytics dashboard | **Modify** | Metrics exported to **Reporting** microservice — not standalone DCC dashboard |
| F-ADM-003 Health checks | **Keep** | Platform ops requirement |
| F-ADM-004 Admin console API | **Modify** | **Platform Admin API** for DocumentTypes, retention, quotas — consumed by Dejban admin UI |

### 3.9 Integrations & Platform Engine

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-INT-001 API v2 | **Keep** | **Document Service API** — primary contract for modules |
| F-INT-002 SDK (.NET) | **Keep** | **Unified Upload SDK** in Common/Dejban.Common — extend beyond upload-only |
| F-INT-003 Background jobs | **Keep** | Platform workers |
| F-INT-004 Webhooks | **Modify** | **Optional** — prefer MassTransit integration events as primary; webhooks for external systems only |
| F-INT-005 Domain/integration events | **Keep** | **Primary integration** with Dejban modules |
| F-INT-006 IdentityServer endpoint sync | **Keep** | Platform authorization catalog |
| F-INT-007 Comments & annotations | **Remove** | Collaboration belongs in business modules if ever needed |
| F-INT-008 Notification integration | **Remove** (from DCC) | Modules send notifications; DCC emits events modules consume |

### 3.10 AI & Client (Standalone product bias)

| Previous recommendation | Verdict | Why |
|------------------------|---------|-----|
| F-AI-001 Content moderation | **Modify** | Platform gate on upload for image DocumentTypes — block/quarantine before module reference saved |
| F-AI-002 Auto-classification | **Modify** | Suggest DocumentType from content — modules confirm |
| F-AI-003 Summarization | **Remove** | Module-specific (Contracts) — not platform core |
| F-CLI-001 Desktop sync | **Remove** | Not Dejban platform scope |
| F-CLI-002 Mobile SDK | **Modify** | **Resumable upload in unified SDK** — not separate mobile product |

### 3.11 Phase 2 Audit Remediation

| Audit finding | Verdict | Why |
|---------------|---------|-----|
| Authorization gaps | **Keep** | Platform Permission Engine must be correct before any module trusts DCC |
| Path traversal | **Keep** | Platform storage safety |
| Disk/DB ordering | **Keep** | Platform reliability |
| GetFileMeta unprotected | **Keep** | Platform API security |
| Static public `/files` bypass | **Modify** | Replace with module-scoped signed URLs |
| No domain events | **Keep** | Modules need DocumentPurged to clear AvatarDocumentId |
| Anemic domain / FileService god class | **Keep** | Platform code quality |
| ClaimService unused | **Modify** | Wire into Permission Engine or remove |
| Outbox without publishers | **Keep** | Integration Engine requirement |

---

## 4. New Platform-First Concepts (Previously Under-Specified)

These were implied but not centered in prior docs. They are now **first-class**:

| Concept | Purpose |
|---------|---------|
| **OwnerModule** | `Dejban.Personnels`, `Dejban.Visitors` — namespace for all platform queries |
| **OwnerEntityId** | GUID of business entity (PersonnelId, VisitorId) — link without FK across DBs |
| **DocumentType** | Registered profile: `Personnel.Avatar`, `Visitor.Photo`, `Inventory.ItemImage` |
| **MetadataProfile** | Schema per DocumentType — validated by Metadata Engine |
| **DocumentId** | Sole reference stored in business DB |
| **AttachmentDescriptor** | Lightweight DTO modules cache for UI (optional denormalized read model fed by events) |

---

## 5. Summary Counts

| Verdict | Count (approx.) |
|---------|-----------------|
| **Keep** | 28 |
| **Modify** | 22 |
| **Remove** | 8 |

**Removed themes:** standalone collaboration, guest sharing product, desktop sync, DCC-owned approval workflows, DCC notification hub, general-purpose admin portal.

**Strengthened themes:** OwnerModule/Entity, DocumentType registry, SDK, events, permission engine, module-scoped search and quota.

---

## 6. Related Documents

- [Platform Vision](./DCC_PLATFORM_VISION.md)
- [Platform Architecture](./DCC_PLATFORM_ARCHITECTURE.md)
- [Responsibility Boundaries](./DCC_RESPONSIBILITY_BOUNDARIES.md)
- [Platform Roadmap](./DCC_PLATFORM_ROADMAP.md)
- [Revised Implementation Plan](./DCC_REVISED_IMPLEMENTATION_PLAN.md)
