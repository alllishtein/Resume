# 14 — Context

Ye dade-ye moshtarak (theme, zaban, user, form) ra ye bar balay-e derakht migozarim. Har bache, har omgh, an ra mikhanad. Sath-haye vasat an dade ra dast-be-dast nemikonand.

In GoF nist. Gharardad-e React ast. To mosahebe esm-e React Context ra begou.

## Moshkel

```
App → Layout → Page → Panel → Toolbar → Button
```

`Button` bayad bedanad user admin ast ya na. Agar an ra prop bedahi, Layout va Page va Panel va Toolbar ham prop-e `isAdmin` migirand, bedune inke khodeshan an ra bekahand. Faghat postchi-and.

Har taghir-e shekl-e an dade, postchi-ha ra ham edit mikonad.

Moshkel "prop" nist. Moshkel dadan-e etela'at be kasi ast ke masraf-konande nist.

## Ide

Context ye gharardad ast (shekl-e value) va ye Provider ke value ra ru ye zir-derakht migozarad. `useContext` nazdik-tarin Provider-e bala ra peyda mikonad.

```
Provider value={user}
  Layout          ← user ra nemibinad
    Page
      Button      ← useContext
```

Button nemidanad value koja sakhte shode. Faghat gharardad ra midanad.

Default-e `createContext` joz'-e tarh ast. `undefined` yani bug-e "Provider yadet raft" crash mikonad. Ye object-e khali yani bug-e bi-seda: dokme fekr mikonad user nist va hich error nist. Har do ra amdan entekhab kon.

## Ghanun-e render

Context broadcast ast. Agar `value` avaz shavad, hame-ye consumer-haye haman context dobare render mishavand.

```jsx
<Provider value={{ user }}>   // object-e jadid har bar
```

Parent render shod → object-e jadid → hame-ye consumer-ha render, hatta agar `user` haman bashad. `useMemo` ru value in sam ra mibandad.

Ye context-e god baraye hame-ye app nasaz. Theme + user + jostoju + mouse. Avaz shodan-e mouse hame-ye app ra render mikonad. Context-e kootah va kam-taghir marz-e bidar shodan ra mahdud mikonad.

Chiz-e por-taghir inja nist. Har kelid-e jostoju, har pixel-e drag. An state-e mahali ast, ya store-i ke subscriber-e riz darad. Context baraye chizi ast ke derakht be an niaz darad va kam avaz mishavad: theme, zaban, session, form-e bala.

Provider-e pa'in, Provider-e bala ra saye mizanad. `useContext` nazdik-tarin ra mibinad. Do form-e too-daro do Provider mikhahand. Bache-ye dakheli form-e birun ra nemibinad.

Context store-e pishrafte nist. Cache va selector nadarad.

Context jay-e composition-e sade nist. Agar faghat ye sath pa'in mikhahi, prop-e sade behtar ast. Context vaghti chand sath-e vasat-e bi-masraf dari.

Context amniat nist. Makhfi kardan-e dokme ba `isAdmin` UI ast. API hamchenan bayad dastresi ra check konad.

Context birun-e render nist. Interceptor-e HTTP `useContext` nadarad. Agar haman dade ra birun-e derakht mikhahi, store-e module-level lazem ast.

Dade-ye server (list-e jadval) context nist. An cache-e query ast. Do manba'-e haghighat misazad.

## Mesal-e koochik

```jsx
const ThemeContext = createContext('light');

function App() {
  const [theme, setTheme] = useState('light');
  const value = useMemo(() => ({ theme, setTheme }), [theme]);
  return (
    <ThemeContext.Provider value={value}>
      <Layout />
    </ThemeContext.Provider>
  );
}
```

`Layout` az theme khabar nadarad. `useMemo` jeloy-e object-e jadid-e bi-taghir ra migirad.

## Hala dar front-e Dejban

**Claim-ha baraye guard-e joz'i.** `packages/ui/src/auth/guard/component-guard.jsx`

`ComponentGuardContext` default-ash `userClaimValues: new Set()` ast. `ComponentGuard` claim-ha ra mikhanad, ba `useMemo` set misazad, va dobare `useMemo` ru object-e value. Haman ghanun-e "object-e jadid har render sam ast".

`Guard` (dokme) `useContext` mikonad va nemidanad claim-ha az koja amade-and.

**Form.** `FormProvider` az react-hook-form. Field `useFormContext` mikhanad. Form-e bozorg-e visitor hamin ra darad ta har input `register` ra az dah sath-e bala pas nagirad. Do form-e too-daro Provider-e khod ra darand. Nazdik-tarin ghalabe mikonad.

**Planner.** `sections/duty-roster/planner-shared.jsx` — `PlannerScopeContext`.

**Shell.** `ThemeProvider`, `SettingsProvider`, `I18nProvider`, `AuthProvider`, `MRTTableStateProvider`. Chand kanal-e joda, na ye `AppContext`.

**Site inja nist.** Site-e entekhabi Zustand ast chon axios birun-e render `getState` mikhahad.

Provider-haye auth `use client` hastand. Context-e React ra be server component-e Next be haman shekl-e hook neshan nade.

## Agar beporsand, in tor begou

> Context baraye dade-ye sakhtari-ye derakht ast. Provider value migozarad, useContext nazdik-tarin ra mikhanad, sath-e vasat postchi nemishavad. Taghir hame-ye consumer-haye haman kanal ra bidar mikonad, pas value ra memo mikonam va theme ra ba jostoju ghalt nemikonam. Dade-ye server va chiz-e birun-e React context nistand. To Dejban claim-e Guard, FormProvider, theme va planner context-haye joda-and. Site Zustand ast chon interceptor hook nist.

## Dah so'al

**1. Prop drilling daghighan chi ast?**
Rad kardan-e dade az sath-hayi ke an ra masraf nemikonand, faghat ta be masraf-konande-ye pa'in beresad.

**2. `useContext` kodam Provider ra mibinad?**
Nazdik-tarin Provider-e haman context balay-e khod. Provider-e pa'in, bala ra saye mizanad.

**3. Chera `value={{ a }}` har render sam ast?**
Object-e jadid identity-e jadid ast. React an ra taghir-e value mibinad.

**4. Che chizi ra context nemikoni?**
State-e por-taghir, cache-e server, va dade-i ke birun-e render lazem ast.

**5. Default-e `createContext` che gharardadi ast?**
Raftar-e "Provider gom shode". Crash-e zud ya shekast-e bi-seda. Bayad amdan bashad.

**6. Context va amniat?**
Hich. Makhfi kardan-e UI dastresi-ye API nist.

**7. Context va Zustand farq-e asli to in proje?**
Site ra ham UI mikhahad ham axios. Context birun-e component khande nemishavad.

**8. `useMemo` ru value-e `ComponentGuard` che ra jelow migirad?**
Bidar shodan-e hame-ye `Guard`-ha vaghti parent render shode vali claim avaz nashode.

**9. Do `FormProvider` too-daro?**
Field-e dakheli nazdik-tarin form ra mibinad.

**10. Chera theme va claims ye context nistan?**
Taghir-e yeki nabayad consumer-e digari ra hatman bidar konad.
