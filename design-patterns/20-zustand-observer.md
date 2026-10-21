# 20 — Store

Daftarche-ye 08 observer-e mafhum ast. Inja haman mafhum ru state-e client mizendegi. Agar 08 ra nakhandi, avval an.

## Moshkel

State-e "kodam site alan entekhab shode" ra chand ja mikhahand: header, guard-e permission, va har request-e HTTP dakhel-e tabe'-i ke component nist.

Agar an ra `useState` balay-e derakht bezani, drilling va broadcast-e context bargasht. Va moshkel-e sevom: interceptor-e axios `useState` nadarad. Hook faghat zir-e render ast.

Agar har component mostaghim `localStorage.getItem` bezanad, chand manba'-e haghighat dari. Yeki set karde, digari hanuz ghadim ra dar render darad. Kasi khabar nemishavad.

## Ide

Store = subject-e observer + ye object-e data.

- `getState()` pull ast: snapshot-e alan, bedune subscribe
- `set` taghir + khabar
- `subscribe` sabt-nam
- hook-e `useStore(selector)` ye observer-e React: mount subscribe, unmount unsubscribe, va faghat agar khoruji-ye selector avaz shode bashad render

```javascript
const useSite = create((set, get) => ({
  id: null,
  setId: (id) => set({ id }),
  getId: () => get().id,
}));

const id = useSite((s) => s.id);          // observer-e React
const now = useSite.getState().getId();   // pull, bedune render
```

`setId` list-e component-ha ra be esm nemishnasad.

Ghanun-ha:

**Ye manba'-e haghighat.** Agar ham store va ham `localStorage` va ham `useState`-e joda "site" ra negah darand, se subject dari. Storage mirror ast: store set mikonad, storage ra ham minevisad, va runtime az store mikhanad.

**`getState` reactive nist.** Snapshot-e lahze-ye call. UI ba an khod-be-khod render nemishavad. Baraye "header-e hamin request chi bashad" kafi ast. Baraye "vaghti site avaz shod in component avaz shavad" selector mikhahad.

**Selector khoruji-ye koochak bedahad.** `(s) => s.id` khub. `(s) => ({ id: s.id })` object-e jadid har khabar, hatta agar id avaz nashode. Haman sam-e identity.

**Set-e tu-dar tu copy mikhahad.** `state.user.name = 'a'` aksaran khabar-e dorost nemizanad, chon reference-e `user` avaz nashode. Ya object-e jadid besaz, ya immer ke taghir-e zaheri ra be copy-e vaghe'i tabdil mikonad. Immer observer nist. Komak-e neveshtan-e state-e tu-dar tu ast. Store-e ye field immer nemikhahad.

**Unsubscribe.** Hook-e khub unmount ra laghv mikonad. `store.subscribe` dasti ke unmount nakoni, haman memory leak-e observer ast. Store omr-e tab ra darad. Component omr-e safhe ra.

**Store-e client jay-e cache-e server nist.** List-e personnel haghighat-ash server ast. Copy-e an to Zustand va copy-e an to query cache do haghighat. Store baraye chizi ast ke client malek-ash ast: site-e entekhabi, sidebar, draft-e zakhire-nashode.

Do shenavande, ye subject:

| Shenavande | Che mikhahad | Che abzari |
|---|---|---|
| Component | vaghti avaz shod dobare render sho | selector |
| Interceptor | hamin alan site chi ast | `getState` |

Set-e ba'di, request-e ghabl ra avaz nemikonad. Request-e ghabl header-ash ra lahze-ye send khande. Request-e ba'di snapshot-e jadid migirad. In race bug nist.

## Persistence

`localStorage` tab ra az refresh zende mibarad. Memory-e store na.

- start: storage → state-e avval
- set: state va storage
- khandan-e runtime: state

Agar kasi mostaghim storage ra dast bezanad va store ra na, mirror shekaste. API-e omumi faghat `set` store bashad.

Do tab: event-e `storage` be tab-e digar mifrestad, faghat agar listen karde bashi. Bedune an, do tab do subject-e joda-and ta reload.

Store-e UI outbox nemikhahad. Event-e aggregate `useStore` nemishavad. Yeki session-e ye tab ast. Digari consistency-e system.

## Hala dar front-e Dejban

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

**Observer-e React.** `PageGuard` selector darad: `useSiteStore((state) => state.selectedSiteIds)`. Taghir-e site guard ra dobare hesab mikonad.

**Pull-e transport.** Interceptor: `useSiteStore.getState().getSiteIds()`. Hook nist.

**Mirror.** Avvalin state az `readStoredSiteIds`. Har `setSiteIds` ham `set` ham `localStorage`. Agar memory khali bashad, `getSiteIds` disk ra mikhanad.

`normalizeSiteIds` alan `slice(0, 1)` ast. Ye site. Header-e axios `join(',')` baraye chand id neveshte shode, vali store ye id mifrestad. Pipe-e chand-ta'i hast, ghanun-e alan ye site. "Multi-site-e kamel" nagou.

Listener-e `storage` in file nist. Do tab khodkar ye site nemishavand.

Immer in store nist. `set({ selectedSiteIds: ids })` kafi ast.

List-e personnel in store nist. An query cache ast.

## Agar beporsand, in tor begou

> Store subject-e observer ast. set shenavande-ha ra khabar mikonad bedune esm-e component. Selector render ra riz mikonad. getState pull-e lahze ast va UI ra zende nemikonad. Storage mirror-e refresh ast na manba'-e dovom. To Dejban useSiteStore hamin kar ra baraye site mikonad. PageGuard selector darad. Axios getState mikhanad. Alan ye site normalize mishavad. Do tab listener-e storage nadarand. Dade-ye server in store nist.

## Dah so'al

**1. Store kodam naghsh-e observer ast?**
Subject. `set` khabar midahad. Hook unmount ra unsubscribe mikonad.

**2. Selector che chizi ra kam mikonad?**
Tedad-e render. Faghat khoruji-ye khod ra moghayese mikonad.

**3. Chera selector-e object-e jadid sam ast?**
Identity-e khoruji har bar avaz mishavad. React fekr mikonad state avaz shode.

**4. `getState` key kafi nist?**
Vaghti UI bayad ba taghir-e ba'di dobare render shavad.

**5. Immer che pattern-i nist?**
Observer nist. Abzar-e copy-e tu-dar tu ast.

**6. Chera list-e server to store na?**
Manba'-e haghighat-ash server ast. Do cache do javab-e motanaghez misazad.

**7. Mirror-e localStorage che gharardadi darad?**
Start az disk. Set har do. Khandan az memory.

**8. Do tab chetor sync nemishavand?**
Event-e `storage` faghat agar listen koni. Bedune listener, har tab subject-e khod ra darad.

**9. To Dejban interceptor chera hook-e site nemizanad?**
Interceptor render nist. `getState().getSiteIds()` pull-e haman subject ast.

**10. `slice(0, 1)` yani chi baraye header-e `join`?**
Ghanun-e zakhire ye site ast. Pipe-e chand id amade ast vali store bishtar az ye id nemifrestad.
