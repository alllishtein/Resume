# Day 02 — C# / .NET runtime: async, concurrency, GC

*Ketabche-ye Dejban stack — style: sade, kamel, berooz — Sep 2026, .NET 10 LTS*

---

## Ye khat kholase

`async` thread-e jadid nemisaze. Ta avalin `await`-e nocomplete, code sync roye haman thread-e. `await` thread ra bar migardone be pool ta I/O tamum she. ASP.NET Core ba in model hezaran request-e baz ra ba chand dah thread handle mikone. Blockage (`.Result`, `ToList()` sync, `lock` round-e await) in model ra mikoshe.

---

# BAKHSH-E AVAL: WORLD — async, concurrency, GC to donya

## Thread vs Task vs async

| | Thread | Task | async method |
|---|---|---|---|
| chiye | OS worker | promise-e kar | compiler state-machine |
| geran? | bale (stack ~1MB) | koochik | state machine + Task |
| CPU-bound | `Task.Run` / `Parallel` | wrapper | async CPU ra parallel nemikone |
| I/O-bound | block — bad | Task az socket/DB | await dorost-e |

Shaye'e-ye ghalat: "async yani background thread." Haghighat: async yani "mitonam await konam." Ta await, haman caller thread.

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

.NET ThreadPool do noe thread dare:

- **Worker threads:** CPU ya continuation-e async
- **I/O completion threads:** callback-e socket/file (IOCP/epoll)

`await npgsql.QueryAsync` → query ferestade mishe → thread azad → Postgres javab → IOCP → Task complete → continuation.

**Starvation:** 100 request harkdum `query.ToList()` sync → 100 worker lock-e Postgres. Request-e 101om bayad saf beishe.

`Task.Run` baraye I/O ziadi thread masraf mikone. Baraye CPU (image resize, hash) ghabul-e.

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

## PagedList — smell-e asli

```csharp
public static async Task<PagedList<T>> CreateAsync(...)
{
    await Task.CompletedTask;          // fake async
    var totalCount = query.Count();    // SYNC!
    var items = query.Skip(...).ToList();  // SYNC!
}
```

Esm `Async`, raftar sync. Thread block mikone. Avvalin fix-e performance zir-e load. Bayad `CountAsync` + `ToListAsync` + CT.

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

Day 02 tamum. Ba'd: Day 03 — OOP + SOLID + patterns. Fehrest: [README.md](./README.md).
