# 20 — Store be onvan-e Observer

Ketabche-ye 08 observer-e **mafhoom** ast. Inja haman mafhoom rooye **state-e client** zemestani mishavad. Agar 08 ra nakhandi, avval an. In file az "Attach / Notify / chand shenavande" shoru nemikonad. Az ja-i shoru mikonad ke UI va yek tab-e browser farq darand.

---

## Ye khat

Yek anbar-e state birun-e derakht-e component zendegi mikonad. Har kas ke be yek **tekke** az an alaghe darad, vaghti haman tekke avaz shod khabar mishavad. Kas-e bi-alaghe bidar nemishavad. Kasi ke component nist ham mitavanad **hamin lahze** anbar ra bekhanad, bedune inke render beshavad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

State-e "kodam site alan entekhab shode" ra chand ja mikhahand:

- header-e safhe
- guard-e permission (permission shayad be site baste bashad)
- **har** request-e HTTP, dakhel-e tabe'-i ke component nist

Agar an ra `useState` bala-ye derakht bezani, do moshkel-e ketabche-ye context bargasht: drilling, va broadcast-e hame-ye consumer-ha. Va moshkel-e sevom ke context **aslan** hal nemikonad: interceptor-e axios `useState` nadarad. Hook faghat zire-ye render ast.

Agar har component yek `localStorage.getItem` mostaghim bezanad, chand manba'-e haghighat dari. Yeki set karde, digari hanuz ghadim ra dar hafeze-ye render darad. Kasi Notify nemishavad.

## Ta'rif

Store = subject-e observer + yek object-e data.

- `getState()` pull: snapshot-e alan, bedune subscribe
- `setState` / `set` taghir + **Notify**
- `subscribe(listener)` Attach
- hook-e `useStore(selector)` yek observer-e React: Attach vaghti mount, Detach vaghti unmount, va **faghat** agar khoruji-e selector avaz shode bashad render

Selector haman "man be hame-ye subject alaghe nadaram" ast. Subject hanooz yek dane ast. Observer-ha riz mishavand.

```javascript
const useSite = create((set, get) => ({
  id: null,
  setId: (id) => set({ id }),
  getId: () => get().id,
}));

// observer-e React:
const id = useSite((s) => s.id);

// pull-e gheyr-e React:
const now = useSite.getState().getId();
```

`setId` list-e component-ha ra be esm nemishnasad. Haman ghanun-e subject-e GoF. Fargh-e abzar: bejaye `observer.Update()`, store tabe'-haye subscribe-shode ra seda mizanad va React moghayese-ye selector mikonad.

## Ghanun-ha

**1. Yek manba'-e haghighat baraye haman tekke-ye state.**
Agar ham store va ham `localStorage` va ham `useState`-e joda "site" ra negah darand, se subject dari. Taghir-e yeki Notify-e digari nist. Ya storage **mirror** ast (store set mikonad, storage ra ham minevisad, va faghat store ra mikhanand) ya storage manba' ast va store nadari. Har do ra manba' kardan bug ast.

**2. `getState` reactive nist.**
Snapshot-e lahze-ye call. UI-e baz-e ba an khod-be-khod render nemishavad. Baraye "header-e hamin request chi bashad" kafi ast. Baraye "vaghti site avaz shod in component avaz shavad" kafi nist. An selector mikhahad.

**3. Selector bayad khoruji-e koochak va sabet bedahad.**
`(s) => s.id` khoob. `(s) => ({ id: s.id, name: s.name })` object-e jadid **har** Notify, hatta agar id avaz nashode. Haman sam-e identity-e context. Ya primitive bargardan, ya moghayese-ye amiq.

**4. Set-e toot-daro copy mikhahad.**
`state.user.name = 'a'` mutation-e mostaghim aksaran Notify-e dorost nemizanad, chon reference-e `user` avaz nashode. Ya object-e jadid besaz (`set({ user: { ...state.user, name } })`) ya abzar-e immer ke mutation-e **zaheri** ra be copy-e vaghe'i tabdil mikonad. Immer observer nist. Komak-e neveshtan-e set-e toot-daro ast. Store-e yek field immer nemikhahad.

**5. Detach.**
Hook-e khoob unmount ra unsubscribe mikonad. Subscribe-e dasti-e `store.subscribe(...)` ke unmount nakoni, haman memory leak-e klassik-e observer ast. Subject-e store omr-e tab ra darad. Component omr-e safhe ra. Farq-e omr = hatman Detach.

**6. Store-e client jaye cache-e server nist.**
List-e personnel haghighat-ash server ast. Copy-e an to Zustand va copy-e an to query cache do haghighat. Store baraye chizi ast ke **client** malek-ash ast: site-e entekhabi, baz budan-e sidebar, draft-e zakhire-nashode. Chiz-e malek-e server: query cache.

## Push-e UI va pull-e transport

Do shenavande-ye motefavet, yek subject:

| Shenavande | Che mikhahad | Che abzari |
|---|---|---|
| Component | "vaghti avaz shod dobare render sho" | selector, subscribe |
| Interceptor | "hamin alan, site-e header chi ast" | `getState`, bedune subscribe |

Set-e ba'di, request-e **ghabl** ra avaz nemikonad. Request-e ghabl header-ash ra lahze-ye send khande. Request-e ba'di snapshot-e jadid migirad. In race bug nist. Gharardad-e pull ast. Agar an ra "header-e hame-ye request-haye dar-rah ham avaz shavad" bekahi, dige pull-e sade nist. Bayad saf-e request ra subject koni. Aksaran an kar ra nemikoni.

## Persistence mirror ast

`localStorage` tab ra az refresh zende mibarad. Memory-e store na. Pattern-e dorost:

- start: storage → state-e avval
- set: state **va** storage
- khanadan-e runtime: state

Agar kasi mostaghim storage ra dast bezanad va store ra na, mirror shekaste. API-e omumi faghat `set` store bashad.

Do tab: `localStorage` event-e `storage` be tab-e **digar** mifrestad, va faghat agar `addEventListener('storage')` dashte bashi. Bedune an, do tab do subject-e joda-and ta reload. Observer-e dakhel-e yek tab, observer-e beyn-e tab nist magar an event ra vasl koni.

## Farq ba domain event-e server

| | Store-e UI | Domain event |
|---|---|---|
| Omq | yek tab | process / bus |
| Zaman-e Notify | haman lahze | aksaran ba'd az commit |
| Shenavande | selector va `getState` | handler-haye module |
| Manba'-e haghighat | client | database |

Har do "set kon, shenavande-ye bi-esm khabar shavad". Yeki session-e ensan-e jelo-ye browser. Digari consistency-e system. Store-e Zustand outbox nemikhahad. Event-e aggregate `useStore` nemishavad.

## Eshtebah-haye rayej

- list-e server dakhel-e store
- selector-i ke object-e jadid misazad
- `getState` baraye render-e zende
- subscribe-e dasti bedune unsubscribe
- do manba': storage-e mostaghim **va** store
- immer-e ejbari baraye yek `string`

## Mafhoom ra injoori begou

> "Store subject-e observer-e client ast. set Notify mikonad. Selector faghat observer-e alaghemand ra render mikonad. getState pull-e bi-render ast baraye ja-i mesl-e interceptor. Hook bayad unsubscribe konad. Yek manba': store. Storage mirror-e refresh ast. Data-ye server in store nist. Immer faghat neveshtan-e toot-daro ra asan mikonad. Do tab bedune listener-e storage sync nemishavand."

---

# BAKHSH-E DOVOM — hamin mafhoom to front-e Dejban

`packages/ui/src/auth/utils/site-storage.js`

```javascript
const useSiteStore = create((set, get) => ({
  selectedSiteIds: readStoredSiteIds(),
  setSiteIds: (siteIds) => {
    const ids = normalizeSiteIds(siteIds);
    if (typeof window !== 'undefined') {
      if (ids.length) localStorage.setItem(SITE_KEY, ids[0]);
      else localStorage.removeItem(SITE_KEY);
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

Subject: `useSiteStore`. `set` haman Notify. `get` pull.

**Observer-e React.** `PageGuard` selector darad: `useSiteStore((state) => state.selectedSiteIds)`. Taghir-e site guard ra dobare hesab mikonad. Field-e digar agar ezafe shavad va selector an ra nadahad, guard bidar nemishavad.

**Pull-e transport.** Interceptor: `useSiteStore.getState().getSiteIds()`. Hook nist. Request-e ba'di header-e jadid. Request-e dar-rah na.

**Mirror.** Avvalin state az `readStoredSiteIds`. Har `setSiteIds` ham `set` ham `localStorage`. Runtime az memory mikhanad, va agar memory khali bashad fallback-e disk darad. Manba'-e omumi `setSiteIds` ast. Dast-e mostaghim-e `localStorage` gharardad nist.

`normalizeSiteIds` alan `slice(0, 1)` ast. **Yek** site. Header-e axios `join(',')` baraye chand id neveshte shode, vali store yek id mifrestad. Pipe-e chand-ta'i hast, ghanun-e alan yek site. "Multi-site-e kamel" nagou.

Listener-e `window` `storage` in file nist. Do tab khodkar yek site nemishavand.

Immer in store nist. `set({ selectedSiteIds: ids })` object-e jadid-e sath-e avval ast. Kafi. Immer ra be an napichan.

List-e personnel in store nist. An query cache ast. Site-e entekhabi male client ast. Haman joda'i-e bakhsh-e avval.

---

## Script-e 90 sanie

> "Store subject-e observer ast. set shenavande-ha ra khabar mikonad bedune esm-e component. Selector render ra riz mikonad. getState pull-e lahze ast va UI ra zende nemikonad. Unsubscribe joz'-e hook ast chon store az safhe bishtar zende mimanad. Storage mirror-e refresh ast na manba'-e dovom. To Dejban useSiteStore hamin kar ra baraye site mikonad. PageGuard selector darad. Axios getState mikhanad. set ham localStorage ra minevisad. Alan yek site normalize mishavad. Do tab listener-e storage nadarand. Data-ye server in store nist."

---

## 10 soal

**1. Store kodam naghsh-e observer ast?**
Subject. `set` Notify. `subscribe` Attach. Hook Detach-e unmount ra ham anjam midahad.

**2. Selector che chizi ra kam mikonad?**
Tedad-e render. Observer faghat khoruji-e khod ra moghayese mikonad, na kole store.

**3. Chera selector-e object-e jadid sam ast?**
Identity-e khoruji har bar avaz mishavad. React fekr mikonad state avaz shode, hatta agar field-ha haman bashand.

**4. `getState` key kafi nist?**
Vaghti UI bayad ba taghir-e ba'di dobare render shavad. `getState` snapshot-e bi-subscribe ast.

**5. Immer che pattern-i nist?**
Observer nist. Abzar-e copy-e toot-daro ast. Store-e yek field an ra nemikhahad.

**6. Chera list-e server to store na?**
Manba'-e haghighat-ash server ast. Do cache do javab-e motanaghez misazad.

**7. Mirror-e localStorage che gharardadi darad?**
Start az disk. Set har do. Khanadan az memory. Dast-e mostaghim-e disk manba'-e dovom misazad.

**8. Do tab chetor sync nemishavand?**
Event-e `storage` faghat agar listen koni. Bedune listener, har tab subject-e khod ra darad.

**9. To Dejban interceptor chera hook-e site nemizanad?**
Interceptor render nist. `getState().getSiteIds()` pull-e haman subject ast.

**10. `slice(0, 1)` ya'ni chi baraye header-e `join`?**
Ghanun-e zakhire yek site ast. Pipe-e chand id amade ast vali store bishtar az yek id nemifrestad. Multi-site-e kamel nist.
