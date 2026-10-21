# 14 — Provider / Context

*Yek dependency-e moshtarak ra yek bar bala-ye derakht bedeh. Har bache an ra bekhanad, bedune 8 taye prop.*

---

## Ye khat

Provider yek value ra dar derakht-e React mizarad. `useContext` an ra az har omgh mikhanad. In haman dependency injection-e UI ast: consumer nemidanad value kojast, faghat gharardad ra midanad.

GoF-e nazdik: **mediator-e sade** baraye data-e moshtarak, va gahi **observer** (taghir-e value → render-e consumer). Khod-e React an ra Context seda mikonad. To mosahebe begou "React Context", na "man ye mediator-e GoF neveshtam".

## Moshkel

`claims` ra az `layout` be `page` be `table` be `button` prop bedahi. Har sath-e vasat prop ra faghat rad mikonad. Taghir-e shekl = dast zadan be file-hayi ke an data ra estefade nemikonand.

## Mesal-haye vaghe'i

**1. Claim-ha baraye guard-e jozi**

`packages/ui/src/auth/guard/component-guard.jsx`

```jsx
const ComponentGuardContext = createContext({
  userClaimValues: new Set(),
});

export function ComponentGuard({ children }) {
  const { claims } = useAuthContext();
  const userClaimValues = useMemo(() => getUserClaimValueSet(claims), [claims]);
  const ctx = useMemo(() => ({ userClaimValues }), [userClaimValues]);

  return (
    <ComponentGuardContext.Provider value={ctx}>
      {children}
    </ComponentGuardContext.Provider>
  );
}
```

`Guard` ba `useContext(ComponentGuardContext)` mibinad aya in dokme mojaz ast. List-e claim-ha ra prop nemigirad.

**2. Form**

`FormProvider` az react-hook-form. Field-ha `useFormContext()` mikhanand. Form-e bozorg-e visitor (`visitor-and-appointment-new-edit-form.jsx`) hamin kar ra mikonad ta 20 input `register` ra dasti pas nadahand.

**3. Scope-e planner**

`sections/duty-roster/planner-shared.jsx` — `PlannerScopeContext.Provider`. Zir-component-haye shift nemidanand state-e planner ra ki sakht.

**4. Shell**

`ThemeProvider`, `SettingsProvider`, `I18nProvider`, `AuthProvider`, `MRTTableStateProvider`, `WorkspaceTabActivityProvider`. Har kodam **yek** delil. An-ha ra yek context-e `AppGodContext` nakon.

## Ghanun-e render

Har taghir-e `value`, hame-ye consumer-haye **haman** context dobare render mishavand. Pas:

- `value={{ userClaimValues }}` object-e jadid **har** render misazad va hame ra bidar mikonad. Code-e bala `useMemo` darad. An ra to mosahebe begou.
- Context-e "har keystroke" (search box) ghalat ast. An state-e mahali ya Zustand ast.
- Context baraye chiz-e **kam-taghir** va **derakht-gunja** ast: theme, auth, claims, zaban, tenant-e UI.

Default-e `createContext({ userClaimValues: new Set() })` vaghti Provider gom shode, `Guard` crash nemikonad; hame chiz ra makhfi mikonad ya ejaze midahad, baste be logic. Danestan-e default bakhsh-e debug ast.

## Farq ba Zustand (ketabche-ye 20)

| | Context | Zustand |
|---|---|---|
| Subscription | hame-ye consumer-e an context | faqat selector-i ke taghir karde |
| Kharej az React | na | `getState()` moshkel nist |
| Inja | theme, form, claims-e guard | site-e entekhab-shode, chon axios ham an ra mikhahad |

Site ra to context-e faghat-React nagozashtim chon interceptor-e axios component nist va `useContext` nemitavanad.

## Script-e 60 sanie

> "Context dependency-e moshtarak-e derakht ast. `ComponentGuard` set-e claim ra yek bar misazad va `Guard` dokme-ha an ra mikhanand, bedune prop drilling. `FormProvider` hamin kar ra baraye react-hook-form mikonad. Value ra `useMemo` mikonim ta object-e jadid har render hame ra bidar nakonad. Chiz-e por-taghir va chiz-i ke birun-e React lazem ast — mesl-e site id baraye axios — miravad to Zustand, na context."

---

## 10 soal

**1. Context che moshkeli ra hal mikonad?**
Prop drilling. Data-e sakhtari (theme, auth, form) ra bedune rad kardan az sath-haye bi-tafavot mifersad.

**2. Chera context-e god yek dane nist?**
Har taghir hame-ye consumer-ha ra render mikonad. Shekastan be context-haye koochak (theme joda az claims) blast radius ra mahdud mikonad.

**3. `useMemo` roye value chera?**
Identity-e object. Bedune an, parent render = value-e jadid = hame-ye `useContext` render, hatta age claim avaz nashode bashad.

**4. Provider gom shavad chi?**
Default-e `createContext` bargardad. Ya crash-e `undefined`, ya raftar-e bi-seda. Default ra amdan entekhab kon va to dev warning bedeh.

**5. Context va Redux/Zustand?**
Context transport-e React ast, store-e pishrafte nist (selector, birun-e render, persistence). Baraye site-e ma Zustand ast chon axios `getState` mikhahad.

**6. `FormProvider` pattern-e joda ast?**
Context + composition. Field-ha be form-e bala vasl mishavand bedune prop-e `control` dar har sath. Agar do form-e too-daro dari, do provider dari; `useFormContext` nazdik-tarin ra mibinad.

**7. Performance-e `claims` bozorg?**
Set yek bar `useMemo` mishavad. Consumer-e `Guard` hanuz ba taghir-e claim render mishavad. An ghaabel-e ghabool ast chon claim har keystroke avaz nemishavad.

**8. Server component va context?**
Provider-haye in app `use client` hastand (`AuthGuard` ham). Context-e React to server component-e Next be haman shekl-e client zende nist. Boundary ra moshakhas kon.

**9. Test?**
Render ba `<ComponentGuard>` va claims-e fake. Bedune provider, default ra test kon ta raftar-e "gom shode" shaffaf bashad.

**10. Key az context be zustand mohajerat mikoni?**
Vaghti ya subscription-e riz mikhahi, ya module-e gheyr-React (axios, router guard birun az render) bayad haman state ra bekhanad.
