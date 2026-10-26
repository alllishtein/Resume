# Docker و Docker Compose در این مخزن

شناسهٔ کاتالوگ: `03-docker-compose`.

پیش‌نیاز: `02-configuration.md`. آن درس می‌گوید متغیر محیط با `__` به درخت ASP.NET Core می‌رسد و `globalAppsettings` فقط کلیدهایی را می‌برد که خودش دارد. اینجا همان کلیدها از دید کانتینر دنبال می‌شوند.

رمز، connection string کامل، و مقدار پیش‌فرض داخل `${VAR:-...}` در این سند نیست. کانتینر اجرا نشد و image ساخته نشد.

## کانتینر چه مسئله‌ای را حل می‌کند

یک سرویس .NET به runtime، کتابخانه، و فایل پیکربندی وابسته است. اگر هر سرور این‌ها را دستی نصب کند، نسخهٔ runtime روی لپ‌تاپ با سرور فرق می‌کند و جملهٔ «روی ماشین من کار می‌کرد» بی‌معنی می‌شود.

ماشین مجازی یک سیستم‌عامل کامل را تقلید می‌کند. هسته، دیسک، و شبکهٔ خودش را دارد. سنگین است، چون هر نمونه یک OS جدا بالا می‌آورد.

کانتینر همان هستهٔ سیستم‌عامل میزبان را با بقیه شریک می‌شود و فقط پردازه، فایل‌سیستم، و شبکهٔ خودش را جدا می‌کند. برای این مخزن معنی‌اش این است که `dejban` و `identityserver` دو پردازهٔ جدا هستند، هر کدام با فایل‌های image خودشان، ولی لازم نیست برای هر کدام یک ویندوز یا لینوکس مجازی ساخته شود.

تصویر (image) بستهٔ آماده‌است: runtime و DLLهای publishشده. کانتینر یک نمونهٔ در حال اجرا از آن تصویر است. از یک image به نام `dejban:latest` می‌شود چند کانتینر ساخت. در Compose این مخزن برای هر سرویس اپ یک `container_name` ثابت هست، پس از همان نام بیش از یک کانتینر همزمان ساخته نمی‌شود.

Dockerfile دستور ساخت image است. Docker Compose چند کانتینر، شبکه، و volume را با هم توصیف می‌کند. Compose خودش کد C# را کامپایل نمی‌کند، مگر سرویسی بلوک `build` داشته باشد.

زمان build لحظه‌ای است که `dotnet publish` داخل stageهای Dockerfile اجرا می‌شود و فایل‌ها داخل image کپی می‌شوند. زمان start لحظه‌ای است که کانتینر از image ساخته می‌شود، متغیر محیط به پردازه می‌رسد، و `ENTRYPOINT` اجرا می‌شود. عوض کردن `ConnectionStrings__Postgres` در Compose نیاز به build دوباره ندارد، چون متغیر موقع start تزریق می‌شود. عوض کردن کد C# بدون build یا load کردن image جدید به کانتینر نمی‌رسد.

## واژه‌هایی که Compose استفاده می‌کند

سرویس یک کانتینر توصیف‌شده در فایل YAML است. نام سرویس در شبکهٔ Compose به DNS تبدیل می‌شود. `container_name` اسم دیگری برای همان کانتینر در دستور `docker ps` است. در این مخزن اغلب این دو رشته یکی هستند، مثل `dejban`.

شبکهٔ bridge کانتینرهای همان شبکه را به هم وصل می‌کند. کانتینر شبکهٔ دیگر آن نام را نمی‌بیند، مگر پورت روی host منتشر شده باشد و از راه host برگردد.

volume داده را بیرون از لایهٔ قابل‌نوشتن کانتینر نگه می‌دارد. volume نام‌دار را Docker مدیریت می‌کند و با stop معمولی پاک نمی‌شود. bind mount یک پوشهٔ host را داخل کانتینر نشان می‌دهد. فایل‌سیستم خود کانتینر، اگر هیچکدام نباشد، با حذف کانتینر از بین می‌رود.

پورت داخلی پورتی است که پردازه داخل کانتینر گوش می‌دهد. پورت host سمت چپ نگاشت `host:container` است. `18004:5432` یعنی از بیرون میزبان به پورت 18004 وصل می‌شوی و Docker آن را به پورت 5432 داخل کانتینر Postgres می‌رساند. کانتینر هم‌شبکه لازم نیست از 18004 استفاده کند. نام سرویس و پورت داخلی برای او کافی است.

`depends_on` فقط ترتیب شروع را می‌گوید. `condition: service_healthy` یعنی healthcheck باید موفق شود. `condition: service_started` یعنی پردازه شروع شده، نه اینکه دیتابیس آمادهٔ query باشد. `restart: unless-stopped` یعنی بعد از خطا Docker دوباره اجرا می‌کند، مگر کسی خودش stop کرده باشد.

## فایل‌های این مخزن

هیچ‌کدام از Composeهای خوانده‌شده کلید `profiles` ندارند. جایی که `build` هست، کلید `target` نیست. در Dockerfile مرحلهٔ آخر `final` است. ننوشتن `target` یعنی Docker همان آخرین stage را می‌سازد. این رفتار پیش‌فرض Docker است و با اجرای build در این فاز تأیید نشد. نبود کلید `target` در YAML: `verified`.

### بک‌اند، سه فایلی که اسکریپت واقعاً با هم بالا می‌آورد

`infrastructure/offline-mode/start-offline.sh` تابع `start_backend` این سه فایل را با هم به `docker compose` می‌دهد:

- `docker-compose.yml`
- `docker-compose.development.yml`
- `docker-compose.docker-development.yml`

`docker/import-and-run.sh` همان سه فایل را بعد از `docker load` بالا می‌آورد. هر دو `--no-build --pull never` دارند. یعنی انتظارشان image از قبل loadشده است، نه build آنلاین.

`docker-compose.yml` شبکهٔ `backend` با subnet `10.10.0.0/24` را می‌سازد و سرویس‌های داده را روی آن می‌گذارد. image پستیگرس این فایل `postgres` است، بدون tag. Redis برابر `redis` بدون tag است. RabbitMQ برابر `rabbitmq:management` است. پورت host در خود این فایل برای دیتابیس‌ها نیست. volume نام‌دار هست، مثلاً `identityserverdb-data` روی `/var/lib/postgresql`. healthcheck پستیگرس `pg_isready` است. Redis در این فایل volume فعال ندارد. بلوک volume و `redis-server --save` کامنت است. دادهٔ Redis با حذف کانتینر می‌ماند فقط اگر جای دیگری ذخیره شده باشد. در این فایل نشده است.

`docker-compose.development.yml` فقط پورت host را به سرویس‌های همان پروژه اضافه می‌کند: `18001:5432` تا `18007:5432` برای هفت دیتابیس، `5672` و `15672` برای RabbitMQ، `6379` برای Redis، `19000:9000` و `19001:9001` برای MinIO. Seq و Jaeger داخل کامنت‌اند و سرویس فعال نیستند.

`docker-compose.docker-development.yml` هشت سرویس اپ را اضافه می‌کند. هر کدام `build.context` برابر `.` و یک Dockerfile دارند، `networks: [backend]`، محیط `ASPNETCORE_ENVIRONMENT=DockerDevelopment`، و bind به `./GlobalAppsettings:/app/GlobalAppsettings`. `depends_on` دژبان این است: `dejbandb` و `eventbus` و `redis` با `service_healthy`، و `mediamtx` با `service_started`. gateway پورت `7036:443` را منتشر می‌کند و به شروع `identityserver` با `service_started` وابسته است. این فایل کلید `ConnectionStrings__Postgres` ندارد.

نگاشت پورت دیتابیس در override توسعه، که با فایل پایه یکی است:

| سرویس | پورت host | پورت داخل کانتینر | `POSTGRES_DB` |
|---|---|---|---|
| `identitydb` | 18001 | 5432 | `payamgostar_identity` |
| `requesttrackerdb` | 18002 | 5432 | `payamgostar_requesttracker` |
| `aclserverdb` | 18003 | 5432 | `payamgostar_aclserver` |
| `dejbandb` | 18004 | 5432 | `payamgostar_dejban` |
| `dccdb` | 18005 | 5432 | `payamgostar_dcc` |
| `reportingdb` | 18006 | 5432 | `payamgostar_reporting` |
| `gateserverdb` | 18007 | 5432 | `payamgostar_gateserver` |

همین نام‌ها در `docker-compose.yml` و در `docker/compose.data.yml` نوشته شده‌اند. پورت host از `docker-compose.development.yml` و از خود `compose.data.yml` می‌آید، نه از فایل پایه.

### دو فایل جدا برای سرور داده و سرور اپ

`docker/compose.data.yml` پروژهٔ Compose به نام `dejban-data` و شبکهٔ `dejban-data` است. کامنت فایل می‌گوید اپ این‌جا نیست و اپ از پورت‌های منتشرشدهٔ host وصل می‌شود. image پستیگرس اینجا `postgres:latest` است، نه `postgres` بدون tag و نه `postgres:18.1`. پورت‌ها همان 18001 تا 18007 هستند. Redis دستور `redis-server --bind 0.0.0.0 --protected-mode no` دارد، پورت `6379:6379`، و volume ندارد. MinIO داده را در volume نام‌دار `minio-data` روی `/data` می‌گذارد.

`docker/compose.backend.yml` پروژهٔ جدا به نام `dejban-backend` و شبکهٔ `dejban-backend` است. هشت image از قبل ساخته‌شده را صدا می‌زند: `identityserver:latest`، `dcc:latest`، `reporting:latest`، `requesttracker:latest`، `aclserver:latest`، `dejban:latest`، `gateserver:latest`، `apigateway:latest`. بلوک `build` ندارد. فقط gateway پورت منتشر می‌کند: `7036:443`. healthcheck اپ در این فایل نیست. `restart: unless-stopped` از anchor به نام `app` می‌آید.

این دو فایل به شبکهٔ هم وصل نیستند. کامنت `compose.data.yml` همین را می‌گوید. اسکریپتی داخل مخزن که `compose.data.yml` را اجرا کند در جستجوی `*.sh` پیدا نشد. `infrastructure/postgres-dr/README.md` می‌گوید `./offline.sh data start` همان فایل را بالا می‌آورد، ولی فایلی به نام `offline.sh` در درخت جستجو نبود. پس قصد از روی کامنت و README است. اجرای آن اسکریپت غایب تأیید نشد.

### بقیهٔ فایل‌ها

`docker-compose.docker-production.yml` همان سرویس‌های اپ را با `build` و image به شکل `${DOCKER_REGISTRY-}...` توصیف می‌کند و باز `GlobalAppsettings` را mount می‌کند. Seq و Jaeger کامنت‌اند.

`docker-compose.development-clean.yml` شبکه و سرویس دادهٔ خودش را دارد و اسم بعضی volumeها پسوند `-new` دارد، مثل `identityserverdb-data-new`. این همان volume به نام `identityserverdb-data` نیست. بالا آوردنش دادهٔ فایل اصلی را نشان نمی‌دهد و دادهٔ جدید جدا می‌سازد.

`docker-compose.minio.yml` فقط MinIO را جدا توصیف می‌کند.

`infrastructure/postgres-dr/docker-compose.standby.yml` و `docker-compose.backup.yml` image را از `POSTGRES_IMAGE` می‌گیرند و پیش‌فرض README برابر `postgres:18.1` است. README خودش هشدار می‌دهد که `postgres:latest` روی دو ماشین ممکن است یک نسخه نباشد. این سه رشته را یکی ندانید: `postgres` بدون tag در `docker-compose.yml`، `postgres:latest` در `compose.data.yml`، و `postgres:18.1` به‌عنوان پیش‌فرض کیت DR.

### فرانت

`dejban_frontend_new/docker-compose.yml` پروژهٔ `dejban-frontend` و شبکهٔ `dejban-frontend` است. کامنت می‌گوید به شبکهٔ بک‌اند وصل نیست و اسم کانتینر بک‌اند را دوباره استفاده نمی‌کند. سرویس‌ها: `nginx` با image برابر `nginx:1.27-alpine`، و `main`، `dejban`، `gate`، `dcc`، `access-control`. اپ‌های Next با `docker/Dockerfile.next` و build arg از جمله `NEXT_PUBLIC_SERVER_URL: /api/v1` ساخته می‌شوند. access-control با `docker/Dockerfile.access-control` و `VITE_SERVER_URL: /api/v1`. Nginx پورت `${FRONTEND_PORT:-3080}:80` را منتشر می‌کند و `API_GATEWAY` پیش‌فرضش `host.docker.internal:7036` است. `depends_on` فقط لیست اپ‌هاست، بدون healthcheck.

`docker-compose.nginx-only.yml` پروژه و کانتینر دیگری است (`frontend-nginx-only`) و اپ Next را build نمی‌کند.

## Dockerfile چه می‌سازد

هشت Dockerfile بک‌اند الگوی چندمرحله‌ای دارند. مرحلهٔ `base` از `mcr.microsoft.com/dotnet/aspnet:10.0` است، `WORKDIR /app`، و `EXPOSE 80`. مرحلهٔ `build` از `mcr.microsoft.com/dotnet/sdk:10.0` است، csprojها را کپی می‌کند، `dotnet restore` می‌زند، بعد `COPY . .` و `dotnet build`. مرحلهٔ `publish` دستور `dotnet publish ... -o /app/publish /p:UseAppHost=false` را می‌زند. مرحلهٔ `final` فقط خروجی publish را در image اجرا کپی می‌کند. `ENTRYPOINT` برای دژبان `dotnet Dejban.Api.dll` است و برای بقیه به همان شکل نام DLL خودشان.

`EXPOSE 80` پورت را روی host منتشر نمی‌کند. فقط سند image است. گوش دادن واقعی از `ASPNETCORE_HTTP_PORTS=80` در Compose می‌آید، و برای gateway علاوه بر آن `ASPNETCORE_HTTPS_PORTS=443` چون نگاشت `7036:443` است.

Dockerfileها `ARG BUILD_CONFIGURATION=Release` دارند و `dotnet publish` از همان متغیر استفاده می‌کند. بلوک‌های `build` در `docker-compose.docker-development.yml` کلید `args` و `target` ندارند. پس اگر Compose بسازد، مقدار پیش‌فرض همان ARG می‌ماند و stage آخر ساخته می‌شود. این رفتار پیش‌فرض Docker است و در این فاز build اجرا نشد.

`ApiGateway/Dockerfile` در stage نهایی با `USER root` پوشهٔ `/app/public-assets/public` را می‌سازد و دوباره `USER app` می‌شود. `Microservices/DCC/Dockerfile` در stage نهایی روی `USER root` می‌ماند. Reporting در stage پایه فونت نصب می‌کند و قبل از `EXPOSE` به `USER app` برمی‌گردد. کپی `GlobalAppsettings` داخل Dockerfile نیست. فایل global با bind mount به `/app/GlobalAppsettings` می‌رسد. اگر mount نباشد و فایل داخل image هم نباشد، `AddJsonFile` با `optional: false` بالا آمدن را می‌شکند. این شرط از درس 02 و از نبود دستور COPY برای آن پوشه در Dockerfile است.

### `modules.*.json` داخل image

`Dejban.Api.csproj` برای `modules.*.json` ویژگی `CopyToOutputDirectory` یا `CopyToPublishDirectory` ندارد. Dockerfile هم آن فایل‌ها را جدا COPY نمی‌کند. فقط خروجی `dotnet publish` به image نهایی می‌رود. زیر پوشهٔ `Dejban.Api` تنها `modules.personnels.json` کنار خود csproj است، نه یک کپی زیر `bin` یا `publish`. هدف‌های پیش‌فرض SDK وب هم در این فاز از روی فایل targets نصب‌شده خوانده نشد.

پس معلوم نیست image منتشرشده آن JSONها را دارد یا نه. اگر content root داخل کانتینر فایل اجباری `modules.{module}.json` را نداشته باشد، `AddModuleConfiguration` بالا آمدن دژبان را قطع می‌کند. اگر SDK آن‌ها را جزو content پابلیش کند، هستند. این دو حالت با هم جمع نمی‌شوند. وضعیت: `unresolved`.

## سه کلید پیکربندی، از Compose تا .NET

Docker متغیرهای بلوک `environment` را به پردازهٔ `ENTRYPOINT` می‌دهد. ASP.NET Core نام را با `__` به `:` درخت پیکربندی تبدیل می‌کند. `ConnectionStrings__Postgres` یعنی `ConnectionStrings:Postgres`. این قرارداد در درس 02 از روی Learn آمده است. اینجا فقط منبع Docker اضافه می‌شود.

provider دیرتر فقط کلیدی را عوض می‌کند که خودش دارد. فایل global کلید `ConnectionStrings` ندارد. پس رشتهٔ اتصال یا از `appsettings*.json` می‌ماند یا اگر Compose همان کلید را گذاشته باشد، متغیر محیط بر JSON پیش‌فرض می‌نشیند.

### `ConnectionStrings__Postgres`

در `docker/compose.backend.yml` هر سرویس اپ مقدار خودش را می‌گیرد. میزبان برابر `${DATA_HOST}` است و پورت host است، نه پورت داخلی 5432. دژبان پورت 18004 و دیتابیس `payamgostar_dejban` است. هویت 18001 و `payamgostar_identity`. گزارش علاوه بر `Postgres` کلیدهای `DejbanPostgres`، `IdentityPostgres`، و `AclPostgres` را هم دارد. gateway این کلید را ندارد.

این مقدار بر `appsettings.DockerDevelopment.json` می‌نشیند، چون متغیر محیط بعد از آن JSON پیش‌فرض است و global همان کلید را ندارد. درس 02 این ترتیب را شرح داده است.

در ادغام سه‌فایلی `start-offline.sh`، سرویس `dejban` این متغیر را ندارد. آن وقت JSON محیطی می‌ماند. در `appsettings.DockerDevelopment.json` دژبان، کلید Postgres مقدار `Host=dejbandb` دارد و در رشته‌ای که خوانده شد قطعهٔ `Port=` نبود. `dejbandb` نام سرویس روی شبکهٔ `backend` است. پورت 18004 فقط نگاشت host است. کانتینر هم‌شبکه به پورت داخلی سمت راست همان نگاشت، یعنی 5432، می‌رسد اگر درایور پورت پیش‌فرض خودش را همان بداند. اینکه Npgsql در نبود `Port=` واقعاً 5432 می‌زند اجرا نشد. وضعیت Host: `verified`. وضعیت پورت پیش‌فرض درایور: `unresolved`.

پس دو توپولوژی را قاطی نکنید. فایل split به host و پورت منتشرشده وصل است. فایل ادغامی، در غیاب متغیر، به نام سرویس Docker وصل است.

### `ConnectionStrings__Redis`

anchor به نام `app-env` در `compose.backend.yml` این کلید را ` ${DATA_HOST}:6379 ` می‌گذارد و همهٔ سرویس‌هایی که `<<: *app-env` دارند آن را می‌گیرند، از جمله gateway. رمز داخل این مقدار در آن خط نیست. فقط host و پورت است.

در ادغام سه‌فایلی این کلید روی سرویس دژبان ست نشده است. `appsettings.DockerDevelopment.json` دژبان مقدار `redis:6379` دارد و gateway در فایل DockerDevelopment خودش هم `redis:6379` دارد. `appsettings.json` و `appsettings.Development.json` دژبان `localhost:6379` هستند. `redis` نام سرویس در Compose است. `localhost` داخل کانتینر خود کانتینر است، نه Redis کناری.

Redis در Compose داده volume ندارد. restart کانتینر دادهٔ داخل لایهٔ کانتینر را نگه نمی‌دارد.

### `JwtSettings`

هیچ بلوک `environment` در `compose.backend.yml` یا `docker-compose.docker-development.yml` این کلید را نمی‌گذارد. منبعش فایل global است که با bind mount به `/app/GlobalAppsettings` می‌رسد و `Program.cs` آن را بعد از provider محیط بار می‌کند. چون فایل global این کلید را دارد، حتی اگر کسی همان کلید را در محیط بگذارد، JSON دیرتر برنده می‌شود. درس 02 این را گفته و اینجا فقط mount را اضافه می‌کند. مقدار JWT نقل نمی‌شود.

`AddCustomJwtAuth` همان مقدار را موقع ثبت سرویس داخل پارامترهای bearer کپی می‌کند. عوض کردن فایل روی volume، بدون restart پردازه، آن کپی را عوض نمی‌کند.

## شبکه و آدرس

```mermaid
flowchart LR
  browser["مرورگر روی host"]
  nginx["nginx:80 پورت host 3080"]
  gw["apigateway:443 پورت host 7036"]
  idn["identityserver"]
  dej["dejban"]
  idb["identitydb:5432"]
  ddb["dejbandb:5432"]
  red["redis:6379"]

  browser -->|"شبکه dejban-frontend"| nginx
  nginx -->|"host.docker.internal:7036"| gw
  gw -->|"http://identityserver روی backend"| idn
  gw -->|"http://dejban روی backend"| dej
  dej -->|"Host=dejbandb اگر env رشته را عوض نکند"| ddb
  idn -->|"نام identitydb روی backend"| idb
  dej -->|"redis:6379 در JSON داکر"| red
```

نمودار ادغام سه‌فایلی به‌علاوهٔ فرانت جداست، چون `start-offline.sh` بک‌اند را همان‌طور بالا می‌آورد و فرانت را با Compose جدا. فلش دژبان به `dejbandb` فقط وقتی است که `ConnectionStrings__Postgres` ست نشده باشد. در `compose.backend.yml` آن فلش عوض می‌شود و به `${DATA_HOST}:18004` می‌رود. فلش هویت هم همین شرط را دارد: `appsettings.DockerDevelopment.json` هویت مقدار `Host=identitydb` دارد و قطعهٔ `Port=` در آن رشته نیست. آدرس‌های YARP که خوانده شدند این‌ها هستند: `http://identityserver`، `http://requesttracker`، `http://dcc`، `http://aclserver`، `http://dejban`، `http://reporting`، `http://gateserver`، و `http://host.docker.internal:5053` برای باسکول. این نام‌ها با `container_name` سرویس‌های اپ در Compose ادغامی یکی هستند و هر دو روی شبکهٔ `backend`اند. باسکول در این Composeها سرویس نیست. `5053` پورت host بیرون از این فایل‌هاست.

فرانت به شبکهٔ `backend` وصل نیست. اگر کسی به‌جای `host.docker.internal:7036` نام `apigateway` را در Nginx بگذارد، DNS آن شبکه آن نام را ندارد.

## ماندگاری و ریسک

پستیگرس فایل پایه و فایل داده، volume نام‌دار روی `/var/lib/postgresql` دارند. اینکه این مسیر همان دایرکتوری دادهٔ image واقعی `postgres` یا `postgres:latest` باشد اجرا نشد. اگر image داده‌اش را جای دیگری بنویسد، volume خالی می‌ماند و داده داخل لایهٔ کانتینر می‌رود. این را باید با مستند همان tag چک کرد، نه با حدس.

RabbitMQ در `docker-compose.yml` مسیر `/var/lib/rabbitmq` را به `eventbusdb-data` وصل می‌کند و `definitions.json` را bind می‌کند.

MinIO در فایل داده، `/data` را به `minio-data` وصل می‌کند.

Redis عمداً پایدار نیست. کامنت فایل پایه این را نشان می‌دهد.

`dcc-storage` در `compose.backend.yml` فقط خواندنی روی `/app/uploads` سرویس `dcc` است. در gateway ادغامی، mount مربوط به `/app/public-assets` کامنت است.

ریسک امنیتی، بدون نقل مقدار: `compose.backend.yml` و فایل ادغامی برای رمز دیتابیس، RabbitMQ، MinIO، و رمز گواهی gateway یا fallback داخل YAML دارند یا مقدار را مستقیم در `environment` نوشته‌اند. `start-offline.sh` هم برای نبودن فایل pfx به یک رمز ثابت اشاره می‌کند. هر کس مخزن را دارد آن مقدارها را می‌بیند. این با secret manager یکی نیست. user secrets هم، طبق درس 02، مسیر این کانتینرها نیست چون محیط `DockerDevelopment` است.

`docker compose down -v` volume نام‌دار را پاک می‌کند. کامنت `compose.data.yml` می‌گوید این سوئیچ را نزنید. این درس هیچ volumeای را عوض نکرد.

## اگر چیزی بالا نیامد

این دستورها فقط می‌خوانند. `down`، `rm`، `volume rm`، و `-v` در این فهرست نیستند.

سرویس اصلاً start نمی‌شود: `docker compose ps` و `docker compose logs` همان سرویس. اگر پیام نبودن `globalAppsettings.{Environment}.json` بود، mount یا نام محیط غلط است. محیط ادغامی و فایل split هر دو `DockerDevelopment` هستند، پس فایل باید `globalAppsettings.DockerDevelopment.json` باشد نه فقط فایل `Development`.

وصل نشدن به Postgres: ببینید کدام Compose بالاست. در split، host باید `${DATA_HOST}` و پورت 18004 برای دژبان باشد و از داخل کانتینر اپ به آن host برسد. `extra_hosts: host.docker.internal:host-gateway` در anchor فایل split هست. در ادغام سه‌فایلی، اگر متغیر اتصال ست نشده، host باید نام سرویس `dejbandb` باشد و هر دو روی شبکهٔ `backend` باشند. healthcheck `pg_isready` فقط همان کانتینر دیتابیس را می‌گوید. `depends_on` با `service_started` روی gateway آماده بودن Postgres را ضمانت نمی‌کند.

وصل نشدن به Redis: در split آدرس `${DATA_HOST}:6379` است و Redis داده `protected-mode` را خاموش کرده تا غیر از loopback را بپذیرد. در ادغام، JSON می‌گوید `redis:6379`. `localhost:6379` داخل کانتینر اپ به Redis کناری نمی‌رسد. Redis اگر restart شده و volume نداشته، دادهٔ قبلی نیست. این خطای پیکربندی نیست. فراموشی ماندگاری است.

پورت اشغال است: نگاشت‌های 7036، 3080، 18001 تا 18007، 6379، 5672، و 15672 را با چیزی که روی host گوش می‌دهد مقایسه کنید. دو Compose که هر دو 18004 را منتشر کنند با هم بالا نمی‌آیند. `docker-compose.yml` تنها پورت دیتابیس را منتشر نمی‌کند. override توسعه و `compose.data.yml` منتشر می‌کنند. اگر هر دو پروژه همزمان همان پورت host را بگیرند، دومی خطا می‌دهد.

gateway و 502: YARP وقتی مقصد را نرسد 502 می‌دهد. `ProxyErrorHandlingMiddleware` وضعیت 502 و 500 را به 503 بدل می‌کند و برای مرورگر به `/error/503` می‌رود. پس در مرورگر 503 می‌بینید در حالی که علت پروکسی 502 بوده است. اول ببینید نام مقصد با سرویس همان شبکه یکی است. `http://dejban` روی شبکهٔ `dejban-frontend` حل نمی‌شود. `http://localhost:5042` داخل کانتینر gateway خود gateway است، نه دژبان. آن آدرس مال `appsettings` نمونه و پروفایل محلی است، نه مال `DockerDevelopment`.

فرق اجرای محلی و Docker: پروفایل `Dejban` محیط `Development` و آدرس `http://localhost:5042` دارد. JSON توسعهٔ دژبان Postgres را `localhost` و پورت 18004 می‌گذارد، به شرطی که داده پورت host را منتشر کرده باشد. Docker محیط `DockerDevelopment` است، global را از `/app/GlobalAppsettings` می‌خواند نه از چهار پوشه بالاتر، و YARP به نام سرویس وصل است. `dotnet run` روی ویندوز هیچ‌کدام از DNSهای `dejbandb` و `identityserver` را ندارد.

## سؤال‌های مصاحبه

### 1. کانتینر با ماشین مجازی چه فرقی دارد و این مخزن کدام را توصیف می‌کند؟

ماشین مجازی هستهٔ جدا دارد. کانتینر هسته را با host شریک می‌شود و پردازه و فایل را جدا می‌کند. Dockerfileهای این مخزن image را از `mcr.microsoft.com/dotnet/aspnet:10.0` می‌سازند و Compose چند کانتینر را روی یک شبکهٔ bridge می‌گذارد. فایل VM در این مسیرها نیست.

دنباله: image با کانتینر چه فرقی دارد؟

جواب: image خروجی build یا `docker load` است، مثل `dejban:latest`. کانتینر نمونهٔ در حال اجرای آن است و در این فایل‌ها `container_name: dejban` دارد.

### 2. چرا عوض کردن connection string در Compose به build دوباره نیاز ندارد، ولی عوض کردن کد نیاز دارد؟

متغیر `environment` موقع start به پردازه می‌رسد. `ENTRYPOINT` همان `dotnet Dejban.Api.dll` داخل image است. کد داخل image در stage `publish` با `dotnet publish` ثابت شده است. اسکریپت آفلاین عمداً `--no-build` می‌زند.

دنباله: `EXPOSE 80` پورت را باز می‌کند؟

جواب: نه. فقط سند image است. باز شدن روی host کار `ports` در Compose است. gateway `7036:443` دارد. بقیهٔ اپ‌ها در `compose.backend.yml` پورت host ندارند.

### 3. دو روش بالا آوردن بک‌اند این مخزن چیست؟

روش دارای اسکریپت: `start-offline.sh` سه فایل `docker-compose.yml` و `docker-compose.development.yml` و `docker-compose.docker-development.yml` را ادغام می‌کند. داده و اپ روی شبکهٔ `backend` هستند.

روش فایل‌های `docker/compose.data.yml` و `docker/compose.backend.yml`: دو پروژه و دو شبکهٔ جدا. اپ با پورت host به داده وصل می‌شود. اسکریپت `offline.sh` که README به آن ارجاع می‌دهد در درخت جستجو نبود.

دنباله: اگر فقط فایل پایه را بدون override توسعه بالا بیاورید، از لپ‌تاپ به Postgres وصل می‌شوید؟

جواب: نه از روی پورت host. خود `docker-compose.yml` برای دیتابیس `ports` ندارد. پورت 18004 از override یا از `compose.data.yml` می‌آید.

### 4. `18004:5432` را کانتینر دژبان چطور باید ببیند؟

18004 پورت host است. 5432 پورت داخل کانتینر `dejbandb` است. در فایل split، رشتهٔ اتصال دژبان پورت 18004 و host برابر `${DATA_HOST}` است، چون اپ در شبکهٔ داده نیست. در ادغام سه‌فایلی متغیر Postgres روی دژبان نیست و JSON داکر `Host=dejbandb` دارد. آن نام فقط روی شبکهٔ `backend` حل می‌شود.

دنباله: `localhost` داخل کانتینر دژبان یعنی چه؟

جواب: خود همان کانتینر. Postgres کناری را نشان نمی‌دهد. `appsettings.Development.json` با `localhost` برای `dotnet run` روی host است، جایی که پورت 18004 روی خود ماشین منتشر شده باشد.

### 5. `ConnectionStrings__Redis` و `JwtSettings` در Docker از یک منبع می‌آیند؟

نه. Redis در `compose.backend.yml` از anchor محیط به شکل آدرس `${DATA_HOST}:6379` به پردازه می‌رسد و چون global این کلید را ندارد، بر JSON می‌نشیند. در ادغام سه‌فایلی آن متغیر نیست و JSON داکر `redis:6379` را نگه می‌دارد. `JwtSettings` در environment این Composeها نیست. از bind پوشهٔ `GlobalAppsettings` می‌آید و چون آن JSON دیرتر بار می‌شود، کلیدهای خودش را می‌برد.

دنباله: چرا global کل پیکربندی را عوض نمی‌کند؟

جواب: provider دیرتر فقط کلیدهایی را که دارد جایگزین می‌کند. `AllowedHosts` در فایل پایهٔ global هست و در فایل `DockerDevelopment` نیست، پس پاک نمی‌شود. `ConnectionStrings` در global نیست، پس محیط یا `appsettings` همان درخت را نگه می‌دارد.

### 6. healthcheck این‌جا چه را ضمانت می‌کند و چه را نه؟

`pg_isready` و `redis-cli ping` و `rabbitmq-diagnostics ping` در فایل داده فقط همان سرویس را سالم می‌دانند. در ادغام، دژبان تا healthy شدن دیتابیس و Redis و Rabbit صبر می‌کند. gateway فقط تا `service_started` شدن `identityserver` صبر می‌کند، نه تا آماده شدن login. در `compose.backend.yml` اصلاً healthcheck اپ نیست و `identityserver` به شروع بقیهٔ اپ‌ها وابسته است، نه به Postgres.

دنباله: `restart: unless-stopped` جای healthcheck را می‌گیرد؟

جواب: نه. فقط بعد از خروج پردازه دوباره start می‌کند. اگر پردازه بالا باشد و دیتابیس را نبیند، restart نمی‌شود.

### 7. چرا gateway در Docker به `http://dejban` می‌رود و روی لپ‌تاپ به `localhost:5042`؟

`appsettings.DockerDevelopment.json` درگاه آدرس cluster دژبان را `http://dejban` گذاشته و Compose ادغامی همان نام را روی شبکهٔ `backend` دارد. پروفایل محلی و sample از `http://localhost:5042` استفاده می‌کنند، چون آنجا کانتینر و DNS سرویس وجود ندارد. محیط `DockerDevelopment` فایل JSON متناظر را انتخاب می‌کند.

دنباله: باسکول چرا `host.docker.internal:5053` است؟

جواب: در همان JSON مقصد `dejban-baskool-cluster` این آدرس است و سرویس باسکول در Composeهای خوانده‌شده نیست. پس از شبکهٔ Docker به یک پورت روی host برمی‌گردد. اینکه آن پورت واقعاً باز باشد اجرا نشد.

### 8. Redis چرا بعد از restart خالی به نظر می‌رسد؟

در `docker-compose.yml` ذخیره و volume کامنت است. در `compose.data.yml` سرویس Redis اصلاً `volumes` ندارد. داده روی فایل‌سیستم خود کانتینر است. Postgres برعکس volume نام‌دار دارد. قاطی کردن این دو رفتار یعنی انتظار persist از سرویسی که فایلش persist را خاموش کرده است.

دنباله: MinIO چطور؟

جواب: در فایل داده، `/data` به volume نام‌دار `minio-data` وصل است. restart همان volume را دوباره mount می‌کند. `down -v` آن را پاک می‌کند. این دستور در این درس اجرا نشد.

### 9. یک 502 از gateway را در این معماری کجا می‌گردید؟

اول شبکه. فرانت نام `apigateway` را نمی‌بیند. Nginx به `host.docker.internal:7036` می‌رود. gateway نام `dejban` را فقط اگر هر دو روی `backend` باشند می‌بیند. اگر مقصد down باشد YARP 502 می‌دهد و `ProxyErrorHandlingMiddleware` آن را برای کلاینت 503 می‌کند. پس لاگ پروکسی را ببینید، نه فقط status مرورگر.

دنباله: difference محلی چیست؟

جواب: `dotnet run` محیط Development است، global را چند پوشه بالاتر از پوشهٔ پروژه می‌خواند، و به `localhost` وصل است. کانتینر محیط DockerDevelopment است، global را از mount `/app/GlobalAppsettings` می‌خواند، و به نام سرویس وصل است.

### 10. کدام image پستیگرس را نباید یکی فرض کرد؟

`docker-compose.yml` مقدار `postgres` بدون tag دارد. `docker/compose.data.yml` مقدار `postgres:latest` دارد. کیت DR پیش‌فرض `postgres:18.1` دارد و README می‌گوید `latest` روی دو ماشین ممکن است فرق کند. tag بخشی از هویت image است. بدون tag یعنی Docker هر چه را برای آن نام محلی دارد استفاده می‌کند، نه الزاماً 18.1.

دنباله: `modules.*.json` حتماً داخل image دژبان است؟

جواب: از روی این مخزن ثابت نیست. csproj کپی صریح ندارد، Dockerfile فقط خروجی publish را برمی‌دارد، و یک خروجی publish محلی که فایل را نشان بدهد پیدا نشد. اگر داخل image نباشند، start دژبان به‌خاطر `optional: false` می‌شکند. این را باید با محتوای image دید، نه با حدس SDK.

## مرور

Compose این مخزن دو توپولوژی دارد. اسکریپت موجود، داده و اپ را روی شبکهٔ `backend` ادغام می‌کند و فرانت را جدا به پورت 7036 می‌فرستد. فایل‌های `docker/` داده و اپ را در دو شبکه می‌گذارند و اتصال را با پورت host می‌سازند. `ConnectionStrings__Postgres` فقط در فایل split به پردازه تزریق می‌شود. در ادغام، JSON داکر با نام سرویس می‌ماند. `JwtSettings` از mount می‌آید نه از environment. Redis ماندگار نیست. image پستیگرس سه شکل متفاوت دارد. بودن `modules.*.json` در image هنوز باز است و هیچ کانتینری در این فاز اجرا نشد.
