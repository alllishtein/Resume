# روز ۰۱ — ۲۰ سؤال کلی مصاحبه (HTTP / REST / Web)

*سؤال‌ها و پاسخ‌ها کلی‌اند و وابسته به پروژه نیستند. هر پاسخ را با زبان خودت بگو.*

---

## ۱. HTTP چیست و «stateless» یعنی چه؟
**پاسخ:** HTTP یک پروتکل request/response روی مدل client-server است که روی TCP (و معمولاً TLS) سوار می‌شود. Stateless یعنی سرور بین request ها چیزی به خاطر نمی‌سپارد و هر request باید همهٔ اطلاعات لازم (auth، locale و ...) را همراه خودش بیاورد. مزیتش: scale-out ساده می‌شود، چون هر instance می‌تواند به هر درخواست جواب بدهد و sticky session لازم نیست.

## ۲. وقتی URL را در مرورگر می‌زنی و Enter می‌کنی چه اتفاقی می‌افتد؟
**پاسخ:** (۱) مرورگر URL را parse می‌کند. (۲) DNS: دامنه ← IP. (۳) TCP handshake با سرور. (۴) TLS handshake (اگر HTTPS باشد): بررسی certificate و key exchange. (۵) HTTP request فرستاده می‌شود. (۶) سرور response می‌دهد (HTML). (۷) مرورگر HTML را parse می‌کند، CSS/JS/تصویر را با request های جدید می‌گیرد، DOM و CSSOM را می‌سازد و render می‌کند.

## ۳. method های HTTP را بگو. safe و idempotent یعنی چه؟
**پاسخ:** GET، HEAD، POST، PUT، PATCH، DELETE، OPTIONS. **Safe** یعنی state سرور را تغییر نمی‌دهد (GET، HEAD، OPTIONS). **Idempotent** یعنی اجرای N بار = ۱ بار و state نهایی یکی می‌ماند (GET، PUT، DELETE، HEAD، OPTIONS). POST idempotent نیست (دو بار POST = دو بار ساخت). PATCH معمولاً idempotent است ولی تضمین ندارد.

## ۴. PUT در برابر PATCH در برابر POST؟
**پاسخ:** POST برای ساخت یا عملیات است (idempotent نیست). PUT جایگزینی کامل منبع با body ی کامل است (idempotent). PATCH آپدیت جزئی است (فقط فیلدهای تغییرکرده). اگر با PUT فیلدی را نفرستی، ممکن است null یا مقدار پیش‌فرض شود؛ PATCH فقط چیزی را عوض می‌کند که فرستاده‌ای.

## ۵. status code ها را دسته‌بندی کن. 401 در برابر 403؟
**پاسخ:** 2xx = موفق، 3xx = redirect، 4xx = خطای client، 5xx = خطای server. **401** یعنی «تو کی هستی؟» (authenticate نشده یا توکن نامعتبر است)، **403** یعنی «می‌شناسمت ولی اجازه نداری» (authorization). روی 401 کلاینت می‌تواند دوباره login/refresh کند؛ روی 403 تکرار فایده‌ای ندارد.

## ۶. 400 در برابر 404 در برابر 409 در برابر 422؟ خطاها را چطور برمی‌گردانی؟
**پاسخ:** 400 یعنی request خراب است (syntax، validation). 404 یعنی منبع یا route وجود ندارد. 409 یعنی تعارض با state سرور (تکراری، version mismatch). 422 یعنی syntax درست ولی معنا نامعتبر است. برای بدنهٔ خطا از فرمت استاندارد **ProblemDetails (RFC 7807/9457)** استفاده کن: `type`، `title`، `status`، `detail`؛ `title`/کد برای منطق client و `detail` برای انسان.

## ۷. 500 در برابر 502 در برابر 503 در برابر 504؟
**پاسخ:** 500 یعنی exception ی handle نشده در اپلیکیشن. 502 یعنی proxy/gateway از upstream response ی نامعتبر گرفته. 503 یعنی سرور overload است یا در maintenance است (می‌تواند `Retry-After` داشته باشد). 504 یعنی upstream در زمان مشخص جواب نداده (timeout). برای debug: 500 ← لاگ اپلیکیشن، 502/504 ← لاگ proxy و سلامت upstream.

## ۸. REST چیست؟ قیدهای آن؟
**پاسخ:** REST یک سبک معماری (Roy Fielding) برای API است، نه framework. قیدها: client-server، stateless، cacheable، uniform interface (منبع با URL، method ی استاندارد، پیام خودتوصیف‌گر)، layered system و code on demand (اختیاری). اگر رعایت کنی، API قابل‌پیش‌بینی، cache-friendly و scalable می‌شود.

## ۹. Richardson maturity model و HATEOAS چیست؟
**پاسخ:** معیاری برای «چقدر RESTful هستی»: Level 0 = یک URL و همه POST؛ Level 1 = چند URL منبع؛ Level 2 = method و status code ی درست؛ Level 3 = HATEOAS، یعنی response لینک اکشن‌های بعدی را در خودش دارد. بیشتر API ها در Level 2 می‌مانند و Level 3 کم پیاده می‌شود.

## ۱۰. REST در برابر RPC در برابر GraphQL در برابر gRPC — کی کدام؟
**پاسخ:** **REST**: API ی عمومی، CRUD منبع‌محور، cache-friendly. **RPC روی HTTP**: اکشن‌های workflow-محور که خوب به «منبع» نگاشت نمی‌شوند (login، import). **GraphQL**: کلاینت‌های متفاوت با نیاز داده ی متفاوت؛ یک endpoint و کلاینت فیلدها را انتخاب می‌کند (دردسر: caching و پیچیدگی). **gRPC**: ارتباط داخلی سرویس‌به‌سرویس، باینری (Protobuf)، سریع و با contract ی سخت؛ بدون gRPC-Web برای مرورگر مناسب نیست.

## ۱۱. flag های کوکی: HttpOnly، Secure، SameSite؟
**پاسخ:** **HttpOnly**: JS نمی‌تواند `document.cookie` را ببیند ← XSS کوکی را نمی‌دزدد. **Secure**: فقط روی HTTPS. **SameSite**: `Strict` (فقط same-site)، `Lax` (لینک GET سطح‌بالای cross-site مجاز، بقیهٔ request های cross-site نه)، `None` (همه‌جا، حتماً با Secure). کوکی با هر request خودکار می‌رود، پس ریسک CSRF دارد.

## ۱۲. احراز هویت با session در برابر توکن (JWT)؟
**پاسخ:** **Session**: سرور state نگه می‌دارد (session ID در کوکی) — revoke آسان است ولی state مشترک/sticky لازم دارد. **JWT**: توکن self-contained و امضاشده، بدون state در سرور — scale-friendly ولی revoke سخت است (expiry کوتاه + refresh token + blacklist). روش مناسب: access token کوتاه‌عمر + refresh token. توکن را در localStorage نگذار (XSS)؛ refresh را در کوکی HttpOnly نگه دار.

## ۱۳. CORS چیست و preflight چیست؟
**پاسخ:** CORS **policy ی مرورگر** است (نه سرور): می‌گوید JS ی origin A فقط وقتی سرور B اجازه بدهد می‌تواند response ی B را بخواند. Origin = scheme + host + port. **Preflight**: برای request ی cross-origin با method/header ی non-simple، مرورگر اول OPTIONS می‌زند تا ببیند سرور اجازه می‌دهد. `Allow-Origin: *` با credentials کار نمی‌کند. curl/Postman CORS ندارند، پس CORS امنیت API نیست و فقط جلوی خواندن توسط JS ی سایت‌های دیگر است.

## ۱۴. XSS در برابر CSRF؟ چطور دفاع می‌کنی؟
**پاسخ:** **XSS**: مهاجم JS به صفحهٔ تو تزریق می‌کند. دفاع: output encoding/escape، CSP، کوکی HttpOnly، sanitize ی ورودی. **CSRF**: سایت مهاجم request می‌زند و مرورگر کوکی کاربر را خودکار می‌فرستد. دفاع: SameSite، antiforgery token، هدر سفارشی، بررسی Origin/Referer. توکن در هدر `Authorization` جلوی CSRF را می‌گیرد ولی اثر XSS را بیشتر می‌کند.

## ۱۵. HTTPS و TLS چطور کار می‌کند؟
**پاسخ:** HTTPS = HTTP + TLS. Handshake: client hello ← certificate ی سرور (هویت را ثابت می‌کند) ← key exchange ← از آن به بعد با **کلید symmetric** رمز می‌شود. سه تضمین: **confidentiality** (کسی نمی‌خواند)، **integrity** (کسی تغییر نمی‌دهد)، **authentication** (با سرور درست حرف می‌زنی). بدون TLS داده plaintext است و در Wi-Fi قابل sniff است.

## ۱۶. cache در HTTP چطور کار می‌کند؟
**پاسخ:** `Cache-Control`: `max-age=n`، `no-store` (اصلاً ذخیره نکن)، `no-cache` (ذخیره کن ولی revalidate کن)، `public`/`private` (CDN یا فقط مرورگر). **Validation**: سرور `ETag` می‌دهد؛ کلاینت `If-None-Match` می‌فرستد؛ اگر تغییری نکرده باشد ← **304 Not Modified** بدون body. خطر: response ی شخصی را روی shared cache/CDN cache نکن (`private` یا `no-store`، `Vary`).

## ۱۷. HTTP/1.1 در برابر HTTP/2 در برابر HTTP/3؟
**پاسخ:** **1.1**: متنی، روی TCP، درخواست‌ها پشت‌سرهم (head-of-line blocking) و به چند connection نیاز دارد. **2**: باینری، **multiplexing** (چند stream روی ۱ connection)، فشرده‌سازی هدر با HPACK، روی TCP. **3**: روی **QUIC/UDP**، head-of-line ی TCP را هم حل می‌کند، handshake سریع‌تر، مناسب موبایل.

## ۱۸. WebSocket در برابر SSE در برابر long polling؟
**پاسخ:** **Long polling**: کلاینت request می‌زند و سرور تا وقتی داده نباشد جواب نمی‌دهد — ساده ولی پرهزینه. **SSE**: اتصال یک‌طرفه (سرور ← کلاینت) روی HTTP با auto-reconnect، ساده. **WebSocket**: اتصال دوطرفه و دائمی؛ با HTTP Upgrade شروع می‌شود (101 Switching Protocols) و بعد از آن دیگر معنای HTTP ندارد. انتخاب: push ی یک‌طرفه ← SSE، چت/بازی/realtime ی دوطرفه ← WebSocket.

## ۱۹. API versioning چطور است و چه موقع v2؟
**پاسخ:** چهار روش: URL (`/api/v1/`)، header (`api-version`)، query (`?api-version=`)، media type (`Accept: application/vnd.x.v1+json`). URL ساده و cache-friendly و رایج‌ترین است. **Breaking change** (حذف/تغییر فیلد، تغییر معنا) ← v2 موازی و deprecate کردن v1 با زمان‌بندی. **Non-breaking** (فیلد optional ی جدید) ← همان v1.

## ۲۰. idempotency، retry و rate limiting در API چطور حل می‌شود؟
**پاسخ:** چون شبکه گاهی request را دو بار می‌فرستد، POST های مهم (پرداخت، ثبت) باید بازدارندهٔ امن داشته باشند: هدر **`Idempotency-Key`** (سرور نتیجه را ذخیره می‌کند)، **unique constraint** در DB (تکراری ← 409)، یا PUT به‌جای POST. **Retry**: فقط روی خطاهای موقت (5xx/timeout) و با exponential backoff + jitter. **Rate limit**: سرور 429 + `Retry-After` می‌دهد؛ کلاینت باید صبر کند، نه اسپم.

---

## نکتهٔ مصاحبه
- برای هر سؤال اول تعریف ۱ جمله‌ای، بعد «چرا مهم است» و بعد یک مثال واقعی.
- اگر نمی‌دانی، صادق باش و از چیزی که می‌دانی شروع کن؛ مصاحبه‌کننده‌ها بیشتر به «اشتباه محترمانه» احترام می‌گذارند تا «اشتباه با اعتماد به نفس کاذب».
