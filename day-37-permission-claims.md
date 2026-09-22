# Day 37 — Permission claims

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Day 36 goft Identity *chekasi hasti*. In ruz: **che kar mituni bokoni?**

To Dejban dastresi ba **claim catalog** idare mishe, na faghat role string:

1. **`ApplicationClaimType`** — mesal `permission`, `endpoint` (Name)  
2. **`ApplicationClaim`** — `Value` ≈ **componentId** (FE/BE key), tree ba Parent/Sub  
3. **Assign** be User / Role / Position / Site (+ **Exclude** az user) — **per SiteId**  
4. **`ClaimService.GetUserSiteClaimsAsync`** — jam'e hame manabe' − exclude (+ expand children)  
5. **`IClaimsTransformation` (`CustomClaimsTransformation`)** — har request principal enrich: claim `permission` ba value `"{siteId}|{componentId}"`  
6. **Authorize:** `[PermissionAuthorization("…")]` ya Minimal `.RequirePermissions(…)` → dynamic policy `permission:a,b` → check ba **X-Site-Id** header (site-scoped)

Endpoint claim joda (`endpoint`) + sync az service-ha (`EndpointSyncService`) — API path ↔ permission map.

**Band-e gharardad-e jadid:** tozihat ravoontar va sade-tar.

---

# BAKHSH-E AVAL: WORLD — permission / claim

## Farz kon — kart-e hotel + otagh-ha

Role = «Staff».  
Permission = «mitunam dar-e anbar ro baz konam», «mitunam gozaresh mali bebinam».

Yek nafar mitune chand role dashte bashe; yek permission mitune az role *ya* mostaghim be user biaad; yek permission mitune *baraye ye site* bashe na hameja.

**Claim** (JWT/Identity ma'ni): `type` + `value`.  
Mesal: type=`permission`, value=`accessPersonnelView`.

---

## RBAC vs Claims — sade

| model | soal | za'f |
|---|---|---|
| **RBAC** faghat | «role-et chi-e?» | role explosion; permission fine-grain sakht |
| **Claims / permissions** | «in hagho dari?» | catalog management |
| **Dejban** | hardo: Role/Position + Permission claims + Site scope | pichide ama flexible |

---

## Chera site-scoped?

Sherkat chand site/shobe.  
User to Site A «delete personnel» dare; to Site B na.  
Pas permission value to principal = `siteGuid|componentId` — na faghat componentId global.

Header **`X-Site-Id`** (Day 16) mige *alan* kodom site; evaluator check mikone oon site permission dare.

---

## Dynamic authorization policy (WORLD ASP.NET)

```csharp
[Authorize(Policy = "permission:foo,bar")]
// ya attribute ke Policy string misaze
```

`IAuthorizationPolicyProvider` age policy az ghabl register nabashe, **runtime** misaze ba `PermissionRequirement`.

**Yani chi?** Lazem nist har permission ye `options.AddPolicy` dasti — Dejban dynamic.

---

# BAKHSH-E DOVOM: DEJBAN — model va flow

## Naqshe-ye yek negah

```
Catalog: ClaimType + ApplicationClaim (tree, Value=componentId)
    ↓ assign
UserClaims / RoleClaims / PositionClaims / SiteClaims  (− UserExcludedClaims)
    ↓
ClaimService (cache) → SiteClaimDTO per site
    ↓
IClaimsTransformation → ClaimsPrincipal
    permission = "{siteId}|{value}"
    endpoint  = "{siteId}|{endpointKey}"
    role/position similarly scoped
    ↓
[PermissionAuthorization] / RequirePermissions
    + X-Site-Id → SiteScopedPermissionEvaluator
```

---

## Qesmat 1 — Catalog

### ApplicationClaimType

```csharp
public class ApplicationClaimType
{
    public Guid Id { get; set; }
    public string Name { get; set; }        // "permission" | "endpoint" | …
    public string DisplayValue { get; set; }
    public string? Description { get; set; }
}
```

`CustomClaims.Permission = "permission"` / `Endpoint = "endpoint"` — Name ba in align.

### ApplicationClaim

```csharp
public class ApplicationClaim
{
    public Guid Id { get; set; }
    public string Value { get; set; }        // componentId
    public string DisplayValue { get; set; } // UI label
    public Guid ClaimTypeId { get; set; }
    public Guid? ParentApplicationClaimId { get; set; }
    public ICollection<ApplicationClaim> SubApplicationClaims { get; set; }
    // Users, Roles, Positions, SiteClaims
}
```

**Yani chi?**  
- `Value` = key-e fanni (FE `componentId`, BE attribute string)  
- Tree: parent «Access Management tab» → child «Save Claims button»  
- Assign parent → children expand (`ExpandWithChildrenAsync` / `AppendChildClaims`)

---

## Qesmat 2 — Chahar manba'-e grant + exclude

| manba' | ma'ni-ye sade |
|---|---|
| **RoleClaims** | role X to site S in claim-ha |
| **PositionClaims** | semat/position |
| **UserClaims** | special access mostaghim |
| **SiteClaims** | hame-ye a'za'-e site (bishtar endpoint) |
| **UserExcludedClaims** | «in claim ro *nadah*» (override minus) |

**Farz kon:** Role midahad 10 permission; Exclude yeki ra mikone; User special yeki ezafe.  
ClaimService jam mikone.

Assign handlers (mesal `AssignClaimsToUser`):

1. Validate sites  
2. Delete old grants for those sites  
3. Expand claimIds ba children  
4. Insert rows `(UserId, ClaimId, SiteId)`  
5. **Blacklist** hame access tokens user  
6. **Invalidate** `IUserSiteClaimsCache`

**Chera blacklist?** Token/transform cache kohne; permission avaz → session ghabli namande.

---

## Qesmat 3 — ClaimService (qalb)

`GetUserSiteClaimsAsync(userId)`:

1. Sites az direct user sites + role sites + position sites  
2. Load user/role/position/site claims + excluded  
3. Expand children; excluded children ham exclude  
4. Per site: `SiteClaimDTO(siteId, name, roleClaims, positionClaims, userClaims, siteClaims)`  
5. Cache (`ICacheService`, TTL kutah ~2s local + cache key userId)

**Yani chi?** Yek function = «map-e dastresi user to hame site-hash». Transformation va GetMe/FE az in no'-e data mian.

`IgnoreQueryFilters` — tenant filter nabayad calc dastresi ro beshkane.

---

## Qesmat 4 — CustomClaimsTransformation

Har authenticated request (ba'd JWT validate):

```csharp
// permissions flatten:
// "{siteId}|{permissionValue}" az Position + Role + User claims
// endpoints: + SiteClaims
claimsIdentity.AddClaim(new Claim(CustomClaims.Permission, permission));
```

Identity name `"SiteClaims"` — dobare transform nakone.

**Yani chi?** JWT khodesh shayad faqat `sub` + kami claim dashte bashe; **enrichment** har request az DB/cache miad.  
Tradeoff: fresh-ish permissions bedune JWT re-issue hamishe; hazine ClaimService+cache.

Day 06/25: cache + blacklist ba assign sync.

---

## Qesmat 5 — CustomClaims constants

```csharp
public static class CustomClaims
{
    public const string Sub = "sub";
    public const string Site = "site";
    public const string SiteClaims = "site_claims";
    public const string Position = "position";
    public const string Role = "role";
    public const string Permission = "permission";
    public const string Endpoint = "endpoint";
}
```

Format scoped: `siteId|value` baraye permission/role/position/endpoint.

---

## Qesmat 6 — Enforce permission

### Controller attribute

```csharp
[PermissionAuthorization(
    VehiclePolicyPermissions.ManualApprove,
    VehiclePolicyPermissions.TrafficManagement)]
```

Misaze policy: `permission:ManualApprove,TrafficManagement` (join).

### Dynamic policy provider

`AuthorizationPolicyProvider` age `permission:…` did → `PermissionRequirement(perms)`.

### Handler

```csharp
var headerSiteIds = httpContext.GetHeaderSiteIds();
if (SiteScopedPermissionEvaluator.HasAnyPermission(user, headerSiteIds, requirement.Permissions))
    context.Succeed(requirement);
```

**HasAny** (OR beyn permission list). Baraye *yeki* az site-haye header: user oon permission ro dare → succeed (na «hame site-ha» — fargh ba `JwtSitePermission.Has` ke All sites).

**SiteClaims twist:** evaluator `site_claims` ro mesl **feature license catalog** mibine — age site hichkodom az required-ha ro «license» nakarde, block nemikone; age license list gheyr-khali va overlap nadare ba matched → continue. Comment code: «not an AND of every listed permission.»

**Yani chi?** Permission grant ≠ site product feature flag; hardo claim type, semantics evaluator daqiq.

### Minimal APIs

```csharp
.RequirePermissions("accessPersonnelView")
```

→ `PermissionRequirementFilter` haman evaluator.

### Helper ACL

`JwtSitePermission.Has(httpContext, permission, siteId?)` — dar handler business (capacity override) bedune attribute.

---

## Qesmat 7 — Endpoint claims vs Permission claims

| | permission | endpoint |
|---|---|---|
| maqsad | UI feature / business action | API route allow |
| Value mesal | `accessPermissionSaveClaimsButton` | `AccountManagement/AssignClaimsToUser` style key |
| Enforce | PermissionAuthorization | EndpointAccess policy / filter |
| Sync | dasti/admin catalog | `EndpointSyncService` az microservice endpoints |

`IdentityServerEndpointPermissionMap` — map endpoint → permission ta admin UI coherent.

**Farz kon:** FE button ba componentId; API ba endpoint claim. Hardo bayad grant she — defense in depth.

`RequireEndpointAccess()` roye Minimal — Day 17/auth.

---

## Qesmat 8 — EndpointSyncService (kholase)

Identity az Dejban/ACL/DCC/… ba MassTransit request list endpoint migire → upsert `ApplicationClaim` type endpoint.  
Careful: delete claims wipe grants — code comment warn.

**Yani chi?** Catalog endpoint ba code sync; kamtar manual typo.

---

## Se dastan (farz kon)

### A) Admin Save Claims button

1. FE `componentId=accessPermissionSaveClaimsButton` — agar permission nist, hide/disable (Day 49)  
2. API AssignClaims → PermissionAuthorization / endpoint map  
3. Transform principal `site|accessPermissionSaveClaimsButton`  
4. Evaluator OK ba X-Site-Id  

### B) Exclude yek claim

User az role «View» dare; Exclude View → ClaimService hazf (+ children) → UI/API na.

### C) Avaz role claims

AssignClaimsToRole → invalidate cache users → blacklist tokens → next request transform jadid.

---

## Smell-ha (kamel + tozih)

1. **Complexity** — 4 grant source + exclude + tree + site = onboarding sakht  
2. **String componentId** — typo FE/BE mismatch silent deny  
3. **JWT kam claim + transform har request** — ClaimService load; cache mohem  
4. **OR permissions in attribute** — document «any of»  
5. **Site header empty** → deny (secure default)  
6. **SuperAdmin** bypass? check TenantContext / special paths  
7. **Endpoint sync delete** risk wipe grants  
8. **Duplicate VehiclePolicyPermissions** constants vs DB catalog — dual source  
9. **Permission vs Endpoint confusion** baraye junior  
10. **Cache TTL 2s** — eventual consistency kutah  
11. **Blacklist on assign** — UX logout-ish hame session  
12. **Fat transformation** — claim count ziad to principal  

---

## Debug checklist (sade)

1. ClaimType Name exact `permission`?  
2. ApplicationClaim.Value == string to attribute?  
3. Grant row SiteId == X-Site-Id?  
4. Excluded?  
5. Children expand expected?  
6. Cache stale — invalidate?  
7. Token blacklist ba'd assign?  
8. Transform ran? (identity SiteClaims)  
9. Principal has `siteGuid|value`?  
10. Header site ids parse?  
11. Policy name `permission:…`?  
12. Endpoint vs permission wrong type?  

---

## 25 soal-e mosahebe

1. Permission claim chie?  
2. RBAC vs claims Dejban?  
3. ApplicationClaim.Value?  
4. ClaimType permission vs endpoint?  
5. Chahar grant source?  
6. Exclude chie?  
7. Tree parent/child?  
8. Chera siteId\|value?  
9. ClaimService chikar?  
10. IClaimsTransformation?  
11. PermissionAuthorizationAttribute?  
12. Dynamic policy provider?  
13. SiteScopedPermissionEvaluator?  
14. X-Site-Id ertebat?  
15. RequirePermissions Minimal?  
16. JwtSitePermission.Has?  
17. AssignClaims blacklist chera?  
18. Cache invalidate?  
19. EndpointSyncService?  
20. componentId FE?  
21. HasAny vs HasAll?  
22. SiteClaims type?  
23. IgnoreQueryFilters chera?  
24. Dual catalog smell?  
25. Resume 60s?

---

## Senario-ha

### A) 403 ba'd az grant

Cache/token kohne; ya SiteId header ghalat; ya Value typo.

### B) Button hast API 403

FE permission OK; endpoint claim na — map/sync.

### C) Cross-site leak?

Evaluator site-scoped — Site A permission nabayad Site B ro baz kone.

### D) Parent assign

Expand children → child buttons ham grant.

---

## Mini lab

1. Read `ApplicationClaim` + ClaimType  
2. `ClaimService` aggregation skim  
3. `CustomClaimsTransformation` permission flatten  
4. `PermissionAuthorizationAttribute` + PolicyProvider  
5. `SiteScopedPermissionEvaluator` / `JwtSitePermission`  
6. `AssignClaimsToUser` blacklist+cache  
7. Grep `RequirePermissions` / `PermissionAuthorization`  
8. `IdentityServerEndpointPermissionMap` chand radif  

---

## Resume

**kutah:**

> Designed a site-scoped permission system on ASP.NET Identity claims: a catalog of `ApplicationClaim`/`ClaimType` (permission + endpoint, hierarchical componentIds), grants via user/role/position/site with exclusions, aggregation in `ClaimService`, per-request enrichment through `IClaimsTransformation`, and enforcement via dynamic `permission:…` policies, Minimal API filters, and `X-Site-Id`-aware evaluators.

**bullet-ha:**

- Modeled claim catalog with parent/child expansion and multi-source assignment  
- Enriched principals with `{siteId}|{value}` permission/endpoint claims  
- Enforced authorization with `PermissionAuthorization` / `RequirePermissions` and cache/token invalidation on grant changes  

**skill-ha:** `Claims-based authorization, RBAC, ASP.NET Core Authorization, IClaimsTransformation, Policy provider, Multi-tenant permissions, Identity`

---

## File-haye mohem

| chi | koja |
|---|---|
| Entities | `IdentityServer/Domain/Entities/ApplicationClaim*.cs` |
| ClaimService | `IdentityServer/Infrastructure/Services/ClaimService.cs` |
| Transformation | `Common/Authorization/CustomClaimsTransformation.cs` |
| CustomClaims | `Common/Authentication/CustomClaims.cs` |
| Policy provider | `Common/Authorization/AuthorizationPolicyProvider.cs` |
| Permission attr/handler | `Common/Authorization/PermissionAuthorization*.cs` |
| Evaluator | `SiteScopedPermissionEvaluator.cs` |
| Minimal extensions | `AuthorizationExtensions.cs` |
| Assign user | `AssignClaimsToUserCommandHandler.cs` |
| Endpoint sync | `EndpointSyncService.cs` |
| Map | `IdentityServerEndpointPermissionMap.cs` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 06 JWT | sub; enrich ba'd validate |
| 16 Tenancy | X-Site-Id + site scope |
| 36 Identity | User/Role/Position base |
| 17 Minimal | RequirePermissions |
| 25 Cache | ClaimService cache |
| 49 Auth UI | componentId guards |
| 28 DCC | file RequiredPermission |

---

## Chejori digest koni

1. WORLD hotel + RBAC/claims (15 min)  
2. Catalog + assign sources (20 min)  
3. ClaimService + transform (25 min) — **qalb**  
4. Enforce attribute/filter/header (20 min)  
5. Endpoint vs permission (15 min)  
6. Lab + 25 soal (25 min)  

---

## Glossary (sade)

| kalame | ma'ni-ye yek khati |
|---|---|
| Permission | haghe anjam action/UI |
| Claim | type+value pair |
| componentId | Value string FE/BE |
| ClaimType | permission/endpoint/… |
| Grant | assign claim be principal |
| Exclude | minus override |
| Site-scoped | per SiteId |
| Transformation | enrich ClaimsPrincipal |
| Dynamic policy | policy az esm runtime |
| Endpoint claim | allow API route |
| Catalog | ApplicationClaims table |

---

## Deep dive — format `siteId|value`

```
a1b2-...|accessPersonnelView
```

Split `|` → Guid site + permission string.  
Group by site → HashSet permissions.  
Header sites must **all** (JwtSitePermission) or **any** (evaluator — check implementation) match.

Read `SiteScopedPermissionEvaluator` daqiq: HasAnyPermission = baraye *har* header site, aya *yeki* az required permissions hast?

---

## Deep dive — HasAnyPermission semantics

Attribute chand permission = OR beyn anha.  
Chand site to header: evaluator mige siteIds + permissions — daqiq bekhun source; ACL `JwtSitePermission.Has` = **All** header/requested sites must contain that one permission.

**Smell:** do helper semantics — document.

---

## Deep dive — Position value format

Transform: `"{siteId}|{positionName}"` baraye claim type position.  
Role: `"{siteId}|{normalizedRoleName}"`.  
Permission: `"{siteId}|{componentId}"`.

Yeksan pattern scoped.

---

## Anti-pattern

```csharp
// BAD: if (User.IsInRole("Admin")) everywhere
// GOOD: permission checks / policies

// BAD: permission global bedune site
// GOOD: siteId|value + X-Site-Id

// BAD: typo componentId FE != DB Value
// GOOD: shared constants / codegen later

// BAD: forget invalidate cache on assign
// GOOD: blacklist + UserSiteClaimsCache (Dejban)
```

---

## Interview 60s (ravoon)

> «We don’t rely on roles alone. There’s a claim catalog—permissions and endpoints keyed by componentId, with a parent/child tree. Grants come from roles, positions, users, and sites, minus exclusions, always per site. ClaimService builds that map; IClaimsTransformation puts site-scoped permission claims on the principal each request. APIs use PermissionAuthorization or RequirePermissions, evaluated against X-Site-Id. Changing grants blacklists tokens and invalidates the claims cache.»

---

## Quick self-test

1. Value field? → componentId  
2. Types asosi? → permission, endpoint  
3. Exclude? → UserExcludedClaims  
4. Transform class? → CustomClaimsTransformation  
5. Permission format? → siteId\|value  
6. Attribute? → PermissionAuthorization  
7. Policy prefix? → permission:  
8. Header? → X-Site-Id  
9. Assign side effect? → blacklist + cache invalidate  
10. Endpoint sync? → EndpointSyncService  

---

## Final checklist

- [ ] Catalog + tree  
- [ ] 4 grants + exclude  
- [ ] ClaimService  
- [ ] Transformation  
- [ ] Enforce + site scope  
- [ ] Endpoint vs permission  
- [ ] Resume  

---

## Extra — FE componentId (pish-nama Day 49)

FE: `if (!hasPermission('accessPermissionView')) hide`.  
Haman string = `ApplicationClaim.Value`.  
Backend attribute haman string.  
Yek dictionary = source of truth DB; FE/BE copy.

---

## Extra — Farz kon SuperAdmin

Ba'zi path-ha SuperAdmin hame site; transform/tenant special.  
Permission catalog hanuz baraye admin UI management.  
Bypass ≠ «bedune claim system».

---

## Extra — DCC file RequiredPermission

File metadata mitune permission string bekhade; `FileAccessService.HasPermission` shabih site-scoped.  
Haman claim model cross-service.

---

## Extra — RoleAuthorization / PositionAuthorization

Sibling patterns: policy `role:…` / `position:…` + handlers.  
Permission fine-grain; role/position coarse.  
Dynamic provider hardo.

---

## Map — request ba PermissionAuthorization

```
JWT valid
→ CustomClaimsTransformation (ClaimService)
→ Principal has permission claims
→ Authorize filter Policy permission:a,b
→ PermissionAuthorizationHandler
→ GetHeaderSiteIds + HasAnyPermission
→ OK / 403
```

---

## Map — AssignClaimsToRole

```
Replace RoleClaims for sites
Expand children
Save
Invalidate affected users' claim cache
Blacklist their tokens
```

---

## Lab aha

1. Grant permission → without new login, ba'd cache TTL/blacklist — behavior  
2. Wrong X-Site-Id → 403  
3. Exclude child of granted parent  
4. Compare endpoint claim vs permission on same screen  

---

## What Day 37 is *not*

- Full FE AuthGuard code (Day 49)  
- OAuth scopes standard  
- Policy-based ABAC engine generic  

Focus: **Dejban permission/endpoint claims + site-scoped authorize**.

---

## Resume keywords (ATS)

`Claims-based authorization` · `RBAC` · `ASP.NET Core Authorization` · `IClaimsTransformation` · `Permission policies` · `Multi-tenant` · `componentId` · `Identity`

---

## Band-e gharardad-e jadid

> Tozihat ravoontar/sade-tar: hotel kart; siteId\|value; dastan assign→blacklist; farq endpoint/permission.

---

## 10 jomle fluency

1. Permission = claim type permission + componentId value.  
2. Site-scoped ba siteId\|value.  
3. Grants: user/role/position/site − exclude.  
4. Tree expand children.  
5. ClaimService aggregate + cache.  
6. Transformation enrich principal.  
7. PermissionAuthorization → dynamic policy.  
8. X-Site-Id evaluator.  
9. Assign → blacklist + invalidate.  
10. Endpoint claim ≠ permission claim.

---

## Extra — Chera na hame permission to JWT?

JWT bozorg + stale ta expire.  
Transform+cache = update sari'tar ba blacklist.  
Hybrid: identity to JWT; authorization detail enrich.

---

## Extra — ApplicationUserClaim vs IdentityUserClaim

Custom entity ba ClaimId FK + SiteId — na faghat string ClaimValue Identity default.  
Catalog normalize; referential integrity.

---

## Extra — Farz kon GetMe / site switch

FE site avaz mikone → `X-Site-Id` avaz → haman JWT → transform haman permissions → evaluator site digar.  
Button-ha ba componentId per site farq mikonan.  
**Yani:** token avaz nemikhad baraye switch site; header + site-scoped claims kafi-st (ta grant oon site bashe).

---

## Extra — Chera Position *va* Role?

Role = grouh amniati (Admin, Operator).  
Position = semat sazmani (HSE, Guard).  
Har kodom claim set joda; user mitune hardo dashte bashe to site.  
ClaimService hardo ro merge mikone.

---

## Extra — Debugging principal (practical)

Ba'd login, breakpoint to handler:

```
User.FindAll("permission").Select(c => c.Value)
```

Bayad `guid|access…` bebini. Age khali: transform/cache/userId. Age hast ama 403: header site / typo Value / SiteClaims license branch.

---

## Extra — AssignClaimsToSite vs User

SiteClaims bishtar baraye endpoint / feature catalog site-level.  
User/Role/Position baraye permission UI.  
Evaluator SiteClaims ro «license» mibine — ba permission AND narm.

---

## Extra — Security review quick

- Deny by default (no header sites → false)  
- No global permission string without site in principal format  
- Grant change → revoke tokens  
- IgnoreQueryFilters only inside ClaimService calc — na leak data API  

---

## Extra — Comparison WORLD simple Authorize Roles

```csharp
[Authorize(Roles = "Admin")]
```

Sade; Dejban multi-site + hundreds componentId → dynamic permission policies.  
Roles hanuz hastan (claim role + RoleRequirement) — complementary.

---

## Extra — Soalat-e «chera» yek-khat

**Chera blacklist on assign?** Stale transform/JWT session.  
**Chera tree?** UX: tick parent → children.  
**Chera endpoint sync?** API surface drift.  
**Chera string Value?** FE/BE share key bedune GUID to UI.  
**Chera 2s cache?** Balance freshness vs DB hit.

---

## Khoruj-e zehni

> Midunam dastresi Dejban ba catalog claim (permission/endpoint), grant chand-manba'e per site, ClaimService, transformation be siteId|value, va enforce ba policy/filter + X-Site-Id-e. Midunam exclude, tree, blacklist, va farq endpoint ba permission.

Age in paragraph mal-e to shod — Day 37 done.

---

*Day 37 tamum. Ba'd: Day 38 — Excel import (amade). Fehrest: [README.md](./README.md).*
