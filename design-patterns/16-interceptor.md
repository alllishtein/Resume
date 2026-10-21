# 16 — Interceptor va Single Flight

---

## Ye khat

Har request-e HTTP bayad chand kar-e **hamishegi** rooye khod dashte bashad: token, zaban, tenant, ragham. An kar-ha ra dakhel-e har call copy nemikonim. Yek zanjir, yek bar, dor-e hame-ye call-ha mineshinad.

Va agar sad call-e hamzaman yek manba'-e refresh bekhand, **yek** refresh anjam mishavad, na sad ta.

Do mafhoom-and. Avval zanjir. Ba'd single flight. Ba'd code.

---

# BAKHSH-E AVAL — khode pattern

## Interceptor chist

Interceptor (va esm-e nazdik: middleware-e client) halqe-i ast ke **ghabl** az raftan-e request, ya **ba'd** az residan-e response, dastresi darad. Caller-e `getOrders()` an ra seda nemizanad. Caller faghat URL va body-e business ra midanad.

Sakhtar-ash haman chain of responsibility ast, in bar rooye transport:

```
getOrders()
  -> halqe-ye zaban
  -> halqe-ye token
  -> halqe-ye tenant
  -> shabake
  -> halqe-ye 401
  -> halqe-ye tarjome-ye khata
  -> caller
```

Har halqe ya `config` ra taghir midahad va rad mikonad, ya zanjir ra miband (masalan "in 401 ast, boro login, in request ra edame nade").

## Ghanun-haye zanjir-e transport

**1. Faghat concern-e hame-ye call-ha.**
Token male hame ast. "Agar in form-e shift bud, field-e X ra ezafe kon" male hame nist. An ghanun-e yek safhe ast va agar inja beneshinad, hame-ye API-ha an ra ers mibarand. Zanjir-e markazi God Object-e HTTP mishavad.

**2. Tartib gharardad ast.**
Avval token-e taze ra bezar, ba'd log. Avval 401 ra handle kon, ba'd toast-e "khataye na-malum". Tartib-e baraks toast-e dorough ya retry-e bi-token misazad.

**3. Retry bayad saqf dashte bashad.**
401 → refresh → dobare haman request. Agar haman request dobare 401 shod va haman rah ra beri, loop-e binahayat. Yek flag-e "in ra hanuz retry kardam" saqf ast.

**4. Request-e khod-e refresh nabayad haman ghanun-e "token-e access ra bechasan" ra koor-koor ers bebarad.**
Access morde ast. Refresh ba vasile-ye digar (cookie) miravad. Agar access-e morde ra rooye refresh ham bezani, ya server an ra ghalat mifahmad ya loop misazi.

**5. Zanjir-e client jaye server nist.**
Client header-e tenant ra **mifrestad**. Server an ra **bavar** mikonad va dobare az rooye session check mikonad. Pak kardan-e header to devtools tenant-e kasi digar nist, agar server dorost bashad. Interceptor rahati-e client ast, marz-e amniat na.

## Single flight chist

Moshkel-e joda az zanjir:

100 request-e hamzaman 401 mishavand. Har kodam mostaghil `POST /refresh` mizanad. Refresh-token-e charkheshi (rotation) eshtebah-e klassik ast: avvalin refresh token-e ghadim ra batel mikonad, 99-taye ba'di ba token-e morde miravand, server hame ra logout mikonad. Session-e salem, bug-e concurrency.

Single flight (va esm-haye nazdik: promise coalescing, in-flight de-duplication):

- avvalin darkhast-e refresh yek `Promise` misazad va an ra **yadash** midarad
- baghi, ta an promise tamoom nashode, darkhast-e jadid nemisazand. Haman promise ra await mikonand
- vaghti tamoom shod, yadash pak mishavad. Refresh-e **ba'di** (daghighe-ye ba'd) mojaz ast
- har 100 caller, ba'd az resolve, request-e khod ra ba token-e taze retry mikonand

Yek safar-e shabake. Sad montazer. Natije-ye moshtarak.

In lock-e thread-e C# nist. To JavaScript yek thread-e event loop dari. "Hamzaman" ya'ni chand promise-e dar-hava, na chand core. Hanooz bug-e sad-refresh vojud darad, chon `if (!promise) promise = start()` agar do bar posht-e sar-e ham **ghabl** az set shodan-e moteghayer ejra shavad... dar JS-e tak-thread, ta avvalin `await`, code-e sync ghat' nemishavad. Pas:

```javascript
if (!refreshPromise) {
  refreshPromise = doRefresh().finally(() => { refreshPromise = null; });
}
await refreshPromise;
```

ghabl az `await`, hich kas-e digar vared nemishavad. Do 401-e hamzaman (do microtask) bayad **ghabl** az inke avvali `await` konad, promise ra set karde bashad. Shekl-e bala hamin kar ra mikonad: set kardan-e moteghayer sync ast, `await` ba'd-e an ast. Agar avval `await doRefresh()` koni va ba'd moteghayer ra set koni, panjere-ye bug baz ast.

## Saqf-e shekast-e refresh

Agar refresh be dalil-e shabake (timeout) fail shavad, 100 caller hamzaman dobare retry mikonand. Mitavani yek modat-e kutah "dobare talash nakon" bezari. Agar fail **401-e khod-e refresh** bashad, an "shabake" nist. Session morde. Bayad logout koni, na 5 sanie sabr-e bi-fa'ide. Do noe shekast, do gharardad.

## Farq-ha

**Middleware-e server.** Haman chain, samt-e digar-e sim. Client header mifrestad. Server identity ra misazad. Yeki jay-e digari nist.

**Decorator.** Yek call-e moshakhas ra wrap mikoni. Interceptor hame-ye call-haye yek client ra, bedune dast-zadan-e caller. Nazdik-and. Interceptor-e axios shekl-e sabt-shode-ye chain ast.

**Cache.** Single flight cache-e natije-ye movaffagh-e dir-baz nist. Faghat **hamin** kar-e dar-hava ra yeki mikonad. Ba'd az `finally` va `null` shodan, call-e jadid dobare shabake ast. Ghalt: refresh-e diruz ra ta abad cache kardan.

## Eshtebah-haye rayej

- retry-e bi-saqf
- chasb-e ghanun-e yek safhe be interceptor-e jahani
- `await` ghabl az set-e promise-e moshtarak
- logout-e hamegani rooye 500-e movaghat-e refresh
- farz-e amniat az header-e client

## Mafhoom ra injoori begou

> "Interceptor chain-e transport ast. Caller an ra nemibinad. Faghat concern-e hame-ye call inja mimanad. Retry saqf darad. Single flight ya'ni chand montazer, yek promise-e dar-hava. Set-e promise bayad sync va ghabl az await bashad. Shekast-e shabake va shekast-e 401-e refresh do rah-and. Client jaye check-e server nist."

---

# BAKHSH-E DOVOM — hamin mafhoom to front-e Dejban

`packages/api-client/src/axiosInstance.ts` — `createApiClient`.

**Halqe-ye request.** Zaban az `localStorage` (`Accept-Language`, default `fa-IR`). Site az `useSiteStore.getState().getSiteIds()` — birun-e React, pull, na hook. Override-e `config.siteId` agar yek call site-e digar bekhad. Access token az `tokenStorage`, magar URL khod-e refresh bashad. Ragham-e farsi/arabi to params va FormData va JSON be englisi. In akharin mored adapter-e koochak-e dakhel-e chain ast (ketabche-ye adapter).

**Halqe-ye response.**

- 503 → redirect be `/error/503?system=...` va reject
- 401, ba shart → single flight-e refresh
- 403 → toast-e "dastresi nadarid" faghat agar payam-e farsi-e business to body nabashad (ta do ta toast-e tekrari nayad)
- baghi → reject ta UI khodesh tarjome konad

Sharayet-e **na**-refresh: `_retry` ghablan true (saqf-e yek retry), URL-e login, URL-e refresh, ticket-e public.

**Single flight.** `refreshPromise` birun-e interceptor, dakhel-e `createApiClient`. Avvalin 401 an ra misazad. Baghi `await refreshPromise`. `finally` an ra `null` mikonad. Shekl-e set-e sync ghabl az await re'ayat shode.

Ba'd az 200 va `accessToken`: `tokenStorage.setAccess`, ba'd header-e `Authorization` rooye `originalRequest`, ba'd `client(originalRequest)`. In `client(...)` **dobare** az halqe-ye request rad mishavad. Token-e taze ham to storage hast ham rooye header-e explicit.

`refreshBlockedUntil`: fail-e gheyr-e 401/403/404 ta 5 sanie refresh-e jadid nemisazad. 401/403/404 block nemishavand. An-ha miravand logout (`POST /auth/logout`), `tokenStorage.clear`, `redirectToSignIn`.

`withCredentials: true` ta cookie-ye httpOnly-e refresh beravad. Access to header ast, na haman cookie.

`export const apiClient = createApiClient(...)` yek instance-e moshtarak. Yek `refreshPromise` baraye hame-ye app-hayi ke in module ra import mikonand. Do instance = do single-flight-e joda = dobare sad refresh. Yek instance joz'-e gharardad ast.

---

## Script-e 90 sanie

> "Interceptor zanjir-e ghabl va ba'd az HTTP ast va caller an ra seda nemizanad. Faghat ghanun-e hame-ye call. Single flight chand 401-e hamzaman ra rooye yek promise-e refresh jam' mikonad. Promise bayad ghabl az await set shavad. Dejban to createApiClient zaban, site az Zustand, bearer, va ragham ra mizanad. Refresh khodesh bearer-e morde nemigirad. 401-e hamzaman yek refreshPromise darand. Ba'd token-e taze ham storage ham header mishavad va request-e asli yek bar retry mishavad. 401-e refresh logout ast. Timeout-e refresh 5 sanie block-e narm ast. Yek apiClient, yek single flight."

---

## 10 soal

**1. Interceptor az nazar-e pattern chist?**
Chain rooye transport. Mitavanad short-circuit konad ya config ra taghir dahad va rad konad.

**2. Che ghanuni inja mamnoo' ast?**
Ghanun-e yek safhe. Zanjir hame-ye call-ha ra ers midahad.

**3. Saqf-e retry chera?**
401-e ba'd az refresh-e namovaffagh loop misazad. Yek `_retry` kafi ast ta be UI bargardi.

**4. Single flight che race-i ra mibandad?**
Chand refresh-e hamzaman ba token-e charkheshi. Avvalin, baghi ra batel mikonad va session-e salem logout mishavad.

**5. Chera set-e promise ghabl az await ast?**
Ta do vorudi-e sync, ghabl az deliver-e event loop, haman promise ra bebinand. Set-e ba'd az await panjere-ye do-ta'i baz mikonad.

**6. Fail-e shabake va fail-e 401-e refresh farq?**
Avval shayad movaghat bashad. Dovom session morde ast. Dovom ra 5 sanie sabr-e bi-logout nakon.

**7. Client-e interceptor amniat ast?**
Na. Server tenant va token ra dobare check mikonad.

**8. To Dejban site-id az koja be header miravad?**
`useSiteStore.getState()` dakhel-e interceptor. Hook nist, chon inja render nist.

**9. Retry chetor token-e ghadim ra nemifrestad?**
`setAccess` va set-e explicit-e header, ba'd `client(originalRequest)` ke dobare halqe-ye request ra mibinad.

**10. Do `createApiClient` che moshkeli darad?**
Do `refreshPromise`. Single flight-e yeki digari ra nemibinad. 401-e hamzaman dobare chand refresh mishavad.
