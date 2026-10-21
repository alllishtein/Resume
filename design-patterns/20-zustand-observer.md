# 20 — Zustand be onvan-e Observer

*Store taghir mikonad. Faghat kasi ke haman tekke ra mikhanad dobare render mishavad. Birun-e React ham mitavanad bekhanad.*

---

## Ye khat

Observer: subject (`store`) list-e subscriber darad. `set` hame ra khabar mikonad. Subscriber-e React faqat age **selector**-ash taghir karde bashad render mishavad. Subscriber-e gheyr-React `getState()` mikhanad, bedune subscribe-e render.

File: `packages/ui/src/auth/utils/site-storage.js`

```javascript
const useSiteStore = create((set, get) => ({
  selectedSiteIds: readStoredSiteIds(),

  setSiteIds: (siteIds) => {
    const ids = normalizeSiteIds(siteIds);
    if (typeof window !== 'undefined') {
      localStorage.setItem(SITE_KEY, ids[0]);
    }
    set({ selectedSiteIds: ids });
  },

  getSiteIds: () => {
    const state = get();
    if (state.selectedSiteIds.length > 0) return state.selectedSiteIds;
    return readStoredSiteIds();
  },
}));
```

## Do no'e shenavande

**1. React**

```jsx
const selectedSiteIds = useSiteStore((state) => state.selectedSiteIds);
```

`PageGuard` hamin selector ra darad. Taghir-e site → guard dobare `allowed` ra hesab mikonad. Taghir-e field-e digar-e farzi → in component render **nemishavad**, chon selector haman array/value ra dide.

**2. Axios**

```javascript
const getSelectedSiteIds = () => useSiteStore.getState().getSiteIds();
```

Interceptor hook nist. `getState()` snapshot-e alan ast. An subscribe-e render nist; pull ast. Ba taghir-e site, request-e **ba'di** header-e jadid migirad. Request-e dar-rah header-ash avaz nemishavad. In ra daghigh begou.

## Persistence bakhsh-e observer nist

`localStorage` yad-e beyne-refresh ast. `readStoredSiteIds` avvalin state ra por mikonad. `setSiteIds` ham memory (`set`) ham disk ra update mikonad. Do manba' mitavanand joda shavand age kasi mostaghim `localStorage` ra dast bezanad. `getSiteIds` age memory khali bashad disk ra mikhanad. An fallback ast, na subscribe-e storage event.

`normalizeSiteIds` alan **yek** id negah midarad (`slice(0, 1)`). Header `join(',')` baraye chand site neveshte shode, vali store yek id miferestad. To mosahebe dorough-e "multi-site-e kamel" nagou. Begou: "pipe-e chand id hast, ghanun-e alan yek site ast."

## Chera na Context

Ketabche-ye 14: context birun-e render `useContext` nadarad. Site ra ham guard mikhahad ham axios. Store-e module-level har do ra midahad.

Zustand subscriber-e riz darad. Context-e site har consumer-e `SiteContext` ra ba har `set` render mikonad, hatta age faghat yek field-e bi-rabt avaz shode bashad. Ba yek field alan fargh kam ast. Fargh vaghti store bozorg mishavad dide mishavad. Hala daghigh: "alan site koochak ast; dalil-e asli birun-e React ast, na performance."

## Immer

`day-46` immer ra ba zustand gofte. In store `set({ selectedSiteIds })` sade ast, immer nemikhahad. Immer vaghti state-e too-daro ra **taghir-e zaheri** midahi va nemikhahi copy-e dasti benevisi. Observer budan be immer bastegi nadarad.

## Farq ba event-e domain-e backend

| | Zustand | Domain event |
|---|---|---|
| Kei etela' | haman lahze, in-tab | ba'd az commit + outbox |
| Subscriber | selector / `subscribe` | handler-haye assembly |
| Persistence | localStorage-e UI | Postgres |

Har do "set kon, shenavande khabar shavad, subject esm-e shenavande ra nadanad". Yeki UI-e yek tab ast. Digari consistency-e beyn-e module.

## Script-e 60 sanie

> "`useSiteStore` subject ast. `setSiteIds` state ra avaz mikonad va zustand subscriber-ha ra seda mizanad. `PageGuard` ba selector faghat `selectedSiteIds` ra mibine. Axios `getState().getSiteIds()` mikhanad chon interceptor component nist. Avvalin load az localStorage ast va har set ham an ra minevisad. Alan store yek site ra negah midarad. Context baraye in kar nabud chon bayad birun-e React khande shavad."

---

## 10 soal

**1. Observer inja kist?**
Subject: store. `set` notify. Observer-e React: hook ba selector. Observer-e pull: `getState`.

**2. Selector chera?**
Ta component be hame-ye store subscribe nakonad. Faghat khoruji-e selector moghayese mishavad.

**3. `getState` reactive ast?**
Na. Yek snapshot. UI-e baz-e ba an khod-be-khud render nemishavad. Baraye yek request-e alan kafi ast.

**4. Chera localStorage hamzaman?**
Refresh-e safhe memory ra pak mikonad. Site-e entekhabi bayad bemanad. Manba'-e hagh-e runtime hamchenan store ast; storage mirror ast.

**5. Do tab?**
`localStorage` event-e `storage` be tab-e digar mifersad **agar** listen karde bashi. In code `window.addEventListener('storage')` neshon nadad. Pas do tab khodkar sync nemishavand ta reload. An ra be onvan-e mahdoodiat begou.

**6. Race-e `set` va request?**
Request interceptor site ra **lahze-ye send** mikhanad. Set-e ba'di request-e ghabli ra avaz nemikonad. Request-e jadid header-e jadid darad.

**7. Zustand va Redux?**
Har do store-e observer-and. Redux reducer-e sakht va action-e serializable mikhahad. In store se method ast. Redux inja ezafe mibud.

**8. Immer lazem ast?**
Baraye `selectedSiteIds` na. Baraye state-e derakht-i ke chand field-e too-daro ra yekja avaz mikoni bale, ta mutation-e zaheri va copy-e vaghe'i.

**9. Test?**
`useSiteStore.setState` ya `setSiteIds` ra seda bezan, `getState().selectedSiteIds` ra assert kon, va spy-e localStorage. Component: render-e `PageGuard` ba site-e khali vs por.

**10. Key in store ra bozorg nakoni?**
Vaghti server source of truth ast (list-e personnel). An cache-e TanStack ast. Zustand baraye state-e **client** ast: site-e entekhabi, preference-e UI. Do cache-e haghighat = bug.
