# تحقیق پیکربندی YARP — route حافظهٔ خالی

سؤال این بود که چرا مجموعهٔ route داخل حافظه خالی دیده می‌شود، و آیا همان نمونه‌ای است که درخواست را سرو می‌کند.

اپ gateway اجرا نشد. نتیجه از کد مخزن و از سورس tag `v2.3.0` پکیج `Yarp.ReverseProxy` است. نسخهٔ پکیج در `Directory.Packages.props` برابر `2.3.0` است و اسمبلی `Yarp.ReverseProxy.dll` همان نسخه زیر cache نوگت این ماشین وجود دارد.

## نتیجه

آرایهٔ in-memory خالی است چون کد همین را ساخته و بعداً عوضش نمی‌کند. این خالی بودن، در سورس `ProxyConfigManager` نسخهٔ 2.3.0، لیست routeهای providerهای دیگر را جایگزین نمی‌کند. `MapReverseProxy` روی همان builder است که هم `LoadFromMemory` و هم `LoadFromConfig` را صدا می‌زند.

این نتیجه جدول route یک پردازهٔ در حال اجرا را ثابت نمی‌کند. هیچ dump از `GetConfig` در زمان اجرا گرفته نشده است.

وضعیت: ترکیب لیست‌ها از روی سورس tag `2.3.0` و از روی ثبت در `Program.cs` است. فعال بودن یک route مشخص در یک محیط در حال اجرا `unresolved` است.

## همان نمونه است

در کل مخزن فقط `ApiGateway/Program.cs` متد `AddReverseProxy` را صدا می‌زند. همان زنجیره بعداً `MapReverseProxy` دارد. پیاده‌سازی دیگری از `IProxyConfigProvider` در `*.cs` مخزن نیست. کلاسی به نام `InMemoryConfigProvider` در مخزن تعریف نشده است. کتابخانه آن را می‌سازد.

پس یک proxy هست، نه دو نمونه که یکی خالی و یکی پر باشد.

## چرا خود آرایه خالی است

`IdentityServerRoutes.routes` این است:

```csharp
public static readonly RouteConfig[] routes = [
    // auth-login-route و auth-refresh-route comment شده‌اند
];
```

`LoadFromMemory(IdentityServerRoutes.routes, [])` همان آرایه و یک آرایهٔ خالی cluster را می‌دهد. در مخزن `InMemoryConfigProvider.Update` صدا زده نمی‌شود. route از دیتابیس، Redis، یا provider سفارشی هم بار نمی‌شود. شرطی دور `LoadFromMemory` نیست. هم در Development و هم در DockerDevelopment این خط اجرا می‌شود.

سورس tag `v2.3.0`، فایل `src/ReverseProxy/Configuration/InMemoryConfigProvider.cs`: سازنده همان لیست را در `IProxyConfig.Routes` می‌گذارد. `GetConfig` همان snapshot را برمی‌گرداند. اگر کسی این provider را resolve کند و `Routes` را ببیند، شمارش صفر درست است. این خالی بودن از اول ساخت است، نه بعد از یک initialization دیرهنگام.

`src/ReverseProxy/Configuration/InMemoryConfigProviderExtensions.cs` در همان tag دو ثبت انجام می‌دهد: خود `InMemoryConfigProvider` به‌صورت singleton، و همان شیء به‌صورت `IProxyConfigProvider`.

## چرا درخواستها هنوز route دارند

`ProxyConfigManager.InitialLoadAsync` در همان tag همهٔ `IProxyConfigProvider`ها را می‌خواند و `Routes` هر کدام را با `AddRange` به یک لیست مشترک می‌ریزد. لیست خالی چیزی اضافه نمی‌کند و لیست‌های دیگر را جایگزین نمی‌کند.

`Program.cs` بعد از `LoadFromMemory` هشت بار `LoadFromConfig` را روی همان builder صدا می‌زند. اسمبلی 2.3.0 هر دو نام `LoadFromConfig` و `ConfigurationConfigProvider` را دارد. نام کامپایلر `<LoadFromConfig>b__0` نشان می‌دهد این متد یک closure دارد. بدنهٔ کامل `LoadFromConfig` از روی سورس tag در این فاز ذخیره نشد، چون دانلود بعدی همان فایل متوقف شد. پس این جمله دقیق است: manager چند provider را با هم جمع می‌کند، و `LoadFromMemory` یکی از آن providerها را با لیست خالی ثبت می‌کند. اینکه هر `LoadFromConfig` حتماً یک `ConfigurationConfigProvider` جدا ثبت کند از وجود نوع و از الگوی closure محتمل است و `inferred` می‌ماند تا همان فایل extension خوانده شود.

شاهد قوی‌تر از این استنباط، خود JSON است. routeهای `auth-login-route-v1` و `personnel-routes-v1` داخل sectionهایی هستند که به `GetSection` داده شده‌اند. اگر manager آن sectionها را بار کند، این routeها در لیست ادغام‌شده هستند حتی اگر snapshot حافظه صفر باشد.

## منبع‌ها و اولویت

| منبع | نقش برای route |
|---|---|
| `IdentityServerRoutes.routes` | خالی. اولویت معنا ندارد چون عضوی ندارد |
| `appsettings.json` | route و cluster پیش‌فرض، اغلب localhost |
| `appsettings.{Environment}.json` | روی کلیدهای تکراری می‌نشیند. Compose مقدار `DockerDevelopment` را می‌گذارد |
| `appsettings.Docker.json` | فقط وقتی محیط `Docker` باشد. Compose فعلی `DockerDevelopment` است |
| `globalAppsettings*.json` | شش فایل زیر `GlobalAppsettings/` با `AddJsonFile` و `optional: false` بار می‌شوند. جستجوی کلید `ReverseProxy` در همین فایل‌ها هیچ موردی نداشت. پس این فایل‌ها route درگاه را override نمی‌کنند. مقدارهای secret همان فایل‌ها در سند نیامده است. وضعیت نبود کلید: `verified` |
| environment variable | الگوی ASP.NET Core هست. در Compose برای gateway کلید `ReverseProxy__...` دیده نشد. پس override محیطی route در فایل Compose فعلی نیست |

هر پنج فایل `appsettings.json`، `Development`، `Docker`، `DockerDevelopment`، و `appsettings-sample.json` شناسهٔ `auth-login-route-v1` و `personnel-routes-v1` را دارند. تفاوت مهم بین آن‌ها آدرس destination است، نه خالی بودن route.

بارگذاری تنبل یا موکول به یک درخواست اول در کد مخزن نیست. `InitialLoadAsync` کتابخانه همان اول لیست را می‌سازد. این از سورس tag است، نه از log اجرای این سرویس.

## تشخیص بعدی، اگر هنوز شک باشد

کوچک‌ترین کار بی‌خطر، بدون عوض کردن JSON تولید: در یک محیط محلی، بعد از `Build`، همهٔ `IProxyConfigProvider`ها را از DI بگیر و `GetConfig().Routes.Count` هر کدام را log کن، بعد شمارش route داخل `ProxyConfigManager` را با آن مقایسه کن. انتظار از همین سند: provider حافظه صفر، و جمع providerهای config بیشتر از صفر، از جمله `auth-login-route-v1`. این کار انجام نشد.

## چه چیزی عوض نشد

کد برنامه، JSON درگاه، و Compose دست نخورده‌اند. کپی موقت سورس YARP که برای خواندن tag دانلود شده بود جزو سند یادگیری نیست و نباید commit شود.
