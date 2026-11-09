# DCC Database Specification

> Complete PostgreSQL schema for `payamgostar_dcc` — normative

---

## 1. Database Overview

| Property | Value |
|----------|-------|
| Engine | PostgreSQL 16+ |
| Database | `payamgostar_dcc` |
| Schema | `dcc` (explicit schema — not `public`) |
| ORM | EF Core 10 |
| Migrations | EF migrations in `DCC.Infrastructure` |
| Tenancy | Row-level `SiteId` on tenant-scoped tables |

---

## 2. Complete ERD

```mermaid
erDiagram
    DocumentTypes ||--|| MetadataProfiles : uses
    DocumentTypes ||--o| RetentionPolicies : default_policy
    Documents ||--|| DocumentTypes : classified
    Documents ||--o{ DocumentVersions : has
    Documents ||--o{ DocumentPermissions : has
    Documents ||--o| DocumentMetadata : has
    DocumentVersions ||--|| StorageObjects : references
    DocumentVersions ||--o{ MediaAssets : has
    MediaAssets ||--|| StorageObjects : references
    StorageObjects }o--|| StorageProviders : stored_in
    RetentionPolicies ||--o{ DocumentTypes : applies
    AuditEntries }o--o| Documents : references
    Folders ||--o{ Documents : optional
    Folders ||--o| Folders : parent

    Documents {
        uuid Id PK
        uuid SiteId
        varchar OwnerModule
        uuid OwnerEntityId
        varchar DocumentTypeKey FK
        varchar Status
        uuid CurrentVersionId FK
        timestamptz CreatedAt
        varchar CreatedByUserId
        varchar CreatedByService
        timestamptz RecycledAt
        varchar RecycledBy
        timestamptz PurgeScheduledAt
        boolean LegalHoldActive
        varchar LegalHoldReason
        uuid FolderId FK
        uint RowVersion
    }

    DocumentVersions {
        uuid Id PK
        uuid DocumentId FK
        int VersionNumber
        uuid StorageObjectId FK
        varchar ContentType
        bigint SizeBytes
        char64 ChecksumSha256
        varchar OriginalFileName
        timestamptz CreatedAt
        varchar CreatedByUserId
    }

    StorageObjects {
        uuid Id PK
        varchar ProviderKey FK
        varchar Bucket
        varchar ObjectKey UK
        bigint SizeBytes
        char64 ChecksumSha256
        varchar Tier
        int ReferenceCount
        timestamptz CreatedAt
    }

    DocumentTypes {
        varchar Key PK
        varchar Module
        uuid MetadataProfileId FK
        uuid RetentionPolicyId FK
        jsonb MediaProfile
        boolean ScanRequired
        boolean IsActive
        timestamptz RegisteredAt
    }

    MetadataProfiles {
        uuid Id PK
        int Version
        jsonb JsonSchema
        timestamptz CreatedAt
    }

    DocumentMetadata {
        uuid DocumentId PK_FK
        jsonb Payload
        timestamptz UpdatedAt
    }

    DocumentPermissions {
        uuid Id PK
        uuid DocumentId FK
        varchar PrincipalType
        varchar PrincipalId
        varchar PermissionLevel
        timestamptz GrantedAt
        varchar GrantedBy
    }

    MediaAssets {
        uuid Id PK
        uuid DocumentVersionId FK
        varchar AssetKind
        varchar Variant
        uuid StorageObjectId FK
        timestamptz CreatedAt
    }

    RetentionPolicies {
        uuid Id PK
        varchar Name
        int DurationDays
        varchar ActionOnExpiry
        boolean IsActive
    }

    AuditEntries {
        bigint Id PK
        uuid CorrelationId
        uuid DocumentId
        varchar ActorType
        varchar ActorId
        varchar Action
        timestamptz Timestamp
        inet ClientIp
        jsonb Details
    }

    StorageProviders {
        varchar Key PK
        varchar ProviderType
        jsonb Configuration
        boolean IsDefault
    }

    Folders {
        uuid Id PK
        uuid SiteId
        uuid ParentFolderId FK
        varchar Name
        varchar MaterializedPath
        timestamptz CreatedAt
    }

    OutboxMessage {
        bigint SequenceNumber PK
    }

    InboxState {
        bigint Id PK
    }
```

---

## 3. Table Specifications

### 3.1 `dcc.documents`

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| Id | uuid | NO | PK, DocumentId |
| SiteId | uuid | NO | Tenancy |
| OwnerModule | varchar(100) | NO | e.g. Dejban.Personnels |
| OwnerEntityId | uuid | NO | Business entity ref |
| DocumentTypeKey | varchar(150) | NO | FK → document_types |
| Status | varchar(30) | NO | Lifecycle state |
| CurrentVersionId | uuid | YES | FK → document_versions |
| CreatedAt | timestamptz | NO | UTC |
| CreatedByUserId | varchar(100) | YES | JWT sub |
| CreatedByService | varchar(100) | NO | Service identity |
| RecycledAt | timestamptz | YES | Soft delete timestamp |
| RecycledBy | varchar(100) | YES | |
| PurgeScheduledAt | timestamptz | YES | Retention scheduler |
| LegalHoldActive | boolean | NO | Default false |
| LegalHoldReason | varchar(500) | YES | |
| FolderId | uuid | YES | Optional FK → folders |
| RowVersion | uint | NO | Concurrency token |

**Indexes:**

| Name | Columns | Type | Purpose |
|------|---------|------|---------|
| PK_documents | Id | Primary | |
| IX_documents_owner | OwnerModule, OwnerEntityId | B-tree | Module list query |
| IX_documents_site_type | SiteId, DocumentTypeKey | B-tree | Scoped admin |
| IX_documents_status | Status | B-tree partial WHERE Status != 'Available' | Disposition jobs |
| IX_documents_purge_scheduled | PurgeScheduledAt | B-tree partial WHERE PurgeScheduledAt IS NOT NULL | Retention job |
| UQ_documents_owner_type_entity_active | OwnerModule, OwnerEntityId, DocumentTypeKey | Unique partial WHERE Status IN ('Available','Uploading',...) | Optional: one active avatar per entity |

**Constraints:**

- FK `DocumentTypeKey` → `document_types(Key)`
- FK `CurrentVersionId` → `document_versions(Id)` DEFERRABLE
- CHECK `Status` IN (allowed enum values)

**Soft delete:** `Status = Recycled` — not separate IsDeleted flag.

**Partitioning (future):** RANGE on `CreatedAt` yearly when >50M rows.

---

### 3.2 `dcc.document_versions`

| Column | Type | Purpose |
|--------|------|---------|
| Id | uuid PK | |
| DocumentId | uuid FK | CASCADE on document purge |
| VersionNumber | int | Unique per document |
| StorageObjectId | uuid FK | Blob reference |
| ContentType | varchar(127) | MIME |
| SizeBytes | bigint | |
| ChecksumSha256 | char(64) | |
| OriginalFileName | varchar(500) | |
| CreatedAt | timestamptz | |
| CreatedByUserId | varchar(100) | |

**Indexes:**

- `UQ_document_versions_doc_num` (DocumentId, VersionNumber) UNIQUE
- `IX_document_versions_storage` (StorageObjectId)

**Immutability:** Application + DB trigger forbid UPDATE on content columns (Phase B migration).

---

### 3.3 `dcc.storage_objects`

| Column | Type | Purpose |
|--------|------|---------|
| Id | uuid PK | |
| ProviderKey | varchar(50) FK | |
| Bucket | varchar(255) | |
| ObjectKey | varchar(1024) | Unique blob key |
| SizeBytes | bigint | |
| ChecksumSha256 | char(64) | Dedup index |
| Tier | varchar(20) | Hot/Warm/Cold |
| ReferenceCount | int | Dedup |
| CreatedAt | timestamptz | |

**Indexes:**

- `UQ_storage_objects_key` (ProviderKey, Bucket, ObjectKey) UNIQUE
- `IX_storage_objects_checksum` (ChecksumSha256, SizeBytes) — dedup lookup

---

### 3.4 `dcc.document_types`

| Column | Type | Purpose |
|--------|------|---------|
| Key | varchar(150) PK | `{Module}.{Name}` |
| Module | varchar(100) | Dejban module prefix |
| MetadataProfileId | uuid FK | |
| RetentionPolicyId | uuid FK NULL | |
| MediaProfile | jsonb | Thumbnail sizes, OCR, watermark |
| ScanRequired | boolean | |
| IsActive | boolean | |
| RegisteredAt | timestamptz | |

---

### 3.5 `dcc.metadata_profiles`

Versioned JSON Schema definitions.

| Column | Type | Purpose |
|--------|------|---------|
| Id | uuid PK | |
| Version | int | Increment on change |
| JsonSchema | jsonb | JSON Schema draft 2020-12 |
| CreatedAt | timestamptz | |

DocumentTypes point to latest profile Id on registration update.

---

### 3.6 `dcc.document_metadata`

| Column | Type | Purpose |
|--------|------|---------|
| DocumentId | uuid PK FK | 1:1 with documents |
| Payload | jsonb | Validated metadata |
| UpdatedAt | timestamptz | |

**Index:** GIN on `Payload` for JSON queries (optional, Phase B).

---

### 3.7 `dcc.document_permissions`

| Column | Type | Purpose |
|--------|------|---------|
| Id | uuid PK | |
| DocumentId | uuid FK | CASCADE |
| PrincipalType | varchar(20) | User, Role, Service |
| PrincipalId | varchar(200) | |
| PermissionLevel | varchar(20) | Read, Write, Delete, Admin |
| GrantedAt | timestamptz | |
| GrantedBy | varchar(100) | |

**Index:** (DocumentId, PrincipalType, PrincipalId) UNIQUE

---

### 3.8 `dcc.media_assets`

| Column | Type | Purpose |
|--------|------|---------|
| Id | uuid PK | |
| DocumentVersionId | uuid FK | |
| AssetKind | varchar(30) | Thumbnail, Preview, OcrText |
| Variant | varchar(30) | e.g. 256x256 |
| StorageObjectId | uuid FK | |
| CreatedAt | timestamptz | |

**Index:** (DocumentVersionId, AssetKind, Variant) UNIQUE

---

### 3.9 `dcc.retention_policies`

| Column | Type | Purpose |
|--------|------|---------|
| Id | uuid PK | |
| Name | varchar(200) | |
| DurationDays | int NULL | NULL = indefinite |
| ActionOnExpiry | varchar(20) | Recycle, Purge, Archive |
| IsActive | boolean | |

---

### 3.10 `dcc.audit_entries`

| Column | Type | Purpose |
|--------|------|---------|
| Id | bigint GENERATED | PK |
| CorrelationId | uuid | Request trace |
| DocumentId | uuid NULL | |
| ActorType | varchar(20) | |
| ActorId | varchar(200) | |
| Action | varchar(50) | Upload, Download, Recycle, ... |
| Timestamp | timestamptz | |
| ClientIp | inet NULL | |
| Details | jsonb | |

**Indexes:**

- (DocumentId, Timestamp DESC)
- (Timestamp) — partition key candidate

**Rules:** INSERT only — no UPDATE/DELETE (trigger enforced Phase B).

**Partitioning:** RANGE monthly on `Timestamp` when >100M entries.

---

### 3.11 `dcc.folders` (Phase C)

| Column | Type | Purpose |
|--------|------|---------|
| Id | uuid PK | |
| SiteId | uuid | |
| ParentFolderId | uuid NULL FK self | |
| Name | varchar(255) | |
| MaterializedPath | varchar(2000) | |
| CreatedAt | timestamptz | |

**Index:** (SiteId, MaterializedPath) UNIQUE

---

### 3.12 MassTransit Tables

Existing pattern retained:

- `outbox_state`
- `outbox_message`
- `inbox_state`

In schema `dcc` alongside business tables.

---

## 4. Concurrency

| Table | Mechanism |
|-------|-----------|
| documents | `RowVersion` uint — optimistic concurrency |
| document_versions | Immutable — no concurrency needed |
| storage_objects | ReferenceCount via atomic SQL `UPDATE ... SET ReferenceCount = ReferenceCount + 1` |

**Lost update prevention:** EF Core `IsRowVersion()` on Document; retry policy in handler (3 attempts).

---

## 5. Migration from Legacy `Files` Table

| Legacy `Files` | New mapping |
|--------------|-------------|
| Id | documents.Id |
| OwnerService | documents.OwnerModule |
| CreatorId | documents.OwnerEntityId (parse Guid) or metadata |
| FolderName | document_types inference |
| StoragePath | storage_objects.ObjectKey |
| FileName | document_versions.OriginalFileName |
| HashSha256 | storage_objects.ChecksumSha256 |
| IsDeleted | documents.Status = Recycled |
| FileRevisions | audit_entries (migration one-time) |

Migration job: `LegacyFileMigrationWorker` — idempotent by legacy Id.

---

## 6. Query Patterns & Performance

| Query | Index used |
|-------|------------|
| Get by DocumentId | PK |
| List by owner | IX_documents_owner |
| Retention due today | IX_documents_purge_scheduled |
| Dedup on upload | IX_storage_objects_checksum |
| Audit by document | audit (DocumentId, Timestamp) |

**N+1 prevention:** `Include` versions only when explicitly needed; list queries use projection.

**AsNoTracking:** All read queries except command load-for-update.

---

## 7. Future Scalability

| Scale trigger | Action |
|---------------|--------|
| >50M documents | Partition documents by CreatedAt year |
| >100M audit rows | Partition audit_entries monthly |
| Search latency | OpenSearch cluster scale-out |
| Blob size | Storage tiering + CDN |

---

## Related Documents

- [Domain Specification](./DCC_DOMAIN_SPECIFICATION.md)
- [Architecture Bible](./DCC_ARCHITECTURE_BIBLE.md)
- [API Specification](./DCC_API_SPECIFICATION.md)
