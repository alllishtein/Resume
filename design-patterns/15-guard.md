# 15 — Guard (Protection Proxy)

*Dastresi ra jelo-ye khod-e safhe begir. Safhe nabayad khodesh "aya login ast?" ra copy konad.*

---

## Ye khat

Guard yek wrapper ast ke **ghabl** az render-e bache tasmim migirad: neshan bedah, loading, ya redirect. Nazdik-tarin pattern-e klasik: **Protection Proxy** — object-e ja-neshin dastresi be object-e asli ra control mikonad. Bache (`children`) proxy ra nemishnasad.

Do guard-e mokhtalef darim. An-ha ra yeki seda nakon.

## 1. AuthGuard — ki hasti

`packages/ui/src/auth/guard/auth-guard.jsx`

```jsx
export function AuthGuard({ children, signInPath }) {
  const { authenticated, loading } = useAuthContext();
  // loading → SplashScreen
  // !authenticated → redirect be sign-in + returnTo
  // else → children
}
```

So'al: session hast ya na. **Permission-e menu** inja nist.

`returnTo` = path-e alan, ta ba'd az login haman ja bargardi. Age khod-e sign-in bashi, loop nemisazi.

## 2. PageGuard — in safhe baraye in karbar hast?

`packages/ui/src/auth/guard/component-guard.jsx`

```jsx
export function PageGuard({ componentId, children, forbiddenPath = '/error/403' }) {
  const allowed = hasComponentAccess(claims, componentId);
  // !ready → LoadingScreen
  // componentId && !allowed → router.replace('/error/403') va null
  // else → children
}
```

So'al: claim-e `componentId` hast ya na. Mesal-e estefade:

```jsx
<PageGuard componentId={componentPaths.dashboard.arrangements.shifts.dutyRoster.value}>
  ...
</PageGuard>
```

Path-e page: `apps/dejban/src/app/dashboard/.../page.jsx`. Page khodesh if-e permission nadarad.

## 3. Guard — dokme va tekke, na kol-e safhe

```jsx
export function Guard({ componentId, value, children }) {
  const { userClaimValues } = useContext(ComponentGuardContext);
  if (!userClaimValues.has(...)) return null;
  return children;
}
```

403 nist. Faqat UI ra bar midarad. **In security nist.** API hanuz bayad 403 bedahad. Guard-e UI baraye nazdiki-e cheshm ast.

`RouteAccessGuard` hamin tasmim ra az `navData` va path mifahmad, vaghti yek `componentId` roye khod-e page nist.

## Ready che chizi ra montazer mimanad

`PageGuard` ta hame-ye in-ha `ready` nashavad redirect **nemikonad**:

- `loading` auth
- `sessionRefreshing`
- site: ya site entekhab shode, ya aslan site-claim nist

Bedune in, refresh-e safhe yek 403-e dorough midahad chon claims hanuz nayamade. In bug-e rayej-e guard ast. To mosahebe begou.

## Farq-e se taye

```
AuthGuard          session?     na → login
  PageGuard        componentId? na → 403
    Guard          dokme?       na → null (hamchenan API ra lock kon)
      children
```

Proxy-e klassik haman interface-e object ra darad. Inja interface = `children`. Proxy mitavanad object-e asli ra **aslan** render nakonad.

## Script-e 60 sanie

> "Se sath darim. `AuthGuard` faghat authentication ast va be sign-in ba `returnTo` mifrestad. `PageGuard` authorization-e safhe ast: `componentId` ra ba claims check mikonad va 403 midahad, vali ta loading va refresh-e session tamoom nashavad redirect nemikonad. `Guard` dokme ra `null` mikonad va an ra security hesab nemikonam; backend haman claim ra dobare check mikonad. Page-e duty roster khodesh if neminevisad, `PageGuard` dorash ast."

---

## 10 soal

**1. Guard va Proxy?**
Protection Proxy dastresi be subject ra control mikonad. `children` subject ast. Guard haman interface-e "in derakht ra neshan bedeh" ra darad va gahi an ra block mikonad.

**2. Chera Auth va Page joda-and?**
401 va 403 yek chiz nistand. User-e login-nashode bayad login bebine. User-e login-shode-ye bi-permission bayad 403 bebine, na form-e password.

**3. UI guard kafi ast?**
Na. Har API bayad claim ra check konad. `Guard` ke `null` bar migardanad ba devtools dor mikhorad.

**4. Chera `LoadingScreen` ghabl az tasmim?**
Claims va site async hastand. Tasmim-e zud = flash-e 403 ya flash-e data-ye mamnoo'.

**5. `returnTo` chera query ast?**
Ta ba'd az login haman path baz shavad. Bayad path ra validate koni ta open-redirect be site-e bigane nashavad. Inja path-e dakheli-e `window.location.pathname` ast.

**6. `componentId` chist?**
Shenase-ye sabet-e feature (mesl-e duty roster), na URL-e kham. Chand page mitavanand yek id dashte bashand. URL avaz mishavad, permission na.

**7. `Guard` va `PageGuard` farq-e raftar?**
Page kol-e route ra be 403 mibarad. `Guard` faghat an bache ra hazf mikonad ta baghi-e safhe bemanad.

**8. Site in guard che mikonad?**
Permission mitavanad be site-e entekhab-shode baste bashad. Ta site amade nashavad, `allowed` ma'ni-dar nist.

**9. Test?**
Claims-e bedune id → expect-e replace-e 403 va nabudan-e children. Loading=true → 403 **hanuz** seda nashode. AuthGuard: authenticated=false → URL-e sign-in ba `returnTo`.

**10. HOC ya wrapper?**
Ma component-e wrapper (`<PageGuard>`) darim, na `withPageGuard(Page)`. Wrapper to JSX sade-tar tarkib mishavad va type-esh moshkel-e HOC ra nadarad. Har do haman pattern-and.
