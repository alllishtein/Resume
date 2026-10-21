# 09 — Options

*Config string-e part nist. Yek class-e strongly typed ast ke DI midahad.*

---

## Ye khat

Options pattern tanzim-e `appsettings` ra be yek object bind mikonad. Consumer `IOptions<OutboxOptions>` migirad, na `IConfiguration["Personnels:Outbox:BatchSize"]`.

## Moshkel

```csharp
var batch = configuration.GetValue<int>("Personnels:Outbox:BatchSize");
```

- esm-e key typo darad va ta runtime moshakhas nist
- test bayad hame-ye configuration ra besazad
- har job haman string ra copy mikonad
- reload va lifetime moshakhas nist

## Code

`Personnels/.../Outbox/OutboxOptions.cs`

```csharp
internal sealed class OutboxOptions
{
    public int IntervalInSeconds { get; init; }
    public int BatchSize { get; init; }
}
```

`init` yani ba'd az bind avaz nemishavad. Shekl-e immutable.

Sabt to `PersonnelsModule`:

```csharp
services.Configure<OutboxOptions>(configuration.GetSection("Personnels:Outbox"));
services.Configure<InboxOptions>(configuration.GetSection("Personnels:Inbox"));
services.ConfigureOptions<ConfigureProcessOutboxJob>();
```

Section **per module** ast: `Personnels:Outbox` na yek `Outbox` global. Har module interval va batch-e khod ra darad. Hamin baraye Visitors, Vehicles, Armory, ...

Masraf:

```csharp
internal sealed class ProcessOutboxJob(IOptions<OutboxOptions> outboxOptions) : IJob
{
    // outboxOptions.Value.BatchSize
    // outboxOptions.Value.IntervalInSeconds
}
```

`ConfigureProcessOutboxJob` `IConfigureOptions<...>` ast: Quartz/job ra az haman `IntervalInSeconds` misazad. Config-e job posht-e code-e schedule-e hard-code nist.

## Se lifetime — so'al-e hatmi

| Interface | Lifetime-e khodash | Arzesh | Reload-e file |
|---|---|---|---|
| `IOptions<T>` | singleton, `Value` sabet | startup | na |
| `IOptionsSnapshot<T>` | scoped | har request dobare bind | bale, har request |
| `IOptionsMonitor<T>` | singleton | `CurrentValue` + `OnChange` | bale, callback |

Job-e background **scoped request nadarad**. `IOptionsSnapshot` anja ghalat ast (scoped ra nemishavad az singleton/job-e dir-baz gereft bedune scope). `IOptions<T>` baraye job-i ke ta restart avaz nemishavad dorost ast. Age interval bayad bi-restart avaz shavad, `IOptionsMonitor` va `OnChange` baraye reschedule.

In stack job-ha `IOptions<T>` migirand. Javab-e mosahebe: "batch va interval ba deploy avaz mishavad, na vasat-e run. Pas snapshot nemikhahim."

## Validate

Bind-e khali `BatchSize = 0` misazad va job bisar mimanad ya hame chiz ra mikeshad. Options-e jaddi `ValidateDataAnnotations` ya `Validate(o => o.BatchSize > 0)` dar startup fail mikonad. Age in module an ra nadarad, be onvan-e chiz-i ke **midani** begou, na be onvan-e bug-e penhan ke "hatman hast".

`Configure` khodesh exception nemidahad age section gom bashad. Property-ha default-e `0` mimanand.

## Farq ba constant

Constant to code: taghir = rebuild. Options: taghir = config + restart (ba `IOptions`). Secret (connection string) ham options ast vali jay-e digar (env, secret store), na commit-e appsettings.

## Script-e 60 sanie

> "Har module `OutboxOptions` va `InboxOptions` darad: `IntervalInSeconds` va `BatchSize`. `Configure<T>` section-e `Personnels:Outbox` ra bind mikonad. Job `IOptions<T>.Value` migirad. Snapshot nist chon job per-request nist va ma reload-e daqiqei nemikhahim. `ConfigureProcessOutboxJob` haman interval ra be scheduler midahad. Section-ha joda-and ta yek module batch-e digari dashte bashad."

---

## 10 soal

**1. Options che moshkeli ra hal mikonad?**
String-e magic va `IConfiguration` part-and. Class-e typed, testable, va ba DI inject mishavad.

**2. `IOptions` va `IOptionsSnapshot`?**
`IOptions` singleton va ta restart sabet. `Snapshot` scoped va har request config-e taze. Dovomi ra be job-e singleton mostaghim nadah.

**3. `IOptionsMonitor` key?**
Vaghti yek singleton bayad taghir-e config ra **beyn-e** request/job bebine, ba `OnChange`.

**4. Chera section per module ast?**
Har DbContext va har job joda ast. Batch-e Personnels nabayad Vehicles ra kharab konad.

**5. `init` chera?**
Ta ba'd az bind, code `BatchSize` ra ja-be-ja nakonad. Manba'-e hagh config ast.

**6. Section gom bashad chi mishavad?**
Exception-e bind na. `0`. Job-e ba batch-e sefr ya interval-e sefr. Validate-e startup in ra zud neshan midahad.

**7. Chetor test mikoni?**
`Options.Create(new OutboxOptions { BatchSize = 10, IntervalInSeconds = 5 })` va an ra be job bedah. File-e json lazem nist.

**8. Options va Options pattern-e GoF?**
Esm-e yeki ast, chiz-e yeki nist. In **Configuration Options** ASP.NET ast, na pattern-e "optional parameter object" GoF. To mosahebe esm-e dorost ra begou.

**9. Connection string ham `IOptions`?**
Mitavanad bashad. Ma'moolan `GetConnectionString` ya options-e DbContext. Farq-e pattern nist; farq-e in ast ke secret ra to git nazari.

**10. `ConfigureOptions<ConfigureProcessOutboxJob>` chi mikonad?**
Class-e joda-ye `IConfigureOptions` / `IPostConfigureOptions` ra sabt mikonad ta **ba'd** az bind, yek tanzim-e digar (schedule-e job) az haman value sakhte shavad. Hame-ye an to `Program.cs` nemimanad.
