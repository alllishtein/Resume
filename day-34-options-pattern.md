# Day 34 — Options pattern

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Options pattern** yani: setting-haye app (JWT, Storage, Outbox interval, gRPC address, …) az `appsettings` / env / GlobalAppsettings miand, be ye **class-e typed** bind mishan, va ba `IOptions<T>` (ya Monitor/Snapshot) inject mishan — na `configuration["JwtSettings:Issuer"]` harja.

To Dejban in olgu *hamjahast*:

1. **POCO + `SectionName`** — mesal `JwtSettings`, `ACLSettings`, `StorageOptions`, `MediaMTXSettings`  
2. **Register** — `services.Configure<T>(section)` ya `AddOptions<T>().BindConfiguration(...)`  
3. **Consume** — `IOptions<T>.Value` to handler / job / HttpClient / gRPC wrapper  
4. **Pattern-e ziba:** `IConfigureOptions<QuartzOptions>` az `IOptions<OutboxOptions>` mikhone ta Quartz interval = config Outbox  

Kamtar didim: `IOptionsMonitor` / `ValidateOnStart` — gap-e possible baraye mosahebe.

**Band-e gharardad-e jadid:** tozihat ravoontar va sade-tar — bishtar «farz kon / yani chi / chera».

---

# BAKHSH-E AVAL: WORLD — Options chie?

## Farz kon — remote TV

Bedune Options: har bar ke channel avaz mikoni, miravi posht TV cable avaz mikoni.  
Ba Options: remote dare — setting yekja, dastgah mikhone.

Software:

```
appsettings.json  →  JwtSettings class  →  IOptions<JwtSettings>  →  LoginHandler
```

**Yani chi?** Configuration *string dictionary* mimune; code ba *object-e typed* harf mizane. Typo kam, IntelliSense, test asun-tar.

---

## Chera `configuration["key"]` bad-e to business code?

| raw config | Options |
|---|---|
| magic string harja | SectionName yekja |
| type = string hamishe | int/bool/enum typed |
| test sakht | mock `IOptions` |
| typo runtime | compile + bind |

Raw `IConfiguration` baraye *bootstrap* OK (connection string avvali). Baraye *business setting* → Options.

---

## Se interface — farq-e sade

| interface | lifetime-e Value | reload? | ki estefade? |
|---|---|---|---|
| **`IOptions<T>`** | singleton — ye bar bind (mamulan) | na (classic) | aksar Dejban |
| **`IOptionsSnapshot<T>`** | scoped — per request | bale (request jadid) | web request settings |
| **`IOptionsMonitor<T>`** | live + `OnChange` | bale | long-running / hot reload |

**Farz kon:** Outbox `IntervalInSeconds` az 5 → 2 to appsettings, app *bedune restart*.  
Ba `IOptions`: job hanuz 5 mibine (ta restart).  
Ba `IOptionsMonitor`: mitune OnChange → reschedule (code ezafi).

Dejban bishtar **`IOptions<T>`** — restart = config jadid. Honest begu.

---

## Register — do style-e mamul

```csharp
// Style A — classic
services.Configure<JwtSettings>(configuration.GetSection(JwtSettings.SectionName));

// Style B — Options builder
services.AddOptions<StorageOptions>()
    .BindConfiguration(StorageOptions.SectionName);
```

**Yani chi?** Har do be `IOptions<T>` mirasanand. B: chain `.Validate...` / `.ValidateOnStart()` asun-tar.

Dejban **har do** ro dare: Jwt/Outbox → `Configure`; Scalar/Rabbit/MediaMTX/gRPC → `AddOptions().BindConfiguration`.

---

## Validation (WORLD ideal)

```csharp
services.AddOptions<JwtSettings>()
    .BindConfiguration("JwtSettings")
    .ValidateDataAnnotations()
    .Validate(j => j.ExpirationInMinutes > 0, "Expiration must be > 0")
    .ValidateOnStart();
```

**Chera ValidateOnStart?**  
Fail *boot* — na 2 sa'at ba'd avvalin Login.  
Dejban kamtar ino dare; Jwt bootstrap ba `Get<T>() ?? throw` nazdik-e hamin fekr-e.

---

## Named options (pishrafte)

`IOptionsSnapshot<T>.Get("name")` — chand instance az yek type.  
Dejban kam estefade; Outbox per-module ba **section path joda** (`Personnels:Outbox`) + type `OutboxOptions` per namespace — na named options classic.

---

# BAKHSH-E DOVOM: DEJBAN — koja Options hast?

## Naqshe-ye sade

| domain | class | bind | consume |
|---|---|---|---|
| JWT | `JwtSettings` | `Configure` Common | Login/Refresh `IOptions` + JwtBearer setup |
| Identity | `IdentitySettings` | `Configure` | UserManager / store |
| ACL | `ACLSettings` | `AddOptions.BindConfiguration` | handlers, Iclock, sync |
| Storage/MinIO | `StorageOptions` | Options | `S3FileStorage`, presign |
| MediaMTX | `MediaMTXSettings` | `AddOptions.Bind` | `MediaMTXHttpClient` |
| gRPC clients | `ZK/Tiam/VirdiGrpcClientSettings` | Bind | wrappers |
| Outbox/Inbox | `OutboxOptions` / `InboxOptions` | `Configure(section per module)` | Quartz `IConfigureOptions` + jobs |
| Scalar | `ScalarOptions` | Bind `"Scalar"` | Day 33 |
| Rabbit | `RabbitMqTransportOptions` | Bind | MassTransit host |

---

## Qesmat 1 — POCO ba `SectionName` (olgu)

```csharp
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

**Yani chi?**  
- `const SectionName` = yek haqiqat baraye GetSection/Bind — typo kam  
- `init` = bind ba'd mutability kam (immutability-ish)  
- Default `string.Empty` = null-ref kamtar hangam bind naqes  

`ACLSettings`, `MediaMTXSettings`, … hamin dasturan.

---

## Qesmat 2 — Jwt: Configure + Get (bootstrap)

```csharp
var jwtSettingsSection = configuration.GetSection(JwtSettings.SectionName);
services.Configure<JwtSettings>(jwtSettingsSection);
var jwtSettings = jwtSettingsSection.Get<JwtSettings>()
    ?? throw new ArgumentNullException(...);

// ba'd TokenValidationParameters az jwtSettings.Issuer / Secret / …
```

**Chera hardo Configure va Get?**  

- `Configure` → ba'dan `IOptions<JwtSettings>` to Login/Refresh  
- `Get` *alan* → JwtBearer options *hengam DI build* niaz be value dare (nemishe faghat IOptions toseh `AddJwtBearer` bedune resolve)

**Farz kon:** section khali → throw boot. Behtar az 401-haye gij.

GlobalAppsettings (`JwtSettings`) + per-env overlay — Day 00/06.

---

## Qesmat 3 — OutboxOptions + Quartz (ghashang-tarin mesal)

Har module:

```csharp
// PersonnelsModule
services.Configure<OutboxOptions>(configuration.GetSection("Personnels:Outbox"));
services.Configure<InboxOptions>(configuration.GetSection("Personnels:Inbox"));
```

JSON (`modules.personnels.json` style):

```json
{
  "Personnels": {
    "Outbox": { "IntervalInSeconds": 5, "BatchSize": 50 },
    "Inbox":  { "IntervalInSeconds": 5, "BatchSize": 50 }
  }
}
```

POCO:

```csharp
internal sealed class OutboxOptions
{
    public int IntervalInSeconds { get; init; }
    public int BatchSize { get; init; }
}
```

### IConfigureOptions — Options roye Options

```csharp
internal sealed class ConfigureProcessOutboxJob(IOptions<OutboxOptions> outboxOptions)
    : IConfigureOptions<QuartzOptions>
{
    public void Configure(QuartzOptions options)
    {
        options
            .AddJob<ProcessOutboxJob>(...)
            .AddTrigger(... WithIntervalInSeconds(outboxOptions.Value.IntervalInSeconds) ...);
    }
}
```

**Yani chi be zaban-e adam?**  
To nemikhay interval Quartz hardcode 5. Config mige 5. Class-e `ConfigureProcessOutboxJob` *tarjome* mikone: OutboxOptions → Quartz trigger.  
Job khodesh `IOptions<OutboxOptions>` baraye **BatchSize** mikhone.

**Chera in pattern mohem-e mosahebe?**  
Neshun mide Options faghat «DTO config» nist — mitune *system digar* (Quartz) ro configure kone.

Day 21/29: Outbox + Quartz — inja zaviye-ye Options.

---

## Qesmat 4 — StorageOptions (nested)

```csharp
public sealed class StorageOptions
{
    public const string SectionName = "Storage";
    public string Provider { get; set; } = StorageProviders.Local;
    public string? RootPath { get; set; }
    public S3StorageOptions S3 { get; set; } = new();
}
```

`S3` nested: Endpoint, keys, Bucket, ForcePathStyle, PresignTtlSeconds, **PublicEndpoint** (Day 28).

**Yani chi?** Bind hierarchical JSON:

```json
"Storage": {
  "Provider": "S3",
  "S3": { "Endpoint": "...", "PublicEndpoint": "..." }
}
```

`IOptions<StorageOptions>` → `S3FileStorage` / presign handler. Yek inject, nested property.

---

## Qesmat 5 — ACL + gRPC settings

```csharp
services.AddOptions<ACLSettings>().BindConfiguration(ACLSettings.SectionName);
services.AddOptions<ZKGrpcClientSettings>().BindConfiguration(...);
// Tiam, Virdi, DeviceGrpcServices, VehicleAccessOptions, …
```

Consume: `IOptions<ACLSettings>` to CreateACLUser, RealtimeAccessLog, IclockController, device sync strategies.  
`IOptions<ZKGrpcClientSettings>` to `ZKGrpcClientWrapper` — address/channel az config.

**Farz kon:** ServerIP / EncryptionKey ACL az appsettings — code hardcode nadare.

---

## Qesmat 6 — MediaMTX

```csharp
services.AddOptions<MediaMTXSettings>().BindConfiguration(MediaMTXSettings.SectionName);
services.AddHttpClient<MediaMTXHttpClient>();
// ctor: IOptions<MediaMTXSettings>
```

BaseUrl / User / Password / CameraDefaults — Options.  
(Http resilience = Day 32 gap; Options = in ruz.)

---

## Qesmat 7 — Get\<T\> bedune IOptions (jayez?)

Ja-haye bootstrap:

- SuperAdmin seed: `configuration.GetSection(...).Get<SuperAdminSettings>()`  
- Reporting gateway options yekbar  
- Migrate script Storage  

**Yani chi?** Age lifetime-e DI nist (static script / early startup), `Get<T>()` OK.  
Age service-e mamul-e → `IOptions<T>` prefer.

Smell: `Get<T>()` har request to handler — Options pattern ro dor mizani.

---

## Se dastan ba ham

### A) Login

```
GlobalAppsettings JwtSettings
  → Configure<JwtSettings>
  → LoginHandler(IOptions<JwtSettings>)
  → ExpirationInMinutes baraye token
```

### B) Outbox tick

```
modules.personnels.json Personnels:Outbox
  → Configure<OutboxOptions>
  → ConfigureProcessOutboxJob : IConfigureOptions<QuartzOptions>
  → ProcessOutboxJob(IOptions) BatchSize
```

### C) Upload S3

```
Storage section
  → IOptions<StorageOptions>
  → S3FileStorage Provider + PublicEndpoint
```

---

## Smell-ha (kamel + tozih)

1. **Magic section string** bedune `SectionName` const  
2. **IConfiguration inject to Application handler** — layer leak  
3. **Secret to appsettings commit** — Options pattern ≠ secret management (User Secrets / env / vault)  
4. **IOptions baraye hot-reload expectation** — na; Monitor mikhad  
5. **OutboxOptions duplicate per module** — 8 class shabih (modular cost)  
6. **ValidateOnStart kam** — misconfig late fail  
7. **Mutable `set` vs `init`** — Storage ba `set`; Jwt ba `init` — inconsistent style  
8. **Get\<T\> + Configure hardo** — OK bootstrap; document chera  
9. **Named confusion** — Personnels:Outbox vs Vehicles:Outbox types joda namespace  
10. **Quartz interval faghat startup** — taghir JSON bedune restart asar nadare  
11. **Empty string defaults** — bind fail silent → runtime weird  
12. **ScalarOptions bind** section shayad khali — defaults package  

---

## Debug checklist (sade)

1. Section name typo? `JwtSettings` vs `JWT`  
2. JSON hierarchy — nested `S3` under `Storage`?  
3. Env-specific file override (`appsettings.Development.json`)?  
4. GlobalAppsettings path load shode (Gateway/service)?  
5. `IOptions.Value` null property — bind miss  
6. Quartz interval ghalat — Outbox section module-e dorost?  
7. Docker env `Storage__S3__Endpoint` (double underscore)  
8. Secret empty → JWT throw on AddCustomJwtAuth?  

---

## 25 soal-e mosahebe

1. Options pattern chie?  
2. Chera beja-ye string indexer?  
3. IOptions vs Snapshot vs Monitor?  
4. Configure vs AddOptions.BindConfiguration?  
5. SectionName const chera?  
6. ValidateOnStart chie?  
7. Named options?  
8. IConfigureOptions chie?  
9. Dejban Outbox → Quartz chejori?  
10. Jwt Configure + Get chera hardo?  
11. Storage nested S3?  
12. PublicEndpoint koja Options-e?  
13. ACLSettings consume koja?  
14. Hot reload Outbox?  
15. Secret management vs Options?  
16. Get\<T\> jayez koja?  
17. Module json `Personnels:Outbox`?  
18. BatchSize koja use?  
19. MediaMTXSettings?  
20. gRPC client settings?  
21. Smell IConfiguration to Application?  
22. Double underscore env bind?  
23. init vs set?  
24. Options + DI lifetime?  
25. Resume one-liner?

---

## Senario-ha (ba tozih-e ravoon)

### A) Interval Outbox 5 → 1

JSON avaz → **restart** API → `ConfigureProcessOutboxJob` dobare → Quartz 1s.  
Bedune restart ba IOptions: asar nadare.

### B) Jwt Secret empty

`Get<JwtSettings>` / validation → boot fail ya sign fail. Options zud fash mikone.

### C) Provider Local → S3

`Storage:Provider` + S3 block → `IOptions` → `S3FileStorage` path. Code if Provider — Day 28.

### D) Wrong section `Personnel:Outbox` (typo)

Bind empty Interval=0 → Quartz weird / job storm. Smell: ValidateOnStart Interval > 0.

### E) Docker MinIO hostname

Env `Storage__S3__Endpoint=http://minio:9000` + PublicEndpoint host — Options bind automatic.

---

## Mini lab

1. Open `JwtSettings` + `AddCustomJwtAuth`  
2. Open `OutboxOptions` + `ConfigureProcessOutboxJob` Personnels  
3. `modules.*.json` Outbox/Inbox  
4. `StorageOptions` + S3FileStorage ctor  
5. Grep `IOptionsMonitor` — expect rare/empty  
6. Grep `ValidateOnStart` — expect rare  
7. Trace `ACLSettings.SectionName` bind  

---

## Resume

**kutah:**

> Used the ASP.NET Core Options pattern across Dejban: typed settings (`JwtSettings`, `StorageOptions`, `ACLSettings`, per-module `OutboxOptions`/`InboxOptions`) bound from configuration and injected via `IOptions<T>`, including `IConfigureOptions<QuartzOptions>` so outbox/inbox polling intervals come from config rather than hardcoding.

**bullet-ha:**

- Bound JWT, ACL, MediaMTX, gRPC, Scalar, and Storage settings with `Configure` / `AddOptions().BindConfiguration` and `SectionName` constants  
- Wired module outbox/inbox options into Quartz via `IConfigureOptions` and job `BatchSize`  
- Distinguished startup `Get<T>()` bootstrap (JWT) from runtime `IOptions<T>` consumption  

**skill-ha:** `Options pattern, IOptions, IConfigureOptions, IConfiguration, appsettings, ASP.NET Core, Quartz, 12-factor config`

---

## File-haye mohem

| chi | koja |
|---|---|
| JwtSettings | `Common/Abstractions/BindingContracts/JwtSettings.cs` |
| Jwt register | `Common/.../ServiceCollectionExtensions.AddCustomJwtAuth` |
| OutboxOptions | `Modules/*/Infrastructure/Outbox/OutboxOptions.cs` |
| Quartz bridge | `ConfigureProcessOutboxJob.cs` / Inbox twin |
| Module bind | `*Module.cs` `Configure<OutboxOptions>(GetSection(...))` |
| StorageOptions | `DCC/Infrastructure/Options/StorageOptions.cs` |
| MediaMTX | `Dejban.Common.Infrastructure/Http/MediaMTXSettings.cs` |
| ACLSettings | `ACLServer/Abstractions/BindingContracts/ACLSettings.cs` |
| Module JSON | `Dejban.Api/modules.*.json` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 05 DI | Options = DI service |
| 06 JWT | JwtSettings |
| 18 Modular DI | per-module Configure Outbox |
| 21/29 Outbox Quartz | Interval/BatchSize |
| 28 MinIO | StorageOptions |
| 27 gRPC | *GrpcClientSettings |
| 33 Scalar | ScalarOptions bind |
| 31 Docker | env `__` bind |

---

## Chejori digest koni (ravesh-e sade)

1. WORLD remote TV + 3 interface (20 min)  
2. Jwt Configure+Get (15 min)  
3. Outbox → Quartz IConfigureOptions (25 min) — **qalb**  
4. Storage nested + ACL (15 min)  
5. Smells validation/hot-reload (10 min)  
6. Lab + 25 soal (25 min)  

---

## Glossary (sade)

| kalame | ma'ni-ye yek khati |
|---|---|
| Options pattern | config → typed class → inject |
| POCO settings | class bind-shodani |
| SectionName | key-e JSON root section |
| `Configure<T>` | register bind |
| `BindConfiguration` | bind by section name string |
| `IOptions<T>` | accessor `.Value` |
| `IOptionsMonitor<T>` | live + OnChange |
| `IOptionsSnapshot<T>` | per-request reload |
| `IConfigureOptions<T>` | code ke T digar ro set mikone |
| `Get<T>()` | one-shot bind az IConfiguration |
| `ValidateOnStart` | fail boot age invalid |
| Nested options | property object dakhel options |

---

## Deep dive — IOptions lifetime

`IOptions<T>` khodesh singleton-e. `.Value` mamulan ye instance-e cached az config initial.  

**Farz kon** Scoped service `LoginHandler` inject `IOptions<JwtSettings>` — OK, hame request yek setting.  

**Farz kon** mikhay per-tenant setting — Options classic kafi nist; design digar (DB settings / named).

---

## Deep dive — env var bind

Configuration provider:

`Storage__S3__PublicEndpoint=http://localhost:19000`

→ `StorageOptions.S3.PublicEndpoint`  

**Yani chi?** Docker Compose environment = haman Options. 12-factor.

---

## Deep dive — Options vs appsettings hierarchy

Order mamul: appsettings.json → appsettings.{Env}.json → env → command line.  
Last wins. GlobalAppsettings path ezafi to Dejban — layer digar.

**Chera important?** Local Development Issuer avaz; Docker env Secret avaz — Options haman class.

---

## Anti-pattern (ba tozih)

```csharp
// BAD
var mins = configuration["JwtSettings:ExpirationInMinutes"]; // string everywhere

// GOOD
_jwt.Value.ExpirationInMinutes;

// BAD: secret in repo
"AccessTokenSecret": "abc123"

// GOOD: secret env / vault; Options faghat shape

// BAD: expect hot reload ba IOptions
// GOOD: Monitor + reschedule ya restart policy
```

---

## Interview 60s (ravoon)

> «We follow the Options pattern: settings POCOs with SectionName constants, bound via Configure or AddOptions().BindConfiguration, and consumed with IOptions. JWT is configured that way for token issuance and validation. Each Dejban module binds OutboxOptions and InboxOptions from modules.*.json, and an IConfigureOptions\<QuartzOptions\> class maps IntervalInSeconds into Quartz triggers while jobs read BatchSize from IOptions. Storage and gRPC clients use the same approach. We mostly use IOptions rather than Monitor, so config changes need a restart.»

---

## Quick self-test

1. Options yani? → typed config inject  
2. Dejban default interface? → IOptions  
3. Jwt SectionName? → JwtSettings  
4. Outbox fields? → IntervalInSeconds, BatchSize  
5. Quartz bridge? → IConfigureOptions\<QuartzOptions\>  
6. Storage section? → Storage (+ S3 nested)  
7. Bind styles? → Configure / AddOptions.Bind  
8. Hot reload default? → na  
9. ValidateOnStart common? → na (gap)  
10. Env nested? → `__`  

---

## Final checklist

- [ ] 3 interface farq  
- [ ] SectionName + POCO  
- [ ] Jwt dual Get/Configure  
- [ ] Outbox→Quartz story  
- [ ] Nested Storage  
- [ ] Smells  
- [ ] Resume 60s  

---

## Extra — «IConfigureOptions» ra chejori seda koni

Begu:

«Ye class ke vaghti DI mikhad QuartzOptions ro build kone, ma miayim az OutboxOptions mikhunim va trigger interval ro set mikonim. Yani Options-e ma Options-e library-e digar ro feed mikone.»

---

## Extra — Farz kon BatchSize 50 → 5

Load kam; har tick kamtar message.  
Job: `outboxOptions.Value.BatchSize` to query Take.  
Interval joda — do knob: *cheghadr zud* vs *cheghadr har bar*.

---

## Extra — IdentitySettings nested

IdentitySettings dakhelesh SignIn/Password/User/Lockout nested classes.  
Bind `IdentitySettings` section → nested objects. Haman nested Options pattern.

---

## Extra — VehicleAccessOptions + filter

`IOptions<VehicleAccessOptions>` to `PlateReaderAgentAuthFilter` — filter auth az config (key/header).  
Options = policy runtime bedune recompile.

---

## Extra — ReportRegistryOptions

Reporting `Configure<ReportRegistryOptions>(GetSection(...))` — list/registry report-ha typed.  
Options faghat infra nist; domain-ish config ham.

---

## Map — az JSON ta job

```
modules.personnels.json
  Personnels.Outbox.IntervalInSeconds = 5
       ↓
Configure<OutboxOptions>(GetSection("Personnels:Outbox"))
       ↓
IOptions<OutboxOptions>
       ↓
ConfigureProcessOutboxJob.Configure(QuartzOptions)
       ↓
Trigger every 5s → ProcessOutboxJob
       ↓
BatchSize from IOptions → Dedupe publish
```

---

## Map — decision «chejori config bekhonam?»

```
Bootstrap / JwtBearer setup → Get<T>() + Configure
Runtime service → IOptions<T>
Need reload without restart → IOptionsMonitor
Per HTTP request fresh → IOptionsSnapshot
Configuring another options type → IConfigureOptions<TOther>
One-off script → Get<T>()
```

---

## Lab aha (sade)

1. Interval 5→30 → restart → Quartz log/tick  
2. Remove Outbox section → Interval 0 behavior  
3. Print `_storageOptions.Value.S3.Bucket`  
4. Find dual Get+Configure Jwt — comment chera  

---

## What Day 34 is *not*

- Options source custom provider deep  
- Azure App Configuration  
- Feature flags library  
- Full secret vault  

Focus: **typed Options + Dejban bind/consume + Quartz bridge**.

---

## Resume keywords (ATS)

`Options pattern` · `IOptions` · `IConfigureOptions` · `BindConfiguration` · `appsettings` · `ASP.NET Core` · `configuration` · `Quartz` · `12-factor`

---

## Band-e gharardad-e jadid — chejori in fasl neveshte shode

> **Tozihat ravoontar va sade-tar.** Dastan → yani chi → chera → smell.

In ruz:

- remote TV baraye Options  
- Outbox→Quartz ba dastan  
- honest: IOptions na Monitor; ValidateOnStart kam  
- Jwt Get+Configure chera  

---

## 10 jomle ke bayad betuni seda koni (fluency drill)

1. Options = config typed + DI.  
2. IOptions default Dejban; Monitor kam.  
3. SectionName const = yek haqiqat.  
4. Configure va BindConfiguration har do OK.  
5. Jwt: Configure baraye inject + Get baraye bearer setup.  
6. OutboxOptions: Interval + BatchSize.  
7. IConfigureOptions Quartz az Outbox mikhone.  
8. Storage nested S3 + PublicEndpoint.  
9. Env bind ba `__`.  
10. ValidateOnStart gap-e possible.

---

## Khoruj-e zehni (ye paragraph baraye khodet)

> Midunam Options pattern yani setting az JSON/env be class bind she va ba IOptions inject. To Dejban Jwt, Storage, ACL, gRPC, Scalar, va Outbox/Inbox hamin shekl-an; ghashang-tarin mesal ine ke Interval Outbox ba IConfigureOptions miravad to Quartz. Midunam hot-reload default nist va validation on start kam-e.

Age in paragraph mal-e to shod — Day 34 done.

---

*Day 34 tamum. Ba'd: Day 35 — Factory + Strategy (device sync) (amade). Fehrest: [README.md](./README.md).*
