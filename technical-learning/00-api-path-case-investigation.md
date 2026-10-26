# تحقیق `/api` در برابر `/Api`

سؤال این است که مسیر حرف‌کوچک فرانت با الگوی حرف‌بزرگ YARP و با route حرف‌کوچک بک‌اند یکی است یا نه. پاسخ نباید از رفتار یک لایه به کل مسیر تعمیم داده شود.

اپ، تست، و درخواست HTTP اجرا نشدند. Context7 در این فاز در دسترس نبود. جملهٔ routing از Microsoft Learn، صفحهٔ Routing in ASP.NET Core با moniker شامل `aspnetcore-10.0`، نقل شده است. سورس match از tag `Yarp.ReverseProxy` `2.3.0` است.

وضعیت کل مسیر end-to-end: `unresolved` تا وقتی همان دو URL روی gateway این پروژه زده شوند. وضعیت هر لایه پایین جدا است.

## لایه‌ها

### 1. فرانت چه رشته‌ای می‌سازد

`verified` از روی کد و Compose.

- base داکر Next: `NEXT_PUBLIC_SERVER_URL` برابر `/api/v1` در `dejban_frontend_new/docker-compose.yml`.
- login: `/auth/login` در `packages/api-client/src/axiosInstance.ts`. نتیجهٔ داکر: `/api/v1/auth/login`.
- فهرست پرسنل: `/Personnels/GetPersonnels` در `apps/dejban/src/lib/api.js`. نتیجهٔ داکر: `/api/v1/Personnels/GetPersonnels`.

فرانت این دو رشته را به هم تبدیل نمی‌کند. تابعی برای عوض کردن حرف `api` پیدا نشد. اگر `NEXT_PUBLIC_SERVER_URL` در dev خالی باشد، base خالی است و مسیر نسبت به origin صفحه ساخته می‌شود. آن حالت اجرا نشد.

حرف‌های بعد از نسخه یکی نیستند: login در فرانت `auth/login` است و در YARP `Auth/Login`. پرسنل در هر دو `Personnels/GetPersonnels` است. پس فقط پیشوند `api`/`Api` موضوع مشترک هر دو درخواست است. login یک تفاوت حرف اضافه هم دارد.

### 2. Nginx

`verified` برای وجود دو location. اجرا نشده.

`docker/nginx/default.conf.template` هر دو را دارد:

- `location /api/` با `proxy_pass https://${API_GATEWAY};`
- `location /Api/` با همان `proxy_pass`

هیچ‌کدام modifier مثل `~*` ندارند و هیچ‌کدام مسیر را با `rewrite` عوض نمی‌کنند. `proxy_pass` بخش URI ندارد.

نتیجهٔ قابل‌اتکا از خود template: درخواستی که با `/api/` شروع شود location اول را دارد و درخواستی که با `/Api/` شروع شود location دوم را دارد. هر دو به gateway می‌روند. template یک location برای `/API/` ندارد.

اینکه prefix location در Nginx 1.27 نسبت به حرف حساس است از روی سند Nginx در این فاز نقل نشد. پس معادلی دانستن `/API/` با این دو location `unresolved` است. برای همین دو رشته‌ای که در فایل هست، هر دو صریحاً proxy می‌شوند.

فرانت داکر رشتهٔ `/api/...` می‌سازد، پس location مربوط به آن `/api/` است، نه `/Api/`.

### 3. Gateway و YARP

تعریف route: `verified`. قانون match: `documented`. اجرای gateway: نشده.

الگوها در `appsettings.DockerDevelopment.json`:

- login: `/Api/v{apiVersion}/Auth/Login/{**catch-all}` روی `auth-login-route-v1`
- پرسنل: `/Api/v{apiVersion}/Personnels/{**catch-all}` روی `personnel-routes-v1`

هیچ‌کدام `PathPattern`، `PathSet`، یا `PathRemovePrefix` ندارند. اگر match شود، مسیر اصلی به مقصد می‌رود.

سورس `src/ReverseProxy/Routing/ProxyEndpointFactory.cs` در tag 2.3.0 مقدار `Match.Path` را به `RoutePatternFactory.Parse` می‌دهد و با `RouteEndpointBuilder` یک endpoint می‌سازد. یعنی match مسیر، matcher خود ASP.NET Core است، نه یک مقایسهٔ جداگانه که در JSON کلید case داشته باشد. `IsCaseSensitive` در این کارخانه فقط برای header و query parameter است، نه برای path.

Microsoft Learn، Routing in ASP.NET Core، moniker شامل `aspnetcore-10.0`، بخش Route templates:

> Text matching is case-insensitive and based on the decoded representation of the URL's path.

پس طبق همین سند، literalهای `/Api` و `/api`، و همچنین `Auth` و `auth`، در route template یکی گرفته می‌شوند. این ادعا از سند فریم‌ورک است. یک درخواست واقعی به `apigateway` این مخزن زده نشد. جواب Stack Overflow که می‌گوید URL در YARP همیشه case-sensitive است با این زنجیره نمی‌خواند: YARP 2.3 الگو را به route template خود ASP.NET Core می‌دهد و سند routing می‌گوید match متن case-insensitive است. آن جواب انجمن به‌عنوان شاهد این نسخه قبول نشد.

`RouteOptions.LowercaseUrls` در این مخزن ست نشده است. سند همان Learn می‌گوید این پرچم روی URL تولیدشده اثر دارد. در API آن برای `aspnetcore-10.0` هم توضیح، lowercase کردن مسیر تولیدشده است، نه قانون match ورودی. پس نبودن این گزینه، match را case-sensitive نمی‌کند.

### 4. بک‌اند

تعریف route: `verified`. قانون match: `documented` با همان جملهٔ Learn. اجرا نشده.

- هویت: `AuthController` با `[Route("/api/v{version:apiVersion}/[controller]")]` و `[HttpPost("Login")]`.
- دژبان: `MapGet("/api/v{version:apiVersion}/Personnels/GetPersonnels")`.

هر دو template هستند و همان قانون case-insensitive سند routing را دارند، اگر درخواست به آن پردازه برسد. چون YARP مسیر را rewrite نمی‌کند، حرف‌هایی که gateway دیده به مقصد هم می‌رسند.

هیچ `RouteOptions` یا middleware نرمال‌سازی حرف در `Program.cs` این دو میزبان پیدا نشد.

### 5. جمع لایه‌ها، بدون ادعای اجرای زنده

| لایه | `/api` و `/Api` | شاهد | وضعیت |
|---|---|---|---|
| ساخت URL در فرانت داکر | فقط `/api` ساخته می‌شود | Compose و ثابت‌های Axios | `verified` |
| Nginx | هر دو پیشوند location جدا دارند و rewrite ندارند | `default.conf.template` | `verified` برای وجود هر دو. اجرا نشده |
| YARP 2.3 | الگو `/Api` است و matcher از route template است | `ProxyEndpointFactory` و Learn | `documented` |
| ASP.NET Core 10 روی هویت و دژبان | template با `/api` است و match متن case-insensitive است | Learn moniker 10.0 | `documented` |
| کل مسیر از مرورگر تا controller | هنوز یک جفت درخواست مقایسه نشده | — | `unresolved` |

اگر سند routing و کد YARP 2.3 با هم درست خوانده شده باشند، `/api/v1/auth/login` باید با `auth-login-route-v1` جور شود و بعد با `AuthController.Login` هم جور شود. این یک نتیجه‌گیری از سند است، نه لاگ این پروژه. تا تست پایین انجام نشود، درس‌ها نباید بنویسند که دو مسیر در تولید این سامانه معادل بودنشان مشاهده شده است.

تفاوت جدا: bind شدن بدنهٔ `{ "username", "password" }` به `LoginCommand` هنوز به حروف مسیر ربط ندارد و در سند login به‌عنوان `unresolved` مانده است. حتی اگر route match شود، ممکن است مدل خالی بماند. آن موضوع با این تحقیق یکی نیست.

## تستی که بعداً باید زده شود

این سه مقایسه پردازه را از هم جدا می‌کنند. هیچ‌کدام در این فاز اجرا نشد. بدنهٔ login باید ساختگی باشد تا حساب واقعی قفل نشود. JSON و Compose عوض نشود.

### الف. ساخت URL در فرانت

در DevTools همان صفحهٔ ورود و همان صفحهٔ پرسنل، URL واقعی درخواست را بخوان.

- اگر login برابر `/api/v1/auth/login` و پرسنل برابر `/api/v1/Personnels/GetPersonnels` باشد، ساخت URL در فرانت داکر همان چیزی است که کد می‌گوید.
- اگر مسیر دیگری دیده شد، اشکال از `NEXT_PUBLIC_SERVER_URL` یا از ثابت endpoint است و دیگر به YARP نمی‌رسد.
- این مشاهده فرانت را از gateway جدا می‌کند. به‌تنهایی match حروف را ثابت نمی‌کند.

### ب. فقط gateway

پروفایل `ApiGateway` در `ApiGateway/Properties/launchSettings.json` روی `https://+:7036` و محیط `Development` است. در این محیط `appsettings.Development.json` همان الگوها را دارد و مقصد هویت `http://localhost:5038` و مقصد دژبان `http://localhost:5042` است. این دو پورت، پروفایل Project همان سرویس‌ها هستند. درخواست مستقیم به gateway، Nginx و فرانت را از مسیر حذف می‌کند.

هر جفت باید پشت سر هم و با بدنه یا query یکسان زده شود:

| روش | مسیر اول | مسیر دوم |
|---|---|---|
| POST | `/api/v1/auth/login` | `/Api/v1/Auth/Login` |
| GET بدون توکن | `/api/v1/Personnels/GetPersonnels` | `/Api/v1/Personnels/GetPersonnels` |

شاهد match در gateway: هر دو عضو جفت status یکسان غیر از 404 بدهند. برای login، 400 یا 401 از هویت یعنی درخواست به controller رسیده است. 404 یعنی همان لایه مسیر را نشناخته است. برای پرسنل بدون توکن، 401 یعنی `RequireAuthorization` رسیده است. اگر فقط شکل `/Api/...` این status را بدهد و شکل `/api/...` برابر 404 باشد، تفاوت در match همین gateway است.

اگر هر دو 502 باشند، match احتمالاً انجام شده و مقصد پایین خاموش است. این 502 را با 404 عوض نکنید.

### ج. فقط بک‌اند، بدون YARP

همان جفت POST را مستقیم به `http://localhost:5038` بزنید و همان جفت GET را مستقیم به `http://localhost:5042`.

- اگر اینجا هر دو حرف قبول شوند ولی در بند ب یکی 404 شود، تفاوت مال gateway است.
- اگر اینجا هم یکی 404 شود، تفاوت مال route template خود هویت یا دژبان است.
- اگر بند ب و ج هر دو هر دو حرف را قبول کنند، سند routing با این محیط محلی می‌خواند. این هنوز رفتار Nginx یا مرورگر را ثابت نمی‌کند.

### د. Nginx فقط اگر بند ب تمام شده باشد

همان POST را یک بار از راه `location /api/` و یک بار از راه `location /Api/` به gateway داکر بفرستید. اگر مستقیم به gateway هر دو کار کنند و از Nginx فقط یکی کار کند، تفاوت مال location یا rewrite لبه است. template فعلی rewrite ندارد. این بند آخر است و تا وقتی gateway تنها تست نشده، تفسیرش قاطی می‌شود.

پاسخ 200 پرسنل، اگر با توکن آزمایشی گرفته شود، باید کلید `items` یا `Items` را هم ثبت کند. آن مشاهده bind مسیر نیست. نام JSON صفحهٔ staff است.
