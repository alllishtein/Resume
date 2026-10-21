# 15 — Guard va Protection Proxy

---

## Ye khat

Ghabl az inke kar-e asli shoru shavad, yek ja-neshin miporsad: "in nafar haq-e didan-e in chiz ra darad?" Agar na, kar-e asli **aslan** shoru nemishavad. Kar-e asli in porsesh ra to har safhe copy nemikonad.

---

# BAKHSH-E AVAL — khode pattern

## Proxy chist, ghabl az guard

GoF chahar proxy-e nazdik-be-ham darad. Sakhtar-eshan yeki ast: client interface-e asli ra mibinad, vali object-e **ja-neshin** jelo-ye object-e asli istade.

| Noe | Ja-neshin chi mikonad |
|---|---|
| Virtual | sakhtan-e geran ra ta lahze-ye avvalin estefade aghab mindazad |
| Remote | object-e process-e digar ra mesl-e mahali neshan midahad |
| Smart reference | lock, count, release-e ezafe dor-e dastresi |
| Protection | dastresi ra check mikonad va mitavanad **rad** konad |

Guard-e UI protection proxy ast. "Object-e asli" derakht-e safhe ya dokme ast (`children`). Interface-e moshtarak: "in ra render kon". Proxy mitavanad be jaye an, redirect ya `null` bedahad.

Farq ba decorator, chon sakhtar-e wrap yeki ast: decorator **mas'uliat-e jadid** ezafe mikonad (log, retry) va kar-e asli ra anjam midahad. Protection proxy kar-e asli ra **momken ast anjam nadahad**. Hadaf kontrol-e dastresi ast, na ezafe kardan-e feature.

## Do soal-e joda — in ra yeki nakon

**Authentication.** In nafar kist? Session, token, login. Javab-e na: boro login. Status-e zehni: 401.

**Authorization.** In nafar-e maloom, in kar-e khas ra haq darad? Permission, role, claim, malekiat-e record. Javab-e na: 403, ya makhfi kardan-e haman dokme.

Yek guard-e ghalat har do ra yek redirect-e login mikonad. User-e login-shode-ye bi-permission fekr mikonad password-ash eshtebah ast. User-e bi-session safhe-ye "dastresi nadarid" mibinad va rah-e login ra gom mikonad.

Do proxy-e too-daro, do soal:

```
Auth proxy        kist?           na → login
  Authz proxy     in safhe?       na → 403
    children      kar-e asli
```

## Ghanun-ha

**1. Tasmim ghabl az kar-e asli.**
Agar safhe avval data ra fetch konad va ba'd mafhum shavad permission nist, ham leak-e etela'at dari ham flash-e UI. Proxy avval, fetch-e mahramane ba'd. (Fetch-e khod-e "aya permission daram" mojaz ast. Fetch-e "list-e personnel" ghabl az tasmim na.)

**2. Ta dade-ye tasmim nayamade, tasmim-e manfi nade.**
Session va claim aksaran async-and. Lahze-ye avval `claims` khali ast. Guard-e ajool 403-e dorough midahad va ba'd data miresad. Halat-e sevom lazem ast: **hanuz nemidanam** → loading. Na login, na 403.

In se halat ra hefz kon: loading, rad, ejaze.

**3. Guard-e UI amniat nist.**
Browser dast-e karbar ast. `display:none` va `return null` ba devtools hazf mishavad. Har amal-e vaghe'i bayad server-e dobare porside shavad. Guard baraye masir-e rast-e ensan-e sadegh ast: safhe-ye eshtebah, dokme-ye bi-rabt. Server baraye marz-e vaghe'i.

**4. Subject az proxy khabar nadarad.**
Safhe `if (!user) redirect` copy nemikonad. Agar copy konad, yek safhe faramoosh mikonad va do ghanun-e dastresi dari. Proxy dor-e safhe miminad.

**5. Rad-e authentication bayad jay-e bargasht ra yadash dashte bashad.**
`returnTo` = hamun masiri ke user mikhast bebine. Ba'd az login hamanja. Bedune an, hame mirizand safhe-ye khali-e home. `returnTo` khodesh nabayad open-redirect be site-e bigane bashad. Path-e dakheli, na URL-e motlaq-e har domain.

**6. Shenase-ye dastresi be URL-e kham chasbide nist.**
Agar permission = path-e `/dashboard/duty`, taghir-e URL permission ra mishkanad, va do URL-e yek feature do ghanun mishavand. Shenase-ye sabet-e feature (`componentId`) behtar az string-e path ast. Path mitavanad avaz shavad. Ma'ni-e "in safhe-ye shift ast" na.

## Sath-haye mokhtalef-e yek protection

Hame-ye rad-ha yek kar nistan:

| Sath | Agar na |
|---|---|
| Kol-e app | login |
| Kol-e route | 403, safhe render nemishavad |
| Yek dokme | `null` ya disabled. Baghi-e safhe mimanad |
| Yek record | "in yek malek-e to nist" — aksaran server, chon client list-e hame-ye record-ha ra ghanun-e asli nemidanad |

Dokme-ye `null` 403-e kol-e safhe nist. Agar an-ha ra yek component-e bi-tafavot koni, ya hame-ye safhe-ha 403 mishavand ya dokme-ye mamnoo' hamchenan safhe-ye khali mipichanad.

## Farq-ha

**Decorator.** Wrap-e haman interface, vali kar-e asli ra anjam midahad va chiz-e ezafe mikonad. Proxy-e hefazati mitavanad kar-e asli ra seda nazanad.

**Chain of responsibility.** Chain chand halqe-ye ham-noghsh ke shayad "mal-e man nabashad". Guard-e auth va guard-e authz do **soal-e mokhtalef**-and ke har do bayad javab-e are bedahand. Shabihe zanjir-e too-daro ast, vali short-circuit-ash "rad-e dastresi" ast na "bere be handler-e ba'di-e ham-arz".

**Middleware-e server.** Haman protection, jaye digar. UI guard jaye an ra nemigirad. Server guard jaye flash-e UI ra nemigirad. Har do lazem-and.

## Eshtebah-haye rayej

- 401 va 403 yek route
- tasmim ghabl az residan-e claim
- etemad-e amniati be `null` kardan-e dokme
- permission-e chasbide be URL-e emrooz
- fetch-e dade-ye asli ghabl az guard

## Mafhoom ra injoori begou

> "Protection proxy jelo-ye subject istade va mitavanad dastresi ra rad konad. Subject az an khabar nadarad. Auth va authz do proxy-and: na-shenakht boro login, bi-haq boro 403. Halat-e sevom loading ast ta claim nayamade 403-e dorough nadahim. UI guard amn nist. Server hamon soal ra dobare miporsad. Shenase-ye feature behtar az path-e kham ast. Dokme-ye makhfi ba safhe-ye 403 yek sath nistand."

---

# BAKHSH-E DOVOM — hamin mafhoom to front-e Dejban

**Authentication.** `packages/ui/src/auth/guard/auth-guard.jsx` — `AuthGuard`.

`authenticated` va `loading` az `useAuthContext`. Loading → `SplashScreen`, children na. Na-login → redirect be sign-in ba `returnTo` = path-e alan. Agar khod-e safhe-ye sign-in bashi, loop nemisazi. Path az config ya prop. Children faqat ba'd az ejaze.

**Authorization-e safhe.** Haman file-e `component-guard.jsx` — `PageGuard`.

```jsx
<PageGuard componentId={...dutyRoster...}>
  ...
</PageGuard>
```

`hasComponentAccess(claims, componentId)`. Agar `componentId` hast va mojaz nist: `router.replace('/error/403')` va `null`. Safhe-ye duty roster khodesh `if` permission nadarad. Proxy dorash ast. Path-e estefade: `apps/dejban/src/app/dashboard/.../page.jsx`.

**Halat-e "hanuz nemidanam".** `ready` ta hame-ye in-ha dorost shavad tasmim-e manfi nemigirad:

- loading-e auth tamoom
- `sessionRefreshing` tamoom
- site: ya site entekhab shode, ya aslan site-claim nist

Ta an vaght `LoadingScreen`. In haman ghanun-e "403-e ajool na" ast. Permission-e ba'zi safhe-ha be site-e entekhabi baste ast. Tasmim-e ghabl az site dorough ast.

**Sath-e dokme.** `Guard` haman context-e claim ra mikhanad. Agar claim nist `null`. 403-e kol-e route nist. Baghi-e safhe mimanad. Amniat-e an server ast.

**Sath-e route bedune componentId-e dasti.** `RouteAccessGuard` az `navData` va path, shenase-ye lazem ra dar miavarad. Haman protection, vorudi-ash menu ast na prop-e safhe.

`componentId` shenase-ye sabet-e feature ast (mesl-e duty roster), na string-e URL. Chand page mitavanand yek id dashte bashand.

---

## Script-e 90 sanie

> "Protection proxy interface-e subject ra darad vali mitavanad subject ra seda nazanad. Farq-ash ba decorator hamin rad kardan ast. Auth va authz ra joda mikonam: 401 login, 403 forbidden. Se halat: loading, rad, ejaze. Ta claim nayamade 403 nemidaham. UI jaye server nist. To Dejban AuthGuard returnTo misazad, PageGuard componentId ra ba claim check mikonad va 403 midahad, va ta loading va refresh-e session va site ready nashavad redirect nemikonad. Guard-e dokme faghat null mikonad. Page khodesh if-e permission nadarad."

---

## 10 soal

**1. Protection proxy va decorator?**
Har do wrap-e haman interface-and. Proxy mitavanad kar-e asli ra anjam nadahad. Decorator kar-e asli ra anjam midahad va chizi ezafe mikonad.

**2. 401 va 403 farq?**
401: kist, nemidanim ya login nist. 403: midanim kist, in kar ra haq nadarad.

**3. Halat-e sevom chist?**
Loading. Dade-ye tasmim hanuz nayamade. Tasmim-e manfi-e zud dorough ast.

**4. Chera UI guard amn nist?**
Client dast-e karbar ast. Hide kardan fetch-e API ra jelow nemigirad.

**5. `returnTo` che khatari darad?**
Agar URL-e motlaq-e bigane ra bepaziri, open redirect. Path-e dakheli.

**6. Chera permission rooye path-e kham shekanande ast?**
Taghir-e URL ghanun ra avaz mikonad va do route-e yek feature do ghanun mishavand.

**7. Dokme-ye null va safhe-ye 403?**
Avval baghi-e safhe ra negah midarad. Dovom kol-e route ra mibandad. Yek sath nistan.

**8. To Dejban `PageGuard` che vaght redirect mikonad?**
Ba'd az `ready`: na loading, na sessionRefreshing, va site ya entekhab shode ya aslan lazem nist. Va `componentId` mojaz nist.

**9. Safhe-ye duty roster khodesh check mikonad?**
Na. `PageGuard` dor-e children ast. Subject az proxy khabar-e joda nadarad.

**10. `RouteAccessGuard` che farqi darad?**
Shenase ra az nav va path dar miavarad, na az prop-e dasti-e har page. Haman soal-e authorization.
