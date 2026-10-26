# Dapper در دژبان

شناسهٔ کاتالوگ: `10-dapper`.

ارجاع: [07-modular-monolith](07-modular-monolith.md)، [08-cqrs-mediatr](08-cqrs-mediatr.md)، [09-ef-core-postgresql](09-ef-core-postgresql.md)، [06-tenancy-authorization](06-tenancy-authorization.md)، [00-execution-path-index](00-execution-path-index.md).

اپ، تست، و اتصال به دیتابیس در این فاز اجرا نشد. Dapper در این مخزن **مستقیماً در کد تولید دژبان** استفاده می‌شود؛ فقط dependency اعلانی نیست.

## Dapper چیست

Dapper یک micro-ORM برای .NET است. SQL را خودتان می‌نویسید؛ Dapper پارامترها را bind می‌کند، ردیف‌ها را به نوع CLR نگاشت می‌کند، و روی `IDbConnection` اجرا می‌کند. برخلاف EF Core، change tracker، ترجمهٔ LINQ به SQL، و migration ندارد.

مشکل رایج: بعضی کارها با LINQ سنگین یا غیرقابل‌بیان می‌شوند (قفل ردیف، `SKIP LOCKED`، خواندن چند schema با یک SQL ثابت). Dapper آنجا SQL صریح می‌دهد بدون ترک ADO.NET کامل.

در دژبان، EF Core مسیر اصلی command/query دامنه است (درس 09). Dapper مکمل همان PostgreSQL است برای outbox/inbox، idempotency، import، replica healing، و بخش blacklist گزارش گشت.

## نسخه و محل ارجاع

| مورد | شاهد |
|---|---|
| نسخه | `Directory.Packages.props` → `Dapper` **2.1.66** |
| `PackageReference` مستقیم | فقط `Dejban.Common.Application/Dejban.Common.Application.csproj` |
| مصرف | `Dejban.Common.Infrastructure` و ماژول‌های `*.Infrastructure` از طریق `ProjectReference` به Common (transitively) |
| Reporting / Identity / ACL | جستجوی `using Dapper` در Reporting خالی بود؛ `PackageReference` Dapper خارج از Common.Application دیده نشد |

وضعیت: `verified`.

## ثبت و اتصال

1. `ApplicationConfiguration.AddApplication` مقدار `Dapper.DefaultTypeMap.MatchNamesWithUnderscores = true` می‌گذارد تا ستون‌های `snake_case` به propertyهای PascalCase نگاشت شوند.  
2. `InfrastructureConfiguration.AddInfrastructure` با `databaseConnectionString` (همان رشته‌ای که از `GetConnectionStringOrThrow("Postgres")` در `Dejban.Api` می‌آید؛ درس 02) یک `NpgsqlDataSource` Singleton می‌سازد.  
3. `IDbConnectionFactory` → `DbConnectionFactory` Scoped؛ `OpenConnectionAsync` از data source اتصال باز می‌کند.  
4. `SqlMapper.AddTypeHandler(new GenericArrayHandler<string>())` و `SqlMapper.AddTypeHandler(new GuidListHandler())` برای آرایهٔ PostgreSQL و `List<Guid>` (مثلاً `site_ids` در outbox).

وضعیت: `verified`. مقدار زندهٔ connection: runtime؛ کلید پیکربندی `Postgres` است.

```text
Dejban.Api → AddInfrastructure(..., databaseConnectionString, ...)
  → NpgsqlDataSource
  → DbConnectionFactory.OpenConnectionAsync()
  → IDbConnection / DbConnection
  → Dapper QueryAsync / ExecuteAsync / ...
```

مرز شبکه: فراخوانی Dapper in-process است؛ SQL روی TCP به PostgreSQL می‌رود (مثل EF).

## نقشهٔ مصرف واقعی

| حوزه | نمادهای نمونه | نقش |
|---|---|---|
| Outbox job | `ProcessOutboxJob` در هر ماژول (مثلاً Personnels) | خواندن و علامت‌زدن `*.outbox_messages` |
| Inbox job | `ProcessInboxJob` | مشابه برای inbox |
| Idempotency | `IdempotentDomainEventHandler<>`، `IdempotentIntegrationEventHandler<>` | EXISTS/INSERT روی `*_message_consumers` |
| Inbox insert از consumer | `IntegrationEventConsumer<>` | INSERT inbox با Dapper |
| Import پرسنل | `PersonnelImportBatchProcessor.ClaimAsync` | `FOR UPDATE … SKIP LOCKED` + `RETURNING` |
| گزارش گشت | `PatrolReportService` | SQL روی schemaهای `visitors` و `personnels` |
| Replica | `ReplicaHealer` | کپی/وجود ردیف بین schemaها با SQL صریح |

همهٔ این‌ها کنار `DbContext` همان host هستند، نه جایگزین کامل EF.

## مسیر ۱ — Outbox پرسنل با Dapper

شروع: Quartz `ProcessOutboxJob.Execute` (نه HTTP مستقیم؛ job پس‌زمینه). جزئیات زمان‌بندی در درس 12.

گام‌ها:

1. `await using DbConnection connection = await dbConnectionFactory.OpenConnectionAsync()`  
2. `BeginTransactionAsync` روی همان connection  
3. `GetOutboxMessagesAsync`: `QueryAsync<OutboxMessageResponse>` روی SQL ثابت schema `personnels.outbox_messages` با `FOR UPDATE` و `LIMIT {BatchSize}`  
4. برای هر پیام: deserialize، `TenantContextAccessor.SetContext`، اجرای `IDomainEventHandler`ها (ممکن است دوباره EF یا bus صدا بزنند؛ درس 08)  
5. `UpdateOutboxMessageAsync`: `ExecuteAsync` با پارامترهای `@Id`، `@ProcessedOnUtc`، `@Error`  
6. `CommitAsync`

نگاشت ردیف: aliasهای `AS {nameof(...)}` به‌علاوهٔ `MatchNamesWithUnderscores` و `GuidListHandler` برای `site_ids`.

وضعیت مسیر کد: `verified`. اینکه job در محیط واقعی چند وقت یک‌بار می‌دود: درس 12 / `runtime verification pending`.

نکتهٔ مهم: `IdempotentDomainEventHandler` داخل handler دامنه **اتصال جدا** باز می‌کند و روی `personnels.outbox_message_consumers` می‌نویسد؛ آن کار لزوماً داخل تراکنش همان `ProcessOutboxJob` نیست. وضعیت جدا بودن connection: `verified`. تضمین اتمیک بودن handler+consumer+update outbox در یک تراکنش واحد: از این کد اثبات نمی‌شود → ریسک بالقوه.

## مسیر ۲ — گزارش گشت (HTTP تا Dapper)

1. `GetPatrolReportQueryHandler` → `IPatrolReportService.GetPatrolBoardReportAsync`  
2. بخش board/event با **EF** (`GetQueryable`، `Include`) روی schema گشت  
3. سپس `OpenConnectionAsync` و دو `QueryAsync`:  
   - `visitors.black_list_history` … با `@boardDate`  
   - `personnels.black_list_history` … با `@boardDate`  
4. نتیجه در `PatrolBoardReportDto` جمع می‌شود  

این نمونهٔ صریح «Dapper برای خواندن cross-schema» است؛ SecurityPatrols از طریق SQL به جدول Visitors/Personnels می‌رسد، نه از طریق `DbContext` آن ماژول‌ها. وضعیت: `verified`.

## مسیر ۳ — Claim ردیف import (مکمل)

`PersonnelImportBatchProcessor.ClaimAsync` با `CommandDefinition` و `cancellationToken` یک CTE می‌نویسد: `FOR UPDATE OF candidate SKIP LOCKED`، بعد `UPDATE … RETURNING id`، بعد `QueryAsync<Guid>`. پارامترها `@JobId`، `@StaleBefore`، `@BatchSize`. بقیهٔ batch با EF روی `PersonnelsDbContext` اعمال می‌شود. وضعیت: `verified`.

## مفاهیم با کد همین مخزن

### `QueryAsync` در برابر `ExecuteAsync`

- `QueryAsync<T>` ردیف برمی‌گرداند (لیست outbox، blacklist، idهای claimشده).  
- `ExecuteAsync` تعداد ردیف تأثیرگرفته را برای INSERT/UPDATE می‌خواهد (به‌روزرسانی outbox، insert consumer).  
- `ExecuteScalarAsync<T>` یک مقدار (مثلاً `EXISTS` بولین در idempotency).

### پارامترها

شیء ناشناس یا record/DTO با نام property هم‌نام پارامتر SQL (`@Id`). این bind جلوی تزریق مقدار به متن SQL را می‌گیرد وقتی از پارامتر استفاده شود، نه وقتی تکهٔ SQL با رشته ساخته شود.

### نگاشت

ستون → property با نام (و underscore matching). Type handler سفارشی برای آرایه و `List<Guid>`. Dapper navigation و lazy load ندارد.

### عمر connection و تراکنش

الگوی غالب: `await using` روی connection از factory. Outbox job تراکنش صریح دارد. Idempotent handler و PatrolReport معمولاً بدون `BeginTransaction` روی همان متد دیده شدند. وضعیت: `verified` برای نمونه‌های خوانده‌شده.

### آنچه Dapper خودکار نمی‌دهد

Change tracking، `SaveChanges`، global query filterهای EF (tenant/soft-delete)، migration، و graph `Include`. هر فیلتر امنیتی باید در SQL یا لایهٔ بالاتر تکرار شود.

## امنیت و درستی

| موضوع | مسیر / نماد | رفتار | اهمیت | شدت | بهبود متناسب |
|---|---|---|---|---|---|
| پارامتر در UPDATE outbox | `ProcessOutboxJob.UpdateOutboxMessageAsync` | `@Id` و بقیه | جلوگیری از injection روی مقادیر | درست / تأییدشده | حفظ پارامتر |
| `LIMIT` با interpolation | `GetOutboxMessagesAsync` → `LIMIT {outboxOptions.Value.BatchSize}` | عدد از Options داخل SQL | اگر فقط int از config باشد ریسک injection کاربر پایین است؛ همچنان SQL پویا است | ریسک بالقوه (پیکربندی، نه ورودی HTTP) | `LIMIT @BatchSize` پارامتری |
| گزارش بدون فیلتر tenant/soft-delete در SQL | `PatrolReportService` blacklist SQL | فقط `DATE(created_at) = @boardDate` | SQL خام فیلتر EF را دور می‌زند؛ ممکن است ردیف خارج از سایت یا حذف‌شده دیده شود اگر ستون‌ها اجازه دهند | ریسک بالقوه؛ exploitation اثبات نشد | افزودن `site_id` / `is_deleted` صریح در SQL یا محدود کردن با permission سطح گزارش |
| عدم ارسال `CancellationToken` به Dapper در گزارش | `QueryAsync(..., new { boardDate })` بدون `CommandDefinition` | لغو درخواست HTTP لزوماً کوئری را قطع نمی‌کند | لغو ناقص | ریسک بالقوه | `CommandDefinition` مثل import |
| Idempotency روی connection جدا از تراکنش job | `IdempotentDomainEventHandler` در برابر `ProcessOutboxJob` | دو connection | در خطا ممکن است consumer ثبت شود یا نشود ناهم‌زمان با update outbox | ریسک بالقوه | یک تراکنش مشترک یا outbox transactional inbox الگو |
| شناسهٔ جدول در ReplicaHealer | `$"{CanonicalSchema}.{TableName(kind)}"` | نام از enum/ثابت، مقدار `@id` پارامتری | اگر `TableName` فقط از enum باشد امن است | الگوی درست برای شناسه؛ مقادیر پارامتری `verified` | نگه داشتن whitelist enum |
| Claim import | `PersonnelImportBatchProcessor.ClaimAsync` | پارامتر + `SKIP LOCKED` + CT | الگوی خوب برای صف کاری | تأییدشده به‌عنوان الگوی مطلوب | — |

SQL parameterized به‌تنهایی «آسیب‌پذیری» نیست. دور زدن فیلتر EF وقتی عمدی و بدون جایگزین tenant باشد نگران‌کننده‌تر است.

## مقایسه با EF Core در این مخزن

| موضوع | EF Core اینجا | Dapper اینجا |
|---|---|---|
| نوشتن SQL | معمولاً LINQ؛ گاهی `ExecuteSql` در جاهای دیگر | SQL دستی در string |
| نگاشت | model + configuration | column→property + type handler |
| Change tracking | بله روی context | خیر |
| ترکیب کوئری | `IQueryable` | رشتهٔ ثابت / CTE |
| Migration | per-context EF | ندارد؛ روی همان جداول EF ساخته‌شده می‌خواند |
| رابطه | `Include` / FK در مدل | JOIN دستی در SQL |
| تراکنش | `SaveChanges` / `BeginTransactionAsync` | `BeginTransactionAsync` روی ADO connection در outbox |
| فیلتر tenant | global query filter | باید دستی؛ در گزارش گشت blacklist دیده نشد |
| کاربرد نمونه | `GetPersonnels`، `CreatePersonnel` | outbox، import claim، گزارش blacklist، replica |

هر دو به یک کلید `Postgres` / `NpgsqlDataSource` و schemaهای ماژول روی همان دیتابیس دژبان وصل می‌شوند (از ثبت Infra و SQLهای `personnels.` / `visitors.`). وضعیت هم‌پایگاهی: `verified` از کد. نسخه/هاست زنده: unresolved مثل درس 09.

## واژه‌نامه

| اصطلاح | معنی |
|---|---|
| Micro-ORM | ORM سبک؛ SQL با شما، نگاشت با کتابخانه |
| Parameter binding | جایگزینی امن `@Name` با مقدار typed |
| Type handler | تبدیل سفارشی بین CLR و نوع ستون |
| `FOR UPDATE` | قفل ردیف داخل تراکنش |
| `SKIP LOCKED` | رد کردن ردیفهای قفل‌شده برای worker دیگر |
| Outbox | جدول پیام برای پردازش بعد از persist |

## سؤال‌های مصاحبه

### 1. Dapper چیست؟

کتابخانهٔ نگاشت و اجرای SQL روی ADO.NET بدون tracker کامل. SQL را شما می‌نویسید؛ نتیجه را به کلاس می‌دهد.

دنباله: چرا micro-ORM؟

جواب: سطح مسئولیت کمتر از EF؛ کنترل SQL بیشتر، قابلیت کمتر به‌صورت خودکار.

### 2. Dapper در برابر EF Core؟

EF برای مدل دامنه، فیلتر سراسری، و migration مناسب است. Dapper برای SQL خاص، قفل، و گزارش چندschema در این مخزن کنار EF نشسته است، نه به‌جای کل دامنه.

دنباله: آیا در دژبان یکی را حذف می‌کنند؟

جواب: از کد فعلی خیر؛ CreatePersonnel هنوز EF+outbox interceptor است و job با Dapper می‌خواند.

### 3. `QueryAsync` و `ExecuteAsync`؟

اولی نتیجهٔ SELECT را به `IEnumerable<T>` می‌دهد. دومی دستور تغییر را اجرا می‌کند و معمولاً تعداد ردیف را برمی‌گرداند. Outbox هر دو را دارد.

### 4. پارامتر چطور جلوی injection را می‌گیرد؟

مقدار جدا از متن SQL به درایور می‌رود. `@boardDate` در گزارش گشت نمونه است. الحاق رشته برای مقدار کاربر خطرناک است؛ الحاق برای شناسهٔ جدول فقط با whitelist قابل دفاع است.

### 5. نگاشت ردیف چگونه است؟

نام ستون به property؛ با `MatchNamesWithUnderscores` و alias. آرایهٔ uuid با `GuidListHandler`. رابطهٔ تو در تو خودکار نیست.

### 6. عمر connection؟

باز کردن از factory، `await using` برای dispose، و در outbox یک تراکنش تا commit. نشت وقتی dispose نشود یا exception مسیر using را بشکند؛ الگوی فعلی using دارد.

### 7. چند دستور در یک تراکنش؟

Outbox: SELECT … FOR UPDATE و UPDATEها روی یک `DbTransaction`. اگر handler دامنه connection جدا باز کند، از آن تراکنش خارج است.

### 8. async و cancellation؟

APIهای Async Dapper I/O را مسدود نمی‌کنند. `CommandDefinition` می‌تواند `CancellationToken` بگیرد؛ import دارد، گزارش گشت در فراخوانی Dapper ندارد.

### 9. tenant isolation با raw SQL؟

فیلتر EF اعمال نمی‌شود. باید `site_id` (و soft-delete) را در SQL بنویسید یا قبل از اجرا دسترسی را محدود کنید. گزارش blacklist فقط تاریخ را فیلتر می‌کند — ریسک بالقوه در همین مخزن.

### 10. Dapper در دژبان کجا دیده می‌شود؟

پکیج 2.1.66 از Common.Application؛ اتصال از `NpgsqlDataSource`؛ مصرف اصلی outbox/inbox/idempotency، claim import، `PatrolReportService`، و `ReplicaHealer`. مسیر دامنهٔ HTTP لیست پرسنل EF است، نه Dapper.

## پرسش‌های باز

- Interval دقیق Quartz برای `ProcessOutboxJob` (درس 12).  
- آیا در production گزارش گشت عملاً ردیف خارج از tenant برمی‌گرداند (نیاز به داده و درخواست؛ اجرا نشد).  
- آیا همهٔ ماژول‌ها نسخهٔ یکسان SQL outbox دارند یا تفاوت BatchSize/schema جزئی دارند (الگوی Personnels خوانده شد؛ هشت فایل خط‌به‌خط diff نشد).  
- رفتار همزمان چند instance دژبان روی `Migrate` و outbox `FOR UPDATE` در cluster.  
- match حروف `/api` همچنان خارج از این درس.

## مرور

Dapper 2.1.66 در دژبان واقعاً صدا زده می‌شود: factory روی همان Postgres، type handler برای آرایه، و SQL برای outbox، import، گزارش گشت، و replica. EF مسیر اصلی دامنه می‌ماند. پارامترها در بیشتر مسیرها درست‌اند؛ `LIMIT` با interpolation از Options و نبود فیلتر tenant در SQL گزارش، نکات درست‌بودن هستند نه اثبات exploit. Quartz و messaging جزئیات زمان و bus را در درس‌های بعد می‌گیرند.
