# Day 06 — JWT Bearer + Token Blacklist

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Authentication mige "ki hasti?", authorization mige "ejaze dari?" JWT (JSON Web Token) ye token-e stateless-e ke server sign mikone va client har request baresh miferse. Vali "stateless" yani server nemitone cancel-esh kone — magar Redis blacklist dashte bashi. In fasl kole auth cycle ra yad migiri: login → token generation → cookie/header → validation → claims enrichment → refresh rotation → revocation → frontend handling.

---

# BAKHSH-E AVAL: WORLD — JWT to donya

## JWT chie?

JSON Web Token. 3 bakhsh dare ke ba `.` joda mishan:

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U
```

| bakhsh | chi | encode |
|---|---|---|
| **Header** | algorithm + type | Base64URL |
| **Payload** | claims (data) | Base64URL |
| **Signature** | HMAC ya RSA sign | Binary → Base64URL |

```json
// Header:
{ "alg": "HS256", "typ": "JWT" }

// Payload:
{
    "sub": "user-123",
    "name": "Ali",
    "iat": 1695000000,
    "exp": 1695000900
}

// Signature:
HMACSHA256(base64(header) + "." + base64(payload), secret)
```

**Important:** payload **encoded**-e, na **encrypted**! Kasi mitone decode kone va bekhone. Faghat tamper-proof-e (sign shode).

---

## Chera JWT?

### Session-based (traditional) vs Token-based (JWT)

| | Session | JWT |
|---|---|---|
| state | server-side (memory/DB) | client-side (token) |
| scale | hard (sticky session ya shared store) | easy (stateless) |
| revoke | delete session → done | token valid ta expire ⚠️ |
| CORS | same-origin default | any origin (Bearer header) |
| mobile | cookie support varies | header works everywhere |

**JWT maziat:** stateless → horizontal scale. Har server independent validate mikone bedune shared session store.

**JWT moshkel:** na mituni cancel koni ta expire nashe (magar blacklist dashte bashi).

---

## Access Token vs Refresh Token

| | Access Token | Refresh Token |
|---|---|---|
| **omr** | kootah (5-15 min) | boland (7-30 ruz) |
| **kojast** | `Authorization: Bearer ...` header ya cookie | HttpOnly cookie only |
| **chi dare** | user ID, claims, roles | session ID (jti), hash |
| **karbord** | API request auth | gereftane access token-e jadid |
| **revoke** | blacklist ya wait for expiry | delete from DB |

**Flow:**

```
Login → Access (15min) + Refresh (7day)
Request → Bearer access token
Access expired → POST /refresh (send refresh cookie)
    → New access + new refresh (rotation)
    → Continue
Refresh expired → Login again
```

---

## Symmetric vs Asymmetric signing

| | Symmetric (HMAC) | Asymmetric (RSA/ECDSA) |
|---|---|---|
| key | yek secret (shared) | private key + public key |
| sign | secret | private key |
| verify | haman secret | public key (public!) |
| use case | monolith, internal service | microservice, 3rd-party, OIDC |
| speed | fast | slower |

**Symmetric:** sade, vali hame-ye service-ha bayad secret ra dashte bashan. Age yek leak kone, hame compromised.

**Asymmetric:** sign server private key dare, verify-konande faghat public key lazem dare. Secure-tar baraye distributed. OIDC/OAuth2 default.

**Dejban:** Symmetric `HmacSha256`. Chon internal service-ha hastan va hame az yek `globalAppsettings.json` mikhonan.

---

## Cookie vs LocalStorage vs Memory

| | HttpOnly Cookie | localStorage | Memory (variable) |
|---|---|---|---|
| XSS | ✅ safe (JS access nadare) | ❌ vulnerable | ✅ safe (tab close = gone) |
| CSRF | ❌ auto-sent (need SameSite) | ✅ safe (manual attach) | ✅ safe |
| persist | bale (disk) | bale (disk) | na (tab close) |
| cross-tab | bale | bale | na |

**Best practice (2024+):**
- Access token: **memory** (safest) ya **HttpOnly cookie**
- Refresh token: **HttpOnly Secure SameSite cookie** (HAMISHE)

**Dejban:** Access to har do ja — HttpOnly cookie **va** localStorage + response body. Refresh faghat HttpOnly cookie.

---

## Token revocation strategies

JWT stateless-e → server nemitone "cancel" kone. Ama:

| strategy | chi | cost |
|---|---|---|
| **Short expiry** | 5-15 min access → beshtar safe | user refresh ziad |
| **Token blacklist** | revoked token ID ra to Redis/DB negah dar | per-request Redis check |
| **Token versioning** | user table `tokenVersion` → JWT check | DB check per request |
| **Refresh token rotation** | har refresh → old refresh invalid | detect reuse |
| **Session store** | server-side session table | DB/Redis per request |

**Best:** **blacklist + short expiry + refresh rotation**. In exactly chi-e ke Dejban dare.

---

## Claims

JWT payload = **claims**. Key-value pair-ha ke identity information daran.

### Registered claims (standard):

| claim | name | mesal |
|---|---|---|
| `sub` | subject | user ID |
| `iss` | issuer | `https://myapp.com` |
| `aud` | audience | `https://api.myapp.com` |
| `exp` | expiration | Unix timestamp |
| `iat` | issued at | Unix timestamp |
| `nbf` | not before | Unix timestamp |
| `jti` | JWT ID | unique identifier |

### Custom claims:

```json
{
    "sub": "user-123",
    "role": "admin",
    "site": "site-abc",
    "permission": "users/read"
}
```

**Mohem:** Claim ziad = token bozorg = har request header bozorg. Faghat essential claim-ha ra to JWT bezar. Baghie ra server-side enrich kon.

---

## OAuth2 / OpenID Connect (OIDC) — kholase

| | OAuth2 | OIDC |
|---|---|---|
| chi | authorization framework | authentication layer roye OAuth2 |
| baraye | "in app ejaze dare data-t ra bekhone" | "in user ki-e?" |
| token | access token | access token + **ID token** (JWT) |
| provider | Google, GitHub, Azure AD | haman-ha + any OIDC server |

**Dejban:** Custom JWT auth, na OAuth2/OIDC. Khodesh token generate mikone — na az external provider.

**Donya:** production app-ha often OIDC provider daran (Keycloak, Auth0, Azure AD). Dejban age public beshe, OIDC behtar-e.

---

## Chizaei ke to donya hastan vali inja kam/nistan

- **Asymmetric signing (RS256/ES256)** — Dejban HMAC dare
- **OAuth2 / OIDC** — Dejban custom JWT auth
- **PKCE flow** — baraye SPA/mobile OAuth. Dejban nadare
- **ID token** — OIDC concept. Dejban nadare
- **Token introspection endpoint** — RFC 7662. Server-side token validation endpoint
- **JWK endpoint (.well-known/jwks.json)** — public key endpoint. Dejban nadare
- **mTLS client certificates** — mutual TLS. Dejban nadare
- **API key + JWT hybrid** — Dejban ACLServer `PlateReaderAgentAuthFilter` API key dare, vali separate az JWT
- **Passwordless auth (WebAuthn/FIDO2)** — Dejban password-based
- **MFA (multi-factor auth)** — Dejban nadare
- **Rate limit on login per user** — Dejban per-IP dare, na per-user

---

# BAKHSH-E DOVOM: DEJBAN — JWT to in proje

## Architecture overview

```
┌──────────┐     ┌──────────────┐     ┌───────────────┐
│ Frontend  │────►│ API Gateway  │────►│IdentityServer │
│ (Next.js) │     │  (YARP)      │     │  (auth only)  │
└──────────┘     └──────┬───────┘     └───────────────┘
     │                  │
     │ Bearer header    │ TokenRevoke middleware
     │ + cookies        │ + JWT Bearer validation
     │                  ▼
     │           ┌──────────────┐     ┌───────┐
     │           │ Microservice │────►│ Redis │
     │           │ (Dejban/ACL) │     │(black │
     │           └──────────────┘     │ list) │
     │                                └───────┘
     │
     │  localStorage: accessToken
     │  cookie (HttpOnly): AccessToken + RefreshToken
```

---

## Token generation

### Access token — `TokenProvider.CreateAccessToken()`

```csharp
// File: IdentityServer/Infrastructure/Providers/TokenProvider.cs

public string CreateAccessToken(ApplicationUser user)
{
    var claims = new List<Claim>
    {
        new(ClaimTypes.NameIdentifier, user.Id)
    };

    foreach (var site in user.Sites)
        claims.Add(new Claim(CustomClaims.Site, site.Id.ToString()));

    var securityKey = new SymmetricSecurityKey(
        Encoding.UTF8.GetBytes(_jwtSettings.AccessTokenSecret));
    var credentials = new SigningCredentials(securityKey, SecurityAlgorithms.HmacSha256);

    var tokenDescriptor = new SecurityTokenDescriptor
    {
        Subject = new ClaimsIdentity(claims),
        Expires = DateTime.UtcNow.AddMinutes(_jwtSettings.ExpirationInMinutes),
        SigningCredentials = credentials,
        Issuer = _jwtSettings.Issuer,
        Audience = _jwtSettings.Audience
    };

    var handler = new JsonWebTokenHandler();
    return handler.CreateToken(tokenDescriptor);
}
```

| property | value |
|---|---|
| Algorithm | HMAC-SHA256 (symmetric) |
| Key | `JwtSettings.AccessTokenSecret` |
| Expiry | 15 minutes |
| Claims | `NameIdentifier` (user ID) + `site` (per assigned site) |
| Issuer/Audience | `https://localhost:7036` |

**Mohem:** Role, permission, position to JWT **nist**! Faghat user ID + site-ha. Baghie server-side enrich mishe (bakhsh-e claims enrichment).

### Refresh token — `TokenProvider.CreateRefreshToken()`

```csharp
public (string, string) CreateRefreshToken(string refreshTokenHash, string? jti = null)
{
    if (string.IsNullOrWhiteSpace(jti)) jti = Guid.NewGuid().ToString();
    var claims = new List<Claim>
    {
        new(JwtRegisteredClaimNames.Jti, jti),
        new(ClaimTypes.Hash, refreshTokenHash)
    };

    var securityKey = new SymmetricSecurityKey(
        Encoding.UTF8.GetBytes(_jwtSettings.RefreshTokenSecret));
    var credentials = new SigningCredentials(securityKey, SecurityAlgorithms.HmacSha256);

    var tokenDescriptor = new SecurityTokenDescriptor
    {
        Subject = new ClaimsIdentity(claims),
        Expires = DateTime.UtcNow.AddDays(_jwtSettings.SessionExpirationInDays),
        SigningCredentials = credentials,
        Issuer = _jwtSettings.Issuer,
        Audience = _jwtSettings.Audience
    };

    return (handler.CreateToken(tokenDescriptor), jti);
}
```

| property | value |
|---|---|
| Algorithm | HMAC-SHA256 |
| Key | `JwtSettings.RefreshTokenSecret` (**separate** az access!) |
| Expiry | 7 days |
| Claims | `jti` (session ID, unique per login) + `Hash` (ASP.NET Identity token hash) |

**Chera do ta secret?** Age access secret leak kone, refresh token-ha safe-an (different key). Defense in depth.

---

## JwtSettings

```csharp
// File: Common/Abstractions/BindingContracts/JwtSettings.cs

public class JwtSettings
{
    public const string SectionName = "JwtSettings";
    public string AccessTokenSecret { get; init; } = string.Empty;
    public string RefreshTokenSecret { get; init; } = string.Empty;
    public int ExpirationInMinutes { get; init; }
    public int SessionExpirationInDays { get; init; }
    public string Issuer { get; init; } = string.Empty;
    public string Audience { get; init; } = string.Empty;
}
```

```json
// File: GlobalAppsettings/globalAppsettings.json

"JwtSettings": {
    "AccessTokenSecret": "JWTAuthenticationHIGHsecuredPasswordVVVp1OH7Xzyr",
    "RefreshTokenSecret": "JWTAuthenticationHIGHsecuredPasswordVVVp1OH7Xguo",
    "ExpirationInMinutes": 15,
    "SessionExpirationInDays": 7,
    "Issuer": "https://localhost:7036",
    "Audience": "https://localhost:7036"
}
```

**Smell:** Secret-ha to `globalAppsettings.json` hastand — plaintext to repo. Production bayad environment variable ya secret manager bashe (Azure Key Vault, Docker secrets).

---

## Token validation — JWT Bearer middleware

```csharp
// File: Common/Abstractions/Extensions/ServiceCollectionExtensions.cs

services.AddAuthentication(options =>
{
    options.DefaultScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.RequireHttpsMetadata = false;
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(jwtSettings.AccessTokenSecret)),
        ValidIssuer = jwtSettings.Issuer,
        ValidAudience = jwtSettings.Audience,
        ClockSkew = TimeSpan.Zero    // no tolerance — exact expiry
    };

    options.Events = new JwtBearerEvents
    {
        OnMessageReceived = context =>
        {
            // Priority order:
            // 1. Authorization: Bearer header
            // 2. Cookie "AccessToken"
            // 3. Query string "access_token"
            // 4. Query string "AccessToken"
        }
    };
});
```

**4 ja token resolve mishe:**

| # | source | chera |
|---|---|---|
| 1 | `Authorization: Bearer` header | standard REST |
| 2 | `AccessToken` cookie | SPA with `withCredentials: true` |
| 3 | `?access_token=` query string | SignalR WebSocket negotiate |
| 4 | `?AccessToken=` query string | Stimulsoft report `window.open` |

**`ClockSkew = TimeSpan.Zero`** — default 5 minute tolerance ra hazf karde. Token exactly 15 min valid-e, na 20 min.

**`RequireHttpsMetadata = false`** — development/Docker. Production bayad `true` bashe.

---

## Login flow — step by step

```csharp
// File: IdentityServer/Application/Auth/Commands/Login/LoginCommandHandler.cs

public async Task<ErrorOr<object>> Handle(LoginCommand command, CancellationToken ct)
{
    // 1. Find user (phone/username/email)
    var user = await FindUserByCredential(command.UserName);
    if (user == null) return AuthErrors.UserNotFound;

    // 2. Check password (with lockout)
    var result = await _signInManager.CheckPasswordSignInAsync(user, command.Password, lockoutOnFailure: true);
    if (!result.Succeeded) return AuthErrors.IncorrectPassword;
    if (result.IsLockedOut) return AuthErrors.LockedOut;

    // 3. Create access token (15 min)
    var accessToken = _tokenProvider.CreateAccessToken(user);

    // 4. Create refresh token hash (ASP.NET Identity)
    var refreshTokenHash = await _userManager.GenerateUserTokenAsync(
        user, TokenOptions.DefaultProvider, ConfigConstants.RefreshToken);

    // 5. Create refresh JWT (7 day) with jti
    var (refreshToken, jti) = _tokenProvider.CreateRefreshToken(refreshTokenHash);

    // 6. Store session in DB (AspNetUserTokens)
    await _userManager.SetAuthenticationTokenAsync(
        user, jti, accessToken,
        TokenOptions.DefaultProvider, ConfigConstants.RefreshToken,
        refreshTokenHash, _clientInfo.GetSessionInfo());

    // 7. Set HttpOnly cookies
    _accessor.HttpContext!.Response.Cookies.Append(
        ConfigConstants.AccessToken, accessToken, new CookieOptions
        {
            IsEssential = true,
            HttpOnly = true,
            Secure = true,
            SameSite = SameSiteMode.None,
            MaxAge = TimeSpan.FromDays(_jwtSettings.SessionExpirationInDays),
            Expires = DateTime.UtcNow.AddDays(_jwtSettings.SessionExpirationInDays)
        });

    _accessor.HttpContext!.Response.Cookies.Append(
        ConfigConstants.RefreshToken, refreshToken, /* same options */);

    // 8. Return token in body too (for localStorage)
    return new { user = new { ... }, accessToken };
}
```

### Cookie settings

| option | value | chera |
|---|---|---|
| `HttpOnly` | `true` | JS access nadare → XSS safe |
| `Secure` | `true` | faghat HTTPS ersal mishe |
| `SameSite` | `None` | cross-origin SPA (different port/domain) |
| `MaxAge` | 7 days | align ba refresh token expiry |
| `IsEssential` | `true` | GDPR cookie consent skip |

**SameSite=None + Secure=true** → cross-origin cookie. Lazem chon frontend (`localhost:3000`) va backend (`localhost:7036`) port-eshun fargh dare.

### Dual storage (cookie + body)

| token | cookie | response body | frontend storage |
|---|---|---|---|
| Access | ✅ `AccessToken` (HttpOnly) | ✅ `accessToken` field | localStorage |
| Refresh | ✅ `RefreshToken` (HttpOnly) | ❌ | browser cookie only |

**Chera dual?** Cookie baraye auto-send (CORS `withCredentials`). Body/localStorage baraye explicit `Authorization: Bearer` header. Redundant vali backward compatible.

---

## Refresh flow

```csharp
// File: IdentityServer/Application/Auth/Commands/Refresh/RefreshCommandHandler.cs

public async Task<ErrorOr<object>> Handle(RefreshCommand command, CancellationToken ct)
{
    // 1. Read tokens from cookies/headers
    var accessToken = _accessor.HttpContext!.GetAccessToken();
    var refreshToken = _accessor.HttpContext!.GetRefreshToken();

    // 2. Validate EXPIRED access token (lifetime ignored)
    var accessPrincipal = await _tokenProvider
        .GetClaimsPrincipalFromExpiredAccessTokenAsync(accessToken);
    //                        ^^^ ValidateLifetime = false

    // 3. Validate refresh token
    var refreshPrincipal = await _tokenProvider
        .GetClaimsPrincipalFromRefreshTokenAsync(refreshToken);

    // 4. Extract jti + hash from refresh claims
    var jti = refreshPrincipal.FindFirst(JwtRegisteredClaimNames.Jti)!.Value;
    var hash = refreshPrincipal.FindFirst(ClaimTypes.Hash)!.Value;

    // 5. Verify hash against DB (ASP.NET Identity store)
    var isValid = await _userManager.VerifyUserTokenAsync(
        user, TokenOptions.DefaultProvider, ConfigConstants.RefreshToken, hash);

    // 6. Rotate: new access + new refresh, SAME jti
    var newAccessToken = _tokenProvider.CreateAccessToken(user);
    var newRefreshHash = await _userManager.GenerateUserTokenAsync(...);
    var (newRefreshToken, _) = _tokenProvider.CreateRefreshToken(newRefreshHash, jti);
    //                                                                          ^^^ reuse jti

    // 7. Update DB session record
    await _userManager.SetAuthenticationTokenAsync(
        user, jti, newAccessToken, ...);

    // 8. Set new cookies + return new access token
    Response.Cookies.Append(ConfigConstants.AccessToken, newAccessToken, ...);
    Response.Cookies.Append(ConfigConstants.RefreshToken, newRefreshToken, ...);
    return new { accessToken = newAccessToken };
}
```

**Key points:**

- `ValidateLifetime = false` baraye expired access token → chon refresh vaghti access expire shode seda mishe
- **Same `jti`** → session identity hefz mishe. Session row update mishe, delete/recreate nist
- **Refresh rotation** → old refresh hash invalid mishe (new hash generate), old refresh JWT natone dobare estefade beshe
- **Hash verification** → ASP.NET Identity `VerifyUserTokenAsync` → DB check. Fake refresh token = fail

---

## Token blacklist — Redis

### Interface + Implementation

```csharp
// File: Common/Caching/ITokenBlackList.cs

public interface ITokenBlackList
{
    Task<bool> IsRevokedAsync(string key);
    Task<bool> RevokeAsync(string key);
    Task<bool> RevokeAsync(string key, TimeSpan expireAfter);
    Task<bool> DeleteAsync(string key);
}
```

```csharp
// File: Common/Caching/TokenBlackListService.cs

// Key: "revoked:{fullAccessTokenJWT}"
// Value: true
// TTL: 15 min (matches access token expiry)

public async Task<bool> RevokeAsync(string key, TimeSpan expireAfter)
{
    await cache.SetAsync(GetCacheKey(key), true, new HybridCacheEntryOptions
    {
        Expiration = expireAfter,
        Flags = HybridCacheEntryFlags.DisableLocalCache  // always Redis, no L1
    });
    return true;
}

public async Task<bool> IsRevokedAsync(string key)
{
    try {
        return await cache.GetOrCreateAsync(GetCacheKey(key), ...);
    } catch {
        return false;  // Redis down → fail-open (allow request)
    }
}
```

**`DisableLocalCache`** — token revocation bayad hamishe Redis check beshe, na in-memory L1. Chon multi-instance age L1 cache kone, ye instance revoke mikone vali baghie L1-eshun stale-e.

**Fail-open** — Redis down → `IsRevokedAsync` returns `false` → request allowed. Trade-off: availability > security. Age security > availability mikhay → fail-closed (return `true`).

### Middleware — ghabl az auth

```csharp
// File: Common/Caching/TokenRevokeMiddleware.cs

public async Task InvokeAsync(HttpContext context, RequestDelegate next)
{
    var token = tokenSelector(context);
    if (token == null) { await next(context); return; }      // anonymous → pass

    if (!await tokenBlackList.IsRevokedAsync(token))
    {
        await next(context); return;                          // not revoked → pass
    }

    context.Response.StatusCode = 401;                        // revoked → block
}
```

Pipeline: `TokenRevoke → Authentication → Authorization`. Age revoked bashe, authentication aslan run **nemishe**.

### Chera kole token key-e (na jti)?

Access token `jti` claim **nadare** to Dejban! Faghat refresh token `jti` dare. Pas baraye blacklist, **kole access token string** key-e.

**Trade-off:** key bozorg-e (~800 char JWT), vali exact match-e. `jti` kuchik-tar bud vali bayad to JWT ezafe mishod.

---

## 14 revocation trigger

| # | trigger | chi revoke mishe | file |
|---|---|---|---|
| 1 | **Logout** | current access token + delete session | `Auth/Commands/Logout/` |
| 2 | **Terminate session** | target session's access token | `Auth/Commands/TerminateSession/` |
| 3 | **Terminate other sessions** | all other sessions' tokens | `Auth/Commands/TerminateOtherSessions/` |
| 4 | **Assign roles** | all user's tokens | `AccountManagement/AssignRolesToUser/` |
| 5 | **Assign positions** | all user's tokens | `AccountManagement/AssignPositionsToUser/` |
| 6 | **Assign claims** | all user's tokens | `AccountManagement/AssignClaimsToUser/` |
| 7 | **Exclude claims** | all user's tokens | `AccountManagement/ExcludeUserClaims/` |
| 8 | **Grant sites** | all user's tokens | `AccountManagement/GrantSitesToUsers/` |
| 9 | **Update user** | all user's tokens | `AccountManagement/UpdateUser/` |
| 10 | **Change username/password (admin)** | all user's tokens | `AccountManagement/ChangeUserNamePassword/` |
| 11 | **Delete users** | all deleted users' tokens | `AccountManagement/DeleteUsers/` |
| 12 | **Deactivate user** | all user's tokens | `AccountManagement/UserActivation/` |
| 13 | **Single-session login** | previous session's token | `PayamGostarUserManager` |
| 14 | **Invalid refresh** | session removed from DB | `Auth/Commands/Refresh/` |

**Common pattern:**

```csharp
// Har handler:
foreach (var userToken in user.UserTokens)
    await jwtBlackList.RevokeAsync(userToken.AccessToken);
```

**Gap:** Self-service `ChangePassword` token revoke **nakarde**! Faghat admin `ChangeUserNamePassword` revoke mikone. Bug ya conscious choice?

---

## Claims enrichment — CustomClaimsTransformation

JWT faghat `userId` + `sites` dare. Role, permission, position, endpoint claim-ha kojast?

```csharp
// File: Common/Authorization/CustomClaimsTransformation.cs
// Registered: services.AddTransient<IClaimsTransformation, CustomClaimsTransformation>();

// Har request ba'd az JWT validation:
// 1. IClaimService.GetUserClaims(userId) → DB ya cache
// 2. Add claims to ClaimsPrincipal:

// site       → "site-guid"
// position   → "siteId|positionName"
// role       → "siteId|roleName"
// permission → "siteId|permissionValue"
// endpoint   → "siteId|endpointPath"
```

**Chera to JWT nist?**
1. Token size: 50 permission = 50 claim = ~5KB JWT = har request 5KB header
2. Freshness: role change → JWT update lazem (reissue ya blacklist). Server-side → instant
3. Security: less info in client-side token = less exposure

**Trade-off:** har request ye Redis/DB call baraye claim enrichment. Cache khoob bashe → O(1) Redis. Cache miss → DB query.

**Claim format:** `{siteId}|{value}` → site-scoped permission. Evaluation:

```csharp
// File: Common/Authorization/SiteScopedPermissionEvaluator.cs
// "siteA|users/read" → Dictionary<Guid, HashSet<string>>
// Check: user has "users/read" for requested site?
```

---

## Session management

### Entity — ApplicationUserToken

```csharp
// File: IdentityServer/Domain/Entities/ApplicationUserToken.cs

public class ApplicationUserToken : IdentityUserToken<string>
{
    public string Jti { get; set; } = null!;        // session ID (PK)
    public DateTime LoginDate { get; set; }
    public string AccessToken { get; set; } = null!; // current access JWT copy
    public SessionInfo SessionInfo { get; set; } = null!;
}

public class SessionInfo
{
    public string IpAddress { get; set; }
    public string Device { get; set; }
    public string ClientName { get; set; }
    public string ClientType { get; set; }
    public string ClientVersion { get; set; }
    public string OsName { get; set; }
    public string OsVersion { get; set; }
    public string OsArchitecture { get; set; }
    public bool IsBot { get; set; }
}
```

Har login → ye row → ye session. User mitone list bekhone, terminate kone.

### Multi-session support

```json
// File: IdentityServer/appsettings.json
"IdentitySettings": {
    "AllowMultipleSession": true
}
```

- `true` (default): har device/login ye row, hamzaman faal
- `false`: single session, login-e jadid → ghadimi blacklist mishe

```csharp
// File: IdentityServer/Abstractions/Extensions/PayamGostarUserManager.cs

if (!_identitySettings.AllowMultipleSession)
{
    var lastSession = user.UserTokens.OrderBy(ut => ut.LoginDate).LastOrDefault();
    if (lastSession != null)
        await _jwtBlackList.RevokeAsync(lastSession.AccessToken);
}
```

### Session APIs

| endpoint | chi |
|---|---|
| `GET /auth/getmysessions` | list sessions ba `IsCurrentSession` flag |
| `DELETE /auth/terminatesession/{jti}` | terminate yek session |
| `POST /auth/terminateothersessions` | terminate hame joz current |

---

## Frontend auth handling

### Token storage

```typescript
// File: dejban_frontend_new/packages/api-client/src/tokenStorage.ts

export const STORAGE_KEY = 'jwt_access_token';

export const tokenStorage = {
    getAccess: () => localStorage.getItem(STORAGE_KEY),
    setAccess: (t: string) => localStorage.setItem(STORAGE_KEY, t),
    clear: () => localStorage.removeItem(STORAGE_KEY),
};
```

### Axios interceptors

```typescript
// File: dejban_frontend_new/packages/api-client/src/axiosInstance.ts

const client = axios.create({
    baseURL,
    withCredentials: true,  // send cookies cross-origin
});

// REQUEST interceptor — attach Bearer token
client.interceptors.request.use((config) => {
    const isRefreshRequest = config.url === endpoints.auth.refresh;
    if (!isRefreshRequest) {
        const accessToken = tokenStorage.getAccess();
        if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
});

// RESPONSE interceptor — handle 401
client.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            // POST /auth/refresh — cookie auto-sent
            const { data } = await client.post(endpoints.auth.refresh);
            tokenStorage.setAccess(data.accessToken);

            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${data.accessToken}`;
            return client(originalRequest);
        }

        // Refresh failed (401/403/404) → logout
        if (isRefreshFailure) {
            tokenStorage.clear();
            redirectToSignIn();
        }
    }
);
```

**Flow:**
1. Request → 401 (access expired)
2. POST `/auth/refresh` (cookie auto-sent, no Bearer)
3. Server validates expired access + valid refresh → new tokens
4. `tokenStorage.setAccess(newToken)` + cookies updated
5. Retry original request ba new token
6. Age refresh ham fail → logout → redirect

### Login action

```javascript
// File: dejban_frontend_new/packages/ui/src/auth/context/jwt/action.js

export const signInWithPassword = async ({ username, password }) => {
    const { data } = await apiClient.post(endpoints.auth.login, { username, password });
    const { accessToken, user } = data;
    if (accessToken) tokenStorage.setAccess(accessToken);
    return user;
};
```

### Cross-tab sync

```typescript
// File: dejban_frontend_new/packages/auth/src/AuthContext.tsx

// Listen for localStorage change in other tabs
window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY) {
        // Token changed in another tab → sync
    }
});
```

### SignalR auth

```javascript
// File: dejban_frontend_new/apps/dejban/src/sections/cartable/tickets/use-ticket-hub.js

const connection = new HubConnectionBuilder()
    .withUrl(hubUrl, {
        accessTokenFactory: () => tokenStorage.getAccess() || '',
    })
    .withAutomaticReconnect()
    .build();
```

SignalR `accessTokenFactory` → token as `?access_token=` query param → backend `OnMessageReceived` → JWT validation.

---

## Kole flow — az login ta revoke

```
USER                    FRONTEND                 GATEWAY              IDENTITY SERVER         REDIS
 │                         │                        │                       │                    │
 │  username/password      │                        │                       │                    │
 ├────────────────────────►│  POST /auth/login       │                       │                    │
 │                         ├───────────────────────►│ ──────────────────────►│                    │
 │                         │                        │                       │ check password     │
 │                         │                        │                       │ create access JWT  │
 │                         │                        │                       │ create refresh JWT │
 │                         │                        │                       │ store session (DB) │
 │                         │  accessToken + cookies  │                       │                    │
 │                         │◄───────────────────────┤◄──────────────────────┤                    │
 │                         │  localStorage.set()     │                       │                    │
 │                         │                        │                       │                    │
 │  click something        │                        │                       │                    │
 ├────────────────────────►│  GET /api/visitors      │                       │                    │
 │                         │  Bearer: accessToken    │                       │                    │
 │                         ├───────────────────────►│                       │                    │
 │                         │                        │ TokenRevoke check ────┼───────────────────►│
 │                         │                        │                       │   IsRevoked? false  │
 │                         │                        │◄──────────────────────┼────────────────────┤
 │                         │                        │ JWT validate          │                    │
 │                         │                        │ Claims enrich         │                    │
 │                         │                        │ → Dejban.Api          │                    │
 │                         │◄───────────────────────┤                       │                    │
 │                         │                        │                       │                    │
 │  (15 min later)         │                        │                       │                    │
 ├────────────────────────►│  GET /api/visitors      │                       │                    │
 │                         │  Bearer: accessToken    │                       │                    │
 │                         ├───────────────────────►│                       │                    │
 │                         │                        │ JWT validate → 401    │                    │
 │                         │  401 ──────────────────┤                       │                    │
 │                         │  POST /auth/refresh     │                       │                    │
 │                         │  (cookie auto-sent)     │                       │                    │
 │                         ├───────────────────────►│──────────────────────►│                    │
 │                         │                        │                       │ verify refresh     │
 │                         │                        │                       │ rotate tokens      │
 │                         │  new accessToken        │                       │                    │
 │                         │◄───────────────────────┤◄──────────────────────┤                    │
 │                         │  retry GET /api/visitors │                       │                    │
 │                         │  Bearer: newAccessToken  │                       │                    │
 │                         ├───────────────────────►│ validate → OK         │                    │
 │                         │                        │                       │                    │
 │  admin changes my role  │                        │                       │                    │
 │                         │                        │                       │ foreach userToken   │
 │                         │                        │                       │   blacklist.Revoke()│
 │                         │                        │                       │──────────────────►│
 │                         │                        │                       │                  set│
 │                         │                        │                       │                    │
 │  next request           │                        │                       │                    │
 ├────────────────────────►│  GET /api/visitors      │                       │                    │
 │                         ├───────────────────────►│ TokenRevoke check ────┼───────────────────►│
 │                         │                        │                       │   IsRevoked? TRUE   │
 │                         │◄───────────────────────┤ 401 ←────────────────┼────────────────────┤
 │                         │  refresh → new tokens   │                       │                    │
```

---

## Smell-ha

1. **Secret plaintext to repo** — `globalAppsettings.json` ba secret. Bayad env variable/secret manager
2. **Dejban.Api `UseTokenRevoke()` nadare** — direct call = revoked token ghabul mishe
3. **Self-service ChangePassword token revoke nakarde** — password avaz, old token hanooz valid
4. **Access token dual storage (cookie + localStorage)** — localStorage XSS-vulnerable
5. **Fail-open blacklist** — Redis down → revoked tokens pass. Security risk
6. **Na `jti` to access token** — kole JWT string key-e blacklist. Large key, na efficient
7. **Cookie `SameSite=None`** — lazem baraye cross-origin vali CSRF risk bedune additional protection
8. **`RequireHttpsMetadata = false`** — development ok, production risk
9. **Na MFA** — single-factor password only
10. **Na rate limit per user on login** — per-IP hast, per-user nist. Distributed attack from many IPs
11. **Role template change → faghat cache invalidate, na token revoke** — 15 min window ke old permissions valid
12. **Cookie MaxAge 7 days baraye access token cookie** — access 15 min-e vali cookie 7 ruz zende-st. Browser old access cookie miferse, server 401 mide, refresh fix mikone. Na optimal

---

## 20 soal-e mosahebe

1. **JWT chie? 3 bakhsh-esh?** — Header, Payload, Signature. Base64 encoded, signed, na encrypted
2. **JWT ro mituni cancel koni?** — Na. Stateless. Magar blacklist (Redis) ya kootah expiry
3. **Access vs Refresh?** — Access: kootah, har request. Refresh: boland, gereftane access-e jadid
4. **Chera 2 ta token?** — Access leak → 15 min damage. Refresh HttpOnly → XSS safe
5. **Token refresh chejori?** — Expired access + valid refresh → server validates → new pair
6. **Chera refresh rotation?** — Old refresh invalid. Stolen refresh = yek bar estefade → detect reuse
7. **Symmetric vs Asymmetric?** — HMAC: yek secret, fast. RSA: keypair, verify public. Distributed = RSA
8. **Claims chie?** — Key-value to JWT payload. sub, role, permission
9. **Chera role to JWT nist?** — Size + freshness. Role change → instant server-side, na JWT reissue
10. **ClaimsTransformation?** — Per-request enrichment. JWT claims + DB/cache claims → full identity
11. **Token blacklist?** — Redis key = token, TTL = expiry. Check per request ghabl az auth
12. **HttpOnly cookie chie?** — JS access nadare. XSS safe. `document.cookie` nemibine
13. **SameSite chie?** — Lax: same-site only. Strict: na cross-site. None: har ja (+ Secure)
14. **CSRF chie? Chejori?** — Cross-site request forgery. Cookie auto-sent. Fix: SameSite, CSRF token
15. **XSS chie? JWT?** — Cross-site scripting. localStorage token steal. Fix: HttpOnly cookie, CSP
16. **OAuth2 vs custom JWT?** — OAuth2: delegated auth, standard. Custom: simpler, less interop
17. **ClockSkew chie?** — Server time difference tolerance. Zero = strict. 5min = default
18. **Chejori multi-device handle mikoni?** — Session per device (jti). Allow/deny config
19. **SignalR chejori auth mishe?** — `accessTokenFactory` → `?access_token=` query → `OnMessageReceived`
20. **Kole auth flow ra describe kon** — Login → JWT pair → Bearer/cookie → TokenRevoke check → JWT validate → Claims enrich → authorize → 401 → refresh → retry

---

## Resume

**short:**

> Implemented JWT Bearer authentication with dual-key HMAC signing, Redis-backed token blacklist for immediate revocation, HttpOnly cookie + refresh token rotation, and server-side claims enrichment — supporting multi-session management across 8 microservices.

**bullets:**

- Built JWT auth with separate signing keys for access (15min) and refresh (7day) tokens, validated via `TokenValidationParameters` with zero clock skew
- Implemented Redis token blacklist (`HybridCache`) checked pre-authentication via custom `IMiddleware`, with 14 revocation triggers (logout, role change, session terminate, user deactivation)
- Designed refresh token rotation flow: expired access + valid refresh → new pair with same session identity (`jti`), stored in `AspNetUserTokens`
- Created claims enrichment pipeline via `IClaimsTransformation` — site-scoped roles, permissions, positions resolved from cache/DB per request
- Built frontend auth cycle: Axios interceptors for automatic 401 → refresh → retry, cross-tab token sync, SignalR `accessTokenFactory`

**skills:** `JWT, OAuth2 concepts, Token Blacklist, Redis, Refresh Token Rotation, ASP.NET Core Authentication, Claims-Based Authorization, Cookie Security, XSS/CSRF Prevention, SignalR Auth`

---

## File-haye mohem

| chi | koja |
|---|---|
| Token generation | `IdentityServer/Infrastructure/Providers/TokenProvider.cs` |
| JwtSettings class | `Common/Abstractions/BindingContracts/JwtSettings.cs` |
| JWT Bearer config | `Common/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| Login handler | `IdentityServer/Application/Auth/Commands/Login/LoginCommandHandler.cs` |
| Refresh handler | `IdentityServer/Application/Auth/Commands/Refresh/RefreshCommandHandler.cs` |
| Logout handler | `IdentityServer/Application/Auth/Commands/Logout/LogoutCommandHandler.cs` |
| Token blacklist service | `Common/Caching/TokenBlackListService.cs` |
| Token blacklist interface | `Common/Caching/ITokenBlackList.cs` |
| Token revoke middleware | `Common/Caching/TokenRevokeMiddleware.cs` |
| Claims transformation | `Common/Authorization/CustomClaimsTransformation.cs` |
| Custom claims constants | `Common/Authentication/CustomClaims.cs` |
| Session entity | `IdentityServer/Domain/Entities/ApplicationUserToken.cs` |
| Multi-session logic | `IdentityServer/Abstractions/Extensions/PayamGostarUserManager.cs` |
| AccessToken query middleware | `Common/Authentication/AccessTokenQueryMiddleware.cs` |
| GetAccessToken helper | `Common/Abstractions/Extensions/HttpContextAccessorExtensions.cs` |
| Config constants | `Common/Abstractions/Constants/ConfigConstants.cs` |
| JWT settings JSON | `GlobalAppsettings/globalAppsettings.json` |
| Frontend token storage | `dejban_frontend_new/packages/api-client/src/tokenStorage.ts` |
| Axios interceptors | `dejban_frontend_new/packages/api-client/src/axiosInstance.ts` |
| Login action | `dejban_frontend_new/packages/ui/src/auth/context/jwt/action.js` |
| Auth context | `dejban_frontend_new/packages/auth/src/AuthContext.tsx` |
| SignalR auth | `dejban_frontend_new/apps/dejban/src/sections/cartable/tickets/use-ticket-hub.js` |
| Terminate session | `IdentityServer/Application/Auth/Commands/TerminateSession/` |
| Role assign + revoke | `IdentityServer/Application/AccountManagement/Commands/AssignRolesToUser/` |
| Permission evaluator | `Common/Authorization/SiteScopedPermissionEvaluator.cs` |

---

Day 06 tamum. Ba'd: Day 07 — YARP Reverse Proxy. Fehrest: [README.md](./README.md).
