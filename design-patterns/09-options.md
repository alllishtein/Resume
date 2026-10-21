# 09 — Options

---

## Ye khat

Tanzimat **dade** ast, na `if` va na string-e partakande. Yek class shekl-e an dade ra tarif mikonad. System an class ra az file ya mohit por mikonad va be masraf-konande midahad.

In pattern-e GoF nist. Pattern-e **configuration** dar ASP.NET Core ast. To mosahebe esm-e dorost ra begou ta ba Optional Parameter ya ba pattern-e digar ghalt nashavad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Code be adad-e "har chand sanie" va "chand ta dar har bar" niaz darad. Rah-haye bad:

- `const int Batch = 100` — taghir = compile va deploy-e code, hatta vaghti faghat adad avaz shode
- `configuration["Jobs:Outbox:BatchSize"]` to dah class — typo-e string ta runtime moshakhas nist, test bayad hame-ye config-e jahan ra besazad, va hich-kas shekl-e kamele tanzim ra yek ja nemibinad
- khandan-e file-e json dakhel-e job — job be file vast shode, na be **arzesh**

Moshkel-e vahed: masraf-konande be **manba'** vast shode, na be **arzesh-e typed**.

## Ta'rif

Options pattern:

1. yek class-e sade shekl ra tarif mikonad (`BatchSize`, `Interval`)
2. yek bind-konande manba' (json, env, argument) ra rooye an class mineshind
3. masraf-konande faghat class-e por-shode ra az DI migirad

Manba' avaz mishavad, emzaye constructor-e job avaz nemishavad. Shekl avaz mishavad, compiler ja-haye masraf ra neshun midahad. String-e `"BatchSize"` in kar ra nemikonad.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Options class | shekl-e dade, bedune raftar-e sangin |
| Binder | map-e key/value be property |
| Validator (ekhtiari) | "BatchSize > 0" ghabl az inke kasi an ra bekhanad |
| Masraf-konande | `options.BatchSize` , na `IConfiguration` |

Class-e options **service-e business nist**. Database baz nemikonad. Faghat adad va string va flag negah midarad. Agar method-e `StartJob()` rooye an gozashti, do naghsh ra ghalt kard-e-i.

## Se ravesh-e khandan — in bakhsh ra hefz kon

Manba' mitavanad ba'd az start avaz shavad (file-e json-e taghir-karde, config server). Pas "yek bar bekhan" va "har bar taze bekhan" do gharardad-and.

| Rah | Arzesh ke mibini | Kay taze mishavad | Be ki midahand |
|---|---|---|---|
| `IOptions<T>` | `Value` sabet | startup. reload na | singleton-e dir-baz, job |
| `IOptionsSnapshot<T>` | `Value` taze | avval-e **har scope** (har request) | handler-e scoped |
| `IOptionsMonitor<T>` | `CurrentValue` | hamun ke manba' avaz shod, ba callback-e `OnChange` | singleton-i ke bayad bi-restart be-rooz shavad |

`Snapshot` scoped ast. An ra az yek singleton-e bi-scope nagir. Container ya exception midahad ya, badtar, scope-e ghalat ra ghofl mikonad.

`Monitor` khodesh singleton-e amn-tar baraye "be man khabar bedeh config avaz shod" ast. Callback bayad kutah bashad. Kar-e sangin-e dakhel-e `OnChange` thread-e reload ra gir mikonad.

Entekhab gharardad-e mahsul ast, na "hamishe Monitor chon jadidtar ast":

- adad-e batch ke faghat ba deploy avaz mishavad → `IOptions`
- flag-e feature ke bayad request-e ba'di an ra bebine, bedune restart → `Snapshot` ya `Monitor`
- job-e background ke scope-e HTTP nadarad → `IOptions` ya `Monitor`. `Snapshot` na

## Named options

Gahi **yek shekl**, chand nemune mikhahi: outbox-e module-ye A va outbox-e module-ye B, har do `BatchSize` darand, adad-eshan farq mikonad.

Do rah:

- do class-e joda (`PersonnelsOutboxOptions`, `VisitorsOutboxOptions`) — sade, tekrari-e shekl
- yek class + **esm** (`IOptionsSnapshot<OutboxOptions>` ba name-e `"Personnels"`) — shekl yek bar, nemune chand bar

Named options vaghti arzesh darad ke shekl vaghe'an yeki ast. Vaghti shekl-ha joda shodand, do class roshan-tar ast.

Section-e file (`"Personnels:Outbox"`) haman "nemune" ra rooye class mineshanad. Do section, do bind, do object.

## Validate

Bind-e narm khata nemidahad. Section-e gom = property-e `0` va `null`. Job ba batch-e sefr ya hame-ye jadval ra yekja mikeshad ya hichkar nemikonad.

Validate **startup** bayad shekast-e moshakhas bedahad: `BatchSize > 0`, interval kamtar az yek had-e aghl. Shekast-e dir-hanjam (avvalin run-e job, nasf-e shab) badtarin zaman-e fahmidan-e typo ast.

Validate joz'-e pattern-e kamel ast, na ezafe-ye salighe-i. Bind-e bedune validate faghat nesfe-ye rah ast.

## `init` va immutable

Property-e `init` ya `record` ya'ni ba'd az bind, kasi `BatchSize = 1` nemikonad. Manba'-e hagh config ast, na field-e ghabel-e ja-be-jayi-e runtime. Agar runtime bayad an ra avaz konad, an dige options nist. State-e barname ast va jay-e digar mizendegi.

## Mesal-e donya

```csharp
sealed class OutboxOptions
{
    public int IntervalInSeconds { get; init; }
    public int BatchSize { get; init; }
}

services.Configure<OutboxOptions>(configuration.GetSection("Orders:Outbox"));
services.AddOptions<OutboxOptions>()
    .Validate(o => o.BatchSize > 0 && o.IntervalInSeconds > 0);

sealed class Worker(IOptions<OutboxOptions> options)
{
    public Task Run(CancellationToken ct) =>
        Poll(options.Value.BatchSize, options.Value.IntervalInSeconds, ct);
}
```

Test: `Options.Create(new OutboxOptions { BatchSize = 10, IntervalInSeconds = 5 })`. File-e json lazem nist. In haman dalil-e joda kardan-e masraf az manba' ast.

## Farq-ha

**Constant.** Taghir = rebuild. Options taghir = avaz-e manba', ba restart ya bi-restart baste be rah-e khandan.

**`IConfiguration` mostaghim.** String, bi-shekl, bi-validate-e markazi. Options rooye an mineshinad, jay-ash ra nemigirad. Bind az haman `IConfiguration` miayad.

**Service locator.** Gereftan-e `IOptions` az DI locator nist. Locator ya'ni "container ra bedeh ta har chi mikhaham bekasham". Inja type-e daghigh-e `OutboxOptions` to constructor ast. Compiler an ra mibinad.

**Environment variable-e part.** Manba'-e khoob baraye secret va baraye deploy. Hanuz bayad be haman class bind shavad. `Environment.GetEnvironmentVariable` to vasat-e business haman string-e part ast.

## Koja bezan, koja nazan

Bezan baraye har adad, flag, connection, va interval ke beyn-e mohit-ha (dev, test, prod) farq mikonad.

Nazan baraye ghanun-e domain ("had-e aksar-e mojudi 10 ta ast" agar an ghanun-e mahsul ast na tanzim-e ops). An ghanun-e entity ast. Options-e bi-had, domain ra be file-e json tabdil mikonad va test-e ghanun bedune config moshkel mishavad.

Secret (password-e database) shekl-ash options ast, vali **jay-e zakhire-ash** file-e commit-shode nist. Env ya secret store. Pattern-e options an ra joda nemikonad. Enzebat-e deploy an ra joda mikonad.

## Mafhoom ra injoori begou

> "Options shekl-e typed-e tanzim ast. Masraf-konande manba' ra nemibinad. Se rah-e khandan daram: IOptions sabet-e startup, Snapshot taze be ezaye request, Monitor taze ba callback baraye singleton. Snapshot ra be job-e bi-scope nemidaham. Bind-e bedune validate section-e gom ra sefr mikonad. Named options vaghti yek shekl chand nemune darad. In GoF nist."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

`OutboxOptions` va `InboxOptions` to har module. Shekl-e Personnels:

```csharp
internal sealed class OutboxOptions
{
    public int IntervalInSeconds { get; init; }
    public int BatchSize { get; init; }
}
```

`init` haman ghanun-e "ba'd az bind dast nazan" ast.

Bind:

```csharp
services.Configure<OutboxOptions>(configuration.GetSection("Personnels:Outbox"));
services.Configure<InboxOptions>(configuration.GetSection("Personnels:Inbox"));
services.ConfigureOptions<ConfigureProcessOutboxJob>();
```

Section **per module** ast. Shekl yeki ast (`Interval` + `Batch`), nemune chand ta. Be jaye named-options-e yek class-e global, har module class-e dakheli-e khod ra darad va section-e khod ra bind mikonad. Natije haman "chand nemune" ast, ba joda'i-e assembly. Outbox-e Vehicles batch-e Personnels ra avaz nemikonad.

`ProcessOutboxJob` va `ProcessInboxJob` `IOptions<T>` migirand, na Snapshot. Job scope-e HTTP nadarad va gharardad-e alan in ast ke interval ba restart/deploy avaz mishavad, na vasat-e run. Agar beporand "chera Monitor na?": chon reload-e zende-ye schedule ra nakarde-im. Agar farda interval bayad bi-restart avaz shavad, bayad `IOptionsMonitor` va `OnChange` baraye reschedule. Alan an nist. Dorogh nagou.

`ConfigureProcessOutboxJob` `IConfigureOptions` ast. Ya'ni **ba'd** az bind, yek tanzim-e digar (trigger-e Quartz) az haman `IntervalInSeconds` sakhte mishavad. Shekl-e "config-e job" posht-e code-e `cron` hard-code nist. Do laye: avval options por mishavad, ba'd scheduler az an mikhanad.

Validate-e `BatchSize > 0` ra to hamin class-ha farz nakon magar khodet an `Validate` ra dide bashi. Bind-e default-e .NET section-e gom ra be sefr tabdil mikonad. An nokte-ye bakhsh-e avval inja ham zende ast: sefr-e bi-seda.

Test-e job `Options.Create(...)` mikhahad, na `appsettings.json`.

---

## Script-e 90 sanie

> "Options pattern-e ASP.NET ast, GoF nist. Class shekl ra tarif mikonad, bind manba' ra por mikonad, masraf-konande faghat Value-e typed migirad. IOptions sabet ast, Snapshot per request, Monitor singleton-e reload-dar. Snapshot ra be background job nemidaham. Dejban `OutboxOptions` darad: interval va batch, section-e `Personnels:Outbox` va hamta-ye har module. Job `IOptions` migirad chon reload-e zende nadarim. `ConfigureProcessOutboxJob` haman adad ra be scheduler midahad. Section-e gom sefr misazad. Validate-e startup bakhsh-e kamel-e pattern ast."

---

## 10 soal

**1. In pattern che vast-i ra mishkanad?**
Vast-e masraf-konande be manba' va be string-e key. Mimanad vast-e be shekl-e typed.

**2. Chera GoF nist?**
To ketab-e GoF nist. Gharardad-e configuration-e framework ast. Optional argument-e method ham nist.

**3. `IOptions` va `IOptionsSnapshot`?**
Avval sabet-e startup va singleton-pasand. Dovom taze-ye har scope. Dovom ra az singleton-e bi-scope nagir.

**4. `IOptionsMonitor` key?**
Vaghti yek omr-e toolani bayad `CurrentValue` ra bebine va `OnChange` begirad, bedune scope-e request.

**5. Named options ya do class?**
Named vaghti shekl daghighan yeki ast va chand nemune mikhahi. Do class vaghti mikhahi joda'i va esm-e roshan.

**6. Section-e gom chi mishavad?**
Exception-e bind na. Default-e `0` va `null`. Validate-e startup an ra zud mikonad.

**7. Chera `init`?**
Ta code ba'd az bind manba'-e hagh ra ja-be-ja nakonad.

**8. To Dejban chera `IOptions` na Snapshot?**
Job-e outbox/inbox scope-e request nadarad va interval ba deploy avaz mishavad, na vasat-e request.

**9. `ConfigureProcessOutboxJob` chi be pattern ezafe mikonad?**
Bind-e dovom: az options-e por-shode, tanzim-e scheduler sakhte mishavad. `Program` por az `cron` nemimimand.

**10. Che adadi nabayad options bashad?**
Ghanun-e mahsul ke joz'-e invariant-e domain ast. Options baraye tanzim-e amaliat va mohit ast.
