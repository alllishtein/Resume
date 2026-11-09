# DCC SDK Specification

> `IDocumentPlatformClient` — public .NET SDK for Dejban modules  
> Package: `PayamGostar.Dejban.DocumentPlatform` (target: Common or NuGet internal)

---

## 1. Design Principles

1. **Hide storage completely** — no paths, keys, buckets in public API
2. **Return DocumentId** — sole persistent reference for modules
3. **Forward JWT** — user context preserved via `AuthForwardingHandler`
4. **ErrorOr** — consistent with Dejban application layer
5. **Async only** — all methods accept `CancellationToken`
6. **Idempotent uploads** — optional `IdempotencyKey` (Phase B)

---

## 2. Registration

```csharp
// Dejban.Common.Infrastructure — normative registration point
services.AddDocumentPlatform(configuration);

// Single HTTP client named "DocumentPlatform"
// BaseUrl: configuration["DocumentPlatform:BaseUrl"] default http://dcc:80
// Timeout: 120s default
```

**Removes:** duplicate `AddDccClient` calls in module Infrastructure and Dejban.Api Program.cs.

---

## 3. Interface Specification

```csharp
public interface IDocumentPlatformClient
{
    // --- Upload & Version ---
    Task<ErrorOr<DocumentReference>> UploadDocumentAsync(
        UploadDocumentRequest request,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<DocumentReference>> ReplaceDocumentAsync(
        Guid documentId,
        ReplaceDocumentRequest request,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<DocumentReference>> CreateVersionAsync(
        Guid documentId,
        CreateVersionRequest request,
        CancellationToken cancellationToken = default);

    // --- Read ---
    Task<ErrorOr<DocumentMetadata>> GetMetadataAsync(
        Guid documentId,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<Stream>> DownloadContentAsync(
        Guid documentId,
        int? versionNumber = null,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<IReadOnlyList<DocumentSummary>>> ListByOwnerAsync(
        ListDocumentsRequest request,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<PagedResult<DocumentSearchHit>>> SearchAsync(
        SearchDocumentsRequest request,
        CancellationToken cancellationToken = default);

    // --- Media ---
    Task<ErrorOr<Uri>> GetThumbnailUriAsync(
        Guid documentId,
        ThumbnailSize size = ThumbnailSize.Medium,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<Uri>> GetPreviewUriAsync(
        Guid documentId,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<SignedUrl>> GenerateSignedUrlAsync(
        Guid documentId,
        SignedUrlRequest request,
        CancellationToken cancellationToken = default);

    // --- Lifecycle ---
    Task<ErrorOr<Success>> RecycleDocumentAsync(
        Guid documentId,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<Success>> RestoreDocumentAsync(
        Guid documentId,
        CancellationToken cancellationToken = default);

    // --- Attach / Detach (logical link, not blob copy) ---
    Task<ErrorOr<DocumentReference>> AttachDocumentAsync(
        AttachDocumentRequest request,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<Success>> DetachDocumentAsync(
        DetachDocumentRequest request,
        CancellationToken cancellationToken = default);

    // --- Permissions (module delegates ACL to DCC) ---
    Task<ErrorOr<Success>> GrantPermissionAsync(
        GrantPermissionRequest request,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<Success>> RevokePermissionAsync(
        RevokePermissionRequest request,
        CancellationToken cancellationToken = default);

    // --- Copy / Move (Phase C) ---
    Task<ErrorOr<DocumentReference>> CopyDocumentAsync(
        CopyDocumentRequest request,
        CancellationToken cancellationToken = default);

    Task<ErrorOr<Success>> MoveDocumentAsync(
        MoveDocumentRequest request,
        CancellationToken cancellationToken = default);
}
```

---

## 4. Request / Response DTOs

### 4.1 UploadDocumentRequest

| Property | Type | Required |
|----------|------|----------|
| OwnerModule | string | Yes |
| OwnerEntityId | Guid | Yes |
| DocumentTypeKey | string | Yes |
| SiteId | Guid | Yes |
| FileStream | Stream | Yes |
| FileName | string | Yes |
| ContentType | string | Yes |
| Metadata | JsonObject? | No |
| Tags | IReadOnlyList<string>? | No |

### 4.2 DocumentReference (return type)

| Property | Type | Notes |
|----------|------|-------|
| DocumentId | Guid | **Only field modules persist** |
| VersionNumber | int | Informational |
| Status | DocumentStatus | May be Scanning initially |
| ChecksumSha256 | string? | Optional verify |

**Explicitly excluded:** StoragePath, BlobKey, InternalUrl

### 4.3 DocumentMetadata

Full metadata per API spec — no storage internals.

### 4.4 AttachDocumentRequest

Re-assigns logical ownership without re-uploading bytes:

| Property | Purpose |
|----------|---------|
| DocumentId | Existing document |
| NewOwnerEntityId | e.g. copy visitor photo to new visit record |
| NewOwnerModule | Usually same module |

---

## 5. Method Semantics

| Method | HTTP mapping | Idempotent |
|--------|--------------|------------|
| UploadDocumentAsync | POST /upload | With Idempotency-Key |
| ReplaceDocumentAsync | POST /versions (sets current) | No |
| CreateVersionAsync | POST /versions | No |
| RecycleDocumentAsync | DELETE /documents/{id} | Yes |
| RestoreDocumentAsync | POST /restore | Yes |
| GenerateSignedUrlAsync | POST /signed-url | No |

---

## 6. Error Codes

| Code | Meaning | Module action |
|------|---------|---------------|
| Document.NotFound | Invalid DocumentId | Clear stale ref |
| Document.Quarantined | Virus detected | Show error, don't save ref |
| Document.AccessDenied | Permission | Fail operation |
| Document.QuotaExceeded | Site/module quota | Retry later / notify admin |
| Document.InvalidMetadata | Schema fail | Fix payload |
| DocumentPlatform.Unavailable | 503 | Retry with backoff |

---

## 7. Usage Pattern — Personnels

```csharp
// Normative pattern — not generated code
var uploadResult = await documentPlatform.UploadDocumentAsync(new UploadDocumentRequest
{
    OwnerModule = DocumentPlatformModules.Personnels,
    OwnerEntityId = personnel.Id,
    DocumentTypeKey = DocumentTypes.Personnel.Avatar,
    SiteId = personnel.SiteId,
    FileStream = stream,
    FileName = "avatar.jpg",
    ContentType = "image/jpeg"
}, cancellationToken);

if (uploadResult.IsError)
    return uploadResult.Errors;

personnel.SetAvatarDocumentId(uploadResult.Value.DocumentId);
await unitOfWork.SaveChangesAsync(cancellationToken);
```

---

## 8. Usage Pattern — Event Handler

```csharp
public sealed class DocumentPurgedIntegrationEventHandler
    : IntegrationEventHandler<DocumentPurgedIntegrationEvent>
{
    public override async Task Handle(DocumentPurgedIntegrationEvent e, CancellationToken ct)
    {
        var personnel = await repository.GetByAvatarDocumentIdAsync(e.DocumentId, ct);
        if (personnel is null) return;

        personnel.ClearAvatarDocumentId();
        await unitOfWork.SaveChangesAsync(ct);
    }
}
```

---

## 9. Resumable Upload (Phase D)

Extension interface:

```csharp
public interface IResumableUploadClient
{
    Task<ErrorOr<UploadSession>> InitiateUploadAsync(...);
    Task<ErrorOr<Success>> UploadChunkAsync(UploadSession session, byte[] chunk, int index);
    Task<ErrorOr<DocumentReference>> CompleteUploadAsync(UploadSession session);
}
```

For mobile guard apps — optional add-on package.

---

## 10. Testing Support

`IDocumentPlatformClient` registered as:

- Production: `DocumentPlatformHttpClient`
- Tests: `InMemoryDocumentPlatformClient` (Dejban.IntegrationTests)

---

## 11. Versioning

| SDK Version | API Version | Notes |
|-------------|-------------|-------|
| 1.x | v1 Files API | Deprecated |
| 2.0 | v2 platform | Phase A |
| 2.1 | v2 + search | Phase B |

SemVer — breaking changes only on major SDK version.

---

## Related Documents

- [API Specification](./DCC_API_SPECIFICATION.md)
- [Module Integration Guide](./DCC_MODULE_INTEGRATION_GUIDE.md)
- [Event Specification](./DCC_EVENT_SPECIFICATION.md)
