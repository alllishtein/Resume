# 09 — Options

Tanzimat dade ast, na `if` va na string-e partakande. Ye class shekl-e an dade ra ta'rif mikonad. System an class ra az file ya mohit por mikonad va be masraf-konande midahad.

In pattern-e GoF nist. Pattern-e configuration to ASP.NET Core ast. To mosahebe esm-e dorost ra begou ta ba parameter-e ekhtiari-ye method ghalt nashavad.

## Moshkel

Code be adad-e "har chand sanie" va "chand ta dar har bar" niaz darad. Rah-haye bad:

- `const int Batch = 100` — taghir yani compile, hatta vaghti faghat adad avaz shode
- `configuration["Jobs:Outbox:BatchSize"]` to dah class — typo-e string ta runtime malum nist, va hich-kas shekl-e kamel-e tanzim ra ye ja nemibinad
- khandan-e file-e json dakhel-e job — job be file chasbide, na be arzesh

Masraf-konande be manba' chasbide, na be arzesh-e typed.

## Ide

1. Ye class-e sade shekl ra ta'rif mikonad (`BatchSize`, `Interval`).
2. Ye bind-konande manba' (json, env) ra ru an class mineshanad.
3. Masraf-konande faghat class-e por-shode ra az DI migirad.

Manba' avaz mishavad, emzay-e constructor avaz nemishavad. Shekl avaz mishavad, compiler ja-haye masraf ra neshan midahad.

Class-e options service-e business nist. Database baz nemikonad. Faghat adad va string va flag negah midarad. Agar method-e `StartJob()` ru an gozashti, do naghsh ra ghalat kard-e-i.

## Se rah-e khandan

Manba' mitavanad bad az start avaz shavad. Pas "ye bar bekhan" va "har bar taze bekhan" do gharardad-and.

| Rah | Chi mibini | Key taze mishavad | Be ki midahand |
|---|---|---|---|
| `IOptions<T>` | `Value` sabet | startup. reload na | job va singleton |
| `IOptionsSnapshot<T>` | `Value` taze | avval-e har request | handler-e scoped |
| `IOptionsMonitor<T>` | `CurrentValue` | haman ke manba' avaz shod, ba `OnChange` | singleton-i ke bayad bi-restart be-rooz shavad |

`Snapshot` scoped ast. An ra az ye singleton-e bi-scope nagir.

`Monitor` baraye "be man khabar bedeh config avaz shod" ast. Callback bayad kutah bashad.

Entekhab gharardad-e mahsul ast:

- adad-e batch ke faghat ba deploy avaz mishavad → `IOptions`
- flag ke bayad request-e ba'di an ra bebinad → `Snapshot` ya `Monitor`
- job-e background ke scope-e HTTP nadarad → `IOptions` ya `Monitor`. `Snapshot` na

## Chand nemune az ye shekl

Gahi ye shekl, chand nemune mikhahi: outbox-e module-ye A va outbox-e module-ye B, har do `BatchSize` darand, adad-eshan farq mikonad.

Ya do class-e joda, ya ye class ba esm-e joda (named options). Named vaghti shekl vaghe'an yeki ast. Section-e file (`"Personnels:Outbox"`) haman nemune ra ru class mineshanad.

## Validate

Bind-e narm khata nemidahad. Section-e gom yani property-e `0` va `null`. Job ba batch-e sefr ya hame-ye jadval ra yekja mikeshad ya hich kar nemikonad.

Validate-e startup bayad shekast-e roshan bedahad: `BatchSize > 0`. Shekast-e nime-shab badtarin zaman-e fahmidan-e typo ast.

Property-e `init` yani bad az bind, kasi `BatchSize = 1` nemikonad. Manba'-e hagh config ast. Agar runtime bayad an ra avaz konad, digar options nist. State-e barname ast.

## Mesal-e koochik

```csharp
sealed class OutboxOptions
{
    public int IntervalInSeconds { get; init; }
    public int BatchSize { get; init; }
}

services.Configure<OutboxOptions>(configuration.GetSection("Orders:Outbox"));

sealed class Worker(IOptions<OutboxOptions> options)
{
    public Task Run(CancellationToken ct) =>
        Poll(options.Value.BatchSize, options.Value.IntervalInSeconds, ct);
}
```

Test: `Options.Create(new OutboxOptions { BatchSize = 10, IntervalInSeconds = 5 })`. File-e json lazem nist.

Secret (password-e database) shekl-ash options ast, vali jay-e zakhire-ash file-e commit-shode nist. Env ya secret store.

Ghanun-e mahsul ("hadde mojudi 10 ta ast") agar ghanun-e domain ast, options nist. Options baraye tanzim-e amaliat va mohit ast. Agar hame-ye ghanun beravad to json, test-e ghanun bedune config moshkel mishavad.

## Hala dar Dejban

`OutboxOptions` va `InboxOptions` to har module. Shekl-e Personnel:

```csharp
internal sealed class OutboxOptions
{
    public int IntervalInSeconds { get; init; }
    public int BatchSize { get; init; }
}
```

Bind:

```csharp
services.Configure<OutboxOptions>(configuration.GetSection("Personnels:Outbox"));
services.Configure<InboxOptions>(configuration.GetSection("Personnels:Inbox"));
services.ConfigureOptions<ConfigureProcessOutboxJob>();
```

Section per module ast. Shekl yeki ast, nemune chand ta. Outbox-e Vehicles batch-e Personnel ra avaz nemikonad.

`ProcessOutboxJob` `IOptions<T>` migirad, na Snapshot. Job scope-e HTTP nadarad va gharardad-e alan in ast ke interval ba deploy avaz mishavad, na vasat-e run. Agar beporsand "chera Monitor na?": chon reload-e zende-ye schedule ra nakarde-im. Agar farda interval bayad bi-restart avaz shavad, `IOptionsMonitor` va `OnChange` lazem ast. Alan an nist.

`ConfigureProcessOutboxJob` bad az bind, trigger-e Quartz ra az haman `IntervalInSeconds` misazad. Cron-e sakhte-shode posht-e code-e job nist.

Section-e gom sefr misazad. Validate-e `BatchSize > 0` ra farz nakon magar khodet `Validate` ra dide bashi.

## Agar beporsand, in tor begou

> Options shekl-e typed-e tanzim ast. Masraf-konande manba' ra nemibinad. `IOptions` sabet-e startup ast, Snapshot taze be ezaye request, Monitor taze ba callback. Snapshot ra be background job nemidaham. Dejban `OutboxOptions` darad: interval va batch, section-e `Personnels:Outbox`. Job `IOptions` migirad chon reload-e zende nadarim. `ConfigureProcessOutboxJob` haman adad ra be scheduler midahad. In GoF nist.

## Dah so'al

**1. In pattern che chasbidani ra mishkanad?**
Chasbidan-e masraf-konande be manba' va be string-e key. Mimanad chasbidan be shekl-e typed.

**2. Chera GoF nist?**
To ketab-e GoF nist. Gharardad-e configuration-e framework ast.

**3. `IOptions` va `IOptionsSnapshot`?**
Avval sabet-e startup. Dovom taze-ye har request. Dovom ra az job-e bi-scope nagir.

**4. `IOptionsMonitor` key?**
Vaghti ye omr-e toolani bayad `CurrentValue` ra bebinad va `OnChange` begirad.

**5. Named options ya do class?**
Named vaghti shekl daghighan yeki ast. Do class vaghti joda'i va esm-e roshan mikhahi.

**6. Section-e gom chi mishavad?**
Exception-e bind na. Default-e `0` va `null`. Validate-e startup an ra zud mikonad.

**7. Chera `init`?**
Ta code bad az bind manba'-e hagh ra ja-be-ja nakonad.

**8. To Dejban chera `IOptions` na Snapshot?**
Job-e outbox scope-e request nadarad va interval ba deploy avaz mishavad.

**9. `ConfigureProcessOutboxJob` chi ezafe mikonad?**
Az options-e por-shode, tanzim-e scheduler sakhte mishavad.

**10. Che adadi nabayad options bashad?**
Ghanun-e mahsul ke joz'-e invariant-e domain ast. Options baraye tanzim-e amaliat ast.
