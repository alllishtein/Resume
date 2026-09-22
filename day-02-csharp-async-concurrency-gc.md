# Day 02 — C# / .NET runtime: async, concurrency, GC

*Ketabche-ye Dejban stack — style: sade, kamel, berooz — Sep 2026, .NET 10 LTS*

---

## Ye khat kholase

`async`/`await` to .NET **thread-e jadid nemisaze**. Ta avalin `await`-e ke hanuz complete nashode, code sync roye haman thread-e caller ejra mishe; `await` thread ra bar migardone be ThreadPool ta I/O (Postgres, HTTP, disk) tamum she, ba’d continuation (momkene ru thread-e dige) edame mide. ASP.NET Core ba hamin model hezaran request-e baz ra ba chand dah worker handle mikone — yani scale az «na-block kardan» miad, na az «thread bishtar».

To Dejban in olgu hameja-st: MediatR handlers, EF `*Async`, Channel/SSE, Quartz inbox, gRPC device SDK. Chizi ke model ra mikoshe: sync-over-async (`.Result`, `ToList()` sync to `PagedList.CreateAsync`), CT na-pass shodan, Channel unbounded, ya `lock` round-e `await`. In fasl WORLD-e runtime ra midahad, ba’d smell-ha va pattern-haye Dejban ra pin mikone (.NET 10 LTS).

---

# BAKHSH-E AVAL: WORLD — async, concurrency, GC to donya

## Thread vs Task vs async

Aval bayad se mafhum ra joda koni — aksar hang az mix kardan-e ina miad. **Thread** = OS worker (geran). **Task** = va'de-ye «kar tamam mishe». **async method** = compiler state-machine ke mitone await kone. Shaye'e-ye ghalat: «async yani background thread.» Haghighat: async yani «mitonam await konam» — ta await, haman caller thread.

| | Thread | Task | async method |
|---|---|---|---|
| chiye | OS worker | promise-e kar | compiler state-machine |
| geran? | bale (stack ~1MB) | koochik | state machine + Task |
| CPU-bound | `Task.Run` / `Parallel` | wrapper | async CPU ra parallel nemikone |
| I/O-bound | block — bad | Task az socket/DB | await dorost-e |

ASP.NET request:

```
thread-pool thread
  → endpoint lambda
  → await sender.Send(...)    // thread azad mishe
  → Postgres I/O
  → continuation (momkene thread-e dige)
  → Results.Ok
```

## ThreadPool

.NET ThreadPool do noe thread dare — va fahmidan-e ina key-e scale-e ASP.NET-e:

- **Worker threads:** CPU ya continuation-e async
- **I/O completion threads:** callback-e socket/file (IOCP/epoll)

`await npgsql.QueryAsync` → query ferestade mishe → thread azad → Postgres javab → IOCP → Task complete → continuation. Age be jaye await, sync `ToList()` bezani, worker lock mimone ru Postgres — inja **starvation** shoru mishe: 100 request sync → 100 worker block → request-e 101om saf.

`Task.Run` baraye I/O ziadi thread masraf mikone (fake async). Baraye CPU (image resize, hash) ghabul-e.

## async/await — compiler chi misaze

```csharp
public async Task<string> GetNameAsync(Guid id, CancellationToken ct)
{
    var v = await repo.GetAsync(id, ct);
    return v.FirstName;
}
```

Compiler ye `IAsyncStateMachine` misaze ba `MoveNext()` va switch (state 0, 1, ...). Age Task ghablan complete bashe (cache hit), await yield nemikone — edame roye haman thread.

`async void` **mamnoo'** jox event handler. Exception ra gom mikone, caller nemitone await kone.

## Task, ValueTask, IAsyncEnumerable

**Task<T>** — reference type, allocation. Default-e MediatR/ASP.NET.

**ValueTask<T>** — struct, 0-alloc age sync complete bashe. **Ghanun:** yek bar await, dobar `GetAwaiter()` = undefined. Age 2 consumer mikhay: `.AsTask()`.

**IAsyncEnumerable<T>** — stream. Har item ye await. SSE, gRPC response stream, `await foreach`.

## SynchronizationContext

| | ExecutionContext | SynchronizationContext |
|---|---|---|
| chi | AsyncLocal, Security flow | "koja resume konam" |
| ASP.NET Core | flow mikone | **null** — Kestrel SyncContext nadare |
| WinForms/WPF | flow | dare → `.Result` deadlock |

ASP.NET Core SyncContext nadare → deadlock-e classic kamtar. Hanooz `.Result` thread pool ra **block** mikone → starvation.

## ConfigureAwait — ghanun-e 2026

| code | ghanun |
|---|---|
| Library NuGet | `ConfigureAwait(false)` — deadlock-e UI caller kam |
| ASP.NET Core app | omit; SyncContext nist. OK |
| CA2007 | .NET 10 default disabled baraye app |

.NET 8+ `ConfigureAwaitOptions`: `ForceYielding` (yield hatta age complete), `SuppressThrowing` (rare).

## CancellationToken

Cooperative: code bayad check kone. Cancel = `OperationCanceledException`.

Manabe:

- `HttpContext.RequestAborted` — client tab baste
- `IJobExecutionContext.CancellationToken` — Quartz shutdown
- `StoppingToken` — IHostedService
- `CreateLinkedTokenSource(a, b)` — timeout XOR request

**Ghanun:** CT ra ta akharin IO pass kon: `ToListAsync(ct)`, HttpClient, Dapper.

`Task.WaitAsync(TimeSpan, ct)` (.NET 6+): timeout roye **awaiter**, kar ra stop nemikone. HttpClient `Timeout` + CT behtar.

## sync-over-async: `.Result` / `GetAwaiter().GetResult()`

```csharp
task.Result;              // AggregateException
task.GetAwaiter().GetResult();  // unwrapped exception
```

Chera bad: worker thread block, deadlock ba SyncContext, thread-pool starvation.

Gahi justified: STA thread (COM interop), legacy callback ke sync API mikhad. Vali to web request **hichvaght**.

## Exception handling

`await task` → exception-e aval ra throw (na AggregateException). `Task.Wait()` → AggregateException.

`Task.WhenAll`: hame ra wait; age 2 fail, `await` yeki ra throw. Baghie unobserved. .NET 9+ `Task.WhenEach` behtar.

`Task.Run` + exception: unobserved ta GC. Default terminate nemikone (az .NET 4.5), vali log kon.

## Concurrency vs parallelism

| | concurrency | parallelism |
|---|---|---|
| mani | chand kar dar pishraft (overlap) | chand CPU core hamzaman |
| abzar | async/await, Channel | `Parallel.For`, `Task.Run` × N |
| mesal | 1000 HTTP concurrent | image hash CPU |

`Parallel.ForEachAsync` (.NET 6+) ba `MaxDegreeOfParallelism` baraye bulk. **DbContext per task**, na share.

## Race, deadlock, livelock, starvation

In chahar bug-e concurrency-an ke mosahebe ziad miporse. Be zaban-e sade: race = tartib-e unexpected; deadlock = cycle wait; livelock = retry bi-payan; starvation = kesi resource nemigire.

| bug | mani |
|---|---|
| Race | tartib-e unexpected. Do concurrent MAX+1 bedune lock |
| Deadlock | A wait B, B wait A. `lock` + `.Result`; DB row lock cycle |
| Livelock | retry bi-payan |
| Starvation | kesi hichvaght resource nemigire |

**DbContext race:** SaveChanges az 2 thread = undefined. Scoped per request OK. `Task.WhenAll` + yek context = mamnoo'.

## lock, SemaphoreSlim, Lock (.NET 9+)

### `lock (obj)` / Monitor

Sync, reentrant (haman thread dobar OK). **Mamnoo' round-e await:** compiler error.

### `SemaphoreSlim` — async lock

```csharp
private readonly SemaphoreSlim _lock = new(1, 1);
await _lock.WaitAsync(ct);
try { await SendAsync(); }
finally { _lock.Release(); }
```

`new(1,1)` = mutex-e async. Na reentrant. Deadlock age haman flow dobar Wait.

### `System.Threading.Lock` (.NET 9+)

Type-e jadid, contention metric. `lock (myLock)` pattern matching.

### Advisory lock (Postgres)

`pg_advisory_xact_lock(id)` — cross-instance lock ta commit. Behtar az Mutex-e OS baraye DB operation.

## Channel va backpressure

```csharp
var ch = Channel.CreateBounded<T>(new BoundedChannelOptions(256) {
    FullMode = BoundedChannelFullMode.Wait // ya DropOldest
});
```

Bounded = writer wait mikone age por bashe = backpressure. Unbounded = memory grow age consumer kond bashe.

`SingleReader`/`SingleWriter` optimize.

## IAsyncDisposable

```csharp
await using var connection = await source.OpenConnectionAsync(ct);
await using var transaction = await connection.BeginTransactionAsync(ct);
```

`DisposeAsync` I/O-ye dispose ra async mikone. Prefer `await using` to async method.

## ExecutionStrategy

```csharp
var strategy = context.Database.CreateExecutionStrategy();
await strategy.ExecuteAsync(async () => {
    await using var tx = await context.Database.BeginTransactionAsync(Serializable, ct);
    // ...
    await tx.CommitAsync(ct);
});
```

Retry roye transient (serialization failure, deadlock, network). **Ghanun:** kole transaction dakhele ExecuteAsync.

## Memory model

| abzar | baraye chi |
|---|---|
| `lock` | invariant-e chand field |
| `Interlocked` | counter-e sade |
| `volatile` | flag (weak — kam estefade) |
| `ConcurrentDictionary` | cache-e thread-safe |
| `ImmutableList` | snapshot publish |

`HttpClient` / `NpgsqlDataSource` singleton = thread-safe. Static `List<T>` bedune lock = bug.

## GC: generations, Server, DATAS

### Generations

| gen | chi |
|---|---|
| 0 | short-lived: DTO, state machine, buffer |
| 1 | survive 1 GC |
| 2 | long-lived: singleton, cache |
| LOH | > ~85KB: excel buffer, image |

### Server vs Workstation

- Workstation: 1 heap, latency
- Server: 1 heap per core, throughput. ASP.NET default

### DATAS (.NET 9+ default)

Dynamic Adaptation to Application Sizes:

- Heap size ~ long-lived data, na "har chi RAM bede bala"
- Heap count grow/shrink
- Container-friendly (K8s memory limit + old Server GC = OOM)
- Bursty traffic → memory bargardad

`GC.Collect()` to request path **mamnoo'**.

## IDisposable, LOH, Span

- `IDisposable` + `using` baraye unmanaged/connection
- Finalizer: backup, geran. `GC.SuppressFinalize` ba'd az Dispose
- `Span<T>` / `Memory<T>`: slice bedune copy. Async method `Span` local across await na (ref struct). `Memory<T>` OK
- `ArrayPool<byte>` / `RecyclableMemoryStream` baraye upload-e bozorg → LOH pressure kam

## JS event loop (axios refresh)

Browser: 1 thread + event loop. `await axios` thread nemisaze; callback queue.

```javascript
let refreshPromise = null;
if (!refreshPromise) {
  refreshPromise = client.post(refresh).finally(() => refreshPromise = null);
}
await refreshPromise;
```

100 ta 401-e hamzaman → 1 refresh. In `SemaphoreSlim(1,1)`-e JS-e.

Node: ham event loop. CPU-e sangin loop ra block mikone (mesle `.Result` to .NET).

## Chizayi ke vojud dare vali kam estefade mishe

- **`Parallel.ForEachAsync`** — controlled parallelism ba async
- **`System.Threading.Lock`** (.NET 9+) — contention metrics
- **`ConfigureAwaitOptions`** — ForceYielding, SuppressThrowing
- **`Task.WhenEach`** (.NET 9+) — process results as they complete
- **`PeriodicTimer`** — async-friendly timer (behtar az `System.Timers.Timer`)
- **`IAsyncEnumerable` + LINQ** — `System.Linq.Async`
- **`IDbContextFactory`** — safe parallel EF (be jaye `new DbContext`)
- **`TimeProvider`** — testable time (.NET 8+)
- **`FrozenDictionary`** / `FrozenSet` — immutable + fast lookup (.NET 8+)
- **Pinned Object Heap (POH)** — long-lived pinned buffers

---

# BAKHSH-E DOVOM: DEJBAN — async va concurrency to in proje

In bakhsh WORLD ra be smell va pattern-e exact-e repo link mikone. Avvalin chizi ke zir-e load dard mikone, mamulan sync-over-async-e — va Dejban mesal-e classic dare.

## PagedList — smell-e asli

Esm `CreateAsync`-e, vali raftar sync-e. Yani thread-pool thread ra block mikone — exactly hamun senario-ye starvation ke WORLD goft:

```csharp
public static async Task<PagedList<T>> CreateAsync(...)
{
    await Task.CompletedTask;          // fake async
    var totalCount = query.Count();    // SYNC!
    var items = query.Skip(...).ToList();  // SYNC!
}
```

Avvalin fix-e performance zir-e load: bayad `CountAsync` + `ToListAsync` + CT.

## CancellationToken — nime-kamel

Handler-ha CT daran:

```csharp
public async Task<ErrorOr<...>> Handle(GetVisitReservationsQuery query, CancellationToken ct)
```

Vali endpoint:

```csharp
group.MapGet("", async ([AsParameters] request, ISender sender) =>
{
    var result = await sender.Send(request);  // CT nist!
});
```

MediatR `Send(request, ct)`. Bedune ct = `CancellationToken.None`. User safhe ra mibande, query edame mide.

SSE dorost: `ReadAllAsync(httpContext.RequestAborted)`.

**Fix:** Minimal API `CancellationToken ct` parameter ezafe kon → ASP.NET automatic `RequestAborted` bind mikone. Pass be `Send`.

## Channel — SSE live updates

```csharp
var channel = Channel.CreateUnbounded<VisitScheduleChangeEvent>();
services.AddSingleton(channel);
```

**Unbounded** → `WriteAsync` hichvaght wait nemikone. 10k event, 0 consumer → RAM.

**Singleton reader** → yek SSE client `ReadAllAsync` ra mikhore. Client-e dovom hich event nemibine. Multi-user broadcast **nist**. SignalR/Redis backplane baraye scale.

World: `Channel.CreateBounded<T>(256)` ba `FullMode.Wait`.

## SemaphoreSlim — Tiam SDK

```csharp
private readonly SemaphoreSlim _sendLock = new(1, 1);
await _sendLock.WaitAsync(ct);
try { await SendAsync(); }
finally { _sendLock.Release(); }
```

Device SDK single-threaded → serialize-e async calls. Dorost-e.

## ZK SDK — STA thread

```csharp
foreach (var operation in _channel.Reader.ReadAllAsync().ToBlockingEnumerable())
{
    operation(_zkInstance).GetAwaiter().GetResult();
}
```

CZKEM COM/STA: bayad haman thread. Channel az thread-haye dige Write, STA Read + block. Pattern-e thread affinity. Justified-e vali to mosahebe tradeoff ra tozih bede.

## Advisory lock — parking

```csharp
await context.Database.ExecuteSqlRawAsync(
    "SELECT pg_advisory_xact_lock({0})", [lockKey], cancellationToken);
```

Cross-instance lock baraye parking occupancy. Behtar az in-process lock chon chand instance momkene. Lock ta commit.

## WhenAll — Identity sync

```csharp
var responses = await Task.WhenAll(tasks);
```

Fan-out be chand service. `SafeRequestAsync` null bar migardone be jaye throw — fail-soft. Na WhenAll-fail-fast.

## Reporting — GetResult smell

```csharp
.GetAwaiter().GetResult();
ReadAsByteArrayAsync().GetAwaiter().GetResult();
```

Stimulsoft legacy callback. Sync-over-async. "Legacy callback; would prefer async all the way."

## Card generator — ExecutionStrategy

```csharp
var strategy = context.Database.CreateExecutionStrategy();
await strategy.ExecuteAsync(async () => {
    await using var tx = await context.Database.BeginTransactionAsync(Serializable, ct);
    // ... MAX+1 ...
    await tx.CommitAsync(ct);
});
```

Plus `DbUpdateException` loop-e dasti 10 bar. Do sath retry. World: strategy kafi + SEQUENCE.

New DbContext misaze — joda az request scope. `await using` dispose. OK vali `IDbContextFactory` idiomatic-e .NET 10.

## lock-haye sync

```csharp
lock (LockObject) { ... }       // Reporting cache
lock (window.Gate)               // PlateReader rate limiter  
lock (_onlineTerminalsLock)      // Tiam online list
```

Kootah critical section-ha. World-OK. `System.Threading.Lock` jadid-tar vali `object` lock ghabul-e.

## Smell-ha

1. **PagedList.CreateAsync fake-async** — avvalin fix
2. **Reservations Send bedune CT** — disconnect cancel nemikone
3. **Channel unbounded + singleton reader** — scale/RAM risk
4. **Reporting GetResult** — sync-over-async
5. **ZK ToBlockingEnumerable** — justified STA vali isolate
6. **Tiam SemaphoreSlim + lock mix** — document kon
7. **Inbox handler dakhele transaction** — lock duration × async I/O
8. **ConfigureAwait nist** — baraye Kestrel OK, Common library edge case
9. **new DbContext** — OK vali IDbContextFactory idiomatic-tar
10. **WhenAll + null swallow** — fail-soft, timeout check kon

## 25 soal-e mosahabe

1. async thread misaze? — na, state machine + await I/O
2. Task vs Thread? — Task = work unit; Thread = OS worker
3. chera async I/O? — thread azad; scale
4. ValueTask? — 0-alloc sync hit; yek bar await
5. async void? — mamnoo' jox event
6. ConfigureAwait(false)? — library; ASP.NET Core omit
7. SyncContext to ASP.NET Core? — nist
8. `.Result` chera bad? — block + starvation
9. CT cooperative? — bale; IO bayad pass
10. WaitAsync task ra cancel mikone? — na, waiter ra
11. lock across await? — compile error; SemaphoreSlim
12. DbContext thread-safe? — na
13. WhenAll vs WhenAny? — hame vs avalin
14. Channel bounded chera? — backpressure
15. DATAS? — GC heap ~ live data; .NET 9+ default
16. gen0 vs LOH? — short vs >85KB
17. Server vs Workstation GC? — throughput vs latency
18. Race vs deadlock? — tartib-e wrong vs cycle wait
19. Advisory lock? — Postgres lock-e manteqi
20. IAsyncEnumerable? — stream async; SSE/gRPC
21. ExecutionStrategy? — retry transient, whole tx inside
22. ThreadPool starvation? — sync-over-async zir-e load
23. Single-flight? — yek in-flight refresh (axios / SemaphoreSlim)
24. STA + async? — marshaling; GetResult roye haman thread
25. IAsyncDisposable? — dispose-e I/O bedune block

## Resume

**short:**

> Built high-concurrency ASP.NET Core (.NET 10) services using async I/O end-to-end, Channels/SSE for live updates, PostgreSQL advisory locks and Serializable retries for contended writes, with awareness of DATAS GC and thread-pool starvation pitfalls.

**bullets:**

- Propagated cancellation on background jobs and SSE (RequestAborted / Quartz tokens); identified paths missing CT on MediatR Send
- Isolated device-SDK STA threads via Channel + blocking pump; used SemaphoreSlim for async send serialization
- Multi-service fan-out with Task.WhenAll; in-process occupancy with pg_advisory_xact_lock

**skills:** `C#, .NET 10, async/await, ThreadPool, Channels, CancellationToken, locks, GC/DATAS, ValueTask`

## File-haye mohem

| chi | koja |
|---|---|
| PagedList | `Common/Abstractions/Queries/PagedList.cs` |
| Channel + SSE | `VisitorsModule.cs`, `GetVisitScheduleLiveUpdates.cs` |
| CT missing | `VisitReservationEndpoints.cs` |
| Serializable retry | `VisitorCardNumberGenerator.cs` |
| SemaphoreSlim | `TiamGrpcServer/SDK/TiamSdkWrapper.cs` |
| STA pump | `ZKGrpcServer/SDK/Contracts/ZKContracts.cs` |
| WhenAll | `IdentityServer/.../EndpointSyncService.cs` |
| Advisory lock | `ACLServer/.../EfParkingOccupancyStore.cs` |
| GetResult | `Reporting/Infrastructure/ReportRepository.cs` |
| Axios refresh | `packages/api-client/src/axiosInstance.ts` |

---

## ConfigureAwait — deep dive (library vs app)

Age ye NuGet package minevisi ke `await http.GetAsync` dare, caller mitone WinForms/WPF bashe. Ba `ConfigureAwait(true)` (default), continuation roye UI thread mikhad resume she. Age caller sync block kone (`.Result`), deadlock.

```csharp
// Common library pattern
public async Task<T?> GetJsonAsync<T>(Uri url, CancellationToken ct)
{
    using var response = await _http.GetAsync(url, ct).ConfigureAwait(false);
    return await response.Content.ReadFromJsonAsync<T>(ct).ConfigureAwait(false);
}
```

To **Dejban.Api** (Kestrel): SyncContext null → `ConfigureAwait(false)` optional. Vali `Dejban.Common.*` packages age ba tool dige reuse shan, `false` defensive-e.

**Anti-pattern:** `ConfigureAwait(false)` to har line + comment spam. Faghat library public API.

---

## Parallel.ForEachAsync — bulk I/O ba control

.NET 6+:

```csharp
await Parallel.ForEachAsync(
    deviceIds,
    new ParallelOptions { MaxDegreeOfParallelism = 4, CancellationToken = ct },
    async (deviceId, token) =>
    {
        await using var scope = scopeFactory.CreateAsyncScope();
        var sender = scope.ServiceProvider.GetRequiredService<IDeviceClient>();
        await sender.PushAsync(deviceId, payload, token);
    });
```

**Ghanun-ha:**

| rule | dalil |
|---|---|
| Har iteration **DbContext joda** | DbContext thread-safe nist |
| `MaxDegreeOfParallelism` set kon | nabayad 10k task hamzaman besaze |
| CT pass kon | shutdown/cancel |
| Na baraye CPU sangin | baraye CPU `Parallel.For` / `Task.Run` + limit |

Dejban: fan-out-e device sync mitone in pattern dashte bashe; ziad fan-out ba `Task.WhenAll` roye list-e koochik (Identity endpoint sync).

---

## ValueTask — ke vaght arzesh dare

```csharp
public ValueTask<Personnel?> GetCachedAsync(Guid id, CancellationToken ct)
{
    if (_cache.TryGetValue(id, out Personnel? p))
        return ValueTask.FromResult(p);  // 0 allocation
    return new ValueTask<Personnel?>(LoadFromDbAsync(id, ct));
}
```

**Pitfall:** consumer dobar await kone roye haman ValueTask → undefined. Age multiple awaiters: `.AsTask()`.

MediatR handlers `Task<T>` return — OK. ValueTask baraye hot path cache/repository ke 80% sync hit.

---

## IAsyncEnumerable — pagination va stream

```csharp
public async IAsyncEnumerable<VisitorDto> StreamVisitors(
    IQueryable<Visitor> query,
    [EnumeratorCancellation] CancellationToken ct = default)
{
    await foreach (var row in query.AsAsyncEnumerable().WithCancellation(ct))
    {
        yield return Map(row);
    }
}
```

Minimal API:

```csharp
return TypedResults.Ok(stream); // ya Results.Stream
```

Dejban SSE (`GetVisitScheduleLiveUpdates`) az **Channel** estefade mikone, na `IAsyncEnumerable` az DB — vali mental model yeki: producer/consumer async.

`[EnumeratorCancellation]` → compiler CT ro be `WithCancellation` pass mikone.

---

## CancellationToken — checklist-e production

| layer | manba | pass be |
|---|---|---|
| HTTP | `CancellationToken ct` param | `sender.Send(cmd, ct)` |
| MediatR handler | `Handle(..., CancellationToken ct)` | repo `ToListAsync(ct)`, HttpClient |
| Quartz job | `context.CancellationToken` | loop + IO |
| HostedService | `stoppingToken` | background loop |
| MassTransit consumer | `ConsumeContext.CancellationToken` | handler + EF |
| Linked | `CreateLinkedTokenSource(userCt, timeoutCt)` | har do cancel → stop |

**Smell:** `CancellationToken.None` implicit chon parameter nadashtim.

**Npgsql:** query cancel → connection state check. Gahi better retry transient.

**Cooperative cancel:** loop-haye bozorg `ct.ThrowIfCancellationRequested()` har N iteration.

Fix pattern baraye Minimal API:

```csharp
group.MapGet("", async ([AsParameters] Q q, ISender sender, CancellationToken ct) =>
{
    var result = await sender.Send(q, ct);
    return result.Match(Results.Ok, ApiResults.Problem);
});
```

---

## ThreadPool starvation — senario-ye real

```
100 concurrent request
  → har kodam PagedList.CreateAsync
  → Count() + ToList() SYNC roye thread pool
  → 100 worker block roye Postgres
  → request 101+ saf (QueueUserWorkItem)
  → latency spike, health check fail, cascade
```

**Symptoms:** `ThreadPool.SetMinThreads` workaround (bad). `dotnet-counters` ThreadPool queue length bala. CPU kam, latency bala.

**Fix hierarchy:**

1. Async ta akhar (`*Async` + CT)
2. Kam kardan sync-over-async
3. `Task.Run` faghat CPU, na I/O
4. Scale out (moagagat) — root cause hanooz sync

---

## GC — LOH, POH, fragmentation

**LOH (> ~85KB):** object roye Large Object Heap. Gen2 collect geran. Excel export buffer, `byte[]` bozorg.

**Mitigation:** `ArrayPool<byte>`, chunk kardan, stream be client.

**POH (.NET 5+):** pinned buffers (network/GC interaction). Kam to app-level.

**Fragmentation:** long-running process + LOH allocate/free → memory hold. Container limit + DATAS mitone help kone.

**Metrics:** `dotnet-gcdump`, EventPipe GC collections, `% Time in GC` < ~10% ideal.

**Interview:** «Chera `GC.Collect()` bad?» — force full collect, pause request path, mask leak.

---

## MassTransit + async to Dejban

Consumer pattern:

```csharp
public async Task Consume(ConsumeContext<PersonnelCreatedIntegrationEvent> context)
{
    await handler.Handle(context.Message, context.CancellationToken);
}
```

Inbox job (`ProcessInboxJob`) **async end-to-end** — `OpenConnectionAsync`, `BeginTransactionAsync`, `CommitAsync`, handler-ha ba CT.

**Smell:** inbox loop + `foreach` sequential — throughput limited. Parallel consume = `SKIP LOCKED` (Day 04) + careful tenant scope per message.

Outbox publish **sync ba SaveChanges** — same transaction; async after commit baraye dispatch.

---

## EF Core async — pattern va anti-pattern

| dorost | ghalat |
|---|---|
| `await db.Visitors.ToListAsync(ct)` | `db.Visitors.ToList()` |
| `await query.CountAsync(ct)` | `query.Count()` |
| `await SaveChangesAsync(ct)` | `SaveChanges()` |
| `AsNoTracking()` baraye read | tracked list 10k row |
| `SingleOrDefaultAsync` | `FirstOrDefault` sync |

**Include graph:** `GetByIdAsync` ba Include to repo — 1 round-trip. Handler `GetQueryable().Include(...)` — same, vali leak.

**Compiled queries:** hot path list — optional optimization.

---

## Debug checklist («request hang / CPU 0% / timeout»)

1. Thread dump — worker block roye `Monitor.Wait` / Npgsql?
2. Sync `ToList()` to hot path?
3. `.Result` / `Wait()` to stack?
4. DbContext shared between `Task.WhenAll` branches?
5. Unbounded Channel RAM?
6. Lock held during network I/O?
7. CT pass shode? Client disconnect server edame mide?
8. Pool exhaustion — connection + thread?
9. Serializable retry loop bi-payan?
10. STA pump queue backlog?

---

## Senario whiteboard

### A) User tab bast — query edame?

Endpoint bedune CT → query tamum. Fix: `CancellationToken ct` → MediatR → EF.

### B) Do handler hamzaman yek Visitor update

Yek DbContext per request OK. **Na** 2 request = race; optimistic concurrency / domain rule.

### C) Refresh token single-flight

Frontend `refreshPromise` (axios) = SemaphoreSlim(1,1) — 100×401 → 1 refresh.

### D) Card number race

Serializable + retry + ExecutionStrategy — world alternative: `nextval('card_seq')`.

---

## Mini lab (1 session, ~90 min)

1. `PagedList.cs` bekhoon — `Count()` sync ra trace kon ba breakpoint.
2. Yek `GetVisitorsQueryHandler` — `AsNoTracking` + projection.
3. `ProcessInboxJob.cs` — async transaction flow.
4. `TiamSdkWrapper.cs` — SemaphoreSlim around send.
5. `dotnet-counters monitor --counters System.Runtime` — under load test (local) ThreadPool queue.
6. Network tab: request cancel (Abort) — backend CT wired? (identify gap on reservations endpoint)
7. Optional: rewrite one `CreateAsync` call site ba `CountAsync`/`ToListAsync` mentally — chi avaz mishe?

---

## 15 soal-e ezafe (mosahebe)

26. `Parallel.ForEachAsync` vs `Task.WhenAll`? — built-in throttling vs manual list tasks
27. `[EnumeratorCancellation]`? — IAsyncEnumerable CT wiring
28. `IAsyncDisposable` vs `using`? — async dispose path
29. `ExecutionContext` vs `AsyncLocal`? — flow vs tenant (Day 16)
30. Chera `Task.Run` to ASP.NET request bad? — pool steal baraye fake async
31. `ValueTask` pool? — .NET 7+ pooling for async paths
32. `ConfigureAwaitOptions.ForceYielding`? — always yield even sync complete
33. `PeriodicTimer` vs `Timer`? — async await friendly
34. `IDbContextFactory` vs scoped? — parallel work / background
35. Channel `SingleReader`? — perf when true
36. `pg_advisory_xact_lock` vs app Mutex? — cross-pod DB lock
37. `DisallowConcurrentExecution` Quartz? — no overlap same job
38. `IOCP` role? — complete async socket without blocking thread
39. DATAS vs fixed Server heap? — adapt to live set in container
40. `FrozenDictionary` + async? — sync read after build; build once at startup

---

## Chejori digest koni

1. World: thread vs task diagram (10 min)
2. Trace yek GET visitor: endpoint → MediatR → EF (15 min)
3. List 5 smell Dejban + fix (10 min)
4. 25+15 soal boland (25 min)
5. GC generations + LOH mesal (10 min)
6. Mini lab items 1–3 (30 min)

---

## Resume — paragraph-e boland (optional)

> Operated async-first ASP.NET Core services where performance under load depended on eliminating sync-over-async (PagedList, legacy reporting), propagating `CancellationToken` from HTTP and Quartz through MediatR to Npgsql, and using Channels for live SSE with awareness of unbounded-buffer risks. Applied PostgreSQL advisory transaction locks and EF `ExecutionStrategy` with Serializable isolation for contended sequences, isolated STA device SDK work via dedicated pump threads, and used `SemaphoreSlim` for single-flight device SDK calls—while monitoring thread-pool queue depth and DATAS GC behavior in containerized deployments.

---

Day 02 tamum. Ba'd: Day 03 — OOP + SOLID + patterns. Fehrest: [README.md](./README.md).
