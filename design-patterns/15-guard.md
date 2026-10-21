# 15 — Guard

Ghabl az inke kar-e asli shoru shavad, ye ja-neshin miporsad: "in nafar haq-e didan-e in chiz ra darad?" Agar na, kar-e asli aslan shoru nemishavad. Safhe in porsesh ra to har ja copy nemikonad.

## Ide

GoF chahar proxy-e nazdik darad. Shekl-eshan yeki ast: client interface-e asli ra mibinad, vali object-e ja-neshin jelo-ye object-e asli istade.

| Noe | Ja-neshin chi mikonad |
|---|---|
| Virtual | sakhtan-e geran ra ta lahze-ye avval aghab mindazad |
| Remote | object-e process-e digar ra mesl-e mahali neshan midahad |
| Protection | dastresi ra check mikonad va mitavanad rad konad |

Guard-e UI protection proxy ast. "Object-e asli" derakht-e safhe ya dokme ast (`children`). Proxy mitavanad be-jaye an, redirect ya `null` bedahad.

Decorator shekl-e wrap-e nazdik darad, vali kar-e asli ra anjam midahad va chizi ezafe mikonad. Protection proxy mitavanad kar-e asli ra aslan seda nazanad. Hadaf kontrol-e dastresi ast.

## Do so'al-e joda

**Authentication.** In nafar kist? Session, token, login. Javab-e na: boro login. 401.

**Authorization.** In nafar-e malum, in kar-e khas ra haq darad? Permission, claim. Javab-e na: 403, ya makhfi kardan-e haman dokme.

Ye guard-e ghalat har do ra ye redirect-e login mikonad. User-e login-shode-ye bi-permission fekr mikonad password-ash eshtebah ast.

```
Auth          kist?          na → login
  Authz       in safhe?      na → 403
    children  kar-e asli
```

Ghanun-ha:

**Tasmim ghabl az kar-e asli.** Agar safhe avval data ra fetch konad va bad mafhum shavad permission nist, ham leak dari ham flash-e UI. Fetch-e "aya permission daram" mojaz ast. Fetch-e list-e personnel ghabl az tasmim na.

**Ta dade-ye tasmim nayamade, tasmim-e manfi nade.** Session va claim aksaran async-and. Lahze-ye avval `claims` khali ast. Guard-e ajoul 403-e dorugh midahad. Halat-e sevom lazem ast: hanuz nemidanam → loading.

Se halat: loading, rad, ejaze.

**Guard-e UI amniat nist.** Browser dast-e karbar ast. `return null` ba devtools hazf mishavad. Har amal-e vaghe'i bayad server dobare beporsad. Guard baraye masir-e rast-e ensan-e sadegh ast.

**Safhe az proxy khabar-e joda nadarad.** Agar har safhe `if (!user) redirect` copy konad, yeki faramush mikonad.

**Rad-e login bayad jay-e bargasht ra yadash dashte bashad.** `returnTo` = haman masiri ke user mikhast bebinad. `returnTo` nabayad URL-e motlaq-e site-e bigane bashad. Path-e dakheli.

**Shenase-ye dastresi be URL-e kham nachasbad.** Agar permission = path-e `/dashboard/duty`, taghir-e URL permission ra mishkanad. `componentId` sabet-e feature behtar az string-e path ast.

Sath-ha yeki nistan:

| Sath | Agar na |
|---|---|
| Kol-e app | login |
| Kol-e route | 403 |
| Ye dokme | `null`. Baghi-ye safhe mimanad |
| Ye record | aksaran server, chon client ghanun-e asli-ye hame-ye record-ha ra nemidanad |

## Hala dar front-e Dejban

**Authentication.** `packages/ui/src/auth/guard/auth-guard.jsx` — `AuthGuard`.

`authenticated` va `loading` az `useAuthContext`. Loading → `SplashScreen`. Na-login → redirect be sign-in ba `returnTo`. Agar khode safhe-ye sign-in bashi, loop nemisazi.

**Authorization-e safhe.** `component-guard.jsx` — `PageGuard`.

```jsx
<PageGuard componentId={...dutyRoster...}>
  ...
</PageGuard>
```

`hasComponentAccess(claims, componentId)`. Agar mojaz nist: `router.replace('/error/403')` va `null`. Safhe-ye duty roster khodesh `if` permission nadarad. Path: `apps/dejban/src/app/dashboard/.../page.jsx`.

**Halat-e "hanuz nemidanam".** `ready` ta hame-ye in-ha dorost shavad tasmim-e manfi nemigirad: loading-e auth tamoom, `sessionRefreshing` tamoom, va site ya entekhab shode ya aslan site-claim nist. Ta an vaght `LoadingScreen`. Permission-e ba'zi safhe-ha be site-e entekhabi baste ast.

**Sath-e dokme.** `Guard` agar claim nist `null` mikonad. 403-e kol-e route nist. Amniat-e an server ast.

**`RouteAccessGuard`** shenase ra az `navData` va path dar miavarad, na az prop-e dasti-ye har page.

## Agar beporsand, in tor begou

> Protection proxy jelo-ye safhe istade va mitavanad safhe ra render nakonad. Auth va authz ra joda mikonam: 401 login, 403 forbidden. Se halat: loading, rad, ejaze. Ta claim nayamade 403 nemidaham. UI jay-e server nist. To Dejban AuthGuard returnTo misazad. PageGuard componentId ra ba claim check mikonad. Ta loading va refresh-e session va site ready nashavad redirect nemikonad. Guard-e dokme faghat null mikonad.

## Dah so'al

**1. Protection proxy va Decorator?**
Har do wrap-and. Proxy mitavanad kar-e asli ra anjam nadahad. Decorator kar-e asli ra anjam midahad va chizi ezafe mikonad.

**2. 401 va 403 farq?**
401: login nist. 403: midanim kist, in kar ra haq nadarad.

**3. Halat-e sevom chi ast?**
Loading. Dade-ye tasmim hanuz nayamade. Tasmim-e manfi-ye zud dorugh ast.

**4. Chera UI guard amn nist?**
Client dast-e karbar ast. Hide kardan fetch-e API ra jelow nemigirad.

**5. `returnTo` che khatari darad?**
Agar URL-e motlaq-e bigane ra bepazi, open redirect. Path-e dakheli.

**6. Chera permission ru path-e kham shekanande ast?**
Taghir-e URL ghanun ra avaz mikonad.

**7. Dokme-ye null va safhe-ye 403?**
Avval baghi-ye safhe ra negah midarad. Dovom kol-e route ra mibandad.

**8. To Dejban `PageGuard` che vaght redirect mikonad?**
Bad az `ready`: na loading, na sessionRefreshing, va site ya entekhab shode ya lazem nist. Va `componentId` mojaz nist.

**9. Safhe-ye duty roster khodesh check mikonad?**
Na. `PageGuard` dor-e children ast.

**10. `RouteAccessGuard` che farqi darad?**
Shenase ra az nav va path dar miavarad, na az prop-e dasti-ye har page.
