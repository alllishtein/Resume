# Day 36 — ASP.NET Identity

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**ASP.NET Identity** = framework-e membership toye .NET: user, password hash, role, claim, lockout, token provider, store EF. To Dejban **IdentityServer** microservice malek-e in stack-e — na Dejban.Api.

Chizi ke Dejban *customize* karde:

1. **`ApplicationUser : IdentityUser`** — FirstName, NationalCode, IsActive, Sites, Positions, ApiKeys, …  
2. **`ApplicationRole : IdentityRole`** — Description + Claims/Sites  
3. **`PayamGostarUserManager : UserManager<>`** — phone find, session token, multi-session + blacklist, Create/Update ba `saveChanges` flag  
4. **`CustomUserStore : UserStore<…>`** — refresh/session token ba `Jti` / `AllowMultipleSession`  
5. **`UserConfirmation`** — «confirmed» = `IsActive` (na email confirm classic)  
6. **`IdentitySettings`** (Options) → Password / Lockout / SignIn bind be `IdentityOptions`  
7. Login ba **`SignInManager.CheckPasswordSignInAsync`** + JWT khodemon (Day 06) — cookie Identity session classic *na* primary API auth  

Day 37 = Permission claims omigh. In ruz = **Identity engine** (user/password/store/manager).

**Band-e gharardad-e jadid:** tozihat ravoontar va sade-tar — «farz kon / yani chi / chera».

---

# BAKHSH-E AVAL: WORLD — Identity chie?

## Farz kon — receptionist hotel

Moshtari miad: esm, password, otagh (role), kart-e dastresi (claim), agar 5 bar password eshtebah → otagh ghofl (lockout).

ASP.NET Identity hamin receptionist-e baraye app:

| Identity concept | ma'ni-ye sade |
|---|---|
| User | hesab |
| PasswordHasher | hash (na plain text) |
| Role | grouh dastresi kare |
| Claim | haghe/attribute (permission, site, …) |
| UserManager | API kar ba user |
| SignInManager | check password / lockout / 2FA hooks |
| RoleManager | CRUD role |
| UserStore | persistence (inja EF) |
| Token providers | reset password, refresh hash, … |

**Yani chi?** To nemisazi az sefr hashing + lockout + normalization. Framework midahad; to extend mikoni.

---

## Chera Identity ≠ JWT?

| Identity | JWT (Day 06) |
|---|---|
| *chekasi hasti* to DB + password | *token* baraye request-haye ba'd |
| UserManager / tables AspNet* | Bearer / cookie token |
| Lockout, hash, roles store | stateless validation + blacklist |

Dejban: Identity **sakhte/verify** mikone; ba'd **TokenProvider** JWT misaze; Gateway JWT validate + Redis revoke.

**Chera important?** Mosahebe: «We use Identity for credentials and user store; APIs authenticate with JWT, not Identity cookies.»

---

## AddIdentity — skeleton WORLD

```csharp
services.AddIdentity<ApplicationUser, ApplicationRole>(options => { /* password, lockout */ })
    .AddEntityFrameworkStores<ApplicationDbContext>()
    .AddDefaultTokenProviders();
```

Ba'd:

- `UserManager<TUser>`  
- `SignInManager<TUser>`  
- `RoleManager<TRole>`  
- tables via `IdentityDbContext`

---

## IdentityDbContext generics

Identity EF generic-haye ziyad dare ta type-haye custom (UserClaim, UserToken, …) joda she. Dejban hame ro override karde ba `Application*` types.

---

# BAKHSH-E DOVOM: DEJBAN — IdentityServer

## Naqshe-ye yek negah

```
appsettings IdentitySettings
        ↓
AddIdentity + CustomUserStore + PayamGostarUserManager
        ↓
ApplicationDbContext : IdentityDbContext<…>
        ↓
Login / CreateUser / Roles / Tokens
        ↓
JWT TokenProvider + cookies + (optional) blacklist
```

---

## Qesmat 1 — `ApplicationUser`

```csharp
public class ApplicationUser : IdentityUser
{
    public bool IsActive { get; set; }
    public string FirstName { get; set; }
    public string LastName { get; set; }
    public string NationalCode { get; set; }
    public string Avatar { get; set; }
    public DateTime RegisterDate { get; set; }
    public string FullName => $"{FirstName} {LastName}".Trim();

    // nav: ExcludedClaims, UserClaims, Claims, UserTokens,
    // UserRoles, Roles, Positions, Sites, ApiKeys, ActivationHistory, …
}
```

**Az IdentityUser miad:** Id (string), UserName, Email, PhoneNumber, PasswordHash, SecurityStamp, LockoutEnd, AccessFailedCount, …

**Yani chi?** Base Identity + profile HR-ish + multi-site + custom claim model (Day 37).

---

## Qesmat 2 — `ApplicationRole`

```csharp
public class ApplicationRole : IdentityRole
{
    public string? Description { get; set; }
    public DateTime CreatedAt { get; set; }
    // Users, Claims, Sites
}
```

RoleManager CRUD + AssignClaimsToRole (Day 37).

---

## Qesmat 3 — DbContext

```csharp
public class ApplicationDbContext …
  : IdentityDbContext<
      ApplicationUser, ApplicationRole, string,
      ApplicationUserClaim, ApplicationUserRole, ApplicationUserLogin,
      ApplicationRoleClaim, ApplicationUserToken>(options), ITenantDbContext
```

+ MassTransit outbox/inbox entities  
+ tenant query filters (Day 16)

**Yani chi?** Yek DB Identity + business IdentityServer + messaging outbox.

---

## Qesmat 4 — Register Identity (daqiq)

```csharp
services.Configure<IdentitySettings>(…);
services.AddScoped<IUserConfirmation<ApplicationUser>, UserConfirmation>();

services.AddIdentity<ApplicationUser, ApplicationRole>(options =>
{
    options.SignIn.RequireConfirmedAccount = identitySettings.SignIn.RequireConfirmedAccount;
    // Password.* az IdentitySettings
    // User.RequireUniqueEmail, AllowedUserNameCharacters
    // Lockout MaxFailedAccessAttempts, DefaultLockoutTimeSpan (minutes)
})
.AddEntityFrameworkStores<ApplicationDbContext>()
.AddUserStore<CustomUserStore>()
.AddUserManager<PayamGostarUserManager>()
.AddErrorDescriber<PersianIdentityErrorDescriber>()
.AddDefaultTokenProviders();
```

### Yani chi, khat be khat?

| piece | ma'ni |
|---|---|
| Options bind | Day 34 — password policy az config |
| `IUserConfirmation` | SignIn «allowed»? → IsActive |
| `AddUserStore` | CustomUserStore jaygozin default |
| `AddUserManager` | PayamGostarUserManager |
| `PersianIdentityErrorDescriber` | error message Farsi |
| `AddDefaultTokenProviders` | refresh/reset token generate/verify |

---

## Qesmat 5 — `UserConfirmation` = IsActive

```csharp
public class UserConfirmation : IUserConfirmation<ApplicationUser>
{
    public Task<bool> IsConfirmedAsync(…) =>
        Task.FromResult(user.IsActive);
}
```

**Farz kon:** user password dorost, ama `IsActive=false`.  
`CheckPasswordSignInAsync` → `IsNotAllowed` → Login `Errors.Auth.DeActivated`.

**Chera?** Classic Identity «email confirmed»; inja activation flag business. Haman hook, ma'ni digar.

---

## Qesmat 6 — Login flow (Identity + JWT)

```csharp
// find by phone OR normalized username OR email
var user = await _userManager.Users.Include(Sites).Include(UserTokens)
    .SingleOrDefaultAsync(…);
if (user == null) return InvalidCredentials;

var identityResult = await _signInManager.CheckPasswordSignInAsync(
    user, command.Password, lockoutOnFailure: true);

if (!identityResult.Succeeded)
{
    if (IsLockedOut) return LockedOut;
    if (IsNotAllowed) return DeActivated;
    return InvalidCredentials;
}

var accessToken = _tokenProvider.CreateAccessToken(user);
var refreshTokenHash = await _userManager.GenerateUserTokenAsync(
    user, TokenOptions.DefaultProvider, RefreshToken);
var (refreshToken, jti) = _tokenProvider.CreateRefreshToken(refreshTokenHash);
await _userManager.SetAuthenticationTokenAsync(
    user, jti, accessToken, …, refreshTokenHash, sessionInfo);

// HttpOnly cookies Access + Refresh
```

**Yani chi be zaban-e adam?**

1. Identity user ro peyda + password + lockout + active check  
2. JWT access sakhte mishe (custom)  
3. Identity **token provider** ye hash baraye refresh misaze (store-shodani)  
4. Custom store row `ApplicationUserToken` ba Jti + AccessToken + SessionInfo  
5. Cookie baraye browser  

**Chera CheckPasswordSignInAsync na faghat CheckPasswordAsync?**  
Lockout + IsNotAllowed (confirmation) yekja. Security.

---

## Qesmat 7 — `PayamGostarUserManager` extensions

| method | chera |
|---|---|
| `FindByPhoneNumberAsync` | login ba phone mamul Iran |
| `SetAuthenticationTokenAsync` / `Remove…` | session refresh + jti |
| `IsActiveAsync` | wrap confirmation |
| `GenerateUserTokenAsync` override | single-session: SecurityStamp + blacklist last access |
| `CreateAsync(..., saveChanges)` | transaction ba Sites/history |

### AllowMultipleSession = false

```csharp
await UpdateSecurityStampAsync(user);
// on Login action: revoke last session AccessToken via ITokenBlackList
```

**Yani chi?** Session jadid → ghabli invalidate (stamp + Redis blacklist Day 06).  
Age `AllowMultipleSession=true` → chand token row (CustomUserStore Find by jti).

---

## Qesmat 8 — `CustomUserStore` + `ApplicationUserToken`

```csharp
public class ApplicationUserToken : IdentityUserToken<string>
{
    public string Jti { get; set; }
    public DateTime LoginDate { get; set; }
    public string AccessToken { get; set; }
    public SessionInfo SessionInfo { get; set; } // IP, device, OS, …
}
```

`SetTokenAsync`:

- multi-session → find by jti  
- single → find last token for user → update or add  

**Yani chi?** Identity «authentication token» table expand shode baraye session audit + refresh rotation (Day 06 omigh).

---

## Qesmat 9 — CreateUser

```csharp
// duplicate phone / national code checks
user.Sites = sites from command.SiteIds;
var identityResult = await _userManager.CreateAsync(user, password, saveChanges: false);
// ActivationHistory
await _context.SaveChangesAsync();
```

**Yani chi?** `CreateAsync` Identity: hash password, normalize name/email, validate password policy.  
`saveChanges: false` → yek SaveChanges ba Sites + history (transaction-ish).

Age IdentityErrors → map be ErrorOr.

---

## Qesmat 10 — RoleManager (sath-e in ruz)

`CreateRoleCommandHandler(RoleManager<ApplicationRole>)` — `CreateAsync`.  
Assign roles to user, assign claims to role → Day 37.

Identity midahad RoleManager; domain Claims custom.

---

## Farq WORLD default vs Dejban

| topic | default tutorial | Dejban |
|---|---|---|
| Auth API | cookie Identity | JWT + cookie token |
| Confirmation | email | IsActive |
| UserManager | default | PayamGostarUserManager |
| UserStore | default EF | CustomUserStore + Jti |
| Errors | English | Persian describer |
| Multi-tenant | — | Sites + tenant filters |
| Phone login | optional | first-class |

---

## Smell-ha (kamel + tozih)

1. **IdentityUser Id = string** — GUID string; join verbose  
2. **Login SingleOrDefault** phone/user/email — index lazeme  
3. **CreateUser Any() sync** — better async AnyAsync  
4. **Avatar TODO** file service  
5. **SecurityStamp invalidate** side effects — understand ghabl touch  
6. **AccessToken to DB** — secret-ish; protect DB + retention  
7. **SignInManager** used only for password check — na full cookie sign-in scheme confusion  
8. **Fat ApplicationUser** navigations — over-fetch risk (Login Include careful)  
9. **Identity + custom claims** — do model; Day 37 clear  
10. **Lockout minutes** az config int → TimeSpan.FromMinutes — unit document  
11. **Persian errors** — FE i18n double?  
12. **saveChanges flag** — easy to forget SaveChanges caller  

---

## Debug checklist (sade)

1. Password policy fail → IdentityResult.Errors  
2. LockedOut → AccessFailedCount / LockoutEnd  
3. DeActivated → IsActive false  
4. Invalid credentials — user null OR password  
5. Refresh fail — VerifyUserToken / token row  
6. Multi-session flag vs expected concurrent logins  
7. Blacklist after single-session login?  
8. NormalizeName/Email mismatch  
9. Site grant empty — tenant later fail  
10. Persian error text vs ErrorOr mapping  

---

## 25 soal-e mosahebe

1. ASP.NET Identity chie?  
2. Identity vs JWT?  
3. UserManager vs SignInManager?  
4. PasswordHasher chera?  
5. SecurityStamp chie?  
6. Lockout chejori?  
7. IUserConfirmation Dejban?  
8. ApplicationUser ezafe chi dare?  
9. PayamGostarUserManager chera?  
10. CustomUserStore chie?  
11. AllowMultipleSession?  
12. CheckPasswordSignInAsync vs CheckPassword?  
13. GenerateUserToken refresh?  
14. ApplicationUserToken fields?  
15. IdentitySettings → IdentityOptions?  
16. PersianIdentityErrorDescriber?  
17. CreateUser saveChanges false?  
18. IdentityDbContext generics?  
19. RoleManager?  
20. Find by phone?  
21. Cookie + JWT hardo chera?  
22. Day 06 ertebat blacklist?  
23. Tenant Sites?  
24. IsNotAllowed yani?  
25. Resume 60s?

---

## Senario-ha (ravoon)

### A) Login success

Find user → password OK → active → JWT + refresh hash store → cookies → FE.

### B) 5 bar password ghalat

LockoutOnFailure → LockedOut error → wait DefaultLockoutTimeSpan.

### C) User deactive

Password OK → IsNotAllowed → DeActivated.

### D) Second login single-session

GenerateUserToken → stamp update + blacklist previous access → session ghabli 401.

### E) Create user duplicate phone

Business check ghabl CreateAsync → DuplicatePhoneNumber.

---

## Mini lab

1. Read `ApplicationUser` / `ApplicationRole`  
2. `AddIdentity` block ServiceCollectionExtensions  
3. `UserConfirmation`  
4. LoginCommandHandler step-by-step  
5. PayamGostarUserManager GenerateUserToken override  
6. CustomUserStore SetTokenAsync multi vs single  
7. CreateUserCommandHandler CreateAsync+SaveChanges  
8. IdentitySettings in appsettings  

---

## Resume

**kutah:**

> Built IdentityServer on ASP.NET Core Identity with custom `ApplicationUser`/`ApplicationRole`, a `PayamGostarUserManager` and `CustomUserStore` for phone lookup and JWT session tokens (JTI, multi-session policy, blacklist integration), `IUserConfirmation` mapped to `IsActive`, and config-driven password/lockout via `IdentitySettings`, while issuing JWTs after `SignInManager.CheckPasswordSignInAsync`.

**bullet-ha:**

- Extended Identity entities and `IdentityDbContext` with sites, positions, custom tokens/claims  
- Wired `AddIdentity` with custom store/manager, Persian errors, and Options-bound policies  
- Implemented login/create flows combining Identity password/lockout with JWT + refresh token storage  

**skill-ha:** `ASP.NET Core Identity, UserManager, SignInManager, IdentityDbContext, Password hashing, Lockout, JWT, Session management, EF Core`

---

## File-haye mohem

| chi | koja |
|---|---|
| ApplicationUser/Role | `Domain/Entities/` |
| ApplicationUserToken | `Domain/Entities/ApplicationUserToken.cs` |
| DbContext | `Infrastructure/Persistence/ApplicationDbContext.cs` |
| AddIdentity | `Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| UserManager | `PayamGostarUserManager.cs` |
| UserStore | `CustomUserStore.cs` |
| Confirmation | `UserConfirmation.cs` |
| IdentitySettings | `BindingContracts/IdentitySettings.cs` |
| Login | `Application/Auth/Commands/Login/` |
| CreateUser | `Application/AccountManagement/Commands/CreateUser/` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 06 JWT + blacklist | token after Identity check |
| 16 Tenancy | Sites on user |
| 34 Options | IdentitySettings |
| 37 Permission claims | claims model omigh |
| 11 ErrorOr | IdentityResult map |
| 40 Auth e2e | FE login (ba'd) |

---

## Chejori digest koni

1. WORLD receptionist + Identity≠JWT (20 min)  
2. ApplicationUser/Role/DbContext (15 min)  
3. AddIdentity + Settings (15 min)  
4. Login + Confirmation + Lockout (25 min)  
5. Custom manager/store + multi-session (25 min)  
6. CreateUser lab (10 min)  
7. 25 soal (20 min)  

---

## Glossary (sade)

| kalame | ma'ni-ye yek khati |
|---|---|
| Identity | membership framework |
| UserManager | API user CRUD/password |
| SignInManager | sign-in/password/lockout |
| PasswordHasher | hash+verify |
| SecurityStamp | invalidate tokens/cookies |
| Lockout | ghofl ba'd fail ziad |
| Normalization | uppercase stable username/email |
| UserStore | persistence adapter |
| Token provider | generate/verify purpose tokens |
| IUserConfirmation | «allowed to sign in?» |
| IdentityResult | Succeeded + Errors |
| AspNet* tables | default Identity schema names (customizable) |

---

## Deep dive — CheckPasswordSignInAsync outcomes

| result | Dejban map |
|---|---|
| Succeeded | continue JWT |
| Failed | InvalidCredentials |
| IsLockedOut | LockedOut |
| IsNotAllowed | DeActivated (IsActive) |
| RequiresTwoFactor | (agar 2FA — check proje) |

---

## Deep dive — SecurityStamp

Har bar stamp avaz → Identity-generated tokens ghabli invalidate.  
Single-session login stamp update = session digar refresh hash invalid + blacklist access.  
**Chera careful?** Update stamp bi-dalil → hame logout.

---

## Deep dive — Password policy az config

`RequiredLength`, lower/upper/digit/non-alphanumeric — bind az `IdentitySettings.Password`.  
CreateUser / ChangePassword → validators Identity ejra.  
FE bayad hamin rule neshan dahad — dual source smell age sync nabashe.

---

## Anti-pattern

```csharp
// BAD: store plain password
// GOOD: UserManager.CreateAsync → PasswordHasher

// BAD: if(user.Password == input)
// GOOD: CheckPasswordSignInAsync

// BAD: think Identity cookie = API auth
// GOOD: JWT Bearer (+ optional cookies holding JWT)

// BAD: skip lockout
CheckPasswordAsync only
// GOOD: CheckPasswordSignInAsync(lockoutOnFailure: true)
```

---

## Interview 60s (ravoon)

> «IdentityServer is built on ASP.NET Core Identity. We extend IdentityUser/Role, use a custom UserManager and UserStore for phone login and refresh-session rows with JTI, and map IUserConfirmation to an IsActive flag. Password and lockout policies come from IdentitySettings into IdentityOptions. Login uses SignInManager.CheckPasswordSignInAsync, then we issue JWTs and store refresh token hashes; single-session mode updates the security stamp and blacklists the previous access token.»

---

## Quick self-test

1. Microservice? → IdentityServer  
2. User base class? → IdentityUser  
3. Custom manager? → PayamGostarUserManager  
4. Confirmation? → IsActive  
5. Login password API? → CheckPasswordSignInAsync  
6. Multi-session setting? → AllowMultipleSession  
7. Token entity extra? → Jti, AccessToken, SessionInfo  
8. Errors language? → Persian describer  
9. CreateUser Identity call? → CreateAsync + SaveChanges  
10. JWT koja? → TokenProvider ba'd Identity OK  

---

## Final checklist

- [ ] Identity vs JWT  
- [ ] AddIdentity pieces  
- [ ] User/Role/Token entities  
- [ ] Login flow  
- [ ] Manager/Store customs  
- [ ] Lockout + IsActive  
- [ ] Resume  

---

## Extra — «Identity tables» be zaban-e sade

Base: Users, Roles, UserRoles, UserClaims, RoleClaims, UserLogins, UserTokens.  
Dejban esm entity `Application*` + column ezafi; EF config assembly.  
`base.OnModelCreating` Identity schema; ba'd ApplyConfigurations.

---

## Extra — Farz kon ChangePassword

UserManager `ChangePasswordAsync` / `RemovePassword` + `AddPassword` — Identity hash update + optional stamp.  
Ba'd shayad blacklist sessions — product decision.

---

## Extra — ApiKey vs Identity password

User `ApiKeys` collection — auth path digar (machine). Hanuz User Identity parent-e.  
In ruz focus password login; ApiKey detail later/auth e2e.

---

## Extra — SignInManager role in API

FAQ: «Chera SignInManager age cookie Identity use nemikonim?»  
Javab: password+lockout+confirmation pipeline amade; cookie scheme primary nist. Legitimate.

---

## Extra — NormalizeName

`_userManager.NormalizeName(command.UserName)` — lookup case-insensitive stable.  
DB `NormalizedUserName` index. Typo normalize = user not found.

---

## Map — CreateUser

```
Validate duplicates (phone, national code)
Adapt → ApplicationUser + Sites
UserManager.CreateAsync(password, saveChanges:false)
  → validate password, hash, normalize
ActivationHistory
DbContext.SaveChanges
Return Id
```

---

## Map — Login

```
Find user (phone|user|email) + Includes
CheckPasswordSignInAsync
Branch errors
CreateAccessToken
GenerateUserToken (refresh hash) [maybe stamp+blacklist]
SetAuthenticationTokenAsync (store)
Set cookies
Return user DTO + accessToken
```

---

## Lab aha

1. Set IsActive false → login DeActivated  
2. Wrong password ×N → LockedOut  
3. AllowMultipleSession false → second login kills first (blacklist)  
4. Weak password CreateUser → IdentityErrors  

---

## What Day 36 is *not*

- Full claims/permission matrix (Day 37)  
- FE login UI (Day 40/49)  
- Duende IdentityServer / OIDC server product  
- External Google login deep  

Focus: **ASP.NET Identity engine as used in IdentityServer**.

---

## Resume keywords (ATS)

`ASP.NET Core Identity` · `UserManager` · `SignInManager` · `IdentityDbContext` · `PasswordHasher` · `Lockout` · `Custom UserStore` · `JWT` · `Session` · `EF Core`

---

## Band-e gharardad-e jadid

> **Tozihat ravoontar va sade-tar.**  

In ruz: receptionist metaphor; Identity≠JWT clear; Login dastan; Manager/Store chera; IsActive hook honest.

---

## 10 jomle fluency

1. Identity = user/password/role/lockout store.  
2. JWT = API credential ba'd az Identity OK.  
3. ApplicationUser extend IdentityUser.  
4. PayamGostarUserManager + CustomUserStore.  
5. IsActive via IUserConfirmation.  
6. CheckPasswordSignInAsync baraye lockout.  
7. IdentitySettings → IdentityOptions.  
8. AllowMultipleSession + blacklist.  
9. ApplicationUserToken ba Jti/SessionInfo.  
10. Claims omigh = Day 37.

---

## Extra — Farz kon SuperAdmin seed (boot)

DbInitializer (Day 31 Migrate+seed): SuperAdmin az `SuperAdminSettings` Options → UserManager Create age nabashe → roles/claims/sites.  
**Yani:** Identity API ham baraye seed, ham baraye runtime CreateUser.

---

## Extra — IdentityResult → ErrorOr

```csharp
if (!identityResult.Succeeded)
    return Errors.AccountManagement.IdentityErrors(identityResult.Errors);
```

Har `IdentityError.Code/Description` (Persian describer) → FE.  
Pattern: library result → domain ErrorOr (Day 11).

---

## Extra — Chera phone + username + email yek field login?

UX: user har chi yadesh biad type mikone.  
Cost: query OR se field; index va normalize mohem.  
Security: error yeksan InvalidCredentials — user enumeration kamtar (ideal; timing hanuz topic-e).

---

## Extra — ApplicationUserClaim vs ApplicationClaim

Identity built-in UserClaim table hast; Dejban ham model claim catalog (`ApplicationClaim`) + many-to-many.  
Day 37 joda mikone permission assign. Inja: bedun Identity claim store *vojud dare* va extend shode.

---

## Extra — DataProtectionTokenProviderOptions

```csharp
options.TokenLifespan = TimeSpan.FromDays(JwtSettings.SessionExpirationInDays);
```

Refresh/purpose tokens Identity ba session length align.  
Options pattern dobare (Day 34).

---

## Extra — Test zehni

- Unit UserManager sakht (store mock)  
- Integration: Testcontainers Postgres + CreateAsync + CheckPassword  
- Focus login handler ba mock UserManager/SignInManager — common

---

## Extra — Farz kon SuperAdmin seed (boot)

DbInitializer (Day 31 Migrate+seed): SuperAdmin az `SuperAdminSettings` Options → UserManager Create age nabashe → roles/claims/sites.  
**Yani:** Identity API ham baraye seed, ham baraye runtime CreateUser.

---

## Extra — IdentityResult → ErrorOr

```csharp
if (!identityResult.Succeeded)
    return Errors.AccountManagement.IdentityErrors(identityResult.Errors);
```

Har `IdentityError.Code/Description` (Persian describer) → FE.  
Pattern: library result → domain ErrorOr (Day 11).

---

## Extra — Chera phone + username + email yek field login?

UX: user har chi yadesh biad type mikone.  
Cost: query OR se field; index va normalize mohem.  
Security: error yeksan InvalidCredentials — user enumeration kamtar (ideal; timing hanuz topic-e).

---

## Extra — ApplicationUserClaim vs ApplicationClaim

Identity built-in UserClaim table hast; Dejban ham model claim catalog (`ApplicationClaim`) + many-to-many.  
Day 37 joda mikone permission assign. Inja: bedun Identity claim store *vojud dare* va extend shode.

---

## Extra — DataProtectionTokenProviderOptions

```csharp
options.TokenLifespan = TimeSpan.FromDays(JwtSettings.SessionExpirationInDays);
```

Refresh/purpose tokens Identity ba session length align.  
Options pattern dobare (Day 34).

---

## Extra — Test zehni

- Unit UserManager sakht (store mock)  
- Integration: Testcontainers Postgres + CreateAsync + CheckPassword  
- Focus login handler ba mock UserManager/SignInManager — common

---

## Khoruj-e zehni

> Midunam IdentityServer ru-ye ASP.NET Identity hast: user/role custom, manager/store extend baraye phone va session JWT, confirmation = IsActive, login ba SignInManager ba'd TokenProvider. Fargh Identity va JWT ro seda mikonam va midunam multi-session va lockout koja-st.

Age in paragraph mal-e to shod — Day 36 done.

---

*Day 36 tamum. Ba'd: Day 37 — Permission claims (amade). Fehrest: [README.md](./README.md).*
