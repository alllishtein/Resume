# Day 61 — Postgres LISTEN / NOTIFY

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**PostgreSQL LISTEN/NOTIFY** mekanism-e native-e Postgres-e baraye pub/sub-e sabok-e dakhel-e database. Ye trigger ba'd az INSERT to jadval `pg_notify(channel, payload)` seda mizane, va ye `BackgroundService` to app ke `LISTEN channel` karde va ru-ye ye Npgsql connection `WaitAsync` mikone, notification ro migire va az tarigh-e `IHubContext` be SignalR client-ha push mikone. In pattern vaghti write path to database-e (masalan az tarigh-e trigger ya ye service-ye dge ke mostaghim SQL mizane) va app-layer azash khabar nadare, kheili arzeshman-e — chon SignalR push-e ba'd az `SaveChanges` faghat vaghti kar mikone ke **khodesh** save karde bashe. Dejban in ro baraye **plate reader access logs** piyade karde: vaghti ye vehicle access log ba `AccessMethod = 'PlateReader'` insert mishe, trigger fire mikone, BackgroundService migire, va realtime be UI push mikone.

---

# BAKHSH-E AVAL: WORLD — chera LISTEN/NOTIFY

## Farz kon

Farz kon ye apartment dari va mikhay beduni key zang-e dar mikhoresh. Do ta rah dari: ya har 1 sanie dari az panjereh biroone negah mikoni (polling), ya ye zang-e dar nasb mikoni ke feshar dade beshe seda mide (notify). Polling resource mikhore va latency dare — momkene ye nafar biad va 900 millisecond montazer bemune ta to dobare negah koni. Zang-e dar instant-e — hamun lahze-i ke feshar dade beshe seda mide. LISTEN/NOTIFY hamun zang-e dar-e Postgres-e.

## Yani chi — flow-e kamel

```
                                                  ┌─────────────┐
┌──────────┐    INSERT    ┌────────────┐  trigger  │  pg_notify   │
│  Writer   │────────────▶│   Table    │──────────▶│ (channel,    │
│ (any app) │             │            │           │  payload)    │
└──────────┘              └────────────┘           └──────┬──────┘
                                                          │
                                                 Postgres IPC
                                                          │
                                              ┌───────────▼──────────┐
                                              │ Npgsql Connection    │
                                              │ LISTEN channel       │
                                              │ WaitAsync()          │
                                              │ Notification += ...  │
                                              └───────────┬──────────┘
                                                          │
                                              ┌───────────▼──────────┐
                                              │ BackgroundService    │
                                              │ → scope + repo       │
                                              │ → IHubContext push    │
                                              └──────────────────────┘
```

1. Har writer-i (app-e khodet, ye service-ye dge, ya hatta ye manual SQL) to jadval INSERT mikone
2. Trigger-e `AFTER INSERT` ba shart-e `WHEN (condition)` fire mishe
3. `pg_notify(channel_name, payload)` seda zade mishe — payload ma'mulan ID-e row-e (sabk negahsh dar)
4. Npgsql connection-i ke `LISTEN channel_name` ejra karde va `WaitAsync` mikone, notification ro migire
5. Notification handler (`OnNotification`) payload ro parse mikone (Guid) va az repo row ro mikhoone
6. `IHubContext` result ro be SignalR client-ha push mikone

**Chera payload faghat ID-e?** Chon pg_notify payload size limit dare (~8000 byte) va age kamel-e row ro befrestim, ham size problem dare ham sensitive data leak mishe. Behtar-e faghat ID befrestim va app khodesh az DB bekhoone.

---

## Chera LISTEN/NOTIFY — moghayese ba alternative-ha

| approach | latency | complexity | writer coupling | resource |
|---|---|---|---|---|
| **Polling** (har N sanie SELECT) | N/2 avg | kam | hich | CPU/IO waste |
| **SignalR ba'd az SaveChanges** | < 100ms | kam | write path bayad to app bashe | minimal |
| **LISTEN/NOTIFY** | ~instant | moderate | hich — trigger-e DB | dedicated connection |
| **Logical replication / Debezium** | < 1s | ziad | hich | infra-e sangin |

### Polling — sade vali waste-e

```csharp
while (!ct.IsCancellationRequested)
{
    var newRows = await repo.GetUnprocessedAsync();
    foreach (var row in newRows) await hub.Clients.All.NewData(row);
    await Task.Delay(1000, ct);
}
```

Kar mikone, vali:
- Latency-e worst-case = interval time (1s inja)
- DB load: har sanie ye query, hatta vaghti hich data-ye jadidi nist
- Age interval kuchik koni, load bala mire; age bozorg koni, latency bala mire

### SignalR ba'd az SaveChanges — age hame-ye write to app bashe

```csharp
await dbContext.SaveChangesAsync();
await hub.Clients.All.NewAccessLog(dto);
```

Sade-tar-in-e — vali **faghat** vaghti write path to khodesh app-e kar mikone. Age ye service-e dge mostaghim to DB insert kone (masalan ye third-party tool, ya ye trigger-e dge), in push-e miss mishe.

### LISTEN/NOTIFY — DB-native event

**Key estefade beshe:**
- Write path kamelan to app nist (masalan multiple writer ya trigger-based insert)
- Mikhay az DB-level event-ha react koni
- Latency bayad kam bashe vali Debezium overkill-e

### Debezium / Logical replication — CDC-e sangin

Debezium ye kamel-e infrastructure dare: Kafka, connector config, schema registry. Baraye ye jadval-e sade overkill-e — vali age chand-sad jadval ro mikhay track koni ya cross-database sync dari, Debezium arzeshmand-e.

---

## Postgres LISTEN/NOTIFY — mekanik-e dakheli

### pg_notify function

```sql
PERFORM pg_notify('channel_name', 'payload_text');
```

- `channel_name`: esm-e channel ke listener-ha gabl-an LISTEN kardan
- `payload_text`: string-e ke ta 8000 byte mishe bashe (az Postgres 9.0+)
- Notification faghat ba'd az **commit-e transaction** deliver mishe — age transaction rollback kone, notify nemire

### LISTEN command

```sql
LISTEN channel_name;
```

Ru-ye ye connection-e baz ejra mishe. Az in lahze, har `pg_notify` ke ru-ye in channel bashe, be in connection miad.

### Connection-e dedicated

**Kheili mohem:** connection-i ke `LISTEN` karde, bayad **baz bemune** va **az EF pool estefade nashe**. Chera? Chon age connection be pool bargarde va reuse beshe, LISTEN-esh gom mishe. Dejban ye `NpgsqlConnection`-e jadid ba `using` to BackgroundService misaze ke ta zamani ke cancel nashe baz mimune:

```csharp
using var connection = new NpgsqlConnection(_connectionString);
await connection.OpenAsync(stoppingToken);
using var listenCommand = new NpgsqlCommand($"LISTEN {ChannelName}", connection);
await listenCommand.ExecuteNonQueryAsync(stoppingToken);
```

In connection az EF pool **joda-st** — `_connectionString` ro mostaghim az config mikhoone, na az `DbContext`.

### WaitAsync — blocking-e async

```csharp
while (!stoppingToken.IsCancellationRequested)
{
    await connection.WaitAsync(stoppingToken);
}
```

`WaitAsync` ta vaghti ke notification biad **block mikone** (async — thread azad-e). Vaghti notification biad, return mikone va loop edame mide. Age connection ghat beshe ya error bede, exception throw mishe va outer catch handle mikone.

---

## Trigger-e Dejban — deep dive

```sql
CREATE OR REPLACE FUNCTION notify_platereader_vehicle_access_logs()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM pg_notify(
        'platereader_vehicle_access_logs',
        NEW."Id"::text
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_platereader_vehicle_access_logs_notify
AFTER INSERT ON public."VehicleAccessLogs"
FOR EACH ROW
WHEN (NEW."AccessMethod" = 'PlateReader')
EXECUTE FUNCTION notify_platereader_vehicle_access_logs();
```

**Nokte-haye mohem:**

- **AFTER INSERT** — na BEFORE. Yani row ghablan insert shode va commit momkene hanuz nashode bashe (notify ba'd az commit mire)
- **FOR EACH ROW** — baraye har row-e insert-shode joda fire mishe
- **WHEN condition** — faghat vaghti `AccessMethod = 'PlateReader'` bashe fire mishe — access log-haye dge (card, fingerprint, ...) trigger ro fire nemikonan
- **`NEW."Id"::text`** — faghat ID-e row ferestad mishe, na kamel-e row. In sabke, secure-e, va az payload limit prob naist
- **`PERFORM`** be ja-ye `SELECT` — chon natije-ye `pg_notify` ro niaz nadarim, `PERFORM` result ro discard mikone

### Chera "PlateReader" filter?

Chon access log jadval-e bozorgi-e ke card swipe, fingerprint, face recognition, va plate reader hame ro negah midare. Faghat plate reader event-ha niyaz be realtime push daran (baraye operator-e plate reader ke dashboard-esh baz-e). Card/finger event-ha az tarigh-e dge (ACL device hub, Day 26) push mishan.

---

# BAKHSH-E DOVOM: DEJBAN — PlateReaderNotifyHostedService

## Kamel-e BackgroundService

```csharp
public sealed class PlateReaderNotifyHostedService : BackgroundService
{
    private const string ChannelName = "platereader_vehicle_access_logs";

    private readonly ILogger<PlateReaderNotifyHostedService> _logger;
    private readonly IHubContext<PlateReaderHub, IPlateReaderHubClient> _plateReaderHub;
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly string _connectionString;

    public PlateReaderNotifyHostedService(
        ILogger<PlateReaderNotifyHostedService> logger,
        IHubContext<PlateReaderHub, IPlateReaderHubClient> plateReaderHub,
        IServiceScopeFactory scopeFactory,
        IConfiguration configuration)
    {
        _logger = logger;
        _plateReaderHub = plateReaderHub;
        _scopeFactory = scopeFactory;
        _connectionString = configuration.GetConnectionString("Postgres")
            ?? throw new InvalidOperationException("...");
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                using var connection = new NpgsqlConnection(_connectionString);
                await connection.OpenAsync(stoppingToken);

                using var listenCommand = new NpgsqlCommand($"LISTEN {ChannelName}", connection);
                await listenCommand.ExecuteNonQueryAsync(stoppingToken);

                connection.Notification += OnNotification;
                _logger.LogInformation("Listening to channel '{Channel}'", ChannelName);

                while (!stoppingToken.IsCancellationRequested)
                {
                    await connection.WaitAsync(stoppingToken);
                }
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception exception)
            {
                _logger.LogError(exception, "pg_notify listener failed");
                try
                {
                    await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
                }
                catch (OperationCanceledException) { break; }
            }
        }
    }
```

### Reconnect loop — 5 second delay

Age connection ghat beshe (DB restart, network glitch, Postgres crash), outer catch migire va **5 sanie** montazer mishe ghabl az reconnect. In pattern-e mohem-e:

- Bedun-e delay, age DB down bashe, service beshomari bar retry mikone va log spam mikone
- 5 sanie ye trade-off-e: kamtar az in, spam; bishtar az in, latency-e recovery bala mire
- `Task.Delay` khodesh `stoppingToken` dashte bashe — age app shutdown beshe, delay skip mishe

### OperationCanceledException handling

Do ja cancel check dare:
1. `WaitAsync(stoppingToken)` — vaghti app shutdown mikone, stoppingToken cancel mishe va `WaitAsync` throw mikone
2. `Task.Delay(5s, stoppingToken)` — vaghti to delay hasteye va app shutdown mikone, in ham cancel mishe

Har do ja `OperationCanceledException` catch mishe va `break` mizane — clean shutdown.

---

## OnNotification handler

```csharp
private void OnNotification(object? sender, NpgsqlNotificationEventArgs notification)
{
    if (notification is null || string.IsNullOrWhiteSpace(notification.Payload))
        return;

    if (!Guid.TryParse(notification.Payload.Trim(), out Guid accessLogId))
    {
        _logger.LogWarning("Payload is not a valid Guid: {Payload}", notification.Payload);
        return;
    }

    _ = ForwardAccessLogAsync(accessLogId);
}
```

**Nokte-ha:**

- **Fire-and-forget:** `_ = ForwardAccessLogAsync(...)` — hich `await`-i nist. Chera? Chon `OnNotification` ye event handler-e ke ru-ye Npgsql-e internal thread run mishe va nabayad block beshe. Agar await bokoni, `WaitAsync`-e ba'd delay mikhore
- **Guard clauses:** null check + `Guid.TryParse` — age payload eshtebah bashe ya format avaz beshe, log mikone va skip mikone (na crash)
- **Trim:** device-ha ya trigger momkene whitespace ezafe konan

---

## ForwardAccessLogAsync — scope + repo + push

```csharp
private async Task ForwardAccessLogAsync(Guid accessLogId)
{
    try
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        IPlateReaderAccessLogRepository repository =
            scope.ServiceProvider.GetRequiredService<IPlateReaderAccessLogRepository>();

        PlateReaderVehicleAccessLogDto? model =
            await repository.GetForRealtimeAsync(accessLogId);

        if (model is null)
        {
            _logger.LogWarning("Access log {Id} not found after notify", accessLogId);
            return;
        }

        await _plateReaderHub.Clients.All.RealtimePlateReaderAccessLogs(model);
    }
    catch (Exception exception)
    {
        _logger.LogError(exception, "Failed to forward access log {Id}", accessLogId);
    }
}
```

**Zincir:**

1. **Scope sakhtan:** BackgroundService singleton-e — `DbContext` (scoped) ro mostaghim nemitune inject kone. Pas baraye har notification ye scope misaze
2. **Repository resolve:** `IPlateReaderAccessLogRepository` az scope migire — in repository `GetForRealtimeAsync` dare ke row ro ba ID mikhoone
3. **Null check:** age row peida nashe (masalan race condition — trigger fire shode vali transaction rollback shode), log mikone va skip mikone
4. **Hub push:** `_plateReaderHub.Clients.All.RealtimePlateReaderAccessLogs(model)` — be **hame-ye** connected client-ha push mikone

### GetForRealtimeAsync — chi mikhoone

```csharp
public Task<PlateReaderVehicleAccessLogDto?> GetForRealtimeAsync(Guid id, ...)
    => context.VehicleAccessLogs
        .IgnoreQueryFilters([GlobalQueryFilterNames.TenantFilter])
        .AsNoTracking()
        .Where(al => al.Id == id)
        .Select(al => new PlateReaderVehicleAccessLogDto
        {
            Id = al.Id,
            TagId = al.TagId,
            SiteId = al.SiteId,
            Plate = al.Plate,
            OwnerName = al.OwnerName,
            DriverName = al.DriverName,
            TrafficMode = al.TrafficMode,
            DoorName = al.DoorName,
            DateTime = al.DateTime,
            // ...
        })
        .FirstOrDefaultAsync(cancellationToken);
```

**Nokte-ha:**
- **`IgnoreQueryFilters(TenantFilter)`** — trigger az har tenant-i fire mishe, filter-e tenant nabayad block kone
- **`AsNoTracking`** — read-only, performance
- **Manual projection** (na `Adapt`) — chon khodesho kam dare va mikhad control-e kamel dashte bashe
- **`Select` to query** — faghat field-haye lazem SELECT mishe, na kamel-e entity

---

## Smell-ha va risk-ha

1. **`Clients.All`** — hame-ye connected client-ha event migiran, hatta age operator-e site-ye dge bashan. Baraye multi-tenant bayad Group-e site dashte bashe (mesle ManualAccessHub to Day 26)
2. **Fire-and-forget `_ = ForwardAccessLogAsync`** — age exception throw beshe, faghat log mishe va gom mishe. Baraye critical data, bayad retry ya dead-letter pattern dashte bashi
3. **Race condition:** trigger fire mishe vali transaction hanuz commit nashode → `GetForRealtimeAsync` null bargardune → log warning va miss. In rare-e vali momkene — ye retry ba short delay solve-esh mikone
4. **Single connection:** age network glitch bede, 5 sanie delay dare ghabl az reconnect — to in 5 sanie notification-ha miss mishan (at-most-once delivery)
5. **No backpressure:** age 1000 ta notification ye lahze biad, 1000 ta `ForwardAccessLogAsync` concurrent fire mishan — memory/thread pressure
6. **Payload size:** alan faghat ID mifrestim (safe), vali age kasi trigger ro avaz kone va kamel-e row befreshe, 8KB limit-e Postgres momkene zarbe bezane

---

## Masir-e vaghei — az camera ta browser

Baraye inke kamel-e zincir ro dark koni, in masir ro donbal kon:

```
1. Camera aks-e pelak migire → plate reader agent process mikone
2. Agent POST /api/v1/VehicleAccess be ACLServer (ya mostaghim insert)
3. ACLServer handler:
   a. Validate (pelak format, site exists, ...)
   b. VehicleAccessLog.Create(plate, method: "PlateReader", ...)
   c. context.VehicleAccessLogs.Add(log)
   d. await context.SaveChangesAsync()
      → Transaction commit → trigger fire mishe
      → pg_notify('platereader_vehicle_access_logs', log.Id::text)
4. Notification az Postgres be Npgsql connection miad
5. PlateReaderNotifyHostedService.OnNotification:
   a. Guid.TryParse(payload)
   b. _ = ForwardAccessLogAsync(accessLogId)
6. ForwardAccessLogAsync:
   a. scope.ServiceProvider.GetRequiredService<IPlateReaderAccessLogRepository>()
   b. repository.GetForRealtimeAsync(accessLogId)
   c. _plateReaderHub.Clients.All.RealtimePlateReaderAccessLogs(model)
7. SignalR WebSocket → browser-e operator
8. FE component update mishe → pelak va aks neshun dade mishe
```

**Total latency:** ma'mulan < 100ms az commit ta browser update. Compare ba polling ke worst-case = poll interval (1-5 sanie ma'mulan).

---

## Sequence diagram — notification flow

```
Camera      Agent       ACLServer     PostgreSQL    HostedService    PlateReaderHub    Browser
  │           │            │              │              │                │               │
  │──aks────▶│            │              │              │                │               │
  │           │──POST────▶│              │              │                │               │
  │           │            │──INSERT─────▶│              │                │               │
  │           │            │              │──COMMIT──▶  │                │               │
  │           │            │              │──pg_notify──▶│                │               │
  │           │            │              │              │──GetForRealtime│               │
  │           │            │              │◀─────────────│                │               │
  │           │            │              │              │──Clients.All──▶│               │
  │           │            │              │              │                │──WS push─────▶│
```

---

## Deep dive — pg_notify va transaction isolation

Ye nokte-ye kheili mohem: `pg_notify` **ba'd az commit-e transaction** deliver mishe, na hamun lahze ke `PERFORM pg_notify(...)` call mishe. In yani:

1. Age transaction rollback beshe, notification **hargez** nemire — dorost
2. Age transaction tulani bashe (masalan 5 sanie chon lock-e sangin dare), notification ba 5 sanie delay mire
3. Age `pg_notify` dakhel-e ye `AFTER INSERT` trigger bashe va INSERT to ye bozorg transaction bashe ke chand ta operation dge ham dare, notification ba'd az kamel-e transaction commit mire

In **khobie** chon guarantee mikone ke listener data ro mikhune ke **committed** bashe. Vali moshkel-e latency-e mumkene — age transaction-ha tulani bashan, realtime-e ta bud kharab mishe.

---

## Deep dive — behavior vaghti hich listener-i nist

Age `pg_notify` seda zade beshe vali **hich connection-i** LISTEN nakarde:
- Notification **gom mishe** — Postgres hich queue-i baraye notification nadare
- Hich error-i ham nemide
- Resource waste ham nadare

In farghe bozorg ba message broker (RabbitMQ, Kafka) ke message ta consumer biad negah midaran. pg_notify ye **ephemeral** notification system-e — farz mikone consumer **alan** dare gush mide.

**Implication baraye deploy:** age service restart beshe, notification-haye beyn-e shutdown va startup miss mishan. Vase hamin ba'd az startup bayad ye "catch-up" query bezani baraye row-hayi ke to in gap insert shodan.

---

## Deep dive — notification ordering

Postgres guarantee mikone ke notification-haye ye transaction be **tartib-e commit** miresan. Yani age Transaction A ghabl az Transaction B commit kone, notification-e A ghabl az B be listener mire. Vali age do ta transaction concurrent commit konan, tartib-eshun nondeterministic-e.

Baraye Dejban in mohem nist chon har notification independent-e (ye access log) va tartib-e relative-eshun baraye UI farghi nadare — UI khodesh bar asas-e DateTime sort mikone.

---

## Deep dive — LISTEN va prepared statements

Ye gotcha-ye Npgsql: `LISTEN` ra **nabayad** ba prepared statement ejra koni. Npgsql-e ghadimi in restriction ro nadare, vali best practice-e ke `LISTEN` ro be soorat-e simple query ejra koni (ke Dejban ham injuri karde):

```csharp
using var cmd = new NpgsqlCommand($"LISTEN {ChannelName}", connection);
await cmd.ExecuteNonQueryAsync(stoppingToken);
```

`NpgsqlCommand` be default simple query mode-e magar explicitly prepare koni. Pas in OK-e.

---

## Deep dive — scalability-e LISTEN

Age **chand ta instance** az ACLServer run beshe (horizontal scale):
- Har instance ye dedicated connection dare ke LISTEN mikone
- Har instance **hame-ye** notification-ha ro migire (Postgres be hame-ye listener-ha broadcast mikone)
- Har instance `ForwardAccessLogAsync` ro ejra mikone
- Har instance be `Clients.All`-e khod-e hub push mikone

**Natije:** age 3 instance dashte bashi:
- 3 ta DB query baraye hamun row (waste)
- 3 ta SignalR push ba hamun data (duplicate az dide client)

**Fix-ha:**
1. Faghat ye instance LISTEN kone (leader election) — complex
2. Distributed lock ghabl az forward (Redis lock ba ID-e notification) — overhead
3. Client deduplicate kone (ba ID check) — sade-tar-in
4. Az message broker estefade kon (DayTransit ye consumer) — overkill

Dejban alan single-instance ACLServer dare, pas in moshkel pish nayumade. Vali vaghti scale koni, bayad resolve beshe.

---

## Deep dive — security-e notification

pg_notify payload be **hame-ye connection-haye ke LISTEN kardan** mire — hich access control-i ru-ye channel nist (bar khalaf-e RabbitMQ ke per-queue permission dare). Pas:

- Age ye connection-e malicious LISTEN kone, hame-ye notification-ha ro migire
- Payload nabayad sensitive data dashte bashe (password, PII-e kam) — faghat ID
- Connection-e LISTEN bayad ba user-e khas-e app bashe, na superuser

Dejban faghat ID mifrestefe pas security-e payload OK-e. Vali channel name predictable-e — age kasi be DB access dashte bashe mitune LISTEN kone.

---

## Extra — pg_notify to extension-haye dge (pgcron, PostgREST)

pg_notify faghat baraye custom trigger nist — tool-haye dge ham azash estefade mikonan:

- **pg_cron:** mitune har chand vaght ye `pg_notify` befresste baraye heartbeat
- **PostgREST:** mishe ba trigger + pg_notify realtime feature besazi
- **Supabase Realtime:** internal-e Supabase az logical replication estefade mikone, na pg_notify (chon scale-e bozorgtar mikhad)

---

## Extra — testing-e trigger va LISTEN

```sql
-- Test trigger manually:
INSERT INTO public."VehicleAccessLogs" ("Id", "AccessMethod", ...)
VALUES (gen_random_uuid(), 'PlateReader', ...);

-- Check listening channels:
SELECT * FROM pg_listening_channels();

-- Manually send notification:
SELECT pg_notify('platereader_vehicle_access_logs', 'test-guid-here');
```

Baraye integration test to C#:

```csharp
[Fact]
public async Task Notification_Received_When_PlateReader_Insert()
{
    using var conn = new NpgsqlConnection(connectionString);
    await conn.OpenAsync();
    await new NpgsqlCommand("LISTEN platereader_vehicle_access_logs", conn).ExecuteNonQueryAsync();

    var tcs = new TaskCompletionSource<string>();
    conn.Notification += (_, e) => tcs.SetResult(e.Payload);

    // Insert a PlateReader access log via another connection
    await InsertTestAccessLog("PlateReader");

    var payload = await tcs.Task.WaitAsync(TimeSpan.FromSeconds(5));
    Assert.True(Guid.TryParse(payload, out _));
}
```

---

## Extra — migration-e trigger — Up/Down

Dejban trigger ro to ye EF migration piyade karde (raw SQL). In pattern mohem-e:

```csharp
protected override void Up(MigrationBuilder migrationBuilder)
{
    migrationBuilder.Sql("""
        CREATE OR REPLACE FUNCTION notify_platereader_vehicle_access_logs() ...
        CREATE TRIGGER trg_platereader_vehicle_access_logs_notify ...
    """);
}

protected override void Down(MigrationBuilder migrationBuilder)
{
    migrationBuilder.Sql("""
        DROP TRIGGER IF EXISTS ...
        DROP FUNCTION IF EXISTS ...
    """);
}
```

**`CREATE OR REPLACE`** — age function ghablan vojud dashte bashe, overwrite mishe. In idempotent-e va age migration dobare run beshe moshkeli pish nemiad.

**`DROP TRIGGER IF EXISTS` ghabl az `CREATE TRIGGER`** — chon `CREATE TRIGGER` `IF NOT EXISTS` nadare (ta Postgres 14-), avval drop mikoni ba'd create mikoni.

---

## Extra — Npgsql 7+ va notification API changes

To Npgsql 7+, `Notification` event hanuz kar mikone vali ye API-e jadid ham hast:

```csharp
await foreach (var notification in connection.WaitForNotificationsAsync(ct))
{
    // notification.Channel, notification.Payload
}
```

In cleaner-e chon `IAsyncEnumerable`-e va niaz be `while` + `WaitAsync` loop nadare. Dejban az pattern-e ghadimi estefade mikone (event-based) ke ba Npgsql 6 ham compatible-e.

---

## Extra — alternative: outbox + polling baraye guaranteed delivery

Age at-most-once delivery kafi nabud va guaranteed lazem bud:

1. To INSERT trigger, be ja-ye pg_notify, ye row to ye `NotificationOutbox` jadval insert kon
2. BackgroundService har 1 sanie outbox ro poll kone
3. Ba'd az successful push, row ro delete ya `ProcessedAt` set kon
4. Age push fail kone, row baghi mimune va retry mishe

In pattern at-least-once delivery mide (ba duplicate risk ke client handle mikone) vali hargez miss nemikone. Dejban in ro niaz nadashte chon plate reader event-e critical nist — miss beshe, operator daghighe-ye ba'd to list mibinesh.

---

## Khoruj-e zehni

> In ruz ra vaghti digeri kardi ke betuni bedune look-up, kamel-e flow ro az trigger ta SignalR push tozih bedi: trigger AFTER INSERT ba WHEN filter → pg_notify(channel, ID) → dedicated Npgsql connection LISTEN + WaitAsync → OnNotification parse Guid → scope + repo → IHubContext push.

Age in flow mal-e to shod — Day 61 done.

---

## Debug checklist

1. **Hich event nemiad?** → `LISTEN` ejra shode? Connection baz-e? `SELECT * FROM pg_listening_channels()` to psql bezan
2. **Trigger fire nemishe?** → `AccessMethod = 'PlateReader'` doroste? `WHEN` condition ro check kon
3. **Notification miad vali data nist?** → `GetForRealtimeAsync` null bargardune → transaction hanuz commit nashode? Tenant filter block karde?
4. **Log "payload not a valid Guid"?** → trigger dobare check kon; `NEW."Id"::text` doroste?
5. **Service crash mikone?** → exception to `ExecuteAsync` catch nashode? Connection string doroste?
6. **Connection ghat mishe?** → DB restart shode? Network timeout? 5s reconnect delay log ro check kon
7. **Client-ha event nemigiran?** → SignalR connected-an? Hub path doroste? YARP route OK-e?
8. **Duplicate event?** → reconnect ba'd az short disconnect momkene bakhshi az event-ha ro gom kone ya duplicate bede — client bayad idempotent bashe

---

# BAKHSH-E SEVOM: mosahebe + resume

## 25 soal-e mosahebe (ba javab-e kutah)

1. **LISTEN chie?** → SQL command ke connection ro subscribe mikone be ye channel.
2. **NOTIFY chie?** → `pg_notify(channel, payload)` — message be listener-ha mifreste.
3. **Trigger chie inja?** → `AFTER INSERT` trigger ke ba shart-e `PlateReader` fire mishe.
4. **Chera dedicated connection lazeme?** → LISTEN ru-ye pooled connection gom mishe vaghti connection bargarde be pool.
5. **WaitAsync chie?** → Async block ta notification biad — thread azad-e.
6. **Payload limit-e Postgres chie?** → ~8000 byte (8KB).
7. **Chera faghat ID mifrestim?** → Size limit + security (sensitive data leak).
8. **Reconnect delay chie?** → 5s — balance-e beyn-e spam va latency-e recovery.
9. **Fire-and-forget risk chie?** → Exception gom mishe; faghat log mishe.
10. **vs polling?** → Polling waste resource; NOTIFY instant va efficient.
11. **vs SaveChanges + SignalR?** → Faghat vaghti writer khodesh app bashe kar mikone; trigger az har writer fire mishe.
12. **vs Debezium?** → Debezium CDC-e kamel ba Kafka; NOTIFY saboktar baraye ye-do jadval.
13. **Delivery guarantee chie?** → At-most-once — age connection ghat bashe, miss mishe.
14. **Transaction rollback chi mishe?** → Notify send nemishe — faghat ba'd az commit.
15. **OperationCanceledException handling chie?** → Clean shutdown vaghti app stop mishe.
16. **Scope chera lazeme?** → BackgroundService singleton-e; DbContext scoped-e — bayad scope besazi.
17. **Clients.All smell chie?** → Hame-ye client-ha event migiran — multi-tenant isolation nadare.
18. **Thread-e OnNotification chi-e?** → Npgsql internal thread — nabayad block beshe.
19. **IgnoreQueryFilters chera?** → Tenant filter ro skip mikone chon trigger cross-tenant fire mishe.
20. **AsNoTracking chera?** → Read-only query — performance better.
21. **Chera AFTER INSERT na BEFORE?** → Row bayad persist shode bashe ta bekhuniesh.
22. **pg_listening_channels() chie?** → Debug: neshun mide kodum channel-ha listen shodan.
23. **Backpressure chie?** → Nadare — burst-e notification memory/thread pressure mide.
24. **Day 26 link chie?** → `IHubContext<PlateReaderHub>` hamun pattern-e SignalR push az biroon-e hub.
25. **Channel name convention chie?** → `platereader_vehicle_access_logs` — descriptive va unique.

---

## Anti-pattern-ha

```csharp
// BAD: LISTEN ru-ye pooled connection (EF)
using var conn = dbContext.Database.GetDbConnection();
// → age EF pool in connection ro reuse kone, LISTEN gom mishe

// GOOD: dedicated NpgsqlConnection az connection string
using var conn = new NpgsqlConnection(_connectionString);

// BAD: kamel-e row to payload
PERFORM pg_notify('ch', row_to_json(NEW)::text);
// → 8KB limit + sensitive data

// GOOD: faghat ID
PERFORM pg_notify('ch', NEW."Id"::text);

// BAD: bedun-e reconnect loop
await connection.WaitAsync(ct); // crash → app dead
// GOOD: while + try/catch + delay (hamun ke Dejban dare)

// BAD: blocking OnNotification
void OnNotification(...) {
    var data = repo.GetAsync(id).Result; // DEADLOCK risk
}
// GOOD: fire-and-forget ba async method
_ = ForwardAccessLogAsync(id);
```

---

## Senario-ha

### A) Plate reader camera aks migire
Camera aks-e pelak ro mikhune → plate reader agent be ACLServer API call mizane → ACLServer `VehicleAccessLog` insert mikone ba `AccessMethod = 'PlateReader'` → trigger fire mishe → pg_notify → BackgroundService migire → `GetForRealtimeAsync` → SignalR push be operator-e dashboard.

### B) DB connection ghat mishe
BackgroundService `WaitAsync` ro seda zade → Postgres restart mishe → `NpgsqlException` throw mishe → catch: log + 5s delay → reconnect → `LISTEN` dobare → edame. **Notification-haye beyn-e disconnect va reconnect miss mishan** — client bayad vaghti SignalR reconnect mikone, last-known state ro refetch kone.

### C) Transaction rollback
Agent ye access log insert mikone → trigger fire mishe → vali ghabl az commit, validation fail mikone → transaction rollback → **pg_notify send nemishe** (chon notify faghat ba'd az commit mire). Pas listener hich chizi nemigire — dorost-e.

### D) Burst-e 50 vehicle hamzaman
50 ta mashin hamzaman wared mishan → 50 ta INSERT → 50 ta trigger → 50 ta notification → BackgroundService 50 ta `ForwardAccessLogAsync` concurrent fire mikone → 50 ta DB query + 50 ta SignalR push. **Risk:** age DB ya SignalR under pressure bashe, ba'zi fail mishan va faghat log mishe. Baraye scale bayad semaphore ya Channel\<T\> (bounded) estefade koni.

### E) Multi-tenant smell
Operator-e site A dashboard-e plate reader ro baz karde. Mashin to site B wared mishe. **Hame-ye client-ha** event migiran chon `Clients.All` estefade shode. Operator-e site A data-ye site B ro mibine — **isolation failure**. Fix: group-e site to PlateReaderHub (mesle ManualAccessHub).

---

## Resume

**kutah:**

> Bridged **PostgreSQL LISTEN/NOTIFY** to **SignalR** for realtime plate-reader access logs — DB trigger `pg_notify`'s the row ID, a `BackgroundService` listens on a dedicated Npgsql connection, fetches the DTO, and pushes via `IHubContext`.

**bullet-ha:**

- Designed PostgreSQL trigger with row-level WHEN filter to pg_notify only plate-reader inserts
- Built BackgroundService with dedicated Npgsql connection, async LISTEN/WaitAsync loop, and 5-second reconnect
- Parsed Guid payload, resolved scoped repository, and pushed realtime DTO through typed SignalR hub
- Decoupled write path from push path — trigger fires regardless of which service inserts

**skill-ha:** `PostgreSQL` · `LISTEN/NOTIFY` · `pg_notify` · `Npgsql` · `BackgroundService` · `SignalR` · `IHubContext` · `Realtime` · `Trigger` · `Event-driven`

---

## Interview 60s

> «For plate-reader access logs we use PostgreSQL LISTEN/NOTIFY instead of polling. A row-level trigger fires pg_notify with just the row ID after insert when AccessMethod is PlateReader. A BackgroundService holds a dedicated Npgsql connection, LISTENs on the channel, and WaitAsyncs in a loop. On notification it parses the Guid, creates a scope, fetches the DTO, and pushes through IHubContext to SignalR clients. Reconnect on failure with a 5-second backoff. It's at-most-once delivery so the UI reconciles on reconnect.»

---

## File-haye mohem

| chi | koja |
|---|---|
| Trigger migration | `ACLServer/.../Migrations/20260907120000_PlateReaderNotifyIdOnly.cs` |
| BackgroundService | `ACLServer/Infrastructure/Services/PlateReaderNotifyHostedService.cs` |
| Repository | `ACLServer/Infrastructure/Persistence/Repositories/PlateReaderAccessLogRepository.cs` |
| Hub | `ACLServer/Hubs/PlateReaderHub.cs` |
| Registration | `ACLServer/Abstractions/Extensions/ServiceCollectionExtensions.cs` |

---

## Ertebat ba ruz-haye dge

| day | ertebat |
|---|---|
| 26 SignalR | `IHubContext<PlateReaderHub>` — push az biroon-e hub |
| 07 YARP | PlateReaderHub masir-esh az gateway pass mishe |
| 06 JWT | client-e browser authenticate mishe ghabl az vasl shodan be hub |
| 16 Tenancy | `IgnoreQueryFilters(TenantFilter)` to repository |
| 18 DI | `IServiceScopeFactory` baraye resolve-e scoped service az singleton |

---

## Deep dive — chera pg_notify va na logical replication

Postgres ye feature-e dge ham dare be esm-e **logical replication** (wa slots) ke mishe ba tool-haye mesle Debezium ya pgoutput azash WAL-e change-ha ro bekhuni. Fargh-esh:

| | pg_notify | Logical replication |
|---|---|---|
| Setup | ye trigger, ye LISTEN | replication slot, publication, subscriber/connector |
| Payload | custom (to trigger define mikoni) | kamel-e row change (INSERT/UPDATE/DELETE) |
| Consumer | Npgsql connection to app | Kafka, Debezium, ya dge subscriber |
| Scale | ye-chand channel | sad-ha jadval, cross-DB |
| Overhead | minimal | WAL processing, extra disk |
| Delivery | at-most-once (in-process) | at-least-once (ba checkpoint) |

Baraye ye jadval ba ye use-case-e sade, pg_notify ideal-e. Baraye CDC-e kamel-e system, logical replication behtar-e.

---

## Deep dive — Npgsql notification internals

Npgsql vaghti `WaitAsync` seda zade mishe, ye `ReadAsync` ru-ye TCP socket-e Postgres mizane. Postgres notification ro be soorat-e ye message type-e khas (`NotificationResponse`) ru-ye hamun socket mifreste. Npgsql message ro parse mikone va `Notification` event ro raise mikone.

**Mohem:** notification ru-ye **hamun connection** miad — age connection-e pool-shode bashe va ye query-e dge run beshe, notification ta payan-e un query buffer mishe. Vase hamin **dedicated connection** lazeme ke hich query-e dge rush run nashe.

---

## Deep dive — multiple channel support

Mishe ye connection chand ta LISTEN dashte bashe:

```sql
LISTEN channel_a;
LISTEN channel_b;
```

Har notification `channel` property dare ke mige az kodum channel umade. Dejban alan faghat ye channel dare (`platereader_vehicle_access_logs`), vali age farda mikhay visitor access ya weighbridge event ham trigger dashte bashe, mishe hamun connection ro reuse koni va ba `switch(notification.Channel)` route koni.

---

## Deep dive — idempotency-e client

Chon delivery at-most-once-e va reconnect momkene gap dashte bashe, UI client bayad:

1. Vaghti SignalR reconnect mikone, **list-e access log ro refetch kone** (HTTP GET)
2. **Duplicate check kone** — age notification-e repeat biad (rare vali momkene), ba ID check kon age ghablan to list hast ignore kon
3. **Optimistic UI** — event-e realtime ro neshun bede, vali source of truth DB-e, na SignalR

---

## Extra — monitoring-e LISTEN connection

Baraye production, in metric-ha ro track kon:

- **Reconnect count** — age ziad bashe, network ya DB problem dare
- **Notification rate** — chand ta dar daghighe miad
- **Forward failure rate** — chand ta `ForwardAccessLogAsync` fail shode
- **Latency** — az trigger ta SignalR push (sakhte measure koni vali az timestamp-e log mishe taghribi hesab kard)

```csharp
_logger.LogInformation("Notification received for {Id} at {Time}", accessLogId, DateTime.UtcNow);
// va to ForwardAccessLogAsync:
_logger.LogInformation("Forwarded {Id} at {Time}", accessLogId, DateTime.UtcNow);
```

Fargh-e in do timestamp ~= end-to-end latency.

---

## Extra — alternative pattern: Channel\<T\> baraye backpressure

Be ja-ye fire-and-forget, mishe az `Channel<Guid>` estefade koni:

```csharp
private readonly Channel<Guid> _notificationChannel =
    Channel.CreateBounded<Guid>(new BoundedChannelOptions(100)
    {
        FullMode = BoundedChannelFullMode.DropOldest
    });

// OnNotification:
_notificationChannel.Writer.TryWrite(accessLogId);

// Consumer loop:
await foreach (var id in _notificationChannel.Reader.ReadAllAsync(ct))
{
    await ForwardAccessLogAsync(id);
}
```

In **bounded** buffer mide: age consumer kond bashe, ghadimi-tarin-ha drop mishan (ke OK-e chon client refetch mikone). Dejban in pattern ro estefade nakarde vali baraye burst-e 50+ vehicle hamzaman kheili behtar-e.

---

## Extra — UNLISTEN va cleanup

```sql
UNLISTEN channel_name;
UNLISTEN *;  -- hame-ye channel-ha
```

Vaghti connection close mishe, LISTEN-hash khodkar pak mishan. Pas `UNLISTEN` explicit lazem nist magar mikhay to runtime ye channel ro gheyrefaal koni bedun-e close-e connection.

---

## Mini lab

1. To psql: `LISTEN test_channel;` → to ye tab-e dge: `SELECT pg_notify('test_channel', 'hello');` → avvali tab bayad `Asynchronous notification "test_channel" received` ra neshun bede
2. PlateReaderNotifyHostedService ro bekhun — breakpoint ru-ye `OnNotification` bezar → ye access log insert kon ba method=PlateReader
3. `GetForRealtimeAsync` ro bebin — chera `IgnoreQueryFilters`?
4. Connection-e dedicated ro check kon — motmaen sho az EF pool nist
5. Service ro restart kon vaghti DB baz-e — bebin reconnect log miad ya na

---

## Extra — NOTIFY va VACUUM / maintenance

pg_notify hich tasiresh bar VACUUM ya maintenance-e jadval nadare. Notification-ha to **shared memory** buffer-e Postgres mimunan (na disk) va ba'd az delivery ya disconnect pak mishan. Pas:

- Hich WAL overhead nadare (bar khalaf-e logical replication)
- Hich disk write nadare
- Faghat memory-e short-lived masraf mikone
- Age buffer por beshe (kheili rare — hazaran notification buffer nashe), Postgres warning mide va notification-ha drop mishan

In yeki az dalayeli-e ke pg_notify saboke — az disk estefade nemikone.

---

## Extra — monitoring ba pg_stat_activity

Baraye check kardan ke LISTEN connection baz-e:

```sql
SELECT pid, state, query, backend_start
FROM pg_stat_activity
WHERE query LIKE '%LISTEN%'
   OR state = 'idle'
ORDER BY backend_start DESC;
```

Connection-e LISTEN ma'mulan state-esh `idle`-e (chon LISTEN ye one-shot command-e va ba'd connection idle wait mikone). In normal-e — naresid be "hanuz LISTEN nakarde".

---

## Extra — fargh-e LISTEN/NOTIFY ba Redis Pub/Sub

| | pg_notify | Redis Pub/Sub |
|---|---|---|
| Niyaz be infra-e jadid? | na — Postgres khodesh dare | are — Redis server lazeme |
| Delivery | at-most-once | at-most-once |
| Persistence | na | na (magar Stream estefade koni) |
| Pattern subscribe | na — exact channel name | are — `PSUBSCRIBE pattern*` |
| Payload limit | ~8KB | 512MB (practical: chand KB) |
| Cross-DB | na — faghat hamun DB | are — har subscriber az har ja |
| Dejban | ✓ trigger-based access logs | ✓ cache invalidation (Day 25) |

**Key pg_notify:** vaghti writer to Postgres-e va mikhay DB-level event react koni bedun-e infra-e jadid.
**Key Redis Pub/Sub:** vaghti cross-service notification mikhay ya subscriber-ha to service-haye mokhtalef-an.

Dejban az **har do** estefade mikone — pg_notify baraye plate reader, Redis baraye cache invalidation.

---

## Jadval-e decision — key az kodum notification system estefade koni

| shart | tool |
|---|---|
| Ye jadval, DB-level trigger, sade | pg_notify |
| Multiple jadval, CDC kamel | Debezium / logical replication |
| Write path to khodesh app bashe | SignalR ba'd az SaveChanges |
| Cross-service notification | MassTransit / Redis Pub/Sub |
| Guaranteed delivery lazeme | Outbox pattern + polling |
| Realtime + at-most-once OK bashe | pg_notify ya SignalR |

---

## Glossary

| kalame | ma'ni |
|---|---|
| LISTEN | SQL command ke connection ro subscribe mikone be channel |
| NOTIFY / pg_notify | message be channel mifreste |
| Trigger | code-e SQL ke ba'd az event-e DB run mishe |
| AFTER INSERT | trigger ba'd az insert-e row |
| FOR EACH ROW | trigger baraye har row joda |
| WHEN | shart-e filter-e trigger |
| WaitAsync | Npgsql: async block ta notification |
| Dedicated connection | connection ke az pool joda-st va faghat LISTEN mikone |
| Fire-and-forget | async method ke await nemishe |
| At-most-once | delivery ke miss shavad momkene, duplicate na |
| BackgroundService | long-running service ke ba app start/stop mishe |
| IServiceScopeFactory | baraye sakhtan-e scope az singleton |
| Payload | data-ye ke ba notification ferestad mishe |
| CDC | Change Data Capture — track-e hame-ye change-haye DB |

---

## Self-test-e sari

1. Trigger key fire mishe? → AFTER INSERT vaghti AccessMethod = PlateReader
2. Payload chi-e? → `NEW."Id"::text` — Guid-e row
3. Chera dedicated connection? → LISTEN ru-ye pooled connection gom mishe
4. WaitAsync chi mikone? → Async block ta notification biad
5. Reconnect delay chand-e? → 5 sanie
6. OnNotification chera fire-and-forget-e? → Npgsql thread-e — nabayad block beshe
7. Scope chera lazeme? → BackgroundService singleton; DbContext scoped
8. Delivery guarantee chie? → At-most-once
9. Clients.All smell chie? → Multi-tenant isolation nadare
10. Day 26 link chie? → IHubContext push az biroon-e hub

Age 8/10 ya bishtar dorost bud → beri sar-e Day 62.

---

## Extra — monitoring query baraye production

```sql
-- Check ke trigger faal-e:
SELECT tgname, tgenabled, tgrelid::regclass
FROM pg_trigger
WHERE tgname = 'trg_platereader_vehicle_access_logs_notify';
-- tgenabled = 'O' yani Origin (faal). 'D' = disabled.
```

---

## Resume keywords (ATS)

`PostgreSQL` · `LISTEN/NOTIFY` · `pg_notify` · `Database Triggers` · `Npgsql` · `BackgroundService` · `SignalR` · `IHubContext` · `Realtime Systems` · `Event-driven Architecture` · `.NET` · `ASP.NET Core`

---

## In che chizi-e Day 61 *nist*

- Rahnama-ye kamel-e PostgreSQL trigger-ha nist — faghat ye trigger-e ke baraye notify estefade mishe
- Rahnama-ye SignalR nist — un Day 26-e; inja faghat `IHubContext` push ro estefade mikonim
- Debezium setup nist — faghat mention-e moghayese-i
- FE client-e SignalR nist — un Day 50-e
- Kamel-e plate reader workflow nist (camera, agent, policy) — faghat DB → SignalR push

---

## Extra — error handling strategy-e production

Baraye production-e vaghei, in improvement-ha lazeme:

1. **Structured logging ba correlation ID:** har notification ye correlationId dashte bashe ke ta browser trace beshe
2. **Health check:** ye endpoint ke status-e LISTEN connection ro check kone — age disconnected bashe, unhealthy report kone
3. **Alerting:** age reconnect count to 5 daghighe az threshold rad beshe, alert befrest
4. **Graceful shutdown:** `stoppingToken` ghabl az cancel shodan, avval `UNLISTEN` kon (optional — connection close khodesh handle mikone)
5. **Circuit breaker:** age DB 10 bar posht-e ham fail kone, delay ro bozorgtar kon (exponential backoff be ja-ye fixed 5s)

Dejban alan fixed 5s delay dare ke baraye current scale kafi-e vali production-grade nabud.

---

## Checklist-e nahaei

- [ ] Trigger: AFTER INSERT + WHEN filter + pg_notify(channel, ID)
- [ ] BackgroundService: dedicated connection + LISTEN + WaitAsync loop
- [ ] Reconnect: 5s delay + OperationCanceledException handling
- [ ] OnNotification: Guid.TryParse + fire-and-forget ForwardAccessLogAsync
- [ ] ForwardAccessLogAsync: scope + repo + hub push
- [ ] Smell-ha: Clients.All, fire-and-forget, race condition
- [ ] vs polling / SaveChanges SignalR / Debezium
- [ ] 25 soal ba javab
- [ ] Resume bullet-ha

---

## Extra — pg_notify va partitioned tables

Age jadval-e `VehicleAccessLogs` partition shode bashe (masalan bar asas-e mah ya site), trigger bayad ru-ye **har partition** jadagane set beshe ya ru-ye parent jadval ba `ON` clause. Postgres trigger inheritance ba partition-ha pichide-ye — age partition-e jadid ezafe koni va trigger faramush koni, notification-haye un partition miss mishan. In ye gotcha-ye production-e ke bayad to migration-ha handle beshe.

---

## Extra — chetori az pg_notify be event sourcing nazdik mishi

pg_notify khodesh event sourcing nist — vali mishe step-e avval bashe:

1. Trigger INSERT detect mikone
2. Notification be service miad
3. Service event ro to ye event store ham save mikone (optional)
4. Event az event store replay mishe baraye projection

In architecture baraye Dejban overkill-e vali concept-esh mohem-e baraye mosahebe — neshun mide farahmi ke pg_notify ye building block-e, na ye kamel-e solution.

To mosahebe age beporsad "have you worked with event-driven database patterns?" javab-e khobi dari: "Yes — we use PostgreSQL LISTEN/NOTIFY with a trigger that pg_notifies on insert, consumed by a BackgroundService that pushes through SignalR. It's lighter than CDC tools like Debezium when you only need one table."

---

*Day 61 tamum. Ba'di: Day 62 — MassTransit Request/Response. Fehrest: [README.md](./README.md).*
