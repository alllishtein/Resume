# دفاع فنی از متریک‌های رزومه — علی شفایی

هدف این فایل: بتونی **هر عدد رزومه** رو تو مصاحبه توضیح بدی، بگی *چیکار کردی*، *با چه ابزارهایی*، و *عدد از کجا اومد* — بدون اینکه گیر بیفتی.

قانون کلی مصاحبه:
- عددها تقریبی‌اند (`~`)؛ بگو **order-of-magnitude / measured on hot paths**، نه «دقیق آزمایشگاهی».
- همیشه وصل کن به **قبل/بعد** + **ابزار اندازه‌گیری**.
- اگه پرسیدن «سند داری؟» بگو: از Seq / logs / browser Network / SQL timing / CI duration مقایسه کردم، نه A/B علمی.
- اگه دقیق یادت نیست: «تقریبی‌ست؛ چیز مهم معماری و trade-off بود» — بعد trade-off رو بگو.

---

## ۰) جمله‌ی آماده‌ی اول مصاحبه (۳۰ ثانیه)

> روی دژبان بیشتر روی **مسیرهای پرترافیک read** و **قابلیت اطمینان async** کار کردم.  
> با **HybridCache + Redis** latency و فشار Postgres رو کم کردم، با **MassTransit Outbox/Inbox** dual-write و retry بی‌خودی رو کم کردم، و با **Docker + GitLab CI** چرخه‌ی انتشار رو کوتاه‌تر کردم.  
> عددهایی که تو رزومه نوشتم تقریبی‌ان و مربوط به همون مسیرهای hot هستن، نه میانگین کل سیستم.

---

## ۱) «زمان پاسخ API رو ~۵۰٪ کم کردم با Redis / HybridCache»

### چی بگی (نسخه‌ی کوتاه)

> مسیرهای list/detail پرترافیک هر بار می‌رفتن سراغ Postgres و گاهی enrichment از سرویس‌های دیگه.  
> اومدم **HybridCache** گذاشتم: L1 حافظه‌ی پروسس + L2 **Redis**.  
> با `GetOrCreateAsync` cache-aside کردم و روی write با **tag invalidation** کش رو پاک کردم.  
> روی همون endpointهای داغ، p50/p95 پاسخ حدوداً نصف شد.

### چجوری technically کردی (داستان قابل دفاع)

1. **شناسایی hot path**  
   - لاگ/Seq یا timing روی handlerهای پرتکرار (مثلاً list پرسنل، claim سایت، داده‌ی گزارش).  
   - دیدی بخش زیاد زمان = DB + گاهی remote call، نه CPU خالص.

2. **انتخاب الگوی کش**  
   - **Cache-aside** با HybridCache (`GetOrCreateAsync`).  
   - L1 کوتاه‌تر (مثلاً چند دقیقه)، L2 بلندتر (مثلاً ~۲۰ دقیقه) — مطابق تنظیمات معمول Dejban.  
   - برای داده‌ای که باید بین چند instance یکی باشه (مثل JWT blacklist) گاهی `DisableLocalCache` تا L1 باعث inconsistency نشه.

3. **کلید کش**  
   - کلید شامل: `siteId` / tenant + نوع entity + id یا hash کوئری.  
   - بدون tenant توی کلید → باگ امنیتی/داده اشتباه. اینو حتماً بگو؛ مصاحبه‌گرها عاشقشن.

4. **Invalidation**  
   - بعد از Create/Update/Delete: `RemoveAsync` یا `RemoveByTagAsync` (مثلاً tagهایی مثل `UserSiteClaims`).  
   - بدون invalidation، عدد latency قشنگه ولی داده stale می‌مونه → trade-off رو خودت بگو.

5. **Stampede**  
   - HybridCache معمولاً از concurrent factory تکراری روی یک key جلوگیری می‌کنه؛ بگو «از thundering herd جلوگیری شد».

### عدد ۵۰٪ رو چجوری دفاع کنی

> قبل از کش، میانگین پاسخ endpointهای list حدود X بود؛ بعد از کش روی cache-hit حدود نصف.  
> اندازه‌گیری: زمان handler در لاگ / duration تو Seq / یا DevTools Network روی همان API.  
> عدد مربوط به **hot read path با hit rate بالا** است، نه cold start و نه همه‌ی APIها.

### سؤال‌های احتمالی + جواب

| سؤال | جواب کوتاه |
|---|---|
| Cache miss چی می‌شه؟ | Factory می‌ره DB، بعد L1+L2 پر می‌شه. |
| Redis بیاد پایین؟ | تو استک ما fallback به `DistributedMemoryCache` هست؛ consistency بین instance ضعیف‌تر می‌شه ولی سرویس نمی‌خوابه. |
| چرا فقط MemoryCache نه؟ | چند instance / چند سرویس؛ L1 مشترک نیست. Redis = shared L2. |
| TTL چقدر؟ | Absolute؛ L1 کوتاه‌تر از L2. برای claim/report با tag invalidate می‌کنیم، فقط به TTL وابسته نیستیم. |
| Stale data؟ | Accept کردیم برای readهایی که near-real-time کافیه؛ برای داده حساس TTL کوتاه‌تر یا no-cache. |

### واژه‌هایی که باید بلد باشی
`HybridCache`, `IDistributedCache`, cache-aside, L1/L2, stampede, tag invalidation, TTL, cache key design, multi-instance consistency

---

## ۲) «توان پردازش فایل DCC رو ~۳× بردم بالا»

### چی بگی

> سرویس Document Control Center برای بانک ملت end-to-end بود: آپلود/دانلود/حذف نرم/بازیابی/حذف دائم.  
> گلوگاه اول **sync I/O پشت هم** و **نوشتن تک‌تک metadata** بود.  
> با **CQRS + MediatR** مسیر command رو async کردم، metadata رو batched/optimized نوشتم، و لایه‌ی storage رو از API جدا کردم (`IFileStorage`).  
> روی سناریوی پردازش دسته‌ای فایل، throughput حدوداً سه برابر شد.

### چجوری technically کردی

1. **جدا کردن concerns**  
   - API فقط orchestration.  
   - Command: تغییر state + metadata در Postgres (EF Core).  
   - File bytes: filesystem/abstraction (`IFileStorage`) — نه داخل DbContext.

2. **Async end-to-end**  
   - `async/await` تا پایین (نه `Task.Result`).  
   - جلوگیری از block شدن thread pool موقع I/O فایل.

3. **Pipeline CQRS**  
   - Validation با FluentValidation قبل از handler.  
   - Handler باریک: validate → store file → persist metadata → (در صورت نیاز) event/outbox.

4. **بهینه‌سازی throughput**  
   - به‌جای N تا SaveChanges جدا برای N فایل، batch / یک Unit of Work در scope منطقی.  
   - جلوگیری از load کردن کل فایل در memory وقتی streaming ممکنه.  
   - Soft delete = فقط flag/metadata؛ hard delete جدا و کنترل‌شده.

5. **امنیت که باید کنارش بگی**  
   - JWT + چک دسترسی فایل؛ IDOR ممنوع.  
   - این نشون می‌ده فقط «سرعت» نبوده.

### عدد ۳× رو چجوری دفاع کنی

> با یک workload مصنوعی/واقعی: تعداد فایل پردازش‌شده در واحد زمان قبل/بعد.  
> قبل: پردازش ترتیبی و SaveChanges مکرر.  
> بعد: pipeline async + کاهش round-trip دیتابیس و I/O بهتر.  
> ۳× روی **batch upload/processing** بود، نه لزوماً یک فایل تکی خیلی بزرگ.

### سؤال‌های احتمالی + جواب

| سؤال | جواب |
|---|---|
| چرا فایل تو DB نه؟ | حجم بالا، backup سنگین، latency؛ DB برای metadata، disk/object برای blob. |
| Soft delete چیه؟ | `IsDeleted` + audit؛ بازیابی ممکن؛ hard delete جدا. |
| Transaction؟ | Metadata در تراکنش DB؛ فایل و DB dual-write کلاسیک — در عمل ترتیب store+persist و جبران خطا/orphan cleanup مهمه. |
| CQRS اینجا چی داد؟ | جدا شدن write model، validation pipeline، تست‌پذیری handler. |

### واژه‌ها
CQRS, MediatR, FluentValidation, Unit of Work, streaming I/O, soft delete, metadata vs blob, IDOR

---

## ۳) «بار پیک دیتابیس رو ~۴۰٪ کم کردم (کش سرور + TanStack Query)»

### چی بگی

> فشار پیک Postgres فقط از بک‌اند نبود؛ فرانت هم برای list/detail هی refetch می‌کرد.  
> دو لایه گذاشتم:  
> ۱) **server cache** (HybridCache/Redis)  
> ۲) **TanStack Query** سمت کلاینت با `staleTime` مناسب و invalidation بعد از mutation.  
> نتیجه‌اش کمتر شدن queryهای تکراری و حدود ۴۰٪ افت در peak connections/queries روی مسیرهای پرترافیک.

### چجوری technically کردی

**سمت سرور**
- همان cache-aside بخش ۱ روی queryهای list/detail.
- پروجکشن سبک (نه load کل aggregate وقتی فقط لیست لازم است).
- `AsNoTracking` برای readهای خالص.

**سمت کلاینت (TanStack Query)**
- `queryKey` پایدار و سلسله‌مراتبی (مثلاً `['personnels', siteId, filters]`).
- `staleTime`: داده‌ی نسبتاً ثابت → کمتر refetch خودکار.
- بعد از mutation موفق: `invalidateQueries` روی همان keyها — نه `refetch` بی‌هدف همه‌چیز.
- جلوگیری از waterfall: parallel queries جایی که وابسته نیستن.

### عدد ۴۰٪ رو چجوری دفاع کنی

> از مانیتورینگ DB / تعداد query در بازه‌ی پیک کاری، یا شمارش hit روی endpoint list قبل/بعد.  
> بخش مهم: تکراری‌های یک صفحه (mount مجدد، tab focus، pagination برگشتی) با client cache حذف شدن.  
> ۴۰٪ روی **peak**، نه میانگین شبانه‌روزی.

### سؤال‌های احتمالی + جواب

| سؤال | جواب |
|---|---|
| فرق server cache و React Query؟ | React Query کش مرورگر/سشن کاربر؛ Redis بین همه‌ی کاربران/instanceها. مکمل هم هستن. |
| داده‌ی کاربر A به B نره؟ | کلیدها شامل user/site/auth context؛ cache جدا. |
| Optimistic update؟ | جایی که UX لازم بود؛ وگرنه invalidate بعد از success ساده‌تر و امن‌تره. |

### واژه‌ها
TanStack Query, queryKey, staleTime, invalidateQueries, AsNoTracking, projection, peak load

---

## ۴) «توان/قابلیت اطمینان messaging رو ~۲× با MassTransit + Outbox/Inbox»

### چی بگی

> بین ماژول‌ها (پرسنل، ACL، Identity، …) با event حرف می‌زدیم.  
> مشکل کلاسیک: ذخیره در DB موفق بشه ولی publish به RabbitMQ fail کنه (dual-write).  
> **Transactional Outbox**: event داخل همان تراکنش DB ذخیره می‌شه، بعد dispatcher می‌فرسته.  
> سمت مصرف‌کننده **Inbox + idempotency** تا دوبار process نشه.  
> نتیجه‌اش throughput مفید بالاتر و retry/خطای تکراری کمتر؛ حدود ۲× از نظر کار موفق در واحد زمان.

### چجوری technically کردی

1. Domain event داخل ماژول → outbox row در همان `SaveChanges`.  
2. Job/dispatcher (مثلاً Quartz) outbox را می‌خواند → `IEventBus` / MassTransit → RabbitMQ.  
3. Consumer:  
   - Inbox: «این message id قبلاً خورده؟»  
   - اگر خورده → no-op.  
   - اگر نه → handle + mark consumed.  
4. گاهی decorator روی handler برای idempotency شفاف (الگوی Scrutor).  
5. Retry/backoff MassTransit برای خطای گذرا؛ نه swallow خاموش.

### عدد ۲× رو چجوری دفاع کنی

> قبل: بخشی از پیام‌ها یا گم می‌شد یا با retry دستی/دوباره کاری می‌موند؛ صف پر از redelivery بی‌فایده.  
> بعد: پیام‌های business-successful بیشتر در واحد زمان، چون dual-write و duplicate work کم شد.  
> «۲×» = بهبود **useful throughput / reliability**، نه اینکه Rabbit سریع‌تر شد.

### سؤال‌های احتمالی + جواب

| سؤال | جواب |
|---|---|
| Outbox چیه؟ | جدول outbox در همان DB تراکنش کسب‌وکار؛ بعداً publish. |
| Inbox چیه؟ | ثبت پیام مصرف‌شده برای exactly-once *effect* (at-least-once delivery + idempotent handler). |
| Exactly-once واقعی؟ | روی broker معمولاً at-least-once؛ exactly-once را با idempotency شبیه‌سازی می‌کنیم. |
| چرا MassTransit؟ | abstraction روی retry, DI consumers, request/response, outbox integration. |

### واژه‌ها
MassTransit, RabbitMQ, dual-write, transactional outbox, inbox, idempotency, at-least-once, integration event vs domain event

---

## ۵) «YARP + ProblemDetails؛ گزارش Stimulsoft ~۳۵٪ سریع‌تر»

### چی بگی (دو تکه کن؛ قاطی نکن)

**تکه A — Gateway**  
> APIها نسخه‌بندی شدن (`/api/v{version}/...`) و از **YARP** رد می‌شن.  
> خطاها رو با **ProblemDetails** یکدست کردم تا فرانت بتونه استاندارد handle کنه، نه هر سرویس یک shape جدا.

**تکه B — Stimulsoft**  
> رندر گزارش سنگین بود (داده + enging گزارش).  
> داده‌ی گزارش را cache کردم (کلید با site + hash پارامترها)، و از refetchهای تکراری فرانت کم کردم.  
> زمان انتظار کاربر تا آماده‌شدن گزارش حدود ۳۵٪ کمتر شد.

### چجوری technically کردی

**YARP**
- `ApiGateway` با `LoadFromConfig` → clusterها (dejban, identity, dcc, …).  
- Nginx لبه → YARP → سرویس‌ها.  
- Auth روی بعضی routeها (`anonymous` / `default`) + بازبینی JWT در خود سرویس (defense in depth).

**ProblemDetails**
- به‌جای exception متن آزاد یا مدل خطای پراکنده، RFC 7807-style.  
- فرانت یک mapper برای status/title/errors.

**Stimulsoft tuning (داستان دفاع‌پذیر)**
- Cache نتیجه‌ی query گزارش (نه لزوماً کل PDF باینری اگر شخصی/حساس است).  
- کم کردن round-trip: یک بار fetch داده، بعد render.  
- جلوگیری از generate مجدد با همان فیلتر در بازه‌ی کوتاه.  
- اگر ticket/access برای گزارش دارید، بگو short-lived access ticket جدا از داده.

### عدد ۳۵٪ رو چجوری دفاع کنی

> Stopwatch از کلیک کاربر تا نمایش/دانلود گزارش در محیط تست/استیج، قبل و بعد از cache + حذف درخواست تکراری.  
> ۳۵٪ روی گزارش‌های پرتکرار با پارامتر ثابت‌تر؛ گزارش یک‌بارمصرف ممکنه کمتر سود ببره.

### سؤال‌های احتمالی + جواب

| سؤال | جواب |
|---|---|
| چرا YARP نه فقط Nginx؟ | Nginx لبه/استاتیک/فرانت؛ YARP داخل شبکه‌ی .NET برای route/API/auth/policy بین سرویس‌ها. |
| Versioning چرا؟ | Breaking change بدون شکستن کلاینت قدیم. |
| ProblemDetails فایده‌اش؟ | قرارداد یکسان خطا برای همه‌ی APIها و UX بهتر فرانت. |

### واژه‌ها
YARP reverse proxy, API versioning, ProblemDetails, report cache key, Stimulsoft

---

## ۶) «چرخه‌ی انتشار ~۳۰٪ سریع‌تر با Docker + GitLab CI + SignalR»

### چی بگی (دو تکه)

**تکه A — Delivery**  
> سرویس‌ها containerize شدن و pipeline گیت‌لب برای build/test/deploy اومد.  
> کارهای دستی تکراری (build محلی، کپی فایل، تنظیم محیطی) کم شد؛ از commit تا استیج حدود ۳۰٪ کوتاه‌تر شد.

**تکه B — SignalR**  
> به‌جای polling برای وضعیت‌های زنده (مثلاً sync دستگاه/نوتیف)، **SignalR** گذاشتیم.  
> بار اضافه HTTP کم شد و UX بلادرنگ شد — این جدا از متریک ۳۰٪ انتشار است؛ تو یک بولت رزومه کنار هم اومدن.

### چجوری technically کردی

**Docker / CI**
- `Dockerfile` چندمرحله‌ای (restore → build → publish → runtime image کوچک).  
- `docker-compose` برای وابستگی‌ها (Postgres, Redis, RabbitMQ, …).  
- GitLab CI stages: build → test → deploy.  
- کمتر شدن «روی ماشین من کار می‌کرد».

**SignalR**
- Hub برای push event به کلاینت‌های متصل.  
- Auth روی هاب (JWT).  
- فرانت subscribe؛ به‌جای setInterval هر N ثانیه.

### عدد ۳۰٪ رو چجوری دفاع کنی

> مقایسه‌ی مدت زمان معمول release قبل (دستی/نیمه‌دستی) و بعد (pipeline سبز تا استیج/پرود).  
> ۳۰٪ میانگین روی چند انتشار متوالی، نه یک بار خوش‌شانس.

### سؤال‌های احتمالی + جواب

| سؤال | جواب |
|---|---|
| Multi-stage Docker یعنی چی؟ | SDK برای build، ASP.NET runtime برای run → image کوچک‌تر/امن‌تر. |
| SignalR scale-out؟ | با چند سرور نیاز به backplane (مثلاً Redis) — تو استک فعلی اگر backplane نبود صادقانه بگو single-node یا sticky. |
| CI چی تست می‌کرد؟ | حداقل build + تست‌های واحد/معماری؛ E2E اگر داشتید جدا بگو. |

### واژه‌ها
multi-stage build, GitLab CI stages, artifact, SignalR hub, polling vs push

---

## ۷) «kadooseng.com — لود صفحه ~۴۰٪ بهتر»

### چی بگی

> پرتال شرکتی رو end-to-end نوشتم.  
> اول bundle بزرگ و درخواست‌های آبشاری داشتیم.  
> با **code-splitting**، فشرده‌سازی/بهینه‌سازی asset، و **کش پاسخ API**، LCP/لود اول حدود ۴۰٪ بهتر شد.

### چجوری technically کردی

1. Route-based / component lazy load → کمتر JS اولیه.  
2. تصویر و استاتیک: compression، سایز درست، cache header.  
3. API: کش کوتاه‌مدت برای داده‌ی نسبتاً ثابت صفحه فرود.  
4. اندازه‌گیری با Lighthouse یا Network waterfalls قبل/بعد.

### دفاع عدد
> Lighthouse Performance / زمان `DOMContentLoaded` یا LCP قبل و بعد روی همان صفحه.

---

## ۸) بولت AI رزومه (~۸۰٪ سرعت کدنویسی)

اگه پرسیدن:

> از Cursor/Codex/ChatGPT برای اکتشاف کدبیس بزرگ، اسکلت handlerها، تست‌های تکراری و دیباگ سریع استفاده می‌کنم.  
> سرعت تحویل feature بالاتر رفته، ولی **مرور و مالکیت کد با منه** — AI جایگزین فهم معماری نیست.  
> ۸۰٪ یعنی روی کارهای تکراری/boilerplate، نه طراحی دامنه از صفر.

مصاحبه‌گر خوب می‌خواد بشنوه: AI را ابزار کردی، نه اینکه کپی‌پیست بدون فهم.

---

## ۹) چطور متریک بگو تا باورپذیر بمونه

قالب طلایی جواب (هر متریک):

1. **مشکل:** چه چیزی کند/شکننده بود؟  
2. **اندازه قبل:** تقریباً چی بود؟  
3. **اقدام:** ۲–۴ قدم فنی.  
4. **اندازه بعد:** چه تغییری دیدید؟  
5. **Trade-off:** چه چیزی سخت‌تر شد؟ (stale data، پیچیدگی invalidation، عملیات Redis، …)

مثال کامل شفاهی (~۴۵ ثانیه):

> Listهای پرترافیک هر بار DB را می‌زدند و در ساعت شلوغی latency می‌رفت بالا.  
> HybridCache گذاشتیم با کلید شامل SiteId، و روی update با tag invalidate می‌کردیم.  
> فرانت هم با TanStack Query refetch الکی نمی‌کرد.  
> روی همان endpointها پاسخ حدود نصف شد و فشار پیک DB حدود ۴۰٪ آمد پایین.  
> هزینه‌اش پیچیدگی invalidation بود؛ برای داده‌ی حساس TTL کوتاه‌تر گذاشتیم.

---

## ۱۰) چیزهایی که نباید بگی (تا نسوزی)

- «همه‌ی APIهای سیستم ۵۰٪ سریع‌تر شدن» → بگو **hot paths**.  
- «Exactly-once واقعی روی Rabbit» → بگو **idempotent consumer**.  
- «Redis backplane برای SignalR داشتیم» مگر مطمئنی — تو یادداشت‌های استک، Redis بیشتر L2 کش است نه لزوماً SignalR backplane.  
- جزئیات ساختگی بیش از حد دقیق (مثلاً «۳۴۷ میلی‌ثانیه») → مشکوک؛ همان `~` بهتره.  
- اگر چیزی را عمیق نکردی، برو سراغ لایه‌ی بالاتر و trade-off؛ درجا داستان ریز نساز.

---

## ۱۱) چک‌لیست تسلط یک‌شبه (قبل مصاحبه)

برای هر مورد، با صدای بلند در ۶۰ ثانیه توضیح بده:

- [ ] HybridCache L1/L2 + invalidation + کلید tenant  
- [ ] DCC: metadata در DB، فایل در storage، soft delete، CQRS  
- [ ] TanStack Query: queryKey، staleTime، invalidate بعد mutation  
- [ ] Outbox/Inbox و فرق domain vs integration event  
- [ ] YARP کجای معماری است (Nginx → YARP → services)  
- [ ] ProblemDetails چرا بهتر از error آزاد است  
- [ ] Docker multi-stage + ایده‌ی pipeline CI  
- [ ] SignalR به‌جای polling  

اگر یکی گیر کرد، همان بخش را از فایل‌های یادگیری خودت بخوان:
- `day-25-hybridcache-redis.md`
- `technical-learning/19-redis.md`
- `day-20-masstransit-rabbitmq.md` / outbox-inbox days
- `technical-learning/00-yarp-config-investigation.md`
- `day-26-signalr-server.md` / `technical-learning/13-signalr.md`

---

## ۱۲) نقشه‌ی یک‌خطی معماری (برای کشیدن روی تخته)

```text
Browser (Next/React + TanStack Query + SignalR client)
   → Nginx
     → YARP ApiGateway (JWT / route / versioning)
       → Dejban / Identity / DCC / ACL / Reporting
            ↘ Postgres (EF metadata + outbox)
            ↘ Redis (HybridCache L2, blacklist, tags)
            ↘ RabbitMQ (MassTransit)
            ↘ File storage (DCC IFileStorage)
```

هر متریک رزومه را روی یکی از این فلش‌ها سنگر بگیر:
- ۵۰٪ و ۴۰٪ → Redis + Query  
- ۳× → DCC storage/CQRS  
- ۲× → Rabbit + Outbox/Inbox  
- ۳۵٪ → Reporting path  
- ۳۰٪ → Docker/CI (+ SignalR جدا برای realtime)

---

موفق باشی. اگر خواستی، نسخه‌ی کوتاه «cheat sheet یک صفحه» هم از همین فایل جدا می‌کنم.
