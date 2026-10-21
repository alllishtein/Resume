# 16 — Interceptor (chain + single flight)

*Har request az yek zanjir-e sabet rad mishavad: zaban, site, token, ragham. 401 yek bar refresh mishavad, na dah bar.*

---

## Ye khat

Interceptor-e Axios haman **Chain of Responsibility** roye HTTP-e client ast. Har request va har response az tabe'-haye sabt-shode rad mishavad. Caller-e `getDutyCycles` an-ha ra seda nemizanad.

File: `packages/api-client/src/axiosInstance.ts` — `createApiClient`.

## Zanjir-e request

```javascript
client.interceptors.request.use((config) => {
  config.headers['Accept-Language'] = language || 'fa-IR';
  config.headers['X-Site-Id'] = siteOverride || siteIds.join(',');
  if (!isRefreshRequest) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  // params, FormData, JSON → ragham-e farsi/arabi be englisi
  return config;
});
```

Site az Zustand **birun-e React** khande mishavad: `useSiteStore.getState().getSiteIds()`. Interceptor hook nist. In dalil-e store-e birun-az-component ast (ketabche-ye 20).

Refresh-e khod-e token **header-e access** nemigirad (`isRefreshRequest`), vagarna ba token-e morde refresh mikoni.

## Zanjir-e response

1. **503** → redirect be `/error/503?system=...` va reject.
2. **401** ba shart-ha → yek refresh, ba'd retry-e request-e asli.
3. Baghi-e khata-ha → reject ta UI `getErrorMessage` konad.

Sharayet-e 401 ke refresh **nemishe**:

- hamin request ghablan `_retry` shode (loop)
- URL-e login ya refresh
- ticket-e public (`isPublicTicketRequest`)

## Single flight

```javascript
let refreshPromise = null;

if (!refreshPromise) {
  refreshPromise = client.post(endpoints.auth.refresh)
    .finally(() => { refreshPromise = null; });
}
await refreshPromise;
return client(originalRequest);
```

Dah request-e hamzaman 401 mishavand. Bedune in, dah `POST /auth/refresh`. Refresh token rotation an-ha ra invalidate mikonad va hame logout mishavand.

Single flight: **avalin** 401 promise ra misazad, baghi **haman promise** ra await mikonand. Yek refresh, chand retry.

In pattern-e **promise coalescing** ast. Nazdik be flyweight nist. Nazdik be "leader election" koochak-e in-memory ast. Esm-e mosahebe: single flight.

`refreshBlockedUntil` : age refresh be dalil-e shabake (na 401/403/404) fail shavad, ta 5 sanie refresh-e jadid sakht nemishavad. 401/403/404 block nemishavand ta logout/login ghofl nashavad.

Cookie: `withCredentials: true` ta refresh-e httpOnly beravad. Access to memory/`tokenStorage` ast, na haman cookie.

## Farq ba middleware-e server

| | Axios interceptor | ASP.NET middleware |
|---|---|---|
| Koja | browser, gabl/ba'd az XHR | server, gabl az endpoint |
| Kar-e ma | token, site, ragham, refresh | auth-e asl, tenant, route |

Har do chain hastand. Yeki jaye digari nist: UI header ra mitarsanad, server an ra **bavar** mikonad va dobare check mikonad.

## Script-e 60 sanie

> "`createApiClient` do interceptor darad. Request zaban, `X-Site-Id` az Zustand, bearer, va normalize-e ragham ra ezafe mikonad. Response 503 ra be safhe-ye khata mibarad. 401 yek `refreshPromise` moshtarak misazad ta request-haye hamzaman yek refresh bezanand, ba'd haman config ra retry mikonad. Login, refresh, va ticket-e public az in halqe birun-and. Access header roye khod-e refresh nemiravad."

---

## 10 soal

**1. Interceptor kodam pattern ast?**
Chain of responsibility roye client. Mitavani an ra decorator-e pipeline ham seda koni. Chand halqe, har kodam `config` ra taghir midahad ya short-circuit mikonad.

**2. Chera single flight?**
401-e hamzaman. Chand refresh-e hamzaman refresh-token ra mishkanad va session-haye salem logout mishavand.

**3. `_retry` chera?**
Ta refresh-e namovaffagh ya 401-e dobare loop-e binahayat nasazad. Yek retry, ba'd error be UI.

**4. Site ra chera az hook nemikhani?**
Interceptor birun-e render ejra mishavad. `useSiteStore.getState()` haman snapshot-e store ast.

**5. Refresh cookie va access header?**
Refresh httpOnly ast va browser an ra ba `withCredentials` mifersad. Access ra ma `Authorization` migozarim ta har API an ra bebine. Refresh khodesh bearer-e morde nemikhahad.

**6. 503 inja ya error boundary?**
Interceptor hame-ye call-ha ra yek ja mibinad va be safhe-ye system-unavailable miravad. Error boundary crash-e render ra migirad, na status-e HTTP.

**7. Normalize-e ragham inja chera?**
Har form yek `toEnglishDigits` faramoosh mikonad. API yek gharardad darad. Zanjir-e markazi an ra ejbari mikonad. An adapter-e koochak ham hast (ketabche-ye 19).

**8. Race: refresh tamoom, request-e ghadimi hanuz token-e ghadim darad?**
Code avval `tokenStorage.setAccess` mikonad, ba'd `originalRequest.headers.Authorization` ra ba token-e taze set mikonad, ba'd `client(originalRequest)`. In `client(...)` dobare az interceptor-e request rad mishavad. Header-e explicit va storage har do taze-and. `_retry` jeloye loop-e 401-e dovom ra migirad.

**9. Test?**
Do request-e 401-e hamzaman: `post refresh` **yek** bar. 401 roye `/auth/refresh`: retry-e refresh-e do bar nist. Public ticket: refresh seda nashode.

**10. Interceptor-e kheili hooshmand?**
Zanjir ja-ye business-e yek safhe nist. Age rule-e "faghat in form" ra inja bezani, hame-ye API-ha an ra ers mibarand. Inja faghat concern-e **hame-ye** call-ha: auth, site, zaban, ragham, 503.
