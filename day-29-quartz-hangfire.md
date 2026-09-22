# Day 29 — Quartz + Hangfire

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

To ASP.NET, har kari ke «ba'dan» ya «har chand saniye» bayad anjam she, niaz be **background job** dare. Do tooling-e asosli to Dejban inja mibinim:

**Quartz.NET** — scheduler-e dakhel-e process-e **Dejban** (modular monolith). Har module (`Personnels`, `Visitors`, …) ye `ProcessOutboxJob` va `ProcessInboxJob` dare ke `IJob`-e Quartz-an, ba schedule-e sade (`IntervalInSeconds`) va attribute-e `[DisallowConcurrentExecution]`. In hamun worker-i-e ke Days 19/21/23 goftim: poll outbox/inbox ba Dapper.

**Hangfire** — queue + dashboard baraye kar-haye **fire-and-forget / continue / recurring** to microservice-haye dge: **ACLServer** (sync-e device, `MemoryStorage`, queue `devices_queue`) va **RequestTracker** (PostgreSQL storage + `RecurringJob` baraye `StepSubstitutionSweeper` har 5 daghighe). Dashboard-hashun «hardened»-e (Basic auth, remote/write flag).

Yani chi? Quartz = clock-e poll-e messaging dakhel-e Dejban. Hangfire = job queue baraye sync-e hardware va business sweep. Har do background-an, ama mas'uliyat-hashun fargh mikone — ba MassTransit/outbox (Days 20–23) hamposh nistand, balke **trigger**-e worker-ha-n.

---

# BAKHSH-E AVAL: WORLD — background jobs chera lazeman

## Chera request thread kaf nist?

| to request HTTP | background job |
|---|---|
| user montazer mimune | javab zud; kar posht sahne |
| timeout gateway | tool mikeshad (sync device, sweep) |
| retry sakht | retry / continue / dashboard |

Mesal: sync-e 500 user be terminal ZK — nabayad HTTP 30s hang kone. Enqueue → worker → SignalR progress.

---

## Se daste-ye ma'mool

| daste | ma'ni | tool-e tipic |
|---|---|---|
| **Recurring / scheduled** | har N saniye/daqiqe/cron | Quartz, Hangfire RecurringJob |
| **Fire-and-forget** | yebar enqueue | Hangfire `BackgroundJob.Enqueue` |
| **Continuation / chain** | job B ba'd az A | Hangfire `ContinueJobWith` |

`BackgroundService` / `IHostedService` (mesal TimeBroadcast, GateStatusChecker) ham background-e — ama **framework-e job** nist: queue, dashboard, retry policy, storage nadare. Inja focus Quartz + Hangfire.

---

## Quartz.NET — tasvir-e zehni

Quartz = scheduler + job store (memory ya DB) + worker threads.

```
Trigger (har 5s) → JobDetail (ProcessOutboxJob) → Execute(IJobExecutionContext)
```

Mafahim:

| mafhum | ma'ni |
|---|---|
| **IJob** | class ba `Execute` |
| **JobDetail / Identity** | esm-e unique job |
| **Trigger** | key / cheghad intermittent |
| **DisallowConcurrentExecution** | ye instance az in job type hamzaman run nashe |
| **IConfigureOptions\<QuartzOptions\>** | register job+trigger az DI/options |

Cluster mode (chand node, shared ADO store) pishrafte-st — Dejban alan in-process ba SchedulerId random.

---

## Hangfire — tasvir-e zehni

Hangfire = **persistent (ya memory) queue** + server workers + optional dashboard.

```
API thread: BackgroundJob.Enqueue(() => DoSync(...))
     ↓
Storage (SQL / Memory)
     ↓
Hangfire Server workers (WorkerCount, Queues)
     ↓
method run + retry on fail
```

| API | karbord |
|---|---|
| `Enqueue` | yebar, zud |
| `Schedule` | delay |
| `ContinueJobWith` | chain |
| `RecurringJob.AddOrUpdate` | cron |
| Dashboard `/hangfire` | didan/retry (amn kon!) |

Storage:

| storage | fayde | moshkel |
|---|---|---|
| **Memory** | sade | restart = job gom; multi-instance share nist |
| **PostgreSQL / SQL** | durable, multi-server | schema + cleanup |

---

## Quartz vs Hangfire (chejori entekhab)

| soal | Quartz | Hangfire |
|---|---|---|
| Poll-e sade har N saniye dakhel-e app? | kheili fit | ham mishe |
| Fire-and-forget az handler + chain? | sakht-tar | **fit** |
| Dashboard UI? | kam | **fit** |
| Cron expression? | ✓ | ✓ Recurring |
| .NET expression tree serialize? | — | Hangfire method call serialize mikone |

Dejban: **har do** — na yeki. Domain poll = Quartz; device sync + sweeper = Hangfire.

---

## Idempotency va overlap

Job-e recurring age tool bekeshad bishtar az interval, **overlap** etefagh miofte → double process.

Rahkar-ha:

- `[DisallowConcurrentExecution]` (Quartz)  
- Hangfire: disable concurrent / mutex / «only one»  
- Inbox/outbox locks (`FOR UPDATE SKIP LOCKED`) — Days 19/21/23  

Scheduler trigger mikone; **safety** to job body + DB.

---

## Amniat-e dashboard

Hangfire dashboard bedune auth = **RCE-ish risk** (trigger job, see args). Bayad:

- disabled by default to prod  
- Basic auth / allowlist  
- read-only mode  
- na public internet bedune VPN  

Dejban `UseHardenedHangfireDashboard` hamin ghavanin ro enforce mikone.

---

## Scale-out

| | single node | multi node |
|---|---|---|
| Quartz memory | OK | har node job-e khodesh (double poll!) |
| Hangfire Memory | OK | **nakon** — job share nemishe |
| Hangfire Postgres | OK | chand server, yek storage |

Smell: ACL Hangfire MemoryStorage — restart mid-sync = chain gom; scale horizontal ACL = har pod queue joda.

---

# BAKHSH-E DOVOM: DEJBAN — koja kodom tool

## Naghshe-ye sari

| koja | tool | storage | chi |
|---|---|---|---|
| Dejban API (8 module) | **Quartz** | in-process | Outbox + Inbox poll per module |
| ACLServer | **Hangfire** | **Memory** | device sync chain, queue `devices_queue` |
| RequestTracker | **Hangfire** | **Postgres** schema `hangfire` | recurring substitution sweeper |
| Identity TimeBroadcast | BackgroundService | — | na Quartz/HF |
| GateStatusChecker | BackgroundService | — | na Quartz/HF |

---

## 1) Quartz to Dejban — registration-e markazi

```csharp
// Dejban.Common.Infrastructure / InfrastructureConfiguration
services.AddQuartz(configurator =>
{
    var scheduler = Guid.NewGuid();
    configurator.SchedulerId = $"default-id-{scheduler}";
    configurator.SchedulerName = $"default-name-{scheduler}";
});

services.AddQuartzHostedService(options =>
    options.WaitForJobsToComplete = true);
```

`WaitForJobsToComplete=true` → hangam shutdown, job-e dar hale ejra tamam she (graceful).

**Smell:** `SchedulerId` har restart **random** — baraye cluster/shared store moshkel mishe; alan memory/in-proc OK-e ama age ba'dan ADO job store bekhan, bayad id sabet.

---

## 2) Per-module job + trigger (olgu)

Har module:

```csharp
// PersonnelsModule
services.Configure<OutboxOptions>(configuration.GetSection("Personnels:Outbox"));
services.ConfigureOptions<ConfigureProcessOutboxJob>();
services.ConfigureOptions<ConfigureProcessInboxJob>();
```

```csharp
internal sealed class ConfigureProcessOutboxJob(IOptions<OutboxOptions> outboxOptions)
    : IConfigureOptions<QuartzOptions>
{
    public void Configure(QuartzOptions options)
    {
        string jobName = typeof(ProcessOutboxJob).FullName!;

        options
            .AddJob<ProcessOutboxJob>(c => c.WithIdentity(jobName))
            .AddTrigger(c => c
                .ForJob(jobName)
                .WithSimpleSchedule(s =>
                    s.WithIntervalInSeconds(_outboxOptions.IntervalInSeconds)
                     .RepeatForever()));
    }
}
```

`OutboxOptions` / `InboxOptions`: `IntervalInSeconds`, `BatchSize`.

Hamin olgu baraye **8 module** takrar mishe (Personnels, Visitors, Vehicles, Armory, …) — har kodum schema/table khodesh.

---

## 3) `ProcessOutboxJob` — chi kar mikone (yadavari)

```csharp
[DisallowConcurrentExecution]
internal sealed class ProcessOutboxJob(...) : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        // Dapper: SELECT … FOR UPDATE outbox batch
        // deserialize domain event
        // TenantContextAccessor.SetContext(siteIds, …)
        // DomainEventHandlersFactory → handlers (Scrutor idempotent)
        // update ProcessedOn / Error
        // Commit
    }
}
```

Jozeiyat-e SQL va outbox = Days 19/21. Inja nokte: **Quartz faghat metronome-e** — har N saniye `Execute` seda mizane.

Inbox job shabih-e (Day 23): claim inbox rows → handlers → mark.

---

## 4) Chera har module job-e joda?

Modular monolith: schema joda, assembly joda, options joda (`Personnels:Outbox`). Ye job-e global «hame outbox» coupling mishe. Joda = failure isolation + interval per module.

Hazine: 8×2 = 16 Quartz job to yek process — OK age interval makul bashe.

---

## 5) Hangfire — ACLServer (device sync)

### DI

```csharp
services.AddHangfire(config => config
    .UseMemoryStorage()
    .UseSerializerSettings(... ReferenceLoopHandling.Ignore));

services.AddHangfireServer(options =>
{
    options.ServerName = "acl_devices";
    options.Queues = ["devices_queue"];
    options.WorkerCount = workerCount ?? Min(ProcessorCount * 5, 20);
});
```

Comment-shode: PostgreSQL storage — **amade budan baraye durable**, ama alan Memory.

### Chain to `DeviceSyncService`

```csharp
private string ChainDeviceJobs(Guid deviceId, Expression<Func<Task>> jobAction)
{
    // last job id per device (static/dict + lock)
    if (!parentExists)
        newJobId = BackgroundJob.Enqueue(jobAction);
    else
        newJobId = BackgroundJob.ContinueJobWith(
            lastJobId, jobAction, JobContinuationOptions.OnAnyFinishedState);

    DeviceJobChains[deviceId] = newJobId;
    return newJobId;
}
```

**Chera chain?** Sync step-ha (users → access group → biometric) nabayad parallel ru-ye **hamun** device — race ru-ye terminal. Chain = serial per device; device-haye mokhtalef mitunan movazi (WorkerCount).

Progress → SignalR `DeviceHub` (Day 26).

**Smell-ha:**

1. MemoryStorage → restart = unfinished chain lost  
2. `DeviceJobChains` in-memory → multi-instance ACL wrong  
3. `OnAnyFinishedState` — hata fail-e parent, child run mishe (ghasdan? check kon)

---

## 6) Hangfire — RequestTracker (sweeper)

### DI — durable

```csharp
services.AddHangfire(config => config
    .UsePostgreSqlStorage(
        options => options.UseNpgsqlConnection(hangfireConnection),
        new PostgreSqlStorageOptions
        {
            SchemaName = "hangfire",
            PrepareSchemaIfNecessary = true
        }));

services.AddHangfireServer(options =>
{
    options.ServerName = "request_tracker";
    options.WorkerCount = configuration.GetValue("HangfireSettings:WorkerCount", 2);
});
```

### Recurring

```csharp
// Program.cs
RecurringJob.AddOrUpdate<StepSubstitutionSweeper>(
    "step-substitution-sweeper",
    sweeper => sweeper.ProcessDueAsync(),
    "*/5 * * * *"); // har 5 daghighe
```

`StepSubstitutionSweeper.ProcessDueAsync`:

1. Substitution-haye active ke start shode va open tasks sync nashode → `SyncOpenTasksAsync`  
2. Anha ke EndAt gozashte va synced → `RevertOpenTasksAsync`  
3. AutoApprove mode ke tamum shode → status Completed  
4. CTS 20s — age cancel, SaveChanges-e baghi-mande  

Business: jaygozin-e assignee to workflow (cartable) — Time-based, fit-e RecurringJob.

---

## 7) Dashboard-e hardened (ACL + RequestTracker)

```csharp
app.UseHardenedHangfireDashboard(configuration);
```

Config:

```json
"HangfireSettings": {
  "WorkerCount": 5,
  "Dashboard": {
    "Enabled": false,
    "Path": "/hangfire",
    "AllowRemoteAccess": false,
    "AllowWrite": false,
    "Username": "",
    "Password": ""
  }
}
```

- Default **Enabled=false**  
- Remote → Basic auth lazeme  
- `IsReadOnlyFunc` age remote va `AllowWrite=false`  
- Filter: localhost vs remote + credentials  

**Lab:** Enabled=true local → `/hangfire` bebin; prod bedune auth = smell.

---

## 8) Quartz / Hangfire / MassTransit — tafkik-e mas'uliyat

```
HTTP Command
  → SaveChanges + outbox row          (transaction)
  → (return 200)

Quartz ProcessOutboxJob (har N s)
  → read outbox → domain handlers
       → IEventBus.Publish → MassTransit → Rabbit

MassTransit consumer (service digar)
  → inbox row → Quartz ProcessInboxJob → handler

ACL sync button
  → Hangfire Enqueue/Continue → gRPC device (Day 27)
  → SignalR progress
```

Hangfire **jaygozin-e outbox nist**. Outbox consistency mide; Hangfire convenience + UI + chain baraye sync-e tool-gir.

---

## Smell-ha (kamel)

1. ACL Hangfire **Memory** — durability kam  
2. Quartz SchedulerId random — cluster-ready nist  
3. Dashboard age Enabled bedune password  
4. 16 Quartz job — monitoring kam (faghat Serilog)  
5. Overlap bedune DisallowConcurrent → double outbox (attribute hast — khub)  
6. Recurring sweeper 5 min — latency substitution  
7. Hangfire serialize Expression — careful ba closure/large args  
8. WorkerCount ziad ru-ye device → overload gRPC  
9. Continue OnAnyFinishedState — fail cascade  
10. No shared Quartz ADO — multi-instance Dejban = double poll (mitune SKIP LOCKED najat bede)  
11. Purge Hangfire succeeded jobs — schema grow  
12. Mixing BackgroundService + HF bedune documentation  

---

## Debug checklist

1. Outbox row mimune ProcessedOn null? → Quartz hosted running? Interval? Log Beginning to process  
2. DisallowConcurrent — job ghabl tool mikeshad?  
3. Hangfire ACL: dashboard Enqueued/Failed  
4. Restart ACL mid-sync → Memory lost?  
5. RequestTracker: table-ha to schema `hangfire`  
6. Sweeper: substitution flags OpenTasksSynced  
7. Cron `*/5 * * * *` timezone UTC?  
8. Queue name `devices_queue` — job be queue eshtebah?  
9. DI: StepSubstitutionSweeper Transient + Recurring OK  
10. Serilog Application name per service  

---

## 25 soal-e mosahebe

1. Chera background job?  
2. Quartz vs Hangfire?  
3. IJob chie?  
4. DisallowConcurrentExecution?  
5. IConfigureOptions\<QuartzOptions\>?  
6. Hangfire Enqueue vs Recurring?  
7. ContinueJobWith?  
8. Memory vs Postgres storage?  
9. Chera Dejban Quartz baraye outbox?  
10. Chera ACL Hangfire baraye sync?  
11. Dashboard risk?  
12. WaitForJobsToComplete?  
13. Multi-instance + Memory Hangfire?  
14. Multi-instance + Quartz in-memory?  
15. Cron expression?  
16. WorkerCount / Queues?  
17. Idempotency ba job overlap?  
18. Fargh ba BackgroundService?  
19. Fargh ba MassTransit consumer?  
20. StepSubstitutionSweeper chi kar mikone?  
21. Chain per deviceId chera?  
22. SchedulerId random smell?  
23. BatchSize outbox?  
24. Chejori job fail ro retry mikoni (HF vs Quartz)?  
25. Observability-e jobs?

---

## Senario-ha

### A) Personnel created  
Save + outbox → Quartz tick → handlers → Rabbit → digar module inbox → Quartz inbox job.

### B) Sync device az UI  
ACL Enqueue chain → workers devices_queue → strategy gRPC → SignalR status.

### C) Substitution start  
Admin substitution save → ta 5 min ba'd sweeper SyncOpenTasks → cartable assignee avaz.

### D) ACL pod restart  
Memory Hangfire empty — sync-haye nime-kar gom; operator dobare sync.

### E) Do instance Dejban  
Har kodum Quartz → do poll; SKIP LOCKED jeloge double handle ro migire (ta hadi).

---

## Mini lab

1. Find `AddQuartz` + yek `ConfigureProcessOutboxJob`  
2. Breakpoint `ProcessOutboxJob.Execute` — create personnel  
3. ACL: enable dashboard local, enqueue sync, watch Succeeded  
4. RequestTracker: `hangfire` schema tables; wait sweeper / trigger manual  
5. Set IntervalInSeconds=60 — latency outbox bebin  
6. Read `UseHardenedHangfireDashboard` flags  

---

## Resume

**kutah:**

> Operated dual background stacks: Quartz.NET hosted jobs per Dejban module to poll transactional outbox/inbox on a configurable interval with non-concurrent execution, and Hangfire for ACL device-sync job chaining (memory queue) plus RequestTracker’s Postgres-backed recurring substitution sweeper, with hardened dashboard access controls.

**bullet-ha:**

- Registered Quartz hosted service and per-module `IConfigureOptions<QuartzOptions>` job/trigger pairs  
- Implemented `[DisallowConcurrentExecution]` outbox/inbox `IJob`s wired to Dapper workers  
- Used Hangfire enqueue/continue chains for serialized per-device ACL sync on a dedicated queue  
- Added Postgres Hangfire storage + cron sweeper for step assignee substitutions; locked down `/hangfire`  

**skill-ha:** `Quartz.NET, Hangfire, Background Jobs, Recurring Jobs, Job Chaining, PostgreSQL Job Storage, ASP.NET Core Hosted Services, Cron, Distributed Systems`

---

## File-haye mohem

| chi | koja |
|---|---|
| AddQuartz | `Dejban.Common.Infrastructure/InfrastructureConfiguration.cs` |
| ConfigureProcessOutboxJob | `Modules/*/Infrastructure/Outbox/` |
| ProcessOutboxJob | hamin |
| ConfigureProcessInboxJob | `Modules/*/Infrastructure/Inbox/` |
| Hangfire ACL DI | `ACLServer/.../ServiceCollectionExtensions.cs` |
| DeviceSyncService.ChainDeviceJobs | `ACLServer/.../DeviceSyncService.cs` |
| Hangfire RT DI + sweeper | `RequestTracker/...` |
| Dashboard | `*/Infrastructure/Hangfire/HangfireDashboard*.cs` |
| Recurring register | `RequestTracker/Program.cs` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 19 Dapper | SQL inside Quartz jobs |
| 20–23 messaging | Quartz = poller outbox/inbox |
| 24 Scrutor | handlers called from outbox job |
| 26 SignalR | sync progress from Hangfire workers |
| 27 gRPC | device calls inside sync jobs |
| 18 DI | ConfigureOptions + module registration |
| 30 Observability | log/metric job duration |

---

## Chejori digest koni

1. Jadval Quartz vs HF vs MT (10 min)  
2. Trace ConfigureOutbox → Execute (20 min)  
3. ChainDeviceJobs + Memory smell (15 min)  
4. Sweeper + cron + Postgres hangfire (15 min)  
5. Dashboard security (10 min)  
6. 25 soal (20 min)

---

## Glossary

| kalame | ma'ni |
|---|---|
| Quartz | .NET job scheduler |
| IJob | unit-e kar-e Quartz |
| Trigger | timing |
| Hangfire | library-e background job + dashboard |
| Enqueue | fire-and-forget |
| RecurringJob | cron-based |
| Continuation | job ba'd az job |
| WorkerCount | parallel workers |
| Job storage | koja state save mishe |
| DisallowConcurrent | no overlap same job |

---

## Deep dive — IConfigureOptions\<QuartzOptions\>

Module-ha `ConfigureOptions<T>` register mikonan. Hangam build-e Quartz, hame `IConfigureOptions<QuartzOptions>` ejra mishan → job+trigger ezafe. In az `AddJob` mostaghim to Program sade-tar-e baraye modular monolith: har module khodesh schedule-esh ro miyare bedune edit-e Common.

---

## Deep dive — expression serialization (Hangfire)

`BackgroundJob.Enqueue(() => Sync(...))` — Hangfire expression tree ro serialize mikone (type + method + args). Args bayad JSON-serializable bashan; DbContext/stream **nade**. Guid arrays OK. In dalil-e `ReferenceLoopHandling.Ignore` ru-ye serializer settings.

---

## Deep dive — queues

```csharp
options.Queues = ["devices_queue"];
```

Job-ha bayad ba hamin queue enqueue shode bashan (ya default). Age Enqueue be default `default` queue bere va server faghat `devices_queue` gush bede → job forever Waiting. Check signature-haye overload ba queue name to DeviceSyncService.

---

## Anti-pattern-ha

```csharp
// BAD: heavy sync to controller
await SyncAllDevices(); // 10 min
return Ok();

// GOOD: BackgroundJob.Enqueue(() => SyncAllDevices(...)); return Accepted();
```

```csharp
// BAD: outbox publish mostaghim az Hangfire bedune row
BackgroundJob.Enqueue(() => bus.Publish(evt));

// GOOD: outbox row + Quartz (ya MT outbox Day 22)
```

```csharp
// BAD: dashboard Enabled public
// GOOD: Enabled false ya VPN + Basic + read-only
```

---

## Interview 60s

> «In Dejban, Quartz runs per-module outbox and inbox pollers on a simple interval with DisallowConcurrentExecution. Hangfire handles longer ACL device syncs with per-device job chaining on an in-memory queue, and RequestTracker uses Postgres-backed Hangfire with a five-minute recurring sweeper for assignee substitutions. Dashboards are off by default and gated with basic auth.»

---

## Quick self-test

1. Outbox poller tool? → Quartz IJob  
2. Attribute no overlap? → DisallowConcurrentExecution  
3. ACL Hangfire storage? → Memory  
4. RT Hangfire storage? → Postgres schema hangfire  
5. Sweeper cron? → `*/5 * * * *`  
6. Device queue name? → devices_queue  
7. Dashboard default? → Enabled false  
8. WaitForJobsToComplete? → true on Quartz hosted  
9. Chain API? → ContinueJobWith  
10. Options wire? → IConfigureOptions\<QuartzOptions\>  

---

## Final checklist

- [ ] Quartz role vs Hangfire role  
- [ ] Per-module Configure*Job  
- [ ] Memory vs Postgres smell  
- [ ] Chain per device  
- [ ] Sweeper business  
- [ ] Dashboard harden  
- [ ] resume  

---

## Extra — retry semantics

**Hangfire:** automatic retry ba delaya (configurable); Failed dashboard.  
**Quartz simple trigger:** age Execute exception — job fail log; tick ba'di dobare (outbox row hanuz unprocessed → natural retry). Inbox/outbox Error column = visibility.

---

## Extra — timezone cron

Hangfire recurring default UTC. `*/5 * * * *` = har 5 min UTC. Business «Daghighe-ye Tehran» nist — baraye substitution EndAt ke UtcNow moghayese mishe, OK. Age cron-e local bekhay, TimeZone ro set kon.

---

## Extra — monitoring pishnahadi

- Metric: outbox lag (now - oldest unprocessed)  
- Metric: Hangfire Enqueued/Failed count  
- Alert: lag > threshold  
- TraceId az HTTP → job (manual pass) — gap-e mamool  

Day 30 (Serilog/OTel) inja vasl mishe.

---

## Extra — BackgroundService-haye hamsaaye (ke in fasl nistan)

| service | koja | chera HF/Quartz nist |
|---|---|---|
| TimeBroadcastHostedService | Identity | loop sade 1s |
| GateStatusCheckerService | Gate | poll + SignalR |
| *StartupService device | ACL | event subscribe gRPC |

Inha «always on loop»-an, na queued work item. Eshtebah: hame chiz ro Hangfire koni — overkill.

---

## Extra — BatchSize

Outbox job har tick `BatchSize` row migire (FOR UPDATE). Interval kuchik + BatchSize bozorg = CPU/DB spike. Tune: Interval 2–10s typical; Batch 10–100. Lab ba config.

---

## Map — ACL sync (simplified)

```
UI Sync
  → API
  → ChainDeviceJobs(deviceId, () => SyncPhase1)
  → (done) Continue → SyncPhase2 → …
  → each phase: strategy → gRPC → update SyncStatus → SignalR
```

---

## Map — Quartz outbox tick

```
Quartz trigger (5s)
  → ProcessOutboxJob.Execute
  → open connection + tx
  → batch locked messages
  → foreach: handlers (+ tenant)
  → mark processed/error
  → commit
```

---

## Decision: job-e jadid koja?

| niaz | koja |
|---|---|
| Poll table messaging Dejban | Quartz module job |
| User-clicked long ACL work | Hangfire Enqueue (+ queue) |
| Time-based business RT | Hangfire Recurring + Postgres |
| Har saniye clock | BackgroundService |
| Cross-service event | Outbox → MT, na Hangfire Publish |

---

## Lab aha

1. Stop Quartz hosted (comment) → outbox stuck  
2. Two rapid syncs same device → chain serial  
3. Enable dashboard without password remote → blocked by harden  
4. Drop Memory by restart → jobs vanish  
5. Sweeper: set EndAt past → revert on next cron  

---

## What Day 29 is *not*

- Full rewrite Days 21/23 (faghat trigger side)  
- Hangfire Pro / Redis storage deep  
- Quartz clustering ADO setup step-by-step  
- Cron calendar complex  

Focus: **do stack + Dejban usage + smells**.

---

## Resume keywords (ATS)

`Quartz.NET` · `Hangfire` · `background jobs` · `recurring jobs` · `job chaining` · `IJob` · `cron` · `hosted services` · `PostgreSQL` · `DisallowConcurrentExecution`

---

## Size note — chand job to Dejban?

8 module × (outbox + inbox) ≈ **16** Quartz jobs. Identity/ACL/RT Hangfire joda. To mosahebe adad begu — neshun mide modular scheduling.

---

*Day 29 tamum. Ba'd: Day 30 — Serilog + Seq + OpenTelemetry (amade). Fehrest: [README.md](./README.md).*
