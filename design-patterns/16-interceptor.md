# 16 — Interceptor va Single Flight

Har request-e HTTP bayad chand kar-e hamishegi ru khod dashte bashad: token, zaban, tenant, ragham. An kar-ha ra dakhel-e har call copy nemikonim. Ye zanjire, ye bar, dor-e hame-ye call-ha mineshinad.

Va agar sad call-e hamzaman ye refresh bekhand, ye refresh anjam mishavad, na sad ta.

Do mafhum-and. Aval zanjire. Bad single flight.

## Interceptor

Interceptor halghe-i ast ke ghabl az raftan-e request, ya bad az residan-e response, dastresi darad. Caller-e `getOrders()` an ra seda nemizanad. Caller faghat URL va body-ye business ra midanad.

```
getOrders()
  → halghe-ye zaban
  → halghe-ye token
  → halghe-ye tenant
  → shabake
  → halghe-ye 401
  → caller
```

Har halghe ya `config` ra taghir midahad va rad mikonad, ya zanjire ra miband.

Ghanun-ha:

**Faghat concern-e hame-ye call-ha.** Token mal-e hame ast. "Agar in form-e shift bud, field-e X ra ezafe kon" mal-e hame nist. Zanjire-ye markazi God Object-e HTTP mishavad.

**Tartib gharardad ast.** Avval token-e taze, bad log. Avval 401, bad toast-e "khatay-e namalum".

**Retry bayad saqf dashte bashad.** 401 → refresh → dobare haman request. Agar dobare 401 shod va haman rah ra beri, loop-e binahayat. Ye flag-e "in ra hanuz retry kardam" saqf ast.

**Request-e khode refresh nabayad token-e morde ra bechasbanad.** Access morde ast. Refresh ba cookie miravad.

**Zanjire-ye client jay-e server nist.** Client header-e tenant ra mifrestad. Server an ra bavar mikonad va dobare check mikonad.

## Single flight

100 request-e hamzaman 401 mishavand. Har kodam mostaghil `POST /refresh` mizanad. Refresh-token-e charkheshi: avvalin refresh token-e ghadim ra batel mikonad, 99-tay-e ba'di ba token-e morde miravand, server hame ra logout mikonad.

Single flight:

- avvalin darkhast-e refresh ye `Promise` misazad va an ra yadash midarad
- baghi, ta an promise tamoom nashode, darkhast-e jadid nemisazand. Haman promise ra await mikonand
- vaghti tamoom shod, yadash pak mishavad
- har caller bad az resolve, request-e khod ra ba token-e taze retry mikonad

```javascript
if (!refreshPromise) {
  refreshPromise = doRefresh().finally(() => { refreshPromise = null; });
}
await refreshPromise;
```

Set kardan-e moteghayer sync ast, `await` bad az an. To JS-e tak-thread, ta avvalin `await`, code-e sync ghat' nemishavad. Agar avval `await doRefresh()` koni va bad moteghayer ra set koni, panjere-ye bug baz ast.

Agar refresh be dalil-e shabake fail shavad, mitavani ye moddat-e kutah "dobare talash nakon" bezari. Agar fail 401-e khode refresh bashad, session morde. Bayad logout koni, na 5 sanie sabr.

Single flight cache-e natije-ye diruz nist. Faghat hamin kar-e dar-hava ra yeki mikonad. Bad az `null` shodan, call-e jadid dobare shabake ast.

## Hala dar front-e Dejban

`packages/api-client/src/axiosInstance.ts` — `createApiClient`.

**Halghe-ye request.** Zaban az `localStorage` (`Accept-Language`, default `fa-IR`). Site az `useSiteStore.getState().getSiteIds()`. Override-e `config.siteId` agar ye call site-e digar bekhad. Access token az `tokenStorage`, magar URL khode refresh bashad. Ragham-e farsi/arabi to params va FormData va JSON be englisi.

**Halghe-ye response.**

- 503 → redirect be `/error/503?system=...`
- 401, ba shart → single flight-e refresh
- 403 → toast-e "dastresi nadarid" faghat agar payam-e farsi-ye business to body nabashad
- baghi → reject ta UI khodesh tarjome konad

Shart-haye na-refresh: `_retry` ghablan true, URL-e login, URL-e refresh, ticket-e public.

`refreshPromise` dakhel-e `createApiClient`. Avvalin 401 an ra misazad. Baghi `await` mikonand. `finally` an ra `null` mikonad.

Bad az 200 va `accessToken`: `tokenStorage.setAccess`, bad header-e `Authorization` ru `originalRequest`, bad `client(originalRequest)`. In `client(...)` dobare az halghe-ye request rad mishavad.

`refreshBlockedUntil`: fail-e gheyr-e 401/403/404 ta 5 sanie refresh-e jadid nemisazad. 401/403/404 miravand logout, `tokenStorage.clear`, `redirectToSignIn`.

`withCredentials: true` ta cookie-ye httpOnly-e refresh beravad.

`export const apiClient = createApiClient(...)` ye instance-e moshtarak. Do instance = do single-flight-e joda = dobare chand refresh.

## Agar beporsand, in tor begou

> Interceptor zanjire-ye ghabl va bad az HTTP ast va caller an ra seda nemizanad. Faghat ghanun-e hame-ye call. Single flight chand 401-e hamzaman ra ru ye promise-ye refresh jam' mikonad. Promise bayad ghabl az await set shavad. Dejban zaban, site az Zustand, bearer, va ragham ra mizanad. Refresh khodesh bearer-e morde nemigirad. Bad token-e taze ham storage ham header mishavad va request-e asli ye bar retry mishavad. 401-e refresh logout ast. Ye apiClient, ye single flight.

## Dah so'al

**1. Interceptor az nazar-e pattern chi ast?**
Chain ru transport. Mitavanad short-circuit konad ya config ra taghir dahad.

**2. Che ghanuni inja mamnoo' ast?**
Ghanun-e ye safhe. Zanjire hame-ye call-ha ra ers midahad.

**3. Saqf-e retry chera?**
401-e bad az refresh-e namovaffagh loop misazad. Ye `_retry` kafi ast.

**4. Single flight che race-i ra mibandad?**
Chand refresh-e hamzaman ba token-e charkheshi ke session-e salem ra logout mikonad.

**5. Chera set-e promise ghabl az await ast?**
Ta do vorudi-ye sync, ghabl az deliver-e event loop, haman promise ra bebinand.

**6. Fail-e shabake va fail-e 401-e refresh farq?**
Avval shayad movaghat bashad. Dovom session morde ast va bayad logout shavad.

**7. Interceptor-e client amniat ast?**
Na. Server tenant va token ra dobare check mikonad.

**8. To Dejban site-id az koja be header miravad?**
`useSiteStore.getState()` dakhel-e interceptor. Hook nist.

**9. Retry chetor token-e ghadim ra nemifrestad?**
`setAccess` va set-e header, bad `client(originalRequest)` ke dobare halghe-ye request ra mibinad.

**10. Do `createApiClient` che moshkeli darad?**
Do `refreshPromise`. Single flight-e yeki digari ra nemibinad.
