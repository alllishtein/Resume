# 14 — Provider / Context

---

## Ye khat

Yek dade-ye moshtarak (theme, zaban, user, form) ra **yek bar** bala-ye derakht mizarim. Har bache, har omgh, an ra mikhanad. Sath-haye vasat an dade ra dast-be-dast nemikonand.

In GoF nist. Gharardad-e React (va framework-haye shabihe) ast. Nazdik-tarin fekr: dependency-e mohiti, na mediator-e GoF. To mosahebe esm-e "React Context" ra begou.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel-e prop drilling

```
App → Layout → Page → Panel → Toolbar → Button
```

`Button` bayad bedanad user admin ast ya na. Agar an ra prop bedahi, `Layout` va `Page` va `Panel` va `Toolbar` ham prop-e `isAdmin` migirand, **bedune** inke khodeshan an ra bekahand. Faghat postchi-and.

Har taghir-e shekl-e an dade, postchi-ha ra ham edit mikonad. Derakht-e 8 sath, 8 file baraye yek flag.

Moshkel "prop" nist. Moshkel **dadan-e etela'at be kasi ke masraf-konande nist** ast.

## Ta'rif

Context yek **gharardad** ast (shekl-e value) va yek **arze-konande** (Provider) ke value ra rooye yek zir-derakht mizarad. `useContext` nazdik-tarin Provider-e bala ra peyda mikonad va value ra mikhanad. Sath-haye vasat import-e an value ra ham lazem nadarand.

```
Provider value={user}
  Layout          ← user ra nemibinad
    Page          ← nemibinad
      Button      ← useContext(UserContext)
```

Button nemidanad value kojast sakhte shode. Faghat gharardad ra midanad. In az nazar-e zehni hamon DI-e sath-e UI ast: consumer be sakhtan-e dependency vasl nist.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Context object | `createContext(default)` — kanal, na dade-ye zende |
| Provider | value-e alan ra rooye zir-derakht elam mikonad |
| Consumer / `useContext` | value ra mikhanad va ba taghir-ash dobare render mishavad |
| Default | chizi ke agar Provider gom bashad bargardad |

Default joz'-e tarh ast. `undefined` ya'ni bug-e "Provider yadet raft" crash mikonad. Yek object-e khali ya'ni bug-e bi-seda: dokme fekr mikonad user nist va hich error nist. Har do ra **amdan** entekhab kon.

## Ghanun-e render — in bakhsh ra hefz kon

Context broadcast ast, na selector-e hooshmand.

Agar `value` avaz shavad (az nazar-e **identity** ya moqayese-ye React), **hame-ye** consumer-haye haman context dobare render mishavand. Kasi ke faghat `user.name` mikhast va `user.theme` avaz shode ham bidar mishavad, agar har do dakhel-e yek value bashand.

Pas:

**1. Value-e object-e taze-ye har render sam-ast.**

```jsx
<Provider value={{ user }}>   // object-e jadid har bar
```

Parent render shod → object-e jadid → hame-ye consumer-ha render, **hatta** agar `user` haman bashad. `useMemo` rooye value, ya shekastan-e context, in sam ra mibandad.

**2. Yek context-e God baraye hame-ye app.**
Theme + user + search-box + mouse position. Avaz shodan-e mouse hame-ye app ra render mikonad. Shekastan be context-haye **kootah va kam-taghir** marz-e bidar shodan ra mahdud mikonad.

**3. Chiz-e por-taghir inja nist.**
Har keystroke-e jostojoo, har pixel-e drag. An state-e mahali ast, ya store-i ke subscriber-e riz darad. Context baraye chiz-i ast ke derakht be an niaz darad va **kam** avaz mishavad: theme, locale, session, form-e bala, claim-haye safhe.

**4. Provider-e pa'in, Provider-e bala ra saye mizanad.**
`useContext` nazdik-tarin ra mibinad, na hame ra. Do form-e too-daro do Provider-e form mikhahand. Bache-ye dakheli form-e birun ra nami-binad. Agar yek form-e jahani-e bi-khabar dashte bashi, field-e dakheli be form-e ghalat vasl mishavad.

## Context che chizi nist

**Store-e pishrafte.** Cache, selector, middleware, time-travel. Context hich-kodam ra nemidahad. Faghat value va render.

**Jaygozin-e composition.** Gahi bejaye context, `children` ya render-prop sade-tar ast. Agar faghat yek sath pa'in mikhahi, prop-e sade az context-e yek-bar-masraf behtar ast. Context vaghti **chand** sath-e vasat-e bi-masraf dari.

**Amn-e vaghe'i.** Makhfi kardan-e dokme ba context-e `isAdmin` UI ast. API hamchenan bayad dastresi ra check konad. Context to browser dast-e karbar ast.

**Chiz-e birun-e render.** Interceptor-e HTTP, yek function-e sade, `setTimeout`: `useContext` anja nist. Agar haman dade ra birun-e derakht mikhahi, context tanha kafi nist. Store-e module-level (ketabche-ye Zustand) anja vared mishavad.

## Farq ba prop-e sade

Prop vazeh, mahali, va trace-ash asan ast. Context penhan, jahani-e zir-derakht, va trace-ash "ki in value ra gozasht?" sakht-tar. Gha'ede: prop ta vaghti drilling **dard** nashode. Context vaghti dard-e drilling az dard-e penhan budan bishtar shod.

## Farq ba store-e observer

| | Context | Store (Zustand, Redux) |
|---|---|---|
| Subscriber | hame-ye consumer-e haman kanal | kasi ke selector-ash avaz shode |
| Birun-e React | na | bale, `getState` |
| Default-e zehni | dade-ye sakhtari-e kam-taghir | state-e client ke chand ja, ba ritm-e motefavet, an ra mikhanad |

Theme context mimanad. Site-id-i ke ham dokme an ra mikhanad ham har request-e HTTP, store mishavad. Dalil-e asli-e dovomi "performance-e selector" nist. Dalil-e asli **birun-e render** ast.

## Mesal-e donya

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

function Button() {
  const { theme } = useContext(ThemeContext);
  return <button className={theme} />;
}
```

`Layout` az theme khabar nadarad. `Button` kanal ra mikhanad. `useMemo` jeloye object-e jadid-e bi-taghir ra migirad.

## Eshtebah-haye rayej

- `value={{ ... }}` bedune memo
- yek context baraye state-e kol-e app
- context baraye data-ye server (list-e jadval). An cache-e server ast (query library), na mohit-e UI. Do manba'-e haghighat misazad
- faramoosh-e Provider va etemad-e bi-seda be default
- farz-e inke context-e client to server component-e hamun shekl zende ast. Marz-e client/server joda ast

## Mafhoom ra injoori begou

> "Context drilling-e prop ra baraye dade-ye sakhtari hazf mikonad. Provider value ra mizarad, useContext nazdik-tarin ra mikhanad. Broadcast ast: taghir-e value hame-ye consumer-haye haman kanal ra render mikonad, pas value ra memo mikonam va context-e God nemisazam. Chiz-e por-taghir va chiz-e birun-e React context nist. Data-ye server ham context nist. UI-e admin jaye check-e API ra nemigirad."

---

# BAKHSH-E DOVOM — hamin mafhoom to front-e Dejban

**Claim-ha baraye guard-e jozi.** `packages/ui/src/auth/guard/component-guard.jsx`

`ComponentGuardContext` default-ash `userClaimValues: new Set()` ast. `ComponentGuard` az `useAuthContext` claim-ha ra mikhanad, ba `useMemo` set misazad, va **dobare** `useMemo` rooye object-e value. Haman ghanun-e "object-e jadid-e har render sam ast" inja re'ayat shode.

`Guard` (dokme) `useContext` mikonad va nemidanad claim-ha az koja amade-and. Panel-e vasat prop-e `claims` pas nemidahad.

**Form.** `FormProvider` az react-hook-form. Field `useFormContext` mikhanad. Form-e bozorg-e visitor (`visitor-and-appointment-new-edit-form.jsx`) hamin ra darad ta har input `register` ra az 15 sath-e bala pas nagirad. Do form-e too-daro (mesal-e hamrah-e goroohi) Provider-e khod ra darand. Nazdik-tarin Provider ghalabe mikonad. Agar field "be form-e ghalat vasl shod" didi, hamin ghanun ast.

**Planner.** `sections/duty-roster/planner-shared.jsx` — `PlannerScopeContext`. Zir-component-e shift state-e planner ra prop-drill nemikonad.

**Shell.** `ThemeProvider`, `SettingsProvider`, `I18nProvider`, `AuthProvider`, `MRTTableStateProvider`, `WorkspaceTabActivityProvider`. Chandin kanal-e joda, na yek `AppContext`. Haman "God context nasaz".

**Site inja nist.** Site-e entekhabi Zustand ast chon axios birun-e render `getState` mikhahad. Context an kar ra nemikard. Entekhab-e jaye dorost-e pattern, na "hame chiz context".

Provider-haye auth va guard `use client` hastand. Context-e React ra be server component-e Next be haman shekl-e hook neshan nade. Marz-e client ra negah dar.

---

## Script-e 90 sanie

> "Context baraye dade-ye sakhtari-e derakht ast, na baraye har state. Provider value mizarad, consumer nazdik-tarin ra mikhanad, sath-e vasat postchi nemishavad. Taghir hame-ye consumer-haye haman kanal ra bidar mikonad, pas object-e value ra memo mikonam va theme ra ba search-box ghalt nemikonam. Data-ye server va chiz-e birun-e React context nistand. To Dejban claim-e Guard, FormProvider, theme va planner context-haye joda-and. Site Zustand ast chon interceptor hook nist."

---

## 10 soal

**1. Prop drilling daghighan chi ast?**
Rad kardan-e dade az sath-hayi ke an ra masraf nemikonand, faghat ta be masraf-konande-ye pa'in beresad.

**2. `useContext` kodam Provider ra mibinad?**
Nazdik-tarin Provider-e haman context bala-ye khod. Provider-e pa'in, bala ra saye mizanad.

**3. Chera `value={{ a }}` har render sam ast?**
Object-e jadid identity-e jadid ast. React an ra taghir-e value mibinad va hame-ye consumer-ha ra render mikonad.

**4. Che chizi ra context nemikoni?**
State-e por-taghir, cache-e server, va dade-i ke birun-e render lazem ast.

**5. Default-e `createContext` che gharardadi ast?**
Raftar-e "Provider gom shode". Crash-e zud ya shekast-e bi-seda. Bayad amdan bashad.

**6. Context va amniat?**
Hich. Makhfi kardan-e UI dastresi-e API nist.

**7. Context va Zustand farq-e asli to in proje?**
Site ra ham UI mikhahad ham axios. Context birun-e component khande nemishavad. Store mishavad.

**8. `useMemo` rooye value-e `ComponentGuard` che ra jelow migirad?**
Bidar shodan-e hame-ye `Guard`-ha vaghti parent render shode vali claim avaz nashode.

**9. Do `FormProvider` too-daro?**
Field-e dakheli nazdik-tarin form ra mibinad. Agar ghalat vasl shod, saye-ye Provider ast, na bug-e `register`.

**10. Chera theme va claims yek context nistand?**
Taghir-e yeki nabayad consumer-e digari ra hatman bidar konad. Kanal-e koochak marz-e render ra negah midarad.
